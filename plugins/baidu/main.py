#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import tomli
from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from hotsearch.api import BaiduClient
from hotsearch.api.models.baidu import BaiduHotSearchResponse
from utils import scheduler

logger = logging.getLogger("baidu")
bot = CompatibleEnrollment


@dataclass
class Config:
    white_list: List[int]
    group_white_list: List[int]
    update_interval: int
    max_items: int
    max_files_per_day: int
    keep_days: int
    log_level: str
    templates: Dict[str, str]
    category_emoji: Dict[str, str]
    api_token: str

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        basic = config_dict.get("basic", {})
        access = config_dict.get("access", {})
        storage = config_dict.get("storage", {})
        ui = config_dict.get("ui", {})
        baidu_specific = config_dict.get("baidu_specific", {})
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
            api_token=api.get("token"),
        )


class BaiduDataCollector:
    def __init__(self, data_dir: Path, api_token: str = None):
        self.data_dir = data_dir
        self.api_token = api_token
        self.client = BaiduClient(
            auth_token=api_token, save_data=True, data_dir=str(data_dir)
        )

    def get_baidu_hot(
            self, sub_tab: str = "realtime"
    ) -> Optional[BaiduHotSearchResponse]:
        try:
            if sub_tab == "realtime":
                return self.client.get_realtime(as_model=True)
            elif sub_tab == "phrase":
                return self.client.get_phrase(as_model=True)
            elif sub_tab == "novel":
                return self.client.get_novel(as_model=True)
            elif sub_tab == "game":
                return self.client.get_game(as_model=True)
            elif sub_tab == "car":
                return self.client.get_car(as_model=True)
            elif sub_tab == "teleplay":
                return self.client.get_teleplay(as_model=True)
            return None
        except Exception as e:
            logger.error(f"获取百度热搜数据失败: {e}, 子分类：{sub_tab}")
            return None

    def collect_data(self, sub_tab: str = "realtime") -> Optional[Dict[str, Any]]:
        data = self.get_baidu_hot(sub_tab)
        if not data:
            return None

        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        result = {
            "timestamp": timestamp,
            "sub_tab": sub_tab,
            "last_list_time": data.last_list_time,
            "next_refresh_time": data.next_refresh_time,
            "version": data.version,
            "hot_items": [],
        }

        for item in data.items:
            hot_item = {
                "title": item.word,
                "desc": item.desc,
                "heat_num": item.hot_score,
                "hot_tag": item.hot_tag,
                "url": f"https://www.baidu.com/s?wd={item.query}",
                "highlight": item.hot_tag in ["沸", "热", "爆"],
            }
            result["hot_items"].append(hot_item)

        return result

    def save_data(self, data: Dict[str, Any], sub_tab: str = "realtime") -> str:
        if not data:
            return ""

        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        date_dir = self.data_dir / date_str
        date_dir.mkdir(exist_ok=True, parents=True)

        timestamp = now.strftime("%Y%m%d%H%M%S")
        filename = f"baidu_{sub_tab}_{timestamp}.json"
        filepath = date_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(filepath)


