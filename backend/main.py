"""
Main entry point for the aiohttp server
"""
import asyncio
from aiohttp import web
import aiohttp_cors
from aiohttp_pydantic import oas
from dotenv import load_dotenv
import os

from routes import setup_routes
from database import init_db, close_db


async def on_startup(app: web.Application):
    """Called on application startup"""
    db_path = os.getenv('DB_PATH', './data/kino.db')
    await init_db(db_path)
    print(f"Database initialized at {db_path}")


async def on_cleanup(app: web.Application):
    """Called on application cleanup"""
    await close_db()
    print("Database connection closed")


def create_app() -> web.Application:
    """Create and configure the aiohttp application"""
    load_dotenv()

    app = web.Application()

    # Setup lifecycle handlers
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # Setup routes
    setup_routes(app, cors)

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

