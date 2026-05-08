from __future__ import annotations

import argparse
import sys
import traceback
import subprocess as _sp
import time as _time
from pathlib import Path

from codex_session_delete.app_paths import resolve_codex_app_dir
from codex_session_delete.helper_server import HelperServer
from codex_session_delete.installers import InstallOptions, install_codex_plus_plus, uninstall_codex_plus_plus
from codex_session_delete.launcher import build_codex_executable, launch_and_inject, shutdown_helper


def add_launch_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--app-dir", type=Path, default=None)
    parser.add_argument("--db", type=Path, default=Path.home() / ".codex" / "state_5.sqlite", help="SQLite database path for local deletion fallback")
    parser.add_argument("--backup-dir", type=Path, default=Path.home() / ".codex-session-delete" / "backups")
    parser.add_argument("--debug-port", type=int, default=9229)
    parser.add_argument("--helper-port", type=int, default=57321)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch and install Codex++ for Codex App")
    subparsers = parser.add_subparsers(dest="command")

    launch_parser = subparsers.add_parser("launch", help="Launch Codex with Codex++ injection")
    add_launch_arguments(launch_parser)

    install_parser = subparsers.add_parser("install", help="Install the Codex++ launcher entry point")
    install_parser.add_argument("--install-root", type=Path, default=None)
    install_parser.add_argument("--launcher-command", default=None)

    setup_parser = subparsers.add_parser("setup", help="Install Codex++ with defaults")
    setup_parser.add_argument("--install-root", type=Path, default=None)

    uninstall_parser = subparsers.add_parser("uninstall", help="Remove the Codex++ launcher entry point")
    uninstall_parser.add_argument("--install-root", type=Path, default=None)
    uninstall_parser.add_argument("--remove-data", action="store_true")

    remove_parser = subparsers.add_parser("remove", help="Remove Codex++ with defaults")
    remove_parser.add_argument("--install-root", type=Path, default=None)
    remove_parser.add_argument("--remove-data", action="store_true")

    add_launch_arguments(parser)
    return parser




def launch_log_path() -> Path:
    return Path.home() / ".codex-session-delete" / "launcher.log"


def log_launch_failure(exc: BaseException) -> None:
    path = launch_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), encoding="utf-8")


def wait_for_windows_process_id(process_id: int) -> None:
    if sys.platform != "win32":
        return
    import ctypes

    synchronize = 0x00100000
    infinite = 0xFFFFFFFF
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel32.WaitForSingleObject.restype = ctypes.c_ulong
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int

    handle = kernel32.OpenProcess(synchronize, False, process_id)
    if not handle:
        return
    try:
        kernel32.WaitForSingleObject(handle, infinite)
    finally:
        kernel32.CloseHandle(handle)


def wait_for_shutdown(server: HelperServer, codex_proc) -> None:
    try:
        if isinstance(codex_proc, int):
            wait_for_windows_process_id(codex_proc)
        elif codex_proc is None and sys.platform == "darwin":
            codex_app = resolve_codex_app_dir()
            executable = build_codex_executable(codex_app) if codex_app is not None else Path("/Applications/Codex.app/Contents/MacOS/Codex")
            while True:
                result = _sp.run(["pgrep", "-f", "^" + str(executable)], capture_output=True)
                if result.returncode != 0:
                    break
                _time.sleep(2)
        elif codex_proc is not None:
            codex_proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown_helper(server)


def run_launch(args: argparse.Namespace) -> int:
    try:
        server, codex_proc = launch_and_inject(args.app_dir, args.db, args.backup_dir, args.debug_port, args.helper_port)
    except Exception as exc:
        log_launch_failure(exc)
        raise
    print(f"Codex session delete helper running on http://127.0.0.1:{server.port}")
    print("Keep this terminal open while using the delete buttons. Press Ctrl+C to stop.")
    wait_for_shutdown(server, codex_proc)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"install", "setup"}:
        install_codex_plus_plus(InstallOptions(install_root=args.install_root, launcher_command=getattr(args, "launcher_command", None)))
        return 0
    if args.command in {"uninstall", "remove"}:
        uninstall_codex_plus_plus(InstallOptions(install_root=args.install_root, remove_data=args.remove_data))
        return 0
    return run_launch(args)


if __name__ == "__main__":
    raise SystemExit(main())
