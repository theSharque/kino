"""
Plugin loader and registry

This module dynamically loads plugins from subdirectories.
Each plugin must be in its own directory with a loader.py file.
"""
import os
import importlib
from typing import Dict, Type, Optional
from pathlib import Path
from .base_plugin import BasePlugin


class PluginRegistry:
    """Registry for all available plugins"""

    _plugins: Dict[str, Type[BasePlugin]] = {}

    @classmethod
    def register(cls, plugin_type: str, plugin_class: Type[BasePlugin]):
        """Register a plugin"""
        cls._plugins[plugin_type] = plugin_class

    @classmethod
    def get_plugin(cls, plugin_type: str) -> Optional[Type[BasePlugin]]:
        """Get plugin class by type"""
        return cls._plugins.get(plugin_type)

    @classmethod
    def get_all_plugins(cls) -> Dict[str, Dict]:
        """Get information about all registered plugins"""
        result = {}
        for plugin_type, plugin_class in cls._plugins.items():
            result[plugin_type] = plugin_class.get_plugin_info()
        return result

    @classmethod
    def is_registered(cls, plugin_type: str) -> bool:
        """Check if plugin is registered"""
        return plugin_type in cls._plugins

    @classmethod
    def load_plugins_from_directory(cls):
        """
        Automatically load all plugins from subdirectories.
        Each plugin directory must contain a loader.py file.
        """
        plugins_dir = Path(__file__).parent

        # Iterate through all subdirectories
        for item in plugins_dir.iterdir():
            if not item.is_dir():
                continue

            # Skip __pycache__ and hidden directories
            if item.name.startswith('__') or item.name.startswith('.'):
                continue

            # Check if loader.py exists
            loader_file = item / 'loader.py'
            if not loader_file.exists():
                print(f"Warning: Plugin directory '{item.name}' does not contain loader.py, skipping")
                continue

            try:
                # Load the plugin module using relative import
                plugin_name = item.name

                # Dynamic import
                module = importlib.import_module(f'.{plugin_name}.loader', package='plugins')

                # Find the plugin class (should inherit from BasePlugin)
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, BasePlugin) and
                        attr is not BasePlugin):
                        plugin_class = attr
                        break

                if plugin_class:
                    cls.register(plugin_name, plugin_class)
                    print(f"Loaded plugin: {plugin_name}")
                else:
                    print(f"Warning: No plugin class found in {plugin_name}/loader.py")

            except Exception as e:
                print(f"Error loading plugin '{item.name}': {e}")


# Automatically load all plugins on import
PluginRegistry.load_plugins_from_directory()
