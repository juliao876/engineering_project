from fastapi import HTTPException, Response, requests
from pip._internal.network.auth import Credentials
from sqlalchemy.orm import Session
import os
import json
from src.database.models.Analysis import Analysis
from datetime import datetime
from src.database.models.Analysis import Analysis

FIGMA_INTEGRATION_URL = "http://127.0.0.1:6702"

class Services:
    def __init__(self, db: Session):
        self.db = db

    def run_analysis(self, project_id: int):
        response = requests.get(f"{FIGMA_INTEGRATION_URL}/figma/{project_id}/data")
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Could not fetch Figma data"
            )
        figma_data = response.json()
        # 2. Analiza UX
        issues_data = self._analyze_figma_data(figma_data)
        # 3. Generowanie podsumowania i opinii
        conclusions = self._generate_conclusions(issues_data)
        # 4. Zapis w bazie
        analysis = Analysis(
            analysis_id=f"A-{project_id}-{int(datetime.utcnow().timestamp())}",
            project_id=str(project_id),
            status="completed",

            results_json=json.dumps(issues_data),
            raw_data=json.dumps(figma_data),

            summary=conclusions["summary"],
            opinion=conclusions["opinion"],
            recomendation=json.dumps(conclusions["recommendations"]),

            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        # 5. Zwróć wynik analizy
        return {
            "project_id": project_id,
            "summary": conclusions["summary"],
            "issues": issues_data["issues"],
            "opinion": conclusions["opinion"],
            "recommendations": conclusions["recommendations"]
        }
    def _analyze_figma_data(self, figma_data: dict) -> dict:
        nodes = figma_data.get("nodes", [])
        issues = []
        device = "desktop"
        # ---------------- BUTTON SIZE ---------------------
        MIN_BUTTON_HEIGHT = 42
        for node in nodes:
            if node.get("type") == "BUTTON" or "button" in node.get("name", "").lower():
                frame = node.get("absoluteBoundingBox", {})
                height = frame.get("height")

                if height and height < MIN_BUTTON_HEIGHT:
                    issues.append({
                        "issue": "Button height too small",
                        "expected_min": MIN_BUTTON_HEIGHT,
                        "actual": height,
                        "node": node.get("id")
                    })

        # ---------------- FONT SIZE -----------------------
        for node in nodes:
            if node.get("type") == "TEXT":
                style = node.get("style", {})
                font_size = style.get("fontSize")

                if font_size and font_size < 14:
                    issues.append({
                        "issue": "Font too small",
                        "expected_min": 14,
                        "actual": font_size,
                        "node": node.get("id")
                    })

        # ---------------- CONTRAST ------------------------
        def relative_luminance(rgb):
            rgb = [v / 255 for v in rgb]

            def f(c):
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

            r, g, b = map(f, rgb)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b

        def contrast_ratio(c1, c2):
            L1 = relative_luminance(c1)
            L2 = relative_luminance(c2)
            L1, L2 = max(L1, L2), min(L1, L2)
            return (L1 + 0.05) / (L2 + 0.05)

        for node in nodes:
            fills = node.get("fills")
            if fills and isinstance(fills, list):
                color = fills[0].get("color")
                if color:
                    fg = [int(color["r"] * 255),
                          int(color["g"] * 255),
                          int(color["b"] * 255)]
                    bg = [255, 255, 255]

                    ratio = contrast_ratio(fg, bg)
                    if ratio < 4.5:
                        issues.append({
                            "issue": "Insufficient contrast",
                            "required_ratio": 4.5,
                            "actual_ratio": round(ratio, 2),
                            "node": node.get("id")
                        })
        # ---------------- LAYOUT DEPTH ---------------------
        def get_depth(node):
            if not node.get("children"):
                return 0
            return 1 + max(get_depth(c) for c in node.get("children", []))

        depths = [get_depth(node) for node in nodes]
        if depths and sum(depths) / len(depths) > 6:
            issues.append({
                "issue": "Deep nesting (poor hierarchy)",
                "average_depth": sum(depths) / len(depths),
                "recommended_max": 5
            })
        # ---------------- RECOMMENDATIONS ------------------
        recommendations = []

        if any("button" in i["issue"].lower() for i in issues):
            recommendations.append("Increase button height.")
        if any("font" in i["issue"].lower() for i in issues):
            recommendations.append("Increase font size for readability.")
        if any("contrast" in i["issue"].lower() for i in issues):
            recommendations.append("Use WCAG AA contrast ratios.")
        if any("nesting" in i["issue"].lower() for i in issues):
            recommendations.append("Flatten layout structure.")

        return {
            "device": device,
            "issues": issues,
            "recommendations": recommendations
        }
    # ======================================================
    #          GENEROWANIE PODSUMOWANIA I OPINII
    # ======================================================
    def _generate_conclusions(self, data: dict):
        issues = data["issues"]

        summary = f"Found {len(issues)} UX issues."
        opinion = "Overall layout is acceptable." if len(issues) < 3 else "The project needs UX improvements."

        return {
            "summary": summary,
            "opinion": opinion,
            "recommendations": data["recommendations"]
        }
    def get_analysis(self, project_id: int):
        analysis = (
            self.db.query(Analysis)
            .filter(Analysis.project_id == str(project_id))
            .order_by(Analysis.created_at.desc())
            .first()
        )
        if not analysis:
            return None
        return {
            "project_id": int(analysis.project_id),
            "summary": analysis.summary,
            "issues": json.loads(analysis.results_json)["issues"],
            "opinion": analysis.opinion,
            "recommendations": json.loads(analysis.recomendation)
        }
    def get_checklist(self):
        return {
            "categories": [
                {
                    "name": "Button Size",
                    "rules": [
                        {"description": "Minimum height 42px", "desktop": 42, "mobile": 42},
                        {"description": "Touch-friendly spacing 16–24px"}
                    ]
                },
                {
                    "name": "Spacing",
                    "rules": [
                        {"description": "Large spacing: 16–24px"},
                        {"description": "Medium spacing: 24–40px"},
                        {"description": "Small spacing: 32–48px"},
                    ]
                },
                {
                    "name": "Text Readability",
                    "rules": [
                        {"description": "Minimum font size 14px desktop"},
                        {"description": "Line height between 100–180%"}
                    ]
                },
                {
                    "name": "Color Contrast",
                    "rules": [
                        {"description": "WCAG AA contrast ratio 4.5:1 or higher"}
                    ]
                },
                {
                    "name": "Layout Structure",
                    "rules": [
                        {"description": "Avoid nesting deeper than 5 levels"},
                        {"description": "Ensure clean visual hierarchy"}
                    ]
                }
            ]
        }
