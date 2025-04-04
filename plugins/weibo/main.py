import json
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

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
    comment_count: int  # 评论数量

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})

        return cls(
            whitelist_groups=whitelist.get("group_ids", []),
            whitelist_users=whitelist.get("user_ids", []),
            hot_count=data.get("hot_count", 10),
            comment_count=data.get("comment_count", 10),
        )


class WeiboDataCollector:
    """微博数据收集器"""

    def __init__(
            self,
            headers_path: Path,
            data_dir: Path,
            hot_count: int = 10,
            comment_count: int = 10,
            debug_mode: bool = False,
    ):
        self.headers = self._load_headers(headers_path)
        self.data_dir = data_dir
        self.hot_count = hot_count
        self.comment_count = comment_count
        self.debug_mode = debug_mode  # 调试模式标志，决定是否保存中间数据

    def _load_headers(self, headers_path: Path) -> Dict[str, str]:
        """加载请求头配置"""
        try:
            if headers_path.exists():
                with open(headers_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"警告: 请求头配置文件不存在: {headers_path}")
                return {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                }
        except Exception as e:
            print(f"加载请求头配置出错: {str(e)}")
            return {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            }

    def get_weibo_hot(self) -> Dict[str, Any]:
        """获取微博热榜数据"""
        url = "https://www.weibo.com/ajax/side/hotSearch"
        try:
            print(f"开始请求微博热榜: {url}")
            response = requests.get(url, headers=self.headers)
            print(f"请求状态码: {response.status_code}")

            if response.status_code != 200:
                print(f"获取热榜失败，状态码: {response.status_code}")
                return {}

            return response.json()
        except Exception as e:
            print(f"请求失败: {str(e)}")
            return {}

    def get_topic_comments(self, topic_word: str) -> List[Dict[str, Any]]:
        """获取话题评论

        Args:
            topic_word: 话题关键词
        """
        if not topic_word:
            return []

        # 使用话题关键词构造搜索URL
        search_word = topic_word.replace("#", "")  # 移除可能的#标签
        comment_url = f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{search_word}"

        try:
            print(f"开始请求话题相关微博: {comment_url}")
            response = requests.get(comment_url, headers=self.headers)

            if response.status_code != 200:
                print(f"获取话题相关微博失败，状态码: {response.status_code}")
                return []

            # 解析返回的数据，获取热门微博ID
            response_data = response.json()
            cards = response_data.get("data", {}).get("cards", [])

            # 如果没有数据，返回空列表
            if not cards:
                print(f"未找到话题 '{topic_word}' 的相关微博")
                return []

            # 模拟评论数据结构
            # 由于无法直接获取评论，我们使用微博内容作为"评论"
            comments = []
            for card in cards[: self.comment_count]:
                mblog = card.get("mblog", {})
                if not mblog:
                    continue

                comments.append(
                    {
                        "comment_id": mblog.get("id", f"weibo_{len(comments)}"),
                        "content": mblog.get("text_raw", mblog.get("text", "无内容")),
                        "like_count": mblog.get("attitudes_count", 0),
                        "user": mblog.get("user", {}).get("screen_name", "未知用户"),
                        "created_at": mblog.get("created_at", "未知时间"),
                    }
                )

                if len(comments) >= self.comment_count:
                    break

            return comments
        except Exception as e:
            print(f"获取话题相关微博失败: {str(e)}")
            return []

    def collect_data(self) -> Dict[str, Any]:
        """收集微博热榜数据"""
        # 获取热榜数据
        hot_data = self.get_weibo_hot()
        if not hot_data:
            print("获取热榜失败")
            return {}

        # 数据结构设计
        result = {
            "realtime_topics": [],
            "hot_topics": [],
            "timestamp": int(time.time()),
            "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # 解析实时热搜，根据配置的hot_count限制数量
        realtime = hot_data.get("data", {}).get("realtime", [])[: self.hot_count]
        for item in realtime:
            # 生成一个模拟的话题ID
            word = item.get("word", "")
            topic_id = f"weibo_topic_{item.get('realpos', 0)}_{hash(word) % 10000000}"

            topic = {
                "rank": item.get("realpos"),
                "title": item.get("note"),
                "topic_id": topic_id,  # 使用模拟ID
                "word": word,  # 保存原始关键词，用于搜索
                "url": f"https://s.weibo.com/weibo?q={word}",
                "hot_value": item.get("num"),
                "label": item.get("label_name"),
                "comments": self.get_topic_comments(word),
            }
            result["realtime_topics"].append(topic)
            time.sleep(2)  # 请求间隔，防止被封

        # 解析热门热搜（hotgov字段）
        # 由于API返回的可能是单个对象而非数组，需要特殊处理
        hotgov = hot_data.get("data", {}).get("hotgov", {})
        if hotgov:
            # 如果是单个对象，包装为列表
            hot_items = [hotgov] if isinstance(hotgov, dict) else []

            # 如果是数组，直接使用
            if isinstance(hotgov, list):
                hot_items = hotgov[: self.hot_count]

            # 处理热门话题
            for i, item in enumerate(hot_items):
                word = item.get("word", "")
                topic_id = f"weibo_hotgov_{i}_{hash(word) % 10000000}"

                topic = {
                    "rank": i + 1,  # 添加序号
                    "title": item.get("name", word),
                    "topic_id": topic_id,  # 使用模拟ID
                    "word": word,  # 保存原始关键词
                    "url": item.get("url", f"https://s.weibo.com/weibo?q={word}"),
                    "hot_value": item.get("num", ""),
                    "label": item.get("label_name", ""),
                    "comments": self.get_topic_comments(word),
                }
                result["hot_topics"].append(topic)
                time.sleep(2)  # 请求间隔，防止被封

        # 检查热门话题列表是否为空，如果为空则尝试使用hotgovs字段
        if not result["hot_topics"]:
            hotgovs = hot_data.get("data", {}).get("hotgovs", [])[: self.hot_count]
            for i, item in enumerate(hotgovs):
                word = item.get("word", "")
                topic_id = f"weibo_hotgovs_{i}_{hash(word) % 10000000}"

                topic = {
                    "rank": i + 1,  # 添加序号
                    "title": item.get("name", word),
                    "topic_id": topic_id,  # 使用模拟ID
                    "word": word,  # 保存原始关键词
                    "url": item.get("url", f"https://s.weibo.com/weibo?q={word}"),
                    "hot_value": item.get("num", ""),
                    "label": item.get("label_name", ""),
                    "comments": self.get_topic_comments(word),
                }
                result["hot_topics"].append(topic)
                time.sleep(2)  # 请求间隔，防止被封

        return result

    def save_data(self, data: Dict[str, Any]) -> str:
        """保存数据到JSON文件，使用年月日-小时的文件夹格式"""
        if not data:
            return ""

        # 创建年月日-小时格式的文件夹
        now = datetime.now()
        folder_name = now.strftime("%Y%m%d-%H")
        folder_path = self.data_dir / folder_name
        folder_path.mkdir(exist_ok=True, parents=True)

        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"weibo_hot_{timestamp}.json"
        filepath = folder_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"数据已保存至 {filepath}")
        return str(filepath)


