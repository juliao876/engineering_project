import React from 'react';
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
        <img src={Logo} alt="uinside logo" className="navbar__logo" />
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
