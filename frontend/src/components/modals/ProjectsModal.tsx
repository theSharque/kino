import { useState, useEffect } from "react";
import { Modal } from "../Modal";
import type { Project } from "../../api/client";
import { projectsAPI } from "../../api/client";
import "./ProjectsModal.css";

interface ProjectsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectSelected: (project: Project) => void;
}

export const ProjectsModal = ({
  isOpen,
  onClose,
  onProjectSelected,
}: ProjectsModalProps) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedProjectIds, setSelectedProjectIds] = useState<Set<number>>(
    new Set()
  );
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // Fetch projects from API when modal opens
  useEffect(() => {
    if (isOpen) {
      loadProjects();
    }
  }, [isOpen]);

  const loadProjects = () => {
    setLoading(true);
    setError(null);
    setSelectedProjectIds(new Set());

    projectsAPI
      .getAll()
      .then((fetchedProjects) => {
        setProjects(fetchedProjects);
        setLoading(false);
      })
      .catch((err) => {
        setError(
          err instanceof Error ? err.message : "Failed to load projects"
        );
        setLoading(false);
      });
  };

  const handleProjectClick = (project: Project) => {
    // Open project immediately on card click
    onProjectSelected(project);
    setSelectedProjectIds(new Set());
    onClose();
  };

  const handleCheckboxClick = (e: React.MouseEvent, projectId: number) => {
    e.stopPropagation(); // Prevent card click
    setSelectedProjectIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(projectId)) {
        newSet.delete(projectId);
      } else {
        newSet.add(projectId);
      }
      return newSet;
    });
  };

  const handleDeleteClick = () => {
    if (selectedProjectIds.size > 0) {
      setShowDeleteConfirm(true);
    }
  };

  const handleConfirmDelete = async () => {
    setDeleting(true);
    setError(null);

    try {
      // Delete all selected projects
      await Promise.all(
        Array.from(selectedProjectIds).map((id) => projectsAPI.delete(id))
      );

      // Reload projects list
      setShowDeleteConfirm(false);
      setDeleting(false);
      loadProjects();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete projects"
      );
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Projects" size="large">
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
                className={`project-card ${
                  selectedProjectIds.has(project.id) ? "selected" : ""
                }`}
                onClick={() => handleProjectClick(project)}
              >
                <div
                  className="projects-checkbox"
                  onClick={(e) => handleCheckboxClick(e, project.id)}
                >
                  <input
                    type="checkbox"
                    checked={selectedProjectIds.has(project.id)}
                    onChange={() => {}} // Controlled by handleCheckboxClick
                  />
                </div>
                <h3 className="projects-card-name">{project.name}</h3>
                <div className="projects-details">
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

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="delete-confirm-overlay">
          <div className="delete-confirm-dialog">
            <h3>Confirm Deletion</h3>
            <p>
              Are you sure you want to delete {selectedProjectIds.size}{" "}
              project(s)?
            </p>
            <p className="delete-confirm-warning">
              This action will also delete all frames associated with the
              selected projects and cannot be undone.
            </p>
            <div className="delete-confirm-actions">
              <button
                className="btn btn-secondary"
                onClick={handleCancelDelete}
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={handleConfirmDelete}
                disabled={deleting}
              >
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Close
        </button>
        {selectedProjectIds.size > 0 && (
          <button
            type="button"
            className="btn btn-danger"
            onClick={handleDeleteClick}
          >
            Delete Selected ({selectedProjectIds.size})
          </button>
        )}
      </div>
    </Modal>
  );
};