class WeiboPlugin(BasePlugin):
    name = "WeiboPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    headers_path = None
    config_last_modified = 0
    data_dir = None
    latest_data_file = None
    debug_mode = False  # 调试模式，决定是否保存中间数据文件

    async def on_load(self):
        """插件加载时调用"""
        print(f"正在加载 {self.name} 插件...")

        # 初始化目录和文件路径
        self.config_path = Path(__file__).parent / "config" / "config.toml"
        self.headers_path = Path(__file__).parent / "config" / "headers.json"
        self.data_dir = Path(__file__).parent / "data"

        # 确保目录存在
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 设置定时任务，每小时采集一次数据
        scheduler.add_random_minute_task(self.fetch_weibo_hot, 0, 5)
        scheduler.add_task(self.check_config_update, 30)
        print(f"{self.name} 插件加载完成！")

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "rb") as f:
                    config_dict = tomllib.load(f)
                self.config = Config.from_dict(config_dict)
                self.config_last_modified = self.config_path.stat().st_mtime
                print(f"成功加载配置")
            else:
                print(f"配置文件不存在: {self.config_path}")
                self.config = Config.from_dict({})
        except Exception as e:
            print(f"加载配置出错: {str(e)}")
            self.config = Config.from_dict({})

    def check_config_update(self) -> bool:
        """检查配置是否更新"""
        try:
            if not self.config_path.exists():
                return False

            last_modified = self.config_path.stat().st_mtime
            if last_modified > self.config_last_modified:
                self.load_config()
                return True
            return False
        except Exception as e:
            print(f"检查配置更新出错: {str(e)}")
            return False

    def is_user_authorized(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """检查用户是否有权限使用插件功能"""
        # 确保配置已加载
        if not self.config:
            self.load_config()

        # 检查用户ID是否在白名单中
        if user_id in self.config.whitelist_users:
            return True

        # 检查群组ID是否在白名单中（如果提供了群组ID）
        if group_id and group_id in self.config.whitelist_groups:
            return True

        return False

    async def fetch_weibo_hot(self) -> None:
        """获取微博热榜数据（定时任务）"""
        print("开始采集微博热榜数据...")

        try:
            # 检查配置是否需要更新
            self.check_config_update()

            # 创建数据收集器
            collector = WeiboDataCollector(
                headers_path=self.headers_path,
                data_dir=self.data_dir,
                hot_count=self.config.hot_count if self.config else 10,
                comment_count=self.config.comment_count if self.config else 10,
                debug_mode=self.debug_mode,
            )

            # 收集数据
            data = collector.collect_data()

            if data:
                # 保存数据
                data_file = collector.save_data(data)
                self.latest_data_file = data_file
                print(f"微博热榜数据采集完成，保存到: {data_file}")
            else:
                print("微博热榜数据采集失败")
        except Exception as e:
            print(f"采集微博热榜数据出错: {str(e)}")

    def get_latest_hot_list(self, count: int = None) -> Dict[str, Any]:
        """获取最新的热榜数据，优先获取距离当前最近的一次数据"""
        try:
            # 如果没有指定count，使用配置中的hot_count
            if count is None and self.config:
                count = self.config.hot_count
            elif count is None:
                count = 10

            # 获取所有日期文件夹，按照最新的顺序排序
            data_folders = sorted(
                [f for f in self.data_dir.glob("*-*") if f.is_dir()],
                key=lambda x: x.name,
                reverse=True,
            )

            if not data_folders:
                return {}

            # 获取最新的文件夹
            latest_folder = data_folders[0]

            # 获取文件夹中的所有JSON文件
            data_files = list(latest_folder.glob("weibo_hot_*.json"))
            if not data_files:
                return {}

            # 找到最新的文件
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            self.latest_data_file = str(latest_file)

            # 读取数据
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 限制数量
            if "realtime_topics" in data:
                data["realtime_topics"] = data["realtime_topics"][:count]
            if "hot_topics" in data:
                data["hot_topics"] = data["hot_topics"][:count]

            return data
        except Exception as e:
            print(f"获取最新热榜数据出错: {str(e)}")
            return {}

    def format_hot_list_message(
            self, hot_data: Dict[str, Any], count: int = None
    ) -> str:
        """格式化热榜消息，只返回热榜，不返回其他信息"""
        if not hot_data:
            return "未找到热榜数据"

        # 如果没有指定count，使用配置中的hot_count
        if count is None and self.config:
            count = self.config.hot_count
        elif count is None:
            count = 10

        realtime = hot_data.get("realtime_topics", [])[:count]
        hot_topics = hot_data.get("hot_topics", [])[:count]
        collected_at = hot_data.get("collected_at", "未知")

        message = f"📊 微博热榜 (更新时间: {collected_at})\n\n"

        # 实时热搜
        message += "🔥 实时热搜:\n"
        for i, topic in enumerate(realtime):
            rank = topic.get("rank", i + 1)
            title = topic.get("title", "未知")
            hot = topic.get("hot_value", "")
            label = topic.get("label", "")

            label_str = f"[{label}]" if label else ""
            hot_str = f"{hot}" if hot else ""

            message += f"{rank}. {title} {label_str} {hot_str}\n"

        # 热门话题
        if hot_topics:
            message += "\n📈 热门话题:\n"
            for i, topic in enumerate(hot_topics):
                title = topic.get("title", "未知")
                hot = topic.get("hot_value", "")
                label = topic.get("label", "")

                label_str = f"[{label}]" if label else ""
                hot_str = f"{hot}" if hot else ""

                message += f"{i + 1}. {title} {label_str} {hot_str}\n"

        return message

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群消息事件"""
        if not self.is_user_authorized(msg.user_id, msg.group_id):
            return

        content = msg.raw_message.strip()

        # 处理微博热榜命令
        if content == "微博热榜":
            # 获取热榜数据
            hot_data = self.get_latest_hot_list()
            if not hot_data:
                await msg.reply(text="获取微博热榜数据失败")
                return

            # 格式化并发送消息
            message = self.format_hot_list_message(hot_data)
            await msg.reply(text=message)
            return

        # 处理微博话题详情命令 - 暂不返回详情
        if content.startswith("微博话题 "):
            await msg.reply(text="暂不支持话题详情查询")
            return

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息事件"""
        if not self.is_user_authorized(msg.user_id):
            return

        content = msg.raw_message.strip()

        # 处理微博热榜命令
        if content == "微博热榜":
            # 获取热榜数据
            hot_data = self.get_latest_hot_list()
            if not hot_data:
                await msg.reply(text="获取微博热榜数据失败")
                return

            # 格式化并发送消息
            message = self.format_hot_list_message(hot_data)
            await msg.reply(text=message)
            return

        # 处理微博话题详情命令 - 暂不返回详情
        if content.startswith("微博话题 "):
            await msg.reply(text="暂不支持话题详情查询")
            return
