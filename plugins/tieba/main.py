#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import tomli
from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

# 从hotsearch.api导入BaiduTiebaClient替代rebang_core
from hotsearch.api import BaiduTiebaClient
from hotsearch.api.models.baidu_tieba import BaiduTiebaHotTopicItem, BaiduTiebaHotTopics
from scheduler import scheduler

# 配置日志
logger = logging.getLogger("tieba")

# 兼容装饰器
bot = CompatibleEnrollment


@dataclass
class Config:
    """配置类"""

    white_list: List[int]  # 允许使用的用户ID列表
    group_white_list: List[int]  # 允许使用的群组ID列表
    update_interval: int  # 数据更新间隔（秒）
    max_items: int  # 默认展示条数
    max_files_per_day: int  # 每天最多保存的文件数
    keep_days: int  # 保留最近几天的数据
    log_level: str  # 日志级别
    templates: Dict[str, str]  # 消息模板
    category_emoji: Dict[str, str]  # 分类标签对应的emoji
    api_token: str  # API授权令牌

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        basic = config_dict.get("basic", {})
        access = config_dict.get("access", {})
        storage = config_dict.get("storage", {})
        ui = config_dict.get("ui", {})
        tieba_specific = config_dict.get("tieba_specific", {})
        api = config_dict.get("api", {})

        return cls(
            white_list=access.get("white_list", []),
            group_white_list=access.get("group_white_list", []),
            update_interval=basic.get("update_interval", 300),
            max_items=basic.get("max_items", 10),
            max_files_per_day=storage.get("max_files_per_day", 20),
            keep_days=storage.get("keep_days", 7),
            log_level=basic.get("log_level", "INFO"),
            templates={
                "header": ui.get("header_template", "📊 百度贴吧热榜 ({time})\n\n"),
                "item": ui.get(
                    "item_template", "{rank}. {highlight}{title}{hot_tag}\n"
                ),
                "footer": ui.get(
                    "footer_template",
                    "\n💡 提示: 发送「贴吧热榜 数字」可指定获取的条数，如「贴吧热榜 20」",
                ),
            },
            category_emoji=tieba_specific.get(
                "category_emoji",
                {
                    "热": "🔥",
                    "新": "✨",
                    "爆": "💥",
                    "精": "💎",
                },
            ),
            api_token=api.get("token", "Bearer b4abc833-112a-11f0-8295-3292b700066c"),
        )


