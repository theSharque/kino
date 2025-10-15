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
  // Current project state
  const [currentProject, setCurrentProject] = useState<Project | null>(null);

  // Frames state
  const [frames, setFrames] = useState<Frame[]>([]);

  // Image keys for forcing reload (timestamp-based cache busting)
  const [imageKeys, setImageKeys] = useState<Map<number, number>>(new Map());

  // Track frames currently being generated (for auto-refresh)
  const [generatingFrames, setGeneratingFrames] = useState<Set<number>>(
    new Set()
  );
  const previewIntervalRef = useRef<number | null>(null);

  // Force reload image for a specific frame
  const forceReloadFrame = useCallback((frameId: number) => {
    setImageKeys((prev) => {
      const newKeys = new Map(prev);
      newKeys.set(frameId, Date.now());
      return newKeys;
    });
  }, []);

  // Handle WebSocket messages
  const handleWebSocketMessage = useCallback(
    async (event: any) => {
      if (!currentProject) return;

      // Handle different event types
      if (
        event.type === "generation_started" &&
        event.data.project_id === currentProject.id
      ) {
        console.log("🎬 Generation started:", event.data);

        try {
          const frame = await framesAPI.getFrame(event.data.frame_id);
          setFrames((prev) => {
            const exists = prev.some((f) => f.id === event.data.frame_id);
            if (exists) return prev;
            return [...prev, frame].sort((a, b) => a.id - b.id);
          });

          setGeneratingFrames((prev) => new Set(prev).add(event.data.frame_id));
        } catch (error) {
          console.error("Failed to fetch frame:", error);
        }
      } else if (
        event.type === "generation_completed" &&
        event.data.project_id === currentProject.id
      ) {
        console.log("✅ Generation completed:", event.data);

        setGeneratingFrames((prev) => {
          const newSet = new Set(prev);
          newSet.delete(event.data.frame_id);
          return newSet;
        });

        forceReloadFrame(event.data.frame_id);
      } else if (
        event.type === "frame_update" &&
        event.project_id === currentProject.id
      ) {
        // Legacy support
        console.log("📸 Frame updated (legacy):", event);

        try {
          const updatedFrame = await framesAPI.getFrame(event.frame_id);
          setFrames((prevFrames) => {
            const existingIndex = prevFrames.findIndex(
              (f) => f.id === event.frame_id
            );
            if (existingIndex >= 0) {
              const newFrames = [...prevFrames];
              newFrames[existingIndex] = updatedFrame;
              return newFrames;
            } else {
              return [...prevFrames, updatedFrame];
            }
          });
          forceReloadFrame(event.frame_id);
        } catch (error) {
          console.error("Failed to fetch updated frame:", error);
        }
      }
    },
    [currentProject, forceReloadFrame]
  );

  // WebSocket for real-time updates
  const { metrics, isConnected } = useWebSocket(handleWebSocketMessage);

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

  // Frame context menu state
  const [frameToDelete, setFrameToDelete] = useState<{
    id: number;
    index: number;
  } | null>(null);
  const [regenerateParams, setRegenerateParams] = useState<Record<
    string,
    any
  > | null>(null);

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

  // Auto-refresh preview images during generation (every 1 second)
  useEffect(() => {
    if (generatingFrames.size === 0) {
      if (previewIntervalRef.current) {
        clearInterval(previewIntervalRef.current);
        previewIntervalRef.current = null;
      }
      return;
    }

    console.log(
      `Starting auto-refresh for ${generatingFrames.size} generating frames`
    );

    previewIntervalRef.current = window.setInterval(() => {
      generatingFrames.forEach((frameId) => {
        forceReloadFrame(frameId);
      });
    }, 1000); // Refresh every second

    return () => {
      if (previewIntervalRef.current) {
        clearInterval(previewIntervalRef.current);
        previewIntervalRef.current = null;
      }
    };
  }, [generatingFrames, forceReloadFrame]);

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

  const handleDeleteFrame = useCallback(async () => {
    if (!frameToDelete) return;

    try {
      await framesAPI.delete(frameToDelete.id);

      // Reload frames
      if (currentProject) {
        await loadProjectFrames(currentProject.id);
      }

      // Adjust current frame index if needed
      if (currentFrameIndex >= frames.length - 1) {
        setCurrentFrameIndex(Math.max(0, frames.length - 2));
      }

      setFrameToDelete(null);
      setIsDeleteFrameModalOpen(false);
    } catch (error) {
      console.error("Failed to delete frame:", error);
      alert("Failed to delete frame: " + (error as Error).message);
    }
  }, [
    frameToDelete,
    currentProject,
    frames.length,
    currentFrameIndex,
    loadProjectFrames,
  ]);

  const handleDeleteFrameFromTimeline = useCallback(
    (frameId: number, frameIndex: number) => {
      setFrameToDelete({ id: frameId, index: frameIndex });
      setIsDeleteFrameModalOpen(true);
    },
    []
  );

  const handleRegenerateFrame = useCallback(
    async (frameId: number, frameIndex: number) => {
      try {
        // Load generation parameters for the frame
        const params = await framesAPI.getGenerationParams(frameId);

        if (!params) {
          alert("No generation parameters found for this frame");
          return;
        }

        // Extract plugin name from params
        const pluginName = params.generator || params.plugin;
        if (!pluginName) {
          alert("Cannot determine generator plugin for this frame");
          return;
        }

        // Load plugins to find the right one
        const plugins = await generatorAPI.getPlugins();
        const plugin = plugins.find((p) => p.name === pluginName);

        if (!plugin) {
          alert(`Generator plugin '${pluginName}' not found`);
          return;
        }

        // Set plugin and params
        setSelectedPlugin(plugin);
        // Extract parameters from the API response structure
        const extractedParams = params.parameters || params;
        console.log("Regenerate params loaded:", extractedParams);
        setRegenerateParams(extractedParams);
        setIsGenerateFrameModalOpen(true);
      } catch (error) {
        console.error("Failed to load generation params:", error);
        alert(
          "Failed to load generation parameters: " + (error as Error).message
        );
      }
    },
    []
  );

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

  // Get current frame URL with cache-busting timestamp
  const currentFrameUrl = frames[currentFrameIndex]
    ? (() => {
        const baseUrl = getFrameImageUrl(frames[currentFrameIndex].path);
        const frameId = frames[currentFrameIndex].id;
        const timestamp = imageKeys.get(frameId);
        return timestamp ? `${baseUrl}?t=${timestamp}` : baseUrl;
      })()
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
          onRegenerateFrame={handleRegenerateFrame}
          onDeleteFrame={handleDeleteFrameFromTimeline}
          imageKeys={imageKeys}
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
        onClose={() => {
          setIsDeleteFrameModalOpen(false);
          setFrameToDelete(null);
        }}
        onConfirm={handleDeleteFrame}
        frameNumber={
          frameToDelete ? frameToDelete.index + 1 : currentFrameIndex + 1
        }
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
        onClose={() => {
          setIsGenerateFrameModalOpen(false);
          setRegenerateParams(null);
        }}
        plugin={selectedPlugin}
        projectId={currentProject?.id || null}
        projectWidth={currentProject?.width}
        projectHeight={currentProject?.height}
        initialParams={regenerateParams}
        onGenerate={handleGenerate}
      />
    </div>
  );
}

export default App;
