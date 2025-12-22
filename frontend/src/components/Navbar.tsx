import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Navbar.css';
import Logo from '../assets/icons/Logo.svg';
import SidebarIcon from '../assets/icons/SidebarIcon.svg';

interface NavbarProps {
  onMenuClick: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onMenuClick }) => {
  return (
    <header className="navbar">
      <div className="navbar__brand">
        <Link to="/discover" aria-label="Go to Discover">
          <img src={Logo} alt="uinside logo" className="navbar__logo" />
        </Link>
      </div>

      <div className="navbar__actions">
        <button
          type="button"
          className="navbar__menuButton"
          onClick={onMenuClick}
          aria-label="Open menu"
        >
          <img src={SidebarIcon} alt="Menu icon" className="navbar__menuIcon" />
        </button>
      </div>
    </header>
  );
};

export default Navbar;