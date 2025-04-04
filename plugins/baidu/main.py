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
logger = logging.getLogger("baidu")

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
        baidu_specific = config_dict.get("baidu_specific", {})

        return cls(
            white_list=access.get("white_list", []),
            group_white_list=access.get("group_white_list", []),
            update_interval=basic.get("update_interval", 300),
            max_items=basic.get("max_items", 10),
            max_files_per_day=storage.get("max_files_per_day", 20),
            keep_days=storage.get("keep_days", 7),
            log_level=basic.get("log_level", "INFO"),
            templates={
                "header": ui.get("header_template", "📊 百度热搜榜 ({time})\n\n"),
                "item": ui.get(
                    "item_template", "{rank}. {highlight}{title}{hot_tag}\n"
                ),
                "footer": ui.get(
                    "footer_template",
                    "\n💡 提示: 发送「百度热搜 数字」可指定获取的条数，如「百度热搜 20」",
                ),
            },
            category_emoji=baidu_specific.get(
                "category_emoji",
                {
                    "热": "🔥",
                    "新": "✨",
                    "爆": "💥",
                    "沸": "♨️",
                    "商": "🛒",
                    "娱": "🎬",
                    "体": "⚽",
                    "情": "💖",
                },
            ),
        )


class BaiduDataCollector:
    """百度热搜数据收集器"""

    def __init__(self, data_dir: Path):
        """初始化数据收集器

        Args:
            data_dir: 数据保存目录
        """
        self.data_dir = data_dir

    def get_baidu_hot(self) -> Dict[str, Any]:
        """获取百度热搜数据"""
        try:
            # 使用rebang模块获取数据
            data = get_tab_data("baidu")
            if not data or not data.get("hot_items"):
                logger.error("获取百度热搜数据失败：数据为空")
                return {}

            # 添加时间戳
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return data
        except Exception as e:
            logger.error(f"获取百度热搜数据失败: {e}")
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
        """收集百度热搜数据并整合"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        hot_data = self.get_baidu_hot()
        if not hot_data:
            return {}

        # 保持原有数据结构，添加统一的时间戳
        hot_data["timestamp"] = timestamp
        hot_data["metadata"] = {
            "source": "baidu",
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
        filename = f"baidu_hot_{timestamp}.json"
        filepath = date_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)


class BaiduPlugin(BasePlugin):
    """百度热搜插件 - 获取百度实时热搜榜数据"""

    name = "BaiduPlugin"  # 插件名称
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
        scheduler.add_random_minute_task(self.fetch_baidu_hot, 0, 5)

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

    async def fetch_baidu_hot(self) -> None:
        """获取并保存百度热搜数据"""
        try:
            collector = BaiduDataCollector(data_dir=self.data_dir)
            data = collector.collect_data()
            if data:
                data_file = collector.save_data(data)
                if data_file:
                    self.latest_data_file = data_file
                    logger.info(f"成功获取并保存百度热搜数据: {data_file}")

                    # 清理旧文件
                    await self.clean_old_files()
        except Exception as e:
            logger.error(f"获取百度热搜数据失败: {e}")

    def get_latest_hot_list(self, count: int = None) -> Dict[str, Any]:
        """获取最新的热榜数据

        Args:
            count: 获取的热榜数量，如果为None则使用配置中的max_items
        """
        # 检查是否有最新数据文件
        if not self.latest_data_file:
            return {}

        try:
            with open(self.latest_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if count is None or count <= 0:
                # 使用默认显示数量
                count = self.config.max_items
            # 确保不超出最大数量限制
            elif count > 50:
                count = 50

            # 限制返回的热榜数量
            result = data.copy()
            if "hot_items" in result and len(result["hot_items"]) > count:
                result["hot_items"] = result["hot_items"][:count]

            return result
        except Exception as e:
            logger.error(f"读取热榜数据失败: {e}")
            return {}

    async def clean_old_files(self) -> None:
        """清理旧的数据文件，按配置保留文件"""
        try:
            # 清理过期数据：保留最近N天的数据
            all_date_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
            all_date_dirs.sort(reverse=True)  # 按日期倒序排列

            # 保留最近N天的数据目录
            if len(all_date_dirs) > self.config.keep_days:
                for old_dir in all_date_dirs[self.config.keep_days:]:
                    # 删除旧目录及其内容
                    for file in old_dir.iterdir():
                        file.unlink()
                    old_dir.rmdir()
                    logger.debug(f"已删除旧数据目录: {old_dir}")

            # 清理每个日期目录中的多余文件
            for date_dir in all_date_dirs[: self.config.keep_days]:
                files = list(date_dir.glob("baidu_hot_*.json"))
                if len(files) > self.config.max_files_per_day:
                    # 按修改时间排序
                    files.sort(key=lambda x: os.path.getmtime(x))
                    # 删除旧文件
                    for file in files[: -self.config.max_files_per_day]:
                        file.unlink()
                        logger.debug(f"已删除旧文件: {file}")
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")

    def format_hot_list_message(
            self, hot_data: Dict[str, Any], count: int = None, show_detail: bool = False
    ) -> str:
        """格式化热榜消息

        Args:
            hot_data: 热榜数据
            count: 显示的热榜数量
            show_detail: 是否显示详情
        """
        if not hot_data or "hot_items" not in hot_data:
            return "⚠️ 百度热搜数据获取失败，请稍后再试"

        hot_items = hot_data.get("hot_items", [])
        if not hot_items:
            return "⚠️ 未获取到百度热搜数据"

        if count is None or count <= 0:
            count = self.config.max_items  # 默认显示量

        # 限制条数
        hot_items = hot_items[:count]

        # 构建消息
        update_time = hot_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        # 添加头部信息
        msg = f"📱 {self.config.templates['header'].format(time=update_time)}"

        # 添加数据统计
        total_items = len(hot_data.get("hot_items", []))
        highlighted_count = sum(
            1
            for item in hot_data.get("hot_items", [])
            if item.get("is_highlighted", False)
        )
        msg += f"共{total_items}条热搜，{highlighted_count}条热点话题\n"
        msg += "━━━━━━━━━━━━━━━━━━\n\n"

        # 热度趋势符号映射
        trend_symbols = {"up": "📈", "down": "📉", "hot": "🔥", "new": "🆕"}

        for idx, item in enumerate(hot_items, 1):
            title = item.get("title", "无标题")
            hot_value = item.get("hot_value", "")
            category = item.get("category", "")
            description = item.get("description", "")
            trend = item.get("trend", "")

            # 构建排名前缀（前三名使用特殊emoji）
            if idx == 1:
                rank_prefix = "🥇 "
            elif idx == 2:
                rank_prefix = "🥈 "
            elif idx == 3:
                rank_prefix = "🥉 "
            else:
                rank_prefix = f"{idx}. "

            # 构建热度标签
            hot_tag = ""
            if hot_value:
                # 格式化热度值，大于10000显示为"万"
                formatted_hot = hot_value
                try:
                    hot_num = float(hot_value)
                    if hot_num >= 10000:
                        formatted_hot = f"{hot_num / 10000:.1f}万"
                except:
                    pass
                hot_tag = f" 🔥{formatted_hot}"

            # 添加热度趋势
            if trend:
                hot_tag += f" {trend_symbols.get(trend.lower(), '')}"

            # 添加分类标签
            category_tag = ""
            if category:
                emoji = self.config.category_emoji.get(category, "")
                if emoji:
                    # 根据分类添加不同颜色
                    if category == "热":
                        category_tag = f" [{emoji}热门]"
                    elif category == "新":
                        category_tag = f" [{emoji}新增]"
                    elif category == "爆":
                        category_tag = f" [{emoji}爆点]"
                    elif category in ["沸", "热"]:
                        category_tag = f" [{emoji}沸腾]"
                    elif category == "商":
                        category_tag = f" [{emoji}商业]"
                    elif category == "娱":
                        category_tag = f" [{emoji}娱乐]"
                    elif category == "体":
                        category_tag = f" [{emoji}体育]"
                    elif category == "情":
                        category_tag = f" [{emoji}情感]"
                    else:
                        category_tag = f" [{emoji}{category}]"

            # 标记热门内容
            highlight = "🔴 " if item.get("is_highlighted", False) else ""

            # 添加基本格式（标题和热度信息）
            msg += f"{rank_prefix}{highlight}{title}{category_tag}{hot_tag}\n"

            # 如果有描述信息且显示详情，添加描述
            if description and show_detail:
                msg += f"   {description}\n"

            # 如果需要显示详情，添加链接
            if show_detail and item.get("link"):
                msg += f"   🔗 {item.get('link')}\n"

            # 添加分隔符，每三个条目添加一次
            if idx % 3 == 0 and idx < len(hot_items):
                msg += "┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n"

        # 添加底部统计和提示
        msg += "\n━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 热搜更新时间: {update_time}\n"
        msg += self.config.templates["footer"]

        return msg

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        # 检查白名单权限
        if not self.is_user_authorized(msg.sender.user_id, msg.group_id):
            return

        content = msg.raw_message.strip()

        # 解析命令
        if content == "百度热搜":
            # 获取默认数量的热榜
            hot_data = self.get_latest_hot_list(self.config.max_items)
            response = self.format_hot_list_message(hot_data, self.config.max_items)
            await msg.reply(text=response)
        elif content.startswith("百度热搜 "):
            # 解析参数
            args = content.split(" ")[1:]
            limit = self.config.max_items
            show_detail = False

            # 处理参数
            for arg in args:
                if arg.isdigit():
                    # 如果是数字，作为条数限制
                    try:
                        limit = int(arg)
                        # 限制最大条数，避免消息过长
                        limit = min(limit, 50)
                    except ValueError:
                        pass
                elif arg.lower() in ["-d", "--detail", "详情"]:
                    # 显示详情模式
                    show_detail = True

            # 获取热榜数据
            hot_data = self.get_latest_hot_list(limit)
            response = self.format_hot_list_message(hot_data, limit, show_detail)
            await msg.reply(text=response)

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        # 检查白名单权限
        if not self.is_user_authorized(msg.sender.user_id):
            return

        content = msg.raw_message.strip()

        # 解析命令
        if content == "百度热搜":
            # 获取默认数量的热榜
            hot_data = self.get_latest_hot_list(self.config.max_items)
            response = self.format_hot_list_message(hot_data, self.config.max_items)
            await msg.reply(text=response)
        elif content.startswith("百度热搜 "):
            # 解析参数
            args = content.split(" ")[1:]
            limit = self.config.max_items
            show_detail = False

            # 处理参数
            for arg in args:
                if arg.isdigit():
                    # 如果是数字，作为条数限制
                    try:
                        limit = int(arg)
                        # 限制最大条数，避免消息过长
                        limit = min(limit, 50)
                    except ValueError:
                        pass
                elif arg.lower() in ["-d", "--detail", "详情"]:
                    # 显示详情模式
                    show_detail = True

            # 获取热榜数据
            hot_data = self.get_latest_hot_list(limit)
            response = self.format_hot_list_message(hot_data, limit, show_detail)
            await msg.reply(text=response)

    async def on_exit(self) -> None:
        """插件退出时执行的操作"""
        logger.info("百度热搜插件正在退出...")
