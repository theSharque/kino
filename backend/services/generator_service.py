"""
Generator service for managing generation tasks
"""
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from database import Database
from models.task import TaskCreate, TaskUpdate, TaskResponse, TaskStatus
from plugins.plugin_loader import PluginRegistry


class GeneratorService:
    """Service for managing generator tasks"""

    def __init__(self, db: Database):
        self.db = db
        self.running_tasks: Dict[int, Any] = {}  # Store running plugin instances

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
            result = await plugin.generate(task_id, data, progress_callback)

            # Update final status
            if result.success:
                await self.update_task_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    progress=100.0,
                    result=result.data
                )
            else:
                await self.update_task_status(
                    task_id,
                    TaskStatus.FAILED,
                    error=result.error
                )

        except Exception as e:
            await self.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e)
            )

        finally:
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

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

