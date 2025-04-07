import asyncio
import inspect
import time
from datetime import datetime, timedelta
from typing import Callable, Any, List, Dict, Optional


class CronParser:
    """Cron表达式解析器类"""

    @staticmethod
    def parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """
        解析cron表达式中的单个字段

        Args:
            field: cron表达式字段
            min_val: 允许的最小值
            max_val: 允许的最大值

        Returns:
            解析后的值列表
        """
        if field == "*":
            return list(range(min_val, max_val + 1))

        values = []

        # 处理逗号分隔的列表
        for part in field.split(","):
            # 处理范围表达式 (例如: 1-5)
            if "-" in part:
                start, end = map(int, part.split("-"))
                if start <= end:
                    values.extend(range(start, end + 1))
                else:  # 处理跨边界情况 (例如: 22-3)
                    values.extend(range(start, max_val + 1))
                    values.extend(range(min_val, end + 1))
            # 处理步长表达式 (例如: */5)
            elif "/" in part and part.startswith("*/"):
                step = int(part.split("/")[1])
                values.extend(range(min_val, max_val + 1, step))
            # 处理固定值
            else:
                values.append(int(part))

        return sorted(list(set(values)))  # 去重并排序

    @staticmethod
    def parse_cron_expression(cron_expr: str) -> Dict[str, List[int]]:
        """
        解析完整的cron表达式

        Args:
            cron_expr: cron表达式 (分 时 日 月 周)

        Returns:
            包含各字段解析结果的字典
        """
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("无效的cron表达式，格式应为: '分 时 日 月 周'")

        minutes, hours, days, months, weekdays = parts

        return {
            "minutes": CronParser.parse_field(minutes, 0, 59),
            "hours": CronParser.parse_field(hours, 0, 23),
            "days": CronParser.parse_field(days, 1, 31),
            "months": CronParser.parse_field(months, 1, 12),
            "weekdays": CronParser.parse_field(weekdays, 0, 6),
        }


def _calculate_next_run(cron_expr: str, now: datetime) -> datetime:
    """
    计算下一次执行时间

    Args:
        cron_expr: cron表达式
        now: 当前时间

    Returns:
        下一次执行时间
    """
    try:
        # 使用CronParser解析表达式
        cron_fields = CronParser.parse_cron_expression(cron_expr)

        # 复制当前时间为起点
        next_run = now.replace(second=0, microsecond=0)

        # 增加1分钟作为搜索起点（避免立即执行）
        if next_run.minute == now.minute:
            next_run += timedelta(minutes=1)

        # 最多循环1500次（大约可搜索一年时间）避免死循环
        for _ in range(1500):
            minutes = cron_fields["minutes"]
            hours = cron_fields["hours"]
            days = cron_fields["days"]
            months = cron_fields["months"]
            weekdays = cron_fields["weekdays"]

            # 检查月份
            if next_run.month not in months:
                # 跳到下个有效月的1号
                next_valid_month = next(
                    (m for m in months if m > next_run.month), months[0]
                )
                if next_valid_month <= next_run.month:
                    next_run = next_run.replace(
                        year=next_run.year + 1,
                        month=next_valid_month,
                        day=1,
                        hour=0,
                        minute=0,
                    )
                else:
                    next_run = next_run.replace(
                        month=next_valid_month, day=1, hour=0, minute=0
                    )
                continue

            # 检查日期（考虑月份天数和星期几）
            max_day = [
                31,
                (
                    29
                    if next_run.year % 4 == 0
                       and (next_run.year % 100 != 0 or next_run.year % 400 == 0)
                    else 28
                ),
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
            ][next_run.month - 1]
            valid_days = [d for d in days if d <= max_day]

            # 检查星期几约束
            day_matches = next_run.day in valid_days
            weekday_matches = next_run.weekday() in weekdays

            # 如果星期几字段是"*"，只检查日期；否则两者必须至少满足一个
            weekday_constraint = weekdays == list(range(7))

            if not (
                    (weekday_constraint and day_matches)
                    or (not weekday_constraint and (day_matches or weekday_matches))
            ):
                # 前进到下一天
                next_run = (next_run + timedelta(days=1)).replace(hour=0, minute=0)
                continue

            # 检查小时
            if next_run.hour not in hours:
                # 找到当天下一个有效小时
                next_valid_hour = next((h for h in hours if h > next_run.hour), None)
                if next_valid_hour is not None:
                    next_run = next_run.replace(hour=next_valid_hour, minute=0)
                else:
                    # 没有更多有效小时，前进到下一天
                    next_run = (next_run + timedelta(days=1)).replace(
                        hour=hours[0], minute=0
                    )
                continue

            # 检查分钟
            if next_run.minute not in minutes:
                # 找到当前小时的下一个有效分钟
                next_valid_minute = next(
                    (m for m in minutes if m > next_run.minute), None
                )
                if next_valid_minute is not None:
                    next_run = next_run.replace(minute=next_valid_minute)
                else:
                    # 当前小时没有更多有效分钟，前进到下一个有效小时
                    next_valid_hour = next(
                        (h for h in hours if h > next_run.hour), None
                    )
                    if next_valid_hour is not None:
                        next_run = next_run.replace(
                            hour=next_valid_hour, minute=minutes[0]
                        )
                    else:
                        # 没有更多有效小时，前进到下一天
                        next_run = (next_run + timedelta(days=1)).replace(
                            hour=hours[0], minute=minutes[0]
                        )
                continue

            # 所有条件都匹配，找到了下一个执行时间
            return next_run

        # 如果超过循环限制仍未找到有效时间
        raise ValueError("无法在合理时间范围内找到下一个执行时间")

    except Exception as e:
        print(f"计算下一次执行时间出错: {e}")
        # 默认1分钟后执行
        return now.replace(minute=(now.minute + 1) % 60, second=0, microsecond=0)


