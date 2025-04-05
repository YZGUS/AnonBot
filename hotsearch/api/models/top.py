"""热榜综合数据模型。

提供热榜综合数据的模型类。
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class TopHotSearchItem:
    """热榜综合条目数据结构"""

    title: str
    link: str
    item_key: str
    hot_value: int
    hot_value_format: str
    icon: Optional[str] = None
    is_ad: Optional[bool] = False

    @property
    def is_popular(self) -> bool:
        """判断是否为热门条目"""
        return self.hot_value > 10000

    @property
    def formatted_hot_value(self) -> str:
        """获取格式化的热度数值"""
        return self.hot_value_format

    def get_full_icon_url(self) -> str:
        """获取完整图标URL"""
        if not self.icon:
            return ""

        if self.icon.startswith(("http://", "https://")):
            return self.icon

        return f"https://rebang.today/icons/{self.icon}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopHotSearchItem":
        """从字典创建对象

        Args:
            data: 数据字典

        Returns:
            TopHotSearchItem: 热榜综合条目对象
        """
        # 处理API返回的热度值字段，可能是hot_value或heat_num
        hot_value_raw = data.get("hot_value", data.get("heat_num", 0))

        # 安全地转换热度值为整数
        try:
            hot_value = int(float(hot_value_raw))
        except (ValueError, TypeError):
            hot_value = 0

        # 热度格式化字段
        hot_value_format = data.get("hot_value_format", "")
        # 如果没有格式化热度，尝试使用原热度值
        if not hot_value_format and hot_value > 0:
            if hot_value >= 10000:
                hot_value_format = f"{hot_value/10000:.1f}万"
            else:
                hot_value_format = str(hot_value)

        # 安全地转换广告标记为布尔值
        is_ad = data.get("is_ad", False)
        if isinstance(is_ad, str):
            is_ad = is_ad.lower() in ("true", "1", "yes")

        # 处理标题和链接字段
        title = data.get("title", "")
        # 处理链接字段，可能是link或mobile_url或www_url
        link = data.get("link", data.get("mobile_url", data.get("www_url", "")))
        # 处理条目ID，可能是item_key或id
        item_key = data.get("item_key", data.get("id", ""))
        # 处理图标字段，可能是icon或img
        icon = data.get("icon", data.get("img", None))

        return cls(
            title=title,
            link=link,
            item_key=item_key,
            hot_value=hot_value,
            hot_value_format=hot_value_format,
            icon=icon,
            is_ad=is_ad,
        )


@dataclass
class TopHotSearchResponse:
    """热榜综合响应数据结构"""

    items: List[TopHotSearchItem]
    tab: str
    sub_tab: str
    page: int
    total_page: int
    current_page: int
    last_update_time: Optional[int] = None
    next_refresh_time: Optional[int] = None

    @property
    def has_next_page(self) -> bool:
        """判断是否有下一页"""
        return self.current_page < self.total_page

    @property
    def item_count(self) -> int:
        """获取条目数量"""
        return len(self.items)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TopHotSearchResponse":
        """从字典创建对象

        Args:
            data: API响应数据

        Returns:
            TopHotSearchResponse: 热榜综合响应对象
        """
        api_data = data.get("data", {})

        # 解析items列表
        items_list = []
        # 优先尝试获取items字段，如果不存在则尝试获取list字段
        items_raw = api_data.get("items", api_data.get("list", []))

        # 处理可能的JSON字符串
        if isinstance(items_raw, str):
            try:
                items_raw = json.loads(items_raw)
            except json.JSONDecodeError:
                items_raw = []

        # 确保items_raw是列表
        if not isinstance(items_raw, list):
            items_raw = []

        # 创建条目对象列表
        items_list = [TopHotSearchItem.from_dict(item) for item in items_raw]

        # 构建响应对象
        return cls(
            items=items_list,
            tab="top",  # 固定为top
            sub_tab=api_data.get("sub_tab", ""),
            page=api_data.get("current_page", 1),
            total_page=api_data.get("total_page", 1),
            current_page=api_data.get("current_page", 1),
            last_update_time=api_data.get("last_update_time"),
            next_refresh_time=api_data.get("next_refresh_time"),
        )
