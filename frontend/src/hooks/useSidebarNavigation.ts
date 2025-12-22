import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { SidebarItemId } from "../components/Sidebar.tsx";

interface SidebarNavigationOptions {
  openSearch?: () => void;
}

const useSidebarNavigation = (options: SidebarNavigationOptions = {}) => {
  const navigate = useNavigate();
  const { openSearch } = options;

  return useCallback(
    (itemId: SidebarItemId) => {
      switch (itemId) {
        case "home":
          navigate("/discover");
          break;
        case "notifications":
          navigate("/notifications");
          break;
        case "profile":
          navigate("/profile");
          break;
        case "create":
          navigate("/projects/create");
          break;
        case "search":
          if (openSearch) {
            openSearch();
          } else {
            navigate("/discover");
          }
          break;
        case "settings":
          navigate("/settings");
          break;
        default:
          break;
      }
    },
    [navigate, openSearch],
  );
};

export default useSidebarNavigation;