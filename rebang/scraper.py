#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
热榜 Today 网站爬虫模块

实现从热榜 Today 网站抓取特定标签页的热榜数据
"""

import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup

from rebang.constants import BASE_URL, AVAILABLE_TABS
from rebang.utils.browser import fetch_page
from rebang.utils.parser import parse_hot_items

# 配置日志
logger = logging.getLogger(__name__)


class RebangScraper:
    """热榜 Today 网站爬虫类"""

    def __init__(self, log_level=logging.INFO):
        """
        初始化爬虫

        Args:
            log_level: 日志级别
        """
        self.setup_logger(log_level)

    def setup_logger(self, log_level):
        """
        设置日志

        Args:
            log_level: 日志级别
        """
        # 配置根日志记录器
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        # 设置模块日志级别
        logger.setLevel(log_level)

    def fetch_data(self, tab):
        """
        抓取指定标签的数据

        Args:
            tab (str): 标签名称

        Returns:
            dict: 抓取的数据

        Raises:
            ValueError: 当提供的标签无效时
            ConnectionError: 当网络连接出错时
            Exception: 其他错误
        """
        if tab not in AVAILABLE_TABS:
            available_tabs_str = ", ".join(AVAILABLE_TABS)
            raise ValueError(f"无效的标签: {tab}。可用标签: {available_tabs_str}")

        try:
            # 构建URL
            url = f"{BASE_URL}/home?tab={tab}"
            logger.info(f"开始抓取标签: {tab}, URL: {url}")

            # 获取页面数据
            page_data = fetch_page(url)

            if not page_data:
                raise ConnectionError(f"无法获取页面数据: {url}")

            # 解析页面内容
            soup = BeautifulSoup(page_data["page_source"], "html.parser")

            # 解析热榜条目
            hot_items = parse_hot_items(soup, page_data.get("highlighted_elements", []))

            # 构建结果数据
            result = {
                "site_name": "热榜 Today",
                "tab": tab,
                "url": url,
                "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hot_items": hot_items,
                "highlighted_count": len(
                    [item for item in hot_items if item.get("is_highlighted", False)]
                ),
            }

            logger.info(f"成功抓取标签: {tab}, 共 {len(hot_items)} 条内容")

            return result

        except Exception as e:
            logger.error(f"抓取标签 {tab} 失败: {str(e)}")
            raise

    def fetch_data_json(self, tab):
        """
        抓取指定标签的数据并返回JSON字符串

        Args:
            tab (str): 标签名称

        Returns:
            str: JSON格式的数据字符串
        """
        try:
            data = self.fetch_data(tab)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            error_data = {
                "error": True,
                "message": str(e),
                "tab": tab,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            return json.dumps(error_data, ensure_ascii=False, indent=2)


# 模块级别的便捷函数
def get_tab_data(tab):
    """
    获取指定标签的数据

    Args:
        tab (str): 标签名称

    Returns:
        dict: 抓取的数据
    """
    scraper = RebangScraper()
    return scraper.fetch_data(tab)


def get_tab_data_json(tab):
    """
    获取指定标签的数据，以JSON字符串返回

    Args:
        tab (str): 标签名称

    Returns:
        str: JSON格式的数据字符串
    """
    scraper = RebangScraper()
    return scraper.fetch_data_json(tab)
