"""网易新闻客户端。

提供获取网易新闻热榜数据的客户端。
"""

from typing import Dict, Any, List, Union
import json

from ..client import HotSearchClient
from .models.ne_news import NetEaseNewsHotSearchItem, NetEaseNewsHotSearchResponse


class NetEaseNewsClient(HotSearchClient):
    """网易新闻客户端。"""

    def __init__(self, **kwargs):
        """初始化网易新闻客户端。"""
        super().__init__(**kwargs)

    def get_news(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], NetEaseNewsHotSearchResponse]:
        """获取新闻。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], NetEaseNewsHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="ne-news", sub_tab="news", page=page)
        if as_model:
            return NetEaseNewsHotSearchResponse.from_dict(data, "news")
        return data

    def get_hot(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], NetEaseNewsHotSearchResponse]:
        """获取热度榜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], NetEaseNewsHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="ne-news", sub_tab="htd", page=page)
        if as_model:
            return NetEaseNewsHotSearchResponse.from_dict(data, "htd")
        return data

    def get_items(
        self, sub_tab: str = "news", page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[NetEaseNewsHotSearchItem]]:
        """获取新闻条目。

        Args:
            sub_tab: 子分类，可选值：news, htd
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[List[Dict[str, Any]], List[NetEaseNewsHotSearchItem]]: 新闻条目列表或结构化模型对象列表
        """
        data = self.request(tab="ne-news", sub_tab=sub_tab, page=page)
        if "data" in data and "list" in data["data"]:
            list_str = data["data"]["list"]
            try:
                items = json.loads(list_str)
                if as_model:
                    return [NetEaseNewsHotSearchItem.from_dict(item) for item in items]
                return items
            except json.JSONDecodeError:
                pass
        return []
