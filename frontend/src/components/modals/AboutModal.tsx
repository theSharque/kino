import { Modal } from "../Modal";
import "./AboutModal.css";

interface AboutModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AboutModal = ({ isOpen, onClose }: AboutModalProps) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="About Kino" size="small">
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

