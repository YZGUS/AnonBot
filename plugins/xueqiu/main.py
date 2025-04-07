#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from hotsearch.api import XueqiuClient
from hotsearch.api.models.xueqiu import (
    XueqiuTopicItem,
    XueqiuNewsItem,
    XueqiuNoticeItem,
)
from utils import scheduler

# 配置日志
logger = logging.getLogger("xueqiu")

# 兼容装饰器
bot = CompatibleEnrollment


@dataclass
class Config:
    """配置类"""

    whitelist_groups: List[int]  # 允许使用的群组ID列表
    whitelist_users: List[int]  # 允许使用的用户ID列表
    hot_count: int  # 热榜数量
    news_count: int  # 新闻数量
    notice_count: int  # 公告数量
    update_interval: int  # 数据更新间隔
    keep_days: int  # 保留数据天数
    save_data: bool  # 是否保存数据

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})
        storage = config_dict.get("storage", {})

        return cls(
            whitelist_groups=whitelist.get("group_ids", []),
            whitelist_users=whitelist.get("user_ids", []),
            hot_count=data.get("hot_count", 20),
            news_count=data.get("news_count", 10),
            notice_count=data.get("notice_count", 10),
            update_interval=data.get("update_interval", 300),
            keep_days=storage.get("keep_days", 7),
            save_data=storage.get("save_data", True),
        )


