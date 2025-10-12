"""
Frame handlers (controllers)
"""
from aiohttp import web
from pydantic import ValidationError

from database import get_db
from services.frame_service import FrameService
from models.frame import FrameCreate, FrameUpdate, FrameListResponse


async def list_frames(request: web.Request) -> web.Response:
    """
    Get all frames, optionally filtered by project_id

    GET /api/v1/frames?project_id={id}
    """
    try:
        # Get optional project_id filter from query params
        project_id = request.query.get('project_id')
        if project_id:
            try:
                project_id = int(project_id)
            except ValueError:
                return web.json_response({
                    'error': 'Bad request',
                    'message': 'Invalid project_id parameter'
                }, status=400)

        db = get_db()
        service = FrameService(db)

        frames = await service.get_all_frames(project_id=project_id)

        response = FrameListResponse(
            total=len(frames),
            frames=frames
        )

        return web.json_response(response.model_dump(), status=200)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_frame(request: web.Request) -> web.Response:
    """
    Get frame by ID

    GET /api/v1/frames/{id}
    """
    try:
        frame_id = int(request.match_info['id'])

        db = get_db()
        service = FrameService(db)

        frame = await service.get_frame_by_id(frame_id)

        if not frame:
            return web.json_response({
                'error': 'Not found',
                'message': f'Frame with id {frame_id} not found'
            }, status=404)

        return web.json_response(frame.model_dump(), status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid frame ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def create_frame(request: web.Request) -> web.Response:
    """
    Create a new frame

    POST /api/v1/frames
    Body: {"path": "string", "generator": "string", "project_id": int}
    """
    try:
        data = await request.json()
        frame_data = FrameCreate(**data)

        db = get_db()
        service = FrameService(db)

        frame = await service.create_frame(frame_data)

        return web.json_response(frame.model_dump(), status=201)

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


async def update_frame(request: web.Request) -> web.Response:
    """
    Update an existing frame

    PUT /api/v1/frames/{id}
    Body: {"path": "string", "generator": "string", "project_id": int} (all optional)
    """
    try:
        frame_id = int(request.match_info['id'])
        data = await request.json()

        frame_update = FrameUpdate(**data)

        db = get_db()
        service = FrameService(db)

        frame = await service.update_frame(frame_id, frame_update)

        if not frame:
            return web.json_response({
                'error': 'Not found',
                'message': f'Frame with id {frame_id} not found'
            }, status=404)

        return web.json_response(frame.model_dump(), status=200)

    except ValueError as e:
        return web.json_response({
            'error': 'Bad request',
            'message': str(e)
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


async def delete_frame(request: web.Request) -> web.Response:
    """
    Delete a frame

    DELETE /api/v1/frames/{id}
    """
    try:
        frame_id = int(request.match_info['id'])

        db = get_db()
        service = FrameService(db)

        success = await service.delete_frame(frame_id)

        if not success:
            return web.json_response({
                'error': 'Not found',
                'message': f'Frame with id {frame_id} not found'
            }, status=404)

        return web.json_response({
            'message': 'Frame deleted successfully'
        }, status=200)

    except ValueError:
        return web.json_response({
            'error': 'Bad request',
            'message': 'Invalid frame ID'
        }, status=400)

    except Exception as e:
        return web.json_response({
            'error': 'Internal server error',
            'message': str(e)
        }, status=500)


async def get_project_frames(request: web.Request) -> web.Response:
    """
    Get all frames for a specific project

    GET /api/v1/projects/{id}/frames
    """
    try:
        project_id = int(request.match_info['id'])

        db = get_db()
        service = FrameService(db)

        frames = await service.get_frames_by_project(project_id)

        response = FrameListResponse(
            total=len(frames),
            frames=frames
        )

        return web.json_response(response.model_dump(), status=200)

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

