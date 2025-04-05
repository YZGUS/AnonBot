import os
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union, Callable

from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from hotsearch.api.xiaohongshu import XiaohongshuClient
from hotsearch.api.xiaohongshu import XiaohongshuHotSearchItem
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
    auth_token: str  # 小红书API授权令牌

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
            auth_token=api.get(
                "auth_token", "Bearer b4abc833-112a-11f0-8295-3292b700066c"
            ),
        )


class XiaohongshuPlugin(BasePlugin):
    """小红书插件"""

    name = "XiaohongshuPlugin"  # 插件名称
    version = "0.1.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    xiaohongshu_client = None
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

        # 初始化小红书客户端
        self.init_xiaohongshu_client()

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

    def init_xiaohongshu_client(self) -> None:
        """初始化小红书客户端"""
        try:
            auth_token = (
                self.config.auth_token
                if self.config
                else "Bearer b4abc833-112a-11f0-8295-3292b700066c"
            )
            data_dir = str(self.data_dir)

            self.xiaohongshu_client = XiaohongshuClient(
                auth_token=auth_token, save_data=True, data_dir=data_dir
            )
        except Exception as e:
            print(f"初始化小红书客户端失败: {e}")

    def check_config_update(self) -> bool:
        """检查配置是否更新"""
        if not self.config_path.exists():
            return False

        current_mtime = self.config_path.stat().st_mtime
        if current_mtime > self.config_last_modified:
            self.load_config()
            self.init_xiaohongshu_client()
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

            # 使用XiaohongshuClient获取数据
            if self.xiaohongshu_client:
                # 获取热搜数据
                self.latest_data = self.xiaohongshu_client.get_hot_search(as_model=True)
                await self.clean_old_files()
        except Exception as e:
            print(f"获取小红书数据失败: {e}")

    async def clean_old_files(self) -> None:
        """清理旧数据文件"""
        try:
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

    def get_hot_search_items(
        self, count: Optional[int] = None
    ) -> List[XiaohongshuHotSearchItem]:
        """获取热搜条目列表"""
        if not self.xiaohongshu_client or not self.latest_data:
            return []

        items = self.latest_data.items

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        return items

    def get_new_items(self) -> List[XiaohongshuHotSearchItem]:
        """获取新上榜热搜"""
        if not self.xiaohongshu_client or not self.latest_data:
            return []

        return self.xiaohongshu_client.get_new_items()

    def get_hot_items(self) -> List[XiaohongshuHotSearchItem]:
        """获取热门热搜"""
        if not self.xiaohongshu_client or not self.latest_data:
            return []

        return self.xiaohongshu_client.get_hot_items()

    def get_exclusive_items(self) -> List[XiaohongshuHotSearchItem]:
        """获取独家热搜"""
        if not self.xiaohongshu_client or not self.latest_data:
            return []

        return self.xiaohongshu_client.get_exclusive_items()

    def search_items(self, keyword: str) -> List[XiaohongshuHotSearchItem]:
        """搜索热搜条目"""
        if not self.xiaohongshu_client or not self.latest_data:
            return []

        return self.xiaohongshu_client.search_items(keyword)

    def get_timestamp_str(self) -> str:
        """获取格式化的时间戳字符串"""
        try:
            if (
                self.latest_data and self.latest_data.last_list_time > 946656000000
            ):  # 2000-01-01 以后的时间戳才有效
                # 确保时间戳有效（毫秒转秒）
                timestamp_ms = self.latest_data.last_list_time
                return datetime.fromtimestamp(timestamp_ms / 1000).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        except Exception as e:
            print(f"时间戳转换错误: {e}")

        # 默认返回当前时间
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def format_hot_list_message(
        self, items: List[XiaohongshuHotSearchItem], count: Optional[int] = None
    ) -> str:
        """格式化热榜消息"""
        if not items:
            return "❌ 获取小红书热榜失败，请稍后再试"

        timestamp = self.get_timestamp_str()

        # 限制条数
        if count and count > 0 and count < len(items):
            items = items[:count]

        message = f"📖 小红书热榜 ({timestamp})\n\n共{len(items)}条热榜\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            title = item.title
            view_num = item.view_num
            tag_type = item.tag_type

            # 前三名使用特殊标记
            if rank == 1:
                prefix = "🥇 "
            elif rank == 2:
                prefix = "🥈 "
            elif rank == 3:
                prefix = "🥉 "
            else:
                prefix = f"{rank}. "

            # 标签
            tag_str = f"[{tag_type}]" if tag_type and tag_type != "普通" else ""

            message += (
                f"{prefix}{title} {tag_str} 🔥 {view_num}\n🔗 链接: {item.www_url}\n"
            )

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「小红书热榜 数字」或「🍠热榜 数字」可指定获取的条数"

        return message

    def format_trending_message(self, items: List[XiaohongshuHotSearchItem]) -> str:
        """格式化热门话题消息"""
        if not items:
            return "❌ 获取小红书热门话题失败，请稍后再试"

        timestamp = self.get_timestamp_str()

        # 获取热门项目
        hot_items = [item for item in items if item.is_hot]

        message = f"🔍 小红书热门话题 ({timestamp})\n\n共{len(hot_items)}条热门话题\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(hot_items):
            rank = i + 1
            title = item.title
            view_num = item.view_num

            message += f"{rank}. {title} 🔥 {view_num}\n🔗 链接: {item.www_url}\n"

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「小红书笔记 关键词」可查询相关笔记详情"

        return message

    def format_new_items_message(self, items: List[XiaohongshuHotSearchItem]) -> str:
        """格式化新上榜热搜消息"""
        if not items:
            return "❌ 获取小红书新上榜热搜失败，请稍后再试"

        timestamp = self.get_timestamp_str()

        message = f"🆕 小红书新上榜热搜 ({timestamp})\n\n共{len(items)}条新上榜\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            title = item.title
            view_num = item.view_num

            message += f"{rank}. {title} 🔥 {view_num}\n🔗 链接: {item.www_url}\n"

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「小红书热榜」或「🍠热榜」可查看完整热榜内容"

        return message

    def format_search_results_message(
        self, keyword: str, items: List[XiaohongshuHotSearchItem]
    ) -> str:
        """格式化搜索结果消息"""
        if not items:
            return f"❌ 没有找到包含「{keyword}」的小红书热搜"

        timestamp = self.get_timestamp_str()

        message = f"🔍 小红书热搜 - 「{keyword}」搜索结果 ({timestamp})\n\n共找到{len(items)}条相关热搜\n━━━━━━━━━━━━━━━━━━\n\n"

        for i, item in enumerate(items):
            rank = i + 1
            title = item.title
            view_num = item.view_num
            tag_type = item.tag_type

            # 标签
            tag_str = f"[{tag_type}]" if tag_type and tag_type != "普通" else ""

            message += (
                f"{rank}. {title} {tag_str} 🔥 {view_num}\n🔗 链接: {item.www_url}\n"
            )

        message += f"━━━━━━━━━━━━━━━━━━\n📊 更新时间: {timestamp}\n💡 提示: 发送「小红书热榜」或「🍠热榜」可查看完整热榜内容"

        return message

    def parse_command(self, content: str) -> Tuple[str, Optional[str]]:
        """解析命令"""
        content = content.strip()

        # 简化的命令映射
        if content in ["小红书热榜", "🍠热榜"]:
            return "hot_list", None
        elif content == "小红书热门":
            return "hot_items", None
        elif content == "小红书新上榜":
            return "new_items", None

        # 带参数的命令处理
        hot_list_match = re.match(r"^(小红书热榜|🍠热榜)\s+(\d+)$", content)
        if hot_list_match:
            return "hot_list", hot_list_match.group(2)

        search_match = re.match(r"^小红书搜索\s+(.+)$", content)
        if search_match:
            return "search", search_match.group(1)

        return "", None

    async def handle_command(
        self, cmd_type: str, param: Optional[str]
    ) -> Union[str, None]:
        """处理命令并返回回复消息"""
        if cmd_type == "hot_list":
            count = int(param) if param else None
            items = self.get_hot_search_items(count)
            return self.format_hot_list_message(items, count)
        elif cmd_type == "hot_items":
            items = self.get_hot_items()
            return self.format_trending_message(items)
        elif cmd_type == "new_items":
            items = self.get_new_items()
            return self.format_new_items_message(items)
        elif cmd_type == "search":
            keyword = param
            items = self.search_items(keyword)
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