class Task:
    """任务类，用于存储和管理单个定时任务"""

    def __init__(self, func: Callable, task_id: str = None):
        """
        初始化任务

        Args:
            func: 任务函数
            task_id: 任务ID，如果不提供则自动生成
        """
        self.func = func
        self.task_id = task_id or f"task_{id(self)}"
        self.is_running = False
        self.last_run = None
        self.next_run = None
        self.task_object = None
        self._cancelled = False

    async def execute(self):
        """执行任务"""
        self.is_running = True
        self.last_run = datetime.now()

        try:
            # 检查函数是否是协程函数
            if inspect.iscoroutinefunction(self.func):
                return await self.func()
            else:
                # 如果是同步函数，直接调用
                return self.func()
        except Exception as e:
            print(f"任务 {self.task_id} 执行出错: {e}")
            return None
        finally:
            self.is_running = False

    def cancel(self):
        """取消任务"""
        self._cancelled = True
        if self.task_object and not self.task_object.done():
            self.task_object.cancel()

    @property
    def cancelled(self):
        """任务是否已取消"""
        return self._cancelled


async def _run_once_at_time_task(task: Task, run_time: datetime):
    """
    在指定时间执行一次任务

    Args:
        task: 任务对象
        run_time: 运行时间
    """
    now = datetime.now()
    task.next_run = run_time

    # 如果指定时间已过，直接返回
    if run_time < now:
        print(f"任务 {task.task_id} 的执行时间 {run_time} 已过")
        return

    # 计算等待时间
    wait_seconds = (run_time - now).total_seconds()

    # 等待到执行时间
    await asyncio.sleep(wait_seconds)

    # 检查任务是否被取消
    if not task.cancelled:
        await task.execute()


