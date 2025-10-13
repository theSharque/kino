# Kino Project - AI Context & Development Guide

**Last Updated:** 2025-10-13 (Migrated to full ComfyUI installation with sys.path integration)

This file serves as a persistent context storage for AI assistance. It contains essential information about the project's architecture, decisions, and conventions to ensure consistent and correct code generation throughout the development process.

---

## Project Overview

**Project Name:** Kino
**Type:** Single Page Application (SPA)
**Purpose:** Video project management and editing application with ML/AI functionality
**Authentication:** None - public access application

---

## Tech Stack

### Backend
- **Language:** Python 3.12
- **Framework:** aiohttp (async web framework)
- **CORS:** Custom middleware (supports all routes including PydanticView)
- **API Documentation:** aiohttp-pydantic (OpenAPI/Swagger)
- **Database:** SQLite with aiosqlite (async driver)
- **Validation:** Pydantic v2
- **ML/AI:** PyTorch, transformers, torchvision, torchaudio
- **Other:** python-dotenv, psutil, einops, scipy, numpy

### Frontend
- **Language:** TypeScript
- **Framework:** React 19.1
- **Build Tool:** Vite 7.1
- **UI Components:** Custom React components
- **Virtual Scrolling:** react-window 1.8
- **Styling:** CSS Modules (dark theme)

### Communication
- **Primary:** REST API (HTTP endpoints for CRUD operations)
- **Real-time:** WebSocket (`ws://localhost:8000/ws`) for live metrics and task updates
  - Heartbeat: 10 seconds
  - Updates every: 2 seconds
  - Auto-reconnect: 3 second delay
  - Broadcasts: System metrics (CPU, GPU type/usage, GPU VRAM, RAM), task queue, current task progress
  - GPU Support: Intel XPU (Arc GPU) and NVIDIA CUDA auto-detection

---

## Architecture & Structure

### Repository Structure

**Monorepo:** Single git repository containing both backend and frontend.

```
/qs/kino/                        # 🔴 Git Root (Monorepo)
├── .git/                        # Git repository
├── .gitignore                   # Root gitignore (common rules)
├── .cursorrules                 # AI development rules
├── PROJECT_CONTEXT.md           # This file - project context
├── kino.code-workspace          # VS Code workspace configuration
├── backend/                     # Python backend
│   ├── .gitignore              # Backend-specific rules
│   └── [backend structure]
└── frontend/                    # React frontend
    ├── .gitignore              # Frontend-specific rules
    └── [frontend structure]
```

**Why monorepo?**
- Synchronized API changes (backend + frontend in one commit)
- Shared PROJECT_CONTEXT.md
- Unified git history
- Simpler CI/CD
- Single source of truth for data models

