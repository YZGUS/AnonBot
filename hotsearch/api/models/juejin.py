"""掘金热榜数据模型。

包含掘金热榜的数据模型。
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class JuejinHotItem:
    """掘金热榜条目模型。"""

    item_key: str  # 条目唯一标识
    id: str  # 文章ID
    title: str  # 文章标题
    author_id: str  # 作者ID
    author_name: str  # 作者名称
    author_avatar: str  # 作者头像URL
    view: int  # 浏览量
    collect: int  # 收藏数
    hot_rank: int  # 热度排名
    interact_count: int  # 互动数量
    comment_count: int  # 评论数量
    like: int  # 点赞数

    @property
    def article_url(self) -> str:
        """获取文章完整URL

        Returns:
            str: 文章URL
        """
        if not self.id:
            return ""
        return f"https://juejin.cn/post/{self.id}"

    @property
    def author_url(self) -> str:
        """获取作者主页URL

        Returns:
            str: 作者主页URL
        """
        if not self.author_id:
            return ""
        return f"https://juejin.cn/user/{self.author_id}"

    @property
    def full_avatar_url(self) -> str:
        """获取完整头像URL

        Returns:
            str: 完整头像URL
        """
        if not self.author_avatar:
            return ""

        if self.author_avatar.startswith(("http://", "https://")):
            return self.author_avatar

        return f"https:{self.author_avatar}"

    @property
    def popularity_index(self) -> float:
        """计算热度指数

        热度指数 = (点赞数 * 2 + 评论数 * 3 + 收藏数 * 4) / 100

        Returns:
            float: 热度指数
        """
        return (self.like * 2 + self.comment_count * 3 + self.collect * 4) / 100

    @property
    def interaction_rate(self) -> float:
        """计算互动率

        互动率 = 互动数 / 浏览量

        Returns:
            float: 互动率，0到1之间
        """
        if self.view == 0:
            return 0
        return self.interact_count / self.view

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "item_key": self.item_key,
            "id": self.id,
            "title": self.title,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "author_avatar": self.author_avatar,
            "view": self.view,
            "collect": self.collect,
            "hot_rank": self.hot_rank,
            "interact_count": self.interact_count,
            "comment_count": self.comment_count,
            "like": self.like,
            "article_url": self.article_url,
            "author_url": self.author_url,
            "full_avatar_url": self.full_avatar_url,
            "popularity_index": self.popularity_index,
            "interaction_rate": self.interaction_rate,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JuejinHotItem":
        """从字典创建模型。

        Args:
            data: 字典数据

        Returns:
            JuejinHotItem: 模型实例
        """
        if not data or not isinstance(data, dict):
            return cls("", "", "", "", "", "", 0, 0, 0, 0, 0, 0)

        # 安全处理字符串值
        item_key = data.get("item_key", "")
        if item_key is None:
            item_key = ""

        id_val = data.get("id", "")
        if id_val is None:
            id_val = ""

        title = data.get("title", "")
        if title is None:
            title = ""

        author_id = data.get("author_id", "")
        if author_id is None:
            author_id = ""

        author_name = data.get("author_name", "")
        if author_name is None:
            author_name = ""

        author_avatar = data.get("author_avatar", "")
        if author_avatar is None:
            author_avatar = ""

        # 安全转换数值类型
        try:
            view = int(data.get("view", 0))
        except (ValueError, TypeError):
            view = 0

        try:
            collect = int(data.get("collect", 0))
        except (ValueError, TypeError):
            collect = 0

        try:
            hot_rank = int(data.get("hot_rank", 0))
        except (ValueError, TypeError):
            hot_rank = 0

        try:
            interact_count = int(data.get("interact_count", 0))
        except (ValueError, TypeError):
            interact_count = 0

        try:
            comment_count = int(data.get("comment_count", 0))
        except (ValueError, TypeError):
            comment_count = 0

        try:
            like = int(data.get("like", 0))
        except (ValueError, TypeError):
            like = 0

        return cls(
            item_key=item_key,
            id=id_val,
            title=title,
            author_id=author_id,
            author_name=author_name,
            author_avatar=author_avatar,
            view=view,
            collect=collect,
            hot_rank=hot_rank,
            interact_count=interact_count,
            comment_count=comment_count,
            like=like,
        )


@dataclass
class JuejinHotTopics:
    """掘金热榜数据模型。"""

    items: List[JuejinHotItem]  # 热榜条目列表
    last_list_time: int  # 上次更新时间
    next_refresh_time: int  # 下次刷新时间
    version: int  # 版本号
    current_page: int  # 当前页码
    total_page: int  # 总页数

    def get_top_items(self, limit: int = 10) -> List[JuejinHotItem]:
        """获取前N个热门条目

        Args:
            limit: 返回条目数量限制

        Returns:
            List[JuejinHotItem]: 热门条目列表
        """
        return self.items[: min(limit, len(self.items))]

    def get_by_author(self, author_name: str) -> List[JuejinHotItem]:
        """按作者名称筛选条目

        Args:
            author_name: 作者名称关键词

        Returns:
            List[JuejinHotItem]: 筛选后的条目列表
        """
        return [
            item
            for item in self.items
            if author_name.lower() in item.author_name.lower()
        ]

    def search_by_title(self, keyword: str) -> List[JuejinHotItem]:
        """按标题关键词搜索条目

        Args:
            keyword: 标题关键词

        Returns:
            List[JuejinHotItem]: 搜索结果列表
        """
        return [item for item in self.items if keyword.lower() in item.title.lower()]

    def sort_by_popularity(self, reverse: bool = True) -> List[JuejinHotItem]:
        """按热度指数排序条目

        Args:
            reverse: 是否降序排列，默认为True

        Returns:
            List[JuejinHotItem]: 排序后的条目列表
        """
        return sorted(self.items, key=lambda x: x.popularity_index, reverse=reverse)

    def sort_by_views(self, reverse: bool = True) -> List[JuejinHotItem]:
        """按浏览量排序条目

        Args:
            reverse: 是否降序排列，默认为True

        Returns:
            List[JuejinHotItem]: 排序后的条目列表
        """
        return sorted(self.items, key=lambda x: x.view, reverse=reverse)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            Dict[str, Any]: 字典表示
        """
        return {
            "items": [item.to_dict() for item in self.items],
            "last_list_time": self.last_list_time,
            "next_refresh_time": self.next_refresh_time,
            "version": self.version,
            "current_page": self.current_page,
            "total_page": self.total_page,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JuejinHotTopics":
        """从字典创建模型。

        Args:
            data: 字典数据

        Returns:
            JuejinHotTopics: 模型实例
        """
        if not data or not isinstance(data, dict):
            return cls([], 0, 0, 0, 0, 0)

        if "data" not in data:
            return cls([], 0, 0, 0, 0, 0)

        api_data = data["data"]

        # 处理JSON字符串列表
        list_data = api_data.get("list", "[]")
        if isinstance(list_data, str):
            try:
                list_data = json.loads(list_data)
            except json.JSONDecodeError:
                try:
                    # 尝试修复损坏的JSON字符串
                    import re

                    cleaned = re.sub(r"[^\x20-\x7E]", "", list_data)
                    list_data = json.loads(cleaned)
                except:
                    list_data = []

        # 确保列表类型
        if not isinstance(list_data, list):
            list_data = []

        # 从列表创建模型
        items = [JuejinHotItem.from_dict(item) for item in list_data]

        # 安全转换数值类型
        try:
            last_list_time = int(api_data.get("last_list_time", 0))
        except (ValueError, TypeError):
            last_list_time = 0

        try:
            next_refresh_time = int(api_data.get("next_refresh_time", 0))
        except (ValueError, TypeError):
            next_refresh_time = 0

        try:
            version = int(api_data.get("version", 0))
        except (ValueError, TypeError):
            version = 0

        try:
            current_page = int(api_data.get("current_page", 0))
        except (ValueError, TypeError):
            current_page = 0

        try:
            total_page = int(api_data.get("total_page", 0))
        except (ValueError, TypeError):
            total_page = 0

        return cls(
            items=items,
            last_list_time=last_list_time,
            next_refresh_time=next_refresh_time,
            version=version,
            current_page=current_page,
            total_page=total_page,
        )
