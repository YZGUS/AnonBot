"""腾讯新闻客户端。

提供获取腾讯新闻热榜数据的客户端。
"""

import json
from typing import Dict, Any, List, Union

from ..client import HotSearchClient
from .models.tencent_news import TencentNewsHotSearchItem, TencentNewsHotSearchResponse


class TencentNewsClient(HotSearchClient):
    """腾讯新闻客户端。"""

    def __init__(self, **kwargs):
        """初始化腾讯新闻客户端。"""
        super().__init__(**kwargs)

    def get_hot(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], TencentNewsHotSearchResponse]:
        """获取热门新闻。

        Args:
            page: 页码
            as_model: 是否返回数据模型对象

        Returns:
            Union[Dict[str, Any], TencentNewsHotSearchResponse]: API响应的JSON数据或数据模型对象
        """
        data = self.request(tab="tencent-news", sub_tab="hot", page=page)
        if as_model:
            return TencentNewsHotSearchResponse.from_dict(data, "hot")
        return data

    def get_items(
        self, page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[TencentNewsHotSearchItem]]:
        """获取热门新闻条目。

        Args:
            page: 页码
            as_model: 是否返回数据模型对象

        Returns:
            Union[List[Dict[str, Any]], List[TencentNewsHotSearchItem]]: 热门新闻条目列表或数据模型对象列表
        """
        data = self.request(tab="tencent-news", sub_tab="hot", page=page)
        if "data" in data and "list" in data["data"]:
            list_str = data["data"]["list"]
            try:
                items = json.loads(list_str)
                if as_model:
                    return [TencentNewsHotSearchItem.from_dict(item) for item in items]
                return items
            except json.JSONDecodeError:
                pass
        return []
