"""
API routes configuration
CORS is handled by middleware in main.py
"""
from aiohttp import web

from handlers import health, api, projects, frames, generator, api_documented, models
from config import Config


def setup_routes(app: web.Application):
    """Configure all application routes"""

    # Health check endpoint
    app.router.add_get('/health', health.health_check)

    # API v1 routes - General
    app.router.add_get('/api/v1/hello', api.hello)
    app.router.add_post('/api/v1/echo', api.echo)
    app.router.add_get('/api/v1/info', api.info)

    # API v1 routes - Projects
    app.router.add_get('/api/v1/projects', projects.list_projects)
    app.router.add_get('/api/v1/projects/{id}', projects.get_project)
    app.router.add_post('/api/v1/projects', projects.create_project)
    app.router.add_put('/api/v1/projects/{id}', projects.update_project)
    app.router.add_delete('/api/v1/projects/{id}', projects.delete_project)

    # Get frames for a specific project
    app.router.add_get('/api/v1/projects/{id}/frames', frames.get_project_frames)

    # API v1 routes - Frames
    app.router.add_get('/api/v1/frames', frames.list_frames)
    app.router.add_get('/api/v1/frames/{id}', frames.get_frame)
    app.router.add_post('/api/v1/frames', frames.create_frame)
    app.router.add_put('/api/v1/frames/{id}', frames.update_frame)
    app.router.add_delete('/api/v1/frames/{id}', frames.delete_frame)

    # API v1 routes - Generator
    app.router.add_get('/api/v1/generator/tasks', generator.list_tasks)
    app.router.add_get('/api/v1/generator/tasks/{id}', generator.get_task)
    app.router.add_post('/api/v1/generator/tasks', generator.create_task)
    app.router.add_post('/api/v1/generator/tasks/{id}/generate', generator.start_task)
    app.router.add_post('/api/v1/generator/tasks/{id}/stop', generator.stop_task)
    app.router.add_get('/api/v1/generator/tasks/{id}/progress', generator.get_task_progress)
    app.router.add_get('/api/v1/generator/plugins', generator.get_plugins)

    # API v1 routes - Models
    app.router.add_get('/api/v1/models/categories', models.get_model_categories)
    app.router.add_get('/api/v1/models/{category}', models.get_models_by_category)
    app.router.add_get('/api/v1/models/{category}/{filename}', models.get_model_info)

    # Documented API v2 routes (with OpenAPI auto-documentation)
    # These use PydanticView for automatic Swagger documentation
    app.router.add_view('/api/v2/projects', api_documented.ProjectsView)
    app.router.add_view('/api/v2/projects/{project_id}', api_documented.ProjectView)

    # Static files routes
    # Serve generated frames from data/frames directory
    app.router.add_static('/data/frames', Config.FRAMES_DIR, show_index=False)
