from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from codex_session_delete.macos_installer import install_macos_app, uninstall_macos_app
from codex_session_delete.windows_installer import install_windows_shortcuts, uninstall_windows_shortcuts


@dataclass(frozen=True)
class InstallOptions:
    install_root: Path | None = None
    launcher_command: str | None = None
    remove_data: bool = False


def install_codex_plus_plus(options: InstallOptions) -> None:
    if sys.platform == "darwin":
        install_macos_app(options)
        return
    if sys.platform == "win32":
        install_windows_shortcuts(options)
        return
    raise RuntimeError(f"Unsupported platform for Codex++ install: {sys.platform}")


def uninstall_codex_plus_plus(options: InstallOptions) -> None:
    if sys.platform == "darwin":
        uninstall_macos_app(options)
        if options.remove_data:
            remove_owned_data()
        return
    if sys.platform == "win32":
        uninstall_windows_shortcuts(options)
        if options.remove_data:
            remove_owned_data()
        return
    raise RuntimeError(f"Unsupported platform for Codex++ uninstall: {sys.platform}")


def remove_owned_data() -> None:
    data_dir = Path.home() / ".codex-session-delete"
    if data_dir.exists():
        shutil.rmtree(data_dir)
