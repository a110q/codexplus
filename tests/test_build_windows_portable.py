import zipfile
from pathlib import Path

from scripts import build_windows_portable


def test_build_launcher_exe_uses_gui_stub_and_relative_embedded_python(tmp_path):
    stub = b"MZ-stub"
    output = tmp_path / "Codex++.exe"

    build_windows_portable.build_launcher_exe(output, stub)

    data = output.read_bytes()
    assert data.startswith(stub)
    assert b"#!.\\python\\pythonw.exe" in data
    assert b"codex_session_delete.cli" in data
    assert b"launch" in data

    zip_start = data.find(b"PK\x03\x04")
    assert zip_start > 0
    with zipfile.ZipFile(output) as archive:
        main_py = archive.read("__main__.py").decode("utf-8")

    assert "base = Path(sys.executable).resolve().parent.parent" in main_py
    assert "sys.path.insert(0, str(base / 'app'))" in main_py
    assert "cli.main(['launch', *sys.argv[1:]])" in main_py


def test_copy_application_files_preserves_runtime_package_and_inject_script(tmp_path):
    source = tmp_path / "source"
    package = source / "codex_session_delete"
    assets = package / "assets"
    inject = package / "inject"
    user_scripts = package / "user_scripts"
    assets.mkdir(parents=True)
    inject.mkdir(parents=True)
    user_scripts.mkdir(parents=True)
    (package / "__init__.py").write_text("__version__ = 'test'\n", encoding="utf-8")
    (package / "cli.py").write_text("def main(argv=None): return 0\n", encoding="utf-8")
    (package / "__pycache__").mkdir()
    (package / "__pycache__" / "cli.pyc").write_bytes(b"cache")
    (assets / "codex-plus-plus.ico").write_bytes(b"icon")
    (inject / "renderer-inject.js").write_text("console.log('same-ui');\n", encoding="utf-8")
    (user_scripts / ".gitkeep").write_text("", encoding="utf-8")
    (source / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    target = tmp_path / "portable"
    build_windows_portable.copy_application_files(source, target)

    app = target / "app"
    assert (app / "codex_session_delete" / "cli.py").is_file()
    assert (app / "codex_session_delete" / "assets" / "codex-plus-plus.ico").read_bytes() == b"icon"
    assert (app / "codex_session_delete" / "inject" / "renderer-inject.js").read_text(encoding="utf-8") == "console.log('same-ui');\n"
    assert (app / "codex_session_delete" / "user_scripts" / ".gitkeep").is_file()
    assert not (app / "codex_session_delete" / "__pycache__").exists()


def test_create_python_pth_enables_app_and_vendor_paths(tmp_path):
    build_windows_portable.create_python_pth(tmp_path, "python311")

    pth = (tmp_path / "python311._pth").read_text(encoding="utf-8")

    assert "../app" in pth
    assert "../vendor" in pth
    assert "import site" in pth


def test_read_project_dependencies_reads_runtime_dependencies(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = [
  "requests>=2.31",
  "websocket-client>=1.7",
]
""",
        encoding="utf-8",
    )

    assert build_windows_portable.read_project_dependencies(tmp_path) == ["requests>=2.31", "websocket-client>=1.7"]


def test_install_vendor_dependencies_downloads_and_extracts_wheels(monkeypatch, tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text(
        """
[project]
dependencies = [
  "requests>=2.31",
]
""",
        encoding="utf-8",
    )
    vendor = tmp_path / "vendor"
    calls = []

    def fake_run(args, check):
        calls.append(args)
        wheelhouse = Path(args[args.index("--dest") + 1])
        wheelhouse.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(wheelhouse / "requests-2.32.0-py3-none-any.whl", "w") as archive:
            archive.writestr("requests/__init__.py", "__version__ = '2.32.0'\n")
            archive.writestr("requests-2.32.0.dist-info/METADATA", "Name: requests\n")

    monkeypatch.setattr(build_windows_portable.subprocess, "run", fake_run)

    build_windows_portable.install_vendor_dependencies(vendor, project_root)

    assert (vendor / "requests" / "__init__.py").is_file()
    assert calls
    assert "--platform" in calls[0]
    assert "win_amd64" in calls[0]
    assert "requests>=2.31" in calls[0]
