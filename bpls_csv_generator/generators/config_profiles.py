"""
Config Profiles — Save and switch between different validation rule sets.
"""

import copy
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProfileFieldOverride:
    sheet: str
    field: str
    property: str  # e.g., "required", "min_value", "max_length", "enum_values"
    value: Any


@dataclass
class ValidationProfile:
    name: str
    description: str = ""
    created_at: str = ""
    field_overrides: list[ProfileFieldOverride] = field(default_factory=list)
    disabled_validators: dict[str, list[str]] = field(default_factory=dict)  # sheet -> [field_types]
    custom_rules: dict[str, list[dict]] = field(default_factory=dict)  # sheet -> [conditional_rules]
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "field_overrides": [
                {"sheet": o.sheet, "field": o.field, "property": o.property, "value": o.value}
                for o in self.field_overrides
            ],
            "disabled_validators": self.disabled_validators,
            "custom_rules": self.custom_rules,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationProfile":
        overrides = [
            ProfileFieldOverride(**o) for o in data.get("field_overrides", [])
        ]
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            field_overrides=overrides,
            disabled_validators=data.get("disabled_validators", {}),
            custom_rules=data.get("custom_rules", {}),
            enabled=data.get("enabled", True),
        )


class ProfileManager:
    """Manages validation profiles."""

    def __init__(self, profiles_file: str = "outputs/profiles.json"):
        self.profiles_file = profiles_file
        self.profiles: dict[str, ValidationProfile] = {}
        self.active_profile: str | None = None
        self._load_profiles()

    def _load_profiles(self):
        """Load profiles from file."""
        if os.path.exists(self.profiles_file):
            with open(self.profiles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for name, profile_data in data.get("profiles", {}).items():
                    self.profiles[name] = ValidationProfile.from_dict(profile_data)
                self.active_profile = data.get("active_profile")

    def _save_profiles(self):
        """Save profiles to file."""
        os.makedirs(os.path.dirname(self.profiles_file) or ".", exist_ok=True)
        with open(self.profiles_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "profiles": {name: p.to_dict() for name, p in self.profiles.items()},
                    "active_profile": self.active_profile,
                },
                f,
                indent=2,
            )

    def create_profile(self, name: str, description: str = "") -> ValidationProfile:
        """Create a new empty profile."""
        profile = ValidationProfile(
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
        )
        self.profiles[name] = profile
        self._save_profiles()
        return profile

    def clone_from_current(self, name: str, description: str = "") -> ValidationProfile:
        """Create a profile cloned from the current base schema."""
        from config.schema import SHEET_SCHEMAS, CONDITIONAL_RULES, CROSS_FIELD_RULES

        profile = ValidationProfile(
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
        )

        # Save current schema as the baseline — overrides will be applied on top
        self.profiles[name] = profile
        self._save_profiles()
        return profile

    def add_override(self, profile_name: str, sheet: str, field: str, property: str, value: Any):
        """Add a field override to a profile."""
        if profile_name not in self.profiles:
            raise ValueError(f"Profile not found: {profile_name}")

        override = ProfileFieldOverride(
            sheet=sheet, field=field, property=property, value=value
        )
        self.profiles[profile_name].field_overrides.append(override)
        self._save_profiles()

    def remove_override(self, profile_name: str, index: int):
        """Remove an override by index."""
        if profile_name not in self.profiles:
            raise ValueError(f"Profile not found: {profile_name}")
        overrides = self.profiles[profile_name].field_overrides
        if 0 <= index < len(overrides):
            overrides.pop(index)
            self._save_profiles()

    def activate(self, profile_name: str):
        """Activate a profile."""
        if profile_name not in self.profiles:
            raise ValueError(f"Profile not found: {profile_name}")
        self.profiles[profile_name].enabled = True
        self.active_profile = profile_name
        self._save_profiles()

    def deactivate(self):
        """Deactivate the current profile."""
        self.active_profile = None
        self._save_profiles()

    def get_active_profile(self) -> ValidationProfile | None:
        """Get the active profile."""
        if self.active_profile:
            return self.profiles.get(self.active_profile)
        return None

    def apply_overrides(self, sheet_schemas: dict, conditional_rules: dict, cross_field_rules: dict) -> tuple:
        """Apply the active profile's overrides to the schemas."""
        profile = self.get_active_profile()
        if not profile:
            return sheet_schemas, conditional_rules, cross_field_rules

        # Deep copy to avoid mutating the base schemas
        schemas = copy.deepcopy(sheet_schemas)
        cond_rules = copy.deepcopy(conditional_rules)
        cross_rules = copy.deepcopy(cross_field_rules)

        for override in profile.field_overrides:
            if override.sheet in schemas and override.field in schemas[override.sheet]:
                setattr(schemas[override.sheet][override.field], override.property, override.value)

        if profile.custom_rules:
            for sheet, rules in profile.custom_rules.items():
                if sheet not in cond_rules:
                    cond_rules[sheet] = []
                cond_rules[sheet].extend(rules)

        return schemas, cond_rules, cross_rules

    def list_profiles(self) -> list[dict]:
        """List all profiles."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at,
                "enabled": p.enabled,
                "is_active": self.active_profile == p.name,
                "override_count": len(p.field_overrides),
            }
            for p in self.profiles.values()
        ]

    def delete_profile(self, name: str):
        """Delete a profile."""
        if name in self.profiles:
            del self.profiles[name]
            if self.active_profile == name:
                self.active_profile = None
            self._save_profiles()
