import datetime
import json
import os
import shutil
import time
import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from utils import scheduler

bot = CompatibleEnrollment  # 兼容回调函数注册器

# 上下文限制常量
MAX_CONTEXT_LENGTH = 64000  # deepseek-chat 模型的上下文长度为64K
MAX_OUTPUT_TOKENS = 4000  # 默认输出长度
RESERVE_TOKENS = 1000  # 为系统消息和新请求预留的token数量

# 命令前缀
CMD_PREFIX = "/cr_"

# 音频复制重试配置
MAX_RETRY_ATTEMPTS = 10
RETRY_INTERVALS = [10, 30, 50, 100, 100, 100, 100, 100, 100, 100]  # 重试间隔时间(毫秒)


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    OTHER = "other"


class CriticStyle(Enum):
    SUNBA = "sunba"  # 孙吧风格
    NUCLEAR = "nuclear"  # 核战避难吧风格
    NGA = "nga"  # NGA风格
    ZHIHU = "zhihu"  # 知乎风格


@dataclass
class Config:
    api_key: str  # Deepseek API密钥
    whitelist_groups: List[int]  # 白名单群组ID
    whitelist_users: List[int]  # 白名单用户ID
    admin_users: List[int]  # 超级管理员ID

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            api_key=data.get("api_key", ""),
            whitelist_groups=data.get("whitelist", {}).get("group_ids", []),
            whitelist_users=data.get("whitelist", {}).get("user_ids", []),
            admin_users=data.get("whitelist", {}).get("admin_ids", []),
        )


