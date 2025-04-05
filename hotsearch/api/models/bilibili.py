"""B站热搜数据模型。

提供B站热搜数据的模型类定义。
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class BilibiliItem:
    """B站热门条目模型。"""

    item_key: str
    title: str
    describe: str
    bvid: str
    pic: str
    owner_name: str
    owner_mid: int
    danmaku: int
    view: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BilibiliItem":
        """从字典数据创建模型实例。

        Args:
            data: 原始字典数据

        Returns:
            BilibiliItem: 模型实例
        """
        if data is None or not isinstance(data, dict):
            return cls("", "", "", "", "", "", 0, 0, 0)

        # 安全获取字段，确保类型转换和处理None值
        item_key = data.get("item_key", "")
        item_key = "" if item_key is None else str(item_key)

        title = data.get("title", "")
        title = "" if title is None else str(title)

        describe = data.get("describe", "")
        describe = "" if describe is None else str(describe)

        bvid = data.get("bvid", "")
        bvid = "" if bvid is None else str(bvid)

        pic = data.get("pic", "")
        pic = "" if pic is None else str(pic)

        owner_name = data.get("owner_name", "")
        owner_name = "" if owner_name is None else str(owner_name)

        try:
            owner_mid = int(data.get("owner_mid", 0))
        except (ValueError, TypeError):
            owner_mid = 0

        try:
            danmaku = int(data.get("danmaku", 0))
        except (ValueError, TypeError):
            danmaku = 0

        try:
            view = int(data.get("view", 0))
        except (ValueError, TypeError):
            view = 0

        return cls(
            item_key=item_key,
            title=title,
            describe=describe,
            bvid=bvid,
            pic=pic,
            owner_name=owner_name,
            owner_mid=owner_mid,
            danmaku=danmaku,
            view=view,
        )

    @property
    def video_url(self) -> str:
        """获取视频URL。

        Returns:
            str: 视频链接
        """
        if not self.bvid:
            return ""
        return f"https://www.bilibili.com/video/{self.bvid}"

    @property
    def owner_url(self) -> str:
        """获取UP主主页URL。

        Returns:
            str: UP主主页链接
        """
        if not self.owner_mid:
            return ""
        return f"https://space.bilibili.com/{self.owner_mid}"

    @property
    def full_pic_url(self) -> str:
        """获取完整图片URL。

        Returns:
            str: 完整图片链接
        """
        if not self.pic:
            return ""

        if self.pic.startswith(("http://", "https://")):
            return self.pic

        # 避免重复添加域名前缀
        return f"https://rebang.today/assets/{self.pic}"

    @property
    def popularity_level(self) -> str:
        """获取热门程度等级。

        Returns:
            str: 热门等级
        """
        if self.view > 1000000:  # 超过100万播放
            return "极热门"
        elif self.view > 500000:  # 超过50万播放
            return "很热门"
        elif self.view > 100000:  # 超过10万播放
            return "热门"
        elif self.view > 10000:  # 超过1万播放
            return "较热门"
        else:
            return "一般"


@dataclass
class BilibiliHotTopics:
    """B站热门话题集合模型。"""

    items: List[BilibiliItem]
    last_list_time: int
    next_refresh_time: int
    version: int
    current_page: int
    total_page: int
    code: int
    msg: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BilibiliHotTopics":
        """从API响应创建模型实例。

        Args:
            data: API响应字典

        Returns:
            BilibiliHotTopics: 模型实例
        """
        if data is None or not isinstance(data, dict):
            return cls([], 0, 0, 0, 0, 0, 0, "")

        code = data.get("code", 0)
        msg = data.get("msg", "")

        if "data" not in data:
            return cls([], 0, 0, 0, 0, 0, code, msg)

        api_data = data["data"]

        # 提取列表数据
        items = []
        if "list" in api_data:
            list_data = api_data["list"]

            # 处理JSON字符串
            if isinstance(list_data, str):
                try:
                    list_data = json.loads(list_data)
                except:
                    list_data = []

            if isinstance(list_data, list):
                items = [BilibiliItem.from_dict(item) for item in list_data]

        # 安全获取其他字段，确保类型转换
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
            code=code,
            msg=msg,
        )
