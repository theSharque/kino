"""
System control handlers for emergency stop and restart
"""
from aiohttp import web
import sys
import asyncio


async def emergency_stop(request: web.Request) -> web.Response:
    """
    Emergency stop all running generation tasks

    POST /api/v1/system/emergency-stop
    """
    try:
        # Get generator service from app
        generator_service = request.app['generator_service']

        # Stop all running tasks
        stopped_count = await generator_service.stop_all_tasks()

        return web.json_response({
            'success': True,
            'message': f'Stopped {stopped_count} running task(s)',
            'stopped_count': stopped_count
        }, status=200)

    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


async def restart_server(request: web.Request) -> web.Response:
    """
    Restart the backend server
    Exits the process, expecting run.sh to restart it

    POST /api/v1/system/restart
    """
    try:
        # Send response first
        response = web.json_response({
            'success': True,
            'message': 'Server restart initiated. Please wait 5-10 seconds for reconnection.'
        }, status=200)

        # Schedule restart after response is sent
        async def do_restart():
            await asyncio.sleep(0.5)  # Give time for response to be sent
            print("🔄 Server restart requested via API - exiting for auto-restart")
            sys.exit(0)

        asyncio.create_task(do_restart())

        return response

    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


async def shutdown_server(request: web.Request) -> web.Response:
    """
    Gracefully shutdown the server
    Exits with code 1 to signal run.sh to NOT restart

    POST /api/v1/system/shutdown
    """
    try:
        # Send response first
        response = web.json_response({
            'success': True,
            'message': 'Server shutdown initiated'
        }, status=200)

        # Schedule shutdown after response is sent
        async def do_shutdown():
            await asyncio.sleep(0.5)
            print("🛑 Server shutdown requested via API")
            sys.exit(1)  # Exit code 1 to signal intentional shutdown

        asyncio.create_task(do_shutdown())

        return response

    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

