"""小红书客户端。

提供获取小红书热搜数据的客户端。
"""

import json
from typing import Dict, Any, List, Union, Optional

from ..client import HotSearchClient
from .models.xiaohongshu import XiaohongshuHotSearch, XiaohongshuHotSearchItem


class XiaohongshuClient(HotSearchClient):
    """小红书客户端。"""

    def __init__(self, **kwargs):
        """初始化小红书客户端。"""
        super().__init__(**kwargs)

    def get_hot_search(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], XiaohongshuHotSearch]:
        """获取热搜。

        Args:
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            如果as_model为True，返回XiaohongshuHotSearch对象，否则返回原始数据字典
        """
        data = self.request(tab="xiaohongshu", sub_tab="hot-search", page=page)

        if as_model:
            return XiaohongshuHotSearch.from_dict(data)
        return data

    def get_items(
        self, page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[XiaohongshuHotSearchItem]]:
        """获取热搜条目。

        Args:
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            如果as_model为True，返回XiaohongshuHotSearchItem对象列表，否则返回原始数据列表
        """
        try:
            data = self.request(tab="xiaohongshu", sub_tab="hot-search", page=page)

            if "data" in data and "list" in data["data"]:
                list_data = data["data"]["list"]

                # 处理JSON字符串
                if isinstance(list_data, str):
                    try:
                        items = json.loads(list_data)
                    except json.JSONDecodeError:
                        items = []
                else:
                    items = list_data
            else:
                items = []

            if as_model:
                return [XiaohongshuHotSearchItem.from_dict(item) for item in items]
            return items
        except Exception as e:
            self.logger.error(f"获取热搜条目失败: {str(e)}")
            return []

    def get_items_by_tag(
        self, tag: str, page: int = 1
    ) -> List[XiaohongshuHotSearchItem]:
        """获取特定标签的热搜条目。

        Args:
            tag: 热搜标签，如"新"、"热"、"独家"等
            page: 页码

        Returns:
            List[XiaohongshuHotSearchItem]: 指定标签的热搜条目列表
        """
        items = self.get_items(page=page, as_model=True)
        return [item for item in items if item.tag == tag]

    def get_new_items(self, page: int = 1) -> List[XiaohongshuHotSearchItem]:
        """获取新上榜的热搜条目。

        Args:
            page: 页码

        Returns:
            List[XiaohongshuHotSearchItem]: 新上榜的热搜条目列表
        """
        return self.get_items_by_tag("新", page)

    def get_hot_items(self, page: int = 1) -> List[XiaohongshuHotSearchItem]:
        """获取热门热搜条目。

        Args:
            page: 页码

        Returns:
            List[XiaohongshuHotSearchItem]: 热门热搜条目列表
        """
        return self.get_items_by_tag("热", page)

    def get_exclusive_items(self, page: int = 1) -> List[XiaohongshuHotSearchItem]:
        """获取独家热搜条目。

        Args:
            page: 页码

        Returns:
            List[XiaohongshuHotSearchItem]: 独家热搜条目列表
        """
        return self.get_items_by_tag("独家", page)

    def get_items_sorted_by_views(
        self, page: int = 1, reverse: bool = True
    ) -> List[XiaohongshuHotSearchItem]:
        """获取按浏览量排序的热搜条目。

        Args:
            page: 页码
            reverse: 是否倒序排序（默认为True，即从高到低）

        Returns:
            List[XiaohongshuHotSearchItem]: 排序后的热搜条目列表
        """
        items = self.get_items(page=page, as_model=True)
        return sorted(items, key=lambda item: item.views, reverse=reverse)

    def search_items(
        self, keyword: str, page: int = 1
    ) -> List[XiaohongshuHotSearchItem]:
        """搜索包含关键词的热搜条目。

        Args:
            keyword: 关键词
            page: 页码

        Returns:
            List[XiaohongshuHotSearchItem]: 匹配的热搜条目列表
        """
        items = self.get_items(page=page, as_model=True)
        return [item for item in items if keyword in item.title]
