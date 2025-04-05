"""小红书数据模型。

提供小红书热搜数据的模型类。
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class XiaohongshuHotSearchItem:
    """小红书热搜条目模型。"""

    item_key: str  # 条目唯一标识
    title: str  # 热搜标题
    view_num: str  # 浏览数量
    tag: str  # 标签，如"新"、"热"、"无"、"独家"等
    www_url: str  # 网页链接

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XiaohongshuHotSearchItem":
        """从字典创建实例。

        Args:
            data: 包含条目数据的字典

        Returns:
            XiaohongshuHotSearchItem: 条目实例
        """
        return cls(
            item_key=data.get("item_key", ""),
            title=data.get("title", ""),
            view_num=data.get("view_num", ""),
            tag=data.get("tag", ""),
            www_url=data.get("www_url", ""),
        )

    @property
    def views(self) -> int:
        """获取浏览数值。

        Returns:
            int: 浏览数值，解析失败时返回0
        """
        try:
            # 解析类似"936.1万"的格式
            if "万" in self.view_num:
                number = float(self.view_num.replace("万", ""))
                return int(number * 10000)
            return int(self.view_num)
        except (ValueError, TypeError):
            return 0

    @property
    def is_new(self) -> bool:
        """是否为新热搜。

        Returns:
            bool: 是否为新上榜的热搜
        """
        return self.tag == "新"

    @property
    def is_hot(self) -> bool:
        """是否为热门热搜。

        Returns:
            bool: 是否为热门热搜
        """
        return self.tag == "热"

    @property
    def is_exclusive(self) -> bool:
        """是否为独家热搜。

        Returns:
            bool: 是否为独家热搜
        """
        return self.tag == "独家"

    @property
    def tag_type(self) -> str:
        """获取标签类型的描述。

        Returns:
            str: 标签类型描述
        """
        tag_map = {"新": "新上榜", "热": "热门", "独家": "独家", "无": "普通"}
        return tag_map.get(self.tag, "普通")


@dataclass
class XiaohongshuHotSearch:
    """小红书热搜数据模型。"""

    items: List[XiaohongshuHotSearchItem]  # 热搜条目列表
    last_list_time: int  # 上次列表时间
    next_refresh_time: int  # 下次刷新时间
    version: int  # 版本号
    current_page: int  # 当前页码
    total_page: int  # 总页数

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "XiaohongshuHotSearch":
        """从API响应字典创建实例。

        Args:
            data: API响应字典

        Returns:
            XiaohongshuHotSearch: 热搜数据模型实例
        """
        if "data" not in data:
            return cls([], 0, 0, 0, 0, 0)

        api_data = data["data"]

        # 解析list字段（包含在JSON字符串中）
        list_str = api_data.get("list", "[]")
        try:
            # 尝试解析JSON字符串
            if isinstance(list_str, str):
                items_raw = json.loads(list_str)
            else:
                items_raw = list_str

            items = [XiaohongshuHotSearchItem.from_dict(item) for item in items_raw]
        except json.JSONDecodeError:
            items = []

        return cls(
            items=items,
            last_list_time=api_data.get("last_list_time", 0),
            next_refresh_time=api_data.get("next_refresh_time", 0),
            version=api_data.get("version", 0),
            current_page=api_data.get("current_page", 0),
            total_page=api_data.get("total_page", 0),
        )
