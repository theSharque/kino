"""
WebSocket handler for real-time updates
"""
from aiohttp import web, WSMsgType
import asyncio
import json
import weakref
from services.system_monitor import SystemMonitor
from logger import get_logger


# Global set of connected WebSocket clients
websockets: weakref.WeakSet = weakref.WeakSet()


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    """
    WebSocket endpoint for real-time updates

    GET /ws

    Sends periodic updates:
    - System metrics (CPU, GPU, MEM)
    - Task queue status
    - Current task progress
    """
    ws = web.WebSocketResponse(heartbeat=10.0)
    await ws.prepare(request)

    log = get_logger("ws")
    # Add to active connections
    websockets.add(ws)

    # Get services
    generator_service = request.app.get('generator_service')
    system_monitor = SystemMonitor()

    log.info("client_connected", extra={"total_clients": len(websockets)})

    # Background task to send periodic updates
    async def send_updates():
        try:
            while not ws.closed:
                # Collect data
                metrics = system_monitor.get_metrics()

                # Get task queue info
                pending_count = 0
                running_count = 0
                current_task = None
                current_progress = 0.0

                if generator_service:
                    # Count pending and running tasks separately
                    all_tasks = await generator_service.get_all_tasks()
                    pending_count = sum(1 for t in all_tasks if t.status.value == 'pending')
                    running_count = sum(1 for t in all_tasks if t.status.value == 'running')

                    # Find running task
                    running_tasks = [t for t in all_tasks if t.status.value == 'running']
                    if running_tasks:
                        current_task = running_tasks[0]
                        current_progress = current_task.progress

                # Build update message
                update = {
                    'type': 'metrics',
                    'data': {
                        'cpu_percent': metrics['cpu_percent'],
                        'memory_percent': metrics['memory_percent'],
                        'gpu_percent': metrics['gpu_percent'],
                        'gpu_memory_percent': metrics['gpu_memory_percent'],
                        'gpu_available': metrics['gpu_available'],
                        'gpu_type': metrics['gpu_type'],
                        'pending_count': pending_count,
                        'running_count': running_count,
                        'current_task': {
                            'id': current_task.id if current_task else None,
                            'name': current_task.name if current_task else None,
                            'progress': current_progress
                        } if current_task else None
                    }
                }

                # Send to client
                await ws.send_json(update)
                log.debug("metrics_sent", extra={
                    "pending": pending_count,
                    "running": running_count,
                    "current_task": (current_task.id if current_task else None),
                    "progress": current_progress,
                })

                # Wait before next update (2 seconds)
                await asyncio.sleep(2.0)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.exception("ws_update_error")

    # Start background update task
    update_task = asyncio.create_task(send_updates())

    try:
        # Handle incoming messages
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    msg_type = data.get('type')

                    if msg_type == 'ping':
                        # Respond to ping
                        await ws.send_json({'type': 'pong'})

                    elif msg_type == 'close':
                        await ws.close()
                        break

                except json.JSONDecodeError:
                    log.warning("invalid_json", extra={"data": msg.data[:256]})

            elif msg.type == WSMsgType.ERROR:
                log.error("ws_error", extra={"exception": str(ws.exception())})
                break

    finally:
        # Cancel background task
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass

        # Remove from active connections
        websockets.discard(ws)
        log.info("client_disconnected", extra={"total_clients": len(websockets)})

    return ws


async def broadcast_message(message: dict):
    """
    Broadcast a message to all connected WebSocket clients

    Args:
        message: Dictionary to send as JSON
    """
    disconnected = set()

    for ws in websockets:
        try:
            if ws.closed:
                disconnected.add(ws)
            else:
                await ws.send_json(message)
        except Exception as e:
            print(f"Error broadcasting to client: {e}")
            disconnected.add(ws)

    # Clean up disconnected clients
    for ws in disconnected:
        websockets.discard(ws)


async def on_shutdown(app: web.Application):
    """
    Gracefully close all WebSocket connections on server shutdown
    """
    from aiohttp import WSCloseCode

    for ws in set(websockets):
        await ws.close(
            code=WSCloseCode.GOING_AWAY,
            message="Server shutdown"
        )

