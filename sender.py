import http.client
import json
import logging
from typing import Dict, Any, Union


def build_text_message(text: str) -> Dict[str, Any]:
    """构建文本消息

    Args:
        text: 文本内容

    Returns:
        文本消息字典
    """
    return {"type": "text", "data": {"text": text}}


def build_custom_music_card(
        url: str, audio: str, title: str, image: str, singer: str
) -> Dict[str, Any]:
    """构建自定义音乐卡片

    Args:
        url: 音乐页面链接
        audio: 音频文件链接
        title: 歌曲标题
        image: 封面图片链接
        singer: 歌手名称

    Returns:
        自定义音乐卡片字典
    """
    return {
        "type": "music",
        "data": {
            "type": "custom",
            "url": url,
            "audio": audio,
            "title": title,
            "image": image,
            "singer": singer,
        },
    }


class MessageSender:
    """用于发送HTTP请求的类，支持发送消息到指定API"""

    def __init__(self, host: str = "127.0.0.1", port: int = 3000):
        """初始化消息发送器

        Args:
            host: API主机地址
            port: API端口
        """
        self.host = host
        self.port = port
        self.logger = logging.getLogger("MessageSender")

    async def send_group_msg(
            self, group_id: Union[int, str], message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送群消息

        Args:
            group_id: 群ID
            message: 消息内容字典，作为请求payload直接发送

        Returns:
            API响应结果
        """
        try:
            conn = http.client.HTTPConnection(self.host, self.port)
            payload = json.dumps(message)
            headers = {"Content-Type": "application/json"}
            conn.request("POST", "/send_group_msg", payload, headers)
            res = conn.getresponse()
            data = res.read()
            response = data.decode("utf-8")
            self.logger.debug(f"发送群消息成功: {response}")
            return {"status": "success", "response": response}
        except Exception as e:
            self.logger.error(f"发送群消息失败: {str(e)}")
            return {"status": "failed", "message": f"发送请求错误: {str(e)}"}

    async def send_private_msg(
            self, user_id: Union[int, str], message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送私聊消息

        Args:
            user_id: 用户ID
            message: 消息内容字典，作为请求payload直接发送

        Returns:
            API响应结果
        """
        try:
            conn = http.client.HTTPConnection(self.host, self.port)
            payload = json.dumps(message)
            headers = {"Content-Type": "application/json"}
            conn.request("POST", "/send_private_msg", payload, headers)
            res = conn.getresponse()
            data = res.read()
            response = data.decode("utf-8")
            self.logger.debug(f"发送私聊消息成功: {response}")
            return {"status": "success", "response": response}
        except Exception as e:
            self.logger.error(f"发送私聊消息失败: {str(e)}")
            return {"status": "failed", "message": f"发送请求错误: {str(e)}"}
