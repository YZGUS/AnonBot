import json
import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import requests
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from utils import scheduler

bot = CompatibleEnrollment  # 兼容回调函数注册器

# 上下文限制常量
MAX_CONTEXT_LENGTH = 64000  # deepseek-chat 模型的上下文长度为64K
MAX_OUTPUT_TOKENS = 4000  # 默认输出长度
RESERVE_TOKENS = 1000  # 为系统消息和新请求预留的token数量


@dataclass
class Config:
    api_key: str
    whitelist_groups: List[int]
    whitelist_users: List[int]
    default_model: str
    temperature: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            api_key=data.get("api_key", ""),
            whitelist_groups=data.get("whitelist", {}).get("group_ids", []),
            whitelist_users=data.get("whitelist", {}).get("user_ids", []),
            default_model=data.get("model", {}).get("default", "deepseek-chat"),
            temperature=data.get("model", {}).get("temperature", 1.0),
        )


class DeepSeekPlugin(BasePlugin):
    name = "DeepSeekPlugin"  # 插件名称
    version = "0.0.1"  # 插件版本

    # 定义类变量而不是在__init__中初始化
    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None
    # 存储用户对话历史
    conversation_history = {}
    # 用户是否启用记忆模式
    memory_enabled = {}

    async def on_load(self):
        """插件加载时执行的操作"""
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")

        # 初始化配置路径
        self.config_path = Path(__file__).parent / "config" / "config.toml"
        self.data_dir = Path(__file__).parent / "data"

        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)

        # 加载配置
        self.load_config()

        # 加载对话历史
        self.load_conversation_history()

        # 添加配置文件监控任务
        scheduler.add_task(self.check_config_update, 30)  # 每30秒检查一次配置更新

        # 添加定期保存对话历史任务
        scheduler.add_task(
            self.save_conversation_history, 300
        )  # 每5分钟保存一次对话历史

    def load_conversation_history(self) -> None:
        """加载对话历史"""
        history_path = self.data_dir / "conversation_history.json"
        memory_path = self.data_dir / "memory_status.json"

        try:
            if history_path.exists():
                with open(history_path, "r", encoding="utf-8") as f:
                    self.conversation_history = json.load(f)
                print(f"成功加载对话历史数据")

            if memory_path.exists():
                with open(memory_path, "r", encoding="utf-8") as f:
                    self.memory_enabled = json.load(f)
                print(f"成功加载记忆模式状态数据")
        except Exception as e:
            print(f"加载对话历史或记忆模式状态出错: {str(e)}")

    def save_conversation_history(self) -> None:
        """保存对话历史"""
        try:
            history_path = self.data_dir / "conversation_history.json"
            memory_path = self.data_dir / "memory_status.json"

            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)

            with open(memory_path, "w", encoding="utf-8") as f:
                json.dump(self.memory_enabled, f, ensure_ascii=False)

            print(f"成功保存对话历史和记忆模式状态")
            return True
        except Exception as e:
            print(f"保存对话历史和记忆模式状态出错: {str(e)}")
            return False

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
                self.config = Config("", [], [], "deepseek-chat", 1.0)
        except Exception as e:
            print(f"加载 {self.name} 配置出错: {str(e)}")
            self.config = Config("", [], [], "deepseek-chat", 1.0)

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

    def is_user_authorized(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """检查用户是否有权限使用此插件"""
        if not self.config:
            return False

        # 检查用户ID是否在白名单中
        if user_id in self.config.whitelist_users:
            return True

        # 如果提供了群组ID，检查群组是否在白名单中
        if group_id and group_id in self.config.whitelist_groups:
            return True

        return False

    def estimate_tokens(self, text: str) -> int:
        """粗略估计文本包含的token数量

        一个粗略的估计方法是：
        - 英文词平均约为1.3个tokens
        - 中文字符约为1.5个tokens

        这只是一个估计，实际token数可能会有所不同
        """
        # 计算英文词数
        english_words = len(re.findall(r"[a-zA-Z]+", text))
        # 计算中文字符数
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # 计算数字
        digits = len(re.findall(r"\d+", text))
        # 计算标点符号
        punctuation = len(re.findall(r'[,.;:?!()[\]{}\'"`]', text))

        # 估算总token数
        return int(english_words * 1.3 + chinese_chars * 1.5 + digits + punctuation)

    def calculate_message_tokens(self, message: Dict[str, str]) -> int:
        """计算单个消息的预估token数"""
        role_tokens = 4  # 估计role字段占用的token数
        content = message.get("content", "")
        content_tokens = self.estimate_tokens(content)
        return role_tokens + content_tokens

    def get_user_history(self, user_id: Union[int, str]) -> List[Dict[str, str]]:
        """获取用户的对话历史，从最近的消息开始加载，确保不超出上下文限制"""
        user_id_str = str(user_id)
        full_history = self.conversation_history.get(user_id_str, [])

        if not full_history:
            return []

        # 从后往前构建历史记录，确保不超出token限制
        available_tokens = MAX_CONTEXT_LENGTH - RESERVE_TOKENS - MAX_OUTPUT_TOKENS
        result = []
        total_tokens = 0

        # 从最新的消息开始处理（反向遍历）
        for message in reversed(full_history):
            message_tokens = self.calculate_message_tokens(message)

            # 如果添加这条消息会超出限制，就停止添加
            if total_tokens + message_tokens > available_tokens:
                break

            # 将消息添加到结果的开头（保持原始顺序）
            result.insert(0, message)
            total_tokens += message_tokens

        if len(result) < len(full_history):
            print(
                f"由于上下文限制，仅加载了最近 {len(result)}/{len(full_history)} 条消息记录"
            )

        return result

    def add_to_history(self, user_id: Union[int, str], role: str, content: str) -> None:
        """添加消息到用户的对话历史"""
        user_id_str = str(user_id)
        if user_id_str not in self.conversation_history:
            self.conversation_history[user_id_str] = []

        # 添加新消息
        self.conversation_history[user_id_str].append(
            {"role": role, "content": content}
        )

        # 限制历史记录长度，保留最近的10轮对话（20条消息）
        if len(self.conversation_history[user_id_str]) > 20:
            self.conversation_history[user_id_str] = self.conversation_history[
                user_id_str
            ][-20:]

    def clear_history(self, user_id: Union[int, str]) -> None:
        """清除用户的对话历史"""
        user_id_str = str(user_id)
        if user_id_str in self.conversation_history:
            self.conversation_history[user_id_str] = []

    async def call_deepseek_api(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = 4000,
    ) -> Dict[str, Any]:
        """调用DeepSeek API"""
        if not self.config or not self.config.api_key:
            return {"error": "API密钥未配置"}

        model = model or self.config.default_model
        temperature = temperature or self.config.temperature

        # 估算输入token数量
        estimated_input_tokens = sum(
            self.calculate_message_tokens(msg) for msg in messages
        )
        print(f"预估输入token数: {estimated_input_tokens}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            response = requests.post(
                "https://api.deepseek.com/chat/completions", headers=headers, json=data
            )
            response.raise_for_status()
            result = response.json()

            # 如果返回结果中包含用量信息，记录实际token数
            if "usage" in result:
                print(f"实际token用量: {result['usage']}")

            return result
        except Exception as e:
            return {"error": f"API调用失败: {str(e)}"}

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群消息事件"""
        # 判断是否为ds命令或@机器人
        is_command = msg.raw_message.startswith("ds ")
        is_at_bot = msg.raw_message.startswith("@") and "[CQ:at,qq=" in msg.raw_message

        if not (is_command or is_at_bot):
            return

        # 检查用户权限
        if not self.is_user_authorized(msg.user_id, msg.group_id):
            await self.api.post_group_msg(
                msg.group_id, text="🚫 您没有权限使用DeepSeek AI"
            )
            return

        # 提取命令和查询内容
        if is_command:
            cmd_content = msg.raw_message[3:].strip()
        else:
            # 处理@消息，提取实际内容
            cmd_content = msg.raw_message.split("]", 1)[-1].strip()
            if not cmd_content:
                await self.api.post_group_msg(
                    msg.group_id, text="请在@我之后输入您的问题"
                )
                return

        # 处理记忆模式切换命令
        if cmd_content == "memory on":
            self.memory_enabled[str(msg.user_id)] = True
            await self.api.post_group_msg(
                msg.group_id, text="✅ 已开启记忆模式，我会记住我们的对话"
            )
            return
        elif cmd_content == "memory off":
            self.memory_enabled[str(msg.user_id)] = False
            await self.api.post_group_msg(
                msg.group_id, text="❌ 已关闭记忆模式，我不会记住我们的对话"
            )
            return
        elif cmd_content == "memory clear":
            self.clear_history(msg.user_id)
            await self.api.post_group_msg(msg.group_id, text="🧹 已清除您的对话历史")
            return
        elif cmd_content == "memory status":
            is_memory_on = self.memory_enabled.get(str(msg.user_id), False)
            history_count = len(self.get_user_history(msg.user_id))
            full_history_count = len(
                self.conversation_history.get(str(msg.user_id), [])
            )
            status = "开启" if is_memory_on else "关闭"
            await self.api.post_group_msg(
                msg.group_id,
                text=f"📊 记忆模式状态: {status}\n📝 当前会话消息数: {history_count}/{full_history_count}",
            )
            return

        # 提取用户问题
        query = cmd_content
        if not query:
            await self.api.post_group_msg(msg.group_id, text="请输入您的问题")
            return

        # 构建消息列表
        messages = []

        # 如果启用了记忆模式，添加历史消息
        if self.memory_enabled.get(str(msg.user_id), False):
            history = self.get_user_history(msg.user_id)
            if history:
                messages.extend(history)

        # 添加当前用户提问
        messages.append({"role": "user", "content": query})

        # 调用API
        response = await self.call_deepseek_api(messages)

        if "error" in response:
            await self.api.post_group_msg(
                msg.group_id, text=f"❌ 调用失败: {response['error']}"
            )
        else:
            try:
                answer = response["choices"][0]["message"]["content"]

                # 如果启用了记忆模式，保存对话历史
                if self.memory_enabled.get(str(msg.user_id), False):
                    self.add_to_history(msg.user_id, "user", query)
                    self.add_to_history(msg.user_id, "assistant", answer)

                # 发送响应，使用markdown格式
                await self.api.post_group_msg(msg.group_id, text=answer)
            except (KeyError, IndexError) as e:
                await self.api.post_group_msg(
                    msg.group_id, text=f"⚠️ 解析响应时出错: {str(e)}"
                )

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息事件"""
        # 判断是否为ds命令
        is_command = msg.raw_message.startswith("ds ")

        if not is_command:
            return

        # 检查用户权限
        if not self.is_user_authorized(msg.user_id):
            await self.api.post_private_msg(
                msg.user_id, text="🚫 您没有权限使用DeepSeek AI"
            )
            return

        # 提取命令和查询内容
        cmd_content = msg.raw_message[3:].strip()

        # 处理记忆模式切换命令
        if cmd_content == "memory on":
            self.memory_enabled[str(msg.user_id)] = True
            await self.api.post_private_msg(
                msg.user_id, text="✅ 已开启记忆模式，我会记住我们的对话"
            )
            return
        elif cmd_content == "memory off":
            self.memory_enabled[str(msg.user_id)] = False
            await self.api.post_private_msg(
                msg.user_id, text="❌ 已关闭记忆模式，我不会记住我们的对话"
            )
            return
        elif cmd_content == "memory clear":
            self.clear_history(msg.user_id)
            await self.api.post_private_msg(msg.user_id, text="🧹 已清除您的对话历史")
            return
        elif cmd_content == "memory status":
            is_memory_on = self.memory_enabled.get(str(msg.user_id), False)
            history_count = len(self.get_user_history(msg.user_id))
            full_history_count = len(
                self.conversation_history.get(str(msg.user_id), [])
            )
            status = "开启" if is_memory_on else "关闭"
            await self.api.post_private_msg(
                msg.user_id,
                text=f"📊 记忆模式状态: {status}\n📝 当前会话消息数: {history_count}/{full_history_count}",
            )
            return

        # 提取用户问题
        query = cmd_content
        if not query:
            await self.api.post_private_msg(msg.user_id, text="请输入您的问题")
            return

        # 构建消息列表
        messages = []

        # 如果启用了记忆模式，添加历史消息
        if self.memory_enabled.get(str(msg.user_id), False):
            history = self.get_user_history(msg.user_id)
            if history:
                messages.extend(history)

        # 添加当前用户提问
        messages.append({"role": "user", "content": query})

        # 调用API
        response = await self.call_deepseek_api(messages)

        if "error" in response:
            await self.api.post_private_msg(
                msg.user_id, text=f"❌ 调用失败: {response['error']}"
            )
        else:
            try:
                answer = response["choices"][0]["message"]["content"]

                # 如果启用了记忆模式，保存对话历史
                if self.memory_enabled.get(str(msg.user_id), False):
                    self.add_to_history(msg.user_id, "user", query)
                    self.add_to_history(msg.user_id, "assistant", answer)

                # 发送响应，使用markdown格式
                await self.api.post_private_msg(msg.user_id, text=answer)
            except (KeyError, IndexError) as e:
                await self.api.post_private_msg(
                    msg.user_id, text=f"⚠️ 解析响应时出错: {str(e)}"
                )
