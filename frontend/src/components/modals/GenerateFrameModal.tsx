import { useState, useEffect } from "react";
import { Modal } from "../Modal";
import type { PluginInfo, ModelInfo } from "../../api/client";
import { modelsAPI } from "../../api/client";
import { LoraListField } from "./LoraListField";
import "./GenerateFrameModal.css";

interface GenerateFrameModalProps {
  isOpen: boolean;
  onClose: () => void;
  plugin: PluginInfo | null;
  projectId: number | null;
  onGenerate: (pluginName: string, parameters: Record<string, any>) => void;
}

export const GenerateFrameModal = ({
  isOpen,
  onClose,
  plugin,
  projectId,
  onGenerate,
}: GenerateFrameModalProps) => {
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [modelsByCategory, setModelsByCategory] = useState<
    Record<string, ModelInfo[]>
  >({});
  const [loadingModels, setLoadingModels] = useState<Record<string, boolean>>(
    {}
  );

  // Load models for model_selection type parameters
  useEffect(() => {
    if (!isOpen || !plugin) return;

    const loadModels = async () => {
      for (const [paramName, param] of Object.entries(plugin.parameters)) {
        if (param.type === "model_selection" && param.category) {
          const category = param.category;

          // Skip if already loaded
          if (modelsByCategory[category]) continue;

          setLoadingModels((prev) => ({ ...prev, [category]: true }));

          try {
            const models = await modelsAPI.getByCategory(category);
            setModelsByCategory((prev) => ({ ...prev, [category]: models }));
          } catch (err) {
            console.error(`Failed to load models for ${category}:`, err);
          } finally {
            setLoadingModels((prev) => ({ ...prev, [category]: false }));
          }
        }
      }
    };

    loadModels();
  }, [isOpen, plugin]);

  const handleInputChange = (paramName: string, value: any) => {
    setParameters((prev) => ({
      ...prev,
      [paramName]: value,
    }));
    // Clear error for this field
    if (errors[paramName]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[paramName];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    if (!plugin || !projectId) return false;

    const newErrors: Record<string, string> = {};

    // Check required fields
    Object.entries(plugin.parameters).forEach(([paramName, param]) => {
      if (param.required && !parameters[paramName]) {
        newErrors[paramName] = "This field is required";
      }

      // Validate number ranges
      if (
        param.type === "integer" ||
        param.type === "number" ||
        param.type === "float"
      ) {
        const value = parameters[paramName];
        if (value !== undefined && value !== "") {
          const numValue = Number(value);
          if (isNaN(numValue)) {
            newErrors[paramName] = "Must be a number";
          } else {
            if (param.min !== undefined && numValue < param.min) {
              newErrors[paramName] = `Must be at least ${param.min}`;
            }
            if (param.max !== undefined && numValue > param.max) {
              newErrors[paramName] = `Must be at most ${param.max}`;
            }
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!plugin || !projectId) {
      return;
    }

    if (!validateForm()) {
      return;
    }

    // Prepare parameters with defaults
    const finalParameters: Record<string, any> = { ...parameters };

    // Add defaults for missing optional parameters
    Object.entries(plugin.parameters).forEach(([paramName, param]) => {
      if (!param.required && finalParameters[paramName] === undefined) {
        if (param.default !== undefined) {
          finalParameters[paramName] = param.default;
        }
      }
      // Convert to proper types
      if (param.type === "integer" && finalParameters[paramName]) {
        finalParameters[paramName] = parseInt(finalParameters[paramName], 10);
      }
      if (
        (param.type === "number" || param.type === "float") &&
        finalParameters[paramName]
      ) {
        finalParameters[paramName] = parseFloat(finalParameters[paramName]);
      }
    });

    // Add project_id to parameters
    finalParameters.project_id = projectId;

    onGenerate(plugin.name, finalParameters);
    setParameters({});
    setErrors({});
    onClose();
  };

  const handleCancel = () => {
    setParameters({});
    setErrors({});
    onClose();
  };

  if (!plugin) {
    return null;
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleCancel}
      title={`Generate with ${plugin.name.toUpperCase()}`}
      size="large"
    >
      <form onSubmit={handleSubmit} className="generate-form">
        <div className="plugin-info">
          <p className="plugin-description">{plugin.description}</p>
        </div>

        <div className="form-fields">
          {Object.entries(plugin.parameters).map(
            ([paramName, param], index, array) => {
              // Skip height if we're grouping it with width
              if (paramName === "height") {
                const widthExists = array.some(([name]) => name === "width");
                if (widthExists) return null;
              }

              // Check if we should render width and height together
              const isWidth = paramName === "width";
              const heightParam = isWidth
                ? array.find(([name]) => name === "height")
                : null;

              if (isWidth && heightParam) {
                const [heightName, heightInfo] = heightParam;
                return (
                  <div key="dimensions" className="form-field-row">
                    {/* Width field */}
                    <div className="form-field-compact">
                      <label htmlFor="width" className="form-label">
                        WIDTH
                        {param.required && <span className="required">*</span>}
                      </label>
                      <input
                        id="width"
                        type="number"
                        className={`form-input ${errors.width ? "error" : ""}`}
                        value={parameters.width ?? ""}
                        onChange={(e) =>
                          handleInputChange("width", e.target.value)
                        }
                        placeholder={param.default?.toString() || ""}
                        min={param.min}
                        max={param.max}
                      />
                      <div className="field-info">
                        <span className="field-description">
                          {param.description}
                        </span>
                        {param.default !== undefined && (
                          <span className="field-default">
                            Default: {param.default}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Height field */}
                    <div className="form-field-compact">
                      <label htmlFor="height" className="form-label">
                        HEIGHT
                        {heightInfo.required && (
                          <span className="required">*</span>
                        )}
                      </label>
                      <input
                        id="height"
                        type="number"
                        className={`form-input ${errors.height ? "error" : ""}`}
                        value={parameters.height ?? ""}
                        onChange={(e) =>
                          handleInputChange("height", e.target.value)
                        }
                        placeholder={heightInfo.default?.toString() || ""}
                        min={heightInfo.min}
                        max={heightInfo.max}
                      />
                      <div className="field-info">
                        <span className="field-description">
                          {heightInfo.description}
                        </span>
                        {heightInfo.default !== undefined && (
                          <span className="field-default">
                            Default: {heightInfo.default}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              }

              return (
                <div key={paramName} className="form-field">
                  {/* Label for most fields, but not for lora_list (it has its own header) */}
                  {param.type !== "lora_list" && (
                    <label htmlFor={paramName} className="form-label">
                      {paramName.replace(/_/g, " ").toUpperCase()}
                      {param.required && <span className="required">*</span>}
                    </label>
                  )}

                  {param.type === "lora_list" && param.item_schema ? (
                    <LoraListField
                      itemSchema={param.item_schema}
                      value={parameters[paramName] || []}
                      onChange={(value) => handleInputChange(paramName, value)}
                    />
                  ) : param.type === "model_selection" && param.category ? (
                    <select
                      id={paramName}
                      className={`form-input ${
                        errors[paramName] ? "error" : ""
                      }`}
                      value={parameters[paramName] || ""}
                      onChange={(e) =>
                        handleInputChange(paramName, e.target.value)
                      }
                      disabled={loadingModels[param.category]}
                    >
                      <option value="">
                        {loadingModels[param.category]
                          ? "Loading models..."
                          : "Select a model"}
                      </option>
                      {modelsByCategory[param.category]?.map((model) => (
                        <option key={model.filename} value={model.filename}>
                          {model.display_name}
                        </option>
                      ))}
                    </select>
                  ) : param.type === "selection" && param.options ? (
                    <select
                      id={paramName}
                      className={`form-input ${
                        errors[paramName] ? "error" : ""
                      }`}
                      value={parameters[paramName] || param.default || ""}
                      onChange={(e) =>
                        handleInputChange(paramName, e.target.value)
                      }
                    >
                      {param.options.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  ) : param.type === "string" &&
                    (paramName.includes("prompt") ||
                      param.example?.length > 50) ? (
                    <textarea
                      id={paramName}
                      className={`form-textarea ${
                        errors[paramName] ? "error" : ""
                      }`}
                      value={parameters[paramName] || ""}
                      onChange={(e) =>
                        handleInputChange(paramName, e.target.value)
                      }
                      placeholder={param.example || param.description}
                      rows={3}
                    />
                  ) : param.type === "string" ? (
                    <input
                      id={paramName}
                      type="text"
                      className={`form-input ${
                        errors[paramName] ? "error" : ""
                      }`}
                      value={parameters[paramName] || ""}
                      onChange={(e) =>
                        handleInputChange(paramName, e.target.value)
                      }
                      placeholder={param.example || param.description}
                    />
                  ) : param.type === "integer" ||
                    param.type === "number" ||
                    param.type === "float" ? (
                    <input
                      id={paramName}
                      type="number"
                      className={`form-input ${
                        errors[paramName] ? "error" : ""
                      }`}
                      value={parameters[paramName] ?? ""}
                      onChange={(e) =>
                        handleInputChange(paramName, e.target.value)
                      }
                      placeholder={param.default?.toString() || ""}
                      min={param.min}
                      max={param.max}
                      step={param.type === "integer" ? 1 : 0.01}
                    />
                  ) : (
                    <input
                      id={paramName}
                      type="text"
                      className={`form-input ${
                        errors[paramName] ? "error" : ""
                      }`}
                      value={parameters[paramName] || ""}
                      onChange={(e) =>
                        handleInputChange(paramName, e.target.value)
                      }
                      placeholder={param.description}
                    />
                  )}

                  {/* Field info for all types except lora_list */}
                  {param.type !== "lora_list" && (
                    <div className="field-info">
                      <span className="field-description">
                        {param.description}
                      </span>
                      {errors[paramName] && (
                        <span className="field-error">{errors[paramName]}</span>
                      )}
                      {param.default !== undefined && !param.required && (
                        <span className="field-default">
                          Default: {param.default.toString()}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            }
          )}
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCancel}
          >
            Cancel
          </button>
          <button type="submit" className="btn btn-primary">
            Generate
          </button>
        </div>
      </form>
    </Modal>
  );
};