class Scheduler:
    """增强的任务调度器"""

    def __init__(self):
        """初始化调度器"""
        self._tasks = {}  # 使用字典存储任务，便于按ID查找
        self._running = True
        self._main_task = None

    async def _run_interval_task(self, task: Task, interval: int):
        """
        以固定间隔运行任务

        Args:
            task: 任务对象
            interval: 间隔时间（秒）
        """
        while self._running and not task.cancelled:
            start_time = time.time()

            await task.execute()

            # 计算下一次执行的等待时间
            execution_time = time.time() - start_time
            wait_time = max(0, int(interval - execution_time))
            task.next_run = datetime.now() + timedelta(seconds=wait_time)

            await asyncio.sleep(wait_time)

    async def _run_cron_task(self, task: Task, cron_expr: str):
        """
        按cron表达式运行任务

        Args:
            task: 任务对象
            cron_expr: cron表达式
        """
        while self._running and not task.cancelled:
            # 计算下一次执行时间
            now = datetime.now()
            next_run = _calculate_next_run(cron_expr, now)
            task.next_run = next_run

            # 计算等待时间
            wait_seconds = (next_run - now).total_seconds()
            if wait_seconds < 0:
                wait_seconds = 0

            # 等待到下一次执行时间
            await asyncio.sleep(wait_seconds)

            # 再次检查任务是否被取消
            if task.cancelled:
                break

            # 执行任务
            await task.execute()

    def add_task(self, func: Callable, interval: int, task_id: str = None) -> str:
        """
        添加一个需要定时执行的任务

        Args:
            func: 任务函数（同步或异步）
            interval: 时间间隔（秒）
            task_id: 可选的任务ID

        Returns:
            任务ID
        """
        task = Task(func, task_id)
        task_coroutine = self._run_interval_task(task, interval)
        task.task_object = asyncio.create_task(task_coroutine)
        self._tasks[task.task_id] = task
        return task.task_id

    def add_cron_task(self, func: Callable, cron_expr: str, task_id: str = None) -> str:
        """
        添加一个基于cron表达式的定时任务

        Args:
            func: 任务函数（同步或异步）
            cron_expr: cron表达式，格式为"分 时 日 月 周"
            task_id: 可选的任务ID

        Returns:
            任务ID
        """
        task = Task(func, task_id)
        task_coroutine = self._run_cron_task(task, cron_expr)
        task.task_object = asyncio.create_task(task_coroutine)
        self._tasks[task.task_id] = task
        return task.task_id

    def add_once_task(
            self, func: Callable, run_at: datetime, task_id: str = None
    ) -> str:
        """
        添加一个在指定时间只执行一次的任务

        Args:
            func: 任务函数（同步或异步）
            run_at: 执行时间
            task_id: 可选的任务ID

        Returns:
            任务ID
        """
        task = Task(func, task_id)
        task_coroutine = _run_once_at_time_task(task, run_at)
        task.task_object = asyncio.create_task(task_coroutine)
        self._tasks[task.task_id] = task
        return task.task_id

    def add_random_minute_task(
            self,
            func: Callable,
            start_minute: int,
            end_minute: int,
            hours: str = "*",
            task_id: str = None,
    ) -> str:
        """
        添加一个在指定分钟范围内随机执行的定时任务

        Args:
            func: 任务函数（同步或异步）
            start_minute: 开始分钟（包含）
            end_minute: 结束分钟（包含）
            hours: 小时表达式，默认为"*"（每小时）
            task_id: 可选的任务ID

        Returns:
            任务ID
        """
        cron_expr = f"{start_minute}-{end_minute} {hours} * * *"
        return self.add_cron_task(func, cron_expr, task_id)

    def cancel_task(self, task_id: str) -> bool:
        """
        取消指定任务

        Args:
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.cancel()
            return True
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取指定任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象，如不存在则返回None
        """
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> Dict[str, Task]:
        """
        获取所有任务

        Returns:
            任务字典
        """
        return self._tasks.copy()

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字典
        """
        task = self.get_task(task_id)
        if not task:
            return {"error": "任务不存在"}

        return {
            "task_id": task.task_id,
            "is_running": task.is_running,
            "last_run": task.last_run,
            "next_run": task.next_run,
            "cancelled": task.cancelled,
        }

    def stop_all_tasks(self):
        """停止所有任务"""
        self._running = False
        for task_id in list(self._tasks.keys()):
            self.cancel_task(task_id)

    async def start(self):
        """启动调度器"""
        self._running = True
        # 创建一个永不完成的任务，确保调度器一直运行
        self._main_task = asyncio.create_task(self._keep_alive())

    async def _keep_alive(self):
        """保持调度器运行"""
        while self._running:
            await asyncio.sleep(1)

    def stop(self):
        """停止调度器"""
        self.stop_all_tasks()
        if self._main_task and not self._main_task.done():
            self._main_task.cancel()


# 创建全局调度器实例
scheduler = Scheduler()
