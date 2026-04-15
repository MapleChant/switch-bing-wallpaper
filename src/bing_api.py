#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bing壁纸API调用模块
"""

import requests
import json
import os
from src.config_manager import ConfigManager

class BingAPI:
    def __init__(self):
        self.config = ConfigManager()
        self.api_url = "https://www.bing.com/HPImageArchive.aspx"
        self.cache_file = os.path.join(os.path.dirname(__file__), "..", "cache", "wallpapers.json")
        
        # 确保缓存目录存在
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
    
    def get_wallpapers(self, n=8):
        """获取Bing壁纸列表"""
        params = {
            "format": "js",
            "idx": 0,
            "n": n
        }
        
        try:
            # 调用API
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            
            # 解析响应
            data = response.json()
            wallpapers = data.get("images", [])
            
            # 处理壁纸数据
            processed_wallpapers = []
            for wallpaper in wallpapers:
                # 构建完整的壁纸URL
                base_url = "https://www.bing.com"
                wallpaper_url = base_url + wallpaper["url"]
                
                # 生成唯一ID
                wallpaper_id = wallpaper["hsh"]
                
                # 构建壁纸信息
                processed_wallpaper = {
                    "id": wallpaper_id,
                    "title": wallpaper.get("title", ""),
                    "copyright": wallpaper.get("copyright", ""),
                    "url": wallpaper_url,
                    "urlbase": wallpaper.get("urlbase", ""),
                    "startdate": wallpaper.get("startdate", ""),
                    "enddate": wallpaper.get("enddate", "")
                }
                processed_wallpapers.append(processed_wallpaper)
            
            # 去重
            processed_wallpapers = self._remove_duplicates(processed_wallpapers)
            
            # 保存到缓存
            self._save_to_cache(processed_wallpapers)
            
            return processed_wallpapers
            
        except Exception as e:
            print(f"获取壁纸失败: {e}")
            # 从缓存加载
            return self._load_from_cache()
    
    def _remove_duplicates(self, wallpapers):
        """去重壁纸"""
        seen = set()
        unique_wallpapers = []
        
        for wallpaper in wallpapers:
            if wallpaper["id"] not in seen:
                seen.add(wallpaper["id"])
                unique_wallpapers.append(wallpaper)
        
        return unique_wallpapers
    
    def _save_to_cache(self, wallpapers):
        """保存到缓存"""
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(wallpapers, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def _load_from_cache(self):
        """从缓存加载"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载缓存失败: {e}")
        return []