### Backend Structure
```
backend/
├── main.py              # Application entry point, server setup, OpenAPI config
├── routes.py            # Route configuration and registration (v1 + v2)
├── database.py          # Database connection management and utilities
├── config.py            # Configuration (paths: models, data, frames, projects)
├── API_DOCUMENTATION.md # Complete API documentation and Swagger guide
├── handlers/            # Request handlers (controllers) organized by domain
│   ├── __init__.py
│   ├── health.py       # Health check endpoints
│   ├── api.py          # General API handlers (v1)
│   ├── api_documented.py # API v2 handlers with OpenAPI documentation
│   ├── projects.py     # Project CRUD handlers (v1)
│   ├── frames.py       # Frame CRUD handlers (v1)
│   ├── generator.py    # Generator/task handlers (v1)
│   ├── models.py       # Model management handlers (v1)
│   ├── system.py       # System control handlers (emergency stop, restart, shutdown)
│   └── websocket.py    # WebSocket handler for real-time metrics and task updates
├── models/              # Pydantic data models
│   ├── __init__.py
│   ├── project.py      # Project models
│   ├── frame.py        # Frame models
│   └── task.py         # Task models for generator system
├── services/            # Business logic services
│   ├── __init__.py
│   ├── project_service.py  # Project service layer
│   ├── frame_service.py    # Frame service layer
│   ├── generator_service.py # Generator/task management service (with stop_all_tasks)
│   ├── model_service.py    # Model management service (list categories, models)
│   ├── system_monitor.py   # System resource monitoring (CPU, GPU [XPU/CUDA], VRAM, Memory)
│   └── test_gpu_detection.py # GPU detection test script
├── bricks/              # ComfyUI connector layer (bridge between Kino and ComfyUI)
│   ├── comfy_bricks.py # ComfyUI wrapper functions (load checkpoint, encode, sample, decode, lora)
│   ├── comfy_constants.py # ComfyUI constants (40+ samplers, 9 schedulers)
│   ├── frames_routine.py # Frame saving utilities
│   ├── generation_params.py # Generation parameters storage (save/load JSON metadata)
│   ├── README.md       # Bricks documentation and usage examples
│   └── README_PARAMS.md # Generation parameters documentation
├── ComfyUI/             # Full ComfyUI installation (complete framework)
│   ├── comfy/          # Core ComfyUI library
│   │   ├── sd.py       # Stable Diffusion implementations
│   │   ├── sample.py   # Sampling algorithms
│   │   ├── samplers.py # All 40+ samplers and 9 schedulers
│   │   ├── model_management.py # Model loading and memory
│   │   ├── ldm/        # Latent Diffusion Models
│   │   └── text_encoders/ # CLIP, T5, and other encoders
│   ├── comfy_api/      # ComfyUI API modules
│   ├── comfy_extras/   # Extra nodes and features
│   ├── custom_nodes/   # Custom node system
│   ├── models/         # Model storage (symlinked to ../models_storage/)
│   └── [full ComfyUI codebase - server, execution, etc.]
├── COMFYUI_INTEGRATION.md # ComfyUI integration guide for Kino
├── data/                # Data storage (gitignored content)
│   ├── frames/         # Generated frame files (.png)
│   ├── projects/       # Project-specific data (organized by project name)
│   └── kino.db         # SQLite database file
├── models_storage/      # AI models storage (gitignored files, keep structure)
│   ├── README.md       # Model storage documentation and usage guide
│   ├── DiffusionModels/ # Diffusion model files (.gitkeep)
│   ├── StableDiffusion/ # Stable Diffusion checkpoints (.safetensors, .ckpt)
│   ├── Lora/           # LoRA weight files (.gitkeep)
│   ├── TextEncoders/   # Text encoder models (.gitkeep)
│   ├── ClipVision/     # CLIP Vision models (.gitkeep)
│   └── VAE/            # VAE models (.gitkeep)
├── plugins/             # Generator plugins (modular generation system)
│   ├── __init__.py
│   ├── base_plugin.py  # Base plugin interface (async methods)
│   ├── plugin_loader.py # Auto-loader and registry
│   ├── README.md       # Plugin development guide
│   ├── example/        # Example plugin (directory = plugin name)
│   │   ├── __init__.py
│   │   └── loader.py  # Example plugin implementation
│   └── sdxl/          # SDXL plugin (fully implemented with ComfyUI)
│       ├── __init__.py
│       ├── loader.py  # SDXL plugin implementation (uses bricks)
│       └── README.md  # SDXL plugin documentation
├── scripts/             # Utility scripts
│   └── format_code.sh  # Code formatting script
├── venv/                # Python virtual environment (gitignored)
├── run.sh               # Auto-restart script for development (recommended)
├── .env                 # Environment variables (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

### Frontend Structure
```
frontend/
├── src/
│   ├── main.tsx         # Entry point
│   ├── App.tsx          # Main application component (MenuBar + 70/30 layout + modals)
│   ├── App.css          # Application layout styles
│   ├── index.css        # Global styles and resets
│   ├── config/          # Configuration constants
│   │   ├── constants.ts # Centralized constants (API URLs, app name, version, helpers)
│   │   └── README.md    # Configuration documentation
│   ├── api/             # API client and types
│   │   └── client.ts   # Backend API client (projects, frames, health, models, system)
│   ├── hooks/           # React custom hooks
│   │   └── useWebSocket.ts  # WebSocket hook for real-time updates with auto-reconnect
│   ├── components/      # React components
│   │   ├── README.md           # Components documentation
│   │   ├── MenuBar.tsx         # Top menu bar (File, Edit, System, Help)
│   │   ├── MenuBar.css         # MenuBar styles
│   │   ├── Modal.tsx           # Base modal component (reusable)
│   │   ├── Modal.css           # Modal styles with animations
│   │   ├── FrameViewer.tsx     # Upper section (70% - frame display + controls)
│   │   ├── FrameViewer.css     # FrameViewer styles
│   │   ├── Timeline.tsx        # Lower section (30% - filmstrip timeline)
│   │   ├── Timeline.css        # Timeline styles
│   │   └── modals/             # Modal dialogs
│   │       ├── NewProjectModal.tsx    # Create new project form
│   │       ├── ProjectsModal.tsx      # Manage projects (open, select, delete)
│   │       ├── ProjectsModal.css      # Project cards styling
│   │       ├── FindFrameModal.tsx     # Jump to frame by number
│   │       ├── DeleteFrameModal.tsx   # Confirm frame deletion
│   │       ├── AboutModal.tsx         # About dialog (Kino v1.0)
│   │       ├── AboutModal.css         # About dialog styles
│   │       ├── SelectGeneratorModal.tsx    # Select generator plugin
│   │       ├── SelectGeneratorModal.css    # Generator selection styles
│   │       ├── GenerateFrameModal.tsx      # Dynamic form for plugin parameters
│   │       ├── GenerateFrameModal.css      # Generate form styles (with row layout)
│   │       ├── LoraListField.tsx           # LoRA list input component
│   │       └── LoraListField.css           # LoRA field styles (compact inline layout)
│   └── assets/          # Static assets (images, icons)
├── public/              # Public assets
├── node_modules/        # NPM dependencies (gitignored)
├── .gitignore
├── package.json         # Dependencies (React 19, react-window, TypeScript) - version 1.0.0
├── tsconfig.json        # TypeScript configuration
├── tsconfig.app.json    # App-specific TS config
├── tsconfig.node.json   # Node-specific TS config
├── vite.config.ts       # Vite build configuration
├── eslint.config.js     # ESLint configuration
└── README.md            # Frontend documentation
```

---

## Code Style & Best Practices

### General Principles
1. **Write efficient, readable, and maintainable code**
2. **🔴 ALL CODE, COMMENTS, DOCUMENTATION, AND FILE CONTENT MUST BE IN ENGLISH ONLY**
   - No Russian or any other language in source files
   - No Russian in README.md, comments, or documentation
   - Variable names, function names, strings - all English
   - Exception: user-facing UI text (to be localized later if needed)
3. **Use type hints in Python and TypeScript types in React**
4. **Follow async/await patterns consistently**
5. **Keep handlers small and focused - single responsibility**
6. **Use Pydantic models for validation on backend**
7. **Error handling must be comprehensive and informative**

### Python Code Style
- Use type hints for function parameters and return values
- Async functions for all I/O operations
- Pydantic models for request/response validation
- Descriptive docstrings for functions and classes
- Follow PEP 8 naming conventions
- Use `async with` for resource management
- **No trailing whitespace** on any line
- **Empty lines must be truly empty** (no spaces/tabs)
- **Files must end with a newline** character
- Use 4 spaces for indentation (no tabs)

### TypeScript/React Code Style
- Use functional components with hooks
- TypeScript interfaces for all data structures
- Descriptive component and variable names
- Use const for immutable values
- Proper error handling in async operations
- **No trailing whitespace** on any line
- **Empty lines must be truly empty** (no spaces/tabs)
- **Files must end with a newline** character
- Use 2 spaces for indentation

### API Design
- RESTful endpoints: `/api/v{version}/{resource}`
- Consistent response format: JSON
- HTTP status codes used correctly
- CORS enabled for cross-origin requests
- Validation errors return 400 with details
- Server errors return 500 with safe error messages

---

## Data Models & Naming Conventions

**IMPORTANT:** All data models must have identical naming between frontend and backend.

### Project Model

**Backend (Python/Pydantic):**
```python
class ProjectResponse(BaseModel):
    id: int
    name: str
    width: int
    height: int
    fps: int
    created_at: str
    updated_at: str

