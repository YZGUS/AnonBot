"""百度热搜数据模型。

提供百度热搜数据的模型类。
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class BaiduHotSearchItem:
    """百度热搜条目数据结构"""

    item_key: str
    word: str
    desc: str
    query: str
    hot_score: Optional[str] = None
    hot_tag: Optional[str] = None
    hot_change: Optional[str] = None
    img: Optional[str] = None
    expression: Optional[str] = None
    show: Optional[List[Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaiduHotSearchItem":
        """从字典创建对象

        Args:
            data: 数据字典

        Returns:
            BaiduHotSearchItem: 热搜条目对象
        """
        return cls(
            item_key=data.get("item_key", ""),
            word=data.get("word", ""),
            desc=data.get("desc", ""),
            query=data.get("query", ""),
            hot_score=data.get("hot_score"),
            hot_tag=data.get("hot_tag"),
            hot_change=data.get("hot_change"),
            img=data.get("img"),
            expression=data.get("expression"),
            show=data.get("show", []),
        )


@dataclass
class BaiduHotSearchResponse:
    """百度热搜响应数据结构"""

    items: List[BaiduHotSearchItem]
    tab: str
    sub_tab: str
    page: int
    last_list_time: Optional[int] = None
    next_refresh_time: Optional[int] = None
    version: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaiduHotSearchResponse":
        """从字典创建对象

        Args:
            data: API响应数据

        Returns:
            BaiduHotSearchResponse: 热搜响应对象
        """
        api_data = data.get("data", {})

        # 解析items列表，items实际上是一个JSON字符串
        items_list = []
        list_str = api_data.get("list", "[]")
        try:
            items_raw = json.loads(list_str)
            items_list = [BaiduHotSearchItem.from_dict(item) for item in items_raw]
        except json.JSONDecodeError:
            items_list = []

        # 构建响应对象
        return cls(
            items=items_list,
            tab="baidu",  # 固定为baidu
            sub_tab=api_data.get("sub_tab", ""),
            page=api_data.get("current_page", 1),
            last_list_time=api_data.get("last_list_time"),
            next_refresh_time=api_data.get("next_refresh_time"),
            version=api_data.get("version"),
        )
