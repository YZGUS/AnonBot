import os
import random
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from snownlp import SnowNLP

from scheduler import scheduler

bot = CompatibleEnrollment


@dataclass
class Config:
    api_key: str
    whitelist_groups: List[int]
    whitelist_users: List[int]
    sentiment_threshold: float
    default_model: str
    temperature: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            api_key=data.get("api_key", ""),
            whitelist_groups=data.get("whitelist", {}).get("group_ids", []),
            whitelist_users=data.get("whitelist", {}).get("user_ids", []),
            sentiment_threshold=data.get("sentiment", {}).get("threshold", 0.2),
            default_model=data.get("model", {}).get("default", "deepseek-chat"),
            temperature=data.get("model", {}).get("temperature", 0.7),
        )


def analyze_sentiment(text: str) -> float:
    """分析文本情感值，返回0到1之间的值，值越低表示越消极"""
    try:
        s = SnowNLP(text)
        return s.sentiments
    except Exception as e:
        print(f"情感分析出错: {str(e)}")
        return 0.5  # 发生错误时返回中性值


async def generate_comfort_message(config: Config, text: str) -> str:
    """调用DeepSeek API生成安慰消息"""
    content = """🎯【千早爱音第一人称安慰对话生成器】🎯
请严格遵循以下结构生成符合Ano酱性格的安慰台词：

💎核心需求
「用我的方式让TA振作起来！」+「用表情符号说话」

🌟关键规则
1️⃣ 每句必须带3种符号：
   - 暖色符号😁🌟✨（表达积极情绪）
   - 冷色符号🏷💧🌧️（暗示脆弱/回忆）
   - 特效符号🔮🎸🎯（突出乐队元素）

2️⃣ 符号使用逻辑：
   [调侃开头]😈+🌈
   [回忆触发]🏷+💦
   [情感升温]🌟+🎸
   [决胜台词]✨+🎯

3️⃣ 颜色对比强化：
   █黄色符号（主情绪）
   █蓝色符号（回忆/脆弱）
   █紫色符号（关键转折）

🎨示例模板
「Ano~这里藏着哭泣小猫可不行呢😈🌈（探头）  
要是泪珠把和弦表弄湿了...🏷💧上次灯酱的歌词本差点泡汤的事还记得吗？🔮」  

「Da-Me！Da-Me！🎸立希的鼓棒敲头攻击可比眼泪痛100倍哦😖⚡（假装抱头）  
但是呢...🏷那次海外视频被恶评的时候——」  

「是某人偷偷给我塞了抹茶大福对吧？🌟🎵（眨眼）  
所以现在...轮到Ano酱当你的精神甜点师啦✨🎯（举虚拟应援棒）」  

⚙️生成要求
✅ 必须交替使用▞▞▞三色符号块分隔情感层次
✅ 关键回忆用🏷+💧符号组标记
✅ 每段结尾用🎯+✨强化决心

📌当前场景
▞窗外暴雨⛈️ + ▞倒计时48小时🕑 + ▞潮湿的排练室🌫️

当前具体场景：需要安慰表现出消极情绪的朋友。他/她发送了以下消息："{}"
请生成爱音的安慰回应，不要包含括号内的隐藏动机/剧情呼应点说明。""".format(
        text
    )

    messages = [{"role": "user", "content": content}]
    return await call_deepseek_api(config, messages)


