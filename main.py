#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bing壁纸切换软件主入口
"""

import sys
import os

if sys.platform == 'win32' and sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.app import WallpaperApp

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("switch-bing-wallpaper")
    app.setApplicationVersion("1.0.0")
    
    window = WallpaperApp()
    window.show()
    
    sys.exit(app.exec_())
