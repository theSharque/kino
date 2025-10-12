"""
Project handlers (controllers)
"""
from aiohttp import web
from pydantic import ValidationError

from database import get_db
from services.project_service import ProjectService
from models.project import ProjectCreate, ProjectUpdate, ProjectListResponse


async def list_projects(request: web.Request) -> web.Response:
    """
    Get all projects

    GET /api/v1/projects
    """
    try:
        db = get_db()
        service = ProjectService(db)

        projects = await service.get_all_projects()

        response = ProjectListResponse(
            total=len(projects),
            projects=projects
        )

        return web.json_response(response.model_dump(), status=200)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_project(request: web.Request) -> web.Response:
    """
    Get project by ID

    GET /api/v1/projects/{id}
    """
    try:
        project_id = int(request.match_info['id'])

        db = get_db()
        service = ProjectService(db)

        project = await service.get_project_by_id(project_id)

        if not project:
            return web.json_response({
                'error': 'Not found',
                'message': f'Project with id {project_id} not found'
            }, status=404)

        return web.json_response(project.model_dump(), status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid project ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def create_project(request: web.Request) -> web.Response:
    """
    Create a new project

    POST /api/v1/projects
    Body: {"name": "string", "width": int, "height": int, "fps": int}
    """
    try:
        data = await request.json()
        project_data = ProjectCreate(**data)

        db = get_db()
        service = ProjectService(db)

        project = await service.create_project(project_data)

        return web.json_response(project.model_dump(), status=201)

    except ValidationError as e:
        return web.json_response({
            'error': 'Validation error',
            'details': e.errors()
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def update_project(request: web.Request) -> web.Response:
    """
    Update an existing project

    PUT /api/v1/projects/{id}
    Body: {"name": "string", "width": int, "height": int, "fps": int} (all optional)
    """
    try:
        project_id = int(request.match_info['id'])
        data = await request.json()

        project_update = ProjectUpdate(**data)

        db = get_db()
        service = ProjectService(db)

        project = await service.update_project(project_id, project_update)

        if not project:
            return web.json_response({
                'error': 'Not found',
                'message': f'Project with id {project_id} not found'
            }, status=404)

        return web.json_response(project.model_dump(), status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid project ID'
        }, status=400)

    except ValidationError as e:
        return web.json_response({
            'error': 'Validation error',
            'details': e.errors()
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def delete_project(request: web.Request) -> web.Response:
    """
    Delete a project

    DELETE /api/v1/projects/{id}
    """
    try:
        project_id = int(request.match_info['id'])

        db = get_db()
        service = ProjectService(db)

        success = await service.delete_project(project_id)

        if not success:
            return web.json_response({
                'error': 'Not found',
                'message': f'Project with id {project_id} not found'
            }, status=404)

        return web.json_response({
            'message': 'Project deleted successfully'
        }, status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid project ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

