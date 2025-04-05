"""数据模型模块。

包含各类热榜的数据模型。
"""

from .baidu_tieba import BaiduTiebaHotTopics, BaiduTiebaHotTopicItem
from .xueqiu import (
    XueqiuHotSearchResponse,
    XueqiuTopicItem,
    XueqiuNewsItem,
    XueqiuNoticeItem,
    XueqiuStock,
)
from .bilibili import BilibiliItem, BilibiliHotTopics
from .xiaohongshu import XiaohongshuHotSearch, XiaohongshuHotSearchItem
from .baidu import BaiduHotSearchItem, BaiduHotSearchResponse
from .ne_news import NetEaseNewsHotSearchItem, NetEaseNewsHotSearchResponse
from .tencent_news import TencentNewsHotSearchItem, TencentNewsHotSearchResponse
from .juejin import JuejinHotItem, JuejinHotTopics
from .top import TopHotSearchItem, TopHotSearchResponse
from .thepaper import ThePaperItem, ThePaperHotTopics
from .toutiao import ToutiaoHotSearchItem, ToutiaoHotTopics

__all__ = [
    "BaiduTiebaHotTopics",
    "BaiduTiebaHotTopicItem",
    "XueqiuHotSearchResponse",
    "XueqiuTopicItem",
    "XueqiuNewsItem",
    "XueqiuNoticeItem",
    "XueqiuStock",
    "BilibiliItem",
    "BilibiliHotTopics",
    "XiaohongshuHotSearch",
    "XiaohongshuHotSearchItem",
    "BaiduHotSearchItem",
    "BaiduHotSearchResponse",
    "NetEaseNewsHotSearchItem",
    "NetEaseNewsHotSearchResponse",
    "TencentNewsHotSearchItem",
    "TencentNewsHotSearchResponse",
    "JuejinHotItem",
    "JuejinHotTopics",
    "TopHotSearchItem",
    "TopHotSearchResponse",
    "ThePaperItem",
    "ThePaperHotTopics",
    "ToutiaoHotSearchItem",
    "ToutiaoHotTopics",
]

"""热榜API数据模型。"""
