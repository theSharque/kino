"""
Frame business logic service
"""
from typing import Optional, List
from datetime import datetime
from database import Database
from models.frame import FrameCreate, FrameUpdate, FrameResponse


class FrameService:
    """Service for managing frames"""

    def __init__(self, db: Database):
        self.db = db

    async def get_all_frames(self, project_id: Optional[int] = None) -> List[FrameResponse]:
        """
        Get all frames, optionally filtered by project_id
        """
        if project_id is not None:
            query = """
                SELECT id, path, generator, project_id, created_at, updated_at
                FROM frames
                WHERE project_id = ?
                ORDER BY created_at ASC
            """
            rows = await self.db.fetch_all(query, (project_id,))
        else:
            query = """
                SELECT id, path, generator, project_id, created_at, updated_at
                FROM frames
                ORDER BY created_at DESC
            """
            rows = await self.db.fetch_all(query)

        frames = []
        for row in rows:
            frames.append(FrameResponse(
                id=row['id'],
                path=row['path'],
                generator=row['generator'],
                project_id=row['project_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))

        return frames

    async def get_frame_by_id(self, frame_id: int) -> Optional[FrameResponse]:
        """Get frame by ID"""
        query = """
            SELECT id, path, generator, project_id, created_at, updated_at
            FROM frames
            WHERE id = ?
        """
        row = await self.db.fetch_one(query, (frame_id,))

        if not row:
            return None

        return FrameResponse(
            id=row['id'],
            path=row['path'],
            generator=row['generator'],
            project_id=row['project_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    async def create_frame(self, frame: FrameCreate) -> FrameResponse:
        """Create a new frame"""
        # Verify that project exists
        project_query = "SELECT id FROM projects WHERE id = ?"
        project = await self.db.fetch_one(project_query, (frame.project_id,))
        if not project:
            raise ValueError(f"Project with id {frame.project_id} does not exist")

        query = """
            INSERT INTO frames (path, generator, project_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()

        frame_id = await self.db.execute(
            query,
            (frame.path, frame.generator, frame.project_id, now, now)
        )

        # Fetch the created frame
        created_frame = await self.get_frame_by_id(frame_id)
        if not created_frame:
            raise RuntimeError("Failed to create frame")

        return created_frame

    async def update_frame(
        self,
        frame_id: int,
        frame_update: FrameUpdate
    ) -> Optional[FrameResponse]:
        """Update an existing frame"""
        # Check if frame exists
        existing = await self.get_frame_by_id(frame_id)
        if not existing:
            return None

        # Build dynamic update query
        update_fields = []
        params = []

        if frame_update.path is not None:
            update_fields.append("path = ?")
            params.append(frame_update.path)

        if frame_update.generator is not None:
            update_fields.append("generator = ?")
            params.append(frame_update.generator)

        if frame_update.project_id is not None:
            # Verify new project exists
            project_query = "SELECT id FROM projects WHERE id = ?"
            project = await self.db.fetch_one(project_query, (frame_update.project_id,))
            if not project:
                raise ValueError(f"Project with id {frame_update.project_id} does not exist")

            update_fields.append("project_id = ?")
            params.append(frame_update.project_id)

        if not update_fields:
            # Nothing to update
            return existing

        # Add updated_at
        update_fields.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())

        # Add frame_id for WHERE clause
        params.append(frame_id)

        query = f"""
            UPDATE frames
            SET {', '.join(update_fields)}
            WHERE id = ?
        """

        await self.db.execute(query, tuple(params))

        # Fetch updated frame
        return await self.get_frame_by_id(frame_id)

    async def delete_frame(self, frame_id: int) -> bool:
        """Delete a frame"""
        # Check if frame exists
        existing = await self.get_frame_by_id(frame_id)
        if not existing:
            return False

        query = "DELETE FROM frames WHERE id = ?"
        await self.db.execute(query, (frame_id,))

        return True

    async def get_frames_by_project(self, project_id: int) -> List[FrameResponse]:
        """Get all frames for a specific project"""
        return await self.get_all_frames(project_id=project_id)

