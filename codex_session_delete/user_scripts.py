from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UserScriptConfig:
    enabled: bool
    scripts: dict[str, bool]


@dataclass(frozen=True)
class UserScript:
    key: str
    name: str
    source: str
    path: Path
    enabled: bool
    status: str = "pending"
    error: str = ""


class UserScriptManager:
    def __init__(self, builtin_dir: Path, user_dir: Path, config_path: Path):
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self.config_path = config_path

    def load_config(self) -> UserScriptConfig:
        if not self.config_path.exists():
            return UserScriptConfig(enabled=True, scripts={})
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return UserScriptConfig(enabled=True, scripts={})
        scripts = data.get("scripts", {})
        return UserScriptConfig(
            enabled=bool(data.get("enabled", True)),
            scripts={str(key): bool(value) for key, value in scripts.items()} if isinstance(scripts, dict) else {},
        )

    def save_config(self, config: UserScriptConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps({"enabled": config.enabled, "scripts": config.scripts}, ensure_ascii=False, indent=2), encoding="utf-8")

    def scan(self) -> list[UserScript]:
        self.user_dir.mkdir(parents=True, exist_ok=True)
        config = self.load_config()
        scripts: list[UserScript] = []
        for source, directory in [("builtin", self.builtin_dir), ("user", self.user_dir)]:
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.js"), key=lambda item: item.name.lower()):
                key = f"{source}:{path.name}"
                scripts.append(UserScript(key=key, name=path.name, source=source, path=path, enabled=config.scripts.get(key, True)))
        return scripts

    def set_global_enabled(self, enabled: bool) -> UserScriptConfig:
        config = self.load_config()
        next_config = UserScriptConfig(enabled=enabled, scripts=dict(config.scripts))
        self.save_config(next_config)
        return next_config

    def set_script_enabled(self, key: str, enabled: bool) -> UserScriptConfig:
        config = self.load_config()
        scripts = dict(config.scripts)
        scripts[key] = enabled
        next_config = UserScriptConfig(enabled=config.enabled, scripts=scripts)
        self.save_config(next_config)
        return next_config

    def inventory(self, statuses: dict[str, dict[str, str]] | None = None) -> dict[str, object]:
        config = self.load_config()
        status_map = statuses or {}
        scripts = []
        for script in self.scan():
            status = "disabled" if not config.enabled or not script.enabled else status_map.get(script.key, {}).get("status", "not_loaded")
            scripts.append({
                "key": script.key,
                "name": script.name,
                "source": script.source,
                "enabled": script.enabled,
                "status": status,
                "error": status_map.get(script.key, {}).get("error", ""),
            })
        return {"enabled": config.enabled, "builtin_dir": str(self.builtin_dir), "user_dir": str(self.user_dir), "scripts": scripts}

    def enabled_scripts(self) -> list[UserScript]:
        config = self.load_config()
        if not config.enabled:
            return []
        return [script for script in self.scan() if script.enabled]

    def build_enabled_bundle(self) -> str:
        blocks = []
        for script in self.enabled_scripts():
            try:
                source = script.path.read_text(encoding="utf-8")
            except OSError as exc:
                source = f"throw new Error({json.dumps(str(exc))});"
            blocks.append(self._wrap_script(script, source))
        return "\n".join(blocks)

    def _wrap_script(self, script: UserScript, source: str) -> str:
        key = json.dumps(script.key)
        name = json.dumps(script.name)
        source_name = json.dumps(script.source)
        return f"""
(() => {{
  window.__codexPlusUserScripts = window.__codexPlusUserScripts || {{ scripts: {{}} }};
  const key = {key};
  window.__codexPlusUserScripts.scripts[key] = {{ key, name: {name}, source: {source_name}, status: "loading", error: "", loadedAt: new Date().toISOString() }};
  try {{
{source}
    window.__codexPlusUserScripts.scripts[key].status = "loaded";
    window.__codexPlusUserScripts.scripts[key].loadedAt = new Date().toISOString();
  }} catch (error) {{
    window.__codexPlusUserScripts.scripts[key].status = "failed";
    window.__codexPlusUserScripts.scripts[key].error = String(error && (error.stack || error.message) || error);
  }}
}})();
"""