class BaiduPlugin(BasePlugin):
    name = "BaiduPlugin"
    version = "1.0.0"

    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    latest_data_file = None
    data_collector = None

    async def on_load(self):
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)

        self.load_config()
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))
        self.data_collector = BaiduDataCollector(self.data_dir, self.config.api_token)
        scheduler.add_random_minute_task(self.fetch_baidu_hot, 0, 5)

    def load_config(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    config_dict = tomli.load(f)
                self.config = Config.from_dict(config_dict)
                self.config_last_modified = os.path.getmtime(self.config_path)
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                self.config = Config.from_dict({})
        else:
            self.config = Config.from_dict({})

    def check_config_update(self) -> bool:
        if not self.config_path.exists():
            return False

        last_modified = os.path.getmtime(self.config_path)
        if last_modified > self.config_last_modified:
            self.load_config()
            return True
        return False

    def is_user_authorized(self, user_id: int, group_id: Optional[int] = None) -> bool:
        if self.config.white_list and user_id not in self.config.white_list:
            return False
        if (
                group_id is not None
                and self.config.group_white_list
                and group_id not in self.config.group_white_list
        ):
            return False
        return True

    async def fetch_baidu_hot(self) -> None:
        try:
            self.check_config_update()
            sub_tabs = ["realtime", "phrase", "novel", "game", "car", "teleplay"]
            for sub_tab in sub_tabs:
                hot_data = self.data_collector.collect_data(sub_tab)
                if hot_data:
                    filepath = self.data_collector.save_data(hot_data, sub_tab)
                    if filepath and sub_tab == "realtime":
                        self.latest_data_file = filepath
            await self.clean_old_files()
        except Exception as e:
            logger.error(f"抓取百度热搜失败: {e}")

    def get_latest_hot_list(
            self, count: int = None, sub_tab: str = "realtime"
    ) -> Dict[str, Any]:
        if count is None:
            count = self.config.max_items

        latest_file = None
        if sub_tab != "realtime" or not self.latest_data_file:
            try:
                for date_dir in sorted(self.data_dir.glob("20*"), reverse=True):
                    if date_dir.is_dir():
                        files = list(date_dir.glob(f"baidu_{sub_tab}_*.json"))
                        if files:
                            files.sort(key=lambda x: x.name, reverse=True)
                            latest_file = str(files[0])
                            break
            except Exception:
                pass
        else:
            latest_file = self.latest_data_file

        if not latest_file:
            hot_data = self.data_collector.collect_data(sub_tab)
            if hot_data:
                filepath = self.data_collector.save_data(hot_data, sub_tab)
                if filepath:
                    latest_file = filepath
            return hot_data or {}

        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                hot_data = json.load(f)

            if hot_data and "hot_items" in hot_data:
                timestamp = hot_data.get("timestamp", "")
                if timestamp:
                    data_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    if (now - data_time).total_seconds() > 1800:
                        fresh_data = self.data_collector.collect_data(sub_tab)
                        if fresh_data:
                            hot_data = fresh_data
                            filepath = self.data_collector.save_data(hot_data, sub_tab)
                            if filepath and sub_tab == "realtime":
                                self.latest_data_file = filepath
                return hot_data
            else:
                return self.data_collector.collect_data(sub_tab) or {}
        except Exception:
            return self.data_collector.collect_data(sub_tab) or {}

    async def clean_old_files(self) -> None:
        try:
            for date_dir in self.data_dir.glob("20*"):
                if not date_dir.is_dir():
                    continue

                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y%m%d").date()
                    now_date = datetime.now().date()
                    days_diff = (now_date - dir_date).days

                    if days_diff > self.config.keep_days:
                        for file in date_dir.glob("*.json"):
                            file.unlink()
                        date_dir.rmdir()
                        continue
                except Exception:
                    continue

                files = list(date_dir.glob("*.json"))
                if len(files) > self.config.max_files_per_day:
                    files.sort(key=lambda x: x.stat().st_mtime)
                    for file in files[: -self.config.max_files_per_day]:
                        file.unlink()
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")

    def format_hot_list_message(
            self,
            hot_data: Dict[str, Any],
            count: int = None,
            show_detail: bool = False,
            sub_tab: str = "realtime",
    ) -> str:
        if count is None:
            count = self.config.max_items

        if not hot_data or "hot_items" not in hot_data:
            return (
                f"❌ 获取百度{self.get_sub_tab_display_name(sub_tab)}失败，请稍后再试"
            )

        hot_items = hot_data.get("hot_items", [])
        if not hot_items:
            return f"❌ 百度{self.get_sub_tab_display_name(sub_tab)}列表为空"

        hot_items = hot_items[: min(count, len(hot_items))]
        timestamp = hot_data.get("timestamp", "")
        time_str = timestamp
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%m-%d %H:%M")
        except:
            pass

        msg_parts = []
        sub_tab_name = self.get_sub_tab_display_name(sub_tab)
        header = (
            self.config.templates["header"]
            .replace("热搜榜", f"{sub_tab_name}榜")
            .format(time=time_str)
        )
        msg_parts.append(header)

        for idx, item in enumerate(hot_items, 1):
            title = item.get("title", "")
            hot_tag = ""
            highlight = ""

            if item.get("highlight", False):
                highlight = "🔴 "

            heat_num = item.get("heat_num", "")
            if heat_num:
                for key, emoji in self.config.category_emoji.items():
                    if key in title:
                        hot_tag = f" {emoji}"
                        break
                hot_tag += f" [{heat_num}]" if show_detail else ""

            item_text = self.config.templates["item"].format(
                rank=idx,
                highlight=highlight,
                title=title,
                hot_tag=hot_tag,
            )
            msg_parts.append(item_text)

        footer = self.config.templates["footer"].replace(
            "百度热搜", f"百度{sub_tab_name}"
        )
        if sub_tab == "realtime":
            footer += "\n💡 发送「百度热搜 详情ID」可查看指定条目详情，如「百度热搜 详情3」查看第3条"
        msg_parts.append(footer)

        return "".join(msg_parts)

    def format_hot_list_simple(
            self,
            hot_data: Dict[str, Any],
            count: int = None,
            sub_tab: str = "realtime",
    ) -> str:
        """格式化简约版热搜列表，只展示ID+标题+热度"""
        if count is None:
            count = self.config.max_items

        if not hot_data or "hot_items" not in hot_data:
            return (
                f"❌ 获取百度{self.get_sub_tab_display_name(sub_tab)}失败，请稍后再试"
            )

        hot_items = hot_data.get("hot_items", [])
        if not hot_items:
            return f"❌ 百度{self.get_sub_tab_display_name(sub_tab)}列表为空"

        hot_items = hot_items[: min(count, len(hot_items))]
        timestamp = hot_data.get("timestamp", "")
        time_str = timestamp
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%m-%d %H:%M")
        except:
            pass

        msg_parts = []
        sub_tab_name = self.get_sub_tab_display_name(sub_tab)
        header = f"📊 百度{sub_tab_name}榜 - 简约版 ({time_str})\n\n"
        msg_parts.append(header)

        for idx, item in enumerate(hot_items, 1):
            title = item.get("title", "")
            heat_num = item.get("heat_num", "")
            heat_display = f" [{heat_num}]" if heat_num else ""

            # 简约版只展示ID、标题和热度
            item_text = f"{idx}. {title}{heat_display}\n"
            msg_parts.append(item_text)

        footer = f"\n💡 提示: 发送「百度{sub_tab_name} 数字」可指定获取的条数"
        if sub_tab == "realtime":
            footer += f"\n💡 发送「百度{sub_tab_name} 详情ID」可查看详情，如「百度实时热点 详情3」"
        msg_parts.append(footer)

        return "".join(msg_parts)

    def format_hot_list_detailed(
            self,
            hot_data: Dict[str, Any],
            count: int = None,
            sub_tab: str = "realtime",
    ) -> str:
        """格式化详情版热搜列表，展示更多信息"""
        if count is None:
            count = self.config.max_items

        if not hot_data or "hot_items" not in hot_data:
            return (
                f"❌ 获取百度{self.get_sub_tab_display_name(sub_tab)}失败，请稍后再试"
            )

        hot_items = hot_data.get("hot_items", [])
        if not hot_items:
            return f"❌ 百度{self.get_sub_tab_display_name(sub_tab)}列表为空"

        hot_items = hot_items[: min(count, len(hot_items))]
        timestamp = hot_data.get("timestamp", "")
        time_str = timestamp
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%m-%d %H:%M")
        except:
            pass

        msg_parts = []
        sub_tab_name = self.get_sub_tab_display_name(sub_tab)
        header = f"📊 百度{sub_tab_name}榜 - 详情版 ({time_str})\n\n"
        msg_parts.append(header)

        for idx, item in enumerate(hot_items, 1):
            title = item.get("title", "")
            desc = item.get("desc", "")
            heat_num = item.get("heat_num", "")
            hot_tag = item.get("hot_tag", "")

            # 详情版展示更多信息
            item_text = f"{idx}. {title}\n"
            if heat_num:
                item_text += f"   🔥 热度: {heat_num}\n"
            if desc and len(desc) > 0:
                # 限制描述长度，保持消息简洁
                short_desc = desc[:50] + "..." if len(desc) > 50 else desc
                item_text += f"   📝 简介: {short_desc}\n"
            if hot_tag:
                item_text += f"   🏷️ 标签: {hot_tag}\n"

            item_text += "\n"
            msg_parts.append(item_text)

        footer = f"\n💡 提示: 发送「百度{sub_tab_name} 简约」可查看简约版"
        if sub_tab == "realtime":
            footer += f"\n💡 发送「百度{sub_tab_name} 详情ID」可查看单条详情，如「百度实时热点 详情3」"
        msg_parts.append(footer)

        return "".join(msg_parts)

    def format_hot_item_detail(
            self, hot_data: Dict[str, Any], item_id: int, sub_tab: str = "realtime"
    ) -> str:
        """格式化单个热搜条目的详细信息"""
        if not hot_data or "hot_items" not in hot_data:
            return (
                f"❌ 获取百度{self.get_sub_tab_display_name(sub_tab)}失败，请稍后再试"
            )

        hot_items = hot_data.get("hot_items", [])
        if not hot_items:
            return f"❌ 百度{self.get_sub_tab_display_name(sub_tab)}列表为空"

        if item_id < 1 or item_id > len(hot_items):
            return f"❌ ID超出范围，请输入1-{len(hot_items)}之间的数字"

        item = hot_items[item_id - 1]
        title = item.get("title", "")
        desc = item.get("desc", "暂无描述")
        heat_num = item.get("heat_num", "")
        url = item.get("url", "")
        hot_tag = item.get("hot_tag", "")

        sub_tab_name = self.get_sub_tab_display_name(sub_tab)
        timestamp = hot_data.get("timestamp", "")
        time_str = timestamp
        try:
            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            time_str = dt.strftime("%m-%d %H:%M")
        except:
            pass

        # 构建详情消息
        msg_parts = [
            f"📊 百度{sub_tab_name}详情 ({time_str})\n\n",
            f"🔍 [{item_id}] {title}\n",
            f"📝 描述: {desc}\n",
        ]

        if heat_num:
            msg_parts.append(f"🔥 热度: {heat_num}\n")

        if hot_tag:
            msg_parts.append(f"🏷️ 标签: {hot_tag}\n")

        if url:
            msg_parts.append(f"🔗 链接: {url}\n")

        return "".join(msg_parts)

    def get_sub_tab_display_name(self, sub_tab: str) -> str:
        sub_tab_names = {
            "realtime": "实时热点",
            "phrase": "热搜词",
            "novel": "小说",
            "game": "游戏",
            "car": "汽车",
            "teleplay": "电视剧",
        }
        return sub_tab_names.get(sub_tab, "热搜")

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        self.check_config_update()
        content = msg.raw_message.strip()
        user_id = msg.user_id
        group_id = msg.group_id

        if not self.is_user_authorized(user_id, group_id):
            return

        # 处理百度热搜命令
        if content == "百度热搜" or content.startswith("百度热搜 "):
            await self.handle_hot_search(msg)
        # 处理各种分类热搜命令
        elif content == "百度实时热点" or content.startswith("百度实时热点 "):
            await self.handle_specific_tab(msg, "realtime")
        elif content == "百度热搜词" or content.startswith("百度热搜词 "):
            await self.handle_specific_tab(msg, "phrase")
        elif content == "百度小说榜" or content.startswith("百度小说榜 "):
            await self.handle_specific_tab(msg, "novel")
        elif content == "百度游戏榜" or content.startswith("百度游戏榜 "):
            await self.handle_specific_tab(msg, "game")
        elif content == "百度汽车榜" or content.startswith("百度汽车榜 "):
            await self.handle_specific_tab(msg, "car")
        elif content == "百度电视剧榜" or content.startswith("百度电视剧榜 "):
            await self.handle_specific_tab(msg, "teleplay")

    async def handle_hot_search(self, msg: GroupMessage):
        """处理百度热搜命令"""
        content = msg.raw_message.strip()

        # 默认参数
        count = self.config.max_items
        sub_tab = "realtime"
        detail_id = None
        display_mode = "normal"  # 默认展示模式：normal, simple, detailed

        # 解析参数
        if " " in content:
            parts = content.split(" ", 1)
            params = parts[1].strip().split()

            for param in params:
                # 处理详情ID查询
                detail_match = re.search(r"详情(\d+)", param)
                if detail_match and sub_tab == "realtime":  # 只有实时热点支持详情查询
                    detail_id = int(detail_match.group(1))
                    continue

                # 处理展示模式
                if param in ["简约", "simple"]:
                    display_mode = "simple"
                    continue
                elif param in ["详情", "detailed", "detail"]:
                    display_mode = "detailed"
                    continue

                # 处理分类
                tab_map = {
                    "实时热点": "realtime",
                    "热搜词": "phrase",
                    "小说": "novel",
                    "游戏": "game",
                    "汽车": "car",
                    "电视剧": "teleplay",
                }
                if param in tab_map:
                    sub_tab = tab_map[param]
                    continue

                # 处理数量
                if param.isdigit():
                    count = int(param)
                    count = min(max(1, count), 50)

        # 获取数据
        hot_data = self.get_latest_hot_list(count, sub_tab)

        # 按要求展示数据
        if detail_id is not None and sub_tab == "realtime":
            # 查看特定ID的详情
            reply = self.format_hot_item_detail(hot_data, detail_id, sub_tab)
        else:
            # 根据展示模式返回不同格式
            if display_mode == "simple":
                reply = self.format_hot_list_simple(hot_data, count, sub_tab)
            elif display_mode == "detailed":
                reply = self.format_hot_list_detailed(hot_data, count, sub_tab)
            else:
                reply = self.format_hot_list_message(hot_data, count, False, sub_tab)

        await msg.reply(text=reply)

    async def handle_specific_tab(self, msg: GroupMessage, sub_tab: str):
        """处理特定分类的热搜命令"""
        content = msg.raw_message.strip()

        # 默认参数
        count = self.config.max_items
        detail_id = None
        display_mode = "normal"  # 默认展示模式：normal, simple, detailed

        # 解析参数
        if " " in content:
            parts = content.split(" ", 1)
            params = parts[1].strip().split()

            for param in params:
                # 处理详情ID查询，只有实时热点支持
                detail_match = re.search(r"详情(\d+)", param)
                if detail_match and sub_tab == "realtime":
                    detail_id = int(detail_match.group(1))
                    continue

                # 处理展示模式
                if param in ["简约", "simple"]:
                    display_mode = "simple"
                    continue
                elif param in ["详情", "detailed", "detail"]:
                    display_mode = "detailed"
                    continue

                # 处理数量
                if param.isdigit():
                    count = int(param)
                    count = min(max(1, count), 50)

        # 获取数据
        hot_data = self.get_latest_hot_list(count, sub_tab)

        # 按要求展示数据
        if detail_id is not None and sub_tab == "realtime":
            # 查看特定ID的详情，只有实时热点支持
            reply = self.format_hot_item_detail(hot_data, detail_id, sub_tab)
        else:
            # 根据展示模式返回不同格式
            if display_mode == "simple":
                reply = self.format_hot_list_simple(hot_data, count, sub_tab)
            elif display_mode == "detailed":
                reply = self.format_hot_list_detailed(hot_data, count, sub_tab)
            else:
                reply = self.format_hot_list_message(hot_data, count, False, sub_tab)

        await msg.reply(text=reply)

    async def on_exit(self) -> None:
        pass
