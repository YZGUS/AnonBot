import json
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import brotli
import requests
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


class DouyinDataCollector:
    """抖音数据收集器"""

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
            "Referer": "https://www.douyin.com/",
        }

    def get_douyin_hot(self) -> Dict[str, Any]:
        """获取抖音热榜数据"""
        url = "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return {}

            content_encoding = response.headers.get("Content-Encoding", "").lower()
            raw_content = response.content

            if "br" in content_encoding:
                try:
                    raw_content = brotli.decompress(raw_content)
                except:
                    pass

            try:
                result = json.loads(raw_content)
                return result
            except:
                return {}
        except:
            return {}

    def get_topic_detail(self, topic_word: str) -> Dict[str, Any]:
        """获取话题详情
        Args:
            topic_word: 话题关键词
        """
        if not topic_word:
            return {}

        search_word = topic_word.replace("#", "")
        detail_url = f"https://www.douyin.com/search/{search_word}"

        try:
            response = requests.get(detail_url, headers=self.headers)
            if response.status_code != 200:
                return {}

            return {
                "topic_id": f"douyin_topic_{hash(topic_word) % 10000000}",
                "title": topic_word,
                "view_count": 0,
                "video_count": 0,
                "url": detail_url,
            }
        except:
            return {}

    def get_topic_comments(self, topic_word: str) -> List[Dict[str, Any]]:
        """获取话题评论
        Args:
            topic_word: 话题关键词
        """
        if not topic_word:
            return []

        comments = []
        for i in range(self.comment_count):
            comments.append(
                {
                    "comment_id": f"comment_{hash(topic_word) % 10000000}_{i}",
                    "content": f"这是关于{topic_word}的模拟评论 {i + 1}",
                    "like_count": (10 - i) * 100,
                    "user": f"用户_{i + 1}",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return comments

    def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """获取视频元数据
        Args:
            video_id: 视频ID
        """
        if not video_id:
            return {}

        return {
            "video_id": video_id,
            "play_count": 10000,
            "author": "创作者",
            "publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "description": "视频描述内容",
        }

    def parse_hot_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析热榜数据
        Args:
            data: 原始API返回的数据
        """
        hot_list = []
        word_list = data.get("data", {}).get("word_list", [])

        for i, item in enumerate(word_list):
            if i >= self.hot_count:
                break

            topic = {
                "rank": item.get("position", i + 1),
                "title": item.get("word", "未知话题"),
                "topic_id": item.get("sentence_id", f"douyin_topic_{i}"),
                "hot_value": item.get("hot_value", 0),
                "label": item.get("label", 0),
                "word_type": item.get("word_type", 0),
                "url": f"https://www.douyin.com/search/{item.get('word', '').replace(' ', '%20')}",
            }

            if (
                    "word_cover" in item
                    and "url_list" in item["word_cover"]
                    and item["word_cover"]["url_list"]
            ):
                topic["cover_url"] = item["word_cover"]["url_list"][0]
            else:
                topic["cover_url"] = ""

            hot_list.append(topic)

        return hot_list

    def parse_trending_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析实时上升热点数据
        Args:
            data: 原始API返回的数据
        """
        trending_list = []
        trend_data = data.get("data", {}).get("trending_list", [])

        for i, item in enumerate(trend_data):
            if i >= self.hot_topic_count:
                break

            topic = {
                "rank": i + 1,
                "title": item.get("word", "未知话题"),
                "topic_id": item.get("sentence_id", f"douyin_trending_{i}"),
                "sentence_tag": item.get("sentence_tag", 0),
                "group_id": item.get("group_id", ""),
                "url": f"https://www.douyin.com/search/{item.get('word', '').replace(' ', '%20')}",
            }

            if (
                    "word_cover" in item
                    and "url_list" in item["word_cover"]
                    and item["word_cover"]["url_list"]
            ):
                topic["cover_url"] = item["word_cover"]["url_list"][0]
            else:
                topic["cover_url"] = ""

            trending_list.append(topic)

        return trending_list

    def collect_data(self) -> Dict[str, Any]:
        """收集抖音数据并整合"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        hot_data = self.get_douyin_hot()
        if not hot_data:
            return {}

        hot_list = self.parse_hot_list(hot_data)
        trending_list = self.parse_trending_list(hot_data)

        result = {
            "timestamp": timestamp,
            "hot_list": hot_list,
            "trending_list": trending_list,
            "metadata": {
                "source": "douyin",
                "hot_count": len(hot_list),
                "trending_count": len(trending_list),
                "update_time": timestamp,
            },
        }

        return result

    def save_data(self, data: Dict[str, Any]) -> str:
        """保存数据到JSON文件，使用年月日-小时的文件夹格式"""
        if not data:
            return ""

        now = datetime.now()
        folder_name = now.strftime("%Y%m%d-%H")
        folder_path = self.data_dir / folder_name
        folder_path.mkdir(exist_ok=True, parents=True)

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"douyin_hot_{timestamp}.json"
        filepath = folder_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)


class DouyinPlugin(BasePlugin):
    name = "DouyinPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    headers_path = None
    config_last_modified = 0
    data_dir = None
    latest_data_file = None

    async def on_load(self):
        # 初始化插件
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.headers_path = base_path / "config" / "headers.json"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 设置定时任务，定期获取热榜数据
        scheduler.add_random_minute_task(self.fetch_douyin_hot, 0, 5)

        # 立即执行一次，获取初始数据
        await self.fetch_douyin_hot()

    def load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            with open(self.config_path, "rb") as f:
                config_dict = tomllib.load(f)
            self.config = Config.from_dict(config_dict)
            self.config_last_modified = self.config_path.stat().st_mtime
        else:
            self.config = Config.from_dict({})

    def check_config_update(self) -> bool:
        """检查配置文件是否更新"""
        if not self.config_path.exists():
            return False

        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self.config_last_modified:
            self.load_config()
            return True
        return False

    def is_user_authorized(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """检查用户是否有权限"""
        # 检查配置文件是否更新
        self.check_config_update()

        # 如果白名单为空，则允许所有用户
        if not self.config.whitelist_users and not self.config.whitelist_groups:
            return True

        # 检查用户ID是否在白名单中
        if user_id in self.config.whitelist_users:
            return True

        # 检查群组ID是否在白名单中
        if group_id and group_id in self.config.whitelist_groups:
            return True

        return False

    async def fetch_douyin_hot(self) -> None:
        """获取抖音热榜数据"""
        collector = DouyinDataCollector(
            headers_path=self.headers_path,
            data_dir=self.data_dir,
            hot_count=self.config.hot_count,
            hot_topic_count=self.config.hot_topic_count,
            comment_count=self.config.comment_count,
        )
        data = collector.collect_data()
        if data:
            data_file = collector.save_data(data)
            if data_file:
                self.latest_data_file = data_file

    def get_latest_hot_list(self, count: int = None) -> Dict[str, Any]:
        """获取最新的热榜数据
        Args:
            count: 获取的热榜数量，如果为None则使用配置中的hot_count
        """
        # 检查是否有最新数据文件
        if not self.latest_data_file:
            return {}

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if count is None or count <= 0:
                # 使用默认显示数量，一般为10条
                count = 10
            elif count > self.config.hot_count:
                count = self.config.hot_count

            # 限制返回的热榜数量
            result = data.copy()
            if "hot_list" in result and len(result["hot_list"]) > count:
                result["hot_list"] = result["hot_list"][:count]

            return result
        except:
            return {}

    def get_topic_details(self, keyword: str) -> Dict[str, Any]:
        """获取话题详情
        Args:
            keyword: 话题关键词
        """
        collector = DouyinDataCollector(
            headers_path=self.headers_path,
            data_dir=self.data_dir,
            hot_count=self.config.hot_count,
            hot_topic_count=self.config.hot_topic_count,
            comment_count=self.config.comment_count,
        )

        # 获取话题详情
        topic_detail = collector.get_topic_detail(keyword)
        if not topic_detail:
            return {}

        # 获取话题评论
        topic_detail["comments"] = collector.get_topic_comments(keyword)

        return topic_detail

    def format_hot_list_message(
            self, hot_data: Dict[str, Any], count: int = None
    ) -> str:
        """格式化热榜消息
        Args:
            hot_data: 热榜数据
            count: 显示的热榜数量
        """
        if not hot_data or "hot_list" not in hot_data:
            return "抖音热榜数据获取失败，请稍后再试"

        if count is None or count <= 0:
            count = 10  # 默认显示10条
        elif count > len(hot_data["hot_list"]):
            count = len(hot_data["hot_list"])

        collected_time = hot_data.get("timestamp", "未知时间")
        message = f"【抖音实时热榜】 - {collected_time}\n\n"

        for i, item in enumerate(hot_data["hot_list"][:count]):
            rank = item.get("rank", i + 1)
            title = item.get("title", "未知话题")
            hot_value = item.get("hot_value", 0)

            # 格式化热度值，如果大于10000则显示为万
            hot_str = (
                f"{hot_value / 10000:.1f}万" if hot_value > 10000 else str(hot_value)
            )

            # 添加标签
            label = item.get("label", 0)
            label_text = ""
            if label == 1:
                label_text = "🔥 "
            elif label == 3:
                label_text = "📢 "
            elif label == 8:
                label_text = "👍 "

            message += f"{rank}. {label_text}{title}"
            if hot_value:
                message += f" ({hot_str})"
            message += "\n"

        return message

    def format_trending_message(self, hot_data: Dict[str, Any]) -> str:
        """格式化实时上升热点消息
        Args:
            hot_data: 热榜数据
        """
        if not hot_data or "trending_list" not in hot_data:
            return "抖音实时上升热点数据获取失败，请稍后再试"

        topics = hot_data["trending_list"]
        count = min(self.config.hot_topic_count, len(topics))

        collected_time = hot_data.get("timestamp", "未知时间")
        message = f"【抖音实时上升热点】 - {collected_time}\n\n"

        for i, item in enumerate(topics[:count]):
            rank = i + 1
            title = item.get("title", "未知话题")
            tag = item.get("sentence_tag", 0)

            # 添加标签
            tag_text = ""
            if tag == 3001:
                tag_text = "🔄 "  # 时事
            elif tag == 2012:
                tag_text = "🎭 "  # 娱乐
            elif tag == 4003:
                tag_text = "📰 "  # 新闻

            message += f"{rank}. {tag_text}{title}\n"

        return message

    def format_topic_detail_message(self, topic_data: Dict[str, Any]) -> str:
        """格式化话题详情消息
        Args:
            topic_data: 话题详情数据
        """
        if not topic_data:
            return "未找到相关话题详情，请确认关键词是否正确"

        title = topic_data.get("title", "未知话题")
        view_count = topic_data.get("view_count", 0)
        video_count = topic_data.get("video_count", 0)
        url = topic_data.get("url", "")

        message = f"【话题详情】 {title}\n\n"

        if view_count:
            message += f"观看量: {view_count}\n"
        if video_count:
            message += f"视频数: {video_count}\n"
        if url:
            message += f"链接: {url}\n"

        message += "\n【相关评论】\n"

        comments = topic_data.get("comments", [])
        if comments:
            for i, comment in enumerate(comments[:5]):  # 只显示前5条评论
                content = comment.get("content", "")
                user = comment.get("user", "")
                like_count = comment.get("like_count", 0)

                message += f"{i + 1}. {content}"
                if user:
                    message += f" - {user}"
                if like_count:
                    message += f" ({like_count}赞)"
                message += "\n"
        else:
            message += "暂无相关评论\n"

        return message

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        # 检查白名单权限
        if not self.is_user_authorized(msg.user_id, msg.group_id):
            return

        content = msg.raw_message.strip()

        # 解析命令和参数
        # 格式: 抖音热榜 [数量]
        if content == "抖音热榜":
            # 获取默认数量的热榜
            hot_data = self.get_latest_hot_list(10)
            response = self.format_hot_list_message(hot_data, 10)
            await msg.reply(text=response)
        elif content.startswith("抖音热榜 "):
            # 尝试解析热榜数量参数
            try:
                count = int(content.replace("抖音热榜 ", "").strip())
                hot_data = self.get_latest_hot_list(count)
                response = self.format_hot_list_message(hot_data, count)
                await msg.reply(text=response)
            except ValueError:
                await msg.reply(text="命令格式错误，正确格式：抖音热榜 [数量]")
        # 格式: 抖音热榜话题
        elif content == "抖音热榜话题":
            hot_data = self.get_latest_hot_list()
            response = self.format_trending_message(hot_data)
            await msg.reply(text=response)
        # 格式: 抖音话题详情 [关键词]
        elif content.startswith("抖音话题详情 "):
            keyword = content.replace("抖音话题详情 ", "").strip()
            if keyword:
                topic_data = self.get_topic_details(keyword)
                response = self.format_topic_detail_message(topic_data)
                await msg.reply(text=response)
            else:
                await msg.reply(text="请提供话题关键词，格式：抖音话题详情 [关键词]")

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        # 检查白名单权限
        if not self.is_user_authorized(msg.user_id):
            return

        content = msg.raw_message.strip()

        # 解析命令和参数
        # 格式: 抖音热榜 [数量]
        if content == "抖音热榜":
            # 获取默认数量的热榜
            hot_data = self.get_latest_hot_list(10)
            response = self.format_hot_list_message(hot_data, 10)
            await msg.reply(text=response)
        elif content.startswith("抖音热榜 "):
            # 尝试解析热榜数量参数
            try:
                count = int(content.replace("抖音热榜 ", "").strip())
                hot_data = self.get_latest_hot_list(count)
                response = self.format_hot_list_message(hot_data, count)
                await msg.reply(text=response)
            except ValueError:
                await msg.reply(text="命令格式错误，正确格式：抖音热榜 [数量]")
        # 格式: 抖音热榜话题
        elif content == "抖音热榜话题":
            hot_data = self.get_latest_hot_list()
            response = self.format_trending_message(hot_data)
            await msg.reply(text=response)
        # 格式: 抖音话题详情 [关键词]
        elif content.startswith("抖音话题详情 "):
            keyword = content.replace("抖音话题详情 ", "").strip()
            if keyword:
                topic_data = self.get_topic_details(keyword)
                response = self.format_topic_detail_message(topic_data)
                await msg.reply(text=response)
            else:
                await msg.reply(text="请提供话题关键词，格式：抖音话题详情 [关键词]")
