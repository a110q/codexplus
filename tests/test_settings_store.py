import json

from codex_session_delete.settings_store import BackendSettings, SettingsStore


def test_settings_store_defaults_provider_sync_disabled(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")

    settings = store.load()

    assert settings == BackendSettings(provider_sync_enabled=False)
    assert settings.to_dict() == {"providerSyncEnabled": False}


def test_settings_store_saves_and_reloads_provider_sync(tmp_path):
    store = SettingsStore(tmp_path / "settings.json")

    saved = store.save(BackendSettings(provider_sync_enabled=True))

    assert saved == BackendSettings(provider_sync_enabled=True)
    assert json.loads((tmp_path / "settings.json").read_text(encoding="utf-8")) == {"providerSyncEnabled": True}
    assert store.load() == BackendSettings(provider_sync_enabled=True)


def test_settings_store_ignores_malformed_json(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("not json", encoding="utf-8")
    store = SettingsStore(path)

    assert store.load() == BackendSettings(provider_sync_enabled=False)
