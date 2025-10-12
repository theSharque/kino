import { useState, useEffect, useCallback, useRef } from "react";
import { FrameViewer } from "./components/FrameViewer";
import { Timeline } from "./components/Timeline";
import "./App.css";

// Mock frame data for development
// TODO: Replace with actual API call to backend
const generateMockFrames = (count: number) => {
  return Array.from({ length: count }, (_, index) => ({
    id: index + 1,
    index,
    thumbnailUrl: undefined, // Will be loaded from backend
    path: undefined,
  }));
};

function App() {
  const [frames] = useState(() => generateMockFrames(100)); // Mock: 100 frames
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [fps] = useState(24); // Mock FPS, will come from project settings
  const playIntervalRef = useRef<number | null>(null);

  // Handle frame change
  const handleFrameChange = useCallback(
    (index: number) => {
      if (index >= 0 && index < frames.length) {
        setCurrentFrameIndex(index);
      }
    },
    [frames.length]
  );

  // Play/Pause toggle
  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  // Handle frame selection from timeline
  const handleFrameSelect = useCallback((index: number) => {
    setCurrentFrameIndex(index);
    // Pause playback when manually selecting a frame
    setIsPlaying(false);
  }, []);

  // Playback effect - advance frames at FPS rate
  useEffect(() => {
    if (isPlaying) {
      const interval = 1000 / fps; // milliseconds per frame

      playIntervalRef.current = window.setInterval(() => {
        setCurrentFrameIndex((prevIndex) => {
          const nextIndex = prevIndex + 1;
          // Loop back to start or stop at end
          if (nextIndex >= frames.length) {
            setIsPlaying(false); // Stop at the end
            return prevIndex;
          }
          return nextIndex;
        });
      }, interval);

      return () => {
        if (playIntervalRef.current) {
          clearInterval(playIntervalRef.current);
        }
      };
    }
  }, [isPlaying, fps, frames.length]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowLeft":
          e.preventDefault();
          handleFrameChange(currentFrameIndex - 1);
          break;
        case "ArrowRight":
          e.preventDefault();
          handleFrameChange(currentFrameIndex + 1);
          break;
        case " ":
        case "k":
          e.preventDefault();
          handlePlayPause();
          break;
        case "Home":
          e.preventDefault();
          handleFrameChange(0);
          break;
        case "End":
          e.preventDefault();
          handleFrameChange(frames.length - 1);
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentFrameIndex, handleFrameChange, handlePlayPause, frames.length]);

  // Get current frame URL
  // TODO: Implement actual frame loading from backend
  const currentFrameUrl = frames[currentFrameIndex]?.thumbnailUrl;

  return (
    <div className="app-container">
      {/* Upper part: Frame Viewer (70%) */}
      <div className="viewer-section">
        <FrameViewer
          currentFrameIndex={currentFrameIndex}
          totalFrames={frames.length}
          fps={fps}
          isPlaying={isPlaying}
          onFrameChange={handleFrameChange}
          onPlayPause={handlePlayPause}
          frameImageUrl={currentFrameUrl}
        />
      </div>

      {/* Lower part: Timeline (30%) */}
      <div className="timeline-section">
        <Timeline
          frames={frames}
          currentFrameIndex={currentFrameIndex}
          onFrameSelect={handleFrameSelect}
        />
      </div>
    </div>
  );
}

export default App;
