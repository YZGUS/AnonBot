import asyncio
import inspect
import random
import time
from datetime import datetime
from typing import Callable, Any


def _calculate_next_run(cron_expr: str, now: datetime) -> datetime:
    """
    计算下一次执行时间
    :param cron_expr: cron表达式
    :param now: 当前时间
    :return: 下一次执行时间
    """
    # 简单实现：解析cron表达式
    try:
        minutes_str, hours_str, days_str, months_str, weekdays_str = (
            cron_expr.split()
        )

        # 处理小时表达式
        if hours_str == "*":
            # 任意小时，从当前开始
            target_hours = list(range(24))
        elif "-" in hours_str:
            # 小时范围，如 "8-17"
            start, end = map(int, hours_str.split("-"))
            if start <= end:
                target_hours = list(range(start, end + 1))
            else:  # 跨午夜，如 "22-3"
                target_hours = list(range(start, 24)) + list(range(0, end + 1))
        elif "," in hours_str:
            # 小时列表，如 "9,12,15,18"
            target_hours = [int(h) for h in hours_str.split(",")]
        else:
            # 单一小时，如 "8"
            target_hours = [int(hours_str)]

        # 处理分钟表达式
        if minutes_str == "*":
            # 每分钟执行
            if now.hour in target_hours:
                next_minute = (now.minute + 1) % 60
                if next_minute > now.minute:
                    next_hour = now.hour
                else:
                    # 下一个有效小时
                    hour_candidates = [h for h in target_hours if h > now.hour]
                    if hour_candidates:
                        next_hour = min(hour_candidates)
                    else:
                        # 跨天，取第一个小时
                        next_hour = target_hours[0]
                        next_run = now.replace(
                            day=now.day + 1,
                            hour=next_hour,
                            minute=0,
                            second=0,
                            microsecond=0,
                        )
                        return next_run
            else:
                # 不在目标小时内，找下一个目标小时
                hour_candidates = [h for h in target_hours if h > now.hour]
                if hour_candidates:
                    next_hour = min(hour_candidates)
                    next_minute = 0
                else:
                    # 跨天，取第一个小时
                    next_hour = target_hours[0]
                    next_minute = 0
                    next_run = now.replace(
                        day=now.day + 1,
                        hour=next_hour,
                        minute=next_minute,
                        second=0,
                        microsecond=0,
                    )
                    return next_run
        elif "-" in minutes_str:
            # 分钟范围，如 "0-5"
            start, end = map(int, minutes_str.split("-"))
            # 在范围内随机选择
            target_minutes = list(range(start, end + 1))

            # 判断当前时间是否在目标小时和分钟范围内
            if now.hour in target_hours and any(
                    m > now.minute for m in target_minutes
            ):
                # 当前小时有效，选择大于当前分钟的随机分钟
                valid_minutes = [m for m in target_minutes if m > now.minute]
                next_minute = random.choice(valid_minutes)
                next_hour = now.hour
            elif any(h > now.hour for h in target_hours):
                # 有大于当前小时的目标小时
                next_hour = min([h for h in target_hours if h > now.hour])
                next_minute = random.choice(target_minutes)
            else:
                # 需要跨天
                next_hour = target_hours[0]
                next_minute = random.choice(target_minutes)
                next_run = now.replace(
                    day=now.day + 1,
                    hour=next_hour,
                    minute=next_minute,
                    second=0,
                    microsecond=0,
                )
                return next_run
        elif "," in minutes_str:
            # 分钟列表，如 "0,15,30,45"
            target_minutes = [int(m) for m in minutes_str.split(",")]

            # 在当前小时中寻找下一个有效分钟
            if now.hour in target_hours:
                valid_minutes = [m for m in target_minutes if m > now.minute]
                if valid_minutes:
                    next_minute = min(valid_minutes)
                    next_hour = now.hour
                else:
                    # 当前小时没有更多有效分钟，寻找下一个有效小时
                    hour_candidates = [h for h in target_hours if h > now.hour]
                    if hour_candidates:
                        next_hour = min(hour_candidates)
                        next_minute = min(target_minutes)
                    else:
                        # 需要跨天
                        next_hour = target_hours[0]
                        next_minute = min(target_minutes)
                        next_run = now.replace(
                            day=now.day + 1,
                            hour=next_hour,
                            minute=next_minute,
                            second=0,
                            microsecond=0,
                        )
                        return next_run
            else:
                # 不在目标小时内，找下一个目标小时
                hour_candidates = [h for h in target_hours if h > now.hour]
                if hour_candidates:
                    next_hour = min(hour_candidates)
                    next_minute = min(target_minutes)
                else:
                    # 需要跨天
                    next_hour = target_hours[0]
                    next_minute = min(target_minutes)
                    next_run = now.replace(
                        day=now.day + 1,
                        hour=next_hour,
                        minute=next_minute,
                        second=0,
                        microsecond=0,
                    )
                    return next_run
        else:
            # 单一分钟，如 "30"
            next_minute = int(minutes_str)

            # 检查当前时间
            if now.hour in target_hours and next_minute > now.minute:
                # 当前小时有效且分钟未过
                next_hour = now.hour
            elif any(h > now.hour for h in target_hours):
                # 今天稍后有有效小时
                next_hour = min([h for h in target_hours if h > now.hour])
            else:
                # 需要跨天
                next_hour = target_hours[0]
                next_run = now.replace(
                    day=now.day + 1,
                    hour=next_hour,
                    minute=next_minute,
                    second=0,
                    microsecond=0,
                )
                return next_run

        # 构建下一次执行时间
        next_run = now.replace(
            hour=next_hour, minute=next_minute, second=0, microsecond=0
        )

        # 最终检查，确保时间在未来
        if next_run <= now:
            # 如果计算的时间仍在过去，则加一天
            next_run = next_run.replace(day=now.day + 1)

        return next_run
    except Exception as e:
        print(f"计算下一次执行时间出错: {e}")
        # 默认1分钟后执行
        return now.replace(minute=(now.minute + 1) % 60, second=0, microsecond=0)


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

    async def schedule_cron_task(self, func: Callable[..., Any], cron_expr: str):
        """
        调度一个基于cron表达式的任务
        :param func: 任务函数（同步或异步）
        :param cron_expr: cron表达式，格式为"分 时 日 月 周"
        """
        # 解析cron表达式
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("无效的cron表达式，格式应为: '分 时 日 月 周'")

        while self._running:
            # 计算下一次执行时间
            now = datetime.now()
            next_run = _calculate_next_run(cron_expr, now)

            # 计算等待时间
            wait_seconds = (next_run - now).total_seconds()
            if wait_seconds < 0:
                wait_seconds = 0

            # 等待到下一次执行时间
            await asyncio.sleep(wait_seconds)

            # 执行任务
            try:
                # 检查函数是否是协程函数
                if inspect.iscoroutinefunction(func):
                    await func()
                else:
                    # 如果是同步函数，直接调用
                    func()
            except Exception as e:
                print(f"定时任务执行出错: {e}")

    def add_task(self, func: Callable, interval: int):
        """
        添加一个需要定时执行的任务
        :param func: 任务函数（同步或异步）
        :param interval: 时间间隔（秒）
        """
        task = asyncio.create_task(self.schedule_task(func, interval))
        self._tasks.append(task)
        return task

    def add_cron_task(self, func: Callable, cron_expr: str):
        """
        添加一个基于cron表达式的定时任务
        :param func: 任务函数（同步或异步）
        :param cron_expr: cron表达式，格式为"分 时 日 月 周"
        """
        task = asyncio.create_task(self.schedule_cron_task(func, cron_expr))
        self._tasks.append(task)
        return task

    def add_random_minute_task(
            self, func: Callable, start_minute: int, end_minute: int, hours: str = "*"
    ):
        """
        添加一个在指定分钟范围内随机执行的定时任务
        :param func: 任务函数（同步或异步）
        :param start_minute: 开始分钟（包含）
        :param end_minute: 结束分钟（包含）
        :param hours: 小时表达式，默认为"*"（每小时）
        """
        cron_expr = f"{start_minute}-{end_minute} {hours} * * *"
        return self.add_cron_task(func, cron_expr)

    def stop_all_tasks(self):
        """停止所有任务"""
        self._running = False
        for task in self._tasks:
            if not task.done():
                task.cancel()


scheduler = Scheduler()
