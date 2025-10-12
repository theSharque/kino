"""
Example plugin loader
"""
import asyncio
from typing import Dict, Any, Optional, Callable
from ..base_plugin import BasePlugin, PluginResult


class ExamplePlugin(BasePlugin):
    """
    Example plugin that simulates image generation
    """

    async def generate(
        self,
        task_id: int,
        data: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> PluginResult:
        """
        Simulate generation process
        """
        try:
            self.is_running = True
            self.should_stop = False
            self.progress = 0.0

            # Get parameters from data
            prompt = data.get('prompt', 'default prompt')
            steps = data.get('steps', 20)

            # Simulate generation steps
            for step in range(steps):
                if self.should_stop:
                    return PluginResult(
                        success=False,
                        data={},
                        error="Generation stopped by user"
                    )

                # Simulate work
                await asyncio.sleep(0.5)

                # Update progress
                progress = ((step + 1) / steps) * 100
                await self.update_progress(progress, progress_callback)

            # Return successful result
            result_data = {
                'prompt': prompt,
                'steps': steps,
                'output_path': f'/data/frames/example_task_{task_id}.png',
                'message': 'Generation completed successfully'
            }

            self.is_running = False
            return PluginResult(
                success=True,
                data=result_data
            )

        except Exception as e:
            self.is_running = False
            return PluginResult(
                success=False,
                data={},
                error=str(e)
            )

    async def stop(self):
        """Stop generation"""
        self.should_stop = True
        self.is_running = False

    @classmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': 'example',
            'version': '1.0.0',
            'description': 'Example plugin for testing',
            'author': 'Kino Team',
            'parameters': {
                'prompt': {
                    'type': 'string',
                    'required': True,
                    'description': 'Text prompt for generation'
                },
                'steps': {
                    'type': 'integer',
                    'required': False,
                    'default': 20,
                    'description': 'Number of generation steps'
                }
            }
        }

