import { useRef, useEffect, useCallback } from "react";
import type { Frame } from "../api/client";
import "./Timeline.css";

interface TimelineProps {
  frames: Frame[];
  currentFrameIndex: number;
  onFrameSelect: (index: number) => void;
}

// Helper to get frame thumbnail URL
const getFrameThumbnailUrl = (frame: Frame): string | undefined => {
  // TODO: Backend should provide thumbnail URL or serve images via API
  // For now, construct URL from frame path
  if (frame.path) {
    const filename = frame.path.split("/").pop();
    return `http://localhost:8000/data/frames/${filename}`;
  }
  return undefined;
};

export const Timeline = ({
  frames,
  currentFrameIndex,
  onFrameSelect,
}: TimelineProps) => {
  const timelineRef = useRef<HTMLDivElement>(null);
  const selectedFrameRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to selected frame
  useEffect(() => {
    if (selectedFrameRef.current && timelineRef.current) {
      selectedFrameRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "center",
      });
    }
  }, [currentFrameIndex]);

  const handleFrameClick = useCallback(
    (index: number) => {
      onFrameSelect(index);
    },
    [onFrameSelect]
  );

  return (
    <div className="timeline" ref={timelineRef}>
      <div className="timeline-scroll-container">
        {/* Render existing frames */}
        {frames.map((frame, index) => {
          const thumbnailUrl = getFrameThumbnailUrl(frame);
          return (
            <div
              key={frame.id}
              ref={index === currentFrameIndex ? selectedFrameRef : null}
              className={`timeline-frame ${index === currentFrameIndex ? "selected" : ""}`}
              onClick={() => handleFrameClick(index)}
            >
              {thumbnailUrl ? (
                <img
                  src={thumbnailUrl}
                  alt={`Frame ${index + 1}`}
                  className="timeline-frame-image"
                  loading="lazy"
                />
              ) : (
                <div className="timeline-frame-placeholder">
                  {index + 1}
                </div>
              )}
              <div className="timeline-frame-number">{index + 1}</div>
            </div>
          );
        })}

        {/* Virtual "add frame" card */}
        <div
          className="timeline-frame timeline-frame-add"
          title="Add new frame"
        >
          <div className="timeline-frame-add-icon">+</div>
        </div>
      </div>
    </div>
  );
};
