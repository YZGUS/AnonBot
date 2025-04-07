"""
utilities 包，提供各种工具函数和类
"""

from .scheduler import Scheduler, scheduler, CronParser, Task  # 全局调度器实例

from .sender import MessageSender, build_text_message, build_custom_music_card

from .stock import StockData, StockDataError, stock_data  # 股票数据模块

__all__ = [
    # 调度器
    "Scheduler",
    "scheduler",
    "CronParser",
    "Task",
    # 消息发送
    "MessageSender",
    "build_text_message",
    "build_custom_music_card",
    # 股票数据
    "StockData",
    "StockDataError",
    "stock_data",
]
