"""
Plugin System — Third-party validators and cleaners.
"""

import importlib
import importlib.util
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    plugin_type: str  # "validator" or "cleaner"
    author: str = ""
    enabled: bool = True


class BasePluginValidator(ABC):
    """Base class for custom validator plugins."""

    @abstractmethod
    def validate(self, field_name: str, value: Any, row: dict, row_num: int) -> list[dict]:
        """
        Validate a field value.
        Returns list of {status, severity, message, field, row}
        """
        ...


class BasePluginCleaner(ABC):
    """Base class for custom cleaner plugins."""

    @abstractmethod
    def clean(self, field_name: str, value: Any, row: dict) -> tuple[Any, bool]:
        """
        Clean a field value.
        Returns (cleaned_value, was_modified)
        """
        ...


class PluginRegistry:
    """Registry for third-party validators and cleaners."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.validators: dict[str, BasePluginValidator] = {}
        self.cleaners: dict[str, BasePluginCleaner] = {}
        self.plugin_infos: dict[str, PluginInfo] = {}
        os.makedirs(plugins_dir, exist_ok=True)

    def discover_plugins(self):
        """Discover and load plugins from the plugins directory."""
        if not os.path.exists(self.plugins_dir):
            return

        for filename in os.listdir(self.plugins_dir):
            if not filename.endswith(".py"):
                continue
            if filename.startswith("_"):
                continue

            filepath = os.path.join(self.plugins_dir, filename)
            self._load_plugin(filepath, filename)

    def _load_plugin(self, filepath: str, filename: str):
        """Load a single plugin module."""
        module_name = filename[:-3]  # Remove .py

        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None or spec.loader is None:
                return
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check for plugin registration
            if hasattr(module, "PLUGIN_INFO"):
                info = module.PLUGIN_INFO
                if isinstance(info, PluginInfo):
                    self.plugin_infos[module_name] = info

                    if info.plugin_type == "validator" and hasattr(module, "get_validator"):
                        self.validators[module_name] = module.get_validator()
                    elif info.plugin_type == "cleaner" and hasattr(module, "get_cleaner"):
                        self.cleaners[module_name] = module.get_cleaner()
        except Exception:
            pass  # Skip broken plugins

    def run_validators(self, field_name: str, value: Any, row: dict, row_num: int) -> list[dict]:
        """Run all enabled validator plugins."""
        results = []
        for name, validator in self.validators.items():
            info = self.plugin_infos.get(name)
            if info and info.enabled:
                try:
                    results.extend(validator.validate(field_name, value, row, row_num))
                except Exception:
                    results.append({
                        "field": field_name,
                        "row": row_num,
                        "status": "FAIL",
                        "severity": "WARNING",
                        "message": f"Plugin {name} crashed",
                    })
        return results

    def run_cleaners(self, field_name: str, value: Any, row: dict) -> tuple[Any, bool]:
        """Run all enabled cleaner plugins."""
        modified = False
        current_value = value

        for name, cleaner in self.cleaners.items():
            info = self.plugin_infos.get(name)
            if info and info.enabled:
                try:
                    cleaned, was_changed = cleaner.clean(field_name, current_value, row)
                    if was_changed:
                        current_value = cleaned
                        modified = True
                except Exception:
                    pass  # Skip broken cleaners

        return current_value, modified

    def list_plugins(self) -> list[dict]:
        """List all discovered plugins."""
        return [
            {
                "name": info.name,
                "version": info.version,
                "description": info.description,
                "plugin_type": info.plugin_type,
                "author": info.author,
                "enabled": info.enabled,
            }
            for info in self.plugin_infos.values()
        ]

    def toggle_plugin(self, name: str, enabled: bool):
        """Enable or disable a plugin."""
        if name in self.plugin_infos:
            self.plugin_infos[name].enabled = enabled
