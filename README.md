# Kino - AI-Powered Video Project Management

**Kino** is a modern video project management and editing application with integrated AI/ML functionality for frame generation and processing.

## 🎯 Project Overview

Kino combines a powerful backend API with ComfyUI integration and an intuitive React frontend to provide a complete solution for managing video projects, generating AI-powered frames, and editing timelines.

### Key Features

- 🎬 **Project Management** - Create, manage, and organize video projects
- 🖼️ **Frame Management** - Import, generate, and edit individual frames
- 🤖 **AI Frame Generation** - Integrated SDXL and ComfyUI for AI-powered image generation
- 📽️ **Timeline Editor** - Visual filmstrip timeline with playback controls
- 🔌 **Plugin System** - Extensible architecture for custom generators
- 📊 **Task Management** - Async task queue for long-running operations
- 📚 **API Documentation** - Auto-generated OpenAPI/Swagger documentation

---

## 🏗️ Architecture

This is a **monorepo** containing both backend and frontend:

```
/qs/kino/
├── backend/              # Python backend (aiohttp + ComfyUI)
├── frontend/             # React frontend (TypeScript + Vite)
├── PROJECT_CONTEXT.md    # AI assistant context & development guide
└── README.md             # This file
```

### Backend (Python)

- **Framework:** aiohttp (async web framework)
- **Database:** SQLite with aiosqlite (async driver)
- **Validation:** Pydantic v2
- **AI/ML:** PyTorch, ComfyUI, SDXL
- **API Docs:** aiohttp-pydantic (OpenAPI/Swagger)

### Frontend (React)

- **Framework:** React 19.1 + TypeScript
- **Build Tool:** Vite 7.1
- **UI:** Custom components with dark theme
- **State:** React hooks (useState, useEffect, useCallback)

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+** (for backend)
- **Node.js LTS** (for frontend, managed via nvm)
- **nvm** (Node Version Manager)
- **Git**

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd kino
```

2. **Backend Setup**

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend
python main.py
```

Backend will start on `http://localhost:8000`

3. **Frontend Setup**

```bash
cd frontend

# Activate Node.js LTS
nvm use --lts

# Install dependencies
npm install

# Run the frontend
npm run dev
```

Frontend will start on `http://localhost:5173`

---

## 📖 Documentation

### Backend Documentation

- **Main README:** [backend/README.md](backend/README.md)
- **API Documentation:** [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md)
- **Plugin System:** [backend/plugins/README.md](backend/plugins/README.md)
- **Swagger UI:** http://localhost:8000/api/docs (when backend is running)
- **OpenAPI Spec:** http://localhost:8000/api/docs/swagger.json

### Frontend Documentation

- **Main README:** [frontend/README.md](frontend/README.md)

### Development Guide

