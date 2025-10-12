import { useState } from "react";
import { Modal } from "../Modal";
import { projectsAPI, Project } from "../../api/client";

interface NewProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectCreated: (project: Project) => void;
}

export const NewProjectModal = ({
  isOpen,
  onClose,
  onProjectCreated,
}: NewProjectModalProps) => {
  const [name, setName] = useState("");
  const [width, setWidth] = useState(1920);
  const [height, setHeight] = useState(1080);
  const [fps, setFps] = useState(24);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      setLoading(true);
      setError(null);

      try {
        const project = await projectsAPI.create({
          name: name.trim(),
          width,
          height,
          fps,
        });

        // Reset form
        setName("");
        setWidth(1920);
        setHeight(1080);
        setFps(24);

        // Notify parent component
        onProjectCreated(project);
        onClose();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create project");
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCancel = () => {
    // Reset form
    setName("");
    setWidth(1920);
    setHeight(1080);
    setFps(24);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="New Project" size="medium">
      <form className="modal-form" onSubmit={handleSubmit}>
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="project-name" className="form-label">
            Project Name
          </label>
          <input
            id="project-name"
            type="text"
            className="form-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter project name"
            required
            autoFocus
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="project-width" className="form-label">
            Width (pixels)
          </label>
          <input
            id="project-width"
            type="number"
            className="form-input"
            value={width}
            onChange={(e) => setWidth(Number(e.target.value))}
            min={512}
            max={7680}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="project-height" className="form-label">
            Height (pixels)
          </label>
          <input
            id="project-height"
            type="number"
            className="form-input"
            value={height}
            onChange={(e) => setHeight(Number(e.target.value))}
            min={512}
            max={4320}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="project-fps" className="form-label">
            FPS (Frames per second)
          </label>
          <input
            id="project-fps"
            type="number"
            className="form-input"
            value={fps}
            onChange={(e) => setFps(Number(e.target.value))}
            min={1}
            max={120}
            required
            disabled={loading}
          />
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCancel}
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Creating..." : "Create Project"}
          </button>
        </div>
      </form>
    </Modal>
  );
};

