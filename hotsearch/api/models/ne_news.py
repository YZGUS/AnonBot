"""网易新闻数据模型。

提供网易新闻热榜数据的模型类。
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class NetEaseNewsHotSearchItem:
    """网易新闻热搜条目数据结构"""

    item_key: str  # 条目唯一标识
    title: str  # 热搜标题
    www_url: str  # 链接地址
    source: Optional[str] = None  # 来源
    img: Optional[str] = None  # 图片URL
    reply_count: Optional[int] = None  # 回复数
    hot_score: Optional[int] = None  # 热度分数
    hot_comment: Optional[str] = None  # 热门评论
    is_video: Optional[bool] = None  # 是否视频
    duration_str: Optional[str] = None  # 视频时长

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetEaseNewsHotSearchItem":
        """从字典创建对象"""
        return cls(
            item_key=data.get("item_key", ""),
            title=data.get("title", ""),
            www_url=data.get("www_url", ""),
            source=data.get("source", None),
            img=data.get("img", None),
            reply_count=data.get("reply_count", None),
            hot_score=data.get("hot_score", None),
            hot_comment=data.get("hot_comment", None),
            is_video=data.get("is_video", None),
            duration_str=data.get("duration_str", None),
        )


@dataclass
class NetEaseNewsHotSearchResponse:
    """网易新闻热搜响应数据结构"""

    items: List[NetEaseNewsHotSearchItem]  # 热搜条目列表
    platform: str  # 平台名称
    category: str  # 分类
    page: int  # 页码
    last_list_time: Optional[int] = None  # 上次列表时间
    next_refresh_time: Optional[int] = None  # 下次刷新时间
    version: Optional[int] = None  # 版本
    total_page: Optional[int] = None  # 总页数

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], sub_tab: str
    ) -> "NetEaseNewsHotSearchResponse":
        """从字典创建对象"""
        api_data = data.get("data", {})

        # 解析items列表，items实际上是一个JSON字符串
        items_list = []
        list_str = api_data.get("list", "[]")
        try:
            items_raw = json.loads(list_str)
            items_list = [
                NetEaseNewsHotSearchItem.from_dict(item) for item in items_raw
            ]
        except json.JSONDecodeError:
            items_list = []

        return cls(
            items=items_list,
            platform="ne-news",
            category=sub_tab,
            page=api_data.get("current_page", 1),
            last_list_time=api_data.get("last_list_time"),
            next_refresh_time=api_data.get("next_refresh_time"),
            version=api_data.get("version"),
            total_page=api_data.get("total_page"),
        )
