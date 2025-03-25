import signal
import tomllib

from ncatbot.core import BotClient
from ncatbot.utils.config import config

from scheduler import scheduler  # 导入调度器

with open("config.toml", "rb") as f:
    cfg = tomllib.load(f)
    config.set_bot_uin(cfg["bot_uin"])
    config.set_ws_uri(cfg["ws_uri"])
    config.set_token(cfg["token"])

bot = BotClient()


# 示例：如何添加一个定时任务
async def example_task():
    print("执行定时任务...")


# 注册信号处理程序，确保退出时清理任务
def handle_shutdown(sig, frame):
    print("正在关闭定时任务...")
    scheduler.stop_all_tasks()
    # 让程序自然退出
    exit(0)


if __name__ == "__main__":
    # 注册信号处理
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # 启动机器人
    try:
        bot.run()
    except KeyboardInterrupt:
        handle_shutdown(None, None)
