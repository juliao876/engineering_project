import React, { useEffect, useState } from 'react';
import '../styles/ProjectCard.css';
import StarEmptyIcon from '../assets/icons/StarEmpty-Icon.svg';
import StarFullIcon from '../assets/icons/StarFull-Icon.svg';
import CommentIcon from '../assets/icons/CommentIcon.svg';
import FigmaIcon from '../assets/icons/FigmaIcon.svg';
import AnalysisIcon from '../assets/icons/AnalysisIcon.svg';
import { CollabAPI } from '../services/api.ts';
import { ButtonSAlt } from './ButtonPresets.tsx';

export interface ProjectCardProps {
  projectId: number;
  title: string;
  description: string;
  rating?: number; // 0–5
  commentsCount?: number;
  figmaUrl?: string;
  previewUrl?: string | null;
  contentType?: "figma" | "image" | "video" | string;
  onPreviewClick?: () => void;
  onAnalyzeClick?: () => void;
  isPublic?: boolean;
  onToggleVisibility?: () => void;
  onDelete?: () => void;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  projectId,
  title,
  description,
  rating = 0,
  commentsCount = 0,
  figmaUrl,
  previewUrl,
  contentType,
  onPreviewClick,
  onAnalyzeClick,
  isPublic,
  onToggleVisibility,
  onDelete,
}) => {
  const [averageRating, setAverageRating] = useState<number>(rating);

  useEffect(() => {
    let isMounted = true;

    async function loadRating() {
      const response = await CollabAPI.getProjectRating(projectId);
      if (!isMounted) return;
      if (response.ok && response.data) {
        const averageValue = response.data.average_rating ?? response.data.average ?? 0;
        setAverageRating(averageValue);
      }
    }

    loadRating();
    return () => {
      isMounted = false;
    };
  }, [projectId]);

  const stars = Array.from({ length: 5 }, (_, index) => {
    const value = index + 1;
    const filled = value <= Math.round(averageRating);
    const Icon = filled ? StarFullIcon : StarEmptyIcon;

    return (
      <span key={value} className="project-card__starIcon" aria-hidden>
        <img
          src={Icon}
          alt={filled ? "Filled star" : "Empty star"}
          className="project-card__star"
        />
      </span>
    );
  });

  return (
    <article className="project-card">
      <button
        type="button"
        className={`project-card__mediaWrapper ${contentType === "video" ? "is-video" : ""}`}
        onClick={onPreviewClick}
        aria-label="Open project details"
      >
        {typeof isPublic === "boolean" && (
          <span
            className={`project-card__visibility ${isPublic ? "is-public" : "is-private"}`}
            aria-label={`Project is ${isPublic ? "public" : "private"}`}
          >
            {isPublic ? "Public" : "Private"}
          </span>
        )}
        <div className="project-card__media">
          {contentType === "video" && previewUrl ? (
            <video src={previewUrl} muted playsInline />
          ) : previewUrl ? (
            <img src={previewUrl} alt={`${title} preview`} />
          ) : (
            <div className="project-card__placeholder">
              <span className="project-card__placeholderCross" aria-hidden>
                ×
              </span>
            </div>
          )}
        </div>
        <div className="project-card__rating">
          <div className="project-card__stars">{stars}</div>
          <div className="project-card__ratingInfo">
            <span className="project-card__ratingAverage">{averageRating.toFixed(1)}</span>
            <span className="project-card__ratingLabel">Average</span>
          </div>
        </div>
        {contentType === "figma" && (
          <span className="project-card__thumbnailBadge" aria-label="Figma project">
            <img src={FigmaIcon} alt="Figma" />
          </span>
        )}
      </button>

      <div className="project-card__bottom">
        <div>
          <h3 className="project-card__title">{title}</h3>
          <p className="project-card__description">{description}</p>
        </div>

        <div className="project-card__actions">
          {onAnalyzeClick && (
            <ButtonSAlt className="project-card__analyseButton" type="button" onClick={onAnalyzeClick}>
              <img src={AnalysisIcon} alt="Analyse" />
              Analyse
            </ButtonSAlt>
          )}
          <button type="button" className="project-card__iconButton">
            <img src={CommentIcon} alt="Comments" />
            {commentsCount > 0 && (
              <span className="project-card__badge">{commentsCount}</span>
            )}
          </button>

          {figmaUrl && (
            <a
              href={figmaUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="project-card__iconButton"
            >
              <img src={FigmaIcon} alt="Open in Figma" />
            </a>
          )}
        </div>

        {(onToggleVisibility || onDelete) && (
          <div className="project-card__ownerActions">
            {onToggleVisibility && typeof isPublic === "boolean" && (
              <button type="button" className="project-card__textButton" onClick={onToggleVisibility}>
                {isPublic ? "Make private" : "Make public"}
              </button>
            )}
            {onDelete && (
              <button type="button" className="project-card__textButton project-card__deleteButton" onClick={onDelete}>
                Delete
              </button>
            )}
          </div>
        )}
      </div>
    </article>
  );
};

export default ProjectCard;