"""百度贴吧热搜数据模型。

提供百度贴吧热门话题数据的模型类。
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import json


@dataclass
class BaiduTiebaHotTopicItem:
    """百度贴吧热门话题条目。"""

    item_key: str
    id: str
    name: str  # 标题
    desc: str  # 描述
    discuss_num: int  # 讨论数
    image: str  # 图片地址
    topic_tag: int  # 话题标签
    is_video_topic: str  # 是否视频话题

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaiduTiebaHotTopicItem":
        """从字典创建实例。"""
        return cls(
            item_key=data.get("item_key", ""),
            id=data.get("id", ""),
            name=data.get("name", ""),
            desc=data.get("desc", ""),
            discuss_num=int(data.get("discuss_num", 0)),
            image=data.get("image", ""),
            topic_tag=int(data.get("topic_tag", 0)),
            is_video_topic=data.get("is_video_topic", "0"),
        )


@dataclass
class BaiduTiebaHotTopics:
    """百度贴吧热门话题列表。"""

    items: List[BaiduTiebaHotTopicItem]
    last_list_time: int
    next_refresh_time: int
    version: int
    current_page: int
    total_page: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaiduTiebaHotTopics":
        """从API响应字典创建实例。"""
        if "data" not in data:
            return cls([], 0, 0, 0, 0, 0)

        api_data = data["data"]

        # 解析list字段（JSON字符串）
        list_str = api_data.get("list", "[]")
        try:
            items_raw = json.loads(list_str)
            items = [BaiduTiebaHotTopicItem.from_dict(item) for item in items_raw]
        except json.JSONDecodeError:
            items = []

        return cls(
            items=items,
            last_list_time=api_data.get("last_list_time", 0),
            next_refresh_time=api_data.get("next_refresh_time", 0),
            version=api_data.get("version", 0),
            current_page=api_data.get("current_page", 0),
            total_page=api_data.get("total_page", 0),
        )
