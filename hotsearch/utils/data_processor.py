"""数据处理工具。

提供分析和处理热榜数据的工具函数。
"""

import json
import os
from typing import Dict, List, Any, Optional, Union


class HotSearchDataProcessor:
    """热榜数据处理器。"""
    
    def __init__(self, data_dir: str = "./data"):
        """初始化数据处理器。
        
        Args:
            data_dir: 数据保存目录
        """
        self.data_dir = data_dir
        
    def load_data(self, tab: str, sub_tab: str) -> Dict[str, Any]:
        """加载保存的数据。
        
        Args:
            tab: 热榜分类
            sub_tab: 热榜子分类
            
        Returns:
            Dict[str, Any]: 加载的数据
            
        Raises:
            FileNotFoundError: 数据文件不存在
        """
        filepath = os.path.join(self.data_dir, tab, f"{sub_tab}.json")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"数据文件不存在: {filepath}")
            
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def analyze_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析数据结构。
        
        Args:
            data: 待分析的数据
            
        Returns:
            Dict[str, Any]: 数据结构分析结果
        """
        result = {}
        
        # 分析顶层结构
        result["top_level_keys"] = list(data.keys())
        
        # 分析items结构（如果存在）
        if "data" in data and "items" in data["data"]:
            items = data["data"]["items"]
            if items and len(items) > 0:
                first_item = items[0]
                result["item_keys"] = list(first_item.keys())
                result["item_example"] = first_item
                
        return result
        
    def extract_items(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取热榜条目。
        
        Args:
            data: 原始数据
            
        Returns:
            List[Dict[str, Any]]: 提取的热榜条目列表
        """
        if "data" in data and "items" in data["data"]:
            return data["data"]["items"]
        return []