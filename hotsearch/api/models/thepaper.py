"""澎湃新闻数据模型。

提供澎湃新闻热榜数据的模型类定义。
"""

import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class ThePaperItem:
    """澎湃新闻条目模型。"""

    item_key: str
    id: str
    title: str
    desc: str
    comment_num: int
    image: str
    pub_time: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThePaperItem":
        """从字典数据创建模型实例。

        Args:
            data: 原始字典数据

        Returns:
            ThePaperItem: 模型实例
        """
        if data is None or not isinstance(data, dict):
            return cls("", "", "", "", 0, "", 0)

        # 安全获取字段，确保类型转换和处理None值
        item_key = data.get("item_key", "")
        item_key = "" if item_key is None else str(item_key)

        id_value = data.get("id", "")
        id_value = "" if id_value is None else str(id_value)

        title = data.get("title", "")
        title = "" if title is None else str(title)

        desc = data.get("desc", "")
        desc = "" if desc is None else str(desc)

        # 评论数可能为空字符串或缺失
        comment_num_str = data.get("comment_num", "0")
        try:
            comment_num = int(comment_num_str) if comment_num_str else 0
        except (ValueError, TypeError):
            comment_num = 0

        image = data.get("image", "")
        image = "" if image is None else str(image)

        # 发布时间处理
        try:
            pub_time = int(data.get("pub_time", 0))
        except (ValueError, TypeError):
            pub_time = 0

        return cls(
            item_key=item_key,
            id=id_value,
            title=title,
            desc=desc,
            comment_num=comment_num,
            image=image,
            pub_time=pub_time,
        )

    @property
    def article_url(self) -> str:
        """获取文章URL。

        Returns:
            str: 文章链接
        """
        if not self.id:
            return ""
        return f"https://www.thepaper.cn/newsDetail_{self.id}"

    @property
    def full_image_url(self) -> str:
        """获取完整图片URL。

        Returns:
            str: 完整图片链接
        """
        if not self.image:
            return ""

        if self.image.startswith(("http://", "https://")):
            return self.image

        # 避免重复添加域名前缀
        return f"https://rebang.today/assets/{self.image}"


@dataclass
class ThePaperHotTopics:
    """澎湃新闻热门话题集合模型。"""

    items: List[ThePaperItem]
    last_list_time: int
    next_refresh_time: int
    version: int
    current_page: int
    total_page: int
    code: int
    msg: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThePaperHotTopics":
        """从API响应创建模型实例。

        Args:
            data: API响应字典

        Returns:
            ThePaperHotTopics: 模型实例
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
                except json.JSONDecodeError:
                    list_data = []

            if isinstance(list_data, list):
                items = [ThePaperItem.from_dict(item) for item in list_data]

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
