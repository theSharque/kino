import { useState, useEffect, useCallback, useRef } from "react";
import { MenuBar } from "./components/MenuBar";
import { FrameViewer } from "./components/FrameViewer";
import { Timeline } from "./components/Timeline";
import { NewProjectModal } from "./components/modals/NewProjectModal";
import { ProjectsModal } from "./components/modals/ProjectsModal";
import { FindFrameModal } from "./components/modals/FindFrameModal";
import { DeleteFrameModal } from "./components/modals/DeleteFrameModal";
import { AboutModal } from "./components/modals/AboutModal";
import { SelectGeneratorModal } from "./components/modals/SelectGeneratorModal";
import { GenerateFrameModal } from "./components/modals/GenerateFrameModal";
import type { Project, Frame, PluginInfo } from "./api/client";
import { framesAPI, generatorAPI, systemAPI } from "./api/client";
import { useWebSocket } from "./hooks/useWebSocket";
import { getFrameImageUrl, APP_NAME } from "./config/constants";
import "./App.css";

function App() {
  // WebSocket for real-time updates
  const { metrics, isConnected } = useWebSocket();

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
  const [isSelectGeneratorModalOpen, setIsSelectGeneratorModalOpen] =
    useState(false);
  const [isGenerateFrameModalOpen, setIsGenerateFrameModalOpen] =
    useState(false);

  // Generator state
  const [selectedPlugin, setSelectedPlugin] = useState<PluginInfo | null>(null);

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
      // Skip keyboard shortcuts if user is typing in an input field
      const target = e.target as HTMLElement;
      const isInputField =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT" ||
        target.isContentEditable;

      if (isInputField) {
        return; // Don't handle shortcuts when typing
      }

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
  const handleNewProject = useCallback((project: Project) => {
    setCurrentProject(project);
    setFrames([]); // New project has no frames yet
    setCurrentFrameIndex(0);
    console.log("Project created:", project);
  }, []);

  const handleOpenProject = useCallback(
    async (project: Project) => {
      setCurrentProject(project);
      console.log("Opening project:", project);

      // Load frames for the selected project
      await loadProjectFrames(project.id);
    },
    [loadProjectFrames]
  );

  const handleFindFrame = useCallback(
    (frameIndex: number) => {
      handleFrameChange(frameIndex);
    },
    [handleFrameChange]
  );

  const handleDeleteFrame = useCallback(() => {
    // TODO: Call backend API to delete current frame
    console.log("Delete frame:", currentFrameIndex + 1);
  }, [currentFrameIndex]);

  // Generator handlers
  const handleAddFrame = useCallback(() => {
    if (!currentProject) {
      alert("Please open or create a project first");
      return;
    }
    setIsSelectGeneratorModalOpen(true);
  }, [currentProject]);

  const handleGeneratorSelect = useCallback((plugin: PluginInfo) => {
    setSelectedPlugin(plugin);
    setIsGenerateFrameModalOpen(true);
  }, []);

  const handleGenerate = useCallback(
    async (pluginName: string, parameters: Record<string, any>) => {
      if (!currentProject) {
        console.error("No project selected");
        return;
      }

      try {
        console.log("Creating generation task:", {
          pluginName,
          parameters,
        });

        // Create task
        const task = await generatorAPI.createTask({
          name: `Generate frame for ${currentProject.name}`,
          type: pluginName,
          data: parameters,
        });

        console.log("Task created:", task);

        // Start generation
        await generatorAPI.startTask(task.id);
        console.log("Generation started for task:", task.id);

        // TODO: Implement progress tracking and frame reload
        // For now, just reload frames after a delay
        setTimeout(async () => {
          await loadProjectFrames(currentProject.id);
        }, 5000);
      } catch (err) {
        console.error("Failed to generate frame:", err);
        alert(
          `Failed to generate frame: ${
            err instanceof Error ? err.message : "Unknown error"
          }`
        );
      }
    },
    [currentProject, loadProjectFrames]
  );

  // Handle emergency stop
  const handleEmergencyStop = useCallback(async () => {
    if (!confirm("Stop all running generation tasks?")) {
      return;
    }

    try {
      const response = await systemAPI.emergencyStop();
      alert(response.message);
    } catch (err) {
      console.error("Emergency stop failed:", err);
      alert(
        `Emergency stop failed: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    }
  }, []);

  // Handle server restart
  const handleRestartServer = useCallback(async () => {
    if (
      !confirm(
        "Restart the backend server? This will interrupt all running tasks. The page will need to be refreshed after the server restarts."
      )
    ) {
      return;
    }

    try {
      await systemAPI.restartServer();
      alert(
        "Server restart initiated. Please wait 5-10 seconds, then refresh the page."
      );
    } catch (err) {
      console.error("Server restart failed:", err);
      alert(
        `Server restart failed: ${
          err instanceof Error ? err.message : "Unknown error"
        }`
      );
    }
  }, []);

  // Update document title when project changes
  useEffect(() => {
    if (currentProject) {
      document.title = `${APP_NAME} - ${currentProject.name}`;
    } else {
      document.title = APP_NAME;
    }
  }, [currentProject]);

  // Get current frame URL
  const currentFrameUrl = frames[currentFrameIndex]
    ? getFrameImageUrl(frames[currentFrameIndex].path)
    : undefined;

  return (
    <div className="app-container">
      {/* Menu Bar */}
      <MenuBar
        currentProjectName={currentProject?.name}
        systemMetrics={metrics}
        isConnected={isConnected}
        onNewProject={() => setIsNewProjectModalOpen(true)}
        onOpenProject={() => setIsOpenProjectModalOpen(true)}
        onFindFrame={() => setIsFindFrameModalOpen(true)}
        onDeleteFrame={() => setIsDeleteFrameModalOpen(true)}
        onEmergencyStop={handleEmergencyStop}
        onRestartServer={handleRestartServer}
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
          onAddFrame={handleAddFrame}
        />
      </div>

      {/* Modals */}
      <NewProjectModal
        isOpen={isNewProjectModalOpen}
        onClose={() => setIsNewProjectModalOpen(false)}
        onProjectCreated={handleNewProject}
      />

      <ProjectsModal
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

      <SelectGeneratorModal
        isOpen={isSelectGeneratorModalOpen}
        onClose={() => setIsSelectGeneratorModalOpen(false)}
        onSelect={handleGeneratorSelect}
      />

      <GenerateFrameModal
        isOpen={isGenerateFrameModalOpen}
        onClose={() => setIsGenerateFrameModalOpen(false)}
        plugin={selectedPlugin}
        projectId={currentProject?.id || null}
        projectWidth={currentProject?.width}
        projectHeight={currentProject?.height}
        onGenerate={handleGenerate}
      />
    </div>
  );
}

export default App;
