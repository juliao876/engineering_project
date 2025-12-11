from fastapi import HTTPException
from sqlalchemy.orm import Session
import json
import requests
from datetime import datetime

from src.database.models.Analysis import Analysis

FIGMA_SERVICE_URL = "http://localhost:6702/api/v1"   # Docker DNS name OR localhost depending on env


class Services:
    def __init__(self, db: Session):
        self.db = db

    # ======================================================
    #                RUN ANALYSIS ENTRYPOINT
    # ======================================================
    def run_analysis(self, project_id: int, device: str, figma_data: dict = None,
                     token: str = None, figma_url: str = None):

        # ---------------------------------------------
        # CASE 1 — user gives raw figma_data directly
        # ---------------------------------------------
        if figma_data:
            if not isinstance(figma_data, dict):
                raise HTTPException(status_code=400, detail="Invalid figma_data payload")

        # ---------------------------------------------
        # CASE 2 — user gives figma_url → call figma-service
        # ---------------------------------------------
        elif figma_url:
            if not token:
                raise HTTPException(400, "Authorization token required when using figma_url")

            payload = {"file_url": figma_url}
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

    # ======================================================
    #            FIGMA DATA ANALYSIS CORE ENGINE
    # ======================================================
    def _analyze_figma_data(self, figma_data: dict, device: str):
        # ---- (TWÓJ KOD ANALIZY BEZ ZMIAN) ----
        # Wklejam cały, nic nie zmieniam strukturalnie
        def walk(node):
            yield node
            for child in node.get("children", []):
                yield from walk(child)

        document = figma_data.get("document", {})
        all_nodes = list(walk(document))

        issues = []

        BUTTON_MIN_HEIGHT = 42
        FONT_MIN_DESKTOP = 14
        FONT_MIN_MOBILE = 16
        CONTRAST_MIN = 4.5
        TOUCH_MIN = 44

        metrics = {
            "button_size": {"min_detected": None, "expected_min": BUTTON_MIN_HEIGHT, "status": "ok"},
            "button_spacing": {"min_spacing": None, "recommended_min": None, "status": "ok"},
            "contrast_ratio": {"min_ratio": None, "required_min": CONTRAST_MIN, "status": "ok"},
            "font_size": {
                "min_detected": None,
                "recommended_min": FONT_MIN_DESKTOP if device == "desktop" else FONT_MIN_MOBILE,
                "status": "ok"
            },
            "touch_target": None,
            "layout_depth": {"avg_depth": 0, "recommended_max": 5, "status": "ok"},
        }

        # -------- BUTTONS --------
        min_button_height = None
        for node in all_nodes:
            if "button" in node.get("name", "").lower() or node.get("type") in ["RECTANGLE", "FRAME"]:
                box = node.get("absoluteBoundingBox")
                if box:
                    h = box.get("height")
                    if h:
                        if min_button_height is None or h < min_button_height:
                            min_button_height = h
                        if h < BUTTON_MIN_HEIGHT:
                            issues.append({
                                "issue": "Button height too small",
                                "expected_min": BUTTON_MIN_HEIGHT,
                                "actual": h,
                                "node": node.get("id")
                            })

        metrics["button_size"]["min_detected"] = min_button_height
        if min_button_height and min_button_height < BUTTON_MIN_HEIGHT:
            metrics["button_size"]["status"] = "error"

        # -------- FONTS --------
        recommended_min_font = FONT_MIN_DESKTOP if device == "desktop" else FONT_MIN_MOBILE
        min_font = None

        for node in all_nodes:
            if node.get("type") == "TEXT":
                style = node.get("style", {})
                fs = style.get("fontSize")

                if fs:
                    if min_font is None or fs < min_font:
                        min_font = fs

                    if fs < recommended_min_font:
                        issues.append({
                            "issue": "Font too small",
                            "expected_min": recommended_min_font,
                            "actual": fs,
                            "node": node.get("id")
                        })

        metrics["font_size"]["min_detected"] = min_font
        if min_font and min_font < recommended_min_font:
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

                    if r < CONTRAST_MIN:
                        issues.append({
                            "issue": "Insufficient contrast",
                            "actual_ratio": round(r, 2),
                            "required_ratio": CONTRAST_MIN,
                            "node": node.get("id")
                        })

        metrics["contrast_ratio"]["min_ratio"] = lowest_contrast
        if lowest_contrast and lowest_contrast < CONTRAST_MIN:
            metrics["contrast_ratio"]["status"] = "error"

        # -------- TOUCH (mobile) --------
        if device == "mobile":
            smallest_touch = None
            for node in all_nodes:
                box = node.get("absoluteBoundingBox")
                if box:
                    w, h = box.get("width"), box.get("height")
                    if w and h:
                        size = min(w, h)
                        if smallest_touch is None or size < smallest_touch:
                            smallest_touch = size
                        if size < TOUCH_MIN:
                            issues.append({
                                "issue": "Touch target too small",
                                "actual": size,
                                "expected_min": TOUCH_MIN,
                                "node": node.get("id")
                            })

            metrics["touch_target"] = {
                "min_detected": smallest_touch,
                "recommended_min": TOUCH_MIN,
                "status": "ok" if smallest_touch and smallest_touch >= TOUCH_MIN else "error"
            }

        # -------- DEPTH --------
        def depth(node):
            if not node.get("children"):
                return 0
            return 1 + max(depth(c) for c in node["children"])

        depths = [depth(n) for n in all_nodes]
        avg_depth = sum(depths) / len(depths) if depths else 0
        metrics["layout_depth"]["avg_depth"] = avg_depth

        if avg_depth > 5:
            metrics["layout_depth"]["status"] = "warning"
            issues.append({
                "issue": "Deep nesting",
                "avg_depth": avg_depth,
                "recommended_max": 5
            })

        return {"device": device, "metrics": metrics, "issues": issues}

    # ======================================================
    #            OPINION + SUMMARY GENERATION
    # ======================================================
    def _generate_conclusions(self, data: dict):
        issues = data["issues"]
        count = len(issues)

        summary = f"Found {count} UX issues."
        opinion = "Overall layout is acceptable." if count < 3 else "The project needs UX improvements."

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
                        {"description": "Minimum height 42px", "desktop": 42, "mobile": 42},
                        {"description": "Touch-friendly spacing 16–24px"},
                    ],
                },
                {
                    "name": "Spacing",
                    "rules": [
                        {"description": "Large spacing: 16–24px"},
                        {"description": "Medium spacing: 24–40px"},
                        {"description": "Small spacing: 32–48px"},
                    ],
                },
                {
                    "name": "Text Readability",
                    "rules": [
                        {"description": "Minimum font size 14px desktop"},
                        {"description": "Line height between 100–180%"},
                    ],
                },
                {
                    "name": "Color Contrast",
                    "rules": [
                        {"description": "WCAG AA contrast ratio 4.5:1 or higher"},
                    ],
                },
                {
                    "name": "Layout Structure",
                    "rules": [
                        {"description": "Avoid nesting deeper than 5 levels"},
                        {"description": "Ensure clean visual hierarchy"},
                    ],
                },
            ]
        }
