"""雪球热帖数据模型。

提供解析雪球热帖API响应的数据模型。
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class XueqiuStock:
    """雪球股票模型。"""

    name: str
    """股票名称。"""

    percentage: float
    """涨跌幅。"""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XueqiuStock":
        """从字典创建实例。"""
        name = data.get("name", "")

        # 安全处理percentage
        try:
            percentage = float(data.get("percentage", 0.0))
        except (ValueError, TypeError):
            percentage = 0.0

        return cls(name=name, percentage=percentage)


@dataclass
class XueqiuTopicItem:
    """雪球话题条目模型。"""

    item_key: str
    """条目唯一标识。"""

    title: str
    """标题。"""

    desc: str
    """描述。"""

    www_url: str
    """网页链接。"""

    reason: str
    """热度原因。"""

    stocks: List[XueqiuStock]
    """相关股票列表。"""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XueqiuTopicItem":
        """从字典创建实例。"""
        stocks = [XueqiuStock.from_dict(stock) for stock in data.get("stocks", [])]

        return cls(
            item_key=data.get("item_key", ""),
            title=data.get("title", ""),
            desc=data.get("desc", ""),
            www_url=data.get("www_url", ""),
            reason=data.get("reason", ""),
            stocks=stocks,
        )

    @property
    def read_count(self) -> Optional[int]:
        """获取阅读数。

        从热度原因中提取阅读数，例如 "198.2万阅读"

        Returns:
            int: 阅读数（以万为单位）或None（如果无法解析）
        """
        import re

        if not self.reason:
            return None

        pattern = r"(\d+\.?\d*)万阅读"
        match = re.search(pattern, self.reason)
        if match:
            try:
                return float(match.group(1)) * 10000
            except (ValueError, TypeError):
                return None
        return None

    @property
    def top_stock(self) -> Optional[XueqiuStock]:
        """获取排名第一的股票。

        Returns:
            XueqiuStock: 第一只股票或None（如果没有股票）
        """
        if not self.stocks:
            return None
        return self.stocks[0]

    def get_positive_stocks(self) -> List[XueqiuStock]:
        """获取涨幅为正的股票列表。

        Returns:
            List[XueqiuStock]: 涨幅为正的股票列表
        """
        return [stock for stock in self.stocks if stock.percentage > 0]

    def get_negative_stocks(self) -> List[XueqiuStock]:
        """获取涨幅为负的股票列表。

        Returns:
            List[XueqiuStock]: 涨幅为负的股票列表
        """
        return [stock for stock in self.stocks if stock.percentage < 0]


@dataclass
class XueqiuNewsItem:
    """雪球新闻条目模型。"""

    item_key: str
    """条目唯一标识。"""

    title: str
    """标题。"""

    www_url: str
    """网页链接。"""

    created_at: int
    """创建时间戳（毫秒）。"""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XueqiuNewsItem":
        """从字典创建实例。"""
        return cls(
            item_key=data.get("item_key", ""),
            title=data.get("title", ""),
            www_url=data.get("www_url", ""),
            created_at=int(data.get("created_at", 0)),
        )

    @property
    def formatted_date(self) -> str:
        """获取格式化的日期时间字符串。

        Returns:
            str: 格式化的日期时间，格式为'YYYY-MM-DD HH:MM:SS'
        """
        from datetime import datetime

        if not self.created_at:
            return ""

        # 雪球时间戳是毫秒级
        try:
            dt = datetime.fromtimestamp(self.created_at / 1000)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OverflowError):
            return ""


@dataclass
class XueqiuNoticeItem:
    """雪球公告条目模型。"""

    item_key: str
    """条目唯一标识。"""

    title: str
    """标题。"""

    www_url: str
    """网页链接。"""

    created_at: int
    """创建时间戳（毫秒）。"""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XueqiuNoticeItem":
        """从字典创建实例。"""
        return cls(
            item_key=data.get("item_key", ""),
            title=data.get("title", ""),
            www_url=data.get("www_url", ""),
            created_at=int(data.get("created_at", 0)),
        )

    @property
    def formatted_date(self) -> str:
        """获取格式化的日期时间字符串。

        Returns:
            str: 格式化的日期时间，格式为'YYYY-MM-DD HH:MM:SS'
        """
        from datetime import datetime

        if not self.created_at:
            return ""

        # 雪球时间戳是毫秒级
        try:
            dt = datetime.fromtimestamp(self.created_at / 1000)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OverflowError):
            return ""


@dataclass
class XueqiuHotSearchResponse:
    """雪球热搜响应模型。"""

    items: List[Any]
    """热搜条目列表。"""

    last_list_time: int
    """上次列表时间。"""

    next_refresh_time: int
    """下次刷新时间。"""

    version: int
    """版本号。"""

    current_page: int
    """当前页码。"""

    total_page: int
    """总页数。"""

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], item_type: str = "topic"
    ) -> "XueqiuHotSearchResponse":
        """从字典创建实例。

        Args:
            data: API响应数据
            item_type: 条目类型，可选值：topic, news, notice

        Returns:
            XueqiuHotSearchResponse: 实例
        """
        if "data" not in data:
            return cls([], 0, 0, 0, 0, 0)

        api_data = data["data"]

        # 解析list字段（JSON字符串）
        list_str = api_data.get("list", "[]")
        if isinstance(list_str, str):
            try:
                items_raw = json.loads(list_str)
            except json.JSONDecodeError:
                items_raw = []
        else:
            items_raw = list_str

        # 根据类型创建不同的条目
        if item_type == "topic":
            items = [XueqiuTopicItem.from_dict(item) for item in items_raw]
        elif item_type == "news":
            items = [XueqiuNewsItem.from_dict(item) for item in items_raw]
        elif item_type == "notice":
            items = [XueqiuNoticeItem.from_dict(item) for item in items_raw]
        else:
            items = []

        return cls(
            items=items,
            last_list_time=api_data.get("last_list_time", 0),
            next_refresh_time=api_data.get("next_refresh_time", 0),
            version=api_data.get("version", 0),
            current_page=api_data.get("current_page", 0),
            total_page=api_data.get("total_page", 0),
        )
