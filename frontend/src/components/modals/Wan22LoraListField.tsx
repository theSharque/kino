import { useState, useEffect } from "react";
import type { ModelInfo } from "../../api/client";
import { modelsAPI } from "../../api/client";
import "./LoraListField.css";

interface LoraItem {
  lora_name: string;
  strength_model: number;
}

interface Wan22LoraListFieldProps {
  label: string;
  value: LoraItem[];
  onChange: (value: LoraItem[]) => void;
}

export const Wan22LoraListField = ({
  label,
  value,
  onChange,
}: Wan22LoraListFieldProps) => {
  const [availableLoras, setAvailableLoras] = useState<ModelInfo[]>([]);
  const [loadingLoras, setLoadingLoras] = useState(false);

  // Load available LoRA models
  useEffect(() => {
    const loadLoras = async () => {
      setLoadingLoras(true);
      try {
        const loras = await modelsAPI.getByCategory("Lora");
        setAvailableLoras(loras);
      } catch (err) {
        console.error("Failed to load LoRAs:", err);
      } finally {
        setLoadingLoras(false);
      }
    };

    loadLoras();
  }, []);

  const handleAdd = () => {
    const newLora: LoraItem = {
      lora_name: "",
      strength_model: 1.0,
    };
    onChange([...value, newLora]);
  };

  const handleRemove = (index: number) => {
    const newValue = value.filter((_, i) => i !== index);
    onChange(newValue);
  };

  const handleChange = (
    index: number,
    field: keyof LoraItem,
    newValue: any
  ) => {
    const updated = [...value];
    updated[index] = {
      ...updated[index],
      [field]: newValue,
    };
    onChange(updated);
  };

  return (
    <div className="lora-list-field">
      <div className="lora-list-header">
        <span className="lora-list-label">{label}</span>
        <button
          type="button"
          className="btn-add-lora"
          onClick={handleAdd}
          title="Add LoRA"
        >
          + Add LoRA
        </button>
      </div>

      {value.length === 0 ? (
        <div className="lora-list-empty">
          <p>No LoRAs added</p>
          <p className="lora-list-hint">
            Click "+ Add LoRA" to enhance generation
          </p>
        </div>
      ) : (
        <div className="lora-list-items">
          {value.map((lora, index) => (
            <div key={index} className="lora-item">
              <div className="lora-item-header">
                <span className="lora-item-number">LoRA #{index + 1}</span>
                <button
                  type="button"
                  className="btn-remove-lora"
                  onClick={() => handleRemove(index)}
                  title="Remove LoRA"
                >
                  ✕
                </button>
              </div>

              <div className="lora-item-fields-row">
                {/* LoRA Name Selection */}
                <div className="lora-field-name">
                  <select
                    className="form-input"
                    value={lora.lora_name}
                    onChange={(e) =>
                      handleChange(index, "lora_name", e.target.value)
                    }
                    disabled={loadingLoras}
                  >
                    <option value="">
                      {loadingLoras ? "Loading..." : "Select LoRA"}
                    </option>
                    {availableLoras.map((model) => (
                      <option key={model.filename} value={model.filename}>
                        {model.display_name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Strength Model */}
                <div className="lora-field-strength">
                  <label className="lora-strength-label">Strength</label>
                  <input
                    type="number"
                    className="form-input"
                    min="0"
                    max="2"
                    step="0.01"
                    value={lora.strength_model.toFixed(2)}
                    onChange={(e) =>
                      handleChange(
                        index,
                        "strength_model",
                        parseFloat(e.target.value) || 0
                      )
                    }
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