class ProjectCreate(BaseModel):
    name: str
    width: int
    height: int
    fps: int

class ProjectUpdate(BaseModel):
    name: Optional[str]
    width: Optional[int]
    height: Optional[int]
    fps: Optional[int]
```

**Frontend (TypeScript):**
```typescript
interface Project {
  id: number;
  name: string;
  width: number;
  height: number;
  fps: number;
  created_at: string;  // ISO 8601 format
  updated_at: string;  // ISO 8601 format
}

interface ProjectCreate {
  name: string;
  width: number;
  height: number;
  fps: number;
}

interface ProjectUpdate {
  name?: string;
  width?: number;
  height?: number;
  fps?: number;
}
```

### Frame Model

**Backend (Python/Pydantic):**
```python
class FrameResponse(BaseModel):
    id: int
    path: str
    generator: str
    project_id: int
    created_at: str
    updated_at: str

class FrameCreate(BaseModel):
    path: str
    generator: str
    project_id: int

class FrameUpdate(BaseModel):
    path: Optional[str]
    generator: Optional[str]
    project_id: Optional[int]
```

**Frontend (TypeScript):**
```typescript
interface Frame {
  id: number;
  path: string;
  generator: string;
  project_id: number;
  created_at: string;  // ISO 8601 format
  updated_at: string;  // ISO 8601 format
}

interface FrameCreate {
  path: string;
  generator: string;
  project_id: number;
}

interface FrameUpdate {
  path?: string;
  generator?: string;
  project_id?: number;
}
```

### Task Model (Generator System)

**Backend (Python/Pydantic):**
```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"

class TaskResponse(BaseModel):
    id: int
    name: str
    type: str  # Plugin type
    data: Dict[str, Any]  # Plugin-specific data
    status: TaskStatus
    progress: float  # 0.0 to 100.0
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: str
    updated_at: str
    started_at: Optional[str]
    completed_at: Optional[str]

class TaskCreate(BaseModel):
    name: str
    type: str
    data: Dict[str, Any]
```

**Frontend (TypeScript):**
```typescript
enum TaskStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  STOPPED = "stopped"
}

interface Task {
  id: number;
  name: string;
  type: string;  // Plugin type
  data: Record<string, any>;
  status: TaskStatus;
  progress: number;  // 0.0 to 100.0
  result: Record<string, any> | null;
  error: string | null;
  created_at: string;  // ISO 8601 format
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
}

interface TaskCreate {
  name: string;
  type: string;
  data: Record<string, any>;
}
```

### Naming Conventions
- **snake_case:** Python variables, function names, file names
- **camelCase:** TypeScript/JavaScript variables and function names
- **PascalCase:** Python classes, TypeScript interfaces, React components
- **UPPER_CASE:** Constants in both languages
- **Field names in API:** Use snake_case to maintain consistency with Python backend

---

## Current API Endpoints

### API Documentation
- **Swagger UI:** `GET /api/docs` - Interactive API documentation
- **OpenAPI Spec:** `GET /api/docs/spec` - OpenAPI 3.0 specification (JSON)
- **Documentation:** See `API_DOCUMENTATION.md` for detailed guide

### Health & Monitoring
- `GET /health` - Server health check with system metrics
- `GET /ws` - WebSocket endpoint for real-time updates (see WebSocket Messages section)

### API v1 - General (Legacy)
- `GET /api/v1/hello?name={name}` - Simple greeting endpoint
- `POST /api/v1/echo` - Echo message with validation
  - Request: `{"message": "string"}`
  - Response: `{"echo": "string", "length": number}`
- `GET /api/v1/info` - Server and API information

### API v1 - Projects
- `GET /api/v1/projects` - List all projects
  - Response: `{"total": number, "projects": Project[]}`
- `GET /api/v1/projects/{id}` - Get project by ID
  - Response: `Project`
  - Errors: 404 if not found
- `POST /api/v1/projects` - Create new project
  - Request: `ProjectCreate`
  - Response: `Project` (201 Created)
  - Errors: 400 if validation fails
- `PUT /api/v1/projects/{id}` - Update project (partial update supported)
  - Request: `ProjectUpdate`
  - Response: `Project`
  - Errors: 404 if not found, 400 if validation fails
- `DELETE /api/v1/projects/{id}` - Delete project (cascades to frames)
  - Response: `{"message": "Project deleted successfully"}`
  - Errors: 404 if not found
- `GET /api/v1/projects/{id}/frames` - Get all frames for a specific project
  - Response: `{"total": number, "frames": Frame[]}`

### API v1 - Frames
- `GET /api/v1/frames` - List all frames (optionally filtered by project_id)
  - Query params: `?project_id={id}` (optional)
  - Response: `{"total": number, "frames": Frame[]}`
- `GET /api/v1/frames/{id}` - Get frame by ID
  - Response: `Frame`
  - Errors: 404 if not found
- `POST /api/v1/frames` - Create new frame
  - Request: `FrameCreate`
  - Response: `Frame` (201 Created)
  - Errors: 400 if validation fails or project_id doesn't exist
- `PUT /api/v1/frames/{id}` - Update frame (partial update supported)
  - Request: `FrameUpdate`
  - Response: `Frame`
  - Errors: 404 if not found, 400 if validation fails
- `DELETE /api/v1/frames/{id}` - Delete frame
  - Response: `{"message": "Frame deleted successfully"}`
  - Errors: 404 if not found

### API v1 - Generator
- `GET /api/v1/generator/plugins` - Get all available plugins
  - Response: `{"total": number, "plugins": Record<string, PluginInfo>}`
- `GET /api/v1/generator/tasks` - List all tasks
  - Response: `{"total": number, "tasks": Task[]}`
- `GET /api/v1/generator/tasks/{id}` - Get task by ID
  - Response: `Task`
  - Errors: 404 if not found
- `POST /api/v1/generator/tasks` - Create new task
  - Request: `TaskCreate`
  - Response: `Task` (201 Created)
  - Errors: 400 if validation fails or plugin type not registered
- `POST /api/v1/generator/tasks/{id}/generate` - Start generation
  - Response: `{"message": "Generation started", "task_id": number}`
  - Errors: 404 if not found, 400 if task not in pending status
- `POST /api/v1/generator/tasks/{id}/stop` - Stop running task
  - Response: `{"message": "Generation stopped", "task_id": number}`
  - Errors: 404 if not found, 400 if task not running
- `GET /api/v1/generator/tasks/{id}/progress` - Get task progress
  - Response: `{"task_id": number, "status": string, "progress": number}`
  - Errors: 404 if not found

### API v1 - Models
- `GET /api/v1/models/categories` - Get all model categories (folder names)
  - Response: `{"total": number, "categories": string[]}`
- `GET /api/v1/models/{category}` - Get models in a category
  - Response: `{"category": string, "total": number, "models": ModelInfo[]}`
- `GET /api/v1/models/{category}/{filename}` - Get specific model info
  - Response: `ModelInfo`

### API v1 - System Control
- `POST /api/v1/system/emergency-stop` - Stop all running generation tasks
  - Response: `{"success": boolean, "message": string, "stopped_count": number}`
- `POST /api/v1/system/restart` - Restart server (requires run.sh)
  - Response: `{"success": boolean, "message": string}`
  - Note: Server exits with code 0, run.sh restarts it
- `POST /api/v1/system/shutdown` - Shutdown server completely
  - Response: `{"success": boolean, "message": string}`
  - Note: Server exits with code 1, run.sh stops

### API v2 - Projects (Documented with OpenAPI)
**Note:** These endpoints use `PydanticView` and are automatically documented in Swagger UI.

- `GET /api/v2/projects` - List all projects
  - Response: `{"total": number, "projects": Project[]}`
  - Auto-documented with full schema
- `GET /api/v2/projects/{project_id}` - Get project by ID
  - Response: `Project`
  - Errors: 404 if not found
- `POST /api/v2/projects` - Create new project
  - Request: `ProjectCreate`
  - Response: `Project` (201 Created)
  - Automatic validation from Pydantic
- `PUT /api/v2/projects/{project_id}` - Update project
  - Request: `ProjectUpdate` (partial)
  - Response: `Project`
  - Errors: 404 if not found
- `DELETE /api/v2/projects/{project_id}` - Delete project
  - Response: `{"message": "Project deleted successfully"}`
  - Errors: 404 if not found

**Migration:** v1 endpoints continue to work. New development should use v2 for automatic documentation.

### WebSocket Messages

**Connection:** `ws://localhost:8000/ws`

