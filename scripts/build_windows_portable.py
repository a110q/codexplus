from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by Python 3.9 in CI-like local runs.
    tomllib = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PYTHON_VERSION = "3.11.9"
PYTHON_TAG = "python311"


LAUNCHER_MAIN = """\
from __future__ import annotations

import sys
from pathlib import Path

base = Path(sys.executable).resolve().parent.parent
sys.path.insert(0, str(base / 'app'))
sys.path.insert(0, str(base / 'vendor'))

import codex_session_delete.cli as cli

if __name__ == '__main__':
    raise SystemExit(cli.main(['launch', *sys.argv[1:]]))
"""


def python_embed_url(version: str, arch: str) -> str:
    return f"https://www.python.org/ftp/python/{version}/python-{version}-embed-{arch}.zip"


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        destination.write_bytes(response.read())


def extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)


def create_python_pth(python_dir: Path, tag: str = PYTHON_TAG) -> None:
    (python_dir / f"{tag}._pth").write_text(
        "\n".join(
            [
                f"{tag}.zip",
                ".",
                "../app",
                "../vendor",
                "",
                "import site",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _read_pyproject(project_root: Path) -> dict[str, Any]:
    path = project_root / "pyproject.toml"
    if tomllib is not None:
        with path.open("rb") as file:
            return tomllib.load(file)

    # Minimal fallback for Python 3.10 and older. This project only needs the
    # simple [project].dependencies array used in pyproject.toml.
    dependencies: list[str] = []
    in_dependencies = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("dependencies"):
            in_dependencies = True
            continue
        if in_dependencies and line.startswith("]"):
            break
        if in_dependencies and line.startswith('"'):
            dependencies.append(line.split('"', 2)[1])
    return {"project": {"dependencies": dependencies}}


def read_project_dependencies(project_root: Path = PROJECT_ROOT) -> list[str]:
    pyproject = _read_pyproject(project_root)
    return list(pyproject.get("project", {}).get("dependencies", []))


def download_dependency_wheels(wheelhouse: Path, project_root: Path = PROJECT_ROOT, arch: str = "amd64") -> None:
    dependencies = read_project_dependencies(project_root)
    if not dependencies:
        return

    platform = {
        "amd64": "win_amd64",
        "win32": "win32",
        "arm64": "win_arm64",
    }[arch]
    wheelhouse.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "download",
            "--dest",
            str(wheelhouse),
            "--only-binary",
            ":all:",
            "--implementation",
            "py",
            "--python-version",
            "3.11",
            "--abi",
            "none",
            "--platform",
            platform,
            *dependencies,
        ],
        check=True,
    )


def extract_dependency_wheels(wheelhouse: Path, vendor_dir: Path) -> None:
    vendor_dir.mkdir(parents=True, exist_ok=True)
    for wheel in sorted(wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(vendor_dir)


def install_vendor_dependencies(vendor_dir: Path, project_root: Path = PROJECT_ROOT, cache_dir: Path | None = None, arch: str = "amd64") -> None:
    vendor_dir.mkdir(parents=True, exist_ok=True)
    wheelhouse = (cache_dir or project_root / ".build-cache") / "wheels" / arch
    if wheelhouse.exists():
        shutil.rmtree(wheelhouse)
    download_dependency_wheels(wheelhouse, project_root, arch)
    extract_dependency_wheels(wheelhouse, vendor_dir)


def copytree_filtered(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".pytest_cache"))


def copy_application_files(project_root: Path, output_dir: Path) -> None:
    app_dir = output_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    copytree_filtered(project_root / "codex_session_delete", app_dir / "codex_session_delete")
    shutil.copy2(project_root / "pyproject.toml", app_dir / "pyproject.toml")


def distlib_gui_stub() -> bytes:
    try:
        import pip._vendor.distlib.scripts as distlib_scripts

        distlib_dir = Path(distlib_scripts.__file__).resolve().parent
        return (distlib_dir / "w64.exe").read_bytes()
    except (ImportError, OSError) as exc:
        raise RuntimeError("pip vendored distlib Windows launcher stub was not found.") from exc


def build_launcher_exe(output: Path, gui_stub: bytes | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    stub = gui_stub if gui_stub is not None else distlib_gui_stub()
    shebang = b"#!.\\python\\pythonw.exe\n"
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("__main__.py", LAUNCHER_MAIN)
    output.write_bytes(stub + shebang + stream.getvalue())


def write_readme(output_dir: Path, version: str, arch: str) -> None:
    (output_dir / "README-Windows-Portable.txt").write_text(
        f"""Codex++ Windows Portable

Python runtime: {version} embeddable {arch}

Usage:
1. Keep this folder intact.
2. Double-click Codex++.exe.
3. Codex App must already be installed on Windows.

Codex++.exe launches the same codex_session_delete package, assets, user scripts, and renderer-inject.js used by the macOS app bundle, so the Codex++ menu and features stay aligned across macOS and Windows.

Logs:
%USERPROFILE%\\.codex-session-delete\\launcher.log
""",
        encoding="utf-8",
    )


def build_portable(output_dir: Path, cache_dir: Path, version: str, arch: str, skip_vendor: bool) -> Path:
    clean_dir(output_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    zip_path = cache_dir / f"python-{version}-embed-{arch}.zip"
    if not zip_path.exists():
        download_file(python_embed_url(version, arch), zip_path)

    python_dir = output_dir / "python"
    extract_zip(zip_path, python_dir)
    create_python_pth(python_dir)

    copy_application_files(PROJECT_ROOT, output_dir)
    if not skip_vendor:
        install_vendor_dependencies(output_dir / "vendor", PROJECT_ROOT, cache_dir, arch)

    build_launcher_exe(output_dir / "Codex++.exe")
    write_readme(output_dir, version, arch)
    return output_dir / "Codex++.exe"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Windows portable Codex++ folder.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "dist" / "Codex++-win-portable")
    parser.add_argument("--cache-dir", type=Path, default=PROJECT_ROOT / ".build-cache")
    parser.add_argument("--python-version", default=DEFAULT_PYTHON_VERSION)
    parser.add_argument("--arch", default="amd64", choices=["amd64", "win32", "arm64"])
    parser.add_argument("--skip-vendor", action="store_true", help="Skip dependency installation; useful for structure-only packaging tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    exe = build_portable(args.output_dir, args.cache_dir, args.python_version, args.arch, args.skip_vendor)
    print(f"Built {exe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
