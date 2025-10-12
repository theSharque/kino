"""
API routes configuration
"""
from aiohttp import web
import aiohttp_cors

from handlers import health, api, projects, frames, generator, api_documented


def setup_routes(app: web.Application, cors: aiohttp_cors.CorsConfig):
    """Configure all application routes"""

    # Health check endpoint
    health_route = app.router.add_get('/health', health.health_check)
    cors.add(health_route)

    # API v1 routes - General
    api_hello_route = app.router.add_get('/api/v1/hello', api.hello)
    cors.add(api_hello_route)

    api_echo_route = app.router.add_post('/api/v1/echo', api.echo)
    cors.add(api_echo_route)

    api_info_route = app.router.add_get('/api/v1/info', api.info)
    cors.add(api_info_route)

    # API v1 routes - Projects
    projects_list_route = app.router.add_get('/api/v1/projects', projects.list_projects)
    cors.add(projects_list_route)

    projects_get_route = app.router.add_get('/api/v1/projects/{id}', projects.get_project)
    cors.add(projects_get_route)

    projects_create_route = app.router.add_post('/api/v1/projects', projects.create_project)
    cors.add(projects_create_route)

    projects_update_route = app.router.add_put('/api/v1/projects/{id}', projects.update_project)
    cors.add(projects_update_route)

    projects_delete_route = app.router.add_delete('/api/v1/projects/{id}', projects.delete_project)
    cors.add(projects_delete_route)

    # Get frames for a specific project
    project_frames_route = app.router.add_get('/api/v1/projects/{id}/frames', frames.get_project_frames)
    cors.add(project_frames_route)

    # API v1 routes - Frames
    frames_list_route = app.router.add_get('/api/v1/frames', frames.list_frames)
    cors.add(frames_list_route)

    frames_get_route = app.router.add_get('/api/v1/frames/{id}', frames.get_frame)
    cors.add(frames_get_route)

    frames_create_route = app.router.add_post('/api/v1/frames', frames.create_frame)
    cors.add(frames_create_route)

    frames_update_route = app.router.add_put('/api/v1/frames/{id}', frames.update_frame)
    cors.add(frames_update_route)

    frames_delete_route = app.router.add_delete('/api/v1/frames/{id}', frames.delete_frame)
    cors.add(frames_delete_route)

    # API v1 routes - Generator
    generator_list_tasks_route = app.router.add_get('/api/v1/generator/tasks', generator.list_tasks)
    cors.add(generator_list_tasks_route)

    generator_get_task_route = app.router.add_get('/api/v1/generator/tasks/{id}', generator.get_task)
    cors.add(generator_get_task_route)

    generator_create_task_route = app.router.add_post('/api/v1/generator/tasks', generator.create_task)
    cors.add(generator_create_task_route)

    generator_start_route = app.router.add_post('/api/v1/generator/tasks/{id}/generate', generator.start_task)
    cors.add(generator_start_route)

    generator_stop_route = app.router.add_post('/api/v1/generator/tasks/{id}/stop', generator.stop_task)
    cors.add(generator_stop_route)

    generator_progress_route = app.router.add_get('/api/v1/generator/tasks/{id}/progress', generator.get_task_progress)
    cors.add(generator_progress_route)

    generator_plugins_route = app.router.add_get('/api/v1/generator/plugins', generator.get_plugins)
    cors.add(generator_plugins_route)

    # Documented API v2 routes (with OpenAPI auto-documentation)
    # These use PydanticView for automatic Swagger documentation
    app.router.add_view('/api/v2/projects', api_documented.ProjectsView)
    app.router.add_view('/api/v2/projects/{project_id}', api_documented.ProjectView)

