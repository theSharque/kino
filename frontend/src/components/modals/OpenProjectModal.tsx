import { useState, useEffect } from "react";
import { Modal } from "../Modal";
import "./OpenProjectModal.css";

interface Project {
  id: number;
  name: string;
  width: number;
  height: number;
  fps: number;
  created_at: string;
  updated_at: string;
}

interface OpenProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (projectId: number) => void;
}

export const OpenProjectModal = ({
  isOpen,
  onClose,
  onSelect,
}: OpenProjectModalProps) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(
    null
  );

  // TODO: Fetch projects from API
  useEffect(() => {
    if (isOpen) {
      // Mock data for development
      setProjects([
        {
          id: 1,
          name: "Demo Project 1",
          width: 1920,
          height: 1080,
          fps: 30,
          created_at: "2025-10-11T10:00:00",
          updated_at: "2025-10-11T10:00:00",
        },
        {
          id: 2,
          name: "Demo Project 2",
          width: 1280,
          height: 720,
          fps: 24,
          created_at: "2025-10-11T11:00:00",
          updated_at: "2025-10-11T11:00:00",
        },
      ]);
    }
  }, [isOpen]);

  const handleOpen = () => {
    if (selectedProjectId !== null) {
      onSelect(selectedProjectId);
      setSelectedProjectId(null);
      onClose();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Open Project" size="large">
      <div className="project-list">
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