**Incoming messages (from server):**
```json
{
  "type": "metrics",
  "data": {
    "cpu_percent": 4.5,
    "memory_percent": 37.8,
    "gpu_percent": 0.0,
    "gpu_memory_percent": 0.0,
    "gpu_available": false,
    "queue_size": 0,
    "current_task": {
      "id": 123,
      "name": "Generate Frame",
      "progress": 45.5
    } // or null if no task running
  }
}
```

**Outgoing messages (from client):**
```json
{"type": "ping"}  // Client heartbeat
{"type": "close"} // Request close connection
```

**Server responses:**
```json
{"type": "pong"}  // Response to ping
```

**Update frequency:** Every 2 seconds
**Heartbeat:** 10 seconds (automatic)

---

## Database Schema

### Current Tables

**projects**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT NOT NULL) - Project name
- `width` (INTEGER NOT NULL) - Video width in pixels
- `height` (INTEGER NOT NULL) - Video height in pixels
- `fps` (INTEGER NOT NULL) - Frames per second
- `created_at` (TEXT NOT NULL) - ISO 8601 timestamp
- `updated_at` (TEXT NOT NULL) - ISO 8601 timestamp

**frames**
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `path` (TEXT NOT NULL) - Path to frame file
- `generator` (TEXT NOT NULL) - Generator information (ML model, workflow, etc.)
- `project_id` (INTEGER NOT NULL) - Foreign key to projects
- `created_at` (TEXT NOT NULL) - ISO 8601 timestamp
- `updated_at` (TEXT NOT NULL) - ISO 8601 timestamp
- **Foreign Key:** `project_id` → `projects(id)` ON DELETE CASCADE
- **Index:** `idx_frames_project_id` on `project_id`

**tasks** (generator system)
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `name` (TEXT NOT NULL) - Task name
- `type` (TEXT NOT NULL) - Plugin type
- `data` (TEXT NOT NULL) - JSON data for plugin
- `status` (TEXT NOT NULL DEFAULT 'pending') - Task status (pending/running/completed/failed/stopped)
- `progress` (REAL NOT NULL DEFAULT 0.0) - Progress 0.0 to 100.0
- `result` (TEXT) - JSON result data
- `error` (TEXT) - Error message if failed
- `created_at` (TEXT NOT NULL) - ISO 8601 timestamp
- `updated_at` (TEXT NOT NULL) - ISO 8601 timestamp
- `started_at` (TEXT) - When task started
- `completed_at` (TEXT) - When task completed
- **Index:** `idx_tasks_status` on `status`
- **Index:** `idx_tasks_type` on `type`

**users** (for future use)
- `id` (INTEGER PRIMARY KEY)
- `username` (TEXT UNIQUE NOT NULL)
- `email` (TEXT UNIQUE NOT NULL)
- `created_at` (TIMESTAMP)

**sessions** (for future use)
- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER FK → users.id)
- `session_token` (TEXT UNIQUE NOT NULL)
- `created_at` (TIMESTAMP)
- `expires_at` (TIMESTAMP)

*Note: Users and sessions tables exist for future use, but no authentication is currently implemented.*

---

## Environment Configuration

### Backend (.env)
```
HOST=0.0.0.0
PORT=8000
DB_PATH=./data/kino.db
DEBUG=true
LOG_LEVEL=INFO
```

### Backend Running Modes

**Auto-Restart Mode (Recommended for Development):**
```bash
cd backend
./run.sh
```
- Automatically restarts on crashes or via UI "Restart Server" button
- Stops on Ctrl+C or UI "Shutdown" button
- Best for active development

**Direct Mode (For debugging):**
```bash
cd backend
source venv/bin/activate
python main.py
```
- Single run, no auto-restart
- Good for debugging specific issues

