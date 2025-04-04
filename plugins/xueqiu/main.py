#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import tomllib
import requests
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from rebang.scraper import get_tab_data
from scheduler import scheduler

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


class XueqiuDataCollector:
    """雪球数据收集器"""

    def __init__(
        self,
        headers_path: Path,
        data_dir: Path,
        hot_count: int = 50,
        hot_discussion_count: int = 10,
        comment_count: int = 10,
    ):
        """初始化数据收集器

        Args:
            headers_path: 请求头配置文件路径
            data_dir: 数据存储目录
            hot_count: 热榜数量
            hot_discussion_count: 热门讨论数量
            comment_count: 评论数量
        """
        self.headers = self._load_headers(headers_path)
        self.data_dir = data_dir
        self.hot_count = hot_count
        self.hot_discussion_count = hot_discussion_count
        self.comment_count = comment_count

    def _load_headers(self, headers_path: Path) -> Dict[str, str]:
        """加载请求头配置"""
        if headers_path.exists():
            with open(headers_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": "https://xueqiu.com/",
        }

    def get_xueqiu_hot(self) -> Dict[str, Any]:
        """获取雪球热榜数据"""
        try:
            # 使用rebang模块获取数据
            data = get_tab_data("xueqiu")
            if not data or not data.get("hot_items"):
                logger.error("获取雪球热榜数据失败：数据为空")
                return {}

            # 添加时间戳
            data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return data
        except Exception as e:
            logger.error(f"获取雪球热榜数据失败: {e}")
            return {}

    def get_stock_detail(self, stock_code: str) -> Dict[str, Any]:
        """获取股票详情

        Args:
            stock_code: 股票代码
        """
        if not stock_code:
            return {}

        try:
            # 构建API URL，根据实际情况可能需要调整
            url = f"https://xueqiu.com/S/{stock_code}"

            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return {
                    "code": stock_code,
                    "name": "未知",
                    "price": 0,
                    "percent": "0%",
                    "description": "获取数据失败",
                    "url": url,
                }

            # 这里只是模拟数据，实际项目中应该解析HTML或调用API
            return {
                "code": stock_code,
                "name": f"模拟股票{stock_code}",
                "price": 100.0,
                "percent": "+2.5%",
                "description": "这是一个模拟的股票详情",
                "url": url,
            }
        except Exception as e:
            logger.error(f"获取股票详情失败: {e}")
            return {
                "code": stock_code,
                "name": "未知",
                "price": 0,
                "percent": "0%",
                "description": f"获取数据出错: {str(e)}",
                "url": f"https://xueqiu.com/S/{stock_code}",
            }

    def get_topic_detail(self, topic_word: str) -> Dict[str, Any]:
        """获取话题详情

        Args:
            topic_word: 话题关键词
        """
        if not topic_word:
            return {}

        try:
            # 构建搜索URL
            search_word = topic_word.replace("#", "").replace(" ", "%20")
            detail_url = f"https://xueqiu.com/k?q={search_word}"

            # 这里只是模拟数据，实际项目中应该解析HTML或调用API
            return {
                "topic_id": f"xueqiu_topic_{hash(topic_word) % 10000000}",
                "title": topic_word,
                "view_count": 5000,
                "discussion_count": 120,
                "url": detail_url,
            }
        except Exception as e:
            logger.error(f"获取话题详情失败: {e}")
            return {}

    def get_topic_comments(self, topic_word: str) -> List[Dict[str, Any]]:
        """获取话题评论

        Args:
            topic_word: 话题关键词
        """
        if not topic_word:
            return []

        comments = []
        # 生成模拟评论数据
        for i in range(self.comment_count):
            comments.append(
                {
                    "comment_id": f"comment_{hash(topic_word) % 10000000}_{i}",
                    "content": f"这是关于{topic_word}的模拟评论 {i + 1}",
                    "like_count": (10 - i) * 10,
                    "user": f"用户_{i + 1}",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        return comments

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
        """收集雪球数据并整合"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        hot_data = self.get_xueqiu_hot()
        if not hot_data:
            return {}

        # 保持原有数据结构，添加统一的时间戳
        hot_data["timestamp"] = timestamp
        hot_data["metadata"] = {
            "source": "xueqiu",
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
        filename = f"xueqiu_hot_{timestamp}.json"
        filepath = folder_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)


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

        # 设置定时任务，定期获取热榜数据
        scheduler.add_random_minute_task(self.fetch_xueqiu_hot, 0, 5)

        # 立即执行一次，获取初始数据
        await self.fetch_xueqiu_hot()

        logger.info(f"雪球财经热榜插件初始化完成，版本：{self.version}")

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

    async def fetch_xueqiu_hot(self) -> None:
        """获取并保存雪球热榜数据"""
        try:
            collector = XueqiuDataCollector(
                headers_path=self.headers_path,
                data_dir=self.data_dir,
                hot_count=self.config.hot_count,
                hot_discussion_count=self.config.hot_discussion_count,
                comment_count=self.config.comment_count,
            )
            data = collector.collect_data()

            if data and data.get("hot_items"):
                # 保存数据到文件
                data_file = collector.save_data(data)
                if data_file:
                    self.latest_data_file = data_file
                    logger.info(f"成功获取并保存雪球热榜数据: {data_file}")

                # 清理旧文件
                await self.clean_old_files()
            else:
                logger.warning("获取雪球热榜数据失败或数据为空")
        except Exception as e:
            logger.error(f"获取雪球热榜数据出错: {e}")

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

            if count is None or count <= 0:
                # 使用默认显示数量，一般为10条
                count = 10
            elif count > self.config.hot_count:
                count = self.config.hot_count

            # 限制返回的热榜数量
            result = data.copy()
            if "hot_items" in result and len(result["hot_items"]) > count:
                result["hot_items"] = result["hot_items"][:count]

            return result
        except Exception as e:
            logger.error(f"读取最新热榜数据出错: {e}")
            return {}

    def get_stock_details(self, stock_code: str) -> Dict[str, Any]:
        """获取股票详情

        Args:
            stock_code: 股票代码
        """
        collector = XueqiuDataCollector(
            headers_path=self.headers_path,
            data_dir=self.data_dir,
            hot_count=self.config.hot_count,
            hot_discussion_count=self.config.hot_discussion_count,
            comment_count=self.config.comment_count,
        )

        # 获取股票详情
        stock_detail = collector.get_stock_detail(stock_code)
        if not stock_detail:
            return {}

        return stock_detail

    def get_topic_details(self, keyword: str) -> Dict[str, Any]:
        """获取话题详情

        Args:
            keyword: 话题关键词
        """
        collector = XueqiuDataCollector(
            headers_path=self.headers_path,
            data_dir=self.data_dir,
            hot_count=self.config.hot_count,
            hot_discussion_count=self.config.hot_discussion_count,
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
            return "⚠️ 暂无雪球财经热榜数据，请稍后再试"

        # 获取时间和热榜条目
        update_time = hot_data.get(
            "timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        hot_items = hot_data.get("hot_items", [])

        # 限制条目数量
        if count is None:
            count = 10  # 默认显示10条
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
        message += f"共{total_items}条热门内容，{highlighted_count}条特别关注\n"
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
            highlight = "💲 " if item.get("is_highlighted", False) else ""

            # 获取热度值或股票信息
            hot_tag = ""
            hot_value = item.get("hot_value", "")
            stock_code = item.get("stock_code", "")

            if hot_value:
                try:
                    hot_num = float(hot_value)
                    if hot_num >= 10000:
                        hot_value = f"{hot_num / 10000:.1f}万"
                except:
                    pass
                hot_tag += f" 🔥{hot_value}"

            if stock_code:
                hot_tag += f" 📈{stock_code}"

            # 格式化单个条目
            message += f"{rank_prefix}{highlight}{title}{hot_tag}\n"

            # 添加详情
            description = item.get("description", "")
            if show_detail and description:
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

    def format_stock_detail_message(self, stock_data: Dict[str, Any]) -> str:
        """格式化股票详情消息

        Args:
            stock_data: 股票详情数据
        """
        if not stock_data:
            return "未找到相关股票详情，请确认股票代码是否正确"

        code = stock_data.get("code", "未知")
        name = stock_data.get("name", "未知")
        price = stock_data.get("price", 0)
        percent = stock_data.get("percent", "0%")
        description = stock_data.get("description", "")
        url = stock_data.get("url", "")

        message = f"【股票详情】 {name}({code})\n\n"

        if price:
            message += f"当前价: {price}\n"
        if percent:
            # 根据涨跌添加不同颜色的emoji
            if percent.startswith("+"):
                message += f"涨跌幅: {percent} 📈\n"
            elif percent.startswith("-"):
                message += f"涨跌幅: {percent} 📉\n"
            else:
                message += f"涨跌幅: {percent}\n"
        if description:
            message += f"\n{description}\n"
        if url:
            message += f"\n🔗 详情链接: {url}\n"

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
        discussion_count = topic_data.get("discussion_count", 0)
        url = topic_data.get("url", "")

        message = f"【话题详情】 {title}\n\n"

        if view_count:
            message += f"浏览量: {view_count}\n"
        if discussion_count:
            message += f"讨论数: {discussion_count}\n"
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
        # 检查用户权限
        if not self.is_user_authorized(msg.sender.user_id, msg.group_id):
            return

        content = msg.raw_message.strip()

        # 基本命令: 雪球热榜
        if content == "雪球热榜":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热榜'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 带数字参数命令: 雪球热榜 15
        elif content.startswith("雪球热榜 ") and content[5:].strip().isdigit():
            try:
                count = int(content[5:].strip())
                hot_data = self.get_latest_hot_list(count)
                response = self.format_hot_list_message(hot_data, count)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热榜 数字'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 详情命令: 雪球热榜 详情
        elif content == "雪球热榜 详情":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data, show_detail=True)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热榜 详情'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 热议命令: 雪球热议
        elif content == "雪球热议":
            try:
                hot_data = self.get_latest_hot_list(self.config.hot_discussion_count)
                response = self.format_hot_list_message(
                    hot_data, self.config.hot_discussion_count
                )
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热议'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 股票详情命令: 雪球股票 SH600000
        elif content.startswith("雪球股票 "):
            try:
                stock_code = content.replace("雪球股票 ", "").strip()
                if stock_code:
                    stock_data = self.get_stock_details(stock_code)
                    response = self.format_stock_detail_message(stock_data)
                    await msg.reply(text=response)
                else:
                    await msg.reply(text="请提供股票代码，格式：雪球股票 SH600000")
            except Exception as e:
                logger.error(f"处理'雪球股票'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 话题详情命令: 雪球话题 关键词
        elif content.startswith("雪球话题 "):
            try:
                keyword = content.replace("雪球话题 ", "").strip()
                if keyword:
                    topic_data = self.get_topic_details(keyword)
                    response = self.format_topic_detail_message(topic_data)
                    await msg.reply(text=response)
                else:
                    await msg.reply(text="请提供话题关键词，格式：雪球话题 [关键词]")
            except Exception as e:
                logger.error(f"处理'雪球话题'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        # 检查用户权限
        if not self.is_user_authorized(msg.sender.user_id):
            return

        content = msg.raw_message.strip()

        # 基本命令: 雪球热榜
        if content == "雪球热榜":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热榜'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 带数字参数命令: 雪球热榜 15
        elif content.startswith("雪球热榜 ") and content[5:].strip().isdigit():
            try:
                count = int(content[5:].strip())
                hot_data = self.get_latest_hot_list(count)
                response = self.format_hot_list_message(hot_data, count)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热榜 数字'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 详情命令: 雪球热榜 详情
        elif content == "雪球热榜 详情":
            try:
                hot_data = self.get_latest_hot_list()
                response = self.format_hot_list_message(hot_data, show_detail=True)
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热榜 详情'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 热议命令: 雪球热议
        elif content == "雪球热议":
            try:
                hot_data = self.get_latest_hot_list(self.config.hot_discussion_count)
                response = self.format_hot_list_message(
                    hot_data, self.config.hot_discussion_count
                )
                await msg.reply(text=response)
            except Exception as e:
                logger.error(f"处理'雪球热议'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 股票详情命令: 雪球股票 SH600000
        elif content.startswith("雪球股票 "):
            try:
                stock_code = content.replace("雪球股票 ", "").strip()
                if stock_code:
                    stock_data = self.get_stock_details(stock_code)
                    response = self.format_stock_detail_message(stock_data)
                    await msg.reply(text=response)
                else:
                    await msg.reply(text="请提供股票代码，格式：雪球股票 SH600000")
            except Exception as e:
                logger.error(f"处理'雪球股票'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

        # 话题详情命令: 雪球话题 关键词
        elif content.startswith("雪球话题 "):
            try:
                keyword = content.replace("雪球话题 ", "").strip()
                if keyword:
                    topic_data = self.get_topic_details(keyword)
                    response = self.format_topic_detail_message(topic_data)
                    await msg.reply(text=response)
                else:
                    await msg.reply(text="请提供话题关键词，格式：雪球话题 [关键词]")
            except Exception as e:
                logger.error(f"处理'雪球话题'命令出错: {e}")
                await msg.reply(text=f"处理命令时出现错误: {str(e)}")

    async def on_exit(self) -> None:
        """插件卸载时的清理操作"""
        logger.info("雪球财经热榜插件正在卸载...")
