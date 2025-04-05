import json
import logging
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from hotsearch.api import NetEaseNewsClient
from scheduler import scheduler

# 创建logger
logger = logging.getLogger("NetEaseNewsPlugin")

bot = CompatibleEnrollment


@dataclass
class Config:
    """配置类"""

    whitelist_groups: List[int]  # 允许使用的群组ID列表
    whitelist_users: List[int]  # 允许使用的用户ID列表
    hot_count: int  # 热榜数量
    hot_topic_count: int  # 热门话题数量
    comment_count: int  # 评论数量
    update_interval: int  # 数据更新间隔
    api_token: str  # API授权令牌

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})
        api = config_dict.get("api", {})

        return cls(
            whitelist_groups=whitelist.get("group_ids", []),
            whitelist_users=whitelist.get("user_ids", []),
            hot_count=data.get("hot_count", 50),
            hot_topic_count=data.get("hot_topic_count", 10),
            comment_count=data.get("comment_count", 10),
            update_interval=data.get("update_interval", 300),
            api_token=api.get("token", "Bearer b4abc833-112a-11f0-8295-3292b700066c"),
        )


class NetEaseNewsDataCollector:
    """网易新闻数据收集器"""

    def __init__(
            self,
            data_dir: Path,
            hot_count: int = 50,
            hot_topic_count: int = 10,
            comment_count: int = 10,
            api_token: str = None,
    ):
        """初始化数据收集器

        Args:
            data_dir: 数据保存目录
            hot_count: 热榜数量
            hot_topic_count: 热门话题数量
            comment_count: 评论数量
            api_token: API授权令牌，如果为None则使用默认值
        """
        self.data_dir = data_dir
        self.hot_count = hot_count
        self.hot_topic_count = hot_topic_count
        self.comment_count = comment_count
        self.api_token = api_token

        # 初始化API客户端
        self.client = NetEaseNewsClient(
            auth_token=api_token, save_data=True, data_dir=str(data_dir)
        )

    def get_netease_hot(self) -> Dict[str, Any]:
        """获取网易新闻热榜数据"""
        try:
            # 使用NetEaseNewsClient获取热榜数据
            hot_response = self.client.get_hot(as_model=True)

            if not hot_response or not hot_response.items:
                logger.error("获取网易新闻数据失败：数据为空")
                return {}

            # 将结构化数据转换为插件需要的格式
            hot_items = []
            for i, item in enumerate(hot_response.items):
                hot_items.append(
                    {
                        "rank": i + 1,
                        "title": item.title,
                        "hot_value": item.hot_score or 0,
                        "url": item.www_url,
                        "source": item.source,
                        "reply_count": item.reply_count,
                        "category": "视频" if item.is_video else "",
                    }
                )

            # 获取新闻数据
            news_response = self.client.get_news(as_model=True)
            trending_list = []
            if news_response and news_response.items:
                for i, item in enumerate(news_response.items[: self.hot_topic_count]):
                    trending_list.append(
                        {
                            "rank": i + 1,
                            "title": item.title,
                            "url": item.www_url,
                            "source": item.source,
                            "trend": "上升" if (item.hot_score or 0) > 1000 else "持平",
                        }
                    )

            # 构建返回数据
            data = {
                "hot_items": hot_items,
                "hot_list": hot_items,
                "trending_list": trending_list,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "platform": "ne-news",
            }

            return data
        except Exception as e:
            logger.error(f"获取网易新闻数据失败: {e}")
            return {}

    def get_news_detail(self, keyword: str) -> Dict[str, Any]:
        """获取新闻详情
        Args:
            keyword: 新闻关键词
        """
        if not keyword:
            return {}

        try:
            # 从热榜和新闻中搜索相关内容
            news_items = self.client.get_items(sub_tab="news", as_model=True)
            hot_items = self.client.get_items(sub_tab="htd", as_model=True)

            # 合并两个列表
            all_items = list(news_items) + list(hot_items)

            # 搜索匹配的新闻
            matched_items = [item for item in all_items if keyword in item.title]

            if matched_items:
                # 使用第一个匹配项
                item = matched_items[0]
                return {
                    "title": item.title,
                    "summary": f"这是关于{keyword}的新闻。来源: {item.source or '网易新闻'}",
                    "source": item.source or "网易新闻",
                    "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "url": item.www_url,
                    "hot_score": item.hot_score,
                    "reply_count": item.reply_count,
                    "comments": [
                        {
                            "content": item.hot_comment
                                       or f"评论内容 {i + 1} 关于{keyword}",
                            "user": f"网易用户_{i + 1}",
                            "likes": (
                                (item.reply_count or 0) // (i + 1)
                                if i > 0
                                else item.reply_count or 100
                            ),
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        for i in range(min(self.comment_count, 10))
                    ],
                }
            else:
                # 没有找到匹配项，返回模拟数据
                return {
                    "title": f"关于「{keyword}」的网易新闻",
                    "summary": f"这是关于{keyword}的新闻摘要，包含了主要内容和关键信息。网易新闻报道称...",
                    "source": "网易新闻",
                    "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "url": f"https://news.163.com/search?q={keyword}",
                    "reply_count": 0,
                    "comments": [
                        {
                            "content": f"评论内容 {i + 1} 关于{keyword}",
                            "user": f"网易用户_{i + 1}",
                            "likes": (10 - i) * 10,
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        for i in range(min(self.comment_count, 10))
                    ],
                }
        except Exception as e:
            logger.error(f"获取新闻详情失败: {e}")
            return {}

    def collect_data(self) -> Dict[str, Any]:
        """收集网易新闻数据并整合"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        hot_data = self.get_netease_hot()
        if not hot_data:
            return {}

        # 保持原有数据结构，添加统一的时间戳
        hot_data["timestamp"] = timestamp
        hot_data["metadata"] = {
            "source": "ne-news",
            "hot_count": len(hot_data.get("hot_items", [])),
            "update_time": timestamp,
        }

        return hot_data

    def save_data(self, data: Dict[str, Any]) -> str:
        """保存数据到JSON文件，使用年月日的文件夹格式

        Args:
            data: 热榜数据
        """
        if not data:
            return ""

        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        date_dir = self.data_dir / date_str
        date_dir.mkdir(exist_ok=True, parents=True)

        timestamp = now.strftime("%Y%m%d%H%M%S")
        filename = f"nenews_hot_{timestamp}.json"
        filepath = date_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)


class NetEaseNewsPlugin(BasePlugin):
    """网易新闻插件"""

    name = "NetEaseNewsPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    headers_path = None
    config_last_modified = 0
    data_dir = None
    latest_data_file = None

    async def on_load(self):
        """初始化插件"""
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.headers_path = base_path / "config" / "headers.json"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 设置日志级别
        log_level = logging.INFO
        if hasattr(self.config, "log_level"):
            log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logger.setLevel(log_level)

        # 初始化数据收集器
        self.data_collector = NetEaseNewsDataCollector(
            self.data_dir,
            self.config.hot_count,
            self.config.hot_topic_count,
            self.config.comment_count,
            self.config.api_token,
        )

        # 设置定时任务，定期获取热榜数据
        scheduler.add_random_minute_task(
            self.fetch_netease_news, 0, self.config.update_interval, 5
        )

        # 立即执行一次数据获取
        await self.fetch_netease_news()

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
            logger.error(f"加载配置失败: {e}")
            # 使用默认配置
            self.config = Config.from_dict({})

    def check_config_update(self) -> bool:
        """检查配置是否更新"""
        if not self.config_path.exists():
            return False

        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self.config_last_modified:
            self.load_config()
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

    async def fetch_netease_news(self) -> None:
        """获取网易新闻数据"""
        try:
            # 检查配置是否更新
            self.check_config_update()

            data = self.data_collector.collect_data()
            if data:
                self.latest_data_file = self.data_collector.save_data(data)
                await self.clean_old_files()
        except Exception as e:
            logger.error(f"获取网易新闻数据失败: {e}")

    async def clean_old_files(self) -> None:
        """清理旧数据文件"""
        try:
            import os
            import time

            # 当前时间戳
            now = time.time()

            # 获取所有日期目录
            date_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]

            # 按创建时间排序
            date_dirs.sort(key=lambda x: x.stat().st_ctime)

            # 保留最近7天数据（或配置指定的天数）
            keep_days = 7
            if len(date_dirs) > keep_days:
                for old_dir in date_dirs[:-keep_days]:
                    # 删除旧目录及其中的文件
                    for file in old_dir.glob("*"):
                        os.remove(file)
                    os.rmdir(old_dir)
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")

    def get_latest_hot_list(self, count: int = None) -> Dict[str, Any]:
        """获取最新热榜数据"""
        if not self.latest_data_file:
            return {}

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not count:
                count = 10  # 默认显示10条

            hot_list = data.get("hot_list", [])
            if count and count > 0:
                hot_list = hot_list[:count]

            return {
                "timestamp": data.get("timestamp", ""),
                "hot_list": hot_list,
                "metadata": data.get("metadata", {}),
            }
        except Exception as e:
            logger.error(f"获取最新热榜数据失败: {e}")
            return {}

    def get_latest_trending(self) -> Dict[str, Any]:
        """获取最新热点话题数据"""
        if not self.latest_data_file:
            return {}

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "timestamp": data.get("timestamp", ""),
                "trending_list": data.get("trending_list", []),
                "metadata": data.get("metadata", {}),
            }
        except Exception as e:
            logger.error(f"获取最新热点话题数据失败: {e}")
            return {}

    def get_news_details(self, keyword: str) -> Dict[str, Any]:
        """获取新闻详情"""
        if not keyword:
            return {}

        return self.data_collector.get_news_detail(keyword)

    def format_hot_list_simple(
            self, hot_data: Dict[str, Any], count: int = None
    ) -> str:
        """格式化简约版热榜消息"""
        if not hot_data:
            return "❌ 获取网易新闻热榜失败，请稍后再试"

        hot_list = hot_data.get("hot_list", [])
        timestamp = hot_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not hot_list:
            return "❌ 网易新闻热榜数据为空"

        # 限制条数
        if count and count > 0:
            hot_list = hot_list[:count]

        message = f"📰 网易新闻热榜简约版 ({timestamp})\n\n"

        for item in hot_list:
            rank = item.get("rank", 0)
            title = item.get("title", "未知标题")
            message += f"{rank}. {title}\n"

        message += "\n💡 提示: 发送「网易热榜详情」查看详细版本，发送「网易详情 ID」查看指定新闻"
        return message

    def format_hot_list_detail(
            self, hot_data: Dict[str, Any], count: int = None
    ) -> str:
        """格式化详情版热榜消息"""
        if not hot_data:
            return "❌ 获取网易新闻热榜失败，请稍后再试"

        hot_list = hot_data.get("hot_list", [])
        timestamp = hot_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not hot_list:
            return "❌ 网易新闻热榜数据为空"

        # 限制条数
        if count and count > 0:
            hot_list = hot_list[:count]

        message = f"📰 网易新闻热榜详情版 ({timestamp})\n"
        message += "━━━━━━━━━━━━━━\n\n"

        for item in hot_list:
            rank = item.get("rank", 0)
            title = item.get("title", "未知标题")
            hot_value = item.get("hot_value", 0)
            source = item.get("source", "")
            category = item.get("category", "")

            # 格式化热度值
            hot_str = (
                f"🔥 {hot_value // 10000}万"
                if hot_value >= 10000
                else f"🔥 {hot_value}"
            )

            # 分类和来源
            meta = []
            if category:
                meta.append(f"[{category}]")
            if source:
                meta.append(f"来源: {source}")

            meta_str = " | ".join(meta) if meta else ""

            message += f"📌 {rank}. {title}\n"
            if meta_str:
                message += f"   {meta_str}\n"
            if hot_value > 0:
                message += f"   {hot_str}\n"
            message += "\n"

        message += "━━━━━━━━━━━━━━\n"
        message += f"📊 更新时间: {timestamp}\n"
        message += "💡 发送「网易详情 ID」查看指定新闻详情"

        return message

    def get_news_by_id(self, news_id: int) -> Dict[str, Any]:
        """根据新闻ID获取新闻详情"""
        if not self.latest_data_file or news_id <= 0:
            return {}

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            hot_list = data.get("hot_list", [])

            # 查找对应ID的新闻
            for item in hot_list:
                if item.get("rank") == news_id:
                    # 获取关键词并查询详情
                    title = item.get("title", "")
                    if title:
                        news_detail = self.data_collector.get_news_detail(title)

                        # 如果API没有返回回复数，则使用热榜中的数据
                        if "reply_count" not in news_detail and "reply_count" in item:
                            news_detail["reply_count"] = item.get("reply_count", 0)

                        return news_detail

            return {}
        except Exception as e:
            logger.error(f"根据ID获取新闻详情失败: {e}")
            return {}

    def format_trending_message(self, hot_data: Dict[str, Any]) -> str:
        """格式化热点话题消息"""
        if not hot_data:
            return "❌ 获取网易热点话题失败，请稍后再试"

        trending_list = hot_data.get("trending_list", [])
        timestamp = hot_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not trending_list:
            return "❌ 网易热点话题数据为空"

        message = f"🔍 网易热点话题 ({timestamp})\n\n共{len(trending_list)}条热点\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(trending_list):
            rank = item.get("rank", i + 1)
            title = item.get("title", "未知话题")
            trend = item.get("trend", "")

            # 趋势图标
            trend_icon = ""
            if trend == "上升":
                trend_icon = "📈 "
            elif trend == "下降":
                trend_icon = "📉 "
            elif trend == "持平":
                trend_icon = "📊 "

            message += f"{rank}. {title} {trend_icon}\n\n"

            # 每三条添加分隔符
            if i < len(trending_list) - 1 and (i + 1) % 3 == 0:
                message += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n"
        message += f"📊 更新时间: {timestamp}\n"
        message += "💡 提示: 发送「网易新闻 关键词」可查询相关新闻详情"

        return message

    def format_news_detail_message(self, news_data: Dict[str, Any]) -> str:
        """格式化新闻详情消息"""
        if not news_data:
            return "❌ 获取新闻详情失败，请稍后再试"

        title = news_data.get("title", "未知标题")
        summary = news_data.get("summary", "无内容摘要")
        source = news_data.get("source", "未知来源")
        publish_time = news_data.get("publish_time", "未知时间")
        url = news_data.get("url", "")
        comments = news_data.get("comments", [])
        hot_score = news_data.get("hot_score", 0)
        reply_count = news_data.get("reply_count", 0)

        message = f"📰 {title}\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        message += f"📄 内容摘要：\n{summary}\n\n"
        message += f"🔖 来源：{source}\n"
        message += f"🕒 发布时间：{publish_time}\n"

        if hot_score:
            message += f"🔥 热度：{hot_score}\n"

        if reply_count:
            message += f"💬 评论数：{reply_count}\n"

        if url:
            message += f"🔗 链接：{url}\n"

        # 检查评论内容是否是模拟的
        has_real_comments = any(
            not comment.get("content", "").startswith("评论内容 ")
            for comment in comments[:3]
            if comment
        )

        if comments and has_real_comments:
            message += "\n💬 热门评论：\n"
            # 使用字母标记评论，从a开始
            for i, comment in enumerate(comments[:5]):  # 最多显示5条评论
                letter = chr(97 + i)  # a=97, b=98, ...
                content = comment.get("content", "无内容")
                likes = comment.get("likes", 0)

                message += f"{letter}、{content}"
                if likes > 0:
                    message += f" 👍 {likes}"
                message += "\n"

        message += "\n━━━━━━━━━━━━━━━━━━\n"
        message += "💡 提示: 发送「网易热榜」可查看热榜内容"

        return message

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        content = msg.raw_message.strip()
        user_id = msg.user_id
        group_id = msg.group_id

        # 检查权限
        if not self.is_user_authorized(user_id, group_id):
            return

        # 直接处理各种指令模式
        if content == "网易热榜":
            hot_data = self.get_latest_hot_list(10)  # 默认10条
            message = self.format_hot_list_simple(hot_data)
            await msg.reply(text=message)

        elif content == "网易热榜详情":
            hot_data = self.get_latest_hot_list(10)  # 默认10条
            message = self.format_hot_list_detail(hot_data)
            await msg.reply(text=message)

        elif re.match(r"^网易热榜\s+(\d+)$", content):
            count = int(re.match(r"^网易热榜\s+(\d+)$", content).group(1))
            hot_data = self.get_latest_hot_list(count)
            message = self.format_hot_list_simple(hot_data, count)
            await msg.reply(text=message)

        elif re.match(r"^网易热榜详情\s+(\d+)$", content):
            count = int(re.match(r"^网易热榜详情\s+(\d+)$", content).group(1))
            hot_data = self.get_latest_hot_list(count)
            message = self.format_hot_list_detail(hot_data, count)
            await msg.reply(text=message)

        elif content == "网易热点":
            trending_data = self.get_latest_trending()
            message = self.format_trending_message(trending_data)
            await msg.reply(text=message)

        elif re.match(r"^网易新闻\s+(.+)$", content):
            keyword = re.match(r"^网易新闻\s+(.+)$", content).group(1)
            news_data = self.get_news_details(keyword)
            message = self.format_news_detail_message(news_data)
            await msg.reply(text=message)

        elif re.match(r"^网易详情\s+(\d+)$", content):
            news_id = int(re.match(r"^网易详情\s+(\d+)$", content).group(1))
            news_data = self.get_news_by_id(news_id)
            message = self.format_news_detail_message(news_data)
            await msg.reply(text=message)
