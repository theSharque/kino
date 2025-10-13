import { useState, useRef, useEffect } from "react";
import type { SystemMetrics } from "../hooks/useWebSocket";
import "./MenuBar.css";

interface MenuItem {
  label: string;
  action: () => void;
}

interface MenuBarProps {
  currentProjectName?: string;
  systemMetrics?: SystemMetrics | null;
  isConnected?: boolean;
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
  systemMetrics,
  isConnected,
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
      {/* Left section - Menu items */}
      <div className="menu-section">
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
              className={`menu-button ${
                activeMenu === "system" ? "active" : ""
              }`}
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
      </div>

      {/* Center section - Project name */}
      <div className="center-section">
        {currentProjectName && (
          <span className="project-name">{currentProjectName}</span>
        )}
      </div>

      {/* Right section - System metrics and app title */}
      <div className="right-section">
        {systemMetrics && (
          <span className="metrics">
            {systemMetrics.queue_size > 0 && (
              <span className="metric-item">
                Queue: {systemMetrics.queue_size}
              </span>
            )}
            {systemMetrics.current_task && (
              <span className="metric-item">
                Current: {Math.round(systemMetrics.current_task.progress)}%
              </span>
            )}
            <span className="metric-item">
              CPU: {systemMetrics.cpu_percent}%
            </span>
            {systemMetrics.gpu_available && (
              <>
                <span
                  className="metric-item"
                  title={`GPU Type: ${systemMetrics.gpu_type.toUpperCase()}`}
                >
                  {systemMetrics.gpu_type.toUpperCase()}:{" "}
                  {systemMetrics.gpu_percent}%
                </span>
                <span className="metric-item" title="GPU Memory Usage">
                  VRAM: {systemMetrics.gpu_memory_percent}%
                </span>
              </>
            )}
            <span className="metric-item">
              MEM: {systemMetrics.memory_percent}%
            </span>
          </span>
        )}

        <span className="app-title">KINO</span>

        {!isConnected && (
          <span className="connection-status offline">● Offline</span>
        )}
      </div>
    </div>
  );
};
