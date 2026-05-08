import pytest

from codex_session_delete import installers
from codex_session_delete.installers import InstallOptions


def test_install_dispatches_to_macos(monkeypatch):
    calls = []
    monkeypatch.setattr(installers.sys, "platform", "darwin")
    monkeypatch.setattr(installers, "install_macos_app", lambda options: calls.append(options))

    options = InstallOptions()
    installers.install_codex_plus_plus(options)

    assert calls == [options]


def test_install_dispatches_to_windows(monkeypatch):
    calls = []
    monkeypatch.setattr(installers.sys, "platform", "win32")
    monkeypatch.setattr(installers, "install_windows_shortcuts", lambda options: calls.append(options))

    options = InstallOptions()
    installers.install_codex_plus_plus(options)

    assert calls == [options]


def test_uninstall_dispatches_to_macos(monkeypatch):
    calls = []
    monkeypatch.setattr(installers.sys, "platform", "darwin")
    monkeypatch.setattr(installers, "uninstall_macos_app", lambda options: calls.append(options))

    options = InstallOptions(remove_data=True)
    installers.uninstall_codex_plus_plus(options)

    assert calls == [options]


def test_unsupported_platform_raises(monkeypatch):
    monkeypatch.setattr(installers.sys, "platform", "linux")

    with pytest.raises(RuntimeError, match="Unsupported platform"):
        installers.install_codex_plus_plus(InstallOptions())


def test_remove_owned_data_removes_codex_session_delete_dir(tmp_path, monkeypatch):
    data_dir = tmp_path / ".codex-session-delete"
    data_dir.mkdir()
    (data_dir / "marker.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(installers.Path, "home", lambda: tmp_path)

    installers.remove_owned_data()

    assert not data_dir.exists()
