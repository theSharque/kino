import { useState } from "react";
import { Modal } from "../Modal";

interface FindFrameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onFind: (frameNumber: number) => void;
  totalFrames: number;
}

export const FindFrameModal = ({
  isOpen,
  onClose,
  onFind,
  totalFrames,
}: FindFrameModalProps) => {
  const [frameNumber, setFrameNumber] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const num = parseInt(frameNumber, 10);
    if (!isNaN(num) && num >= 1 && num <= totalFrames) {
      onFind(num - 1); // Convert to 0-based index
      setFrameNumber("");
      onClose();
    }
  };

  const handleCancel = () => {
    setFrameNumber("");
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Find Frame" size="small">
      <form className="modal-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="frame-number" className="form-label">
            Frame Number (1 - {totalFrames})
          </label>
          <input
            id="frame-number"
            type="number"
            className="form-input"
            value={frameNumber}
            onChange={(e) => setFrameNumber(e.target.value)}
            placeholder="Enter frame number"
            min={1}
            max={totalFrames}
            required
            autoFocus
          />
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={handleCancel}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary">
            Go to Frame
          </button>
        </div>
      </form>
    </Modal>
  );
};

