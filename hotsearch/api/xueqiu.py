"""雪球热帖客户端。

提供获取雪球热帖数据的客户端。
"""

import json
from typing import Dict, Any, List, Union, Optional

from ..client import HotSearchClient
from .models.xueqiu import (
    XueqiuHotSearchResponse,
    XueqiuTopicItem,
    XueqiuNewsItem,
    XueqiuNoticeItem,
)


class XueqiuClient(HotSearchClient):
    """雪球热帖客户端。"""

    def __init__(self, **kwargs):
        """初始化雪球热帖客户端。"""
        super().__init__(**kwargs)

    def get_topic(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], XueqiuHotSearchResponse]:
        """获取话题。

        Args:
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            如果as_model为True，返回XueqiuHotSearchResponse对象，否则返回原始数据字典
        """
        try:
            data = self.request(tab="xueqiu", sub_tab="topic", page=page)

            if as_model:
                return XueqiuHotSearchResponse.from_dict(data, "topic")
            return data
        except Exception as e:
            # 如果请求失败
            if hasattr(self, "logger"):
                self.logger.error(f"获取话题失败: {str(e)}")
            if as_model:
                return XueqiuHotSearchResponse([], 0, 0, 0, 0, 0)
            return {"code": 500, "data": {"list": "[]"}, "msg": str(e)}

    def get_news(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], XueqiuHotSearchResponse]:
        """获取新闻。

        Args:
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            如果as_model为True，返回XueqiuHotSearchResponse对象，否则返回原始数据字典
        """
        try:
            data = self.request(tab="xueqiu", sub_tab="news", page=page)

            if as_model:
                return XueqiuHotSearchResponse.from_dict(data, "news")
            return data
        except Exception as e:
            # 如果请求失败
            if hasattr(self, "logger"):
                self.logger.error(f"获取新闻失败: {str(e)}")
            if as_model:
                return XueqiuHotSearchResponse([], 0, 0, 0, 0, 0)
            return {"code": 500, "data": {"list": "[]"}, "msg": str(e)}

    def get_notice(
        self, page: int = 1, as_model: bool = False
    ) -> Union[Dict[str, Any], XueqiuHotSearchResponse]:
        """获取公告。

        Args:
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            如果as_model为True，返回XueqiuHotSearchResponse对象，否则返回原始数据字典
        """
        try:
            data = self.request(tab="xueqiu", sub_tab="notice", page=page)

            if as_model:
                return XueqiuHotSearchResponse.from_dict(data, "notice")
            return data
        except Exception as e:
            # 如果请求失败
            if hasattr(self, "logger"):
                self.logger.error(f"获取公告失败: {str(e)}")
            if as_model:
                return XueqiuHotSearchResponse([], 0, 0, 0, 0, 0)
            return {"code": 500, "data": {"list": "[]"}, "msg": str(e)}

    def get_items(
        self, sub_tab: str = "topic", page: int = 1, as_model: bool = False
    ) -> Union[
        List[Dict[str, Any]],
        List[Union[XueqiuTopicItem, XueqiuNewsItem, XueqiuNoticeItem]],
    ]:
        """获取热帖条目。

        Args:
            sub_tab: 子分类，可选值：topic, news, notice
            page: 页码
            as_model: 是否返回模型对象

        Returns:
            如果as_model为True，返回数据模型对象列表，否则返回原始数据列表
        """
        if as_model:
            try:
                response = None
                if sub_tab == "topic":
                    response = self.get_topic(page=page, as_model=True)
                elif sub_tab == "news":
                    response = self.get_news(page=page, as_model=True)
                elif sub_tab == "notice":
                    response = self.get_notice(page=page, as_model=True)

                if response:
                    return response.items
                return []
            except Exception as e:
                # 记录错误但返回空列表
                if hasattr(self, "logger"):
                    self.logger.error(f"获取条目失败: {str(e)}")
                return []
        else:
            try:
                data = self.request(tab="xueqiu", sub_tab=sub_tab, page=page)
                if "data" in data and "list" in data["data"]:
                    list_data = data["data"]["list"]
                    if isinstance(list_data, str):
                        try:
                            return json.loads(list_data)
                        except json.JSONDecodeError:
                            return []
                    return list_data
                return []
            except Exception as e:
                # 记录错误但返回空列表
                if hasattr(self, "logger"):
                    self.logger.error(f"获取条目失败: {str(e)}")
                return []

    @property
    def topic_items(self) -> List[XueqiuTopicItem]:
        """获取话题条目列表。"""
        return self.get_items(sub_tab="topic", as_model=True)

    @property
    def news_items(self) -> List[XueqiuNewsItem]:
        """获取新闻条目列表。"""
        return self.get_items(sub_tab="news", as_model=True)

    @property
    def notice_items(self) -> List[XueqiuNoticeItem]:
        """获取公告条目列表。"""
        return self.get_items(sub_tab="notice", as_model=True)

    def get_topics_by_keyword(self, keyword: str) -> List[XueqiuTopicItem]:
        """按关键词搜索话题。

        在标题和描述中搜索指定关键词，返回匹配的话题条目列表。

        Args:
            keyword: 要搜索的关键词

        Returns:
            List[XueqiuTopicItem]: 匹配关键词的话题条目列表
        """
        items = self.topic_items
        if not keyword:
            return items

        return [item for item in items if keyword in item.title or keyword in item.desc]

    def get_topics_sorted_by_reads(self, reverse: bool = True) -> List[XueqiuTopicItem]:
        """获取按阅读量排序的话题列表。

        Args:
            reverse: 是否倒序排列（默认为True，即阅读量从高到低）

        Returns:
            List[XueqiuTopicItem]: 排序后的话题列表
        """
        items = self.topic_items
        # 过滤掉没有阅读量的条目
        items_with_reads = [item for item in items if item.read_count is not None]
        return sorted(
            items_with_reads, key=lambda x: x.read_count or 0, reverse=reverse
        )

    def get_news_sorted_by_time(self, reverse: bool = True) -> List[XueqiuNewsItem]:
        """获取按时间排序的新闻列表。

        Args:
            reverse: 是否倒序排列（默认为True，即最新的排在前面）

        Returns:
            List[XueqiuNewsItem]: 排序后的新闻列表
        """
        items = self.news_items
        return sorted(items, key=lambda x: x.created_at or 0, reverse=reverse)

    def get_notice_sorted_by_time(self, reverse: bool = True) -> List[XueqiuNoticeItem]:
        """获取按时间排序的公告列表。

        Args:
            reverse: 是否倒序排列（默认为True，即最新的排在前面）

        Returns:
            List[XueqiuNoticeItem]: 排序后的公告列表
        """
        items = self.notice_items
        return sorted(items, key=lambda x: x.created_at or 0, reverse=reverse)

    def get_topics_with_positive_stocks(self) -> List[XueqiuTopicItem]:
        """获取包含上涨股票的话题列表。

        Returns:
            List[XueqiuTopicItem]: 包含上涨股票的话题列表
        """
        items = self.topic_items
        return [item for item in items if item.get_positive_stocks()]

    def get_topics_with_negative_stocks(self) -> List[XueqiuTopicItem]:
        """获取包含下跌股票的话题列表。

        Returns:
            List[XueqiuTopicItem]: 包含下跌股票的话题列表
        """
        items = self.topic_items
        return [item for item in items if item.get_negative_stocks()]