class XueqiuPlugin(BasePlugin):
    """雪球财经热榜插件 - 获取雪球实时财经热榜数据"""

    name = "XueqiuPlugin"  # 插件名称
    version = "1.0.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    xueqiu_client = None
    latest_topic_data = None
    latest_news_data = None
    latest_notice_data = None

    async def on_load(self):
        """插件加载时执行"""
        # 初始化插件
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 初始化雪球客户端
        self.init_xueqiu_client()

        # 设置定时任务
        scheduler.add_random_minute_task(self.fetch_xueqiu_data, 0, 5)

        # 立即执行一次数据获取
        await self.fetch_xueqiu_data()

    def load_config(self) -> None:
        """加载配置"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            with open(self.config_path, "rb") as f:
                config_dict = tomllib.load(f)

            self.config = Config.from_dict(config_dict)
            self.config_last_modified = self.config_path.stat().st_mtime
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 使用默认配置
            self.config = Config.from_dict({})

    def init_xueqiu_client(self) -> None:
        """初始化雪球客户端"""
        try:
            save_data = True if self.config and self.config.save_data else False
            data_dir = str(self.data_dir)

            self.xueqiu_client = XueqiuClient(save_data=save_data, data_dir=data_dir)
        except Exception as e:
            print(f"初始化雪球客户端失败: {e}")

    def check_config_update(self) -> bool:
        """检查配置是否更新"""
        if not self.config_path.exists():
            return False

        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self.config_last_modified:
            self.load_config()
            self.init_xueqiu_client()
            return True
        return False

    def is_user_authorized(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """检查用户是否有权限使用此插件"""
        if not self.config:
            self.load_config()

        # 白名单为空表示允许所有人使用
        if not self.config.whitelist_users and not self.config.whitelist_groups:
            return True

        # 检查用户白名单
        if user_id in self.config.whitelist_users:
            return True

        # 检查群组白名单
        if group_id and group_id in self.config.whitelist_groups:
            return True

        return False

    async def fetch_xueqiu_data(self) -> None:
        """获取雪球数据"""
        try:
            # 检查配置是否更新
            self.check_config_update()

            # 使用XueqiuClient获取数据
            if self.xueqiu_client:
                # 获取话题数据
                self.latest_topic_data = self.xueqiu_client.get_topic(as_model=True)
                # 获取新闻数据
                self.latest_news_data = self.xueqiu_client.get_news(as_model=True)
                # 获取公告数据
                self.latest_notice_data = self.xueqiu_client.get_notice(as_model=True)

                await self.clean_old_files()
        except Exception as e:
            print(f"获取雪球数据失败: {e}")

    async def clean_old_files(self) -> None:
        """清理旧数据文件"""
        try:
            if not self.config or not self.config.save_data:
                return

            # 获取所有日期目录
            date_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]

            # 按创建时间排序
            date_dirs.sort(key=lambda x: x.stat().st_ctime)

            # 保留最近指定天数的数据
            keep_days = self.config.keep_days
            if len(date_dirs) > keep_days:
                for old_dir in date_dirs[:-keep_days]:
                    # 删除旧目录及其中的文件
                    for file in old_dir.glob("*"):
                        os.remove(file)
                    os.rmdir(old_dir)
        except Exception as e:
            print(f"清理旧文件失败: {e}")

    def get_topic_items(self, count: Optional[int] = None) -> List[XueqiuTopicItem]:
        """获取话题条目列表"""
        if not self.xueqiu_client or not self.latest_topic_data:
            return []

        items = self.latest_topic_data.items

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        return items

    def get_news_items(self, count: Optional[int] = None) -> List[XueqiuNewsItem]:
        """获取新闻条目列表"""
        if not self.xueqiu_client or not self.latest_news_data:
            return []

        items = self.latest_news_data.items

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        return items

    def get_notice_items(self, count: Optional[int] = None) -> List[XueqiuNoticeItem]:
        """获取公告条目列表"""
        if not self.xueqiu_client or not self.latest_notice_data:
            return []

        items = self.latest_notice_data.items

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        return items

    def search_topics(self, keyword: str) -> List[XueqiuTopicItem]:
        """搜索话题条目"""
        if not self.xueqiu_client:
            return []

        return self.xueqiu_client.get_topics_by_keyword(keyword)

    def get_timestamp_str(self) -> str:
        """获取格式化的时间戳字符串"""
        # 使用当前时间
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def format_topic_list_message(
            self, items: List[XueqiuTopicItem], count: Optional[int] = None
    ) -> str:
        """格式化话题列表消息"""
        if not items:
            return "❌ 获取雪球热门话题失败，请稍后再试"

        timestamp = self.get_timestamp_str()

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        message = f"📊 雪球热门话题 ({timestamp})\n\n共{len(items)}条热门话题\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            title = item.title
            read_count = item.read_count or "未知"

            # 前三名使用特殊标记
            if rank == 1:
                prefix = "🥇 "
            elif rank == 2:
                prefix = "🥈 "
            elif rank == 3:
                prefix = "🥉 "
            else:
                prefix = f"{rank}. "

            message += f"{prefix}{title} 📖 {read_count}阅读\n"

            # 获取相关股票信息
            if item.stocks:
                stocks_info = []
                for stock in item.stocks[:3]:  # 最多显示3个股票
                    trend = (
                        "📈"
                        if stock.percentage > 0
                        else "📉" if stock.percentage < 0 else "➖"
                    )
                    stocks_info.append(f"{stock.name} {trend} {stock.percentage:.2f}%")
                message += f"🏦 相关股票: {' | '.join(stocks_info)}\n"

            message += f"🔗 链接: {item.www_url}\n"

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「雪球热榜 数字」可指定获取的条数"

        return message

    def format_news_list_message(
            self, items: List[XueqiuNewsItem], count: Optional[int] = None
    ) -> str:
        """格式化新闻列表消息"""
        if not items:
            return "❌ 获取雪球新闻失败，请稍后再试"

        timestamp = self.get_timestamp_str()

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        message = f"📰 雪球最新财经新闻 ({timestamp})\n\n共{len(items)}条新闻\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            title = item.title
            time = item.formatted_date

            message += (
                f"{rank}. {title}\n⏰ 发布时间: {time}\n🔗 链接: {item.www_url}\n"
            )

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「雪球新闻 数字」可指定获取的条数"

        return message

    def format_notice_list_message(
            self, items: List[XueqiuNoticeItem], count: Optional[int] = None
    ) -> str:
        """格式化公告列表消息"""
        if not items:
            return "❌ 获取雪球公告失败，请稍后再试"

        timestamp = self.get_timestamp_str()

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        message = f"📢 雪球最新公告 ({timestamp})\n\n共{len(items)}条公告\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            title = item.title
            time = item.formatted_date

            message += (
                f"{rank}. {title}\n⏰ 发布时间: {time}\n🔗 链接: {item.www_url}\n"
            )

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「雪球公告 数字」可指定获取的条数"

        return message

    def format_search_results_message(
            self, keyword: str, items: List[XueqiuTopicItem]
    ) -> str:
        """格式化搜索结果消息"""
        if not items:
            return f"❌ 没有找到包含「{keyword}」的雪球话题"

        timestamp = self.get_timestamp_str()

        message = f"🔍 雪球话题 - 「{keyword}」搜索结果 ({timestamp})\n\n共找到{len(items)}条相关话题\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            title = item.title
            read_count = item.read_count or "未知"

            message += f"{rank}. {title} 📖 {read_count}阅读\n"

            # 获取相关股票信息
            if item.stocks:
                stocks_info = []
                for stock in item.stocks[:3]:  # 最多显示3个股票
                    trend = (
                        "📈"
                        if stock.percentage > 0
                        else "📉" if stock.percentage < 0 else "➖"
                    )
                    stocks_info.append(f"{stock.name} {trend} {stock.percentage:.2f}%")
                message += f"🏦 相关股票: {' | '.join(stocks_info)}\n"

            message += f"🔗 链接: {item.www_url}\n"

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}"

        return message

    def parse_command(self, content: str) -> Tuple[str, Optional[str]]:
        """解析命令"""
        content = content.strip()

        # 简化的命令映射
        if content in ["雪球热榜", "雪球话题"]:
            return "topic_list", None
        elif content in ["雪球新闻"]:
            return "news_list", None
        elif content in ["雪球公告"]:
            return "notice_list", None

        # 带参数的命令处理
        topic_list_match = re.match(r"^(雪球热榜|雪球话题)\s+(\d+)$", content)
        if topic_list_match:
            return "topic_list", topic_list_match.group(2)

        news_list_match = re.match(r"^雪球新闻\s+(\d+)$", content)
        if news_list_match:
            return "news_list", news_list_match.group(1)

        notice_list_match = re.match(r"^雪球公告\s+(\d+)$", content)
        if notice_list_match:
            return "notice_list", notice_list_match.group(1)

        search_match = re.match(r"^雪球搜索\s+(.+)$", content)
        if search_match:
            return "search", search_match.group(1)

        return "", None

    async def handle_command(
            self, cmd_type: str, param: Optional[str]
    ) -> Union[str, None]:
        """处理命令并返回回复消息"""
        if cmd_type == "topic_list":
            count = int(param) if param else self.config.hot_count
            items = self.get_topic_items(count)
            return self.format_topic_list_message(items, count)
        elif cmd_type == "news_list":
            count = int(param) if param else self.config.news_count
            items = self.get_news_items(count)
            return self.format_news_list_message(items, count)
        elif cmd_type == "notice_list":
            count = int(param) if param else self.config.notice_count
            items = self.get_notice_items(count)
            return self.format_notice_list_message(items, count)
        elif cmd_type == "search":
            keyword = param
            items = self.search_topics(keyword)
            return self.format_search_results_message(keyword, items)
        return None

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        content = msg.raw_message.strip()
        user_id = msg.user_id
        group_id = msg.group_id

        # 检查权限
        if not self.is_user_authorized(user_id, group_id):
            return

        # 解析命令
        cmd_type, param = self.parse_command(content)
        if not cmd_type:
            return

        # 处理命令
        reply_message = await self.handle_command(cmd_type, param)
        if reply_message:
            await msg.reply(text=reply_message)

    async def on_exit(self) -> None:
        """插件卸载时的清理操作"""
        print("雪球财经热榜插件正在卸载...")
