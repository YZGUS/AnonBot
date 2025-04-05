"""腾讯新闻数据模型。

提供腾讯新闻热榜数据的模型类。
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class TencentNewsHotSearchItem:
    """腾讯新闻热搜条目数据结构"""

    item_key: str  # 条目唯一标识
    title: str  # 热搜标题
    www_url: str  # 链接地址
    desc: Optional[str] = None  # 描述
    img: Optional[str] = None  # 图片URL
    is_video: Optional[bool] = None  # 是否是视频
    hot_score: Optional[int] = None  # 热度分数
    comment_num: Optional[int] = None  # 评论数
    like_num: Optional[int] = None  # 点赞数

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TencentNewsHotSearchItem":
        """从字典创建对象"""
        return cls(
            item_key=data.get("item_key", ""),
            title=data.get("title", ""),
            www_url=data.get("www_url", ""),
            desc=data.get("desc"),
            img=data.get("img"),
            is_video=data.get("is_video"),
            hot_score=data.get("hot_score"),
            comment_num=data.get("comment_num"),
            like_num=data.get("like_num"),
        )


@dataclass
class TencentNewsHotSearchResponse:
    """腾讯新闻热搜响应数据结构"""

    items: List[TencentNewsHotSearchItem]  # 热搜条目列表
    platform: str  # 平台
    category: str  # 分类
    page: int  # 页码
    last_list_time: Optional[int] = None  # 上次更新时间
    next_refresh_time: Optional[int] = None  # 下次更新时间
    version: Optional[int] = None  # 版本
    total_page: Optional[int] = None  # 总页数

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], sub_tab: str
    ) -> "TencentNewsHotSearchResponse":
        """从字典创建对象"""
        api_data = data.get("data", {})
        items_list = []

        # 从list字段中获取JSON字符串并解析
        list_str = api_data.get("list", "[]")
        try:
            items_raw = json.loads(list_str)
            items_list = [
                TencentNewsHotSearchItem.from_dict(item) for item in items_raw
            ]
        except json.JSONDecodeError:
            items_list = []

        return cls(
            items=items_list,
            platform="tencent-news",
            category=sub_tab,
            page=api_data.get("current_page", 1),
            last_list_time=api_data.get("last_list_time"),
            next_refresh_time=api_data.get("next_refresh_time"),
            version=api_data.get("version"),
            total_page=api_data.get("total_page"),
        )
