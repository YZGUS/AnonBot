import json
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from scheduler import scheduler
from hotsearch.api import TencentNewsClient
from hotsearch.api.models.tencent_news import (
    TencentNewsHotSearchItem,
    TencentNewsHotSearchResponse,
)

bot = CompatibleEnrollment


@dataclass
class Config:
    """配置类"""

    whitelist_groups: List[int]  # 允许使用的群组ID列表
    whitelist_users: List[int]  # 允许使用的用户ID列表
    hot_count: int  # 热榜数量
    auth_token: str  # 授权令牌
    update_interval: int  # 数据更新间隔

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})

        return cls(
            whitelist_groups=whitelist.get("group_ids", []),
            whitelist_users=whitelist.get("user_ids", []),
            hot_count=data.get("hot_count", 50),
            auth_token=data.get(
                "auth_token", "Bearer b4abc833-112a-11f0-8295-3292b700066c"
            ),
            update_interval=data.get("update_interval", 300),
        )


class TencentNewsPlugin(BasePlugin):
    """腾讯新闻插件"""

    name = "TencentNewsPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    latest_data = None
    news_client = None

    async def on_load(self):
        """插件加载时执行"""
        # 初始化插件
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 初始化腾讯新闻客户端
        self.news_client = TencentNewsClient(
            auth_token=self.config.auth_token,
            save_data=True,
            data_dir=str(self.data_dir),
        )

        # 设置定时任务
        scheduler.add_random_minute_task(self.fetch_tencent_news, 0, 5)

        # 立即执行一次数据获取
        await self.fetch_tencent_news()

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

    def check_config_update(self) -> bool:
        """检查配置是否更新"""
        if not self.config_path.exists():
            return False

        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self.config_last_modified:
            self.load_config()
            # 更新客户端配置
            if self.news_client:
                self.news_client.auth_token = self.config.auth_token
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

    async def fetch_tencent_news(self) -> None:
        """获取腾讯新闻数据"""
        try:
            # 检查配置是否更新
            self.check_config_update()

            # 获取热搜数据
            response = self.news_client.get_hot(as_model=True)
            if response and hasattr(response, "items") and response.items:
                self.latest_data = response
                await self.clean_old_files()
        except Exception as e:
            print(f"获取腾讯新闻数据失败: {e}")

    async def clean_old_files(self) -> None:
        """清理旧数据文件"""
        try:
            import os
            import time

            # 获取所有日期目录
            date_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]

            # 按创建时间排序
            date_dirs.sort(key=lambda x: x.stat().st_ctime)

            # 保留最近7天数据
            keep_days = 7
            if len(date_dirs) > keep_days:
                for old_dir in date_dirs[:-keep_days]:
                    # 删除旧目录及其中的文件
                    for file in old_dir.glob("*"):
                        os.remove(file)
                    os.rmdir(old_dir)
        except Exception as e:
            print(f"清理旧文件失败: {e}")

    def get_latest_hot_list(self, count: int = None) -> List[TencentNewsHotSearchItem]:
        """获取最新热榜数据"""
        if not self.latest_data:
            # 如果没有缓存数据，尝试获取
            try:
                response = self.news_client.get_items(as_model=True)
                if not count:
                    count = 10  # 默认显示10条
                return response[:count] if count and count > 0 else response
            except Exception as e:
                print(f"获取最新热榜数据失败: {e}")
                return []

        # 使用缓存数据
        items = self.latest_data.items
        if count and count > 0:
            items = items[:count]
        return items

    def search_news(self, keyword: str) -> List[TencentNewsHotSearchItem]:
        """搜索相关新闻"""
        if not keyword:
            return []

        try:
            # 获取所有热搜项目
            items = self.news_client.get_items(as_model=True)

            # 搜索包含关键词的项目
            return [item for item in items if keyword in item.title]
        except Exception as e:
            print(f"搜索新闻失败: {e}")
            return []

    def format_hot_list_message(
        self, items: List[TencentNewsHotSearchItem], count: int = None
    ) -> str:
        """格式化热榜消息"""
        if not items:
            return "❌ 获取腾讯新闻热榜失败，请稍后再试"

        # 限制条数
        if count and count > 0:
            items = items[:count]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📰 腾讯新闻热榜 ({timestamp})\n\n共{len(items)}条热榜\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            # 前三名使用特殊标记
            if i == 0:
                prefix = "🥇 "
            elif i == 1:
                prefix = "🥈 "
            elif i == 2:
                prefix = "🥉 "
            else:
                prefix = f"{i+1}. "

            # 格式化热度值
            hot_str = ""
            if item.hot_score:
                if item.hot_score >= 10000:
                    hot_str = f"🔥 {item.hot_score // 10000}万热度"
                else:
                    hot_str = f"🔥 {item.hot_score}热度"

            # 标题
            title = item.title

            message += f"{prefix}{title} {hot_str}\n\n"

            # 每三条添加分隔符
            if i < len(items) - 1 and (i + 1) % 3 == 0:
                message += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n"
        message += f"📊 更新时间: {timestamp}\n"
        message += "💡 提示: 发送「腾讯热榜 数字」可指定获取的条数，如「腾讯热榜 20」"

        return message

    def format_news_detail_message(
        self, items: List[TencentNewsHotSearchItem], keyword: str
    ) -> str:
        """格式化新闻详情消息"""
        if not items:
            return f"❌ 未找到与「{keyword}」相关的新闻，请换个关键词试试"

        message = f"📰 关于「{keyword}」的新闻 (共{len(items)}条)\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        # 最多显示5条相关新闻
        for i, item in enumerate(items[:5]):
            message += f"{i+1}. {item.title}\n"
            if item.hot_score:
                message += f"   🔥 热度: {item.hot_score}\n"
            if item.www_url:
                message += f"   🔗 链接: {item.www_url}\n"
            if item.comment_num:
                message += f"   💬 评论数: {item.comment_num}\n"
            message += "\n"

        message += "━━━━━━━━━━━━━━━━━━\n"
        message += "💡 提示: 发送「腾讯热榜」可查看热榜内容"

        return message

    def parse_command(self, content: str) -> Tuple[str, Optional[str]]:
        """解析命令
        Return:
            (命令类型, 参数)
        """
        content = content.strip()

        if re.match(r"^腾讯热榜$", content):
            return "hot_list", None
        elif re.match(r"^腾讯热榜\s+(\d+)$", content):
            count = re.match(r"^腾讯热榜\s+(\d+)$", content).group(1)
            return "hot_list", count
        elif re.match(r"^腾讯新闻\s+(.+)$", content):
            keyword = re.match(r"^腾讯新闻\s+(.+)$", content).group(1)
            return "news_detail", keyword
        else:
            return "", None

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
        if cmd_type == "hot_list":
            count = int(param) if param else None
            hot_items = self.get_latest_hot_list(count)
            message = self.format_hot_list_message(hot_items, count)
            await msg.reply(text=message)
        elif cmd_type == "news_detail":
            news_items = self.search_news(param)
            message = self.format_news_detail_message(news_items, param)
            await msg.reply(text=message)

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        content = msg.raw_message.strip()
        user_id = msg.user_id

        # 检查权限
        if not self.is_user_authorized(user_id):
            return

        # 解析命令
        cmd_type, param = self.parse_command(content)
        if not cmd_type:
            return

        # 处理命令
        if cmd_type == "hot_list":
            count = int(param) if param else None
            hot_items = self.get_latest_hot_list(count)
            message = self.format_hot_list_message(hot_items, count)
            await msg.reply(text=message)
        elif cmd_type == "news_detail":
            news_items = self.search_news(param)
            message = self.format_news_detail_message(news_items, param)
            await msg.reply(text=message)
