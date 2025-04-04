import signal
import tomllib
import os

from ncatbot.core import BotClient
from ncatbot.utils.config import config

from scheduler import scheduler  # 导入调度器

# 读取主配置文件
with open("config.toml", "rb") as f:
    cfg = tomllib.load(f)
    config.set_bot_uin(cfg["bot_uin"])
    config.set_ws_uri(cfg["ws_uri"])
    config.set_token(cfg["token"])

# 输出忽略目录信息（仅用于日志记录，不进行设置）
ignored_dirs = []

# 读取框架配置文件
try:
    if os.path.exists("ncatbot.toml"):
        with open("ncatbot.toml", "rb") as f:
            ncatbot_cfg = tomllib.load(f)

            # 从配置文件中读取忽略目录
            if (
                "ncatbot" in ncatbot_cfg
                and "ignored_directories" in ncatbot_cfg["ncatbot"]
            ):
                ignored_dirs.extend(ncatbot_cfg["ncatbot"]["ignored_directories"])
except Exception as e:
    print(f"读取框架配置文件出错: {e}")

# 读取 .ncatbotignore 文件
try:
    if os.path.exists(".ncatbotignore"):
        with open(".ncatbotignore", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignored_dirs.append(line)
except Exception as e:
    print(f"读取 .ncatbotignore 文件出错: {e}")

# 去重并输出日志（移除无效的设置代码）
if ignored_dirs:
    ignored_dirs = list(set(ignored_dirs))
    print(
        f"注意: 以下目录不会被自动加载为插件（通过框架机制）: {', '.join(ignored_dirs)}"
    )

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
