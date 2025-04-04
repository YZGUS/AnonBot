#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import tomli
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from rebang.scraper import get_tab_data
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

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        basic = config_dict.get("basic", {})
        access = config_dict.get("access", {})
        storage = config_dict.get("storage", {})
        ui = config_dict.get("ui", {})
        tieba_specific = config_dict.get("tieba_specific", {})

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
        )


class TiebaDataCollector:
    """百度贴吧数据收集器"""

    def __init__(self, data_dir: Path):
        """初始化数据收集器

        Args:
            data_dir: 数据保存目录
        """
        self.data_dir = data_dir

    def get_tieba_hot(self) -> Dict[str, Any]:
        """获取百度贴吧热榜数据"""
        try:
            # 使用rebang模块获取数据
            data = get_tab_data("baidu-tieba")
            if not data or not data.get("hot_items"):
                logger.error("获取百度贴吧热榜数据失败：数据为空")
                return {}

            # 添加时间戳
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return data
        except Exception as e:
            logger.error(f"获取百度贴吧热榜数据失败: {e}")
            return {}

    def parse_hot_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析热榜数据

        Args:
            data: 原始数据
        """
        if not data or "hot_items" not in data:
            return []

        hot_items = data.get("hot_items", [])
        return hot_items

    def collect_data(self) -> Dict[str, Any]:
        """收集百度贴吧热榜数据并整合"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        hot_data = self.get_tieba_hot()
        if not hot_data:
            return {}

        # 保持原有数据结构，添加统一的时间戳
        hot_data["timestamp"] = timestamp
        hot_data["metadata"] = {
            "source": "baidu-tieba",
            "hot_count": len(hot_data.get("hot_items", [])),
            "update_time": timestamp,
        }

        return hot_data

    def save_data(self, data: Dict[str, Any]) -> str:
        """保存数据到JSON文件，使用年月日-小时的文件夹格式

        Args:
            data: 热榜数据
        """
        if not data:
            return ""

        now = datetime.now()
        folder_name = now.strftime("%Y%m%d-%H")
        folder_path = self.data_dir / folder_name
        folder_path.mkdir(exist_ok=True, parents=True)

        timestamp = now.strftime("%Y%m%d%H%M%S")
        filename = f"tieba_hot_{timestamp}.json"
        filepath = folder_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
            collector = TiebaDataCollector(data_dir=self.data_dir)
            data = collector.collect_data()

            if data and data.get("hot_items"):
                # 保存数据到文件
                data_file = collector.save_data(data)
                if data_file:
                    self.latest_data_file = data_file
                    logger.info(f"成功获取并保存百度贴吧热榜数据: {data_file}")

                # 清理旧文件
                await self.clean_old_files()
            else:
                logger.warning("获取百度贴吧热榜数据失败或数据为空")
        except Exception as e:
            logger.error(f"获取百度贴吧热榜数据出错: {e}")

    def get_latest_hot_list(self, count: int = None) -> Dict[str, Any]:
        """获取最新的热榜数据

        Args:
            count: 获取的条目数量

        Returns:
            热榜数据
        """
        if not self.latest_data_file or not os.path.exists(self.latest_data_file):
            logger.warning("最新数据文件不存在")
            return {}

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 限制数量
            if count is not None and count > 0:
                data["hot_items"] = data.get("hot_items", [])[:count]

            return data
        except Exception as e:
            logger.error(f"读取最新热榜数据出错: {e}")
            return {}

    async def clean_old_files(self) -> None:
        """清理旧数据文件"""
        try:
            # 按日期-小时目录清理
            all_folders = sorted(
                [d for d in self.data_dir.iterdir() if d.is_dir() and "-" in d.name],
                key=lambda x: x.name,
                reverse=True,
            )

            # 为保持日期级别的清理逻辑，提取日期前缀（YYYYMMDD）
            date_prefixes = {}
            for folder in all_folders:
                date_prefix = folder.name.split("-")[0]
                if date_prefix not in date_prefixes:
                    date_prefixes[date_prefix] = []
                date_prefixes[date_prefix].append(folder)

            # 保留最近几天的数据
            keep_days = self.config.keep_days
            date_keys = sorted(date_prefixes.keys(), reverse=True)

            if len(date_keys) > keep_days:
                # 清理旧日期的所有数据
                for old_date in date_keys[keep_days:]:
                    for old_dir in date_prefixes[old_date]:
                        logger.debug(f"清理旧数据目录: {old_dir}")
                        for file in old_dir.iterdir():
                            if file.is_file():
                                file.unlink()
                        old_dir.rmdir()

            # 对保留的日期，控制每小时文件夹内的文件数量
            for date in date_keys[:keep_days]:
                for hour_dir in date_prefixes[date]:
                    files = sorted(
                        [f for f in hour_dir.iterdir() if f.is_file()],
                        key=lambda x: x.stat().st_mtime,
                        reverse=True,
                    )

                    max_files = (
                        self.config.max_files_per_day // 24 or 1
                    )  # 平均分配每小时的最大文件数
                    if len(files) > max_files:
                        for old_file in files[max_files:]:
                            logger.debug(f"清理过多的数据文件: {old_file}")
                            old_file.unlink()
        except Exception as e:
            logger.error(f"清理旧文件出错: {e}")

    def format_hot_list_message(
        self, hot_data: Dict[str, Any], count: int = None, show_detail: bool = False
    ) -> str:
        """格式化热榜消息

        Args:
            hot_data: 热榜数据
            count: 显示条目数量
            show_detail: 是否显示详情

        Returns:
            格式化后的消息
        """
        if not hot_data or not hot_data.get("hot_items"):
            return "⚠️ 暂无百度贴吧热榜数据，请稍后再试"

        # 获取时间和热榜条目
        update_time = hot_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        hot_items = hot_data.get("hot_items", [])

        # 限制条目数量
        if count is None:
            count = self.config.max_items
        hot_items = hot_items[:count]

        # 构建消息
        message = f"📱 {self.config.templates['header'].format(time=update_time)}"

        # 添加数据统计
        total_items = len(hot_data.get("hot_items", []))
        highlighted_count = sum(
            1
            for item in hot_data.get("hot_items", [])
            if item.get("is_highlighted", False)
        )
        message += f"共{total_items}条热门帖子，{highlighted_count}条精华内容\n"
        message += "━━━━━━━━━━━━━━━━━━\n\n"

        # 添加热榜条目
        for idx, item in enumerate(hot_items, start=1):
            title = item.get("title", "无标题")

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
            highlight = "💎 " if item.get("is_highlighted", False) else ""

            # 设置热度标签
            hot_tag = ""
            category = item.get("category", "")
            if category:
                emoji = self.config.category_emoji.get(category, "")
                if emoji:
                    hot_tag = f" {emoji}"

            # 获取热度值
            hot_value = item.get("hot_value", "")
            if hot_value:
                try:
                    hot_num = float(hot_value)
                    if hot_num >= 10000:
                        hot_value = f"{hot_num / 10000:.1f}万"
                except:
                    pass
                hot_tag += f" 🔥{hot_value}"

            # 格式化单个条目
            message += f"{rank_prefix}{highlight}{title}{hot_tag}\n"

            # 添加详情
            if show_detail and item.get("description"):
                description = item.get("description", "")
                message += f"   {description}\n"

            # 添加链接
            if show_detail and item.get("link"):
                link = item.get("link", "")
                message += f"   🔗 {link}\n"

            # 添加分隔符，每三个条目添加一次
            if idx % 3 == 0 and idx < len(hot_items):
                message += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"

        # 添加页脚
        message += "\n━━━━━━━━━━━━━━━━━━\n"
        message += f"📊 更新时间: {update_time}\n"
        message += self.config.templates["footer"]

        return message

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        # 检查用户权限
        if not self.is_user_authorized(msg.sender.user_id, msg.group_id):
            return

        content = msg.raw_message.strip()

        # 基本命令: 贴吧热榜
        if content == "贴吧热榜":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'贴吧热榜'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 带数字参数命令: 贴吧热榜 15
        elif content.startswith("贴吧热榜 ") and content[5:].strip().isdigit():
            try:
                count = int(content[5:].strip())
                hot_data = self.get_latest_hot_list(count)
                response = self.format_hot_list_message(hot_data, count)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'贴吧热榜 数字'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 详情命令: 贴吧热榜 详情
        elif content == "贴吧热榜 详情":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data, show_detail=True)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'贴吧热榜 详情'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        # 检查用户权限
        if not self.is_user_authorized(msg.sender.user_id):
            return

        content = msg.raw_message.strip()

        # 基本命令: 贴吧热榜
        if content == "贴吧热榜":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'贴吧热榜'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 带数字参数命令: 贴吧热榜 15
        elif content.startswith("贴吧热榜 ") and content[5:].strip().isdigit():
            try:
                count = int(content[5:].strip())
                hot_data = self.get_latest_hot_list(count)
                response = self.format_hot_list_message(hot_data, count)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'贴吧热榜 数字'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 详情命令: 贴吧热榜 详情
        elif content == "贴吧热榜 详情":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data, show_detail=True)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'贴吧热榜 详情'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

    async def on_exit(self) -> None:
        """插件卸载时的清理操作"""
        logger.info("百度贴吧热榜插件正在卸载...")
