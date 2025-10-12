import { Modal } from "../Modal";

interface DeleteFrameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  frameNumber: number;
}

export const DeleteFrameModal = ({
  isOpen,
  onClose,
  onConfirm,
  frameNumber,
}: DeleteFrameModalProps) => {
  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete Frame" size="small">
      <div className="modal-form">
        <div className="warning-message">
          <p>Are you sure you want to delete Frame {frameNumber}?</p>
          <p className="warning-text">This action cannot be undone.</p>
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="btn btn-danger" onClick={handleConfirm}>
            Delete Frame
          </button>
        </div>
      </div>
    </Modal>
  );
};

