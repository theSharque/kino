/**
 * API Client for Kino Backend
 */

const API_BASE_URL = "http://localhost:8000";

// Types matching backend models
export interface Project {
  id: number;
  name: string;
  width: number;
  height: number;
  fps: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  width: number;
  height: number;
  fps: number;
}

export interface ProjectUpdate {
  name?: string;
  width?: number;
  height?: number;
  fps?: number;
}

export interface Frame {
  id: number;
  path: string;
  generator: string;
  project_id: number;
  created_at: string;
  updated_at: string;
}

export interface BackendHealth {
  status: string;
  service: string;
  python_version: string;
  cpu_percent: number;
  memory_percent: number;
}

export interface PluginParameter {
  type: string;
  required: boolean;
  default?: any;
  description: string;
  example?: string;
  min?: number;
  max?: number;
  category?: string; // For model_selection type
  options?: string[]; // For enum-like fields
}

export interface PluginInfo {
  name: string;
  version: string;
  description: string;
  author: string;
  model_type: string;
  parameters: Record<string, PluginParameter>;
}

export interface Task {
  id: number;
  name: string;
  type: string;
  data: Record<string, any>;
  status: string;
  progress: number;
  result?: Record<string, any>;
  error?: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskCreate {
  name: string;
  type: string;
  data: Record<string, any>;
}

export interface ModelInfo {
  filename: string;
  display_name: string;
  path: string;
  size: number;
  extension: string;
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(
        error.message || error.error || `HTTP ${response.status}`
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Network error");
  }
}

/**
 * Health API
 */
export const healthAPI = {
  check: () => fetchAPI<BackendHealth>("/health"),
};

/**
 * Projects API (v2 - documented)
 */
export const projectsAPI = {
  /**
   * Get all projects
   */
  getAll: async (): Promise<Project[]> => {
    const response = await fetchAPI<{ total: number; projects: Project[] }>(
      "/api/v2/projects"
    );
    return response.projects;
  },

  /**
   * Get project by ID
   */
  getById: (id: number) => fetchAPI<Project>(`/api/v2/projects/${id}`),

  /**
   * Create new project
   */
  create: (data: ProjectCreate) =>
    fetchAPI<Project>("/api/v2/projects", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  /**
   * Update project
   */
  update: (id: number, data: ProjectUpdate) =>
    fetchAPI<Project>(`/api/v2/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  /**
   * Delete project
   */
  delete: (id: number) =>
    fetchAPI<{ message: string }>(`/api/v2/projects/${id}`, {
      method: "DELETE",
    }),
};

/**
 * Frames API (v1)
 */
export const framesAPI = {
  /**
   * Get all frames for a project
   */
  getByProject: async (projectId: number): Promise<Frame[]> => {
    const response = await fetchAPI<{ total: number; frames: Frame[] }>(
      `/api/v1/projects/${projectId}/frames`
    );
    return response.frames;
  },

  /**
   * Get all frames (optionally filtered by project_id)
   */
  getAll: async (projectId?: number): Promise<Frame[]> => {
    const query = projectId ? `?project_id=${projectId}` : "";
    const response = await fetchAPI<{ total: number; frames: Frame[] }>(
      `/api/v1/frames${query}`
    );
    return response.frames;
  },

  /**
   * Delete frame
   */
  delete: (id: number) =>
    fetchAPI<{ message: string }>(`/api/v1/frames/${id}`, {
      method: "DELETE",
    }),
};

/**
 * Generator API (v1)
 */
export const generatorAPI = {
  /**
   * Get all available plugins
   */
  getPlugins: async (): Promise<PluginInfo[]> => {
    const response = await fetchAPI<{
      total: number;
      plugins: Record<string, PluginInfo>;
    }>("/api/v1/generator/plugins");
    // Convert object to array
    return Object.values(response.plugins);
  },

  /**
   * Create new task
   */
  createTask: (data: TaskCreate) =>
    fetchAPI<Task>("/api/v1/generator/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  /**
   * Start task generation
   */
  startTask: (taskId: number) =>
    fetchAPI<{ message: string; task_id: number }>(
      `/api/v1/generator/tasks/${taskId}/generate`,
      {
        method: "POST",
      }
    ),

  /**
   * Stop task generation
   */
  stopTask: (taskId: number) =>
    fetchAPI<{ message: string; task_id: number }>(
      `/api/v1/generator/tasks/${taskId}/stop`,
      {
        method: "POST",
      }
    ),

  /**
   * Get task by ID
   */
  getTask: (taskId: number) =>
    fetchAPI<Task>(`/api/v1/generator/tasks/${taskId}`),

  /**
   * Get task progress
   */
  getTaskProgress: (taskId: number) =>
    fetchAPI<{ task_id: number; status: string; progress: number }>(
      `/api/v1/generator/tasks/${taskId}/progress`
    ),

  /**
   * Get all tasks
   */
  getAllTasks: async (): Promise<Task[]> => {
    const response = await fetchAPI<{ total: number; tasks: Task[] }>(
      "/api/v1/generator/tasks"
    );
    return response.tasks;
  },
};

/**
 * Models API (v1)
 */
export const modelsAPI = {
  /**
   * Get all model categories
   */
  getCategories: async (): Promise<string[]> => {
    const response = await fetchAPI<{ total: number; categories: string[] }>(
      "/api/v1/models/categories"
    );
    return response.categories;
  },

  /**
   * Get models by category
   */
  getByCategory: async (category: string): Promise<ModelInfo[]> => {
    const response = await fetchAPI<{
      category: string;
      total: number;
      models: ModelInfo[];
    }>(`/api/v1/models/${category}`);
    return response.models;
  },

  /**
   * Get model info
   */
  getModelInfo: (category: string, filename: string) =>
    fetchAPI<ModelInfo>(`/api/v1/models/${category}/${filename}`),
};

/**
 * Get frame image URL
 */
export const getFrameImageUrl = (framePath: string): string => {
  // Frame path is absolute, so we need to construct URL differently
  // TODO: Backend should serve frames via API endpoint
  return `${API_BASE_URL}/data/frames/${framePath.split("/").pop()}`;
};
