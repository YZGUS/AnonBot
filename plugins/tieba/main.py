import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import tomli
from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from hotsearch.api.baidu_tieba import BaiduTiebaClient
from hotsearch.api.models.baidu_tieba import BaiduTiebaHotTopicItem
from scheduler import scheduler

bot = CompatibleEnrollment


@dataclass
class Config:
    """配置类"""

    whitelist_groups: List[int]  # 允许使用的群组ID列表
    whitelist_users: List[int]  # 允许使用的用户ID列表
    hot_count: int  # 热榜数量
    update_interval: int  # 数据更新间隔
    auth_token: str  # 百度贴吧API授权令牌

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})
        api = config_dict.get("api", {})

        return cls(
            whitelist_groups=whitelist.get("group_ids", []),
            whitelist_users=whitelist.get("user_ids", []),
            hot_count=data.get("hot_count", 20),
            update_interval=data.get("update_interval", 300),
            auth_token=api.get("auth_token", "Bearer b4abc833-112a-11f0-8295-3292b700066c"),
        )


class TiebaPlugin(BasePlugin):
    """百度贴吧插件"""

    name = "TiebaPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    tieba_client = None
    latest_data = None

    async def on_load(self):
        """插件加载时执行"""
        # 初始化插件
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 初始化百度贴吧客户端
        self.init_tieba_client()

        # 设置定时任务
        scheduler.add_random_minute_task(self.fetch_tieba, 0, 5)

        # 立即执行一次数据获取
        await self.fetch_tieba()

    def load_config(self) -> None:
        """加载配置"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            with open(self.config_path, "rb") as f:
                config_dict = tomli.load(f)

            self.config = Config.from_dict(config_dict)
            self.config_last_modified = self.config_path.stat().st_mtime
        except Exception as e:
            print(f"加载配置失败: {e}")
            # 使用默认配置
            self.config = Config.from_dict({})

    def init_tieba_client(self) -> None:
        """初始化百度贴吧客户端"""
        try:
            auth_token = self.config.auth_token if self.config else "Bearer b4abc833-112a-11f0-8295-3292b700066c"
            data_dir = str(self.data_dir)

            self.tieba_client = BaiduTiebaClient(
                auth_token=auth_token, save_data=True, data_dir=data_dir
            )
        except Exception as e:
            print(f"初始化百度贴吧客户端失败: {e}")

    def check_config_update(self) -> bool:
        """检查配置是否更新"""
        if not self.config_path.exists():
            return False

        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self.config_last_modified:
            self.load_config()
            self.init_tieba_client()
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

    async def fetch_tieba(self) -> None:
        """获取百度贴吧数据"""
        try:
            # 检查配置是否更新
            self.check_config_update()

            # 使用BaiduTiebaClient获取数据
            if self.tieba_client:
                # 获取热门话题数据
                self.latest_data = self.tieba_client.get_items(as_model=True)
                await self.clean_old_files()
        except Exception as e:
            print(f"获取百度贴吧数据失败: {e}")

    async def clean_old_files(self) -> None:
        """清理旧数据文件"""
        try:
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

    def get_hot_topics(self, count: Optional[int] = None) -> List[BaiduTiebaHotTopicItem]:
        """获取热门话题列表"""
        if not self.tieba_client or not self.latest_data:
            return []

        # 按讨论数量排序
        items = sorted(self.latest_data, key=lambda x: x.discuss_num, reverse=True)

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        return items

    def get_important_topics(self) -> List[BaiduTiebaHotTopicItem]:
        """获取重大话题"""
        if not self.tieba_client or not self.latest_data:
            return []

        # 筛选重大话题（topic_tag=2）
        return [item for item in self.latest_data if item.topic_tag == 2]

    def get_hot_tag_topics(self) -> List[BaiduTiebaHotTopicItem]:
        """获取热点话题"""
        if not self.tieba_client or not self.latest_data:
            return []

        # 筛选热点话题（topic_tag=1）
        return [item for item in self.latest_data if item.topic_tag == 1]

    def get_sports_topics(self) -> List[BaiduTiebaHotTopicItem]:
        """获取体育话题"""
        if not self.tieba_client or not self.latest_data:
            return []

        # 筛选体育话题（topic_tag=3）
        return [item for item in self.latest_data if item.topic_tag == 3]

    def search_topics(self, keyword: str) -> List[BaiduTiebaHotTopicItem]:
        """搜索话题"""
        if not self.tieba_client or not self.latest_data:
            return []

        # 标题和描述中包含关键词的话题
        return [item for item in self.latest_data if keyword in item.name or keyword in item.desc]

    def get_timestamp_str(self) -> str:
        """获取当前时间字符串"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def format_hot_topics_message(self, items: List[BaiduTiebaHotTopicItem], count: Optional[int] = None) -> str:
        """格式化热门话题消息"""
        if not items:
            return "❌ 获取百度贴吧热门话题失败，请稍后再试"

        timestamp = self.get_timestamp_str()

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        message = f"📊 百度贴吧热门话题 ({timestamp})\n\n共{len(items)}条热门话题\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            name = item.name
            desc = item.desc
            discuss_num = item.discuss_num

            # 前三名使用特殊标记
            if rank == 1:
                prefix = "🥇 "
            elif rank == 2:
                prefix = "🥈 "
            elif rank == 3:
                prefix = "🥉 "
            else:
                prefix = f"{rank}. "

            # 添加话题标签
            tag_str = ""
            if item.topic_tag == 1:
                tag_str = " [热点]"
            elif item.topic_tag == 2:
                tag_str = " [重大]"
            elif item.topic_tag == 3:
                tag_str = " [体育]"

            message += f"{prefix}{name}{tag_str}\n📝 {desc}\n💬 讨论数: {discuss_num}\n\n"

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「贴吧热榜 数字」可指定获取的条数"

        return message

    def format_search_results(self, keyword: str, items: List[BaiduTiebaHotTopicItem]) -> str:
        """格式化搜索结果消息"""
        if not items:
            return f"❌ 没有找到包含「{keyword}」的贴吧热门话题"

        timestamp = self.get_timestamp_str()

        message = f"🔍 百度贴吧热门话题 - 「{keyword}」搜索结果 ({timestamp})\n\n共找到{len(items)}条相关话题\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            name = item.name
            desc = item.desc
            discuss_num = item.discuss_num

            # 添加话题标签
            tag_str = ""
            if item.topic_tag == 1:
                tag_str = " [热点]"
            elif item.topic_tag == 2:
                tag_str = " [重大]"
            elif item.topic_tag == 3:
                tag_str = " [体育]"

            message += f"{rank}. {name}{tag_str}\n📝 {desc}\n💬 讨论数: {discuss_num}\n\n"

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「贴吧热榜」可查看完整热榜内容"

        return message

    async def handle_command(self, cmd_type: str, param: Optional[str]) -> Union[str, None]:
        """处理命令并返回回复消息"""
        if cmd_type == "hot_topics":
            count = int(param) if param else None
            items = self.get_hot_topics(count)
            return self.format_hot_topics_message(items, count)
        elif cmd_type == "important_topics":
            items = self.get_important_topics()
            return self.format_hot_topics_message(items)
        elif cmd_type == "hot_tag_topics":
            items = self.get_hot_tag_topics()
            return self.format_hot_topics_message(items)
        elif cmd_type == "sports_topics":
            items = self.get_sports_topics()
            return self.format_hot_topics_message(items)
        elif cmd_type == "search":
            keyword = param
            items = self.search_topics(keyword)
            return self.format_search_results(keyword, items)
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

        # 直接在这里处理命令和参数，不再使用parse_command
        cmd_type = ""
        param = None

        # 命令映射
        if content in ["贴吧热榜", "百度贴吧"]:
            cmd_type = "hot_topics"
        elif content == "贴吧重大":
            cmd_type = "important_topics"
        elif content == "贴吧热点":
            cmd_type = "hot_tag_topics"
        elif content == "贴吧体育":
            cmd_type = "sports_topics"
        else:
            # 带参数的命令处理
            hot_list_match = re.match(r"^(贴吧热榜|百度贴吧)\s+(\d+)$", content)
            if hot_list_match:
                cmd_type = "hot_topics"
                param = hot_list_match.group(2)
            else:
                search_match = re.match(r"^贴吧搜索\s+(.+)$", content)
                if search_match:
                    cmd_type = "search"
                    param = search_match.group(1)

        if not cmd_type:
            return

        # 处理命令
        reply_message = await self.handle_command(cmd_type, param)
        if reply_message:
            await msg.reply(text=reply_message)
