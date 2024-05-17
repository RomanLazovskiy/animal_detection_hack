# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('ultralytics')

a = Analysis(
    ['gui/app.py'],
    pathex=['/Users/rvlazovskiy/Desktop/Hacks/animal_detection_hack'],
    binaries=[],
    datas=datas + [
        ('backend/*', 'backend'),  # Включаем файлы из папки backend
    ],
    hiddenimports=[
        'ultralytics',
        'ultralytics.data',
        'ultralytics.data.base',
        'ultralytics.data.utils',
        'ultralytics.nn',
        'ultralytics.nn.tasks',
        'ultralytics.nn.modules',
        'ultralytics.nn.modules.head',
        'ultralytics.utils',
    ],
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
    a.binaries,
    a.datas,
    [],
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='app.app',
    icon=None,
    bundle_identifier=None,
)