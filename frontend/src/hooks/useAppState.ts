import { useState, useEffect, useCallback } from "react";
import type { Project } from "../api/client";

export interface AppState {
  currentProjectId: number | null;
  currentFrameIndex: number;
  lastUpdated: number;
}

const STORAGE_KEY = "kino_app_state";
const DEFAULT_STATE: AppState = {
  currentProjectId: null,
  currentFrameIndex: 0,
  lastUpdated: Date.now(),
};

export function useAppState() {
  const [appState, setAppState] = useState<AppState>(DEFAULT_STATE);

  // Load state from localStorage on mount
  useEffect(() => {
    try {
      const savedState = localStorage.getItem(STORAGE_KEY);
      if (savedState) {
        const parsed = JSON.parse(savedState) as AppState;
        // Validate the saved state
        if (
          typeof parsed.currentProjectId === "number" ||
          parsed.currentProjectId === null
        ) {
          setAppState(parsed);
          console.log("📱 App state restored from localStorage:", parsed);
        }
      }
    } catch (error) {
      console.error("Failed to load app state from localStorage:", error);
    }
  }, []);

  // Save state to localStorage whenever it changes
  const saveState = useCallback((newState: Partial<AppState>) => {
    setAppState((prevState) => {
      const updatedState = {
        ...prevState,
        ...newState,
        lastUpdated: Date.now(),
      };

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedState));
        console.log("💾 App state saved to localStorage:", updatedState);
      } catch (error) {
        console.error("Failed to save app state to localStorage:", error);
      }

      return updatedState;
    });
  }, []);

  // Update current project
  const setCurrentProject = useCallback(
    (project: Project | null) => {
      saveState({
        currentProjectId: project?.id || null,
        currentFrameIndex: 0, // Reset frame index when switching projects
      });
    },
    [saveState]
  );

  // Update current frame index
  const setCurrentFrameIndex = useCallback(
    (index: number) => {
      saveState({ currentFrameIndex: index });
    },
    [saveState]
  );

  // Clear state (when closing app or logging out)
  const clearState = useCallback(() => {
    try {
      localStorage.removeItem(STORAGE_KEY);
      setAppState(DEFAULT_STATE);
      console.log("🗑️ App state cleared");
    } catch (error) {
      console.error("Failed to clear app state:", error);
    }
  }, []);

  return {
    appState,
    setCurrentProject,
    setCurrentFrameIndex,
    clearState,
  };
}
