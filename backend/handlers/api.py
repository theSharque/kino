"""
Main API handlers
"""
from aiohttp import web
from pydantic import BaseModel, ValidationError
import platform


class EchoRequest(BaseModel):
    """Request model for echo endpoint"""
    message: str


async def hello(request: web.Request) -> web.Response:
    """
    Simple hello endpoint

    GET /api/v1/hello?name=<name>
    """
    name = request.query.get('name', 'World')

    response_data = {
        'message': f'Hello, {name}!',
        'endpoint': '/api/v1/hello'
    }

    return web.json_response(response_data)


async def echo(request: web.Request) -> web.Response:
    """
    Echo endpoint - returns the same message that was sent

    POST /api/v1/echo
    Body: {"message": "your message"}
    """
    try:
        data = await request.json()
        echo_request = EchoRequest(**data)

        response_data = {
            'echo': echo_request.message,
            'length': len(echo_request.message)
        }

        return web.json_response(response_data)

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


async def info(request: web.Request) -> web.Response:
    """
    Server information endpoint

    GET /api/v1/info
    """
    info_data = {
        'name': 'Kino Backend API',
        'version': '0.1.0',
        'python': platform.python_version(),
        'platform': platform.platform(),
        'endpoints': [
            'GET /health',
            'GET /api/v1/hello',
            'POST /api/v1/echo',
            'GET /api/v1/info'
        ]
    }

    return web.json_response(info_data)

