"""今日头条热搜数据模型。"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ToutiaoHotSearchItem:
    """今日头条热搜条目模型。"""

    item_key: str
    title: str
    www_url: str
    label: str
    hot_value: str

    @property
    def hot_value_int(self) -> int:
        """获取热度值整数。"""
        try:
            return int(self.hot_value)
        except (ValueError, TypeError):
            return 0

    @property
    def label_name(self) -> str:
        """获取标签名称。"""
        labels = {
            "boom": "爆",
            "hot": "热",
            "new": "新",
            "refuteRumors": "辟谣",
            "interpretation": "解读",
        }
        return labels.get(self.label, "")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToutiaoHotSearchItem":
        """从字典创建热搜条目模型。

        Args:
            data: 字典数据

        Returns:
            ToutiaoHotSearchItem: 热搜条目模型
        """
        if not data or not isinstance(data, dict):
            return cls("", "", "", "", "0")

        return cls(
            item_key=data.get("item_key", "") or "",
            title=data.get("title", "") or "",
            www_url=data.get("www_url", "") or "",
            label=data.get("label", "") or "",
            hot_value=data.get("hot_value", "0") or "0",
        )


@dataclass
class ToutiaoHotTopics:
    """今日头条热搜话题模型。"""

    items: List[ToutiaoHotSearchItem]
    last_list_time: int
    next_refresh_time: int
    version: int
    current_page: int
    total_page: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToutiaoHotTopics":
        """从字典创建热搜话题模型。

        Args:
            data: 字典数据

        Returns:
            ToutiaoHotTopics: 热搜话题模型
        """
        if not data or not isinstance(data, dict):
            return cls([], 0, 0, 0, 0, 0)

        if "data" not in data:
            return cls([], 0, 0, 0, 0, 0)

        api_data = data["data"]

        # 处理列表数据（可能是JSON字符串）
        list_data = api_data.get("list", [])
        if isinstance(list_data, str):
            try:
                list_data = json.loads(list_data)
            except json.JSONDecodeError:
                list_data = []

        if not isinstance(list_data, list):
            list_data = []

        items = [ToutiaoHotSearchItem.from_dict(item) for item in list_data]

        return cls(
            items=items,
            last_list_time=api_data.get("last_list_time", 0) or 0,
            next_refresh_time=api_data.get("next_refresh_time", 0) or 0,
            version=api_data.get("version", 0) or 0,
            current_page=api_data.get("current_page", 0) or 0,
            total_page=api_data.get("total_page", 0) or 0,
        )
