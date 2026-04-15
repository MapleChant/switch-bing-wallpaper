#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
壁纸管理器模块
"""

import os
import requests
import json
import ctypes
from src.config_manager import ConfigManager

class WallpaperManager:
    def __init__(self):
        self.config = ConfigManager()
        self.wallpaper_dir = os.path.abspath(self.config.get("wallpaper_dir", os.path.join(os.path.dirname(__file__), "..", "wallpapers")))
        self.preview_dir = os.path.join(self.wallpaper_dir, "previews")
        self.favorites_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "cache", "favorites.json"))
        
        # 确保目录存在
        os.makedirs(self.wallpaper_dir, exist_ok=True)
        os.makedirs(self.preview_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.favorites_file), exist_ok=True)
        
        # 加载喜欢的壁纸
        self.favorites = self._load_favorites()
    
    def get_wallpaper_path(self, wallpaper):
        """获取壁纸保存路径"""
        wallpaper_id = wallpaper["id"]
        return os.path.join(self.wallpaper_dir, f"{wallpaper_id}.jpg")
    
    def get_preview_path(self, wallpaper):
        """获取预览图路径"""
        wallpaper_id = wallpaper["id"]
        return os.path.join(self.preview_dir, f"{wallpaper_id}_preview.jpg")
    
    def download_wallpaper(self, wallpaper):
        """下载壁纸"""
        wallpaper_path = self.get_wallpaper_path(wallpaper)
        preview_path = self.get_preview_path(wallpaper)
        
        if os.path.exists(wallpaper_path):
            if not os.path.exists(preview_path):
                self._generate_preview(wallpaper, wallpaper_path)
            return wallpaper_path
        
        try:
            response = requests.get(wallpaper["url"], timeout=30)
            response.raise_for_status()
            
            with open(wallpaper_path, "wb") as f:
                f.write(response.content)
            
            self._generate_preview(wallpaper, wallpaper_path)
            
            return wallpaper_path
            
        except Exception as e:
            print(f"下载壁纸失败: {e}")
            return None
    
    def _generate_preview(self, wallpaper, wallpaper_path):
        try:
            preview_path = self.get_preview_path(wallpaper)
            
            from PIL import Image
            with Image.open(wallpaper_path) as img:
                max_width = 400
                max_height = 250
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                img.save(preview_path, "JPEG", quality=85)
            
        except Exception as e:
            print(f"生成预览图失败: {e}")
            try:
                import shutil
                shutil.copy2(wallpaper_path, preview_path)
            except:
                pass
    
    def set_wallpaper(self, wallpaper):
        wallpaper_path = self.get_wallpaper_path(wallpaper)
        
        if os.path.exists(wallpaper_path):
            import platform
            if platform.system() == 'Windows':
                SPI_SETDESKWALLPAPER = 20
                ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, wallpaper_path, 3)
            else:
                print(f"在Linux环境中，壁纸路径: {wallpaper_path}")
            return True
        
        if wallpaper.get("url"):
            downloaded_path = self.download_wallpaper(wallpaper)
            if downloaded_path and os.path.exists(downloaded_path):
                import platform
                if platform.system() == 'Windows':
                    SPI_SETDESKWALLPAPER = 20
                    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, downloaded_path, 3)
                else:
                    print(f"在Linux环境中，壁纸已下载到: {downloaded_path}")
                return True
        
        return False
    
    def add_favorite(self, wallpaper):
        """添加到喜欢"""
        wallpaper_id = wallpaper["id"]
        
        # 检查是否已在喜欢列表中
        if wallpaper_id not in [fav["id"] for fav in self.favorites]:
            self.favorites.append(wallpaper)
            self._save_favorites()
            return True
        
        return False
    
    def remove_favorite(self, wallpaper):
        """从喜欢中移除"""
        wallpaper_id = wallpaper["id"]
        
        # 查找并移除
        new_favorites = [fav for fav in self.favorites if fav["id"] != wallpaper_id]
        if len(new_favorites) != len(self.favorites):
            self.favorites = new_favorites
            self._save_favorites()
            return True
        
        return False
    
    def is_favorite(self, wallpaper):
        """检查是否已喜欢"""
        wallpaper_id = wallpaper["id"]
        return any(fav["id"] == wallpaper_id for fav in self.favorites)
    
    def delete_wallpaper(self, wallpaper):
        """删除壁纸"""
        # 删除壁纸文件
        wallpaper_path = self.get_wallpaper_path(wallpaper)
        if os.path.exists(wallpaper_path):
            os.remove(wallpaper_path)
        
        # 删除预览图
        preview_path = self.get_preview_path(wallpaper)
        if os.path.exists(preview_path):
            os.remove(preview_path)
        
        # 从喜欢列表中移除
        self.remove_favorite(wallpaper)
        
        return True
    
    def _load_favorites(self):
        """加载喜欢的壁纸"""
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载喜欢列表失败: {e}")
        return []
    
    def _save_favorites(self):
        """保存喜欢的壁纸"""
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存喜欢列表失败: {e}")
