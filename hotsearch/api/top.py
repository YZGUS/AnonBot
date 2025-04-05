"""热榜综合客户端。

提供获取热榜综合数据的客户端。
"""

import os
import json
import time
import dataclasses
from typing import Dict, Any, List, Union, Optional, Callable

from ..client import HotSearchClient
from .models.top import TopHotSearchItem, TopHotSearchResponse


class TopClient(HotSearchClient):
    """热榜综合客户端。"""

    def __init__(self, **kwargs):
        """初始化热榜综合客户端。"""
        super().__init__(**kwargs)

    def get_today(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], TopHotSearchResponse]:
        """获取今日热榜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], TopHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="top", sub_tab="today", page=page)
        if as_model:
            response = TopHotSearchResponse.from_dict(data)
            response.sub_tab = "today"  # 确保子分类正确
            return response
        return data

    def get_weekly(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], TopHotSearchResponse]:
        """获取本周热榜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], TopHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="top", sub_tab="weekly", page=page)
        if as_model:
            response = TopHotSearchResponse.from_dict(data)
            response.sub_tab = "weekly"  # 确保子分类正确
            return response
        return data

    def get_monthly(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], TopHotSearchResponse]:
        """获取本月热榜。

        Args:
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[Dict[str, Any], TopHotSearchResponse]: API响应的JSON数据或结构化模型对象
        """
        data = self.request(tab="top", sub_tab="monthly", page=page)
        if as_model:
            response = TopHotSearchResponse.from_dict(data)
            response.sub_tab = "monthly"  # 确保子分类正确
            return response
        return data

    def get_items(
        self, sub_tab: str = "today", page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[TopHotSearchItem]]:
        """获取热榜条目。

        Args:
            sub_tab: 子分类，可选值：today, weekly, monthly
            page: 页码
            as_model: 是否返回结构化模型对象

        Returns:
            Union[List[Dict[str, Any]], List[TopHotSearchItem]]: 热榜条目列表或结构化模型列表
        """
        data = self.request(tab="top", sub_tab=sub_tab, page=page)
        if as_model:
            response = TopHotSearchResponse.from_dict(data)
            return response.items

        if "data" in data:
            # 优先尝试获取items字段，如果不存在则尝试获取list字段
            items = data["data"].get("items", data["data"].get("list", []))
            # 处理可能的JSON字符串
            if isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    return []
            return items
        return []

    def get_items_sorted(
        self, sub_tab: str = "today", page: int = 1, reverse: bool = True
    ) -> List[TopHotSearchItem]:
        """获取按热度排序的热榜条目。

        Args:
            sub_tab: 子分类，可选值：today, weekly, monthly
            page: 页码
            reverse: 是否降序排序，默认为True（从高到低）

        Returns:
            List[TopHotSearchItem]: 排序后的热榜条目列表
        """
        items = self.get_items(sub_tab=sub_tab, page=page, as_model=True)
        return sorted(items, key=lambda x: x.hot_value, reverse=reverse)

    def search_items(
        self, keyword: str, sub_tab: str = "today", page: int = 1
    ) -> List[TopHotSearchItem]:
        """搜索包含关键词的热榜条目。

        Args:
            keyword: 搜索关键词
            sub_tab: 子分类，可选值：today, weekly, monthly
            page: 页码

        Returns:
            List[TopHotSearchItem]: 匹配的热榜条目列表
        """
        items = self.get_items(sub_tab=sub_tab, page=page, as_model=True)
        return [item for item in items if keyword.lower() in item.title.lower()]

    def get_popular_items(
        self, sub_tab: str = "today", page: int = 1, threshold: int = 10000
    ) -> List[TopHotSearchItem]:
        """获取热度超过阈值的热榜条目。

        Args:
            sub_tab: 子分类，可选值：today, weekly, monthly
            page: 页码
            threshold: 热度阈值，默认为10000

        Returns:
            List[TopHotSearchItem]: 热度超过阈值的热榜条目列表
        """
        items = self.get_items(sub_tab=sub_tab, page=page, as_model=True)
        return [item for item in items if item.hot_value > threshold]

    def process_items(
        self,
        items: List[TopHotSearchItem],
        processor_func: Callable[[TopHotSearchItem], Any],
    ) -> List[Any]:
        """批量处理热榜条目。

        Args:
            items: 热榜条目列表
            processor_func: 处理函数，接收单个条目参数

        Returns:
            List[Any]: 处理后的结果列表
        """
        return [processor_func(item) for item in items]

    def export_items(
        self,
        items: List[Union[Dict[str, Any], TopHotSearchItem]],
        format: str = "json",
        file_path: Optional[str] = None,
    ) -> str:
        """导出热榜条目到文件。

        Args:
            items: 热榜条目列表
            format: 格式（json/csv）
            file_path: 文件路径，如果为None则使用默认路径

        Returns:
            str: 导出文件的路径
        """
        # 设置默认导出路径
        if not file_path:
            file_path = os.path.join(
                self.data_dir or "./data", f"top_export_{int(time.time())}.{format}"
            )

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 准备数据，将dataclass对象转换为字典
        export_data = []
        for item in items:
            if hasattr(item, "__dataclass_fields__"):
                export_data.append(dataclasses.asdict(item))
            else:
                export_data.append(item)

        # 根据格式导出
        if format.lower() == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
        elif format.lower() == "csv":
            import csv

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                if export_data:
                    fieldnames = export_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for item in export_data:
                        writer.writerow(item)

        return file_path
