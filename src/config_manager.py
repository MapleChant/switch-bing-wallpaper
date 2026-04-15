#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器模块
"""

import os
import json

class ConfigManager:
    def __init__(self):
        self.config_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))
        self.default_config = {
            "auto_change_interval": 3600,
            "change_mode": "random",
            "wallpaper_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "wallpapers")),
            "custom_interval": 3600,
            "download_quality": "high",
            "max_wallpapers": 50,
            "startup_with_windows": False
        }
        
        # 加载配置
        self.config = self._load_config()
    
    def _load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    if "wallpaper_dir" in config and not os.path.isabs(config["wallpaper_dir"]):
                        config["wallpaper_dir"] = os.path.abspath(config["wallpaper_dir"])
                    return config
        except Exception as e:
            print(f"加载配置失败: {e}")
        
        return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置值"""
        self.config[key] = value
        return self.save_config()
