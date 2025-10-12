"""
Base plugin interface for generator system
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass


@dataclass
class PluginResult:
    """Result of plugin execution"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class BasePlugin(ABC):
    """
    Base class for all generator plugins

    Each plugin must implement:
    - generate(): Main generation logic
    - stop(): Stop generation if running
    - get_progress(): Get current progress (0-100)
    """

    def __init__(self):
        self.is_running = False
        self.progress = 0.0
        self.should_stop = False

    @abstractmethod
    async def generate(
        self,
        task_id: int,
        data: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> PluginResult:
        """
        Execute generation task

        Args:
            task_id: Task ID
            data: Input data for generation
            progress_callback: Optional callback for progress updates

        Returns:
            PluginResult with success status and data
        """
        pass

    @abstractmethod
    async def stop(self):
        """Stop the generation process"""
        pass

    def get_progress(self) -> float:
        """Get current progress (0-100)"""
        return self.progress

    async def update_progress(
        self,
        progress: float,
        progress_callback: Optional[Callable[[float], None]] = None
    ):
        """Update progress and call callback if provided"""
        self.progress = max(0.0, min(100.0, progress))
        if progress_callback:
            await progress_callback(self.progress)

    @classmethod
    @abstractmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """
        Get plugin information

        Returns:
            Dict with plugin metadata (name, version, description, etc.)
        """
        pass

