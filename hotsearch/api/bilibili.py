"""B站热门客户端。

提供获取B站热门数据的客户端。
"""

import json
import os
import time
import dataclasses
from typing import Dict, Any, List, Union, Optional, Callable

from ..client import HotSearchClient
from .models.bilibili import BilibiliItem, BilibiliHotTopics


class BilibiliClient(HotSearchClient):
    """B站热门客户端。"""

    def __init__(self, **kwargs):
        """初始化B站热门客户端。"""
        super().__init__(**kwargs)

    def get_popular(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BilibiliHotTopics]:
        """获取热门视频。

        Args:
            page: 页码
            as_model: 是否返回数据模型

        Returns:
            Union[Dict[str, Any], BilibiliHotTopics]: API响应的JSON数据或模型
        """
        data = self.request(
            tab="bilibili", sub_tab="popular", page=page, date_type="now"
        )

        if as_model:
            return BilibiliHotTopics.from_dict(data)
        return data

    def get_weekly(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BilibiliHotTopics]:
        """获取每周必看。

        Args:
            page: 页码
            as_model: 是否返回数据模型

        Returns:
            Union[Dict[str, Any], BilibiliHotTopics]: API响应的JSON数据或模型
        """
        data = self.request(
            tab="bilibili", sub_tab="weekly", page=page, date_type="now"
        )

        if as_model:
            return BilibiliHotTopics.from_dict(data)
        return data

    def get_rank(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], BilibiliHotTopics]:
        """获取排行榜。

        Args:
            page: 页码
            as_model: 是否返回数据模型

        Returns:
            Union[Dict[str, Any], BilibiliHotTopics]: API响应的JSON数据或模型
        """
        data = self.request(tab="bilibili", sub_tab="rank", page=page, date_type="now")

        if as_model:
            return BilibiliHotTopics.from_dict(data)
        return data

    def get_items(
        self, sub_tab: str = "popular", page: int = 1
    ) -> List[Dict[str, Any]]:
        """获取热门条目。

        Args:
            sub_tab: 子分类，可选值：popular, weekly, rank
            page: 页码

        Returns:
            List[Dict[str, Any]]: 热门条目列表
        """
        data = self.request(tab="bilibili", sub_tab=sub_tab, page=page, date_type="now")
        if "data" in data and "list" in data["data"]:
            list_data = data["data"]["list"]
            # 处理JSON字符串
            if isinstance(list_data, str):
                try:
                    return json.loads(list_data)
                except:
                    return []
            elif isinstance(list_data, list):
                return list_data
        return []

    def get_model_items(
        self, sub_tab: str = "popular", page: int = 1
    ) -> List[BilibiliItem]:
        """获取热门条目模型列表。

        Args:
            sub_tab: 子分类，可选值：popular, weekly, rank
            page: 页码

        Returns:
            List[BilibiliItem]: 热门条目模型列表
        """
        items = self.get_items(sub_tab, page)
        return [BilibiliItem.from_dict(item) for item in items]

    def search_items(
        self, keyword: str, sub_tab: str = "popular", page: int = 1
    ) -> List[BilibiliItem]:
        """搜索包含关键词的条目。

        Args:
            keyword: 搜索关键词
            sub_tab: 子分类，可选值：popular, weekly, rank
            page: 页码

        Returns:
            List[BilibiliItem]: 匹配的条目列表
        """
        items = self.get_model_items(sub_tab, page)
        return [
            item
            for item in items
            if keyword.lower() in item.title.lower()
            or keyword.lower() in item.describe.lower()
        ]

    def get_items_by_views(
        self, min_views: int = 0, sub_tab: str = "popular", page: int = 1
    ) -> List[BilibiliItem]:
        """获取指定播放量以上的条目。

        Args:
            min_views: 最小播放量
            sub_tab: 子分类，可选值：popular, weekly, rank
            page: 页码

        Returns:
            List[BilibiliItem]: 匹配的条目列表
        """
        items = self.get_model_items(sub_tab, page)
        return [item for item in items if item.view >= min_views]

    def get_items_sorted(
        self,
        sub_tab: str = "popular",
        page: int = 1,
        sort_by: str = "view",
        reverse: bool = True,
    ) -> List[BilibiliItem]:
        """获取排序后的条目。

        Args:
            sub_tab: 子分类，可选值：popular, weekly, rank
            page: 页码
            sort_by: 排序字段，可选值：view, danmaku, title
            reverse: 是否降序排序

        Returns:
            List[BilibiliItem]: 排序后的条目列表
        """
        items = self.get_model_items(sub_tab, page)

        # 根据不同字段排序
        if sort_by == "view":
            return sorted(items, key=lambda x: x.view, reverse=reverse)
        elif sort_by == "danmaku":
            return sorted(items, key=lambda x: x.danmaku, reverse=reverse)
        elif sort_by == "title":
            return sorted(items, key=lambda x: x.title, reverse=reverse)
        else:
            return items

    def get_items_by_up(
        self, up_name: str, sub_tab: str = "popular", page: int = 1
    ) -> List[BilibiliItem]:
        """获取指定UP主的条目。

        Args:
            up_name: UP主名称
            sub_tab: 子分类，可选值：popular, weekly, rank
            page: 页码

        Returns:
            List[BilibiliItem]: 匹配的条目列表
        """
        items = self.get_model_items(sub_tab, page)
        return [item for item in items if up_name.lower() in item.owner_name.lower()]

    def process_items(
        self, items: List[BilibiliItem], processor_func: Callable[[BilibiliItem], Any]
    ) -> List[Any]:
        """批量处理条目。

        Args:
            items: 条目列表
            processor_func: 处理函数，接收单个条目参数

        Returns:
            List[Any]: 处理后的结果列表
        """
        return [processor_func(item) for item in items]

    def export_items(
        self,
        items: List[BilibiliItem],
        format: str = "json",
        file_path: Optional[str] = None,
    ) -> str:
        """导出条目到文件。

        Args:
            items: 条目列表
            format: 格式，可选值：json, csv
            file_path: 文件路径，为None时自动生成

        Returns:
            str: 导出文件路径
        """
        if not file_path:
            file_path = os.path.join(
                self.data_dir or "examples/output",
                f"bilibili_export_{int(time.time())}.{format}",
            )

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                data = [
                    (
                        dataclasses.asdict(item)
                        if hasattr(item, "__dataclass_fields__")
                        else item
                    )
                    for item in items
                ]
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                if items and hasattr(items[0], "__dataclass_fields__"):
                    fieldnames = items[0].__dataclass_fields__.keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for item in items:
                        writer.writerow(dataclasses.asdict(item))
                else:
                    writer = csv.writer(f)
                    for item in items:
                        writer.writerow(
                            item.values() if isinstance(item, dict) else item
                        )

        return file_path
