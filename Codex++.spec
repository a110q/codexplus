# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['codex_session_delete/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('codex_session_delete/inject/renderer-inject.js', 'codex_session_delete/inject')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Codex++',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Applications/Codex.app/Contents/Resources/electron.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Codex++',
)
app = BUNDLE(
    coll,
    name='Codex++.app',
    icon='/Applications/Codex.app/Contents/Resources/electron.icns',
    bundle_identifier='com.bigpizzav3.codexplusplus',
    version='1.0.1',
    info_plist={
        'CFBundleDisplayName': 'Codex++',
        'CFBundleShortVersionString': '1.0.1',
        'CFBundleVersion': '1.0.1',
        'LSMinimumSystemVersion': '12.0',
    },
)
