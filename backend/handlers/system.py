"""
System control handlers for emergency stop and restart
"""
from aiohttp import web
import sys
import asyncio


async def emergency_stop(request: web.Request) -> web.Response:
    """
    Emergency stop all generation tasks (running and pending)
    Clears the entire queue

    POST /api/v1/system/emergency-stop
    """
    try:
        # Get generator service from app
        generator_service = request.app['generator_service']

        # Reset all tasks (stop running + clear pending)
        reset_counts = await generator_service.reset_all()

        return web.json_response({
            'success': True,
            'message': f'Stopped {reset_counts["stopped"]} running task(s) and cleared {reset_counts["cleared"]} pending task(s)',
            'stopped_count': reset_counts['stopped'],
            'cleared_count': reset_counts['cleared']
        }, status=200)

    except Exception as e:
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)


async def restart_server(request: web.Request) -> web.Response:
    """
    Restart the backend server
    Stops all running tasks and clears pending queue before restart
    Exits the process, expecting run.sh to restart it

    POST /api/v1/system/restart
    """
    try:
        # Get generator service from app
        generator_service = request.app['generator_service']

        # Reset all tasks (stop running + clear pending)
        reset_counts = await generator_service.reset_all()
        print(f"🧹 Cleared {reset_counts['stopped']} running and {reset_counts['cleared']} pending tasks before restart")

        # Send response first
        response = web.json_response({
            'success': True,
            'message': f'Server restart initiated. Stopped {reset_counts["stopped"]} task(s), cleared {reset_counts["cleared"]} pending task(s). Please wait 5-10 seconds for reconnection.',
            'stopped_count': reset_counts['stopped'],
            'cleared_count': reset_counts['cleared']
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
    Stops all running tasks and clears pending queue before shutdown
    Exits with code 1 to signal run.sh to NOT restart

    POST /api/v1/system/shutdown
    """
    try:
        # Get generator service from app
        generator_service = request.app['generator_service']

        # Reset all tasks (stop running + clear pending)
        reset_counts = await generator_service.reset_all()
        print(f"🧹 Cleared {reset_counts['stopped']} running and {reset_counts['cleared']} pending tasks before shutdown")

        # Send response first
        response = web.json_response({
            'success': True,
            'message': f'Server shutdown initiated. Stopped {reset_counts["stopped"]} task(s), cleared {reset_counts["cleared"]} pending task(s).',
            'stopped_count': reset_counts['stopped'],
            'cleared_count': reset_counts['cleared']
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

