import { useState, useEffect, useCallback, useRef } from "react";
import { MenuBar } from "./components/MenuBar";
import { FrameViewer } from "./components/FrameViewer";
import { Timeline } from "./components/Timeline";
import { NewProjectModal } from "./components/modals/NewProjectModal";
import { OpenProjectModal } from "./components/modals/OpenProjectModal";
import { FindFrameModal } from "./components/modals/FindFrameModal";
import { DeleteFrameModal } from "./components/modals/DeleteFrameModal";
import { AboutModal } from "./components/modals/AboutModal";
import { Project, Frame, framesAPI } from "./api/client";
import "./App.css";

function App() {
  // Current project state
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  
  // Frames state
  const [frames, setFrames] = useState<Frame[]>([]);
  const [loadingFrames, setLoadingFrames] = useState(false);
  
  // Playback state
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const playIntervalRef = useRef<number | null>(null);

  // Modal states
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [isOpenProjectModalOpen, setIsOpenProjectModalOpen] = useState(false);
  const [isFindFrameModalOpen, setIsFindFrameModalOpen] = useState(false);
  const [isDeleteFrameModalOpen, setIsDeleteFrameModalOpen] = useState(false);
  const [isAboutModalOpen, setIsAboutModalOpen] = useState(false);

  // Get FPS from project or use default
  const fps = currentProject?.fps || 24;

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

  // Load frames for current project
  const loadProjectFrames = useCallback(async (projectId: number) => {
    setLoadingFrames(true);
    try {
      const projectFrames = await framesAPI.getByProject(projectId);
      setFrames(projectFrames);
      setCurrentFrameIndex(0); // Reset to first frame
    } catch (err) {
      console.error("Failed to load frames:", err);
      setFrames([]); // Clear frames on error
    } finally {
      setLoadingFrames(false);
    }
  }, []);

  // Modal handlers
  const handleNewProject = useCallback(
    (project: Project) => {
      setCurrentProject(project);
      setFrames([]); // New project has no frames yet
      setCurrentFrameIndex(0);
      console.log("Project created:", project);
    },
    []
  );

  const handleOpenProject = useCallback(
    async (project: Project) => {
      setCurrentProject(project);
      console.log("Opening project:", project);
      
      // Load frames for the selected project
      await loadProjectFrames(project.id);
    },
    [loadProjectFrames]
  );

  const handleFindFrame = useCallback((frameIndex: number) => {
    handleFrameChange(frameIndex);
  }, [handleFrameChange]);

  const handleDeleteFrame = useCallback(() => {
    // TODO: Call backend API to delete current frame
    console.log("Delete frame:", currentFrameIndex + 1);
  }, [currentFrameIndex]);

  // Get current frame URL
  const currentFrameUrl = frames[currentFrameIndex]
    ? `http://localhost:8000/data/frames/${frames[currentFrameIndex].path.split("/").pop()}`
    : undefined;

  return (
    <div className="app-container">
      {/* Menu Bar */}
      <MenuBar
        onNewProject={() => setIsNewProjectModalOpen(true)}
        onOpenProject={() => setIsOpenProjectModalOpen(true)}
        onFindFrame={() => setIsFindFrameModalOpen(true)}
        onDeleteFrame={() => setIsDeleteFrameModalOpen(true)}
        onAbout={() => setIsAboutModalOpen(true)}
      />

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

      {/* Modals */}
      <NewProjectModal
        isOpen={isNewProjectModalOpen}
        onClose={() => setIsNewProjectModalOpen(false)}
        onProjectCreated={handleNewProject}
      />

      <OpenProjectModal
        isOpen={isOpenProjectModalOpen}
        onClose={() => setIsOpenProjectModalOpen(false)}
        onProjectSelected={handleOpenProject}
      />

      <FindFrameModal
        isOpen={isFindFrameModalOpen}
        onClose={() => setIsFindFrameModalOpen(false)}
        onFind={handleFindFrame}
        totalFrames={frames.length}
      />

      <DeleteFrameModal
        isOpen={isDeleteFrameModalOpen}
        onClose={() => setIsDeleteFrameModalOpen(false)}
        onConfirm={handleDeleteFrame}
        frameNumber={currentFrameIndex + 1}
      />

      <AboutModal
        isOpen={isAboutModalOpen}
        onClose={() => setIsAboutModalOpen(false)}
      />
    </div>
  );
}

export default App;