- **Project Context:** [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Complete architecture, conventions, and AI assistant guide

---

## 🎮 Usage

### Creating a Project

1. Open the application at `http://localhost:5173`
2. Go to **File → New Project**
3. Fill in project details (name, dimensions, FPS)
4. Click **Create**

### Managing Projects

- **Open Project:** File → Projects → Click on project card
- **Delete Projects:** File → Projects → Check projects → Delete Selected

### Working with Frames

- **View Frames:** Open a project to see frames in the timeline
- **Navigate:** Use playback controls or arrow keys
- **Play/Pause:** Click play button or press Space/K
- **Generate Frames:** Coming soon (generator UI in progress)

### Keyboard Shortcuts

- `←` / `→` - Previous/Next frame
- `Home` / `End` - First/Last frame
- `Space` / `K` - Play/Pause
- `Esc` - Close modal dialogs

---

## 🔧 Development

### Backend Development

```bash
cd backend
source venv/bin/activate
python main.py
```

The backend runs on port **8000** and provides:
- REST API endpoints (`/api/v1/*`, `/api/v2/*`)
- Health check (`/health`)
- Static files (`/data/frames/*`)
- Swagger UI (`/api/docs`)

### Frontend Development

**Important:** Always activate nvm before running frontend commands:

```bash
cd frontend
nvm use --lts  # Required!
npm run dev
```

The frontend runs on port **5173** (Vite default) and hot-reloads on changes.

### VS Code Workspace

Open `kino.code-workspace` in VS Code for:
- Pre-configured launch configurations (Frontend, Backend, Full Stack)
- Debugging support
- Tasks for common operations
- Automatic nvm activation in tasks

---

## 🗂️ Project Structure

### Backend

```
backend/
├── main.py                 # Application entry point
├── routes.py               # Route configuration
├── config.py               # Configuration (paths, settings)
├── database.py             # Database utilities
├── handlers/               # Request handlers (controllers)
├── models/                 # Pydantic data models
├── services/               # Business logic services
├── plugins/                # Generator plugin system
│   ├── base_plugin.py     # Base plugin class
│   ├── plugin_loader.py   # Plugin registry
│   ├── sdxl/              # SDXL generator plugin
│   └── example/           # Example plugin template
├── bricks/                 # ComfyUI connector layer
├── comfy/                  # ComfyUI backend integration
├── data/                   # Runtime data (gitignored)
│   ├── frames/            # Generated frame images
│   └── kino.db            # SQLite database
└── models_storage/         # AI models storage (gitignored)
```

### Frontend

```
frontend/
├── src/
│   ├── main.tsx           # Entry point
│   ├── App.tsx            # Main application component
│   ├── api/               # Backend API client
│   │   └── client.ts      # API methods and types
│   ├── components/        # React components
│   │   ├── MenuBar.tsx    # Top menu bar
│   │   ├── FrameViewer.tsx # Frame display (70%)
│   │   ├── Timeline.tsx   # Filmstrip timeline (30%)
│   │   └── modals/        # Modal dialogs
│   └── assets/            # Static assets
├── public/                # Public assets
└── vite.config.ts         # Vite configuration
```

---

## 🧪 Testing

### Backend Testing

```bash
cd backend
source venv/bin/activate

# Run specific test
python test_script.py

# Check health endpoint
curl http://localhost:8000/health
```

### Frontend Testing

The frontend includes React DevTools support. Open the browser console to see logs and state.

---

## 🤝 Contributing

1. Follow the conventions in [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)
2. All code, comments, and documentation must be in **English**
3. Update `PROJECT_CONTEXT.md` after significant changes
4. Use TypeScript types and Python type hints
5. Test changes before committing

### Code Style

- **Backend:** Follow PEP 8, use async/await, type hints required
- **Frontend:** Use functional components, TypeScript strict mode
- **Both:** No trailing whitespace, files end with newline

---

## 📋 Status

### ✅ Completed Features

- Backend API (REST, CORS, validation)
- Database with SQLite (projects, frames, tasks)
- Plugin system with SDXL integration
- ComfyUI backend integration
- Frontend UI (FrameViewer, Timeline, MenuBar)
- Project management (CRUD operations)
- Frame loading and display
- Playback controls and keyboard shortcuts
- OpenAPI/Swagger documentation

### 🔄 In Progress

- Generator UI (task management, progress tracking)
- Virtual scrolling for large timelines
- Frame generation workflow

### 📋 Planned

- More generator plugins (Stable Diffusion, custom workflows)
- Video export functionality
- WebSocket for real-time progress updates
- Model management UI
- Batch generation support

---

## ⚠️ Known Issues

### GGUF Model Loading
- **Issue:** GGUF quantized models fail to load with `invalid load key, '\\x00'` error
- **Cause:** ComfyUI-GGUF uses relative imports that prevent proper module loading
- **Affected:** Wan22-I2V plugin with GGUF models (wan2.2_i2v_high_noise_14B_Q6_K.gguf, umt5-xxl-encoder-Q6_K.gguf)
- **Workaround:** Use safetensors models instead of GGUF format
- **Status:** Under investigation - need alternative GGUF loading solution

### PyTorch weights_only
- **Issue:** PyTorch 2.6+ changed default `torch.load` behavior to `weights_only=True`
- **Cause:** Security change in PyTorch for preventing arbitrary code execution
- **Solution:** Implemented patch for GGUF files with `weights_only=False`
- **Status:** Partially resolved - patch applied but GGUF format incompatibility remains

### Generator Service
- **Issue:** Tasks remain in "pending" status and don't start automatically
- **Cause:** Generator service doesn't process tasks from queue automatically
- **Workaround:** Use `/api/v1/generator/tasks/{id}/generate` endpoint to manually start tasks
- **Status:** Identified - needs investigation of automatic task processing

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 🆘 Support

For issues, questions, or contributions:

1. Check [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for architecture details
2. Review [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md) for API usage
3. See backend/frontend READMEs for component-specific info

---

## 🔗 Links

- **Backend:** http://localhost:8000
- **Frontend:** http://localhost:5173
- **API Docs (Swagger):** http://localhost:8000/api/docs
- **API Docs (ReDoc):** http://localhost:8000/api/redoc
- **Health Check:** http://localhost:8000/health

---

**Built with ❤️ using Python, React, and AI**