def call_deepseek_api(
        api_key: str,
        messages: List[Dict[str, str]],
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 1000,
) -> Dict[str, Any]:
    """调用 Deepseek API"""
    try:
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        response = requests.post(api_url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def generate_criticism(
        api_key: str, user_id: int, records: List[Dict[str, Any]], style: CriticStyle
) -> str:
    """生成对用户的锐评

    Args:
        api_key: Deepseek API密钥
        user_id: 用户ID
        records: 用户消息记录
        style: 锐评风格

    Returns:
        str: 生成的锐评文本
    """
    if not api_key:
        return "错误：未配置API密钥"

    if not records:
        return f"没有找到用户 {user_id} 的消息记录"

    # 限制消息记录数量和总长度，避免超出上下文
    text_records = [
        record for record in records if record["type"] == MessageType.TEXT.value
    ]

    if len(text_records) > 20:
        text_records = text_records[-20:]  # 只使用最近的20条记录

    # 构建消息记录文本
    context_lines = []
    total_length = 0

    # 从最新的消息开始处理，确保最新的消息被优先保留
    for record in reversed(text_records):
        line = f"时间: {record['time']}, 内容: {record['content']}"
        line_length = len(line)

        # 如果添加这条记录会超出上下文限制，则停止添加
        if total_length + line_length > MAX_CONTEXT_LENGTH - RESERVE_TOKENS:
            break

        context_lines.insert(0, line)  # 插入到列表开头，保持时间顺序
        total_length += line_length

    context = "\n".join(context_lines)

    # 检查是否有足够的文本内容
    if not context.strip():
        return f"没有找到用户 {user_id} 的足够文本消息"

    # 根据风格构建提示词
    style_prompts = {
        CriticStyle.SUNBA: "请以孙笑川吧(孙吧)的风格，对以下用户发言进行锐评。要充满嘲讽，使用典型的孙吧网络语言，包含恶搞和滑稽的要素。",
        CriticStyle.NUCLEAR: "请以核战避难吧的风格，对以下用户发言进行锐评。要体现出黑暗、反讽、末日氛围，掺杂政治隐喻和阴谋论调侃。",
        CriticStyle.NGA: "请以NGA论坛的风格，对以下用户发言进行锐评。要像资深游戏玩家，使用游戏术语，充满戾气和直男癌的发言方式。",
        CriticStyle.ZHIHU: "请以知乎平台的风格，对以下用户发言进行锐评。要像一个傲慢的精英主义者，用假装客观的语言表达自己的优越感。",
    }

    # 构建API请求
    messages = [
        {"role": "system", "content": style_prompts[style]},
        {
            "role": "user",
            "content": f"以下是用户 {user_id} 的发言记录，请对其进行锐评:\n\n{context}",
        },
    ]

    # 调用Deepseek API
    try:
        result = call_deepseek_api(api_key, messages)

        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"API调用失败: {json.dumps(result, ensure_ascii=False)}"
    except Exception as e:
        return f"生成锐评时出错: {str(e)}"


class ChatRecordPlugin(BasePlugin):
    name = "ChatRecordPlugin"  # 插件名称
    version = "0.0.1"  # 插件版本

    # 定义类变量
    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    images_dir = None
    audio_dir = None
    video_dir = None
    file_dir = None

    # 当前选择的用户
    selected_user = None
    selected_style = CriticStyle.SUNBA

    async def on_load(self):
        """插件加载时执行的操作"""
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")

        # 初始化配置路径
        self.config_path = Path(__file__).parent / "config" / "config.toml"
        self.data_dir = Path(__file__).parent / "data"
        self.images_dir = self.data_dir / "images"
        self.audio_dir = self.data_dir / "audio"
        self.video_dir = self.data_dir / "video"
        self.file_dir = self.data_dir / "file"

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)
        os.makedirs(self.file_dir, exist_ok=True)

        # 加载配置
        self.load_config()

        # 添加配置文件监控任务
        scheduler.add_task(self.check_config_update, 30)  # 每30秒检查一次配置更新

        # 添加聊天记录备份任务
        scheduler.add_task(
            self.backup_daily_records, 3600
        )  # 每小时检查一次是否需要备份

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "rb") as f:
                    config_data = tomllib.load(f)
                    self.config = Config.from_dict(config_data)
                self.config_last_modified = os.path.getmtime(self.config_path)
                print(f"成功加载 {self.name} 配置")
            else:
                print(f"警告: {self.name} 配置文件不存在: {self.config_path}")
                self.config = Config("", [], [], [])
        except Exception as e:
            print(f"加载 {self.name} 配置出错: {str(e)}")
            self.config = Config("", [], [], [])

    def check_config_update(self) -> bool:
        """检查配置文件是否已更新"""
        try:
            if self.config_path.exists():
                last_modified = os.path.getmtime(self.config_path)
                if last_modified > self.config_last_modified:
                    print(f"{self.name} 配置文件已更新，重新加载")
                    self.load_config()
                    return True
            return False
        except Exception as e:
            print(f"检查 {self.name} 配置更新出错: {str(e)}")
            return False

    def backup_daily_records(self) -> None:
        """检查并执行每日聊天记录备份

        每天 00:00 左右将当天的消息记录备份为 messages_年月日.json 并清空主文件
        """
        try:
            current_time = datetime.datetime.now()

            # 检查是否接近午夜或刚过午夜
            # 如果时间在0点到1点之间，或23点到24点之间
            if (0 <= current_time.hour < 1) or (23 <= current_time.hour < 24):
                # 获取昨天的日期字符串
                yesterday = (
                    (current_time - datetime.timedelta(days=1)).strftime("%Y%m%d")
                    if current_time.hour < 1
                    else current_time.strftime("%Y%m%d")
                )

                # 遍历所有群组目录
                for group_dir in self.data_dir.iterdir():
                    if group_dir.is_dir() and group_dir.name not in [
                        "images",
                        "audio",
                        "video",
                        "file",
                    ]:
                        # 遍历所有用户目录
                        for user_dir in group_dir.iterdir():
                            if user_dir.is_dir():
                                message_file = user_dir / "messages.json"

                                # 如果消息文件存在且有内容
                                if (
                                        message_file.exists()
                                        and message_file.stat().st_size > 0
                                ):
                                    # 创建备份文件名
                                    backup_file = (
                                            user_dir / f"messages_{yesterday}.json"
                                    )

                                    # 如果备份文件不存在，则创建备份并清空原文件
                                    if not backup_file.exists():
                                        # 读取当前消息
                                        try:
                                            with open(
                                                    message_file, "r", encoding="utf-8"
                                            ) as f:
                                                messages = json.load(f)

                                            # 创建备份文件
                                            with open(
                                                    backup_file, "w", encoding="utf-8"
                                            ) as f:
                                                json.dump(
                                                    messages,
                                                    f,
                                                    ensure_ascii=False,
                                                    indent=2,
                                                )

                                            # 清空原文件
                                            with open(
                                                    message_file, "w", encoding="utf-8"
                                            ) as f:
                                                json.dump(
                                                    [], f, ensure_ascii=False, indent=2
                                                )

                                            print(
                                                f"已备份 {group_dir.name}/{user_dir.name} 的消息记录到 {backup_file.name}"
                                            )
                                        except Exception as e:
                                            print(
                                                f"备份 {group_dir.name}/{user_dir.name} 的消息记录出错: {str(e)}"
                                            )

                print(
                    f"完成每日聊天记录备份检查 ({current_time.strftime('%Y-%m-%d %H:%M:%S')})"
                )
        except Exception as e:
            print(f"执行聊天记录备份任务出错: {str(e)}")

    def is_user_admin(self, user_id: int) -> bool:
        """检查用户是否为超级管理员"""
        if not self.config:
            return False
        return user_id in self.config.admin_users

    def parse_message_type(
            self, message: List[Dict]
    ) -> Tuple[MessageType, Optional[Dict]]:
        """解析消息类型和相关数据

        Args:
            message: 原始消息内容

        Returns:
            Tuple[MessageType, Optional[Dict]]: 消息类型和相关数据
        """
        if not isinstance(message, list):
            return MessageType.TEXT, None

        # 检查图片消息
        image_info = self.parse_image_message(message)
        if image_info:
            return MessageType.IMAGE, image_info

        # 检查音频消息
        audio_info = self.parse_audio_message(message)
        if audio_info:
            return MessageType.VOICE, audio_info

        # 检查视频和文件
        for item in message:
            if isinstance(item, dict) and "type" in item:
                if item["type"] == "video":
                    return MessageType.VIDEO, item.get("data", {})
                elif item["type"] == "file":
                    return MessageType.FILE, item.get("data", {})

        # 默认为文本
        return MessageType.TEXT, None

    def download_image(
            self, url: str, file_name: str, group_id: int, user_id: int
    ) -> str:
        """下载图片并保存到本地

        Args:
            url: 图片URL
            file_name: 原始文件名
            group_id: 群组ID
            user_id: 用户ID

        Returns:
            str: 保存的图片本地路径
        """
        try:
            # 创建用户图片目录
            group_images_dir = self.images_dir / str(group_id) / str(user_id)
            os.makedirs(group_images_dir, exist_ok=True)

            # 生成时间戳作为文件名前缀，避免重名
            timestamp = int(time.time())
            local_file_name = f"{timestamp}_{file_name}"
            local_path = group_images_dir / local_file_name

            # 下载图片
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(response.content)
                print(f"图片已保存: {local_path}")
                return str(local_path)
            else:
                print(f"下载图片失败，状态码: {response.status_code}")
                return ""
        except Exception as e:
            print(f"下载图片出错: {str(e)}")
            return ""

    def copy_audio(
            self, source_path: str, file_name: str, group_id: int, user_id: int
    ) -> str:
        """复制音频文件到本地存储，失败时进行多次重试

        Args:
            source_path: 源文件路径
            file_name: 原始文件名
            group_id: 群组ID
            user_id: 用户ID

        Returns:
            str: 保存的音频本地路径
        """
        # 创建用户音频目录
        group_audio_dir = self.audio_dir / str(group_id) / str(user_id)
        os.makedirs(group_audio_dir, exist_ok=True)

        # 生成时间戳作为文件名前缀，避免重名
        timestamp = int(time.time())
        local_file_name = f"{timestamp}_{file_name}"
        local_path = group_audio_dir / local_file_name

        # 进行多次重试
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                # 复制文件
                shutil.copy(source_path, local_path)
                print(f"音频已保存: {local_path} (尝试 {attempt + 1})")
                return str(local_path)
            except Exception as e:
                print(
                    f"复制音频出错 (尝试 {attempt + 1}/{MAX_RETRY_ATTEMPTS}): {str(e)}"
                )

                # 最后一次尝试失败，直接返回
                if attempt >= MAX_RETRY_ATTEMPTS - 1:
                    return ""

                # 等待指定时间后重试
                retry_ms = RETRY_INTERVALS[min(attempt, len(RETRY_INTERVALS) - 1)]
                time.sleep(retry_ms / 1000)  # 毫秒转秒

        return ""  # 所有尝试都失败

    def handle_text_message(
            self, group_id: int, user_id: int, content: str
    ) -> Dict[str, Any]:
        """处理文本消息

        Args:
            group_id: 群组ID
            user_id: 用户ID
            content: 消息内容

        Returns:
            Dict: 消息记录
        """
        # 准备记录数据
        timestamp = int(time.time())
        return {
            "timestamp": timestamp,
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)),
            "type": MessageType.TEXT.value,
            "content": content,
        }

    def handle_image_message(
            self, group_id: int, user_id: int, content: str, image_info: Dict
    ) -> Dict[str, Any]:
        """处理图片消息

        Args:
            group_id: 群组ID
            user_id: 用户ID
            content: 消息内容
            image_info: 图片信息

        Returns:
            Dict: 消息记录
        """
        # 准备基础记录
        record = self.handle_text_message(group_id, user_id, content)
        record["type"] = MessageType.IMAGE.value

        # 下载并保存图片
        if image_info and image_info.get("url") and image_info.get("file"):
            local_path = self.download_image(
                image_info["url"], image_info["file"], group_id, user_id
            )

            # 添加图片信息到记录
            if local_path:
                record["image"] = {
                    "local_path": local_path,
                    "file": image_info["file"],
                    "file_size": image_info.get("file_size", ""),
                    "url": image_info["url"],
                }

        return record

    def handle_audio_message(
            self, group_id: int, user_id: int, content: str, audio_info: Dict
    ) -> Dict[str, Any]:
        """处理音频消息

        Args:
            group_id: 群组ID
            user_id: 用户ID
            content: 消息内容
            audio_info: 音频信息

        Returns:
            Dict: 消息记录
        """
        # 准备基础记录
        record = self.handle_text_message(group_id, user_id, content)
        record["type"] = MessageType.VOICE.value

        # 复制音频文件
        if audio_info and audio_info.get("path") and audio_info.get("file"):
            local_path = self.copy_audio(
                audio_info["path"], audio_info["file"], group_id, user_id
            )

            # 添加音频信息到记录
            if local_path:
                record["audio"] = {
                    "local_path": local_path,
                    "file": audio_info["file"],
                    "file_size": audio_info.get("file_size", ""),
                    "original_path": audio_info["path"],
                }

        return record

    def handle_video_message(
            self, group_id: int, user_id: int, content: str, video_info: Dict
    ) -> Dict[str, Any]:
        """处理视频消息

        Args:
            group_id: 群组ID
            user_id: 用户ID
            content: 消息内容
            video_info: 视频信息

        Returns:
            Dict: 消息记录
        """
        # 准备基础记录
        record = self.handle_text_message(group_id, user_id, content)
        record["type"] = MessageType.VIDEO.value

        # 添加视频信息到记录
        if video_info:
            record["video"] = video_info

        return record

    def handle_file_message(
            self, group_id: int, user_id: int, content: str, file_info: Dict
    ) -> Dict[str, Any]:
        """处理文件消息

        Args:
            group_id: 群组ID
            user_id: 用户ID
            content: 消息内容
            file_info: 文件信息

        Returns:
            Dict: 消息记录
        """
        # 准备基础记录
        record = self.handle_text_message(group_id, user_id, content)
        record["type"] = MessageType.FILE.value

        # 添加文件信息到记录
        if file_info:
            record["file"] = file_info

        return record

    def parse_image_message(self, message: List[Dict]) -> Optional[Dict]:
        """解析图片消息

        Args:
            message: 消息内容

        Returns:
            Dict: 图片信息，包含文件名、URL等，如果不是图片则返回None
        """
        if not isinstance(message, list):
            return None

        for item in message:
            if (
                    isinstance(item, dict)
                    and item.get("type") == "image"
                    and "data" in item
                    and isinstance(item["data"], dict)
            ):
                image_data = item["data"]
                return {
                    "file": image_data.get("file", ""),
                    "file_size": image_data.get("file_size", ""),
                    "url": image_data.get("url", ""),
                    "sub_type": image_data.get("sub_type", 0),
                    "summary": image_data.get("summary", ""),
                }

        return None

    def parse_audio_message(self, message: List[Dict]) -> Optional[Dict]:
        """解析音频消息

        Args:
            message: 消息内容

        Returns:
            Dict: 音频信息，包含文件名、路径等，如果不是音频则返回None
        """
        if not isinstance(message, list):
            return None

        for item in message:
            if (
                    isinstance(item, dict)
                    and (item.get("type") == "record" or item.get("type") == "voice")
                    and "data" in item
                    and isinstance(item["data"], dict)
            ):
                audio_data = item["data"]
                return {
                    "file": audio_data.get("file", ""),
                    "file_size": audio_data.get("file_size", ""),
                    "path": audio_data.get("path", ""),
                }

        return None

    def record_message(
            self,
            group_id: int,
            user_id: int,
            message_type: MessageType,
            content: str,
            raw_message: Optional[List[Dict]] = None,
    ) -> None:
        """记录群聊消息"""
        if not group_id or not user_id:
            return

        # 创建目录结构
        group_dir = self.data_dir / str(group_id)
        user_dir = group_dir / str(user_id)
        os.makedirs(user_dir, exist_ok=True)

        # 创建记录文件路径
        record_file = user_dir / "messages.json"

        # 获取现有记录
        records = []
        if record_file.exists():
            try:
                with open(record_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
            except Exception as e:
                print(f"读取消息记录出错: {str(e)}")

        # 解析消息并创建记录
        new_record = None
        message_info = None

        # 如果提供了原始消息，尝试重新解析
        if raw_message:
            message_type, message_info = self.parse_message_type(raw_message)

        # 根据消息类型处理
        if message_type == MessageType.IMAGE:
            new_record = self.handle_image_message(
                group_id, user_id, content, message_info
            )
        elif message_type == MessageType.VOICE:
            new_record = self.handle_audio_message(
                group_id, user_id, content, message_info
            )
        elif message_type == MessageType.VIDEO:
            new_record = self.handle_video_message(
                group_id, user_id, content, message_info
            )
        elif message_type == MessageType.FILE:
            new_record = self.handle_file_message(
                group_id, user_id, content, message_info
            )
        else:
            new_record = self.handle_text_message(group_id, user_id, content)

        # 添加记录
        if new_record:
            records.append(new_record)

        # 保存记录
        try:
            with open(record_file, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存消息记录出错: {str(e)}")

    def get_user_records(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有文本消息记录

        Args:
            user_id: 用户ID

        Returns:
            List[Dict[str, Any]]: 用户的文本消息记录列表
        """
        records = []

        # 遍历所有群组目录
        for group_dir in self.data_dir.iterdir():
            if group_dir.is_dir() and group_dir.name not in [
                "images",
                "audio",
                "video",
                "file",
            ]:  # 排除媒体目录
                user_dir = group_dir / str(user_id)
                if user_dir.exists() and user_dir.is_dir():
                    # 处理当前消息文件
                    self._process_record_file(
                        user_dir / "messages.json", records, int(group_dir.name)
                    )

                    # 处理历史备份文件
                    for backup_file in user_dir.glob("messages_*.json"):
                        self._process_record_file(
                            backup_file, records, int(group_dir.name)
                        )

        # 按时间排序
        records.sort(key=lambda x: x["timestamp"])
        return records

    def _process_record_file(
            self, file_path: Path, records: List[Dict[str, Any]], group_id: int
    ) -> None:
        """处理一个记录文件，提取文本消息

        Args:
            file_path: 记录文件路径
            records: 记录列表，用于添加读取的记录
            group_id: 群组ID
        """
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_records = json.load(f)

                    # 只添加文本类型的消息
                    for record in file_records:
                        if record["type"] == MessageType.TEXT.value:
                            # 添加群组ID信息
                            record["group_id"] = group_id
                            records.append(record)
            except Exception as e:
                print(f"读取记录文件 {file_path} 出错: {str(e)}")

    def get_users_with_records(self) -> List[str]:
        """获取所有有记录的用户ID列表"""
        user_ids = set()

        # 遍历所有群组目录
        for group_dir in self.data_dir.iterdir():
            if group_dir.is_dir() and group_dir.name not in [
                "images",
                "audio",
                "video",
                "file",
            ]:  # 排除媒体目录
                for user_dir in group_dir.iterdir():
                    if user_dir.is_dir():
                        # 检查当前消息文件
                        if (user_dir / "messages.json").exists():
                            user_ids.add(user_dir.name)
                            continue

                        # 检查历史备份文件
                        backup_files = list(user_dir.glob("messages_*.json"))
                        if backup_files:
                            user_ids.add(user_dir.name)

        return sorted(list(user_ids))

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        if not self.config:
            return

        # 检查群组是否在白名单中
        group_id = msg.group_id
        user_id = msg.user_id

        if group_id not in self.config.whitelist_groups:
            return

        # 获取原始消息
        raw_message = msg.message

        # 解析消息类型及数据
        message_type, _ = self.parse_message_type(raw_message)

        # 记录消息
        self.record_message(
            group_id, user_id, message_type, msg.raw_message, raw_message
        )

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        if not self.config:
            return

        user_id = msg.user_id

        # 只处理超级管理员的消息
        if not self.is_user_admin(user_id):
            return

        # 命令处理 (添加前缀)
        raw_message = msg.raw_message

        if raw_message.startswith(f"{CMD_PREFIX}list_users"):
            users = self.get_users_with_records()
            if users:
                await msg.reply(text=f"有记录的用户列表:\n{', '.join(users)}")
            else:
                await msg.reply(text="没有找到任何用户记录")

        elif raw_message.startswith(f"{CMD_PREFIX}select_user "):
            try:
                selected_id = int(raw_message.split(" ")[1])
                self.selected_user = selected_id
                await msg.reply(text=f"已选择用户: {selected_id}")
            except (ValueError, IndexError):
                await msg.reply(
                    text=f"格式错误，正确格式: {CMD_PREFIX}select_user [用户ID]"
                )

        elif raw_message.startswith(f"{CMD_PREFIX}set_style "):
            try:
                style_name = raw_message.split(" ")[1].lower()
                if style_name == "sunba":
                    self.selected_style = CriticStyle.SUNBA
                elif style_name == "nuclear":
                    self.selected_style = CriticStyle.NUCLEAR
                elif style_name == "nga":
                    self.selected_style = CriticStyle.NGA
                elif style_name == "zhihu":
                    self.selected_style = CriticStyle.ZHIHU
                else:
                    await msg.reply(
                        text="不支持的风格，可选: sunba, nuclear, nga, zhihu"
                    )
                    return
                await msg.reply(text=f"锐评风格已设置为: {style_name}")
            except (ValueError, IndexError):
                await msg.reply(
                    text=f"格式错误，正确格式: {CMD_PREFIX}set_style [风格名]"
                )

        elif raw_message == f"{CMD_PREFIX}criticize":
            if not self.selected_user:
                await msg.reply(
                    text=f"请先使用 {CMD_PREFIX}select_user [用户ID] 选择一个用户"
                )
                return

            await msg.reply(
                text=f"正在生成对用户 {self.selected_user} 的{self.selected_style.value}风格锐评..."
            )
            user_records = self.get_user_records(self.selected_user)
            criticism = generate_criticism(
                self.config.api_key,
                self.selected_user,
                user_records,
                self.selected_style,
            )
            await msg.reply(text=criticism)

        elif raw_message == f"{CMD_PREFIX}help":
            await msg.reply(
                text=f"""可用命令:
{CMD_PREFIX}list_users - 列出所有有记录的用户
{CMD_PREFIX}select_user [用户ID] - 选择要锐评的用户
{CMD_PREFIX}set_style [风格] - 设置锐评风格 (sunba/nuclear/nga/zhihu)
{CMD_PREFIX}criticize - 对选中的用户进行锐评
{CMD_PREFIX}help - 显示此帮助信息"""
            )
