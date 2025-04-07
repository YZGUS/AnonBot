import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from hotsearch.api import TencentNewsClient
from hotsearch.api.models.tencent_news import (
    TencentNewsHotSearchItem,
)
from utils import scheduler

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
            return "暂无热榜数据"

        if count is not None and count > 0:
            items = items[:count]

        message = "📰 腾讯新闻热榜 Top{}\n".format(len(items))
        message += "====================\n"

        for index, item in enumerate(items):
            message += "{}. {}\n".format(index + 1, item.title)

            # 添加热度信息（如果有）
            if item.hot_score:
                message += "   🔥 热度: {}\n".format(item.hot_score)

            # 添加摘要信息（如果有）
            if item.desc:
                # 限制摘要长度，避免消息过长
                short_desc = (
                    item.desc[:60] + "..." if len(item.desc) > 60 else item.desc
                )
                message += "   📝 {}\n".format(short_desc)

            # 添加链接
            message += "   🔗 链接: {}\n".format(item.www_url)

            # 添加分隔线
            if index < len(items) - 1:
                message += "--------------------\n"

        message += "====================\n"
        message += "💡 回复「腾讯热榜详情 序号」查看完整内容，如：腾讯热榜详情 1"
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
            message += f"{i + 1}. {item.title}\n"
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

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群组消息"""
        content = msg.raw_message.strip()
        group_id = msg.group_id
        user_id = msg.user_id

        # 检查用户授权
        if not self.is_user_authorized(user_id, group_id):
            return

        # 刷新配置
        if self.check_config_update():
            self.load_config()

        # 腾讯热榜命令处理
        if content.startswith("腾讯热榜"):
            # 检查是否请求简约版
            if "简约版" in content:
                count_match = re.search(r"腾讯热榜简约版\s*(\d+)", content)
                count = int(count_match.group(1)) if count_match else 10
                await self.send_hot_list_simple(msg, count)
                return

            # 检查是否请求详情版
            if "详情版" in content:
                count_match = re.search(r"腾讯热榜详情版\s*(\d+)", content)
                count = int(count_match.group(1)) if count_match else 10
                await self.send_hot_list_detail(msg, count)
                return

            # 按序号查询新闻详情
            num_match = re.search(r"腾讯热榜详情\s*(\d+)", content)
            if num_match:
                index = int(num_match.group(1))
                await self.send_news_by_index(msg, index)
                return

            # 处理常规热榜请求
            count_match = re.search(r"腾讯热榜\s*(\d+)", content)
            count = int(count_match.group(1)) if count_match else 10
            await self.send_hot_list_detail(msg, count)
            return

        # 关键词搜索新闻
        if content.startswith("腾讯新闻"):
            keyword = content[5:].strip()
            if keyword:
                await self.send_news_search(msg, keyword)
            return

    async def send_hot_list_simple(self, msg, count: int = 10):
        """发送简约版热榜"""
        hot_list = self.get_latest_hot_list(count)
        if not hot_list:
            await msg.reply(text="获取热榜数据失败，请稍后再试")
            return

        # 简约版只展示序号和标题
        message = "📰 腾讯新闻热榜简约版 Top{}\n".format(len(hot_list))
        message += "====================\n"

        for index, item in enumerate(hot_list):
            message += "{}. {}\n".format(index + 1, item.title)

        message += "====================\n"
        message += "💡 回复「腾讯热榜详情 序号」查看详情，如：腾讯热榜详情 1"

        await msg.reply(text=message)

    async def send_hot_list_detail(self, msg, count: int = 10):
        """发送详情版热榜"""
        hot_list = self.get_latest_hot_list(count)
        if not hot_list:
            await msg.reply(text="获取热榜数据失败，请稍后再试")
            return

        message = self.format_hot_list_message(hot_list, count)
        await msg.reply(text=message)

    async def send_news_by_index(self, msg, index: int):
        """根据序号发送新闻详情"""
        # 获取热榜数据
        hot_list = self.get_latest_hot_list()
        if not hot_list:
            await msg.reply(text="获取热榜数据失败，请稍后再试")
            return

        # 检查序号是否有效
        if index < 1 or index > len(hot_list):
            await msg.reply(
                text=f"序号 {index} 超出范围，当前热榜共有 {len(hot_list)} 条新闻"
            )
            return

        # 获取指定序号的新闻
        news_item = hot_list[index - 1]
        message = self.format_news_item_detail(news_item)
        await msg.reply(text=message)

    def format_news_item_detail(self, item: TencentNewsHotSearchItem) -> str:
        """格式化单条新闻详情"""
        message = "📰 新闻详情\n"
        message += "====================\n"
        message += f"🔖 标题：{item.title}\n"
        message += f"🔗 链接：{item.www_url}\n"

        if item.hot_score:
            message += f"🔥 热度：{item.hot_score}\n"

        if item.desc:
            message += f"\n📝 摘要：{item.desc}\n"

        if item.comment_num:
            message += f"💬 评论数：{item.comment_num}\n"

        if item.like_num:
            message += f"👍 点赞数：{item.like_num}\n"

        message += "===================="
        return message

    async def send_news_search(self, msg, keyword: str):
        """搜索并发送新闻"""
        search_results = self.search_news(keyword)
        if not search_results:
            await msg.reply(text=f"未找到与'{keyword}'相关的新闻")
            return

        message = self.format_news_detail_message(search_results, keyword)
        await msg.reply(text=message)
