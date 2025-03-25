import asyncio
import time
import inspect
from typing import Callable, Coroutine, Any


class Scheduler:
    def __init__(self):
        self._tasks = []
        self._running = True

    async def schedule_task(self, func: Callable[..., Any], interval: int):
        """
        调度一个任务
        :param func: 任务函数（同步或异步）
        :param interval: 时间间隔（秒）
        """
        while self._running:
            start_time = time.time()
            try:
                # 检查函数是否是协程函数
                if inspect.iscoroutinefunction(func):
                    await func()
                else:
                    # 如果是同步函数，直接调用
                    func()
            except Exception as e:
                print(f"任务执行出错: {e}")

            # 计算下一次执行的等待时间
            execution_time = time.time() - start_time
            wait_time = max(0, interval - execution_time)
            await asyncio.sleep(wait_time)

    def add_task(self, func: Callable, interval: int):
        """
        添加一个需要定时执行的任务
        :param func: 任务函数（同步或异步）
        :param interval: 时间间隔（秒）
        """
        task = asyncio.create_task(self.schedule_task(func, interval))
        self._tasks.append(task)
        return task

    def stop_all_tasks(self):
        """停止所有任务"""
        self._running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()


scheduler = Scheduler()
