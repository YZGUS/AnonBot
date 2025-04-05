"""百度贴吧客户端。

提供获取百度贴吧热门话题数据的客户端。
"""

from typing import Dict, Any, List, Union, Optional

from ..client import HotSearchClient
from .models import BaiduTiebaHotTopics, BaiduTiebaHotTopicItem


class BaiduTiebaClient(HotSearchClient):
    """百度贴吧客户端。"""

    def __init__(self, **kwargs):
        """初始化百度贴吧客户端。"""
        super().__init__(**kwargs)

    def get_hot_topics(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BaiduTiebaHotTopics]:
        """获取热门话题。

        Args:
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            Union[Dict[str, Any], BaiduTiebaHotTopics]:
                如果as_model为True，返回BaiduTiebaHotTopics对象；
                否则返回API响应的JSON数据
        """
        data = self.request(tab="baidu-tieba", sub_tab="topic", page=page)
        if as_model:
            return BaiduTiebaHotTopics.from_dict(data)
        return data

    def get_items(
        self, page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[BaiduTiebaHotTopicItem]]:
        """获取热门话题条目。

        Args:
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            Union[List[Dict[str, Any]], List[BaiduTiebaHotTopicItem]]:
                如果as_model为True，返回BaiduTiebaHotTopicItem对象列表；
                否则返回原始条目列表
        """
        if as_model:
            response = self.get_hot_topics(page=page, as_model=True)
            return response.items

        data = self.request(tab="baidu-tieba", sub_tab="topic", page=page)
        if "data" in data and "list" in data["data"]:
            import json

            try:
                return json.loads(data["data"]["list"])
            except (json.JSONDecodeError, TypeError):
                return []
        return []
