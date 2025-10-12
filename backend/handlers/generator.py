"""
Generator handlers (controllers)
"""
from aiohttp import web
from pydantic import ValidationError

from database import get_db
from services.generator_service import GeneratorService
from models.task import TaskCreate, TaskListResponse


async def list_tasks(request: web.Request) -> web.Response:
    """
    Get all tasks

    GET /api/v1/generator/tasks
    """
    try:
        db = get_db()
        service = GeneratorService(db)

        tasks = await service.get_all_tasks()

        response = TaskListResponse(
            total=len(tasks),
            tasks=tasks
        )

        return web.json_response(response.model_dump(), status=200)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_task(request: web.Request) -> web.Response:
    """
    Get task by ID

    GET /api/v1/generator/tasks/{id}
    """
    try:
        task_id = int(request.match_info['id'])

        db = get_db()
        service = GeneratorService(db)

        task = await service.get_task_by_id(task_id)

        if not task:
            return web.json_response({
                'error': 'Not found',
                'message': f'Task with id {task_id} not found'
            }, status=404)

        return web.json_response(task.model_dump(), status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid task ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def create_task(request: web.Request) -> web.Response:
    """
    Create a new task

    POST /api/v1/generator/tasks
    Body: {"name": "string", "type": "string", "data": {}}
    """
    try:
        data = await request.json()
        task_data = TaskCreate(**data)

        db = get_db()
        service = GeneratorService(db)

        task = await service.create_task(task_data)

        return web.json_response(task.model_dump(), status=201)

    except ValidationError as e:
        return web.json_response({
            'error': 'Validation error',
            'details': e.errors()
        }, status=400)

    except ValueError as e:
        return web.json_response({
            'error': 'Bad request',
            'message': str(e)
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def start_task(request: web.Request) -> web.Response:
    """
    Start generation for a task

    POST /api/v1/generator/tasks/{id}/generate
    """
    try:
        task_id = int(request.match_info['id'])

        db = get_db()
        service = GeneratorService(db)

        success = await service.start_generation(task_id)

        if not success:
            task = await service.get_task_by_id(task_id)
            if not task:
                return web.json_response({
                    'error': 'Not found',
                    'message': f'Task with id {task_id} not found'
                }, status=404)
            else:
                return web.json_response({
                    'error': 'Bad request',
                    'message': f'Task cannot be started (current status: {task.status})'
                }, status=400)

        return web.json_response({
            'message': 'Generation started',
            'task_id': task_id
        }, status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid task ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def stop_task(request: web.Request) -> web.Response:
    """
    Stop a running task

    POST /api/v1/generator/tasks/{id}/stop
    """
    try:
        task_id = int(request.match_info['id'])

        db = get_db()
        service = GeneratorService(db)

        success = await service.stop_generation(task_id)

        if not success:
            task = await service.get_task_by_id(task_id)
            if not task:
                return web.json_response({
                    'error': 'Not found',
                    'message': f'Task with id {task_id} not found'
                }, status=404)
            else:
                return web.json_response({
                    'error': 'Bad request',
                    'message': f'Task cannot be stopped (current status: {task.status})'
                }, status=400)

        return web.json_response({
            'message': 'Generation stopped',
            'task_id': task_id
        }, status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid task ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_task_progress(request: web.Request) -> web.Response:
    """
    Get current progress of a task

    GET /api/v1/generator/tasks/{id}/progress
    """
    try:
        task_id = int(request.match_info['id'])

        db = get_db()
        service = GeneratorService(db)

        # Get task to check if it exists
        task = await service.get_task_by_id(task_id)
        if not task:
            return web.json_response({
                'error': 'Not found',
                'message': f'Task with id {task_id} not found'
            }, status=404)

        # Get live progress if task is running
        live_progress = service.get_task_progress(task_id)

        return web.json_response({
            'task_id': task_id,
            'status': task.status.value,
            'progress': live_progress if live_progress is not None else task.progress
        }, status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid task ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_plugins(request: web.Request) -> web.Response:
    """
    Get all available plugins

    GET /api/v1/generator/plugins
    """
    try:
        db = get_db()
        service = GeneratorService(db)

        plugins = service.get_available_plugins()

        return web.json_response({
            'total': len(plugins),
            'plugins': plugins
        }, status=200)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)

