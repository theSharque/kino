"""
Generator service for managing generation tasks
"""
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import Database
from models.task import TaskCreate, TaskResponse, TaskStatus
from plugins.plugin_loader import PluginRegistry
from logger import get_logger


class GeneratorService:
    """Service for managing generator tasks"""

    def __init__(self, db: Database):
        self.db = db
        self.running_tasks: Dict[int, Any] = {}  # Store running plugin instances
        self.log = get_logger("generator")

    async def get_all_tasks(self) -> List[TaskResponse]:
        """Get all tasks"""
        query = """
            SELECT id, name, type, data, status, progress, result, error,
                   created_at, updated_at, started_at, completed_at
            FROM tasks
            ORDER BY created_at DESC
        """
        rows = await self.db.fetch_all(query)

        tasks = []
        for row in rows:
            tasks.append(self._row_to_task_response(row))

        return tasks

    async def get_task_by_id(self, task_id: int) -> Optional[TaskResponse]:
        """Get task by ID"""
        query = """
            SELECT id, name, type, data, status, progress, result, error,
                   created_at, updated_at, started_at, completed_at
            FROM tasks
            WHERE id = ?
        """
        row = await self.db.fetch_one(query, (task_id,))

        if not row:
            return None

        return self._row_to_task_response(row)

    async def create_task(self, task: TaskCreate) -> TaskResponse:
        """Create a new task"""
        # Verify plugin exists
        if not PluginRegistry.is_registered(task.type):
            raise ValueError(f"Plugin type '{task.type}' is not registered")

        query = """
            INSERT INTO tasks (name, type, data, status, progress, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        now = datetime.utcnow().isoformat()
        data_json = json.dumps(task.data)

        task_id = await self.db.execute(
            query,
            (task.name, task.type, data_json, TaskStatus.PENDING.value, 0.0, now, now)
        )

        created_task = await self.get_task_by_id(task_id)
        if not created_task:
            raise RuntimeError("Failed to create task")

        self.log.info("task_created", extra={"task_id": created_task.id, "type": created_task.type})
        return created_task

    async def update_task_status(
        self,
        task_id: int,
        status: TaskStatus,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[TaskResponse]:
        """Update task status and optionally other fields"""
        existing = await self.get_task_by_id(task_id)
        if not existing:
            return None

        update_fields = ["status = ?", "updated_at = ?"]
        params = [status.value, datetime.utcnow().isoformat()]

        if progress is not None:
            update_fields.append("progress = ?")
            params.append(progress)

        if result is not None:
            update_fields.append("result = ?")
            params.append(json.dumps(result))

        if error is not None:
            update_fields.append("error = ?")
            params.append(error)

        # Update timestamps
        if status == TaskStatus.RUNNING and existing.started_at is None:
            update_fields.append("started_at = ?")
            params.append(datetime.utcnow().isoformat())

        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.STOPPED]:
            update_fields.append("completed_at = ?")
            params.append(datetime.utcnow().isoformat())

        params.append(task_id)

        query = f"""
            UPDATE tasks
            SET {', '.join(update_fields)}
            WHERE id = ?
        """

        await self.db.execute(query, tuple(params))
        return await self.get_task_by_id(task_id)

    async def start_generation(self, task_id: int) -> bool:
        """Start generation for a task"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False

        if task.status != TaskStatus.PENDING:
            return False

        # Get plugin class
        plugin_class = PluginRegistry.get_plugin(task.type)
        if not plugin_class:
            await self.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=f"Plugin '{task.type}' not found"
            )
            return False

        # Create plugin instance
        plugin = plugin_class()
        self.running_tasks[task_id] = plugin

        # Update status to running
        await self.update_task_status(task_id, TaskStatus.RUNNING, progress=0.0)
        self.log.info("task_started", extra={"task_id": task_id, "type": task.type})

        # Start generation in background
        asyncio.create_task(self._run_generation(task_id, plugin, task.data))

        return True

    async def _run_generation(
        self,
        task_id: int,
        plugin: Any,
        data: Dict[str, Any]
    ):
        """Run generation in background"""
        try:
            # Progress callback
            async def progress_callback(progress: float):
                await self.update_task_status(task_id, TaskStatus.RUNNING, progress=progress)

            # Run generation
            self.log.info("generation_begin", extra={"task_id": task_id})
            result = await plugin.generate(task_id, data, progress_callback)

            # Update final status
            if result.success:
                await self.update_task_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    progress=100.0,
                    result=result.data
                )
                self.log.info("task_completed", extra={"task_id": task_id})

                # Create frame record if generation was successful
                if result.data and 'output_path' in result.data:
                    frame = await self._create_frame_record(task_id, data, result.data)

                    # Broadcast frame update event
                    if frame:
                        await self._broadcast_frame_update(frame)
            else:
                await self.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    error=result.error
                )
                self.log.error("task_failed", extra={"task_id": task_id, "error": result.error})

        except Exception as e:
            await self.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e)
            )
            self.log.exception("task_exception", extra={"task_id": task_id})

        finally:
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            self.log.info("task_cleanup", extra={"task_id": task_id})

    async def _create_frame_record(self, task_id: int, task_data: Dict[str, Any], result_data: Dict[str, Any]):
        """Create frame record in database after successful generation"""
        try:
            # Check if frame was already created by plugin (e.g., for preview support)
            if 'frame_id' in result_data and result_data['frame_id']:
                frame_id = result_data['frame_id']
                self.log.info("frame_exists", extra={"frame_id": frame_id, "task_id": task_id})

                # Return the existing frame
                from services.frame_service import FrameService
                frame_service = FrameService(self.db)
                frame = await frame_service.get_frame_by_id(frame_id)
                return frame

            # Get project_id from task data
            project_id = task_data.get('project_id')
            if not project_id:
                self.log.warning("no_project_id", extra={"task_id": task_id})
                return None

            # Get generator name from task
            task = await self.get_task_by_id(task_id)
            if not task:
                self.log.warning("task_missing_on_frame_create", extra={"task_id": task_id})
                return None

            # Create frame record
            from models.frame import FrameCreate
            from services.frame_service import FrameService

            frame_create = FrameCreate(
                path=result_data['output_path'],
                generator=task.type,
                project_id=project_id
            )

            frame_service = FrameService(self.db)
            frame = await frame_service.create_frame(frame_create)

            self.log.info("frame_created", extra={"frame_id": frame.id, "task_id": task_id})
            return frame

        except Exception as e:
            self.log.exception("frame_create_error", extra={"task_id": task_id})
            # Don't fail the task if frame creation fails
            return None

    async def _broadcast_frame_update(self, frame):
        """Broadcast frame update event to all WebSocket clients"""
        try:
            from handlers.websocket import broadcast_message

            message = {
                'type': 'frame_updated',
                'data': {
                    'frame_id': frame.id,
                    'project_id': frame.project_id,
                    'path': frame.path,
                    'generator': frame.generator,
                    'created_at': frame.created_at,
                    'updated_at': frame.updated_at
                }
            }

            await broadcast_message(message)
            self.log.info("frame_update_broadcasted", extra={"frame_id": frame.id})

        except Exception as e:
            self.log.exception("frame_update_broadcast_error", extra={"frame_id": getattr(frame, 'id', None)})

    async def stop_generation(self, task_id: int) -> bool:
        """Stop a running task"""
        task = await self.get_task_by_id(task_id)
        if not task:
            return False

        if task.status != TaskStatus.RUNNING:
            return False

        # Stop plugin
        if task_id in self.running_tasks:
            plugin = self.running_tasks[task_id]
            await plugin.stop()
            del self.running_tasks[task_id]
            self.log.info("task_stopped", extra={"task_id": task_id})

        # Update status
        await self.update_task_status(task_id, TaskStatus.STOPPED)

        return True

    def get_task_progress(self, task_id: int) -> Optional[float]:
        """Get current progress of a running task"""
        if task_id not in self.running_tasks:
            return None

        plugin = self.running_tasks[task_id]
        return plugin.get_progress()

    def get_available_plugins(self) -> Dict[str, Dict]:
        """Get all available plugins"""
        return PluginRegistry.get_all_plugins()

    async def stop_all_tasks(self) -> int:
        """
        Emergency stop all running tasks
        Returns number of stopped tasks
        """
        stopped_count = 0

        # Get all task IDs that are currently running
        running_task_ids = list(self.running_tasks.keys())

        for task_id in running_task_ids:
            try:
                success = await self.stop_generation(task_id)
                if success:
                    stopped_count += 1
            except Exception as e:
                print(f"Error stopping task {task_id}: {e}")
                continue

        return stopped_count

    async def clear_pending_tasks(self) -> int:
        """
        Clear all pending tasks from the queue
        Returns number of cleared tasks
        """
        # Get all pending tasks
        query = """
            SELECT id FROM tasks
            WHERE status = ?
        """
        rows = await self.db.fetch_all(query, (TaskStatus.PENDING.value,))

        pending_ids = [row['id'] for row in rows]
        cleared_count = len(pending_ids)

        if cleared_count > 0:
            # Update all pending tasks to stopped
            update_query = """
                UPDATE tasks
                SET status = ?, updated_at = ?, completed_at = ?
                WHERE status = ?
            """
            now = datetime.utcnow().isoformat()
            await self.db.execute(
                update_query,
                (TaskStatus.STOPPED.value, now, now, TaskStatus.PENDING.value)
            )

        return cleared_count

    async def reset_all(self) -> Dict[str, int]:
        """
        Reset all tasks - stop running and clear pending
        Returns dict with counts of stopped and cleared tasks
        """
        stopped_count = await self.stop_all_tasks()
        cleared_count = await self.clear_pending_tasks()

        return {
            'stopped': stopped_count,
            'cleared': cleared_count
        }

    def _row_to_task_response(self, row) -> TaskResponse:
        """Convert database row to TaskResponse"""
        return TaskResponse(
            id=row['id'],
            name=row['name'],
            type=row['type'],
            data=json.loads(row['data']) if row['data'] else {},
            status=TaskStatus(row['status']),
            progress=row['progress'],
            result=json.loads(row['result']) if row['result'] else None,
            error=row['error'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            started_at=row['started_at'],
            completed_at=row['completed_at']
        )

