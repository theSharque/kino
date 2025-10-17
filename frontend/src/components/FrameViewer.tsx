import { useState, useCallback } from 'react';
import './FrameViewer.css';

interface FrameViewerProps {
  currentFrameIndex: number;
  totalFrames: number;
  fps: number;
  isPlaying: boolean;
  onFrameChange: (index: number) => void;
  onPlayPause: () => void;
  frameImageUrl?: string;
  // Variant support
  currentVariantIndex?: number;
  totalVariants?: number;
  onVariantChange?: (variantIndex: number) => void;
}

export const FrameViewer = ({
  currentFrameIndex,
  totalFrames,
  fps,
  isPlaying,
  onFrameChange,
  onPlayPause,
  frameImageUrl,
  currentVariantIndex = 0,
  totalVariants = 1,
  onVariantChange
}: FrameViewerProps) => {
  // Navigate to first frame
  const handleFirst = useCallback(() => {
    onFrameChange(0);
  }, [onFrameChange]);

  // Navigate to previous frame
  const handlePrevious = useCallback(() => {
    if (currentFrameIndex > 0) {
      onFrameChange(currentFrameIndex - 1);
    }
  }, [currentFrameIndex, onFrameChange]);

  // Navigate to next frame
  const handleNext = useCallback(() => {
    if (currentFrameIndex < totalFrames - 1) {
      onFrameChange(currentFrameIndex + 1);
    }
  }, [currentFrameIndex, totalFrames, onFrameChange]);

  // Navigate to last frame
  const handleLast = useCallback(() => {
    onFrameChange(totalFrames - 1);
  }, [totalFrames, onFrameChange]);

  // Variant navigation handlers
  const handlePreviousVariant = useCallback(() => {
    if (onVariantChange && currentVariantIndex > 0) {
      onVariantChange(currentVariantIndex - 1);
    }
  }, [currentVariantIndex, onVariantChange]);

  const handleNextVariant = useCallback(() => {
    if (onVariantChange && currentVariantIndex < totalVariants - 1) {
      onVariantChange(currentVariantIndex + 1);
    }
  }, [currentVariantIndex, totalVariants, onVariantChange]);

  return (
    <div className="frame-viewer">
      {/* Main frame display area */}
      <div className="frame-display">
        {frameImageUrl ? (
          <img
            src={frameImageUrl}
            alt={`Frame ${currentFrameIndex + 1}`}
            className="frame-image"
          />
        ) : (
          <div className="frame-placeholder">
            <p>No frame selected</p>
            <p className="frame-info">Frame {currentFrameIndex + 1} of {totalFrames}</p>
          </div>
        )}
        
        {/* Variant controls overlay */}
        {totalVariants > 1 && onVariantChange && (
          <div className="variant-controls">
            <button
              onClick={handlePreviousVariant}
              disabled={currentVariantIndex === 0}
              className="variant-button"
              title="Previous variant"
            >
              ◀
            </button>
            
            <div className="variant-counter">
              Variant {currentVariantIndex + 1} / {totalVariants}
            </div>
            
            <button
              onClick={handleNextVariant}
              disabled={currentVariantIndex >= totalVariants - 1}
              className="variant-button"
              title="Next variant"
            >
              ▶
            </button>
          </div>
        )}
      </div>

      {/* Control panel */}
      <div className="control-panel">
        <button
          onClick={handleFirst}
          disabled={currentFrameIndex === 0}
          className="control-button"
          title="Go to first frame"
        >
          ⏮
        </button>

        <button
          onClick={handlePrevious}
          disabled={currentFrameIndex === 0}
          className="control-button"
          title="Previous frame"
        >
          ⏪
        </button>

        <button
          onClick={onPlayPause}
          className="control-button play-button"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>

        <button
          onClick={handleNext}
          disabled={currentFrameIndex >= totalFrames - 1}
          className="control-button"
          title="Next frame"
        >
          ⏩
        </button>

        <button
          onClick={handleLast}
          disabled={currentFrameIndex >= totalFrames - 1}
          className="control-button"
          title="Go to last frame"
        >
          ⏭
        </button>

        <div className="frame-counter">
          {currentFrameIndex + 1} / {totalFrames}
          <span className="fps-info">({fps} FPS)</span>
        </div>
      </div>
    </div>
  );
};

