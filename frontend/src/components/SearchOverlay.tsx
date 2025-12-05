import React, { useEffect, useState } from "react";
import "../styles/SearchOverlay.css";
import { AuthAPI } from "../services/api.ts";

interface SearchOverlayProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateToUser: (username: string) => void;
}

const SearchOverlay: React.FC<SearchOverlayProps> = ({ isOpen, onClose, onNavigateToUser }) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [resultsReady, setResultsReady] = useState(false);

  useEffect(() => {
    if (!showResults) return;
    const timeout = setTimeout(() => setResultsReady(true), 20);
    return () => clearTimeout(timeout);
  }, [showResults]);

  useEffect(() => {
    if (!isOpen) {
      setQuery("");
      setResults([]);
      setError(null);
      setShowResults(false);
      setResultsReady(false);
    }
  }, [isOpen]);

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
              {results.map((user) => (
                <button
                  key={user.id}
                  type="button"
                  className="search-results__item"
                  onClick={() => handleSelect(user.username)}
                >
                  <div className="search-results__avatar">{(user.name || user.username || "?")[0]}</div>
                  <div>
                    <p className="search-results__name">
                      {[user.name, user.family_name].filter(Boolean).join(" ") || user.username}
                    </p>
                    <p className="search-results__username">@{user.username}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default SearchOverlay;