class TiebaDataCollector:
    """百度贴吧数据收集器"""

    def __init__(self, data_dir: Path, api_token: str = None):
        """初始化数据收集器

        Args:
            data_dir: 数据保存目录
            api_token: API授权令牌，如果为None则使用默认值
        """
        self.data_dir = data_dir
        self.api_token = api_token

        # 初始化API客户端
        self.client = BaiduTiebaClient(
            auth_token=(
                api_token
                if api_token
                else "Bearer b4abc833-112a-11f0-8295-3292b700066c"
            ),
            save_data=True,
            data_dir=str(data_dir),
        )

    def get_tieba_hot(self) -> BaiduTiebaHotTopics:
        """获取百度贴吧热榜数据"""
        try:
            # 使用BaiduTiebaClient获取数据
            data = self.client.get_hot_topics()
            if not data or not hasattr(data, "items"):
                logger.error("获取百度贴吧热榜数据失败：数据为空")
                return BaiduTiebaHotTopics([], 0, 0, 0, 0, 0)
            return data
        except Exception as e:
            logger.error(f"获取百度贴吧热榜数据失败: {e}")
            return BaiduTiebaHotTopics([], 0, 0, 0, 0, 0)

    def _get_category_from_tag(self, tag: int) -> str:
        """根据话题标签获取分类"""
        category_map = {
            0: "",  # 普通
            1: "热",  # 热点
            2: "爆",  # 重大
            3: "新",  # 体育
        }
        return category_map.get(tag, "")

    def collect_data(self) -> BaiduTiebaHotTopics:
        """收集百度贴吧热榜数据并整合"""
        return self.get_tieba_hot()

    def save_data(self, data: BaiduTiebaHotTopics) -> str:
        """保存数据到JSON文件，使用年月日-小时的文件夹格式"""
        if not data or not data.items:
            return ""

        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        date_dir = self.data_dir / date_str
        date_dir.mkdir(exist_ok=True, parents=True)

        timestamp = now.strftime("%Y%m%d%H%M%S")
        filename = f"tieba_hot_{timestamp}.json"
        filepath = date_dir / filename

        # 转换为JSON可序列化的字典
        result = {
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [vars(item) for item in data.items],
            "last_list_time": data.last_list_time,
            "next_refresh_time": data.next_refresh_time,
            "version": data.version,
            "current_page": data.current_page,
            "total_page": data.total_page,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return str(filepath)


class TiebaPlugin(BasePlugin):
    """百度贴吧热榜插件 - 获取百度贴吧实时热榜数据"""

    name = "TiebaPlugin"  # 插件名称
    version = "1.0.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    latest_data_file = None
    data_collector = None

    async def on_load(self):
        """初始化插件"""
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 加载配置
        self.load_config()

        # 设置日志级别
        log_level = self.config.log_level.upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        # 初始化数据收集器
        self.data_collector = TiebaDataCollector(self.data_dir, self.config.api_token)

        # 设置定时任务，定期获取热榜数据
        scheduler.add_random_minute_task(self.fetch_tieba_hot, 0, 5)

    def load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    config_dict = tomli.load(f)
                self.config = Config.from_dict(config_dict)
                self.config_last_modified = self.config_path.stat().st_mtime
                logger.info(f"成功加载配置文件: {self.config_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self.config = Config.from_dict({})
        else:
            logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
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
        if not self.config.white_list and not self.config.group_white_list:
            return True

        # 检查用户ID是否在白名单中
        if user_id in self.config.white_list:
            return True

        # 检查群组ID是否在白名单中
        if group_id and group_id in self.config.group_white_list:
            return True

        return False

    async def fetch_tieba_hot(self) -> None:
        """获取并保存百度贴吧热榜数据"""
        try:
            # 检查配置更新
            self.check_config_update()

            # 获取数据
            hot_topics = self.data_collector.collect_data()
            if hot_topics and hot_topics.items:
                # 保存数据到文件
                data_file = self.data_collector.save_data(hot_topics)
                if data_file:
                    self.latest_data_file = data_file
                    logger.info(f"成功获取并保存百度贴吧热榜数据: {data_file}")
            else:
                logger.warning("获取百度贴吧热榜数据失败或数据为空")

            # 清理旧文件
            await self.clean_old_files()
        except Exception as e:
            logger.error(f"获取百度贴吧热榜数据出错: {e}")

    def get_latest_hot_topics(self, count: int = None) -> BaiduTiebaHotTopics:
        """获取最新的热榜数据

        Args:
            count: 获取的条目数量

        Returns:
            热榜数据
        """
        # 查找最新的数据文件
        latest_file = self.latest_data_file
        if not latest_file:
            try:
                for date_dir in sorted(self.data_dir.glob("20*"), reverse=True):
                    if date_dir.is_dir():
                        files = list(date_dir.glob("tieba_hot_*.json"))
                        if files:
                            files.sort(key=lambda x: x.name, reverse=True)
                            latest_file = str(files[0])
                            break
            except Exception as e:
                logger.error(f"查找最新数据文件失败: {e}")

        # 如果找不到数据文件，尝试获取最新数据
        if not latest_file:
            hot_topics = self.data_collector.collect_data()
            if hot_topics and hot_topics.items:
                filepath = self.data_collector.save_data(hot_topics)
                if filepath:
                    self.latest_data_file = filepath
            return hot_topics

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 验证数据有效性
            if data and "items" in data:
                # 如果数据超过30分钟，尝试更新
                timestamp = data.get("timestamp", "")
                if timestamp:
                    data_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    if (now - data_time).total_seconds() > 1800:  # 30分钟
                        logger.info("缓存数据超过30分钟，尝试更新")
                        fresh_data = self.data_collector.collect_data()
                        if fresh_data and fresh_data.items:
                            data = {
                                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                                "items": [vars(item) for item in fresh_data.items],
                                "last_list_time": fresh_data.last_list_time,
                                "next_refresh_time": fresh_data.next_refresh_time,
                                "version": fresh_data.version,
                                "current_page": fresh_data.current_page,
                                "total_page": fresh_data.total_page,
                            }
                            filepath = self.data_collector.save_data(fresh_data)
                            if filepath:
                                self.latest_data_file = filepath

                # 转换为BaiduTiebaHotTopics对象
                items = [
                    BaiduTiebaHotTopicItem.from_dict(item)
                    for item in data.get("items", [])
                ]

                # 限制数量
                if count is not None and count > 0:
                    items = items[:count]

                return BaiduTiebaHotTopics(
                    items=items,
                    last_list_time=data.get("last_list_time", 0),
                    next_refresh_time=data.get("next_refresh_time", 0),
                    version=data.get("version", 0),
                    current_page=data.get("current_page", 0),
                    total_page=data.get("total_page", 0),
                )
            else:
                logger.warning("缓存数据无效，尝试获取新数据")
                return self.data_collector.collect_data()
        except Exception as e:
            logger.error(f"读取最新热榜数据出错: {e}")
            return self.data_collector.collect_data()

    async def clean_old_files(self) -> None:
        """清理旧数据文件"""
        try:
            # 按日期目录清理
            all_folders = sorted(
                [d for d in self.data_dir.iterdir() if d.is_dir()],
                key=lambda x: x.name,
                reverse=True,
            )

            # 保留最近几天的数据
            keep_days = self.config.keep_days
            if len(all_folders) > keep_days:
                # 清理旧日期的所有数据
                for old_dir in all_folders[keep_days:]:
                    logger.debug(f"清理旧数据目录: {old_dir}")
                    for file in old_dir.iterdir():
                        if file.is_file():
                            file.unlink()
                    old_dir.rmdir()

            # 对保留的日期，控制每个日期文件夹内的文件数量
            for date_dir in all_folders[:keep_days]:
                files = sorted(
                    [f for f in date_dir.iterdir() if f.is_file()],
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
                )

                max_files = self.config.max_files_per_day
                if len(files) > max_files:
                    for old_file in files[max_files:]:
                        logger.debug(f"清理过多的数据文件: {old_file}")
                        old_file.unlink()
        except Exception as e:
            logger.error(f"清理旧文件出错: {e}")

    def format_hot_list_message(
            self,
            hot_topics: BaiduTiebaHotTopics,
            count: int = None,
            show_detail: bool = False,
    ) -> str:
        """格式化热榜消息

        Args:
            hot_topics: 热榜数据
            count: 显示条目数量
            show_detail: 是否显示详情

        Returns:
            格式化后的消息
        """
        if not hot_topics or not hot_topics.items:
            return "⚠️ 暂无百度贴吧热榜数据，请稍后再试"

        now = datetime.now()
        update_time = now.strftime("%Y-%m-%d %H:%M:%S")
        hot_items = hot_topics.items

        # 限制条目数量
        if count is None:
            count = self.config.max_items
        hot_items = hot_items[:count]

        # 构建消息
        message = f"📱 {self.config.templates['header'].format(time=update_time)}"

        # 添加数据统计
        total_items = len(hot_topics.items)
        highlighted_count = sum(1 for item in hot_topics.items if item.topic_tag > 0)
        message += f"共{total_items}条热门帖子，{highlighted_count}条热门内容\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        # 添加热榜条目
        for idx, item in enumerate(hot_items, start=1):
            title = item.name
            topic_id = item.id

            # 构建排名前缀（前三名使用特殊emoji）
            if idx == 1:
                rank_prefix = "🥇 "
            elif idx == 2:
                rank_prefix = "🥈 "
            elif idx == 3:
                rank_prefix = "🥉 "
            else:
                rank_prefix = f"{idx}. "

            # 设置高亮标记
            highlight = ""
            if item.topic_tag > 0:
                category = self._get_category_from_tag(item.topic_tag)
                if category:
                    emoji = self.config.category_emoji.get(category, "")
                    if emoji:
                        highlight = f"{emoji} "

            # 设置热度值
            hot_value = item.discuss_num
            hot_tag = ""
            if hot_value:
                if hot_value >= 10000:
                    hot_tag = f" 🔥{hot_value / 10000:.1f}万"
                else:
                    hot_tag = f" 🔥{hot_value}"

            # 添加ID信息，方便用户查询详情
            id_info = f" [ID:{topic_id}]" if topic_id else ""

            # 格式化单个条目
            message += f"{rank_prefix}{highlight}{title}{id_info}{hot_tag}\n"

            # 添加详情
            if show_detail and item.desc:
                message += f"   📝 {item.desc}\n"

            # 添加分隔符，每三个条目添加一次
            if idx % 3 == 0 and idx < len(hot_items):
                message += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"

        # 添加页脚
        message += "\n━━━━━━━━━━━━━━━━━━\n"
        message += f"📊 更新时间: {update_time}\n"
        message += "💡 使用提示：\n"
        message += "• 发送「贴吧热榜」查看贴吧热榜\n"
        message += "• 发送「贴吧热榜 15」指定显示15条\n"
        message += "• 发送「贴吧热榜详情」查看带描述的热榜\n"
        message += "• 发送「贴吧热榜ID 123456」查看指定话题详情\n"

        return message

    def _get_category_from_tag(self, tag: int) -> str:
        """根据话题标签获取分类"""
        category_map = {
            0: "",  # 普通
            1: "热",  # 热点
            2: "爆",  # 重大
            3: "新",  # 体育
        }
        return category_map.get(tag, "")

    def format_topic_detail(
            self, topic_id: str, hot_topics: BaiduTiebaHotTopics
    ) -> str:
        """格式化话题详情信息

        Args:
            topic_id: 话题ID
            hot_topics: 热榜数据

        Returns:
            格式化后的话题详情
        """
        if not hot_topics or not hot_topics.items:
            return f"⚠️ 未找到ID为 {topic_id} 的话题，请检查ID是否正确"

        # 查找指定ID的话题
        topic_item = None
        for item in hot_topics.items:
            if item.id == topic_id:
                topic_item = item
                break

        if not topic_item:
            return f"⚠️ 未找到ID为 {topic_id} 的话题，请检查ID是否正确"

        # 获取话题信息
        title = topic_item.name
        desc = topic_item.desc
        hot_value = topic_item.discuss_num
        tag = topic_item.topic_tag
        category = self._get_category_from_tag(tag)

        # 美化热度值显示
        hot_display = f"{hot_value:,}"
        if hot_value >= 10000:
            hot_display = f"{hot_value / 10000:.1f}万"

        # 获取分类对应的emoji
        category_emoji = ""
        if category:
            category_emoji = self.config.category_emoji.get(category, "")

        # 构建详情消息
        message = f"📋 贴吧话题详情 [ID:{topic_id}]\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        # 添加标题和分类
        message += f"📌 话题：{title}\n"

        # 添加分类和热度
        if category:
            message += f"🏷️ 分类：{category} {category_emoji}\n"
        message += f"🔥 热度：{hot_display} 讨论\n"

        # 添加详细描述
        message += f"\n📝 详情描述：\n{desc}\n"

        # 添加更新时间
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message += f"\n🕒 更新时间：{update_time}\n"

        return message

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        # 检查用户权限
        if not self.is_user_authorized(msg.sender.user_id, msg.group_id):
            return

        content = msg.raw_message.strip()

        # 命令处理逻辑
        if content == "贴吧热榜":
            # 基本热榜查询
            await self.handle_tieba_hot_list(msg)
        elif content.startswith("贴吧热榜 "):
            # 带参数的热榜查询
            param = content.split(" ", 1)[1].strip()
            try:
                count = int(param)
                await self.handle_tieba_hot_list(msg, count=count)
            except ValueError:
                await msg.reply(text="🤔 请输入正确的数字，如「贴吧热榜 15」")
        elif content == "贴吧热榜详情":
            # 详情热榜查询
            await self.handle_tieba_hot_list(msg, show_detail=True)
        elif content.startswith("贴吧热榜ID "):
            # 按ID查询话题详情
            topic_id = content.split(" ", 1)[1].strip()
            await self.handle_topic_detail(msg, topic_id)
        elif content.startswith("贴吧热榜查询 "):
            # 兼容旧命令，按ID查询话题详情
            topic_id = content.split(" ", 1)[1].strip()
            await self.handle_topic_detail(msg, topic_id)

    async def handle_tieba_hot_list(
            self, msg: GroupMessage, count: int = None, show_detail: bool = False
    ):
        """处理贴吧热榜请求"""
        try:
            hot_topics = self.get_latest_hot_topics(count)
            response = self.format_hot_list_message(hot_topics, count, show_detail)
            await msg.reply(text=response)
        except Exception as e:
            logger.error(f"处理贴吧热榜命令出错: {e}")
            await msg.reply(text=f"❌ 处理命令时出现错误: {str(e)}")

    async def handle_topic_detail(self, msg: GroupMessage, topic_id: str):
        """处理话题详情查询请求"""
        try:
            # 获取完整热榜数据
            hot_topics = self.get_latest_hot_topics(None)
            response = self.format_topic_detail(topic_id, hot_topics)
            await msg.reply(text=response)
        except Exception as e:
            logger.error(f"处理话题详情查询出错: {e}")
            await msg.reply(text=f"❌ 处理命令时出现错误: {str(e)}")

    async def on_exit(self) -> None:
        """插件卸载时的清理操作"""
        logger.info("百度贴吧热榜插件正在卸载...")
