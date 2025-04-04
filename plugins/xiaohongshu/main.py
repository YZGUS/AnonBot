import json
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from scheduler import scheduler

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

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})

        return cls(
            whitelist_groups=whitelist.get("group_ids", []),
            whitelist_users=whitelist.get("user_ids", []),
            hot_count=data.get("hot_count", 50),
            hot_topic_count=data.get("hot_topic_count", 10),
            comment_count=data.get("comment_count", 10),
            update_interval=data.get("update_interval", 300),
        )


class XiaohongshuDataCollector:
    """小红书数据收集器"""

    def __init__(
        self,
        headers_path: Path,
        data_dir: Path,
        hot_count: int = 50,
        hot_topic_count: int = 10,
        comment_count: int = 10,
    ):
        self.headers = self._load_headers(headers_path)
        self.data_dir = data_dir
        self.hot_count = hot_count
        self.hot_topic_count = hot_topic_count
        self.comment_count = comment_count

    def _load_headers(self, headers_path: Path) -> Dict[str, str]:
        """加载请求头配置"""
        if headers_path.exists():
            with open(headers_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://www.xiaohongshu.com/",
        }

    def get_xiaohongshu_hot(self) -> Dict[str, Any]:
        """获取小红书热榜数据"""
        url = "https://www.xiaohongshu.com/explore"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return {}

            soup = BeautifulSoup(response.text, "html.parser")
            hot_list = []

            # 提取热榜数据，实际实现会根据小红书网页结构调整
            # 这里提供模拟数据
            for i in range(min(self.hot_count, 50)):
                hot_list.append(
                    {
                        "rank": i + 1,
                        "title": f"小红书热榜标题 {i + 1}",
                        "hot_value": 100000 - (i * 2000),
                        "category": ["美妆", "穿搭", "美食", "旅行", "生活"][i % 5],
                        "url": f"https://www.xiaohongshu.com/explore/search?keyword=热榜{i + 1}",
                    }
                )

            # 获取热门话题
            trending_list = []
            for i in range(min(self.hot_topic_count, 10)):
                trending_list.append(
                    {
                        "rank": i + 1,
                        "title": f"小红书热门话题 {i + 1}",
                        "trend": ["上升", "下降", "持平"][i % 3],
                        "url": f"https://www.xiaohongshu.com/explore/topic_{i}",
                    }
                )

            # 获取热门笔记
            notes_list = []
            for i in range(min(self.hot_topic_count, 10)):
                notes_list.append(
                    {
                        "rank": i + 1,
                        "title": f"小红书热门笔记 {i + 1}",
                        "author": f"用户_{i + 1}",
                        "likes": 10000 - (i * 500),
                        "comments": 1000 - (i * 50),
                        "url": f"https://www.xiaohongshu.com/explore/note_{i}",
                    }
                )

            return {
                "hot_list": hot_list,
                "trending_list": trending_list,
                "notes_list": notes_list,
            }
        except Exception as e:
            print(f"获取小红书热榜失败: {e}")
            return {}

    def get_note_detail(self, keyword: str) -> Dict[str, Any]:
        """获取笔记详情
        Args:
            keyword: 笔记关键词
        """
        if not keyword:
            return {}

        try:
            # 实际实现需要根据小红书网站结构调整
            # 这里提供模拟数据
            return {
                "title": f"关于「{keyword}」的小红书笔记",
                "summary": f"这是关于{keyword}的笔记摘要，包含了主要内容和图片描述...",
                "author": "小红书达人",
                "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "url": f"https://www.xiaohongshu.com/search?keyword={keyword}",
                "likes": 5678,
                "comments": [
                    {
                        "content": f"评论内容 {i + 1} 关于{keyword}",
                        "user": f"小红书用户_{i + 1}",
                        "likes": (10 - i) * 10,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for i in range(min(self.comment_count, 10))
                ],
            }
        except Exception as e:
            print(f"获取笔记详情失败: {e}")
            return {}

    def collect_data(self) -> Dict[str, Any]:
        """收集小红书数据并整合"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        hot_data = self.get_xiaohongshu_hot()
        if not hot_data:
            return {}

        result = {
            "timestamp": timestamp,
            "hot_list": hot_data.get("hot_list", []),
            "trending_list": hot_data.get("trending_list", []),
            "notes_list": hot_data.get("notes_list", []),
            "metadata": {
                "source": "xiaohongshu",
                "hot_count": len(hot_data.get("hot_list", [])),
                "trending_count": len(hot_data.get("trending_list", [])),
                "notes_count": len(hot_data.get("notes_list", [])),
                "update_time": timestamp,
            },
        }
        return result

    def save_data(self, data: Dict[str, Any]) -> str:
        """保存数据到按小时组织的文件中"""
        if not data:
            return ""

        # 使用年月日-小时格式，如 "YYYYMMDD-HH"
        now = datetime.now()
        folder_name = now.strftime("%Y%m%d-%H")
        folder_path = self.data_dir / folder_name
        folder_path.mkdir(exist_ok=True, parents=True)

        file_name = f"xiaohongshu_{now.strftime('%Y%m%d_%H%M%S')}.json"
        file_path = folder_path / file_name

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(file_path)


class XiaohongshuPlugin(BasePlugin):
    """小红书插件"""

    name = "XiaohongshuPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    headers_path = None
    config_last_modified = 0
    data_dir = None
    latest_data_file = None

    async def on_load(self):
        """插件加载时执行"""
        # 初始化插件
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.headers_path = base_path / "config" / "headers.json"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 设置定时任务
        scheduler.add_random_minute_task(self.fetch_xiaohongshu, 0, 5)

        # 立即执行一次数据获取
        await self.fetch_xiaohongshu()

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

    async def fetch_xiaohongshu(self) -> None:
        """获取小红书数据"""
        try:
            # 检查配置是否更新
            self.check_config_update()

            collector = XiaohongshuDataCollector(
                self.headers_path,
                self.data_dir,
                self.config.hot_count,
                self.config.hot_topic_count,
                self.config.comment_count,
            )

            data = collector.collect_data()
            if data:
                self.latest_data_file = collector.save_data(data)
                await self.clean_old_files()
        except Exception as e:
            print(f"获取小红书数据失败: {e}")

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
            print(f"清理旧文件失败: {e}")

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
            print(f"获取最新热榜数据失败: {e}")
            return {}

    def get_latest_trending(self) -> Dict[str, Any]:
        """获取最新热门话题数据"""
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
            print(f"获取最新热门话题数据失败: {e}")
            return {}

    def get_latest_notes(self) -> Dict[str, Any]:
        """获取最新热门笔记数据"""
        if not self.latest_data_file:
            return {}

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return {
                "timestamp": data.get("timestamp", ""),
                "notes_list": data.get("notes_list", []),
                "metadata": data.get("metadata", {}),
            }
        except Exception as e:
            print(f"获取最新热门笔记数据失败: {e}")
            return {}

    def get_note_details(self, keyword: str) -> Dict[str, Any]:
        """获取笔记详情"""
        if not keyword:
            return {}

        collector = XiaohongshuDataCollector(
            self.headers_path,
            self.data_dir,
            self.config.hot_count,
            self.config.hot_topic_count,
            self.config.comment_count,
        )

        return collector.get_note_detail(keyword)

    def format_hot_list_message(
        self, hot_data: Dict[str, Any], count: int = None
    ) -> str:
        """格式化热榜消息"""
        if not hot_data:
            return "❌ 获取小红书热榜失败，请稍后再试"

        hot_list = hot_data.get("hot_list", [])
        timestamp = hot_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not hot_list:
            return "❌ 小红书热榜数据为空"

        # 限制条数
        if count and count > 0:
            hot_list = hot_list[:count]

        message = f"📖 小红书热榜 ({timestamp})\n\n共{len(hot_list)}条热榜\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(hot_list):
            rank = item.get("rank", i + 1)
            title = item.get("title", "未知标题")
            hot_value = item.get("hot_value", 0)
            category = item.get("category", "")

            # 前三名使用特殊标记
            if rank == 1:
                prefix = "🥇 "
            elif rank == 2:
                prefix = "🥈 "
            elif rank == 3:
                prefix = "🥉 "
            else:
                prefix = f"{rank}. "

            # 格式化热度值
            hot_str = ""
            if hot_value > 0:
                if hot_value >= 10000:
                    hot_str = f"🔥 {hot_value // 10000}万热度"
                else:
                    hot_str = f"🔥 {hot_value}热度"

            # 分类标签
            category_str = f"[{category}]" if category else ""

            message += f"{prefix}{title} {category_str} {hot_str}\n\n"

            # 每三条添加分隔符
            if i < len(hot_list) - 1 and (i + 1) % 3 == 0:
                message += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n"
        message += f"📊 更新时间: {timestamp}\n"
        message += (
            "💡 提示: 发送「小红书热榜 数字」可指定获取的条数，如「小红书热榜 20」"
        )

        return message

    def format_trending_message(self, trend_data: Dict[str, Any]) -> str:
        """格式化热门话题消息"""
        if not trend_data:
            return "❌ 获取小红书热门话题失败，请稍后再试"

        trending_list = trend_data.get("trending_list", [])
        timestamp = trend_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not trending_list:
            return "❌ 小红书热门话题数据为空"

        message = (
            f"🔍 小红书热门话题 ({timestamp})\n\n共{len(trending_list)}条热门话题\n"
        )
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
        message += "💡 提示: 发送「小红书笔记 关键词」可查询相关笔记详情"

        return message

    def format_notes_message(self, notes_data: Dict[str, Any]) -> str:
        """格式化热门笔记消息"""
        if not notes_data:
            return "❌ 获取小红书热门笔记失败，请稍后再试"

        notes_list = notes_data.get("notes_list", [])
        timestamp = notes_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        if not notes_list:
            return "❌ 小红书热门笔记数据为空"

        message = f"📝 小红书热门笔记 ({timestamp})\n\n共{len(notes_list)}条热门笔记\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(notes_list):
            rank = item.get("rank", i + 1)
            title = item.get("title", "未知笔记")
            author = item.get("author", "未知作者")
            likes = item.get("likes", 0)
            comments = item.get("comments", 0)

            # 格式化点赞和评论数
            likes_str = f"❤️ {likes}" if likes > 0 else ""
            comments_str = f"💬 {comments}" if comments > 0 else ""
            stats = f"{likes_str} {comments_str}".strip()

            message += f"{rank}. {title}\n"
            message += f"👤 {author} | {stats}\n\n"

            # 每三条添加分隔符
            if i < len(notes_list) - 1 and (i + 1) % 3 == 0:
                message += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n"
        message += f"📊 更新时间: {timestamp}\n"
        message += "💡 提示: 发送「小红书笔记 关键词」可查询相关笔记详情"

        return message

    def format_note_detail_message(self, note_data: Dict[str, Any]) -> str:
        """格式化笔记详情消息"""
        if not note_data:
            return "❌ 获取笔记详情失败，请稍后再试"

        title = note_data.get("title", "未知标题")
        summary = note_data.get("summary", "无内容摘要")
        author = note_data.get("author", "未知作者")
        publish_time = note_data.get("publish_time", "未知时间")
        url = note_data.get("url", "")
        likes = note_data.get("likes", 0)
        comments = note_data.get("comments", [])

        message = f"📝 {title}\n\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"
        message += f"📄 内容摘要：\n{summary}\n\n"
        message += f"👤 作者：{author}\n"
        message += f"🕒 发布时间：{publish_time}\n"

        if likes > 0:
            message += f"❤️ 点赞数：{likes}\n"

        if url:
            message += f"🔗 链接：{url}\n"

        if comments:
            message += "\n💬 热门评论：\n\n"
            for i, comment in enumerate(comments[:5]):  # 最多显示5条评论
                user = comment.get("user", "匿名用户")
                content = comment.get("content", "无内容")
                likes = comment.get("likes", 0)

                message += f"{user}：{content}"
                if likes > 0:
                    message += f" 👍 {likes}"
                message += "\n\n"

        message += "━━━━━━━━━━━━━━━━━━\n"
        message += "💡 提示: 发送「小红书热榜」可查看热榜内容"

        return message

    def parse_command(self, content: str) -> Tuple[str, Optional[str]]:
        """解析命令
        Return:
            (命令类型, 参数)
        """
        content = content.strip()

        if re.match(r"^小红书热榜$", content):
            return "hot_list", None
        elif re.match(r"^小红书热榜\s+(\d+)$", content):
            count = re.match(r"^小红书热榜\s+(\d+)$", content).group(1)
            return "hot_list", count
        elif re.match(r"^小红书热门话题$", content):
            return "trending", None
        elif re.match(r"^小红书热门笔记$", content):
            return "notes", None
        elif re.match(r"^小红书笔记\s+(.+)$", content):
            keyword = re.match(r"^小红书笔记\s+(.+)$", content).group(1)
            return "note_detail", keyword
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
            hot_data = self.get_latest_hot_list(count)
            message = self.format_hot_list_message(hot_data, count)
            await msg.reply(text=message)
        elif cmd_type == "trending":
            trending_data = self.get_latest_trending()
            message = self.format_trending_message(trending_data)
            await msg.reply(text=message)
        elif cmd_type == "notes":
            notes_data = self.get_latest_notes()
            message = self.format_notes_message(notes_data)
            await msg.reply(text=message)
        elif cmd_type == "note_detail":
            note_data = self.get_note_details(param)
            message = self.format_note_detail_message(note_data)
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
            hot_data = self.get_latest_hot_list(count)
            message = self.format_hot_list_message(hot_data, count)
            await msg.reply(text=message)
        elif cmd_type == "trending":
            trending_data = self.get_latest_trending()
            message = self.format_trending_message(trending_data)
            await msg.reply(text=message)
        elif cmd_type == "notes":
            notes_data = self.get_latest_notes()
            message = self.format_notes_message(notes_data)
            await msg.reply(text=message)
        elif cmd_type == "note_detail":
            note_data = self.get_note_details(param)
            message = self.format_note_detail_message(note_data)
            await msg.reply(text=message)
