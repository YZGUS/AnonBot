"""热榜API客户端实现。

提供基础客户端类和通用请求方法。
"""

import json
import os
import requests
from typing import Dict, List, Any, Optional, Union


class HotSearchClient:
    """热榜API基础客户端类。"""

    BASE_URL = "https://api.rebang.today/v1/items"
    DEFAULT_AUTH_TOKEN = "Bearer b4abc833-112a-11f0-8295-3292b700066c"

    def __init__(
        self,
        auth_token: Optional[str] = None,
        save_data: bool = True,
        data_dir: str = "./data",
    ):
        """初始化热榜客户端。

        Args:
            auth_token: 授权令牌，格式为"Bearer xxx"，为None时使用默认令牌（不推荐）
            save_data: 是否保存请求的原始数据
            data_dir: 保存数据的目录
        """
        self.auth_token = auth_token or self.DEFAULT_AUTH_TOKEN
        self.save_data = save_data
        self.data_dir = data_dir

        if save_data and not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头。

        Returns:
            Dict[str, str]: 请求头字典
        """
        return {
            "accept": "application/json",
            "accept-language": "zh-CN,zh;q=0.9",
            "authorization": self.auth_token,
            "origin": "https://rebang.today",
            "referer": "https://rebang.today/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        }

    def request(
        self,
        tab: str,
        sub_tab: str,
        page: int = 1,
        version: int = 1,
        date_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """发送API请求。

        Args:
            tab: 热榜分类
            sub_tab: 热榜子分类
            page: 页码
            version: API版本
            date_type: 日期类型，部分API需要

        Returns:
            Dict[str, Any]: API响应的JSON数据
        """
        params = {"tab": tab, "sub_tab": sub_tab, "page": page, "version": version}

        if date_type:
            params["date_type"] = date_type

        response = requests.get(
            self.BASE_URL, headers=self._get_headers(), params=params
        )

        response.raise_for_status()
        data = response.json()

        if self.save_data:
            self._save_data(tab, sub_tab, data)

        return data

    def _save_data(self, tab: str, sub_tab: str, data: Dict[str, Any]):
        """保存请求的原始数据。

        Args:
            tab: 热榜分类
            sub_tab: 热榜子分类
            data: 要保存的数据
        """
        directory = os.path.join(self.data_dir, tab)
        if not os.path.exists(directory):
            os.makedirs(directory)

        filename = f"{sub_tab}.json"
        filepath = os.path.join(directory, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
