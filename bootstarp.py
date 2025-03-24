from ncatbot.core import BotClient
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.config import config
from ncatbot.utils.logger import get_log
import tomllib

_log = get_log()

# TODO: 测试完成删除配置
with open("config.toml", "rb") as f:
    cfg = tomllib.load(f)
    config.set_bot_uin(cfg["bot_uin"])
    config.set_ws_uri(cfg["ws_uri"])
    config.set_token(cfg["token"])

bot = BotClient()


@bot.group_event()
async def on_group_message(msg: GroupMessage):
    _log.info(msg)
    if msg.raw_message == "测试":
        await msg.reply(text="NcatBot 测试成功喵~")


@bot.private_event()
async def on_private_message(msg: PrivateMessage):
    _log.info(msg)
    if msg.raw_message == "测试":
        await bot.api.post_private_msg(msg.user_id, text="NcatBot 测试成功喵~")


if __name__ == "__main__":
    bot.run()
