import json
import os
from datetime import datetime

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.database.models.Analysis import Analysis

FIGMA_SERVICE_URL = os.getenv("FIGMA_SERVICE_URL", "http://figma-service:6702/api/v1")
PROJECTS_SERVICE_URL = os.getenv("PROJECTS_SERVICE_URL", "http://project-service:6701/api/v1")
PROJECTS_SERVICE_FALLBACK = "http://project-service:6701/api/v1"


class Services:
    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    #                RUN ANALYSIS ENTRYPOINT
    # ======================================================
    def run_analysis(
        self,
        project_id: int,
        device: str,
        figma_data: dict = None,
        token: str = None,
        figma_url: str = None,
    ):

        resolved_figma_url = figma_url
        if not figma_data and not resolved_figma_url:
            resolved_figma_url = self._get_project_figma_url(project_id, token)

        # ---------------------------------------------
        # CASE 1 — user gives raw figma_data directly
        # ---------------------------------------------
        if figma_data:
            if not isinstance(figma_data, dict):
                raise HTTPException(status_code=400, detail="Invalid figma_data payload")

        # ---------------------------------------------
        # CASE 2 — user gives figma_url → call figma-service
        # ---------------------------------------------
        elif resolved_figma_url:
            if not token:
                raise HTTPException(401, "Authorization token required when using figma_url")

            payload = {"file_url": resolved_figma_url}
            headers = {"Authorization": f"Bearer {token}"}

            try:
                res = requests.post(
                    f"{FIGMA_SERVICE_URL}/figma/import",
                    json=payload,
                    headers=headers,
                    timeout=10,
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Could not reach figma-service: {e}")

            if res.status_code != 200:
                raise HTTPException(
                    status_code=res.status_code,
                    detail=f"Figma import failed: {res.text}"
                )

            project_data = res.json().get("project")
            if not project_data:
                raise HTTPException(500, "Figma import did not return project data")

            figma_data = project_data.get("project") or project_data

        else:
            raise HTTPException(400, "You must provide either figma_data or figma_url")

        # Run the core analysis engine
        analysis_result = self._analyze_figma_data(figma_data, device)
        conclusions = self._generate_conclusions(analysis_result)

        # Save to DB
        analysis = Analysis(
            analysis_id=f"A-{project_id}-{int(datetime.utcnow().timestamp())}",
            project_id=str(project_id),
            status="completed",

            results_json=json.dumps(analysis_result),
            raw_data=json.dumps(figma_data),

            summary=conclusions["summary"],
            opinion=conclusions["opinion"],
            recomendation=json.dumps(conclusions["recommendations"]),

            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)

        return {
            "project_id": project_id,
            "device": device,
            "summary": conclusions["summary"],
            "opinion": conclusions["opinion"],
            "recommendations": conclusions["recommendations"],
            "metrics": analysis_result["metrics"],
            "issues": analysis_result["issues"],
        }

    def _get_project_figma_url(self, project_id: int, token: str | None = None) -> str:
        """Fetch the project's Figma link from the Projects service."""

        def _call_projects(url: str):
            return requests.get(
                f"{url}/project/details/{project_id}",
                headers={"Authorization": f"Bearer {token}"} if token else None,
                timeout=5,
            )

        try:
            response = _call_projects(PROJECTS_SERVICE_URL)
        except Exception:
            # Sometimes the compose host is registered as project-service – retry with it
            try:
                response = _call_projects(PROJECTS_SERVICE_FALLBACK)
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Could not reach Projects service: {exc}",
                )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Could not fetch project details",
            )

        payload = (
            response.json()
            if response.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        project = payload.get("project") if isinstance(payload, dict) else None
        figma_link = None
        if isinstance(project, dict):
            figma_link = project.get("figma_link")
        elif isinstance(payload, dict):
            figma_link = payload.get("figma_link")

        if not figma_link:
            raise HTTPException(404, "No Figma link configured for this project")

        return figma_link

    # ======================================================
    #            FIGMA DATA ANALYSIS CORE ENGINE
    # ======================================================
    def _analyze_figma_data(self, figma_data: dict, device: str):
        def walk(node):
            yield node
            for child in node.get("children", []):
                yield from walk(child)

        document = figma_data.get("document", {})
        all_nodes = list(walk(document))

        issues = []

        BUTTON_THRESHOLDS = {
            "high": 72,  # High priority button >= 72px
            "medium": 60,  # Medium priority button >= 60px
            "low": 48,  # Low priority button >= 48px
        }

        SPACING_RANGES = {
            "high": (12, 24),
            "medium": (24, 40),
            "low": (32, 48),
        }

        CONTRAST = {"normal": 4.5, "large": 3.0}

        FONT_MIN = {"desktop": 14, "mobile": 11}
        FONT_IDEAL = {"desktop": (14, 17), "mobile": (15, 17)}

        TOUCH_MIN_CONTROL = 44
        TOUCH_MIN_TEXT = 30

        LAYOUT_MAX_DEPTH = 3

        metrics = {
            "button_size": {
                "min_detected": None,
                "expected_min": BUTTON_THRESHOLDS["low"],
                "priority_breakdown": {},
                "status": "ok",
            },
            "button_spacing": {
                "min_spacing": None,
                "recommended_min": None,
                "status": "ok",
                "priority_breakdown": {},
            },
            "contrast_ratio": {
                "min_ratio": None,
                "required_min_normal": CONTRAST["normal"],
                "required_min_large": CONTRAST["large"],
                "status": "ok",
            },
            "font_size": {
                "min_detected": None,
                "recommended_min": FONT_MIN[device],
                "ideal_range": FONT_IDEAL[device],
                "status": "ok",
            },
            "touch_target": None,
            "layout_depth": {"avg_depth": 0, "recommended_max": LAYOUT_MAX_DEPTH, "status": "ok"},
        }

        def classify_priority(node_name: str):
            name = (node_name or "").lower()
            if "primary" in name or "high" in name:
                return "high"
            if "secondary" in name or "medium" in name:
                return "medium"
            return "low"

        button_boxes = []
        # -------- BUTTONS --------
        for node in all_nodes:
            node_name = node.get("name", "")
            if "button" in node_name.lower() or node.get("type") in ["RECTANGLE", "FRAME"]:
                box = node.get("absoluteBoundingBox")
                if box and box.get("height") and box.get("width"):
                    priority = classify_priority(node_name)
                    h = box.get("height")
                    button_boxes.append((box, priority, node))

                    breakdown = metrics["button_size"]["priority_breakdown"].setdefault(
                        priority, {"min_detected": None, "expected_min": BUTTON_THRESHOLDS[priority]}
                    )

                    if breakdown["min_detected"] is None or h < breakdown["min_detected"]:
                        breakdown["min_detected"] = h

                    if metrics["button_size"]["min_detected"] is None or h < metrics["button_size"]["min_detected"]:
                        metrics["button_size"]["min_detected"] = h

                    if h < BUTTON_THRESHOLDS[priority]:
                        issues.append(
                            {
                                "issue": f"{priority.title()} priority button height too small",
                                "expected_min": BUTTON_THRESHOLDS[priority],
                                "actual": h,
                                "node": node.get("id"),
                            }
                        )

        # Determine button spacing between detected buttons
        def _distance(box_a, box_b):
            ax1, ay1 = box_a.get("x", 0), box_a.get("y", 0)
            ax2, ay2 = ax1 + box_a.get("width", 0), ay1 + box_a.get("height", 0)

            bx1, by1 = box_b.get("x", 0), box_b.get("y", 0)
            bx2, by2 = bx1 + box_b.get("width", 0), by1 + box_b.get("height", 0)

            horiz_gap = max(0, max(bx1 - ax2, ax1 - bx2))
            vert_gap = max(0, max(by1 - ay2, ay1 - by2))
            return max(horiz_gap, vert_gap)

        min_spacing = None
        spacing_priority = None
        for i in range(len(button_boxes)):
            for j in range(i + 1, len(button_boxes)):
                gap = _distance(button_boxes[i][0], button_boxes[j][0])
                if gap <= 0:
                    continue
                if min_spacing is None or gap < min_spacing:
                    min_spacing = gap
                    # take stricter priority among the two buttons being compared
                    priorities = sorted({button_boxes[i][1], button_boxes[j][1]}, key=lambda p: ["high", "medium", "low"].index(p))
                    spacing_priority = priorities[0] if priorities else None

        if spacing_priority:
            metrics["button_spacing"]["recommended_min"] = SPACING_RANGES[spacing_priority][0]
            metrics["button_spacing"]["priority_breakdown"][spacing_priority] = {
                "min_detected": min_spacing,
                "recommended_range": SPACING_RANGES[spacing_priority],
            }
        if min_spacing is not None:
            min_spacing = round(min_spacing, 5)

        metrics["button_spacing"]["min_spacing"] = min_spacing

        if spacing_priority and min_spacing is not None and min_spacing < SPACING_RANGES[spacing_priority][0]:
            metrics["button_spacing"]["status"] = "warning"
            issues.append(
                {
                    "issue": f"Spacing below {spacing_priority} priority guidance",
                    "expected_min": SPACING_RANGES[spacing_priority][0],
                    "actual": min_spacing,
                }
            )

        if metrics["button_size"]["min_detected"] and metrics["button_size"]["min_detected"] < BUTTON_THRESHOLDS["low"]:
            metrics["button_size"]["status"] = "error"

        # -------- FONTS --------
        min_font = None
        for node in all_nodes:
            if node.get("type") == "TEXT":
                style = node.get("style", {})
                fs = style.get("fontSize")

                if fs:
                    if min_font is None or fs < min_font:
                        min_font = fs

                    if fs < FONT_MIN[device]:
                        issues.append(
                            {
                                "issue": "Font too small",
                                "expected_min": FONT_MIN[device],
                                "actual": fs,
                                "node": node.get("id"),
                            }
                        )

        metrics["font_size"]["min_detected"] = min_font
        if min_font and min_font < FONT_MIN[device]:
            metrics["font_size"]["status"] = "warning"

        # -------- CONTRAST --------
        def luminance(rgb):
            def f(c):
                c = c / 255
                return c / 12.92 if c <= 0.03928 else ((c + 0.055)/1.055)**2.4

            r, g, b = rgb
            return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b)

        def contrast(fg, bg):
            L1 = luminance(fg)
            L2 = luminance(bg)
            return (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)

        lowest_contrast = None
        for node in all_nodes:
            fills = node.get("fills")
            if fills and isinstance(fills, list):
                col = fills[0].get("color")
                if col:
                    fg = [int(col["r"] * 255), int(col["g"] * 255), int(col["b"] * 255)]
                    bg = [255, 255, 255]
                    r = contrast(fg, bg)

                    if lowest_contrast is None or r < lowest_contrast:
                        lowest_contrast = r

                    if r < CONTRAST["large"]:
                        issues.append(
                            {
                                "issue": "Contrast below large text requirement",
                                "actual_ratio": round(r, 2),
                                "required_ratio": CONTRAST["large"],
                                "node": node.get("id"),
                            }
                        )
                    elif r < CONTRAST["normal"]:
                        issues.append(
                            {
                                "issue": "Contrast below normal text requirement",
                                "actual_ratio": round(r, 2),
                                "required_ratio": CONTRAST["normal"],
                                "node": node.get("id"),
                            }
                        )

        metrics["contrast_ratio"]["min_ratio"] = lowest_contrast
        if lowest_contrast and lowest_contrast < CONTRAST["large"]:
            metrics["contrast_ratio"]["status"] = "error"
        elif lowest_contrast and lowest_contrast < CONTRAST["normal"]:
            metrics["contrast_ratio"]["status"] = "warning"

        # -------- TOUCH (mobile) --------
        if device == "mobile":
            smallest_touch = None
            smallest_text_touch = None
            for node in all_nodes:
                box = node.get("absoluteBoundingBox")
                if box:
                    w, h = box.get("width"), box.get("height")
                    if w and h:
                        size = min(w, h)
                        if node.get("type") == "TEXT":
                            if smallest_text_touch is None or size < smallest_text_touch:
                                smallest_text_touch = size
                            if size < TOUCH_MIN_TEXT:
                                issues.append(
                                    {
                                        "issue": "Tappable text target too small",
                                        "actual": size,
                                        "expected_min": TOUCH_MIN_TEXT,
                                        "node": node.get("id"),
                                    }
                                )
                        else:
                            if smallest_touch is None or size < smallest_touch:
                                smallest_touch = size
                            if size < TOUCH_MIN_CONTROL:
                                issues.append(
                                    {
                                        "issue": "Touch target too small",
                                        "actual": size,
                                        "expected_min": TOUCH_MIN_CONTROL,
                                        "node": node.get("id"),
                                    }
                                )

            metrics["touch_target"] = {
                "min_detected": smallest_touch,
                "recommended_min": TOUCH_MIN_CONTROL,
                "text_min_detected": smallest_text_touch,
                "text_recommended_min": TOUCH_MIN_TEXT,
                "status": "ok"
                if smallest_touch and smallest_touch >= TOUCH_MIN_CONTROL and smallest_text_touch and smallest_text_touch >= TOUCH_MIN_TEXT
                else "error",
            }

        # -------- DEPTH --------
        def depth(node):
            if not node.get("children"):
                return 0
            return 1 + max(depth(c) for c in node["children"])

        depths = [depth(n) for n in all_nodes]
        avg_depth = sum(depths) / len(depths) if depths else 0
        metrics["layout_depth"]["avg_depth"] = avg_depth

        if avg_depth > LAYOUT_MAX_DEPTH:
            metrics["layout_depth"]["status"] = "warning"
            issues.append({
                "issue": "Deep nesting",
                "avg_depth": avg_depth,
                "recommended_max": LAYOUT_MAX_DEPTH,
            })

        return {"device": device, "metrics": metrics, "issues": issues}

    # ======================================================
    #            OPINION + SUMMARY GENERATION
    # ======================================================
    def _generate_conclusions(self, data: dict):
        issues = data["issues"]
        count = len(issues)

        summary = f"Found {count} UX issues across spacing, readability, and controls."
        if count == 0:
            opinion = "Great job! The design meets the key accessibility guidelines."
        elif count < 3:
            opinion = "Overall layout is acceptable with minor adjustments recommended."
        else:
            opinion = "The project needs UX improvements to meet the provided guidelines."

        recommendations = []
        for i in issues:
            t = i["issue"].lower()
            if "button" in t:
                recommendations.append("Increase button height.")
            if "font" in t:
                recommendations.append("Increase font size for readability.")
            if "contrast" in t:
                recommendations.append("Improve color contrast to meet WCAG AA.")
            if "nest" in t:
                recommendations.append("Reduce layout depth for better hierarchy.")
            if "touch" in t:
                recommendations.append("Increase touch target sizes on mobile.")

        return {
            "summary": summary,
            "opinion": opinion,
            "recommendations": list(set(recommendations)),
        }

    # ======================================================
    #         RETRIEVE LAST ANALYSIS FROM DATABASE
    # ======================================================
    def get_analysis(self, project_id: int):
        analysis = (
            self.db.query(Analysis)
            .filter(Analysis.project_id == str(project_id))
            .order_by(Analysis.created_at.desc())
            .first()
        )

        if not analysis:
            return None

        parsed = json.loads(analysis.results_json)

        return {
            "project_id": int(analysis.project_id),
            "device": parsed["device"],
            "summary": analysis.summary,
            "opinion": analysis.opinion,
            "recommendations": json.loads(analysis.recomendation),
            "metrics": parsed["metrics"],
            "issues": parsed["issues"],
        }

    # ======================================================
    #          SIMPLE CHECKLIST FOR FRONTEND
    # ======================================================
    def get_checklist(self):
        return {
            "categories": [
                {
                    "name": "Button Size",
                    "rules": [
                        {"description": "High priority button ≥ 72px", "desktop": 72, "mobile": 72},
                        {"description": "Medium priority button ≥ 60px", "desktop": 60, "mobile": 60},
                        {"description": "Low priority button ≥ 48px", "desktop": 48, "mobile": 48},
                    ],
                },
                {
                    "name": "Spacing",
                    "rules": [
                        {"description": "High priority buttons spacing 12–24px"},
                        {"description": "Medium priority buttons spacing 24–40px"},
                        {"description": "Low priority buttons spacing 32–48px"},
                    ],
                },
                {
                    "name": "Text Readability",
                    "rules": [
                        {"description": "Desktop title ideal 14–17px (min 14px)"},
                        {"description": "Phone title ideal 15–17px (min 11–12px)"},
                    ],
                },
                {
                    "name": "Color Contrast",
                    "rules": [
                        {"description": "Normal text ratio ≥ 4.5:1"},
                        {"description": "Large text/UI icons ratio ≥ 3:1"},
                    ],
                },
                {
                    "name": "Layout Structure",
                    "rules": [
                        {"description": "Maintain button hierarchy depth ≤ 3"},
                        {"description": "Ensure clean visual hierarchy"},
                    ],
                },
            ]
        }