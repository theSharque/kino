import { useState, useEffect } from "react";
import { Modal } from "../Modal";
import type { BackendHealth } from "../../api/client";
import { healthAPI } from "../../api/client";
import "./AboutModal.css";

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const BACKEND_URL = "http://localhost:8000";

export const AboutModal = ({ isOpen, onClose }: AboutModalProps) => {
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(
    null
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch backend health when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setError(null);

      healthAPI
        .check()
        .then((data) => {
          setBackendHealth(data);
          setLoading(false);
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : "Failed to connect to backend");
          setLoading(false);
        });
    }
  }, [isOpen]);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="About Kino" size="medium">
      <div className="about-content">
        <h1 className="about-logo">🎬 Kino</h1>
        <p className="about-version">Version 1.0.0</p>
        <p className="about-description">
          AI-powered video project management and frame generation system
        </p>

        <div className="about-tech">
          <h3>Technology Stack</h3>
          <ul>
            <li>React 19.1</li>
            <li>TypeScript</li>
            <li>Vite 7.1</li>
            <li>Python 3.12 Backend</li>
            <li>ComfyUI Integration</li>
          </ul>
        </div>

        {/* Backend Status */}
        <div className="about-backend-status">
          <h3>Backend Status</h3>
          {loading ? (
            <div className="status-loading">Checking backend...</div>
          ) : error ? (
            <div className="status-error">
              <span className="status-indicator status-offline">●</span>
              <span>Offline - {error}</span>
            </div>
          ) : backendHealth ? (
            <div className="status-online">
              <div className="status-row">
                <span className="status-indicator status-ok">●</span>
                <span className="status-label">Status:</span>
                <span className="status-value">
                  {backendHealth.status === "ok"
                    ? "Online"
                    : backendHealth.status}
                </span>
              </div>
              <div className="status-row">
                <span className="status-label">Service:</span>
                <span className="status-value">{backendHealth.service}</span>
              </div>
              <div className="status-row">
                <span className="status-label">Python:</span>
                <span className="status-value">
                  {backendHealth.python_version}
                </span>
              </div>
              <div className="status-row">
                <span className="status-label">CPU:</span>
                <span className="status-value">
                  {backendHealth.cpu_percent.toFixed(1)}%
                </span>
              </div>
              <div className="status-row">
                <span className="status-label">Memory:</span>
                <span className="status-value">
                  {backendHealth.memory_percent.toFixed(1)}%
                </span>
              </div>
              <div className="status-row">
                <span className="status-label">URL:</span>
                <span className="status-value status-url">{BACKEND_URL}</span>
              </div>
            </div>
          ) : null}
        </div>

        <div className="about-footer">
          <p>© 2025 Kino Project</p>
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
};
