"""
Main entry point for the aiohttp server
"""
import asyncio
from aiohttp import web
from aiohttp_pydantic import oas
from dotenv import load_dotenv
import os

from routes import setup_routes
from database import init_db, close_db, get_db
from services.generator_service import GeneratorService
from handlers import websocket


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


async def on_startup(app: web.Application):
    """Called on application startup"""
    db_path = os.getenv('DB_PATH', './data/kino.db')
    await init_db(db_path)
    print(f"Database initialized at {db_path}")

    # Initialize generator service
    db = get_db()
    app['generator_service'] = GeneratorService(db)
    print("Generator service initialized")


async def on_cleanup(app: web.Application):
    """Called on application cleanup"""
    # Close WebSocket connections
    await websocket.on_shutdown(app)
    # Close database
    await close_db()
    print("Database connection closed")


def create_app() -> web.Application:
    """Create and configure the aiohttp application"""
    load_dotenv()

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

    return app


def main():
    """Run the application"""
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')

    print(f"======= Starting server on http://{host}:{port}/ =======")
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    main()

