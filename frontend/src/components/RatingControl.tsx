import React, { useEffect, useMemo, useState } from "react";
import StarEmptyIcon from "../assets/icons/StarEmpty-Icon.svg";
import StarFullIcon from "../assets/icons/StarFull-Icon.svg";
import { CollabAPI } from "../services/api.ts";
import "../styles/RatingControl.css";

interface RatingControlProps {
  projectId: number;
  initialAverage?: number;
  onAverageChange?: (value: number) => void;
}

const RatingControl: React.FC<RatingControlProps> = ({ projectId, initialAverage = 0, onAverageChange }) => {
  const [averageRating, setAverageRating] = useState<number>(initialAverage);
  const [userRating, setUserRating] = useState<number>(0);
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const displayedRating = useMemo(() => hoverRating ?? userRating, [hoverRating, userRating]);

  useEffect(() => {
    let isMounted = true;

    async function loadRating() {
      const response = await CollabAPI.getProjectRating(projectId);
      if (!isMounted) return;
      if (response.ok && response.data) {
        const averageValue = response.data.average_rating ?? response.data.average ?? 0;
        const currentUserRating =
          response.data.user_rating ?? response.data.current_user_rating ?? response.data.rating ?? 0;
        setAverageRating(averageValue);
        setUserRating(currentUserRating);
        onAverageChange?.(averageValue);
      }
    }

    loadRating();
    return () => {
      isMounted = false;
    };
  }, [projectId, onAverageChange]);

  useEffect(() => {
    setAverageRating(initialAverage);
  }, [initialAverage]);

  const handleRate = async (value: number) => {
    setIsSaving(true);
    setStatus(null);
    const result = await CollabAPI.rateProject(projectId, value);
    if (result.ok) {
      setUserRating(value);
      setStatus("Rating saved");
      const refreshed = await CollabAPI.getProjectRating(projectId);
      if (refreshed.ok && refreshed.data) {
        const averageValue = refreshed.data.average_rating ?? refreshed.data.average ?? value;
        const currentUserRating =
          refreshed.data.user_rating ?? refreshed.data.current_user_rating ?? refreshed.data.rating ?? value;
        setAverageRating(averageValue);
        setUserRating(currentUserRating);
        onAverageChange?.(averageValue);
      }
    } else {
      setStatus("Could not save rating");
    }
    setIsSaving(false);
  };

  const stars = Array.from({ length: 5 }, (_, index) => {
    const value = index + 1;
    const filled = value <= displayedRating;
    const Icon = filled ? StarFullIcon : StarEmptyIcon;

    return (
      <button
        key={value}
        type="button"
        className="rating-control__starButton"
        onMouseEnter={() => setHoverRating(value)}
        onMouseLeave={() => setHoverRating(null)}
        onClick={() => handleRate(value)}
        disabled={isSaving}
        aria-label={`Rate ${value} out of 5 stars`}
      >
        <img
          src={Icon}
          alt={filled ? "Filled star" : "Empty star"}
          className="rating-control__star"
        />
      </button>
    );
  });

  return (
    <div className="rating-control">
      <div className="rating-control__stars">{stars}</div>
      <div className="rating-control__info">
        <span className="rating-control__average">{averageRating.toFixed(1)}</span>
        <span className="rating-control__label">
          {hoverRating ? `You are rating ${hoverRating}/5` : `Your rating: ${userRating || "–"}`}
        </span>
      </div>
      {status && <p className="rating-control__status">{status}</p>}
    </div>
  );
};

export default RatingControl;