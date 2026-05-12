from codex_session_delete.user_scripts import UserScriptConfig, UserScriptManager


def test_user_script_manager_scans_builtin_then_user_scripts(tmp_path):
    builtin = tmp_path / "builtin"
    user = tmp_path / "user"
    config_path = tmp_path / "config.json"
    builtin.mkdir()
    user.mkdir()
    (builtin / "b.js").write_text("window.b = true;", encoding="utf-8")
    (builtin / "a.txt").write_text("ignored", encoding="utf-8")
    (user / "a.js").write_text("window.a = true;", encoding="utf-8")

    manager = UserScriptManager(builtin, user, config_path)
    scripts = manager.scan()

    assert [script.key for script in scripts] == ["builtin:b.js", "user:a.js"]
    assert [script.name for script in scripts] == ["b.js", "a.js"]
    assert scripts[0].source == "builtin"
    assert scripts[1].source == "user"
    assert scripts[0].enabled is True
    assert scripts[1].enabled is True


def test_user_script_manager_missing_directories_and_default_config(tmp_path):
    manager = UserScriptManager(tmp_path / "missing-builtin", tmp_path / "created-user", tmp_path / "config.json")

    assert manager.load_config() == UserScriptConfig(enabled=True, scripts={})
    assert manager.scan() == []


def test_user_script_manager_updates_global_enabled(tmp_path):
    manager = UserScriptManager(tmp_path / "builtin", tmp_path / "user", tmp_path / "config.json")

    manager.set_global_enabled(False)

    assert manager.load_config().enabled is False


def test_user_script_manager_updates_script_enabled(tmp_path):
    manager = UserScriptManager(tmp_path / "builtin", tmp_path / "user", tmp_path / "config.json")

    manager.set_script_enabled("user:demo.js", False)

    assert manager.load_config().scripts == {"user:demo.js": False}


def test_user_script_manager_inventory_contains_directories_and_disabled_status(tmp_path):
    builtin = tmp_path / "builtin"
    user = tmp_path / "user"
    builtin.mkdir()
    user.mkdir()
    (builtin / "demo.js").write_text("window.demo = true;", encoding="utf-8")
    manager = UserScriptManager(builtin, user, tmp_path / "config.json")
    manager.set_script_enabled("builtin:demo.js", False)

    inventory = manager.inventory()

    assert inventory["enabled"] is True
    assert inventory["builtin_dir"] == str(builtin)
    assert inventory["user_dir"] == str(user)
    assert inventory["scripts"][0]["key"] == "builtin:demo.js"


def test_user_script_manager_builds_enabled_script_bundle(tmp_path):
    builtin = tmp_path / "builtin"
    user = tmp_path / "user"
    builtin.mkdir()
    user.mkdir()
    (builtin / "alpha.js").write_text("window.alpha = true;", encoding="utf-8")
    (user / "beta.js").write_text("throw new Error('boom');", encoding="utf-8")
    manager = UserScriptManager(builtin, user, tmp_path / "config.json")
    manager.set_script_enabled("user:beta.js", False)

    bundle = manager.build_enabled_bundle()

    assert "window.__codexPlusUserScripts" in bundle
    assert "builtin:alpha.js" in bundle
    assert "window.alpha = true;" in bundle
    assert "user:beta.js" not in bundle
    assert "try" in bundle
    assert "catch" in bundle


def test_user_script_manager_global_disable_builds_empty_bundle(tmp_path):
    builtin = tmp_path / "builtin"
    user = tmp_path / "user"
    builtin.mkdir()
    (builtin / "alpha.js").write_text("window.alpha = true;", encoding="utf-8")
    manager = UserScriptManager(builtin, user, tmp_path / "config.json")
    manager.set_global_enabled(False)

    assert manager.build_enabled_bundle() == ""
