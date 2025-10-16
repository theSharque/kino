"""
API handlers with OpenAPI documentation using aiohttp-pydantic
"""
from aiohttp import web
from aiohttp_pydantic import PydanticView
from aiohttp_pydantic.oas.typing import r200, r404

from database import get_db
from services.project_service import ProjectService
from models.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse
)


class ProjectsView(PydanticView):
    """
    Projects API endpoints
    """

    async def get(self) -> r200[ProjectListResponse]:
        """
        List all projects

        Returns a list of all projects in the database.

        Tags:
            - Projects

        Status Codes:
            200: Successfully retrieved projects list
            500: Internal server error
        """
        try:
            db = get_db()
            service = ProjectService(db)
            projects = await service.get_all_projects()

            return web.json_response(
                ProjectListResponse(
                    total=len(projects),
                    projects=projects
                ).model_dump(),
                status=200
            )
        except Exception as e:
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

    async def post(self, project: ProjectCreate) -> r200[ProjectResponse]:
        """
        Create a new project

        Create a new video project with specified parameters.

        Tags:
            - Projects

        Parameters:
            project: Project creation data

        Status Codes:
            200: Project created successfully
            400: Validation error
            500: Internal server error
        """
        try:
            db = get_db()
            service = ProjectService(db)
            created_project = await service.create_project(project)

            return web.json_response(
                created_project.model_dump(),
                status=201
            )
        except Exception as e:
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)


class ProjectView(PydanticView):
    """
    Single project API endpoints
    """

    async def get(self, project_id: int, /) -> r200[ProjectResponse] | r404:
        """
        Get project by ID

        Retrieve detailed information about a specific project.

        Tags:
            - Projects

        Parameters:
            project_id: The ID of the project to retrieve

        Status Codes:
            200: Project found and returned
            404: Project not found
            500: Internal server error
        """
        try:
            db = get_db()
            service = ProjectService(db)
            project = await service.get_project_by_id(project_id)

            if not project:
                return web.json_response({
                    'error': 'Not found',
                    'message': f'Project with id {project_id} not found'
                }, status=404)

            return web.json_response(project.model_dump(), status=200)

        except Exception as e:
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

    async def put(self, project_id: int, /, project: ProjectUpdate) -> r200[ProjectResponse] | r404:
        """
        Update project

        Update an existing project with new data. All fields are optional.

        Tags:
            - Projects

        Parameters:
            project_id: The ID of the project to update
            project: Project update data

        Status Codes:
            200: Project updated successfully
            400: Validation error
            404: Project not found
            500: Internal server error
        """
        try:
            db = get_db()
            service = ProjectService(db)
            updated_project = await service.update_project(project_id, project)

            if not updated_project:
                return web.json_response({
                    'error': 'Not found',
                    'message': f'Project with id {project_id} not found'
                }, status=404)

            return web.json_response(updated_project.model_dump(), status=200)

        except Exception as e:
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

    async def delete(self, project_id: int, /) -> r200 | r404:
        """
        Delete project

        Permanently delete a project and all associated frames.

        Tags:
            - Projects

        Parameters:
            project_id: The ID of the project to delete

        Status Codes:
            200: Project deleted successfully
            404: Project not found
            500: Internal server error
        """
        try:
            db = get_db()
            service = ProjectService(db)
            deleted = await service.delete_project(project_id)

            if not deleted:
                return web.json_response({
                    'error': 'Not found',
                    'message': f'Project with id {project_id} not found'
                }, status=404)

            return web.json_response({
                'message': 'Project deleted successfully'
            }, status=200)

        except Exception as e:
            return web.json_response({
                'error': 'Internal server error',
                'message': str(e)
            }, status=500)

