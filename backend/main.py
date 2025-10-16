"""
Main entry point for the aiohttp server
"""
import asyncio
from aiohttp import web
from aiohttp_pydantic import oas
from dotenv import load_dotenv
import os

from routes import setup_routes
from database import init_db, close_db, get_db, Database
from services.generator_service import GeneratorService
from handlers import websocket
from datetime import datetime
from logger import setup_logging, get_logger


@web.middleware
async def cors_middleware(request, handler):
    """CORS middleware for all requests"""
    # Handle preflight requests
    if request.method == 'OPTIONS':
        response = web.Response()
    else:
        response = await handler(request)

    # Add CORS headers to all responses
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    response.headers['Access-Control-Expose-Headers'] = '*'

    return response


async def cleanup_stuck_tasks(db: Database):
    """Clean up any running tasks that were left from previous sessions"""
    try:
        # Find all tasks with 'running' status
        query = "SELECT id, name FROM tasks WHERE status = 'running'"
        rows = await db.fetch_all(query)

        if rows:
            print(f"Found {len(rows)} stuck running tasks, cleaning up...")
            current_time = datetime.now().isoformat()

            # Update all running tasks to stopped status
            for row in rows:
                task_id, task_name = row
                await db.execute(
                    "UPDATE tasks SET status = 'stopped', progress = 0.0, updated_at = ?, error = ? WHERE id = ?",
                    (current_time, "Task stopped due to server restart", task_id)
                )
                print(f"  - Stopped task ID {task_id}: {task_name}")

            await db.commit()
            print("Stuck tasks cleanup completed")
        else:
            print("No stuck running tasks found")

    except Exception as e:
        print(f"Error during stuck tasks cleanup: {e}")


async def on_startup(app: web.Application):
    """Called on application startup"""
    log = get_logger("startup")
    db_path = os.getenv('DB_PATH', './data/kino.db')
    await init_db(db_path)
    log.info("Database initialized", extra={"db_path": db_path})

    # Initialize generator service
    db = get_db()
    app['generator_service'] = GeneratorService(db)
    log.info("Generator service initialized")

    # Clean up any stuck running tasks from previous sessions
    await cleanup_stuck_tasks(db)


async def on_cleanup(app: web.Application):
    """Called on application cleanup"""
    log = get_logger("cleanup")
    # Close WebSocket connections
    await websocket.on_shutdown(app)
    # Close database
    await close_db()
    log.info("Database connection closed")


def create_app() -> web.Application:
    """Create and configure the aiohttp application"""
    load_dotenv()
    setup_logging()
    log = get_logger("bootstrap")

    app = web.Application(middlewares=[cors_middleware])

    # Setup lifecycle handlers
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    # Setup routes (CORS handled by middleware, no cors parameter needed)
    setup_routes(app)

    # Setup OpenAPI documentation (Swagger UI)
    oas.setup(
        app,
        title_spec="Kino Backend API",
        version_spec="1.0.0",
        url_prefix="/api/docs",
        swagger_ui_version="5"
    )

    log.info("App created")
    return app


def main():
    """Run the application"""
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')

    get_logger("server").info("Starting server", extra={"host": host, "port": port})
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()

