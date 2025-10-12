import { useRef, useEffect, useCallback } from 'react';
import './Timeline.css';

interface Frame {
  id: number;
  index: number;
  thumbnailUrl?: string;
  path?: string;
}

interface TimelineProps {
  frames: Frame[];
  currentFrameIndex: number;
  onFrameSelect: (index: number) => void;
}

export const Timeline = ({
  frames,
  currentFrameIndex,
  onFrameSelect
}: TimelineProps) => {
  const timelineRef = useRef<HTMLDivElement>(null);
  const selectedFrameRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to selected frame
  useEffect(() => {
    if (selectedFrameRef.current && timelineRef.current) {
      selectedFrameRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
        inline: 'center'
      });
    }
  }, [currentFrameIndex]);

  const handleFrameClick = useCallback((index: number) => {
    onFrameSelect(index);
  }, [onFrameSelect]);

  return (
    <div className="timeline" ref={timelineRef}>
      <div className="timeline-scroll-container">
        {frames.length > 0 ? (
          frames.map((frame) => (
            <div
              key={frame.id}
              ref={frame.index === currentFrameIndex ? selectedFrameRef : null}
              className={`timeline-frame ${frame.index === currentFrameIndex ? 'selected' : ''}`}
              onClick={() => handleFrameClick(frame.index)}
            >
              {frame.thumbnailUrl ? (
                <img
                  src={frame.thumbnailUrl}
                  alt={`Frame ${frame.index + 1}`}
                  className="timeline-frame-image"
                  loading="lazy"
                />
              ) : (
                <div className="timeline-frame-placeholder">
                  {frame.index + 1}
                </div>
              )}
              <div className="timeline-frame-number">
                {frame.index + 1}
              </div>
            </div>
          ))
        ) : (
          <div className="timeline-empty">
            <p>No frames available</p>
            <p className="timeline-hint">Create frames to see them here</p>
          </div>
        )}
      </div>
    </div>
  );
};

