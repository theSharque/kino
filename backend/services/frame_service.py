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
                SELECT id, path, generator, project_id, variant_id, created_at, updated_at
                FROM frames
                WHERE project_id = ?
                ORDER BY created_at ASC
            """
            rows = await self.db.fetch_all(query, (project_id,))
        else:
            query = """
                SELECT id, path, generator, project_id, variant_id, created_at, updated_at
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
                variant_id=row['variant_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))

        return frames

    async def get_frame_by_id(self, frame_id: int) -> Optional[FrameResponse]:
        """Get frame by ID"""
        query = """
            SELECT id, path, generator, project_id, variant_id, created_at, updated_at
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
            variant_id=row['variant_id'],
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
            INSERT INTO frames (path, generator, project_id, variant_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()

        frame_id = await self.db.execute(
            query,
            (frame.path, frame.generator, frame.project_id, frame.variant_id, now, now)
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

        if frame_update.variant_id is not None:
            update_fields.append("variant_id = ?")
            params.append(frame_update.variant_id)

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
        """Delete a frame and all its variants"""
        # Get the base frame to find all variants
        base_frame = await self.get_frame_by_id(frame_id)
        if not base_frame:
            return False

        # Find all variants of this frame by looking for frames with same project_id
        # and similar path pattern (same base name)
        import os
        from pathlib import Path
        
        base_path = Path(base_frame.path)
        base_name = base_path.stem  # filename without extension
        
        # Extract the base identifier from the filename
        # Format: frame_{project_id}_{timestamp}_v{variant_id}.png
        # We want to match: frame_{project_id}_{timestamp}
        base_parts = base_name.split('_v')[0]  # Remove variant suffix if present
        
        # Query all frames in the same project with matching base pattern
        query = """
            SELECT id, path FROM frames 
            WHERE project_id = ? AND path LIKE ?
        """
        pattern = f"%{base_parts}%"  # Match base name pattern
        variant_rows = await self.db.fetch_all(query, (base_frame.project_id, pattern))
        
        # Delete all variant files and database records
        deleted_count = 0
        for row in variant_rows:
            try:
                # Delete image file
                if os.path.exists(row['path']):
                    os.remove(row['path'])
                    print(f"Deleted image file: {row['path']}")

                # Delete JSON file
                json_path = row['path'].replace('.png', '.json')
                if os.path.exists(json_path):
                    os.remove(json_path)
                    print(f"Deleted parameters file: {json_path}")

                # Delete from database
                delete_query = "DELETE FROM frames WHERE id = ?"
                await self.db.execute(delete_query, (row['id'],))
                deleted_count += 1

            except Exception as e:
                print(f"Warning: Failed to delete variant {row['id']}: {e}")

        return deleted_count > 0

    async def get_frames_by_project(self, project_id: int) -> List[FrameResponse]:
        """Get all frames for a specific project"""
        return await self.get_all_frames(project_id=project_id)

    async def get_frame_variants(self, frame_id: int) -> List[FrameResponse]:
        """Get all variants of a specific frame"""
        base_frame = await self.get_frame_by_id(frame_id)
        if not base_frame:
            return []

        # Find all variants by looking for frames with same project_id and base name
        from pathlib import Path
        base_path = Path(base_frame.path)
        base_name = base_path.stem.split('_v')[0]  # Remove variant suffix if present
        
        query = """
            SELECT id, path, generator, project_id, variant_id, created_at, updated_at
            FROM frames 
            WHERE project_id = ? AND path LIKE ?
            ORDER BY variant_id ASC
        """
        pattern = f"%{base_name}%"
        rows = await self.db.fetch_all(query, (base_frame.project_id, pattern))
        
        variants = []
        for row in rows:
            variants.append(FrameResponse(
                id=row['id'],
                path=row['path'],
                generator=row['generator'],
                project_id=row['project_id'],
                variant_id=row['variant_id'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            ))
        
        return variants

    async def update_selected_variant(self, frame_id: int, variant_id: int) -> Optional[FrameResponse]:
        """Update the selected variant for a frame (future use)"""
        # This method is reserved for future implementation where we might track
        # which variant is currently selected/active for a frame
        # For now, variants are managed by the frontend
        return await self.get_frame_by_id(frame_id)

    async def update_frame_path(self, frame_id: int, new_path: str) -> Optional[FrameResponse]:
        """
        Update frame path (used for preview updates during generation)

        Args:
            frame_id: Frame ID to update
            new_path: New path to image file

        Returns:
            Updated FrameResponse or None if frame not found
        """
        query = """
            UPDATE frames
            SET path = ?, updated_at = ?
            WHERE id = ?
        """
        now = datetime.utcnow().isoformat()
        await self.db.execute(query, (new_path, now, frame_id))

        # Fetch updated frame
        return await self.get_frame_by_id(frame_id)

