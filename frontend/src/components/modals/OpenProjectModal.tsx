import { useState, useEffect } from "react";
import { Modal } from "../Modal";
import type { Project } from "../../api/client";
import { projectsAPI } from "../../api/client";
import "./OpenProjectModal.css";

interface OpenProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectSelected: (project: Project) => void;
}

export const OpenProjectModal = ({
  isOpen,
  onClose,
  onProjectSelected,
}: OpenProjectModalProps) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null
  );

  // Fetch projects from API when modal opens
  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      setError(null);
      setSelectedProjectId(null);

      projectsAPI
        .getAll()
        .then((fetchedProjects) => {
          setProjects(fetchedProjects);
          setLoading(false);
        })
        .catch((err) => {
          setError(err instanceof Error ? err.message : "Failed to load projects");
          setLoading(false);
        });
    }
  }, [isOpen]);

  const handleOpen = () => {
    if (selectedProjectId !== null) {
      const selectedProject = projects.find((p) => p.id === selectedProjectId);
      if (selectedProject) {
        onProjectSelected(selectedProject);
        setSelectedProjectId(null);
        onClose();
      }
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Open Project" size="large">
      <div className="project-list">
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}

        {loading ? (
          <div className="loading">Loading projects...</div>
        ) : projects.length > 0 ? (
          <div className="projects-grid">
            {projects.map((project) => (
              <div
                key={project.id}
                className={`project-card ${selectedProjectId === project.id ? "selected" : ""}`}
                onClick={() => setSelectedProjectId(project.id)}
              >
                <h3 className="project-name">{project.name}</h3>
                <div className="project-details">
                  <span>
                    {project.width} × {project.height}
                  </span>
                  <span>{project.fps} FPS</span>
                </div>
                <div className="project-date">
                  Created: {new Date(project.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No projects found</p>
            <p className="empty-hint">Create a new project to get started</p>
          </div>
        )}
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleOpen}
          disabled={selectedProjectId === null}
        >
          Open Project
        </button>
      </div>
    </Modal>
  );
};

