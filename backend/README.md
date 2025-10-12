# Kino Backend

AI-powered video project management and frame generation backend.

## Tech Stack

- **Python 3.12** - Programming language
- **aiohttp** - Async web framework
- **aiohttp-cors** - CORS support
- **aiohttp-pydantic** - OpenAPI/Swagger documentation
- **Pydantic v2** - Data validation and models
- **aiosqlite** - Async SQLite database
- **PyTorch** - Machine learning framework
- **ComfyUI** - Image generation backend
- **Transformers, torchvision, torchaudio** - ML models

## Installation

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

## Running

### Auto-Restart Mode (Recommended for Development)

Use `run.sh` for automatic restart on crashes or when using the "Restart Server" feature:

```bash
./run.sh
```

This script will:
- Automatically restart the server if it crashes
- Restart when you use the "Restart Server" button in the UI
- Stop completely on Ctrl+C or when using "Shutdown" from UI

### Direct Mode

For debugging or one-time runs:

```bash
# Activate virtual environment
source venv/bin/activate

# Start server
python main.py
```

Server will start on `http://0.0.0.0:8000`

### System Control

The backend provides system control endpoints accessible via the UI (System menu):
- **Emergency Stop** - Stop all running generation tasks
- **Restart Server** - Restart the backend (only works with `run.sh`)
- **Shutdown** - Gracefully stop the server

## API Documentation

### 📚 Swagger UI (Recommended)
Interactive API documentation with testing capabilities:
```
http://localhost:8000/api/docs
```

### 📄 OpenAPI Specification
JSON specification for import to Postman/Insomnia:
```
http://localhost:8000/api/docs/spec
```

### 📖 Full Documentation
Complete guide available in [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

## Quick Start

### 1. Create a project
```bash
curl -X POST http://localhost:8000/api/v2/projects \
  -H "Content-Type: application/json" \
  -d '{"name":"My Project","width":1920,"height":1080,"fps":30}'
```

### 2. Generate an image (SDXL)
```bash
# Create task
curl -X POST http://localhost:8000/api/v1/generator/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Generate Frame",
    "type": "sdxl",
    "data": {
      "prompt": "beautiful landscape",
      "model_name": "your_model.safetensors",
      "width": 512,
      "height": 512,
      "steps": 20
    }
  }'

# Start generation (use task_id from previous response)
curl -X POST http://localhost:8000/api/v1/generator/tasks/1/generate

# Check progress
curl http://localhost:8000/api/v1/generator/tasks/1/progress
```

### 3. Check server health
```bash
curl http://localhost:8000/health
```

## Main Features

### 🎨 Generator Plugins
- **SDXL Plugin** - Stable Diffusion XL image generation
- **Example Plugin** - Template for new plugins
- Auto-discovery and loading
- Async with progress tracking
- See `plugins/README.md`

### 🔧 ComfyUI Integration
- Full ComfyUI backend in `comfy/` directory
- Bricks layer (`bricks/`) for easy integration
- Support for multiple model architectures
- Extensive sampler selection

### 📦 Models Storage
- `models_storage/StableDiffusion/` - SD/SDXL checkpoints
- `models_storage/Lora/` - LoRA adapters
- `models_storage/VAE/` - VAE models
- See `models_storage/README.md`

### 🗄️ Database
- SQLite with async driver (aiosqlite)
- Projects, Frames, Tasks tables
- Automatic migrations

### 📡 API Versions
- **v1** - Legacy REST API
- **v2** - OpenAPI documented (PydanticView)
- Both versions work simultaneously

## Project Structure

```
backend/
├── main.py                 # Entry point, OpenAPI setup
├── routes.py               # Routes (v1 + v2)
├── config.py               # Configuration (paths)
├── database.py             # Database utilities
├── API_DOCUMENTATION.md    # Complete API guide
├── handlers/               # Request handlers
│   ├── api.py             # v1 handlers
│   ├── api_documented.py  # v2 handlers (OpenAPI)
│   ├── projects.py        # Projects CRUD
│   ├── frames.py          # Frames CRUD
│   └── generator.py       # Generator/tasks
├── models/                 # Pydantic models
├── services/               # Business logic
├── bricks/                 # ComfyUI connector
│   ├── comfy_bricks.py    # Wrapper functions
│   └── frames_routine.py  # Frame utilities
├── comfy/                  # ComfyUI backend
├── plugins/                # Generator plugins
│   ├── sdxl/              # SDXL plugin
│   └── example/           # Example plugin
├── models_storage/         # AI models (.gitkeep)
├── data/                   # Database & frames
├── scripts/                # Utility scripts
└── venv/                  # Virtual environment
```

## Links

- **Main Context:** [../PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) - Complete project documentation
- **API Docs:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) - API usage guide
- **Plugins:** [plugins/README.md](./plugins/README.md) - Plugin development
- **Models:** [models_storage/README.md](./models_storage/README.md) - Models guide
- **SDXL Plugin:** [plugins/sdxl/README.md](./plugins/sdxl/README.md) - SDXL documentation

