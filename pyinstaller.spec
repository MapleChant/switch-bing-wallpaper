# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

added_files = [
    ('src/', 'src/'),
    ('assets/', 'assets/'),
]

binaries = []
if sys.platform == 'win32':
    conda_path = os.path.dirname(sys.executable)
    dlls_path = os.path.join(conda_path, 'DLLs')
    library_bin_path = os.path.join(conda_path, 'Library', 'bin')
    
    dlls_to_include = [
        'libexpat.dll',
        'liblzma.dll', 
        'LIBBZ2.dll',
        'libmpdec-4.dll',
        'libcrypto-3-x64.dll',
        'libssl-3-x64.dll',
        'ffi.dll',
    ]
    
    for dll in dlls_to_include:
        dll_path = os.path.join(dlls_path, dll)
        if os.path.exists(dll_path):
            binaries.append((dll_path, '.'))
        dll_path2 = os.path.join(library_bin_path, dll)
        if os.path.exists(dll_path2):
            binaries.append((dll_path2, '.'))

a = Analysis(['main.py'],
             pathex=['/workspace'],
             binaries=binaries,
             datas=added_files,
             hiddenimports=['pyexpat', 'xml.parsers.expat'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

executable = EXE(pyz,
              a.scripts,
              [],
              exclude_binaries=True,
              name='switch-bing-wallpaper',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              console=False,
              disable_windowed_traceback=False,
              target_arch=None,
              codesign_identity=None,
              entitlements_file=None,
              icon='assets/icon.ico')

coll = COLLECT(executable,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='switch-bing-wallpaper')
