"""
Health check handlers
"""
from aiohttp import web
import psutil
import sys


async def health_check(request: web.Request) -> web.Response:
    """
    Health check endpoint to verify server is running

    GET /health
    """
    health_data = {
        'status': 'ok',
        'service': 'kino-backend',
        'python_version': sys.version.split()[0],
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent
    }

    return web.json_response(health_data)

