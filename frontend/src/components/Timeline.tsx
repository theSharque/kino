import { useRef, useEffect, useCallback, useState } from "react";
import type { Frame } from "../api/client";
import { getFrameImageUrl } from "../config/constants";
import { ContextMenu } from "./ContextMenu";
import "./Timeline.css";

interface TimelineProps {
  frames: Frame[];
  currentFrameIndex: number;
  onFrameSelect: (index: number) => void;
  onAddFrame: () => void;
  onRegenerateFrame?: (frameId: number, frameIndex: number) => void;
  onDeleteFrame?: (frameId: number, frameIndex: number) => void;
  imageKeys?: Map<number, number>; // Cache-busting timestamps for preview updates
}

// Helper to get frame thumbnail URL with optional cache-busting
const getFrameThumbnailUrl = (
  frame: Frame,
  imageKeys?: Map<number, number>
): string | undefined => {
  if (!frame.path) return undefined;
  const baseUrl = getFrameImageUrl(frame.path);
  const timestamp = imageKeys?.get(frame.id);
  return timestamp ? `${baseUrl}?t=${timestamp}` : baseUrl;
};

export const Timeline = ({
  frames,
  currentFrameIndex,
  onFrameSelect,
  onAddFrame,
  onRegenerateFrame,
  onDeleteFrame,
  imageKeys,
}: TimelineProps) => {
  const timelineRef = useRef<HTMLDivElement>(null);
  const selectedFrameRef = useRef<HTMLDivElement>(null);

  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    frameId: number;
    frameIndex: number;
  } | null>(null);

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

  const handleContextMenu = useCallback(
    (event: React.MouseEvent, frameId: number, frameIndex: number) => {
      event.preventDefault();
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        frameId,
        frameIndex,
      });
    },
    []
  );

  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  const handleRegenerateClick = useCallback(() => {
    if (contextMenu && onRegenerateFrame) {
      onRegenerateFrame(contextMenu.frameId, contextMenu.frameIndex);
    }
  }, [contextMenu, onRegenerateFrame]);

  const handleDeleteClick = useCallback(() => {
    if (contextMenu && onDeleteFrame) {
      onDeleteFrame(contextMenu.frameId, contextMenu.frameIndex);
    }
  }, [contextMenu, onDeleteFrame]);

  return (
    <div className="timeline" ref={timelineRef}>
      <div className="timeline-scroll-container">
        {/* Render existing frames */}
        {frames.map((frame, index) => {
          const thumbnailUrl = getFrameThumbnailUrl(frame, imageKeys);
          return (
            <div
              key={frame.id}
              ref={index === currentFrameIndex ? selectedFrameRef : null}
              className={`timeline-frame ${
                index === currentFrameIndex ? "selected" : ""
              }`}
              onClick={() => handleFrameClick(index)}
              onContextMenu={(e) => handleContextMenu(e, frame.id, index)}
            >
              {thumbnailUrl ? (
                <img
                  src={thumbnailUrl}
                  alt={`Frame ${index + 1}`}
                  className="timeline-frame-image"
                  loading="lazy"
                />
              ) : (
                <div className="timeline-frame-placeholder">{index + 1}</div>
              )}
              <div className="timeline-frame-number">{index + 1}</div>
            </div>
          );
        })}

        {/* Virtual "add frame" card */}
        <div
          className="timeline-frame timeline-frame-add"
          title="Add new frame"
          onClick={onAddFrame}
        >
          <div className="timeline-frame-add-icon">+</div>
        </div>
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          onClose={closeContextMenu}
          items={[
            {
              label: "Regenerate",
              icon: "🔄",
              onClick: handleRegenerateClick,
            },
            {
              label: "Delete",
              icon: "🗑️",
              onClick: handleDeleteClick,
              danger: true,
            },
          ]}
        />
      )}
    </div>
  );
};
