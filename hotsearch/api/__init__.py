"""API模块。

包含各类热榜的具体客户端实现。
"""

from .baidu import BaiduClient, BaiduHotSearchResponse, BaiduHotSearchItem
from .baidu_tieba import BaiduTiebaClient
from .models import BaiduTiebaHotTopics, BaiduTiebaHotTopicItem
from .ne_news import (
    NetEaseNewsClient,
    NetEaseNewsHotSearchResponse,
    NetEaseNewsHotSearchItem,
)
from .tencent_news import (
    TencentNewsClient,
    TencentNewsHotSearchResponse,
    TencentNewsHotSearchItem,
)
from .xueqiu import XueqiuClient
from .models import (
    XueqiuHotSearchResponse,
    XueqiuTopicItem,
    XueqiuNewsItem,
    XueqiuNoticeItem,
    XueqiuStock,
)
from .bilibili import BilibiliClient
from .models import BilibiliItem, BilibiliHotTopics
from .thepaper import ThePaperClient
from .models import ThePaperItem, ThePaperHotTopics
from .top import TopClient
from .models import TopHotSearchItem, TopHotSearchResponse
from .toutiao import ToutiaoClient
from .models import ToutiaoHotSearchItem, ToutiaoHotTopics

__all__ = [
    "BaiduClient",
    "BaiduHotSearchResponse",
    "BaiduHotSearchItem",
    "BaiduTiebaClient",
    "BaiduTiebaHotTopics",
    "BaiduTiebaHotTopicItem",
    "NetEaseNewsClient",
    "NetEaseNewsHotSearchResponse",
    "NetEaseNewsHotSearchItem",
    "TencentNewsClient",
    "TencentNewsHotSearchResponse",
    "TencentNewsHotSearchItem",
    "XueqiuClient",
    "XueqiuHotSearchResponse",
    "XueqiuTopicItem",
    "XueqiuNewsItem",
    "XueqiuNoticeItem",
    "XueqiuStock",
    "BilibiliClient",
    "BilibiliItem",
    "BilibiliHotTopics",
    "ThePaperClient",
    "ThePaperItem",
    "ThePaperHotTopics",
    "TopClient",
    "TopHotSearchItem",
    "TopHotSearchResponse",
    "ToutiaoClient",
    "ToutiaoHotSearchItem",
    "ToutiaoHotTopics",
]
