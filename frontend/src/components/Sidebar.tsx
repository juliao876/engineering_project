import React from 'react';
import '../styles/Sidebar.css';
import Logo from '../assets/icons/Logo.svg';

export type SidebarItemId =
  | 'home'
  | 'notifications'
  | 'profile'
  | 'create'
  | 'logout'
  | 'search'
  | 'settings';

export interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeItem?: SidebarItemId;
  onLogout?: () => void | Promise<void>;
  onSelect?: (item: SidebarItemId) => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  activeItem,
  onLogout,
  onSelect,
}) => {
  const items: { id: SidebarItemId; label: string }[] = [
    { id: 'home',          label: 'Home' },
    { id: 'search',        label: 'Search' },
    { id: 'profile',       label: 'Profile' },
    { id: 'create',        label: 'Create' },
    { id: 'notifications', label: 'Notification' },
    { id: 'settings',      label: 'Settings' },
    { id: 'logout',        label: 'Log out' },
  ];

  const handleClick = (itemId: SidebarItemId) => {
    onSelect?.(itemId);

    if (itemId === 'logout') {
      onLogout?.();
    }

    if (itemId !== 'search') {
      onClose();
    }
  };

  return (
    <>
      {/* overlay */}
      <div
        className={`sidebar-overlay ${isOpen ? 'sidebar-overlay--visible' : ''}`}
        onClick={onClose}
        aria-hidden={!isOpen}
      />

      <aside
        className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}
        aria-hidden={!isOpen}
      >
        <div className="sidebar__header">
          <img src={Logo} alt="uinside logo" className="sidebar__logo" />
        </div>

        <nav className="sidebar__nav" aria-label="Main navigation">
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              className={
                'sidebar__item' +
                (item.id === activeItem ? ' sidebar__item--active' : '')
              }
              onClick={() => handleClick(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;