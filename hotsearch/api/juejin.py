"""掘金热榜API客户端。

提供获取掘金热榜数据的方法。
"""

import os
import json
import time
import dataclasses
from typing import Dict, List, Any, Optional, Union

from ..client import HotSearchClient
from .models.juejin import JuejinHotTopics, JuejinHotItem


class JuejinClient(HotSearchClient):
    """掘金热榜API客户端。"""

    def __init__(
            self,
            auth_token: Optional[str] = None,
            save_data: bool = True,
            data_dir: str = "./data",
    ):
        """初始化掘金客户端。

        Args:
            auth_token: 授权令牌，格式为"Bearer xxx"，为None时使用默认令牌（不推荐）
            save_data: 是否保存请求的原始数据
            data_dir: 保存数据的目录
        """
        super().__init__(auth_token, save_data, data_dir)

    def get_hot_topics(
            self, sub_tab: str = "all", page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], JuejinHotTopics]:
        """获取掘金热榜数据。

        Args:
            sub_tab: 分类，可选值有all(全部)、backend(后端)、frontend(前端)、
                    android(安卓)、ios(iOS)、ai(人工智能)、dev-tools(开发工具)、
                    code-life(代码人生)、read(阅读)
            page: 页码
            as_model: 是否返回模型对象，为False时返回原始数据

        Returns:
            Union[Dict[str, Any], JuejinHotTopics]: 热榜数据
        """
        data = self.request(tab="juejin", sub_tab=sub_tab, page=page)

        if self.save_data:
            self._save_data("juejin", sub_tab, data)

        if as_model:
            return JuejinHotTopics.from_dict(data)

        return data

    def get_items(
            self, sub_tab: str = "all", page: int = 1, as_model: bool = False
    ) -> Union[List[Dict[str, Any]], List[JuejinHotItem]]:
        """获取热榜条目列表。

        Args:
            sub_tab: 分类
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            Union[List[Dict[str, Any]], List[JuejinHotItem]]: 条目列表
        """
        data = self.get_hot_topics(sub_tab, page, as_model=True)

        if as_model:
            return data.items

        # 转换为字典列表
        return [item.to_dict() for item in data.items]

    def search_items(
            self, keyword: str, sub_tab: str = "all", page: int = 1
    ) -> List[JuejinHotItem]:
        """搜索包含关键词的热榜条目。

        Args:
            keyword: 关键词
            sub_tab: 分类
            page: 页码

        Returns:
            List[JuejinHotItem]: 符合条件的条目列表
        """
        data = self.get_hot_topics(sub_tab, page, as_model=True)
        return data.search_by_title(keyword)

    def get_items_by_author(
            self, author_name: str, sub_tab: str = "all", page: int = 1
    ) -> List[JuejinHotItem]:
        """获取指定作者的热榜条目。

        Args:
            author_name: 作者名称
            sub_tab: 分类
            page: 页码

        Returns:
            List[JuejinHotItem]: 符合条件的条目列表
        """
        data = self.get_hot_topics(sub_tab, page, as_model=True)
        return data.get_by_author(author_name)

    def get_top_items(
            self, limit: int = 10, sub_tab: str = "all", page: int = 1
    ) -> List[JuejinHotItem]:
        """获取前N个热榜条目。

        Args:
            limit: 数量限制
            sub_tab: 分类
            page: 页码

        Returns:
            List[JuejinHotItem]: 条目列表
        """
        data = self.get_hot_topics(sub_tab, page, as_model=True)
        return data.get_top_items(limit)

    def get_items_sorted_by_popularity(
            self, sub_tab: str = "all", page: int = 1, reverse: bool = True
    ) -> List[JuejinHotItem]:
        """获取按热度指数排序的热榜条目。

        Args:
            sub_tab: 分类
            page: 页码
            reverse: 是否降序排列

        Returns:
            List[JuejinHotItem]: 排序后的条目列表
        """
        data = self.get_hot_topics(sub_tab, page, as_model=True)
        return data.sort_by_popularity(reverse)

    def get_items_sorted_by_views(
            self, sub_tab: str = "all", page: int = 1, reverse: bool = True
    ) -> List[JuejinHotItem]:
        """获取按浏览量排序的热榜条目。

        Args:
            sub_tab: 分类
            page: 页码
            reverse: 是否降序排列

        Returns:
            List[JuejinHotItem]: 排序后的条目列表
        """
        data = self.get_hot_topics(sub_tab, page, as_model=True)
        return data.sort_by_views(reverse)

    def export_items(
            self,
            items: List[JuejinHotItem],
            format: str = "json",
            file_path: Optional[str] = None,
    ) -> str:
        """导出热榜条目到文件。

        Args:
            items: 热榜条目列表
            format: 格式 (json/csv)
            file_path: 文件路径，为None时使用默认路径

        Returns:
            str: 文件路径
        """
        if not file_path:
            file_path = os.path.join(
                self.data_dir, f"juejin_export_{int(time.time())}.{format}"
            )

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if format == "json":
            with open(file_path, "w", encoding="utf-8") as f:
                items_dict = [item.to_dict() for item in items]
                json.dump(items_dict, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv

            with open(file_path, "w", encoding="utf-8", newline="") as f:
                if items:
                    fieldnames = items[0].to_dict().keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for item in items:
                        writer.writerow(item.to_dict())

        return file_path
