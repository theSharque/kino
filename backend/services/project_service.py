"""
Project business logic service
"""
from typing import Optional, List
from datetime import datetime
from database import Database
from models.project import ProjectCreate, ProjectUpdate, ProjectResponse


class ProjectService:
    """Service for managing projects"""

    def __init__(self, db: Database):
        self.db = db

    async def get_all_projects(self) -> List[ProjectResponse]:
        """Get all projects"""
        query = """
            SELECT id, name, width, height, fps, created_at, updated_at
            FROM projects
            ORDER BY created_at DESC
        """
        rows = await self.db.fetch_all(query)

        projects = []
        for row in rows:
            projects.append(ProjectResponse(
                id=row['id'],
                name=row['name'],
                width=row['width'],
                height=row['height'],
                fps=row['fps'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))

        return projects

    async def get_project_by_id(self, project_id: int) -> Optional[ProjectResponse]:
        """Get project by ID"""
        query = """
            SELECT id, name, width, height, fps, created_at, updated_at
            FROM projects
            WHERE id = ?
        """
        row = await self.db.fetch_one(query, (project_id,))

        if not row:
            return None

        return ProjectResponse(
            id=row['id'],
            name=row['name'],
            width=row['width'],
            height=row['height'],
            fps=row['fps'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    async def create_project(self, project: ProjectCreate) -> ProjectResponse:
        """Create a new project"""
        query = """
            INSERT INTO projects (name, width, height, fps, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()

        project_id = await self.db.execute(
            query,
            (project.name, project.width, project.height, project.fps, now, now)
        )

        # Fetch the created project
        created_project = await self.get_project_by_id(project_id)
        if not created_project:
            raise RuntimeError("Failed to create project")

        return created_project

    async def update_project(
        self,
        project_id: int,
        project_update: ProjectUpdate
    ) -> Optional[ProjectResponse]:
        """Update an existing project"""
        # Check if project exists
        existing = await self.get_project_by_id(project_id)
        if not existing:
            return None

        # Build dynamic update query
        update_fields = []
        params = []

        if project_update.name is not None:
            update_fields.append("name = ?")
            params.append(project_update.name)

        if project_update.width is not None:
            update_fields.append("width = ?")
            params.append(project_update.width)

        if project_update.height is not None:
            update_fields.append("height = ?")
            params.append(project_update.height)

        if project_update.fps is not None:
            update_fields.append("fps = ?")
            params.append(project_update.fps)

        if not update_fields:
            # Nothing to update
            return existing

        # Add updated_at
        update_fields.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        # Add project_id for WHERE clause
        params.append(project_id)

        query = f"""
            UPDATE projects
            SET {', '.join(update_fields)}
            WHERE id = ?
        """

        await self.db.execute(query, tuple(params))

        # Fetch updated project
        return await self.get_project_by_id(project_id)

    async def delete_project(self, project_id: int) -> bool:
        """Delete a project and all associated frames"""
        # Check if project exists
        existing = await self.get_project_by_id(project_id)
        if not existing:
            return False

        # Import frame service to delete associated frames
        from services.frame_service import FrameService
        frame_service = FrameService(self.db)

        # Get all frames for this project
        frames = await frame_service.get_frames_by_project(project_id)

        # Delete all associated frames (this will also delete their files)
        for frame in frames:
            await frame_service.delete_frame(frame.id)
            print(f"Deleted frame {frame.id} for project {project_id}")

        # Delete the project from database
        query = "DELETE FROM projects WHERE id = ?"
        await self.db.execute(query, (project_id,))

        print(f"Deleted project {project_id} and {len(frames)} associated frames")
        return True

