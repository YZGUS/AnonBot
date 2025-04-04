#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
浏览器相关工具函数
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from rebang.constants import USER_AGENT

logger = logging.getLogger(__name__)


def get_browser():
    """
    获取配置好的浏览器实例

    Returns:
        webdriver: 配置好的Chrome浏览器实例
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"--user-agent={USER_AGENT}")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"创建浏览器实例失败: {str(e)}")
        raise


def fetch_page(url, wait_time=15, render_time=3):
    """
    获取页面内容

    Args:
        url (str): 要获取的页面URL
        wait_time (int): 等待页面加载的最大时间(秒)
        render_time (int): 等待JavaScript渲染完成的额外时间(秒)

    Returns:
        dict: 页面数据，包含page_source和截获的红框元素等
    """
    driver = None
    try:
        driver = get_browser()
        driver.get(url)

        # 等待页面加载
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))

        # 等待JavaScript渲染完成
        time.sleep(render_time)

        # 获取页面源码
        page_source = driver.page_source

        # 查找红框元素
        highlighted_elements = find_highlighted_elements(driver)

        result = {
            "page_source": page_source,
            "url": url,
            "highlighted_elements": highlighted_elements,
        }

        driver.quit()
        return result

    except Exception as e:
        logger.error(f"获取页面数据失败: {str(e)}")
        if driver:
            driver.quit()
        raise


def find_highlighted_elements(driver):
    """
    查找页面中的红框元素

    Args:
        driver (webdriver): 浏览器实例

    Returns:
        list: 红框元素列表
    """
    highlighted_elements = []

    try:
        # 红框内容可能有特殊的CSS类，例如带有border或特殊样式的元素
        potential_highlight_selectors = [
            ".border-red-500",
            ".border-2",
            ".border-red",
            "article.border",
            "article[style*='border']",
            "li.border",
            "li[style*='border']",
            "div.border-solid",
            "div.highlight",
            "a[style*='border']",
            ".highlight-item",
            ".text-red-500",
            ".text-red-600",
            ".text-red-700",
            "[style*='color: red']",
            "[style*='color:#ff']",
            ".text-primary",
            ".text-danger",
            "div.border-red-600",
            "div.ring-2",
            "div.ring-red-600",
            "div.bg-red-50",
            "li.border-red-600",
            "div[class*='border'][class*='red']",
            "li[class*='border'][class*='red']",
        ]

        for selector in potential_highlight_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.debug(
                    f"找到可能的红框元素 (选择器: {selector}): {len(elements)}个"
                )
                for elem in elements:
                    try:
                        elem_html = elem.get_attribute("outerHTML")
                        elem_text = elem.text
                        highlighted_elements.append(
                            {"selector": selector, "text": elem_text, "html": elem_html}
                        )
                    except:
                        pass

        # 如果上面的方法没找到，尝试查找所有可能包含红框样式的元素
        if not highlighted_elements:
            all_elements = driver.find_elements(By.CSS_SELECTOR, "*[style]")
            for elem in all_elements:
                try:
                    style = elem.get_attribute("style")
                    if style and (
                        (
                            "border" in style.lower()
                            and ("red" in style.lower() or "#f" in style.lower())
                        )
                        or (
                            "outline" in style.lower()
                            and ("red" in style.lower() or "#f" in style.lower())
                        )
                        or (
                            "box-shadow" in style.lower()
                            and ("red" in style.lower() or "#f" in style.lower())
                        )
                    ):
                        elem_html = elem.get_attribute("outerHTML")
                        elem_text = elem.text
                        highlighted_elements.append(
                            {
                                "selector": "style[border/outline/shadow+red]",
                                "text": elem_text,
                                "html": elem_html,
                            }
                        )
                except:
                    pass

        # 特别检查父元素包含特定类名的元素
        parent_highlight_selectors = [
            "div.border-red-600 *",
            "div.ring-red-600 *",
            "div.bg-red-50 *",
            "li.border-red-600 *",
        ]

        for selector in parent_highlight_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.debug(
                    f"找到可能的红框内部元素 (选择器: {selector}): {len(elements)}个"
                )
                for elem in elements:
                    try:
                        # 检查该元素是否有意义的内容
                        elem_text = elem.text.strip()
                        if elem_text and len(elem_text) > 5:
                            elem_html = elem.get_attribute("outerHTML")
                            highlighted_elements.append(
                                {
                                    "selector": selector,
                                    "text": elem_text,
                                    "html": elem_html,
                                }
                            )
                    except:
                        pass
    except Exception as e:
        logger.error(f"查找红框内容失败: {str(e)}")

    return highlighted_elements
