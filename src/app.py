#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bing壁纸切换软件主窗口
"""

import os
import time
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QListWidget, QListWidgetItem, QMenu, QAction, QSystemTrayIcon,
    QApplication, QStyle, QFileDialog, QMessageBox, QDialog, QComboBox,
    QSpinBox, QGridLayout, QGroupBox, QRadioButton, QButtonGroup,
    QTabWidget, QScrollArea, QCheckBox, QLineEdit, QDateTimeEdit,
    QSplitter, QFrame, QSizePolicy, QProgressBar
)
from PyQt5.QtGui import QPixmap, QIcon, QCursor, QFont, QPalette, QColor, QMovie, QImage
from PyQt5.QtCore import Qt, QTimer, QSize, QDateTime, QSortFilterProxyModel, QThread, pyqtSignal

from src.bing_api import BingAPI
from src.wallpaper_manager import WallpaperManager
from src.config_manager import ConfigManager


def load_image_with_pil(path):
    """使用PIL加载图片并转换为QPixmap"""
    try:
        from PIL import Image
        import io
        
        with Image.open(path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            data = io.BytesIO()
            img.save(data, format='PNG')
            data.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(data.read())
            return pixmap
    except Exception as e:
        print(f"[DEBUG] PIL加载图片失败: {e}", flush=True)
        return QPixmap()


class WallpaperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = ConfigManager()
        self.bing_api = BingAPI()
        self.wallpaper_manager = WallpaperManager()
        self.current_wallpaper = None
        self.current_wallpaper_index = 0
        self.wallpapers_list = []
        self.is_loading = False
        
        self.init_ui()
        self.init_tray()
        self.start_auto_change_timer()
        
        QTimer.singleShot(100, self.load_wallpapers)
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("switch-bing-wallpaper")
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        logical_dpi = screen.logicalDotsPerInch()
        standard_dpi = 96.0
        scale_factor = logical_dpi / standard_dpi
        
        base_width = 800
        base_height = 600
        min_base_width = 600
        min_base_height = 450
        
        default_width = int(base_width * scale_factor)
        default_height = int(base_height * scale_factor)
        min_width = int(min_base_width * scale_factor)
        min_height = int(min_base_height * scale_factor)
        
        default_width = min(default_width, int(screen_geometry.width() * 0.8))
        default_height = min(default_height, int(screen_geometry.height() * 0.8))
        min_width = min(min_width, int(screen_geometry.width() * 0.5))
        min_height = min(min_height, int(screen_geometry.height() * 0.5))
        
        self.resize(default_width, default_height)
        self.setMinimumSize(min_width, min_height)
        
        self.setStyleSheet(self._get_main_stylesheet())
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        self.home_page = QWidget()
        self.init_home_page()
        self.tab_widget.addTab(self.home_page, "首页")
        
        self.manager_page = QWidget()
        self.init_manager_page()
        self.tab_widget.addTab(self.manager_page, "壁纸管理")
        
        self.statusBar().showMessage("就绪")
    
    def _get_main_stylesheet(self):
        return """
            QMainWindow { background-color: #f8f9fa; }
            QTabWidget::pane { 
                border: 1px solid #e0e0e0; 
                background-color: white; 
                border-radius: 8px;
            }
            QTabBar::tab { 
                background-color: #e8e8e8; 
                padding: 14px 36px; 
                margin-right: 4px; 
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
                color: #666;
                min-width: 100px;
                min-height: 20px;
            }
            QTabBar::tab:selected { 
                background-color: white; 
                border-bottom: 3px solid #2196f3;
                color: #2196f3;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
            QLabel { color: #424242; }
            QGroupBox { 
                background-color: white; 
                border: 1px solid #e0e0e0; 
                border-radius: 12px; 
                padding: 20px 15px 15px 15px; 
                margin-top: 12px;
                font-size: 11pt;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 8px; 
                font-weight: bold; 
                color: #333; 
            }
            QComboBox { 
                border: 2px solid #e0e0e0; 
                border-radius: 6px; 
                padding: 6px 10px; 
                background-color: white; 
                min-height: 20px;
            }
            QComboBox:hover, QComboBox:focus { border-color: #2196f3; }
            QComboBox::drop-down { border: none; padding-right: 8px; width: 20px; }
            QSpinBox { 
                border: 2px solid #e0e0e0; 
                border-radius: 6px; 
                padding: 6px 10px; 
                background-color: white; 
                min-height: 20px;
            }
            QSpinBox:hover, QSpinBox:focus { border-color: #2196f3; }
            QCheckBox { margin: 8px 0; spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical { 
                background-color: #f5f5f5; 
                width: 10px; 
                border-radius: 5px; 
                margin: 2px;
            }
            QScrollBar::handle:vertical { 
                background-color: #bdbdbd; 
                border-radius: 5px; 
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background-color: #9e9e9e; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QLineEdit { 
                border: 2px solid #e0e0e0; 
                border-radius: 6px; 
                padding: 6px 10px; 
                background-color: white;
                min-height: 20px;
            }
            QLineEdit:hover, QLineEdit:focus { border-color: #2196f3; }
            QStatusBar { 
                background-color: #e3f2fd; 
                padding: 8px 12px; 
                color: #1565c0;
            }
            QTabWidget { background-color: #f8f9fa; }
        """
    
    def init_home_page(self):
        """初始化首页"""
        layout = QVBoxLayout(self.home_page)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title_layout = QHBoxLayout()
        title_label = QLabel("今日Bing壁纸")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")
        title_layout.addWidget(title_label)
        
        self.refresh_button = QPushButton()
        self.refresh_button.setToolTip("刷新壁纸列表")
        self.refresh_button.setFixedSize(44, 44)
        self.refresh_button.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserReload))
        self.refresh_button.setStyleSheet("""
            QPushButton { 
                background-color: white; 
                border: 2px solid #e0e0e0; 
                border-radius: 22px; 
            }
            QPushButton:hover { 
                background-color: #f5f5f5; 
                border-color: #2196f3; 
            }
            QPushButton:pressed { background-color: #e8e8e8; }
        """)
        self.refresh_button.clicked.connect(self.refresh_wallpapers)
        title_layout.addWidget(self.refresh_button)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setSpacing(15)
        
        preview_container = QFrame()
        preview_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
            }
        """)
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(8, 8, 8, 8)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 250)
        self.preview_label.setStyleSheet("background-color: #fafafa; border-radius: 8px;")
        self.preview_label.setText("")
        preview_container_layout.addWidget(self.preview_label)
        
        preview_layout.addWidget(preview_container)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.setAlignment(Qt.AlignCenter)
        
        nav_button_style = """
            QPushButton { 
                background-color: white; 
                color: #666; 
                border: 2px solid #ddd; 
                border-radius: 20px; 
                font-size: 14pt; 
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover { 
                background-color: #f0f7ff; 
                border-color: #2196f3; 
                color: #2196f3;
            }
            QPushButton:pressed { 
                background-color: #e3f2fd; 
            }
        """
        
        self.prev_button = QPushButton("<")
        self.prev_button.setFixedSize(40, 40)
        self.prev_button.setStyleSheet(nav_button_style)
        self.prev_button.setCursor(Qt.PointingHandCursor)
        self.prev_button.clicked.connect(self.prev_wallpaper)
        button_layout.addWidget(self.prev_button)
        
        action_button_style = """
            QPushButton { 
                background-color: #2196f3; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                font-size: 10pt; 
                font-weight: 600;
                padding: 12px 24px;
            }
            QPushButton:hover { 
                background-color: #1976d2; 
            }
            QPushButton:pressed { 
                background-color: #1565c0; 
            }
        """
        
        self.download_button = QPushButton("下载壁纸")
        self.download_button.setStyleSheet(action_button_style)
        self.download_button.setCursor(Qt.PointingHandCursor)
        self.download_button.clicked.connect(self.download_wallpaper)
        button_layout.addWidget(self.download_button)
        
        self.set_wallpaper_button = QPushButton("设为壁纸")
        self.set_wallpaper_button.setStyleSheet(action_button_style)
        self.set_wallpaper_button.setCursor(Qt.PointingHandCursor)
        self.set_wallpaper_button.clicked.connect(self.set_as_wallpaper)
        button_layout.addWidget(self.set_wallpaper_button)
        
        self.favorite_button = QPushButton("♡")
        self.favorite_button.setFixedSize(40, 40)
        self.favorite_button.setStyleSheet("""
            QPushButton { 
                background-color: #fff0f0; 
                color: #e53935; 
                border: 2px solid #ffcdd2; 
                border-radius: 20px; 
                font-size: 16pt;
                padding: 0px;
            }
            QPushButton:hover { 
                background-color: #ffebee; 
                border-color: #e53935; 
            }
            QPushButton:pressed { 
                background-color: #ffcdd2; 
            }
        """)
        self.favorite_button.setCursor(Qt.PointingHandCursor)
        self.favorite_button.clicked.connect(self.toggle_favorite)
        button_layout.addWidget(self.favorite_button)
        
        self.next_button = QPushButton(">")
        self.next_button.setFixedSize(40, 40)
        self.next_button.setStyleSheet(nav_button_style)
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.clicked.connect(self.next_wallpaper)
        button_layout.addWidget(self.next_button)
        
        preview_layout.addLayout(button_layout)
        
        info_container = QFrame()
        info_container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 10px;
            }
        """)
        info_container_layout = QVBoxLayout(info_container)
        info_container_layout.setContentsMargins(15, 12, 15, 12)
        
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-size: 10pt; color: #616161; border: none; background: transparent;")
        self.info_label.setText("加载中...")
        info_container_layout.addWidget(self.info_label)
        
        preview_layout.addWidget(info_container)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(15)
        right_widget.setMinimumWidth(250)
        right_widget.setMaximumWidth(300)
        
        config_group = QGroupBox("设置")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(12)
        
        auto_layout = QGridLayout()
        auto_layout.setSpacing(10)
        
        interval_label = QLabel("切换间隔:")
        interval_label.setStyleSheet("font-weight: 500;")
        auto_layout.addWidget(interval_label, 0, 0)
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["15分钟", "30分钟", "60分钟", "自定义"])
        current_interval = self.config.get("auto_change_interval")
        if current_interval == 900:
            self.interval_combo.setCurrentIndex(0)
        elif current_interval == 1800:
            self.interval_combo.setCurrentIndex(1)
        elif current_interval == 3600:
            self.interval_combo.setCurrentIndex(2)
        else:
            self.interval_combo.setCurrentIndex(3)
        auto_layout.addWidget(self.interval_combo, 0, 1)
        
        custom_label = QLabel("自定义(秒):")
        custom_label.setStyleSheet("font-weight: 500;")
        auto_layout.addWidget(custom_label, 1, 0)
        
        self.custom_spin = QSpinBox()
        self.custom_spin.setMinimum(60)
        self.custom_spin.setMaximum(86400)
        self.custom_spin.setValue(self.config.get("custom_interval", 3600))
        auto_layout.addWidget(self.custom_spin, 1, 1)
        
        mode_label = QLabel("切换模式:")
        mode_label.setStyleSheet("font-weight: 500;")
        auto_layout.addWidget(mode_label, 2, 0)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["随机", "喜爱", "顺序"])
        current_mode = self.config.get("change_mode")
        if current_mode == "random":
            self.mode_combo.setCurrentIndex(0)
        elif current_mode == "favorite":
            self.mode_combo.setCurrentIndex(1)
        else:
            self.mode_combo.setCurrentIndex(2)
        auto_layout.addWidget(self.mode_combo, 2, 1)
        
        dir_label = QLabel("缓存目录:")
        dir_label.setStyleSheet("font-weight: 500;")
        auto_layout.addWidget(dir_label, 3, 0)
        
        dir_layout = QHBoxLayout()
        self.dir_edit = QLineEdit()
        self.dir_edit.setText(self.config.get("wallpaper_dir"))
        dir_layout.addWidget(self.dir_edit)
        self.browse_button = QPushButton("...")
        self.browse_button.setFixedSize(36, 36)
        self.browse_button.setStyleSheet("""
            QPushButton { 
                background-color: #f5f5f5; 
                color: #666; 
                border: 2px solid #ddd; 
                border-radius: 6px; 
                font-size: 12pt;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover { 
                background-color: #e3f2fd; 
                border-color: #2196f3;
                color: #2196f3;
            }
        """)
        self.browse_button.setCursor(Qt.PointingHandCursor)
        self.browse_button.clicked.connect(self.browse_cache_dir)
        dir_layout.addWidget(self.browse_button)
        auto_layout.addLayout(dir_layout, 3, 1)
        
        config_layout.addLayout(auto_layout)
        
        self.save_config_button = QPushButton("保存设置")
        self.save_config_button.setStyleSheet("""
            QPushButton { 
                background-color: #4caf50; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                font-size: 10pt; 
                font-weight: 600;
                padding: 12px 20px;
            }
            QPushButton:hover { background-color: #43a047; }
            QPushButton:pressed { background-color: #388e3c; }
        """)
        self.save_config_button.setCursor(Qt.PointingHandCursor)
        self.save_config_button.clicked.connect(self.save_config)
        config_layout.addWidget(self.save_config_button)
        
        right_layout.addWidget(config_group)
        right_layout.addStretch()
        
        content_layout.addWidget(preview_widget, stretch=3)
        content_layout.addWidget(right_widget, stretch=1)
        layout.addLayout(content_layout)
    
    def init_manager_page(self):
        """初始化壁纸管理页"""
        layout = QVBoxLayout(self.manager_page)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)
        
        title_layout = QHBoxLayout()
        title_label = QLabel("壁纸收藏夹")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #333;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        
        self.favorite_filter = QCheckBox("只显示喜爱")
        self.favorite_filter.stateChanged.connect(self.filter_wallpapers)
        filter_layout.addWidget(self.favorite_filter)
        
        filter_layout.addStretch()
        
        self.refresh_manager_button = QPushButton("刷新列表")
        self.refresh_manager_button.setStyleSheet("""
            QPushButton { 
                background-color: #2196f3; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                font-size: 10pt; 
                font-weight: 600;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #1976d2; }
            QPushButton:pressed { background-color: #1565c0; }
        """)
        self.refresh_manager_button.setCursor(Qt.PointingHandCursor)
        self.refresh_manager_button.clicked.connect(self.load_wallpaper_manager)
        filter_layout.addWidget(self.refresh_manager_button)
        
        self.batch_delete_button = QPushButton("批量删除")
        self.batch_delete_button.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white; 
                border: none; 
                border-radius: 6px; 
                font-size: 10pt; 
                font-weight: 600;
                padding: 10px 20px;
            }
            QPushButton:hover { background-color: #e53935; }
            QPushButton:pressed { background-color: #d32f2f; }
        """)
        self.batch_delete_button.setCursor(Qt.PointingHandCursor)
        self.batch_delete_button.clicked.connect(self.batch_delete)
        filter_layout.addWidget(self.batch_delete_button)
        
        layout.addLayout(filter_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: transparent; }")
        
        self.wallpaper_container = QWidget()
        self.wallpaper_container.setStyleSheet("background-color: transparent;")
        self.wallpaper_layout = QVBoxLayout(self.wallpaper_container)
        self.wallpaper_layout.setSpacing(20)
        self.wallpaper_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.wallpaper_container)
        layout.addWidget(self.scroll_area)
        
        QTimer.singleShot(200, self.load_wallpaper_manager)
    
    def init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(QApplication.style().standardIcon(QStyle.SP_DesktopIcon))
        
        tray_menu = QMenu()
        
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        next_action = QAction("下一张壁纸", self)
        next_action.triggered.connect(self.auto_change_wallpaper)
        tray_menu.addAction(next_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
    
    def _show_loading_animation(self):
        self.preview_label.setText("正在加载...")
        self.preview_label.setStyleSheet("""
            background-color: #fafafa; 
            border-radius: 8px; 
            color: #9e9e9e; 
            font-size: 12pt;
        """)
    
    def _load_preview_image(self, wallpaper):
        if not wallpaper:
            self.preview_label.setText("无壁纸数据")
            return False
        
        wallpaper_path = self.wallpaper_manager.download_wallpaper(wallpaper)
        preview_path = os.path.abspath(self.wallpaper_manager.get_preview_path(wallpaper))
        
        if wallpaper_path and os.path.exists(wallpaper_path):
            if not os.path.exists(preview_path):
                self.wallpaper_manager._generate_preview(wallpaper, wallpaper_path)
        
        label_size = self.preview_label.size()
        if label_size.width() < 100 or label_size.height() < 100:
            label_size = QSize(400, 250)
        
        loaded = False
        load_path = None
        
        if os.path.exists(preview_path):
            load_path = preview_path
        elif wallpaper_path and os.path.exists(wallpaper_path):
            load_path = wallpaper_path
        
        if load_path:
            pixmap = load_image_with_pil(load_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    label_size, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setStyleSheet("background-color: transparent; border-radius: 8px;")
                loaded = True
        
        if not loaded:
            self.preview_label.setText("预览图加载失败")
            self.preview_label.setStyleSheet("""
                background-color: #fff5f5; 
                border: 2px dashed #ffcdd2;
                border-radius: 8px; 
                color: #f44336; 
                font-size: 12pt;
            """)
        
        return loaded
    
    def load_wallpapers(self):
        if self.is_loading:
            return
        
        self.is_loading = True
        self._show_loading_animation()
        self.statusBar().showMessage("正在从Bing获取壁纸列表...")
        QApplication.processEvents()
        
        try:
            wallpapers = self.bing_api.get_wallpapers()
            
            if wallpapers:
                self.wallpapers_list = wallpapers
                self.current_wallpaper = wallpapers[0]
                self.current_wallpaper_index = 0
                
                self._load_preview_image(self.current_wallpaper)
                
                title = self.current_wallpaper.get('title', '未知标题')
                if title == 'Info':
                    title = 'Bing每日壁纸'
                copyright_info = self.current_wallpaper.get('copyright', '')
                info = f"📷 {title}\n\n🌍 {copyright_info}"
                self.info_label.setText(info)
                
                if self.wallpaper_manager.is_favorite(self.current_wallpaper):
                    self.favorite_button.setText("♥")
                else:
                    self.favorite_button.setText("♡")
                
                self.statusBar().showMessage(f"已加载 {len(wallpapers)} 张壁纸")
            else:
                self.preview_label.setText("无法获取壁纸，请检查网络连接")
                self.preview_label.setStyleSheet("""
                    background-color: #fff8e1; 
                    border: 2px dashed #ffe082;
                    border-radius: 8px; 
                    color: #f57c00; 
                    font-size: 12pt;
                """)
                self.statusBar().showMessage("获取壁纸失败")
        except Exception as e:
            self.preview_label.setText(f"加载出错: {str(e)}")
            self.statusBar().showMessage(f"加载失败: {str(e)}")
        finally:
            self.is_loading = False
    
    def refresh_wallpapers(self):
        self.refresh_button.setEnabled(False)
        self.load_wallpapers()
        QTimer.singleShot(1000, lambda: self.refresh_button.setEnabled(True))
    
    def set_as_wallpaper(self):
        if hasattr(self, 'current_wallpaper') and self.current_wallpaper:
            success = self.wallpaper_manager.set_wallpaper(self.current_wallpaper)
            if success:
                self.statusBar().showMessage("壁纸已成功设置")
                QMessageBox.information(self, "成功", "壁纸已设置为桌面背景！")
            else:
                self.statusBar().showMessage("设置壁纸失败")
                QMessageBox.warning(self, "失败", "无法设置壁纸，请重试")
        else:
            QMessageBox.warning(self, "警告", "请先加载壁纸")
    
    def download_wallpaper(self):
        if hasattr(self, 'current_wallpaper') and self.current_wallpaper:
            self.statusBar().showMessage("正在下载壁纸...")
            QApplication.processEvents()
            path = self.wallpaper_manager.download_wallpaper(self.current_wallpaper)
            if path:
                self.statusBar().showMessage(f"壁纸已下载")
                QMessageBox.information(self, "下载成功", f"壁纸已保存到:\n{path}")
            else:
                self.statusBar().showMessage("下载失败")
                QMessageBox.warning(self, "下载失败", "无法下载壁纸，请检查网络连接")
        else:
            QMessageBox.warning(self, "警告", "请先加载壁纸")
    
    def toggle_favorite(self):
        if hasattr(self, 'current_wallpaper') and self.current_wallpaper:
            if self.wallpaper_manager.is_favorite(self.current_wallpaper):
                self.wallpaper_manager.remove_favorite(self.current_wallpaper)
                self.favorite_button.setText("♡")
                self.statusBar().showMessage("已取消收藏")
            else:
                self.wallpaper_manager.add_favorite(self.current_wallpaper)
                self.favorite_button.setText("♥")
                self.statusBar().showMessage("已添加收藏")
        else:
            QMessageBox.warning(self, "警告", "请先加载壁纸")
    
    def display_preview(self, wallpaper):
        if not wallpaper:
            return
        
        self._show_loading_animation()
        QApplication.processEvents()
        
        self._load_preview_image(wallpaper)
        
        title = wallpaper.get('title', '未知标题')
        if title == 'Info':
            title = 'Bing每日壁纸'
        copyright_info = wallpaper.get('copyright', '')
        info = f"📷 {title}\n\n🌍 {copyright_info}"
        self.info_label.setText(info)
        
        if self.wallpaper_manager.is_favorite(wallpaper):
            self.favorite_button.setText("♥")
        else:
            self.favorite_button.setText("♡")
    
    def prev_wallpaper(self):
        if not self.wallpapers_list:
            return
        
        self.current_wallpaper_index = (self.current_wallpaper_index - 1) % len(self.wallpapers_list)
        self.current_wallpaper = self.wallpapers_list[self.current_wallpaper_index]
        self.display_preview(self.current_wallpaper)
        self.statusBar().showMessage(f"第 {self.current_wallpaper_index + 1}/{len(self.wallpapers_list)} 张")
    
    def next_wallpaper(self):
        if not self.wallpapers_list:
            return
        
        self.current_wallpaper_index = (self.current_wallpaper_index + 1) % len(self.wallpapers_list)
        self.current_wallpaper = self.wallpapers_list[self.current_wallpaper_index]
        self.display_preview(self.current_wallpaper)
        self.statusBar().showMessage(f"第 {self.current_wallpaper_index + 1}/{len(self.wallpapers_list)} 张")
    
    def browse_cache_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择缓存目录", self.dir_edit.text())
        if dir_path:
            self.dir_edit.setText(os.path.abspath(dir_path))
    
    def save_config(self):
        interval_index = self.interval_combo.currentIndex()
        if interval_index == 0:
            self.config.set("auto_change_interval", 900)
        elif interval_index == 1:
            self.config.set("auto_change_interval", 1800)
        elif interval_index == 2:
            self.config.set("auto_change_interval", 3600)
        else:
            custom_interval = self.custom_spin.value()
            self.config.set("auto_change_interval", custom_interval)
            self.config.set("custom_interval", custom_interval)
        
        mode_index = self.mode_combo.currentIndex()
        if mode_index == 0:
            self.config.set("change_mode", "random")
        elif mode_index == 1:
            self.config.set("change_mode", "favorite")
        else:
            self.config.set("change_mode", "sequence")
        
        self.config.set("wallpaper_dir", self.dir_edit.text())
        
        self.start_auto_change_timer()
        
        self.statusBar().showMessage("配置已保存")
        QMessageBox.information(self, "保存成功", "设置已保存！")
    
    def clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                sub_layout = item.layout()
                if sub_layout:
                    self.clear_layout(sub_layout)
    
    def load_wallpaper_manager(self):
        self.statusBar().showMessage("正在加载壁纸列表...")
        
        self.clear_layout(self.wallpaper_layout)
        
        wallpaper_dir = os.path.abspath(self.config.get("wallpaper_dir"))
        wallpaper_files = []
        
        show_favorites_only = self.favorite_filter.isChecked()
        favorite_ids = {fav["id"] for fav in self.wallpaper_manager.favorites}
        
        if os.path.exists(wallpaper_dir):
            for file in os.listdir(wallpaper_dir):
                if file.endswith('.jpg'):
                    file_path = os.path.join(wallpaper_dir, file)
                    wallpaper_id = file.replace('.jpg', '')
                    
                    if show_favorites_only and wallpaper_id not in favorite_ids:
                        continue
                    
                    mod_time = os.path.getmtime(file_path)
                    wallpaper_files.append((file_path, mod_time))
        
        wallpaper_files.sort(key=lambda x: x[1], reverse=True)
        
        seen_files = set()
        unique_wallpaper_files = []
        for file_path, mod_time in wallpaper_files:
            if file_path not in seen_files:
                seen_files.add(file_path)
                unique_wallpaper_files.append((file_path, mod_time))
        
        if not unique_wallpaper_files:
            empty_label = QLabel("暂无壁纸，请在首页下载壁纸")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #9e9e9e; font-size: 12pt; padding: 50px;")
            self.wallpaper_layout.addWidget(empty_label)
            self.statusBar().showMessage("壁纸列表为空")
            return
        
        date_groups = {}
        for file_path, mod_time in unique_wallpaper_files:
            date_str = time.strftime('%Y-%m-%d', time.localtime(mod_time))
            if date_str not in date_groups:
                date_groups[date_str] = []
            date_groups[date_str].append((file_path, mod_time))
        
        for date_str, files in date_groups.items():
            date_label = QLabel(f"📅 {date_str}")
            date_label.setStyleSheet("""
                font-size: 12pt; 
                font-weight: bold; 
                color: #333; 
                padding: 10px 5px;
                background: transparent;
            """)
            self.wallpaper_layout.addWidget(date_label)
            
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(15)
            grid_layout.setContentsMargins(0, 0, 0, 0)
            
            for i, (file_path, mod_time) in enumerate(files):
                if 'previews' in file_path:
                    continue
                
                wallpaper_item = QFrame()
                wallpaper_item.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #e0e0e0;
                        border-radius: 12px;
                        padding: 10px;
                    }
                    QFrame:hover {
                        border-color: #2196f3;
                        background-color: #fafafa;
                    }
                """)
                item_layout = QVBoxLayout(wallpaper_item)
                item_layout.setSpacing(10)
                item_layout.setContentsMargins(8, 8, 8, 8)
                
                top_layout = QHBoxLayout()
                
                checkbox = QCheckBox()
                checkbox.setFixedSize(20, 20)
                checkbox.setObjectName(f"checkbox_{i}")
                top_layout.addWidget(checkbox)
                top_layout.addStretch()
                
                preview_path = os.path.abspath(os.path.join(os.path.dirname(file_path), 'previews', 
                                          os.path.basename(file_path).replace('.jpg', '_preview.jpg')))
                preview_label = QLabel()
                preview_label.setFixedSize(180, 112)
                preview_label.setAlignment(Qt.AlignCenter)
                preview_label.setStyleSheet("""
                    background-color: #f5f5f5; 
                    border-radius: 8px;
                """)
                
                preview_loaded = False
                load_path = None
                
                if os.path.exists(preview_path):
                    load_path = preview_path
                elif os.path.exists(file_path):
                    load_path = file_path
                
                if load_path:
                    pixmap = load_image_with_pil(load_path)
                    if not pixmap.isNull():
                        preview_label.setPixmap(pixmap.scaled(
                            preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                        ))
                        preview_loaded = True
                
                if not preview_loaded:
                    preview_label.setText("无预览")
                    preview_label.setStyleSheet("""
                        background-color: #f5f5f5; 
                        border-radius: 8px;
                        color: #9e9e9e;
                    """)
                
                item_layout.addWidget(preview_label)
                
                file_name = os.path.basename(file_path)
                name_label = QLabel(file_name[:25] + '...' if len(file_name) > 25 else file_name)
                name_label.setAlignment(Qt.AlignCenter)
                name_label.setStyleSheet("font-size: 9pt; color: #666; background: transparent;")
                item_layout.addWidget(name_label)
                
                button_layout = QHBoxLayout()
                button_layout.setSpacing(8)
                
                wallpaper_id = file_name.replace('.jpg', '')
                is_fav = wallpaper_id in favorite_ids
                fav_button = QPushButton("♥" if is_fav else "♡")
                fav_button.setFixedSize(36, 36)
                fav_button.setStyleSheet("""
                    QPushButton { 
                        background-color: #fff0f0; 
                        color: #e53935; 
                        border: 2px solid #ffcdd2; 
                        border-radius: 18px; 
                        font-size: 14pt;
                        padding: 0px;
                    }
                    QPushButton:hover { 
                        background-color: #ffebee; 
                        border-color: #e53935; 
                    }
                """)
                fav_button.setCursor(Qt.PointingHandCursor)
                fav_button.setToolTip("取消收藏" if is_fav else "添加收藏")
                fav_button.clicked.connect(lambda checked, wid=wallpaper_id, btn=fav_button: self.toggle_favorite_by_id(wid, btn))
                button_layout.addWidget(fav_button)
                
                set_button = QPushButton("设为壁纸")
                set_button.setStyleSheet("""
                    QPushButton { 
                        background-color: #4caf50; 
                        color: white; 
                        border: none; 
                        border-radius: 6px; 
                        font-size: 9pt; 
                        font-weight: 600;
                        padding: 8px 12px;
                    }
                    QPushButton:hover { background-color: #43a047; }
                    QPushButton:pressed { background-color: #388e3c; }
                """)
                set_button.setCursor(Qt.PointingHandCursor)
                set_button.clicked.connect(lambda checked, path=file_path: self.set_wallpaper_from_path(path))
                button_layout.addWidget(set_button)
                
                delete_button = QPushButton("删除")
                delete_button.setStyleSheet("""
                    QPushButton { 
                        background-color: #ff5252; 
                        color: white; 
                        border: none; 
                        border-radius: 6px; 
                        font-size: 9pt; 
                        font-weight: 600;
                        padding: 8px 12px;
                    }
                    QPushButton:hover { background-color: #ff1744; }
                    QPushButton:pressed { background-color: #d50000; }
                """)
                delete_button.setCursor(Qt.PointingHandCursor)
                delete_button.clicked.connect(lambda checked, path=file_path: self.delete_wallpaper_from_path(path))
                button_layout.addWidget(delete_button)
                
                item_layout.addLayout(button_layout)
                
                wallpaper_item.setProperty("file_path", file_path)
                
                row = i // 3
                col = i % 3
                grid_layout.addWidget(wallpaper_item, row, col)
            
            self.wallpaper_layout.addWidget(grid_widget)
        
        self.statusBar().showMessage(f"已加载 {len(unique_wallpaper_files)} 张壁纸")
    
    def set_wallpaper_from_path(self, path):
        file_name = os.path.basename(path)
        
        import platform
        if platform.system() == 'Windows':
            import ctypes
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, path, 3)
            self.statusBar().showMessage("壁纸已设置成功")
            QMessageBox.information(self, "成功", "壁纸已设置为桌面背景！")
        else:
            self.statusBar().showMessage(f"壁纸路径: {path}")
    
    def delete_wallpaper_from_path(self, path):
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除这张壁纸吗？\n{os.path.basename(path)}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(path):
                    os.remove(path)
                
                preview_path = os.path.join(os.path.dirname(path), 'previews', 
                                          os.path.basename(path).replace('.jpg', '_preview.jpg'))
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                
                self.load_wallpaper_manager()
                self.statusBar().showMessage("壁纸已删除")
            except Exception as e:
                self.statusBar().showMessage(f"删除失败: {e}")
    
    def toggle_favorite_by_id(self, wallpaper_id, button):
        for fav in self.wallpaper_manager.favorites:
            if fav["id"] == wallpaper_id:
                self.wallpaper_manager.remove_favorite(fav)
                button.setText("♡")
                button.setToolTip("添加收藏")
                self.statusBar().showMessage("已取消收藏")
                return
        
        wallpaper = {
            'id': wallpaper_id,
            'title': wallpaper_id,
            'url': '',
            'copyright': ''
        }
        self.wallpaper_manager.add_favorite(wallpaper)
        button.setText("♥")
        button.setToolTip("取消收藏")
        self.statusBar().showMessage("已添加收藏")
    
    def filter_wallpapers(self):
        self.load_wallpaper_manager()
    
    def batch_delete(self):
        selected_wallpapers = []
        
        for i in range(self.wallpaper_layout.count()):
            item = self.wallpaper_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QWidget):
                grid_widget = item.widget()
                grid_layout = grid_widget.layout()
                if grid_layout:
                    for j in range(grid_layout.count()):
                        wallpaper_item = grid_layout.itemAt(j).widget()
                        if wallpaper_item:
                            for k in range(wallpaper_item.layout().count()):
                                layout_item = wallpaper_item.layout().itemAt(k)
                                if layout_item and layout_item.layout():
                                    for l in range(layout_item.layout().count()):
                                        widget = layout_item.layout().itemAt(l).widget()
                                        if isinstance(widget, QCheckBox) and widget.isChecked():
                                            file_path = wallpaper_item.property("file_path")
                                            if file_path:
                                                selected_wallpapers.append(file_path)
        
        if not selected_wallpapers:
            QMessageBox.warning(self, "提示", "请先选择要删除的壁纸")
            return
        
        reply = QMessageBox.question(
            self, "确认批量删除", f"确定要删除选中的 {len(selected_wallpapers)} 张壁纸吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            for file_path in selected_wallpapers:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    preview_path = os.path.join(os.path.dirname(file_path), 'previews', 
                                              os.path.basename(file_path).replace('.jpg', '_preview.jpg'))
                    if os.path.exists(preview_path):
                        os.remove(preview_path)
                    
                    deleted_count += 1
                except Exception as e:
                    self.statusBar().showMessage(f"删除失败: {e}")
            
            self.load_wallpaper_manager()
            self.statusBar().showMessage(f"已删除 {deleted_count} 张壁纸")
            QMessageBox.information(self, "删除完成", f"已成功删除 {deleted_count} 张壁纸")
    
    def auto_change_wallpaper(self):
        change_mode = self.config.get("change_mode", "random")
        
        if change_mode == "favorite":
            if self.wallpaper_manager.favorites:
                import random
                wallpaper = random.choice(self.wallpaper_manager.favorites)
                self.wallpaper_manager.set_wallpaper(wallpaper)
                self.statusBar().showMessage("已从收藏壁纸中切换")
            else:
                self.statusBar().showMessage("没有收藏的壁纸")
        elif change_mode == "sequence":
            wallpapers = self.bing_api.get_wallpapers()
            if wallpapers:
                if hasattr(self, 'current_sequence_index'):
                    self.current_sequence_index = (self.current_sequence_index + 1) % len(wallpapers)
                else:
                    self.current_sequence_index = 0
                wallpaper = wallpapers[self.current_sequence_index]
                self.wallpaper_manager.set_wallpaper(wallpaper)
                self.statusBar().showMessage("已按顺序切换壁纸")
        else:
            wallpapers = self.bing_api.get_wallpapers()
            if wallpapers:
                import random
                wallpaper = random.choice(wallpapers)
                self.wallpaper_manager.set_wallpaper(wallpaper)
                self.statusBar().showMessage("已随机切换壁纸")
    
    def start_auto_change_timer(self):
        if hasattr(self, 'auto_timer') and self.auto_timer:
            self.auto_timer.stop()
        
        interval = self.config.get('auto_change_interval', 3600)
        self.auto_timer = QTimer(self)
        self.auto_timer.timeout.connect(self.auto_change_wallpaper)
        self.auto_timer.start(interval * 1000)
        print(f"自动切换定时器已启动，间隔: {interval} 秒", flush=True)
    
    def closeEvent(self, event):
        msg = QMessageBox(self)
        msg.setWindowTitle('提示')
        msg.setText('程序将在后台继续运行，请选择：')
        msg.addButton('最小化到托盘', QMessageBox.AcceptRole)
        msg.addButton('直接退出', QMessageBox.RejectRole)
        msg.addButton('取消', QMessageBox.ActionRole)
        msg.exec_()
        clicked_button = msg.clickedButton().text()
        if clicked_button == '最小化到托盘':
            self.hide()
            event.ignore()
        elif clicked_button == '直接退出':
            QApplication.quit()
        else:
            event.ignore()
