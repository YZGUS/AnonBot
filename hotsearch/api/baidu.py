"""百度热搜客户端。

提供获取百度热搜数据的客户端。
"""

import json
from typing import Dict, Any, List, Optional, Union

from ..client import HotSearchClient
from .models.baidu import BaiduHotSearchItem, BaiduHotSearchResponse


class BaiduClient(HotSearchClient):
    """百度热搜客户端。"""

    def __init__(self, **kwargs):
        """初始化百度热搜客户端。"""
        super().__init__(**kwargs)

    def get_realtime(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BaiduHotSearchResponse]:
        """获取实时热点。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], BaiduHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="baidu", sub_tab="realtime", page=page)
        if as_model:
            response = BaiduHotSearchResponse.from_dict(data)
            response.sub_tab = "realtime"  # 确保子分类正确
            return response
        return data

    def get_phrase(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BaiduHotSearchResponse]:
        """获取热搜词。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], BaiduHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="baidu", sub_tab="phrase", page=page)
        if as_model:
            response = BaiduHotSearchResponse.from_dict(data)
            response.sub_tab = "phrase"  # 确保子分类正确
            return response
        return data

    def get_novel(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BaiduHotSearchResponse]:
        """获取小说热搜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], BaiduHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="baidu", sub_tab="novel", page=page)
        if as_model:
            response = BaiduHotSearchResponse.from_dict(data)
            response.sub_tab = "novel"  # 确保子分类正确
            return response
        return data

    def get_game(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BaiduHotSearchResponse]:
        """获取游戏热搜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], BaiduHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="baidu", sub_tab="game", page=page)
        if as_model:
            response = BaiduHotSearchResponse.from_dict(data)
            response.sub_tab = "game"  # 确保子分类正确
            return response
        return data

    def get_car(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BaiduHotSearchResponse]:
        """获取汽车热搜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], BaiduHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="baidu", sub_tab="car", page=page)
        if as_model:
            response = BaiduHotSearchResponse.from_dict(data)
            response.sub_tab = "car"  # 确保子分类正确
            return response
        return data

    def get_teleplay(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BaiduHotSearchResponse]:
        """获取电视剧热搜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], BaiduHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="baidu", sub_tab="teleplay", page=page)
        if as_model:
            response = BaiduHotSearchResponse.from_dict(data)
            response.sub_tab = "teleplay"  # 确保子分类正确
            return response
        return data

    def get_items(
        self, sub_tab: str = "realtime", page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[BaiduHotSearchItem]]:
        """获取热搜条目。

        Args:
            sub_tab: 子分类，可选值：realtime, phrase, novel, game, car, teleplay
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[List[Dict[str, Any]], List[BaiduHotSearchItem]]: 热搜条目列表或结构化模型列表
        """
        data = self.request(tab="baidu", sub_tab=sub_tab, page=page)
        if as_model:
            response = BaiduHotSearchResponse.from_dict(data)
            response.sub_tab = sub_tab  # 确保子分类正确
            return response.items

        if "data" in data and "list" in data["data"]:
            try:
                return json.loads(data["data"]["list"])
            except json.JSONDecodeError:
                return []
        return []
