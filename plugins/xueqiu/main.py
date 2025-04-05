#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional

from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

# 配置日志
logger = logging.getLogger("xueqiu")

# 兼容装饰器
bot = CompatibleEnrollment


@dataclass
class Config:
    """配置类"""

    white_list: List[int]  # 允许使用的用户ID列表
    group_white_list: List[int]  # 允许使用的群组ID列表
    update_interval: int  # 数据更新间隔（秒）
    hot_count: int  # 热榜数量
    hot_discussion_count: int  # 热门讨论数量
    comment_count: int  # 评论数量
    max_files_per_day: int  # 每天最多保存的文件数
    keep_days: int  # 保留最近几天的数据
    log_level: str  # 日志级别
    templates: Dict[str, str]  # 消息模板

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        whitelist = config_dict.get("whitelist", {})
        data = config_dict.get("data", {})
        storage = config_dict.get("storage", {})
        ui = config_dict.get("ui", {})

        return cls(
            white_list=whitelist.get("user_ids", []),
            group_white_list=whitelist.get("group_ids", []),
            update_interval=data.get("update_interval", 300),
            hot_count=data.get("hot_count", 50),
            hot_discussion_count=data.get("hot_discussion_count", 10),
            comment_count=data.get("comment_count", 10),
            max_files_per_day=storage.get("max_files_per_day", 24),
            keep_days=storage.get("keep_days", 7),
            log_level=storage.get("log_level", "INFO"),
            templates={
                "header": ui.get("header_template", "📊 雪球财经热榜 ({time})\n\n"),
                "item": ui.get(
                    "item_template", "{rank}. {highlight}{title}{hot_tag}\n"
                ),
                "footer": ui.get(
                    "footer_template",
                    "\n💡 提示: 发送「雪球热榜 数字」可指定获取的条数，如「雪球热榜 20」",
                ),
            },
        )


# 替换XueqiuDataCollector类，使用新的XueqiuClient类
class XueqiuDataCollector:
    """雪球数据收集器"""


class XueqiuPlugin(BasePlugin):
    """雪球财经热榜插件 - 获取雪球实时财经热榜数据"""

    name = "XueqiuPlugin"  # 插件名称
    version = "1.0.0"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    config_last_modified = 0
    headers_path = None
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
        log_level = self.config.log_level.upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

    def load_config(self) -> None:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    config_dict = tomllib.load(f)
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

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        # 检查用户权限
        if not self.is_user_authorized(msg.sender.user_id, msg.group_id):
            return

        content = msg.raw_message.strip()

    async def on_exit(self) -> None:
        """插件卸载时的清理操作"""
        logger.info("雪球财经热榜插件正在卸载...")
