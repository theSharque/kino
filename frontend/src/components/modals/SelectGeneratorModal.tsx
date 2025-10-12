import { useState, useEffect } from "react";
import { Modal } from "../Modal";
import type { PluginInfo } from "../../api/client";
import { generatorAPI } from "../../api/client";
import "./SelectGeneratorModal.css";

interface SelectGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (plugin: PluginInfo) => void;
}

export const SelectGeneratorModal = ({
  isOpen,
  onClose,
  onSelect,
}: SelectGeneratorModalProps) => {
  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch plugins from API when modal opens
  useEffect(() => {
    if (isOpen) {
      loadPlugins();
    }
  }, [isOpen]);

  const loadPlugins = async () => {
    setLoading(true);
    setError(null);

    try {
      const fetchedPlugins = await generatorAPI.getPlugins();
      setPlugins(fetchedPlugins);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load generator plugins"
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePluginSelect = (plugin: PluginInfo) => {
    onSelect(plugin);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Select Generator"
      size="medium"
    >
      <div className="generator-list">
        {error && (
          <div className="error-message">
            <span className="error-icon">⚠</span>
            {error}
          </div>
        )}

        {loading ? (
          <div className="loading">Loading generators...</div>
        ) : plugins.length > 0 ? (
          <div className="generators-grid">
            {plugins.map((plugin) => (
              <div
                key={plugin.name}
                className="generator-card"
                onClick={() => handlePluginSelect(plugin)}
              >
                <div className="generator-icon">🎨</div>
                <h3 className="generator-name">{plugin.name.toUpperCase()}</h3>
                <p className="generator-description">{plugin.description}</p>
                <div className="generator-meta">
                  <span className="generator-version">v{plugin.version}</span>
                  <span className="generator-type">{plugin.model_type}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>No generators available</p>
            <p className="empty-hint">Please check backend configuration</p>
          </div>
        )}
      </div>

      <div className="form-actions">
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          Cancel
        </button>
      </div>
    </Modal>
  );
};
