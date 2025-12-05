import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { FigmaAPI } from "../services/api.ts";
import "../styles/FigmaCallbackPage.css";
import { loadUserSettings } from "../services/userSettings.ts";

const FigmaCallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [status, setStatus] = useState("Connecting your Figma account...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const statusParam = params.get("status");
    const code = params.get("code");
    const state = params.get("state");
    const reason = params.get("reason");

    const handleSuccess = (message: string) => {
      setStatus(message);
      setError(null);
      localStorage.setItem("figma_connected", "true");
      localStorage.removeItem("figma_oauth_state");
      setTimeout(() => navigate("/projects/create?figma=connected"), 1000);
    };

    const handleError = (message: string) => {
      setError(message);
      setStatus("Could not connect to Figma.");
      setTimeout(() => navigate("/projects/create?figma=error"), 1200);
    };

    if (statusParam) {
      if (statusParam === "connected") {
        handleSuccess("Figma connected! Redirecting you back...");
        return;
      }
      const message =
        reason === "oauth_failed"
          ? "Figma did not accept the authorization code."
          : reason === "unexpected_error"
            ? "Unexpected error while connecting to Figma."
            : reason || "Failed to connect your Figma account.";
      handleError(message);
      return;
    }

    if (!code) {
      handleError("Missing authorization code in callback URL.");
      return;
    }

    const storedState = localStorage.getItem("figma_oauth_state");
    if (storedState && state && storedState !== state) {
      handleError("State mismatch. Please start the Figma connect flow again.");
      return;
    }

    const connect = async () => {
      const settings = loadUserSettings();
      const response = await FigmaAPI.connect({
        code,
        state,
        clientId: settings.figmaClientId,
        clientSecret: settings.figmaClientSecret,
      });
      console.log("[Figma] Connect response", response);

      if (response.ok) {
        handleSuccess("Figma connected! Redirecting you back...");
      } else {
        const message = response.data?.detail || "Failed to connect your Figma account.";
        console.error("[Figma] Connect failed", message);
        handleError(message);
      }
    };

    void connect();
  }, [navigate, location.search]);

  return (
    <div className="figma-callback">
      <div className="figma-callback__card">
        <h1>Figma OAuth</h1>
        <p className="figma-callback__status">{status}</p>
        {error && <p className="figma-callback__error">{error}</p>}
        <button
          type="button"
          className="figma-callback__button"
          onClick={() => navigate("/projects/create")}
        >
          Back to create project
        </button>
      </div>
    </div>
  );
};

export default FigmaCallbackPage;