#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
解析器工具，用于解析网页内容
"""

import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_hot_items(soup, highlighted_elements=None):
    """
    解析热榜条目，特别标记红框内容

    Args:
        soup (BeautifulSoup): BeautifulSoup对象
        highlighted_elements (list): 红框元素列表

    Returns:
        list: 热榜条目列表
    """
    hot_items = []

    try:
        # 找到内容列表项
        list_items = soup.select("main li")

        if not list_items:
            logger.debug("未找到热榜条目，尝试其他选择器")
            # 尝试其他可能的选择器
            list_items = (
                soup.select("article")
                or soup.select(".chakra-container article")
                or soup.select("main > div")
            )

        logger.debug(f"找到 {len(list_items)} 个热榜条目")

        # 创建红框内容的文本列表，用于后续匹配
        highlighted_texts = []
        if highlighted_elements:
            for elem in highlighted_elements:
                if elem["text"].strip():
                    highlighted_texts.append(elem["text"].strip())

        for idx, item in enumerate(list_items, 1):
            try:
                # 提取标题
                title_elem = item.select_one("h2")
                title = title_elem.text.strip() if title_elem else "无标题"

                # 提取链接
                link_elem = item.select_one("a")
                link = link_elem.get("href", "") if link_elem else ""

                # 提取描述/内容
                desc_elem = item.select_one("p")
                description = desc_elem.text.strip() if desc_elem else ""

                # 提取来源
                source_elem = item.select_one(".text-xs")
                source = source_elem.text.strip() if source_elem else ""

                # 提取热度/点赞数
                hot_elem = item.select_one(".stroke-current, .space-x-1")
                hot_value = ""
                if hot_elem:
                    hot_text = hot_elem.text.strip()
                    # 使用正则表达式提取数字
                    hot_match = re.search(r"\d+", hot_text)
                    if hot_match:
                        hot_value = hot_match.group()

                # 提取图片URL
                img_elem = item.select_one("img")
                image_url = img_elem.get("src", "") if img_elem else ""
                # 过滤掉 base64 和占位图片
                if image_url and ("data:image" in image_url or "base64" in image_url):
                    # 尝试找到data-src属性
                    image_url = img_elem.get("data-src", "")

                # 检查是否是红框内容
                is_highlighted = False
                item_html = str(item)
                item_text = item.text.strip()

                # 检查当前元素是否在红框元素中
                if highlighted_texts:
                    for h_text in highlighted_texts:
                        if h_text in item_text or item_text in h_text:
                            is_highlighted = True
                            break

                # 如果还没确定是高亮，检查HTML中是否有border或红色相关样式
                if not is_highlighted and (
                    "border" in item_html.lower()
                    and ("red" in item_html.lower() or "highlight" in item_html.lower())
                ):
                    is_highlighted = True

                hot_item = {
                    "rank": idx,
                    "title": title,
                    "link": link,
                    "description": description,
                    "source": source,
                    "hot_value": hot_value,
                    "image_url": image_url,
                    "is_highlighted": is_highlighted,
                }

                hot_items.append(hot_item)
            except Exception as e:
                logger.error(f"解析热榜条目 #{idx} 失败: {str(e)}")

    except Exception as e:
        logger.error(f"解析热榜条目失败: {str(e)}")

    return hot_items
