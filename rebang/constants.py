#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
常量定义模块
"""

# 所有可用的标签列表
AVAILABLE_TABS = [
    "top",
    "zhihu",
    "weibo",
    "ithome",
    "hupu",
    "tencent-news",
    "douban-community",
    "huxiu",
    "sspai",
    "thepaper",
    "xiaohongshu",
    "36kr",
    "toutiao",
    "ifanr",
    "douban-media",
    "smzdm",
    "baidu",
    "penti",
    "ne-news",
    "weread",
    "zhihu-daily",
    "baidu-tieba",
    "52pojie",
    "guancha-user",
    "xueqiu",
    "landian",
    "appinn",
    "apprcn",
    "zhibo8",
    "douyin",
    "bilibili",
    "xmyp",
    "gamersky",
    "juejin",
    "journal-tech",
    "github",
]

# 标签分类
TAB_CATEGORIES = {
    "社交媒体": ["weibo", "douyin", "xiaohongshu", "bilibili"],
    "科技": [
        "ithome",
        "ifanr",
        "36kr",
        "landian",
        "appinn",
        "apprcn",
        "journal-tech",
        "github",
        "juejin",
    ],
    "社区论坛": [
        "douban-community",
        "hupu",
        "baidu-tieba",
        "douban-media",
        "52pojie",
        "guancha-user",
    ],
    "新闻资讯": ["tencent-news", "thepaper", "toutiao", "ne-news", "penti"],
    "财经": ["xueqiu", "smzdm"],
    "知识文化": ["zhihu", "zhihu-daily", "weread", "huxiu", "sspai"],
    "体育游戏": ["zhibo8", "gamersky", "xmyp"],
    "综合": ["top", "baidu"],
}

# 网站基础URL
BASE_URL = "https://rebang.today"

# 用户代理
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
