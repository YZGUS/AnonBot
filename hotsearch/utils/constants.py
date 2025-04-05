#!/usr/bin/env python
# -*- coding: utf-8 -*-

class HotSearchCategory:
    """热榜API类别和端点常量定义"""
    
    class News:
        """新闻类热榜"""
        
        class Top:
            """热榜综合"""
            BASE = "top"
            TODAY = "today"
            WEEKLY = "weekly"
            MONTHLY = "monthly"
        
        class TencentNews:
            """腾讯新闻"""
            BASE = "tencent-news"
            HOT = "hot"
        
        class ThePaper:
            """澎湃新闻"""
            BASE = "thepaper"
            HOT = "hot"
        
        class Toutiao:
            """今日头条"""
            BASE = "toutiao"
            HOT = "hot"
        
        class NetEaseNews:
            """网易新闻"""
            BASE = "ne-news"
            NEWS = "news"
            HTD = "htd"
        
        class Baidu:
            """百度热搜"""
            BASE = "baidu"
            REALTIME = "realtime"
            PHRASE = "phrase"
            NOVEL = "novel"
            GAME = "game"
            CAR = "car"
            TELEPLAY = "teleplay"
    
    class Finance:
        """财经类热榜"""
        
        class EastMoney:
            """东方财富"""
            BASE = "eastmoney"
            NEWS = "news"
        
        class SinaFinance:
            """新浪财经"""
            BASE = "sina-fin"
            ALL = "all"
            STOCK = "stock"
            FUTURE = "future"
        
        class Xueqiu:
            """雪球热帖"""
            BASE = "xueqiu"
            TOPIC = "topic"
            NEWS = "news"
            NOTICE = "notice"
    
    class Tech:
        """科技类热榜"""
        
        class Kr36:
            """36氪"""
            BASE = "36kr"
            HOTLIST = "hotlist"
            LATEST = "latest"
            NEWSFLASHES = "newsflashes"
        
        class Juejin:
            """掘金"""
            BASE = "juejin"
            ALL = "all"
            BACKEND = "backend"
            FRONTEND = "frontend"
            ANDROID = "android"
            IOS = "ios"
            AI = "ai"
            DEV_TOOLS = "dev-tools"
            CODE_LIFE = "code-life"
            READ = "read"
    
    class Community:
        """社区类热榜"""
        
        class DoubanCommunity:
            """豆瓣社区"""
            BASE = "douban-community"
            DISCUSSION = "discussion"
            TOPIC = "topic"
            GROUP = "group"
        
        class Xiaohongshu:
            """小红书"""
            BASE = "xiaohongshu"
            HOT_SEARCH = "hot-search"
        
        class V2ex:
            """V2EX"""
            BASE = "v2ex"
            HOT = "hot"
            TECH = "tech"
            DEALS = "deals"
            CREATIVE = "creative"
    
    class Entertainment:
        """娱乐类热榜"""
        
        class Hupu:
            """虎扑热帖"""
            BASE = "hupu"
            ALL_GAMBIA = "all-gambia"
            ALL_NBA = "all-nba"
            ALL_GG = "all-gg"
            ALL_DIGITAL = "all-digital"
            ALL_ENT = "all-ent"
            ALL_SOCCER = "all-soccer"
        
        class Bilibili:
            """B站热门"""
            BASE = "bilibili"
            POPULAR = "popular"
            WEEKLY = "weekly"
            RANK = "rank"