async def call_deepseek_api(
        config: Config,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = 2000,
) -> str:
    """调用DeepSeek API"""
    if not config or not config.api_key:
        return "API密钥未配置，无法生成回复"

    url = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}",
    }

    data = {
        "model": model or config.default_model,
        "messages": messages,
        "temperature": temperature or config.temperature,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response_data = response.json()

        if "choices" in response_data and len(response_data["choices"]) > 0:
            return response_data["choices"][0]["message"]["content"].strip()
        else:
            print(f"API返回异常: {response.text}")
            return "生成回复时出现错误"
    except Exception as e:
        print(f"调用DeepSeek API出错: {str(e)}")
        return f"调用API时发生错误: {str(e)}"


async def send_voice_message(group_id: int, voice_text: str) -> bool:
    """发送语音消息到群聊"""
    try:
        # 生成一个临时的语音URL，实际应用中可能需要先将文本转为语音
        # 这里使用一个随机文件名模拟
        temp_filename = f"comfort_{random.randint(10000, 99999)}.mp3"

        # 调用语音转换服务，将语音文本转换为MP3文件
        # 此处需要替换为实际的语音转换服务
        voice_url = await text_to_voice(voice_text, temp_filename)

        if not voice_url:
            return False

        # 构建消息体
        url = "/send_group_msg"
        data = {
            "group_id": str(group_id),
            "message": [{"type": "record", "data": {"file": voice_url}}],
        }

        # 发送请求
        response = requests.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok" and result.get("retcode") == 0:
                return True

        print(f"发送语音消息失败: {response.text}")
        return False

    except Exception as e:
        print(f"发送语音消息出错: {str(e)}")
        return False


async def text_to_voice(text: str, filename: str) -> Optional[str]:
    """将文本转换为语音文件，返回语音文件URL"""
    # 此处应调用实际的语音合成服务
    # 例如百度、阿里、腾讯等提供的TTS服务
    # 返回生成的语音文件URL

    # 模拟实现，实际应用中需要替换为真实的语音合成服务
    try:
        # 示例：调用本地TTS服务或在线TTS API
        voice_url = f"http://example.com/voices/{filename}"

        # 实际应用中，可能需要将生成的语音文件上传到可访问的位置
        # 然后返回URL

        return voice_url
    except Exception as e:
        print(f"生成语音出错: {str(e)}")
        return None


class EmotionalSupportPlugin(BasePlugin):
    name = "EmotionalSupportPlugin"
    version = "0.0.1"

    config = None
    config_path = None
    config_last_modified = 0
    data_dir = None

    async def on_load(self):
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")

        self.config_path = Path(__file__).parent / "config" / "config.toml"
        self.data_dir = Path(__file__).parent / "data"

        os.makedirs(self.data_dir, exist_ok=True)
        self.load_config()
        scheduler.add_task(self.check_config_update, 30)

    def load_config(self) -> None:
        try:
            if self.config_path.exists():
                with open(self.config_path, "rb") as f:
                    config_data = tomllib.load(f)
                    self.config = Config.from_dict(config_data)
                self.config_last_modified = os.path.getmtime(self.config_path)
                print(f"成功加载 {self.name} 配置")
            else:
                print(f"警告: {self.name} 配置文件不存在: {self.config_path}")
                self.config = Config("", [], [], 0.2, "deepseek-chat", 0.7)
        except Exception as e:
            print(f"加载 {self.name} 配置出错: {str(e)}")
            self.config = Config("", [], [], 0.2, "deepseek-chat", 0.7)

    def check_config_update(self) -> bool:
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
        if not self.config:
            return False

        if user_id in self.config.whitelist_users:
            return True

        if group_id and group_id in self.config.whitelist_groups:
            return True

        return False

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        try:
            # 只处理文本消息
            if not msg.raw_message or msg.message_type != "group":
                return

            group_id = msg.group_id
            user_id = msg.sender.user_id

            # 检查是否在白名单中
            if not self.is_user_authorized(user_id, group_id):
                return

            # 分析消息情感
            sentiment_value = analyze_sentiment(msg.raw_message)

            # 如果情感值低于阈值，生成安慰消息
            if sentiment_value < self.config.sentiment_threshold:
                print(f"检测到消极情绪，情感值: {sentiment_value}")

                # 生成安慰文本
                comfort_text = await generate_comfort_message(
                    self.config, msg.raw_message
                )

                if comfort_text:
                    # 直接回复文本消息
                    await msg.reply(text=comfort_text)
                    print(f"成功发送安慰消息到群 {group_id}")
        except Exception as e:
            print(f"处理群消息出错: {str(e)}")

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        try:
            # 只处理文本消息
            if not msg.raw_message or msg.message_type != "private":
                return

            user_id = msg.sender.user_id

            # 检查是否在白名单中
            if not self.is_user_authorized(user_id):
                return

            # 分析消息情感
            sentiment_value = analyze_sentiment(msg.raw_message)

            # 如果情感值低于阈值，生成安慰消息
            if sentiment_value < self.config.sentiment_threshold:
                print(f"检测到消极情绪，情感值: {sentiment_value}")

                # 生成安慰文本
                comfort_text = await generate_comfort_message(
                    self.config, msg.raw_message
                )

                if comfort_text:
                    # 私聊直接回复文本消息
                    await msg.reply(text=comfort_text)
                    print(f"成功发送安慰消息给用户 {user_id}")
        except Exception as e:
            print(f"处理私聊消息出错: {str(e)}")
