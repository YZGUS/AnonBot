"""今日头条客户端。

提供获取今日头条热榜数据的客户端。
"""

import json
import os
import time
import dataclasses
from typing import Dict, Any, List, Optional, Union, Callable

from ..client import HotSearchClient
from .models.toutiao import ToutiaoHotTopics, ToutiaoHotSearchItem


class ToutiaoClient(HotSearchClient):
    """今日头条客户端。"""

    def __init__(
        self,
        auth_token: Optional[str] = None,
        save_data: bool = False,
        data_dir: Optional[str] = None,
    ):
        """初始化今日头条客户端。

        Args:
            auth_token: 授权令牌，为None时使用默认令牌
            save_data: 是否保存API原始数据
            data_dir: 保存数据的目录
        """
        super().__init__(auth_token=auth_token, save_data=save_data, data_dir=data_dir)

    def get_hot(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], ToutiaoHotTopics]:
        """获取热门内容。

        Args:
            page: 页码
            as_model: 是否返回数据模型

        Returns:
            Union[Dict[str, Any], ToutiaoHotTopics]: API响应的JSON数据或数据模型
        """
        data = self.request(tab="toutiao", sub_tab="hot", page=page)

        if as_model:
            return ToutiaoHotTopics.from_dict(data)

        return data

    def get_items(
        self, page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[ToutiaoHotSearchItem]]:
        """获取热门内容条目。

        Args:
            page: 页码
            as_model: 是否返回数据模型

        Returns:
            Union[List[Dict[str, Any]], List[ToutiaoHotSearchItem]]: 热门内容条目列表
        """
        data = self.get_hot(page=page, as_model=True)

        if as_model:
            return data.items

        # 转换为字典列表
        return [dataclasses.asdict(item) for item in data.items]

    def get_items_by_label(
        self, label: str, page: int = 1
    ) -> List[ToutiaoHotSearchItem]:
        """获取指定标签的话题。

        Args:
            label: 标签名称，如 "boom", "hot", "new" 等
            page: 页码

        Returns:
            List[ToutiaoHotSearchItem]: 符合标签的话题列表
        """
        data = self.get_hot(page=page, as_model=True)

        # 筛选指定标签
        return [item for item in data.items if item.label == label]

    def get_items_sorted(
        self, page: int = 1, reverse: bool = True
    ) -> List[ToutiaoHotSearchItem]:
        """获取按热度值排序的话题。

        Args:
            page: 页码
            reverse: 是否倒序（从高到低）

        Returns:
            List[ToutiaoHotSearchItem]: 排序后的话题列表
        """
        data = self.get_hot(page=page, as_model=True)

        # 按热度值排序
        return sorted(data.items, key=lambda x: x.hot_value_int, reverse=reverse)

    def search_items(self, keyword: str, page: int = 1) -> List[ToutiaoHotSearchItem]:
        """搜索包含关键词的话题。

        Args:
            keyword: 关键词
            page: 页码

        Returns:
            List[ToutiaoHotSearchItem]: 包含关键词的话题列表
        """
        data = self.get_hot(page=page, as_model=True)

        # 关键词搜索
        return [item for item in data.items if keyword.lower() in item.title.lower()]

    def process_items(
        self, items: List[ToutiaoHotSearchItem], processor_func: Callable
    ) -> List[Any]:
        """批量处理话题条目。

        Args:
            items: 话题条目列表
            processor_func: 处理函数，接收单个条目参数

        Returns:
            List[Any]: 处理后的结果列表
        """
        return [processor_func(item) for item in items]

    def export_items(
        self,
        items: List[ToutiaoHotSearchItem],
        format: str = "json",
        file_path: Optional[str] = None,
    ) -> str:
        """导出话题条目到文件。

        Args:
            items: 话题条目列表
            format: 格式 (json/csv)
            file_path: 文件路径，为None时自动生成

        Returns:
            str: 导出文件的路径
        """
        if not file_path:
            output_dir = self.data_dir or "examples/output"
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(
                output_dir, f"toutiao_export_{int(time.time())}.{format}"
            )

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                data = [dataclasses.asdict(item) for item in items]
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                fieldnames = dataclasses.asdict(items[0]).keys() if items else []
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for item in items:
                    writer.writerow(dataclasses.asdict(item))

        return file_path
