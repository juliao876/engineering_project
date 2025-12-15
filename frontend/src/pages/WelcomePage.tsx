import React, { useEffect, useMemo, useState } from "react";
import "../styles/tokens.css";
import "../styles/WelcomePage.css";

import backgroundCircle from "../assets/images/Circle.png";
import logo from "../assets/icons/Logo.svg";

import { ButtonM } from "../components/ButtonPresets.tsx";

export interface WelcomePageProps {
  onRegisterClick?: () => void;
  onLoginClick?: () => void;
}

const WelcomePage: React.FC<WelcomePageProps> = ({ onRegisterClick, onLoginClick }) => {
  const [showActions, setShowActions] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShowActions(true), 800);
    return () => clearTimeout(timer);
  }, []);

  const heroClasses = useMemo(
    () => `welcome__hero ${showActions ? "is-condensed" : ""}`,
    [showActions]
  );

  const actionsClasses = useMemo(
    () => `welcome__actions ${showActions ? "is-visible" : ""}`,
    [showActions]
  );

  return (
    <div className="welcome">
      <div className="welcome__background">
        <img src={backgroundCircle} alt="Colorful gradient halo" />
      </div>

      <main className="welcome__content" aria-live="polite">
        <div className={heroClasses}>
          <h1 className="welcome__title">Welcome to</h1>
          <div className="welcome__brand">
            <img src={logo} alt="uinside" />
          </div>
        </div>

        <div className={actionsClasses}>
          <ButtonM onClick={onRegisterClick}>Register</ButtonM>
          <ButtonM onClick={onLoginClick}>Log in</ButtonM>
        </div>
      </main>
    </div>
  );
};

export default WelcomePage;