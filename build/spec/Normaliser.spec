# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/franconi/Documents/Codex/Normalisation/desktop_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['combined_null_4nf_frontend', 'combined_null_4nf_decomposer', 'fd_mvd_normalizer', 'sql_null_decomposer', 'six_nf'],
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
    name='Normaliser',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Normaliser',
)
app = BUNDLE(
    coll,
    name='Normaliser.app',
    icon=None,
    bundle_identifier=None,
)
