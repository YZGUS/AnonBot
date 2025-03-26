import datetime
import os
import random

from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

bot = CompatibleEnrollment

library_path = os.path.join(os.path.dirname(__file__), "config", "library.txt")
with open(library_path, "r", encoding="utf-8") as f:
    lines = f.readlines()


class KfcPlugin(BasePlugin):
    name = "KfcPlugin"
    version = "0.0.1"

    async def on_load(self):
        print(f"{self.name} 插件已加载")
        print(f"插件版本: {self.version}")

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        if self.is_hit(msg):
            await self.api.post_group_msg(
                msg.group_id, text=self.get_content()
            )

    def is_hit(self, message: str) -> bool:
        is_thursday = datetime.datetime.now().strftime("%A") == "Thursday"
        keywords = ["KFC", "kfc", "肯德基", "兄弟", "垃圾"]
        contains_keyword = any(keyword in message for keyword in keywords)
        return is_thursday and contains_keyword

    def get_content(self) -> str:
        try:
            if lines:
                selected_line = random.choice(lines).strip()
                return selected_line
            else:
                return "库文件为空"
        except Exception as e:
            return f"读取库文件出错: {str(e)}"

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        if self.is_hit(msg.raw_message):
            await self.api.post_private_msg(
                msg.user_id, text=self.get_content()
            )
