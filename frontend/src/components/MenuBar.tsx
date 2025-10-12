import { useState, useRef, useEffect } from "react";
import "./MenuBar.css";

interface MenuItem {
  label: string;
  action: () => void;
}

interface MenuBarProps {
  currentProjectName?: string;
  onNewProject: () => void;
  onOpenProject: () => void;
  onFindFrame: () => void;
  onDeleteFrame: () => void;
  onEmergencyStop: () => void;
  onRestartServer: () => void;
  onAbout: () => void;
}

export const MenuBar = ({
  currentProjectName,
  onNewProject,
  onOpenProject,
  onFindFrame,
  onDeleteFrame,
  onEmergencyStop,
  onRestartServer,
  onAbout,
}: MenuBarProps) => {
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setActiveMenu(null);
      }
    };

    if (activeMenu) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [activeMenu]);

  const toggleMenu = (menuName: string) => {
    setActiveMenu(activeMenu === menuName ? null : menuName);
  };

  const handleMenuItemClick = (action: () => void) => {
    action();
    setActiveMenu(null);
  };

  const menus = {
    file: [
      { label: "New Project", action: onNewProject },
      { label: "Projects", action: onOpenProject },
    ],
    edit: [
      { label: "Find Frame", action: onFindFrame },
      { label: "Delete Frame", action: onDeleteFrame },
    ],
    system: [
      { label: "Emergency Stop", action: onEmergencyStop },
      { label: "Restart Server", action: onRestartServer },
    ],
    help: [{ label: "About", action: onAbout }],
  };

  return (
    <div className="menu-bar" ref={menuRef}>
      <div className="menu-items">
        {/* File Menu */}
        <div className="menu-item">
          <button
            className={`menu-button ${activeMenu === "file" ? "active" : ""}`}
            onClick={() => toggleMenu("file")}
          >
            File
          </button>
          {activeMenu === "file" && (
            <div className="menu-dropdown">
              {menus.file.map((item, index) => (
                <button
                  key={index}
                  className="menu-dropdown-item"
                  onClick={() => handleMenuItemClick(item.action)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Edit Menu */}
        <div className="menu-item">
          <button
            className={`menu-button ${activeMenu === "edit" ? "active" : ""}`}
            onClick={() => toggleMenu("edit")}
          >
            Edit
          </button>
          {activeMenu === "edit" && (
            <div className="menu-dropdown">
              {menus.edit.map((item, index) => (
                <button
                  key={index}
                  className="menu-dropdown-item"
                  onClick={() => handleMenuItemClick(item.action)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* System Menu */}
        <div className="menu-item">
          <button
            className={`menu-button ${activeMenu === "system" ? "active" : ""}`}
            onClick={() => toggleMenu("system")}
          >
            System
          </button>
          {activeMenu === "system" && (
            <div className="menu-dropdown">
              {menus.system.map((item, index) => (
                <button
                  key={index}
                  className="menu-dropdown-item"
                  onClick={() => handleMenuItemClick(item.action)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Help Menu */}
        <div className="menu-item">
          <button
            className={`menu-button ${activeMenu === "help" ? "active" : ""}`}
            onClick={() => toggleMenu("help")}
          >
            Help
          </button>
          {activeMenu === "help" && (
            <div className="menu-dropdown">
              {menus.help.map((item, index) => (
                <button
                  key={index}
                  className="menu-dropdown-item"
                  onClick={() => handleMenuItemClick(item.action)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {currentProjectName && (
        <div className="project-name-display">{currentProjectName}</div>
      )}

      <div className="menu-title">Kino</div>
    </div>
  );
};
