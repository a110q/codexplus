from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackendSettings:
    provider_sync_enabled: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "BackendSettings":
        return cls(provider_sync_enabled=bool(data.get("providerSyncEnabled", False)))

    def to_dict(self) -> dict[str, object]:
        return {"providerSyncEnabled": self.provider_sync_enabled}


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path or default_settings_path()

    def load(self) -> BackendSettings:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return BackendSettings()
        return BackendSettings.from_dict(data if isinstance(data, dict) else {})

    def save(self, settings: BackendSettings) -> BackendSettings:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(f"{self.path.name}.tmp")
        temp_path.write_text(json.dumps(settings.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp_path, self.path)
        return settings

    def update(self, values: dict[str, object]) -> BackendSettings:
        current = self.load().to_dict()
        if "providerSyncEnabled" in values:
            current["providerSyncEnabled"] = bool(values["providerSyncEnabled"])
        return self.save(BackendSettings.from_dict(current))


def default_settings_path() -> Path:
    return Path.home() / ".codex-session-delete" / "settings.json"
