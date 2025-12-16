import React, { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Button from "../components/Button.tsx";
import { AnalysisAPI, ProjectsAPI } from "../services/api.ts";
import SwitchOff from "../assets/icons/Switch-Off.svg";
import SwitchOn from "../assets/icons/Switch-On.svg";
import "../styles/AnalysisPage.css";
import "../styles/tokens.css";

interface AnalysisIssue {
  issue: string;
  expected_min?: number;
  actual?: number;
  node?: string;
  required_ratio?: number;
  actual_ratio?: number;
  avg_depth?: number;
  recommended_max?: number;
}

interface AnalysisMetrics {
  button_size?: { min_detected?: number | null; expected_min?: number; status?: string };
  button_spacing?: { min_spacing?: number | null; recommended_min?: number | null; status?: string };
  contrast_ratio?: { min_ratio?: number | null; required_min?: number; status?: string };
  font_size?: { min_detected?: number | null; recommended_min?: number; status?: string };
  touch_target?: { min_detected?: number | null; recommended_min?: number; status?: string } | null;
  layout_depth?: { avg_depth?: number; recommended_max?: number; status?: string };
}

interface AnalysisResult {
  project_id: number;
  device: "desktop" | "mobile";
  summary: string;
  opinion: string;
  recommendations: string[];
  metrics: AnalysisMetrics;
  issues: AnalysisIssue[];
}

const AnalysisPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const numericProjectId = useMemo(() => Number(projectId), [projectId]);

  const [projectTitle, setProjectTitle] = useState("Loading project...");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<"desktop" | "mobile">("desktop");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!numericProjectId) return;

    async function loadProject() {
      const response = await ProjectsAPI.getProjectDetails(numericProjectId);
      if (response.ok) {
        const project = response.data?.project || response.data;
        setProjectTitle(project?.title || "Project analysis");
        setPreviewUrl(project?.preview_url || project?.preview || null);
        setContentType(project?.content_type || null);
      } else {
        setProjectTitle("Project analysis");
        setPreviewUrl(null);
        setContentType(null);
      }
    }

    loadProject();
  }, [numericProjectId]);

  useEffect(() => {
    setAnalysis(null);
    setError(null);
  }, [selectedDevice]);

  const startAnalysis = async () => {
    if (!numericProjectId || !selectedDevice) return;

    setIsLoading(true);
    setError(null);
    setAnalysis(null);

    const response = await AnalysisAPI.runAnalysis(numericProjectId, {
      device: selectedDevice,
    });

    if (response.ok) {
      setAnalysis(response.data as AnalysisResult);
    } else {
      const detail = response.data?.detail || "Unable to run analysis";
      setError(typeof detail === "string" ? detail : "Unable to run analysis");
    }

    setIsLoading(false);
  };

  const renderMetricCard = (
    title: string,
    value: string,
    color: "pink" | "yellow" | "indigo",
  ) => (
    <div className={`metric-card metric-card--${color}`}>
      <p className="metric-card__label">{title}</p>
      <p className="metric-card__value">{value}</p>
    </div>
  );

  const hasAnalysis = Boolean(analysis);

  return (
    <div className="analysis-screen">
      <main className="analysis-container">
        <div className="analysis-header">
          <Link to="/profile" style={{ textDecoration: "none" }}>
            <Button variant="secondary" size="small">
              ← Back to profile
            </Button>
          </Link>
        </div>

        <h1 className="analysis-title">Analysis of Project "{projectTitle}"</h1>

        <section className="analysis-hero">
          <div className="analysis-controls">
            <p className="analysis-section-label">Type of device</p>
            <div className="analysis-toggle">
              <span className="analysis-toggle__label">Desktop</span>
              <button
                type="button"
                className="analysis-switch"
                onClick={() =>
                  setSelectedDevice((prev) => (prev === "desktop" ? "mobile" : "desktop"))
                }
                aria-label="Toggle device type"
              >
                <img
                  src={selectedDevice === "desktop" ? SwitchOff : SwitchOn}
                  alt={selectedDevice === "desktop" ? "Desktop selected" : "Mobile selected"}
                />
              </button>
              <span className="analysis-toggle__label">Mobile</span>
            </div>

            {error && <p className="analysis-error">{error}</p>}

            <Button
              variant="primary"
              size="large"
              disabled={isLoading}
              onClick={startAnalysis}
            >
              {isLoading ? "Analysing..." : "Start Analysing"}
            </Button>
          </div>

          <div className="analysis-preview">
            {previewUrl ? (
              contentType === "video" ? (
                <video src={previewUrl} controls className="analysis-preview__media" />
              ) : (
                <img
                  src={previewUrl}
                  alt={`${projectTitle} preview`}
                  className="analysis-preview__media"
                />
              )
            ) : (
              <div className="analysis-preview__placeholder">
                <div className="analysis-preview__mark" />
              </div>
            )}
          </div>
        </section>

        {hasAnalysis && (
          <section className="analysis-results">
            <div className="metrics-grid">
              {renderMetricCard(
                "Button Size",
                analysis?.metrics.button_size?.min_detected
                  ? `${analysis.metrics.button_size.min_detected}px`
                  : "No data",
                "pink",
              )}
              {renderMetricCard(
                "Button Spacing",
                analysis?.metrics.button_spacing?.min_spacing
                  ? `${analysis.metrics.button_spacing.min_spacing.toFixed(5)}px`
                  : "No data",
                "yellow",
              )}
              {renderMetricCard(
                "Contrast Ratio",
                analysis?.metrics.contrast_ratio?.min_ratio
                  ? `${analysis.metrics.contrast_ratio.min_ratio.toFixed(2)}`
                  : "No data",
                "indigo",
              )}
              {renderMetricCard(
                "Font Size",
                analysis?.metrics.font_size?.min_detected
                  ? `${analysis.metrics.font_size.min_detected}px`
                  : "No data",
                "yellow",
              )}
            </div>

            <div className="metrics-secondary-grid">
              {renderMetricCard(
                "Touch Target Size (Mobile Only)",
                analysis?.metrics.touch_target?.min_detected
                  ? `${analysis.metrics.touch_target.min_detected}px`
                  : "Mobile only",
                "indigo",
              )}
              {renderMetricCard(
                "Layout Structure",
                analysis?.metrics.layout_depth?.avg_depth
                  ? `${analysis.metrics.layout_depth.avg_depth.toFixed(1)} levels`
                  : "No data",
                "pink",
              )}

              <div className="analysis-opinion">
                <h3>Overall Opinion</h3>
                <p className="analysis-opinion__text">{analysis?.opinion}</p>
                <p className="analysis-opinion__text">{analysis?.summary}</p>
                {analysis?.recommendations?.length ? (
                  <ul className="analysis-recommendations">
                    {analysis.recommendations.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
};

export default AnalysisPage;