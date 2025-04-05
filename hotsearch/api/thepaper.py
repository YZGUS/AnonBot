"""澎湃新闻客户端。

提供获取澎湃新闻热榜数据的客户端。
"""

import json
import os
import time
import dataclasses
from typing import Dict, Any, List, Union, Optional, Callable

from ..client import HotSearchClient
from .models.thepaper import ThePaperItem, ThePaperHotTopics


class ThePaperClient(HotSearchClient):
    """澎湃新闻客户端。"""

    def __init__(self, **kwargs):
        """初始化澎湃新闻客户端。"""
        super().__init__(**kwargs)

    def get_hot(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], ThePaperHotTopics]:
        """获取热门新闻。

        Args:
            page: 页码
            as_model: 是否返回数据模型

        Returns:
            Union[Dict[str, Any], ThePaperHotTopics]: API响应的JSON数据或模型
        """
        data = self.request(tab="thepaper", sub_tab="hot", page=page)

        if as_model:
            return ThePaperHotTopics.from_dict(data)
        return data

    def get_items(
        self, page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[ThePaperItem]]:
        """获取热门新闻条目。

        Args:
            page: 页码
            as_model: 是否返回数据模型

        Returns:
            Union[List[Dict[str, Any]], List[ThePaperItem]]: 热门新闻条目列表
        """
        data = self.request(tab="thepaper", sub_tab="hot", page=page)

        if "data" not in data or "list" not in data["data"]:
            return []

        list_data = data["data"]["list"]

        # 处理JSON字符串
        if isinstance(list_data, str):
            try:
                items = json.loads(list_data)
            except json.JSONDecodeError:
                items = []
        else:
            items = []

        if as_model:
            return [ThePaperItem.from_dict(item) for item in items]
        return items

    def search_items(self, keyword: str, page: int = 1) -> List[ThePaperItem]:
        """搜索包含关键词的条目。

        Args:
            keyword: 搜索关键词
            page: 页码

        Returns:
            List[ThePaperItem]: 匹配的条目列表
        """
        items = self.get_items(page, as_model=True)
        return [
            item
            for item in items
            if keyword.lower() in item.title.lower()
            or keyword.lower() in item.desc.lower()
        ]

    def get_items_sorted(
        self, page: int = 1, sort_by: str = "comment_num", reverse: bool = True
    ) -> List[ThePaperItem]:
        """获取排序后的条目。

        Args:
            page: 页码
            sort_by: 排序字段，可选值：comment_num, pub_time, title
            reverse: 是否降序排序

        Returns:
            List[ThePaperItem]: 排序后的条目列表
        """
        items = self.get_items(page, as_model=True)

        # 根据不同字段排序
        if sort_by == "comment_num":
            return sorted(items, key=lambda x: x.comment_num, reverse=reverse)
        elif sort_by == "pub_time":
            return sorted(items, key=lambda x: x.pub_time, reverse=reverse)
        elif sort_by == "title":
            return sorted(items, key=lambda x: x.title, reverse=reverse)
        else:
            return items

    def process_items(
        self, items: List[ThePaperItem], processor_func: Callable[[ThePaperItem], Any]
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
        items: List[ThePaperItem],
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
                f"thepaper_export_{int(time.time())}.{format}",
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
