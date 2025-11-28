import React from 'react';
import '../styles/ProjectCard.css';
import StarEmptyIcon from '../assets/icons/StarEmpty-Icon.svg';
import StarFullIcon from '../assets/icons/StarFull-Icon.svg';
import CommentIcon from '../assets/icons/CommentIcon.svg';
import FigmaIcon from '../assets/icons/FigmaIcon.svg';

export interface ProjectCardProps {
  title: string;
  description: string;
  rating: number; // 0–5
  commentsCount?: number;
  figmaUrl?: string;
}

const ProjectCard: React.FC<ProjectCardProps> = ({
  title,
  description,
  rating,
  commentsCount = 0,
  figmaUrl,
}) => {
  const stars = Array.from({ length: 5 }, (_, index) => {
    const filled = index < rating;
    const Icon = filled ? StarFullIcon : StarEmptyIcon;

    return (
      <img
        key={index}
        src={Icon}
        alt={filled ? 'Filled star' : 'Empty star'}
        className="project-card__star"
      />
    );
  });

  return (
    <article className="project-card">
      <div className="project-card__top">
        <div className="project-card__rating">{stars}</div>
        <div className="project-card__thumbnail" />
      </div>

      <div className="project-card__bottom">
        <div>
          <h3 className="project-card__title">{title}</h3>
          <p className="project-card__description">{description}</p>
        </div>

        <div className="project-card__actions">
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
      </div>
    </article>
  );
};

export default ProjectCard;
