import React, { useEffect, useState } from "react";
import "../styles/SearchOverlay.css";
import { AuthAPI, FollowAPI } from "../services/api.ts";

interface SearchOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToUser: (username: string) => void;
}

type SearchResultUser = {
  id: number;
  username: string;
  name?: string;
  family_name?: string;
};

const SearchOverlay: React.FC<SearchOverlayProps> = ({ isOpen, onClose, onNavigateToUser }) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [resultsReady, setResultsReady] = useState(false);
  const [currentUser, setCurrentUser] = useState<any | null>(null);
  const [followStates, setFollowStates] = useState<Record<string, boolean>>({});
  const [followLoading, setFollowLoading] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!showResults) return;
    const timeout = setTimeout(() => setResultsReady(true), 20);
    return () => clearTimeout(timeout);
  }, [showResults]);

  useEffect(() => {
    if (!isOpen) return;

    let isCancelled = false;

    const fetchCurrentUser = async () => {
      const response = await AuthAPI.me();
      if (!isCancelled) {
        setCurrentUser(response.ok ? response.data : null);
      }
    };

    fetchCurrentUser();

    return () => {
      isCancelled = true;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setResults([]);
      setError(null);
      setShowResults(false);
      setResultsReady(false);
      setFollowStates({});
      setFollowLoading({});
    }
  }, [isOpen]);

  useEffect(() => {
    let isCancelled = false;

    const loadFollowStatuses = async () => {
      if (!currentUser || results.length === 0) {
        setFollowStates({});
        return;
      }

      const entries = await Promise.all(
        results.map(async (user) => {
          if (user.username === currentUser.username) {
            return [user.username, false];
          }

          const response = await FollowAPI.getStatus(user.username);
          if (response.ok) {
            return [user.username, Boolean(response.data?.is_following)];
          }

          return [user.username, false];
        })
      );

      if (!isCancelled) {
        setFollowStates(Object.fromEntries(entries));
      }
    };

    loadFollowStatuses();

    return () => {
      isCancelled = true;
    };
  }, [results, currentUser]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    const response = await AuthAPI.searchUsers(query.trim());

    if (response.ok) {
      setResults(response.data?.results || []);
    } else {
      setError(response.data?.detail || "Could not search right now.");
      setResults([]);
    }

    setIsLoading(false);
    setShowResults(true);
  };

  const closeResults = () => {
    setResultsReady(false);
    setTimeout(() => setShowResults(false), 220);
  };

  const handleSelect = (username: string) => {
    onNavigateToUser(username);
    closeResults();
    onClose();
  };

  const handleToggleFollow = async (user: SearchResultUser) => {
    if (!currentUser || user.username === currentUser.username) return;

    const userId = Number(user.id);
    if (Number.isNaN(userId)) return;

    setFollowLoading((prev) => ({ ...prev, [user.username]: true }));
    setFollowStates((prev) => ({ ...prev, [user.username]: !prev[user.username] }));

    const response = await FollowAPI.toggleFollow(userId);

    if (!response.ok) {
      setFollowStates((prev) => ({ ...prev, [user.username]: !prev[user.username] }));
    }

    setFollowLoading((prev) => ({ ...prev, [user.username]: false }));
  };

  return (
    <>
      <div className={`search-bar ${isOpen ? "is-open" : ""}`}>
        <div className="search-bar__inner">
          <form className="search-bar__form" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Search by name, surname or username"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? "Searching..." : "Go"}
            </button>
            <button type="button" className="search-bar__close" onClick={onClose}>
              ×
            </button>
          </form>
        </div>
      </div>

      {showResults && (
        <div
          className="search-results__overlay"
          onClick={(event) => {
            if (event.target === event.currentTarget) {
              closeResults();
            }
          }}
        >
          <div className={`search-results ${resultsReady ? "is-open" : ""}`}>
            <div className="search-results__header">
              <h4>Search results</h4>
              <button type="button" onClick={closeResults} aria-label="Close results">
                ×
              </button>
            </div>

            {error && <p className="search-results__error">{error}</p>}

            {!error && results.length === 0 && !isLoading && (
              <p className="search-results__empty">No results yet. Try a different phrase.</p>
            )}

            <div className="search-results__list">
              {results.map((user) => {
                const isSelf = currentUser && user.username === currentUser.username;
                const isFollowing = followStates[user.username] ?? false;
                const isFollowButtonLoading = followLoading[user.username];

                return (
                  <div
                    key={user.id}
                    className="search-results__item"
                    role="button"
                    tabIndex={0}
                    onClick={() => handleSelect(user.username)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") handleSelect(user.username);
                    }}
                  >
                    <div className="search-results__content">
                      <div className="search-results__avatar">
                        {(user.name || user.username || "?")[0]}
                      </div>
                      <div className="search-results__details">
                        <p className="search-results__name">
                          {[user.name, user.family_name].filter(Boolean).join(" ") || user.username}
                        </p>
                        <p className="search-results__username">@{user.username}</p>
                      </div>
                    </div>

                    {currentUser && !isSelf && (
                      <button
                        type="button"
                        className={`search-results__followButton ${
                          isFollowing ? "is-following" : ""
                        }`}
                        onClick={(event) => {
                          event.stopPropagation();
                          handleToggleFollow(user);
                        }}
                        disabled={isFollowButtonLoading}
                      >
                        {isFollowButtonLoading
                          ? "Loading..."
                          : isFollowing
                          ? "Unfollow"
                          : "Follow"}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SearchOverlay;