### Frontend

**Node Version Manager (nvm):**
- ⚠️ **IMPORTANT:** Always run `nvm use --lts` before any frontend commands
- This activates the LTS version of Node.js
- Required for npm, development server, and builds

**Development:**

*Via command line:*
```bash
# Activate Node.js LTS
nvm use --lts

# Install dependencies
cd frontend
npm install

# Run dev server
npm run dev
```

*Via VS Code workspace:*
- ✅ Launch configurations include nvm activation automatically
- Run → Start Debugging → "Frontend: Dev Server"
- Or use task: "Frontend: Start Dev Server"
- Or compound: "Full Stack (Auto-Restart)" - recommended for development
- Or compound: "Full Stack (Direct)" - for debugging

**Workspace Launch Configurations:**
- **Backend: Auto-Restart (run.sh)** - Uses auto-restart script
- **Python: Backend Server (Direct)** - Direct Python execution for debugging
- **Frontend: Dev Server** - Vite dev server with nvm
- **Full Stack (Auto-Restart)** - Both backend (with auto-restart) + frontend
- **Full Stack (Direct)** - Both backend (direct) + frontend

- Default dev server: `http://localhost:5173` (Vite default)
- Backend URL should be configurable via environment variables

---

## Development Status

### ✅ Completed
- [x] Project structure setup (frontend + backend)
- [x] Backend: aiohttp server with CORS
- [x] Backend: Basic REST API endpoints
- [x] Backend: Database setup with aiosqlite
- [x] Backend: Request validation with Pydantic
- [x] Backend: MVC architecture (Model-Service-Controller)
- [x] Backend: Project CRUD API (full REST implementation)
- [x] Backend: Frame CRUD API (with foreign key to Projects)
- [x] Backend: Generator system with plugin architecture
- [x] Backend: Task management for generation tasks
- [x] Backend: Example plugin (template for new plugins)
- [x] Backend: Plugin loader and registry system
- [x] Backend: Pydantic models with validation
- [x] Backend: Service layer for business logic
- [x] Backend: Frame storage directory structure
- [x] Backend: AI models storage structure (DiffusionModels, StableDiffusion, Lora, TextEncoders, ClipVision, VAE)
- [x] Backend: ComfyUI full integration (comfy/ directory with complete backend)
- [x] Backend: Bricks connector layer (6 bricks: checkpoint, encode, latent, ksampler, decode, lora)
- [x] Backend: LoRA brick (load and apply LoRA to model and CLIP)
- [x] Backend: Bricks documentation (README.md with examples)
- [x] Backend: Config module for paths management
- [x] Backend: Database indexes for performance
- [x] Backend: Models storage with .gitkeep structure
- [x] Frontend: React 19 + TypeScript + Vite setup
- [x] Frontend: FrameViewer component (70% - upper section)
- [x] Frontend: Timeline component (30% - filmstrip with horizontal scroll)
- [x] Frontend: Playback controls (first, prev, play/pause, next, last)
- [x] Frontend: Keyboard shortcuts (arrows, space, home, end)
- [x] Frontend: Play functionality with FPS-based timing
- [x] Frontend: Auto-scroll to selected frame in timeline
- [x] Frontend: Dark theme UI with modern styling
- [x] Frontend: Lazy loading for frame images
- [x] Frontend: MenuBar component (File, Edit, Help menus)
- [x] Frontend: Base Modal component (reusable with animations)
- [x] Frontend: NewProjectModal (create project form)
- [x] Frontend: ProjectsModal (manage projects: open, select, delete with cascade)
- [x] Frontend: FindFrameModal (jump to frame by number)
- [x] Frontend: DeleteFrameModal (confirmation dialog)
- [x] Frontend: AboutModal (app info, version 1.0.0)
- [x] Frontend: First API integration (AboutModal → backend /health)
- [x] Frontend: Backend status monitoring (online/offline, CPU, memory)
- [x] Frontend: API client (client.ts) with types matching backend
- [x] Frontend: Projects API integration (create, list, load)
- [x] Frontend: Frames API integration (get by project)
- [x] Frontend: Current project state management
- [x] Frontend: Automatic frame loading when project selected
- [x] Frontend: Project name display in MenuBar header
- [x] Frontend: Dynamic window title (Kino - ProjectName)
- [x] Frontend: Fixed TypeScript type imports (import type)
- [x] Frontend: Virtual 'add frame' button ('+' card always in timeline)
- [x] Frontend: Smart timeline UX (no empty state, always show add button)
- [x] Frontend: Projects management (delete multiple projects with confirmation)
- [x] Frontend: Cascade deletion (projects + frames deleted together)
- [x] Frontend: Click project card to open (no separate button needed)
- [x] Frontend: SelectGeneratorModal (choose generator plugin)
- [x] Frontend: GenerateFrameModal (dynamic form from plugin parameters)
- [x] Frontend: Model selection dropdown (auto-loads models from backend)
- [x] Frontend: Fixed keyboard shortcuts (don't block input fields)
- [x] Backend: Custom CORS middleware (replaced aiohttp-cors)
- [x] Backend: CORS support for PydanticView routes
- [x] Backend: CASCADE DELETE for frames when project deleted
- [x] Backend: ModelService for managing AI models
- [x] Backend: Models API (categories, models by category)
- [x] Backend: Plugin visibility control (visible field)
- [x] Backend: Static files serving for frames
- [x] Git ignore files for both projects
- [x] Monorepo setup with single git repository
- [x] Basic health check and info endpoints
- [x] PROJECT_CONTEXT.md for AI assistance
- [x] .cursorrules for consistent code generation
- [x] OpenAPI/Swagger documentation with aiohttp-pydantic
- [x] API v2 endpoints with automatic documentation
- [x] API_DOCUMENTATION.md guide
- [x] SDXL plugin fully implemented and tested (with ComfyUI backend)
- [x] Plugin system with async support and progress tracking
- [x] Successful test generation (512x512, 16 steps, ~53 seconds)
- [x] LoRA support in SDXL plugin (multiple LoRAs with strength controls)
- [x] Models API for listing AI models by category
- [x] System control API (emergency stop, restart, shutdown)
- [x] Backend auto-restart script (run.sh)
- [x] Frontend: System menu with server control
- [x] Frontend: LoRA list field component (inline layout)
- [x] Frontend: Dynamic form generation based on plugin parameter types
- [x] Frontend: Model selection dropdowns (auto-populated from backend)
- [x] Frontend: Sampler dropdown (selection type)
- [x] Frontend: Width/Height in single row layout
- [x] SDXL defaults updated (CFG: 3.5, Steps: 32)
- [x] Parameter types: string, integer, float, model_selection, selection, lora_list
- [x] WebSocket real-time communication (/ws endpoint)
- [x] System monitoring (CPU, GPU, Memory) via WebSocket
- [x] Frontend: useWebSocket hook with auto-reconnect
- [x] Frontend: Real-time metrics display in MenuBar
- [x] Frontend: Connection status indicator
- [x] Task queue monitoring via WebSocket
- [x] Current task progress in real-time
- [x] GPU monitoring support (Intel XPU + NVIDIA CUDA)
- [x] Backend: GPU auto-detection via PyTorch (torch.xpu / torch.cuda)
- [x] Backend: GPU type identification (xpu/cuda/none)
- [x] Backend: GPU utilization and memory monitoring
- [x] Backend: XPU metrics via torch.xpu.memory_allocated/reserved
- [x] Backend: CUDA metrics via nvidia-ml-py3 (with PyTorch fallback)
- [x] Frontend: GPU type display in MenuBar (XPU/CUDA)
- [x] Frontend: GPU utilization percentage display
- [x] Frontend: VRAM (GPU memory) percentage display
- [x] Frontend: Centralized configuration constants (src/config/)
- [x] Frontend: API URLs centralized (API_BASE_URL, WS_URL)
- [x] Frontend: App name and version constants (APP_NAME, APP_VERSION)
- [x] Frontend: Helper function getFrameImageUrl()
- [x] Frontend: Version synced with package.json (1.0.0)
- [x] Test script: GPU detection test (services/test_gpu_detection.py)
- [x] Backend: Generation parameters JSON storage (bricks/generation_params.py)
- [x] Backend: Auto-save parameters with each generated frame
- [x] Backend: Load parameters for frame regeneration
- [x] SDXL plugin: Parameters saved to JSON alongside images
- [x] Documentation: Generation parameters guide (README_PARAMS.md)
- [x] Backend: Seed parameter for reproducible generation
- [x] SDXL plugin: Seed support (optional, random if not specified)
- [x] Bricks: common_ksampler returns used seed
- [x] Auto-save actual seed used (even if random was generated)
- [x] Frontend: Width/Height auto-filled from project dimensions
- [x] Frontend: "from project" label when using project dimensions
- [x] Frontend: Fixed null default value handling in GenerateFrameModal
- [x] Smart defaults: Project dimensions override plugin defaults
- [x] Backend: ComfyUI constants module (40+ samplers, 9 schedulers)
- [x] Backend: Full sampler list from ComfyUI (KSAMPLER_NAMES + extras)
- [x] Backend: Full scheduler list from ComfyUI (SCHEDULER_HANDLERS)
- [x] SDXL plugin: Scheduler parameter added
- [x] SDXL plugin: Recommended samplers list for better UX
- [x] Documentation: Sampler and scheduler combinations guide
- [x] Backend: Migrated to full ComfyUI installation (backend/ComfyUI/)
- [x] Bricks: sys.path integration for ComfyUI imports
- [x] Bricks: Updated imports from old comfy/ to new ComfyUI/comfy/
- [x] Requirements: Added all ComfyUI dependencies
- [x] Testing: ComfyUI integration test script
- [x] Documentation: ComfyUI/INTEGRATION.md guide

### 🔄 In Progress
- [ ] Frontend: Implement virtual scrolling with react-window
- [ ] Frontend: Frame reload after generation completes
- [ ] Migrate all v1 handlers to v2 (with OpenAPI docs)

### 📋 Planned
- [ ] More generator plugins (Stable Diffusion, ComfyUI workflows, etc.)
- [ ] Video timeline and editing features
- [ ] WebSocket support for real-time generation progress
- [ ] Frontend state management (context or library TBD)
- [ ] Error boundary and loading states
- [ ] Production deployment configuration
- [ ] Model management API (upload, list, delete models)
- [ ] Batch generation support
- [ ] Task queue management with priorities

---

## Key Decisions & Rationale

1. **Why aiohttp over FastAPI?**
   - Already specified in requirements
   - Gives more control over WebSocket implementation
   - Lightweight and performant for async operations

2. **Why SQLite?**
   - Lightweight, no separate server needed
   - Sufficient for single-node deployment
   - Easy to backup and migrate
   - aiosqlite provides async interface

3. **Why no authentication?**
   - Project requirement: public single-page application
   - Simplifies architecture and development
   - Can be added later if requirements change

4. **Why Vite over Create React App?**
   - Faster development server
   - Better TypeScript support
   - Modern build tool with excellent defaults
   - Smaller bundle sizes

5. **Why ComfyUI?**
   - Powerful workflow-based approach for image generation
   - Supports multiple models and custom nodes
   - Well-maintained and active community
   - Flexible integration possibilities

6. **AI Models Storage Structure**
   - Organized by model type for easy management
   - Separate directories prevent confusion
   - Allows for multiple models of same type
   - Makes it easy to add/remove models

7. **Plugin-based Generator Architecture**
   - Modular design allows easy addition of new generators
   - Each plugin in its own directory (directory name = plugin type)
   - Main file of each plugin is `loader.py`
   - Auto-discovery and loading on server start
   - Plugins implement BasePlugin interface
   - Supports async generation with progress callbacks
   - Can stop running tasks
   - Uniform API regardless of plugin implementation

8. **Bricks Layer (ComfyUI Connector)**
   - Abstraction layer between Kino and ComfyUI
   - `comfy_bricks.py`: Wraps ComfyUI functions (load checkpoint, encode prompts, sample, decode VAE)
   - `frames_routine.py`: Frame saving utilities
   - Makes ComfyUI integration simpler and cleaner
   - Plugins use bricks instead of calling ComfyUI directly
   - Easy to swap or update ComfyUI backend without changing plugins

9. **ComfyUI Backend Integration**
   - Full ComfyUI framework in `ComfyUI/` directory
   - Complete installation with all features (server, API, custom nodes)
   - sys.path integration via bricks layer for clean imports
   - Provides powerful model loading, sampling, and encoding capabilities
   - Supports multiple model architectures (SD, SDXL, Flux, Aura, etc.)
   - 40+ sampling algorithms and 9 noise schedulers
   - Memory-efficient model management
   - Can use ComfyUI updates and custom nodes
   - Integration documented in `ComfyUI/INTEGRATION.md`

10. **Configuration Management**
    - Centralized `config.py` for all paths
    - `MODELS_DIR`: AI models storage
    - `DATA_DIR`: Database and generated files
    - `FRAMES_DIR`: Generated frame images
    - `PROJECTS_DIR`: Project-specific data
    - Auto-creates directories on import

11. **Monorepo Structure**
    - Single git repository for backend + frontend
    - Synchronized versioning and API changes
    - Shared documentation (PROJECT_CONTEXT.md in root)
    - Separate .gitignore for each subproject
    - Root .gitignore for common rules (IDE, OS files)
    - Atomic commits for full-stack features
    - Simplified deployment and CI/CD

12. **GPU Monitoring Strategy**
    - **PyTorch-based detection:** Uses existing PyTorch dependency for GPU detection
    - **Multi-vendor support:** Intel XPU (Arc GPU) and NVIDIA CUDA
    - **Auto-detection:** Automatically detects available GPU type on server start
    - **XPU metrics:** Uses `torch.xpu.memory_allocated()` and `torch.xpu.memory_reserved()`
      - GPU utilization estimated from memory usage (80% heuristic)
      - More accurate solution would require Intel level-zero library
    - **CUDA metrics:** Primary via nvidia-ml-py3 (pynvml), fallback to PyTorch
    - **Graceful degradation:** Works without GPU, shows CPU-only mode
    - **Real-time updates:** GPU metrics broadcast via WebSocket every 2 seconds
    - **Frontend display:** Shows GPU type (XPU/CUDA), utilization %, VRAM %

13. **Generation Parameters Storage**
    - **Auto-save:** Every generated frame gets a companion JSON file
    - **Same naming:** `frame_001.png` → `frame_001.json` (same base name)
    - **Location:** JSON files stored alongside images in frames directory
    - **Content:** All generation parameters (prompt, model, settings, LoRAs, seed, etc.)
    - **Metadata:** Plugin name, version, timestamp, task ID
    - **Seed support:**
      - Optional seed parameter for exact reproducibility
      - If not provided, random seed is generated
      - Actual seed always saved to JSON (even if random)
      - Same seed + parameters = identical image
    - **Reproducibility:** Can regenerate identical frames from JSON
    - **Variations:** Modify JSON parameters to create variations
    - **API:** `save_generation_params()`, `load_generation_params()` utilities
    - **Format:** Human-readable JSON with 2-space indentation, UTF-8 encoding

---

## Testing Strategy

### Backend
- Manual testing with curl for API endpoints
- Server startup/shutdown lifecycle verified
- Database initialization tested
- **Plugin testing:**
  - SDXL plugin tested with real model (cyberrealisticPony_v130.safetensors, 6.5GB)
  - Successful image generation: 512x512, 16 steps, ~53 seconds
  - Progress tracking verified (0-100%)
  - Model caching works correctly
  - ComfyUI integration functioning properly
- **API documentation:**
  - Swagger UI tested at `/api/docs`
  - OpenAPI spec generation verified
  - API v2 endpoints with PydanticView working

### Frontend
- To be implemented

---

## Notes for AI Code Generation

### 🔴 CRITICAL RULES (Project Rules - Always Follow)

1. **ALWAYS UPDATE THIS FILE** (`PROJECT_CONTEXT.md`) after ANY changes:
   - New features, architectural changes, dependencies
   - This file is the single source of truth
   - Maintains continuity between sessions
   - Update "Last Updated" date at the top

2. **ALWAYS USE CONTEXT7** for library documentation:
   - Use Context7 MCP tools for: aiohttp, aiohttp-pydantic, Pydantic v2, PyTorch, React 18, Vite
   - Never assume API details - fetch actual documentation
   - Ensures up-to-date and correct usage

3. **FOLLOW TECH STACK** defined in this file:
   - Backend: Python 3.12, aiohttp, aiohttp-pydantic, Pydantic v2, aiosqlite, PyTorch, ComfyUI
   - Frontend: TypeScript, React 18, Vite
   - Database: SQLite with aiosqlite
   - API: REST + OpenAPI/Swagger

### Standard Development Rules

4. **Check this file first** before generating code to ensure consistency
5. **Follow established patterns** in existing code
6. **Use English** for all code, comments, and documentation
7. **Maintain type safety** with Pydantic (backend) and TypeScript (frontend)
8. **Keep models synchronized** between frontend and backend
9. **Test endpoints** after creation using curl or similar tools
10. **Document new endpoints** in this file's API section
11. **Update status sections** as features are completed

### Documentation Update Chain
When making changes, update in this order:
1. Code implementation
2. Docstrings and inline comments
3. MODULE/README.md (if exists)
4. **PROJECT_CONTEXT.md** (ALWAYS - this file)
5. Update "Last Updated" date

---

## Common Patterns

### Adding a New API Endpoint

1. Create handler in appropriate file under `handlers/`
2. Add route in `routes.py` with CORS configuration
3. Define Pydantic models for validation
4. Update this file's API documentation
5. Test with curl
6. Create corresponding TypeScript interface in frontend

### Adding a Database Table

1. Add schema in `database.py` `_init_tables()` method
2. Create access methods in `database.py`
3. Add Pydantic models for the data
4. Update this file's database schema section

### MVC Pattern for New Resource (Example: Projects)

1. **Model** (`models/resource.py`):
   - Create Pydantic models: `ResourceCreate`, `ResourceUpdate`, `ResourceResponse`
   - Add validation rules with Pydantic validators

2. **Service** (`services/resource_service.py`):
   - Create `ResourceService` class with database instance
   - Implement business logic methods: `get_all`, `get_by_id`, `create`, `update`, `delete`
   - Use type hints for parameters and return values

3. **Controller** (`handlers/resource.py`):
   - Create async handler functions for each endpoint
   - Handle request parsing and validation
   - Call service methods
   - Return appropriate responses with status codes
   - Handle errors and return proper error responses

4. **Routes** (`routes.py`):
   - Import handlers
   - Register routes with CORS
   - Follow RESTful conventions

5. **Database** (`database.py`):
   - Add table schema in `_init_tables()`
   - Ensure proper indexes and constraints

### Using Bricks (ComfyUI Connector)

The `bricks` layer provides convenient wrappers for ComfyUI operations:

```python
import bricks.comfy_bricks as comfy_bricks
from config import Config

# 1. Load checkpoint
ckpt_path = os.path.join(Config.MODELS_DIR, "StableDiffusion", "model.safetensors")
(model, clip, vae, _) = comfy_bricks.load_checkpoint_plugin(ckpt_path)

# 2. Encode prompts
positive = comfy_bricks.clip_encode(clip, "beautiful landscape")
negative = comfy_bricks.clip_encode(clip, "blurry, low quality")

# 3. Generate latent image
latent = comfy_bricks.generate_latent_image(width=512, height=512)

# 4. Run KSampler
sample = comfy_bricks.common_ksampler(
    model, latent, positive, negative,
    steps=20, cfg=7.5, sampler_name='dpmpp_2m_sde'
)

# 5. Decode VAE
image = comfy_bricks.vae_decode(vae, sample)

# 6. Save frame
from bricks.frames_routine import save_frame
frames = save_frame(project_name, frame_id, image)
```

**Available samplers:** 40+ algorithms from ComfyUI (see `bricks/comfy_constants.py`)
- Recommended: `euler`, `euler_ancestral`, `heun`, `dpmpp_2m`, `dpmpp_2m_sde` (default), `dpmpp_3m_sde`, `ddim`, `uni_pc`, `lcm`
- All categories: K-diffusion, DPM/DPM++, classic, advanced, resolution, experimental

**Available schedulers:** 9 types (see `bricks/comfy_constants.py`)
- Options: `normal`, `karras`, `exponential`, `sgm_uniform` (default), `simple`, `ddim_uniform`, `beta`, `linear_quadratic`, `kl_optimal`
- Best for quality: `karras`, best for speed: `normal`

**Using LoRA with Bricks:**

```python
import bricks.comfy_bricks as comfy_bricks

# Load checkpoint first
(model, clip, vae, _) = comfy_bricks.load_checkpoint_plugin(ckpt_path)

# Apply LoRA (can be called multiple times for multiple LoRAs)
lora_path = os.path.join(Config.MODELS_DIR, "Lora", "my_lora.safetensors")
model, clip = comfy_bricks.load_lora(
    lora_path,
    model,
    clip,
    strength_model=1.0,  # 0.0 to 2.0
    strength_clip=1.0    # 0.0 to 2.0
)

# Continue with generation using modified model and clip
```

### Plugin Parameter Types

The dynamic form generator supports the following parameter types:

1. **`string`** - Text input or textarea (auto-detects prompts)
   ```python
   'prompt': {
       'type': 'string',
       'required': True,
       'description': 'Text prompt',
       'example': 'A beautiful landscape'
   }
   ```

2. **`integer`** - Number input (step=1)
   ```python
   'steps': {
       'type': 'integer',
       'default': 32,
       'min': 1,
       'max': 150
   }
   ```

3. **`float`** - Decimal number input (step=0.01)
   ```python
   'cfg_scale': {
       'type': 'float',
       'default': 3.5,
       'min': 1.0,
       'max': 20.0
   }
   ```

4. **`selection`** - Dropdown with predefined options
   ```python
   'sampler': {
       'type': 'selection',
       'default': 'dpmpp_2m_sde',
       'options': ['euler', 'euler_a', 'dpmpp_2m', ...]
   }
   ```

5. **`model_selection`** - Dropdown auto-populated from models_storage
   ```python
   'model_name': {
       'type': 'model_selection',
       'category': 'StableDiffusion',  # Folder name in models_storage
       'required': True
   }
   ```

6. **`lora_list`** - Dynamic list of LoRA configurations
   ```python
   'loras': {
       'type': 'lora_list',
       'default': [],
       'item_schema': {
           'lora_name': {
               'type': 'model_selection',
               'category': 'Lora'
           },
           'strength_model': {
               'type': 'float',
               'default': 1.0,
               'min': 0.0,
               'max': 2.0
           },
           'strength_clip': {
               'type': 'float',
               'default': 1.0,
               'min': 0.0,
               'max': 2.0
           }
       }
   }
   ```

### Creating a New Generator Plugin

1. **Create plugin directory** in `plugins/`:
   ```bash
   mkdir backend/plugins/my_plugin
   ```

2. **Create `__init__.py`**:
   ```python
   # plugins/my_plugin/__init__.py
   """My plugin package"""
   ```

3. **Create `loader.py`** with BasePlugin implementation:
   ```python
   # plugins/my_plugin/loader.py
   from typing import Dict, Any, Optional, Callable
   from ..base_plugin import BasePlugin, PluginResult

   class MyPlugin(BasePlugin):
       async def generate(self, task_id, data, progress_callback):
           # Your code here
           self.update_progress(50.0, progress_callback)
           return PluginResult(success=True, data={...})

       async def stop(self):
           self.should_stop = True

       @classmethod
       def get_plugin_info(cls):
           return {'name': 'my_plugin', ...}
   ```

4. **Restart server** - Plugin will be auto-loaded

5. **Use in tasks**:
   ```json
   {"type": "my_plugin", "data": {...}}
   ```

**Note:** Directory name becomes the plugin type in the API!

---

## Future Considerations

- Rate limiting if needed
- Caching strategy for ML model inference
- File upload handling (if required)
- Logging and monitoring improvements
- Docker containerization
- CI/CD pipeline

---

**Remember:** This file is the source of truth for project context. Keep it updated!

