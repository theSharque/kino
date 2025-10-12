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
}

export const FrameViewer = ({
  currentFrameIndex,
  totalFrames,
  fps,
  isPlaying,
  onFrameChange,
  onPlayPause,
  frameImageUrl
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

