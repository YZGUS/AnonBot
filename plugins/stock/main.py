import asyncio
import datetime
import logging
import os
import time  # 新增导入 time 用于生成文件名
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Union  # Added Union

import akshare as ak
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd  # Ensure pandas is imported
from ncatbot.core.message import GroupMessage
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from tabulate import tabulate  # For formatting tables

matplotlib.use("Agg")  # Use Agg backend for non-GUI environments
bot = CompatibleEnrollment  # 兼容回调函数注册器

# 获取 logger 实例
logger = logging.getLogger(__name__)

# Configure Matplotlib for CJK font
# Provide a list of potential CJK fonts, matplotlib will use the first one found.
plt.rcParams["font.sans-serif"] = [
    "SimHei",
    "PingFang SC",
    "Heiti SC",
    "STHeiti",
    "Microsoft YaHei",
]
plt.rcParams["axes.unicode_minus"] = False  # Handle negative signs correctly
# Verify the actually used font (optional)
# from matplotlib.font_manager import findfont, FontProperties
# font_path = findfont(FontProperties(family=plt.rcParams['font.sans-serif']))
# logger.info(f"Matplotlib is using font: {font_path}")
logger.info(
    f"Attempted to set Matplotlib font to one of: {plt.rcParams['font.sans-serif']}"
)


@dataclass
class Config:
    whitelist_groups: List[int]
    whitelist_users: List[int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(
            whitelist_groups=data.get("whitelist", {}).get("group_ids", []),
            whitelist_users=data.get("whitelist", {}).get("user_ids", []),
        )


async def generate_stock_chart(
        df: pd.DataFrame, stock_code: str, days: int = 90
) -> Optional[str]:
    """为最近 N 天的数据生成收盘价图表并保存到文件"""
    if df.empty:
        logger.warning(f"无法为 {stock_code} 生成图表：数据为空。")
        return None

    df_chart = df.tail(days).copy()
    if df_chart.empty:
        logger.warning(f"无法为 {stock_code} 生成图表：最近 {days} 天数据为空。")
        return None

    if "日期" not in df_chart.columns or "收盘" not in df_chart.columns:
        logger.error(f"无法为 {stock_code} 生成图表：缺少 '日期' 或 '收盘' 列。")
        return None

    # 定义数据目录路径
    plugin_dir = Path(__file__).parent
    data_dir = plugin_dir / "data"
    # 确保数据目录存在
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"创建数据目录失败: {data_dir}, 错误: {e}")
        return None

    # 生成文件名 (例如: 600519_chart_1678886400.png)
    timestamp = int(time.time())
    filename = f"{stock_code}_chart_{timestamp}.png"
    filepath = data_dir / filename

    fig = None  # 初始化 fig 变量
    try:
        plt.style.use("seaborn-v0_8-darkgrid")
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.plot(
            df_chart["日期"],
            df_chart["收盘"],
            marker=".",
            linestyle="-",
            linewidth=1.5,
            label="收盘价",
        )

        ax.set_title(f"{stock_code} 最近 {len(df_chart)} 交易日收盘价走势", fontsize=14)
        ax.set_xlabel("日期", fontsize=10)
        ax.set_ylabel("价格", fontsize=10)
        fig.autofmt_xdate()
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m-%d"))
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.6)

        # 保存到文件
        plt.savefig(filepath, format="png", bbox_inches="tight", dpi=100)
        plt.close(fig)  # 关闭图形释放内存

        logger.info(f"成功为 {stock_code} 生成图表并保存至: {filepath}")
        return str(filepath)  # 返回文件路径字符串
    except Exception as e:
        logger.error(f"为 {stock_code} 生成或保存图表时出错: {e}", exc_info=True)
        if fig:  # 如果 fig 已创建但出错，尝试关闭
            plt.close(fig)
        # 如果文件已部分创建，尝试删除避免残留
        if filepath.exists():
            try:
                os.remove(filepath)
            except OSError:
                logger.error(f"尝试删除失败的图表文件失败: {filepath}")
        return None


async def fetch_stock_historical_data(
        stock_code: str,
        period: str = "daily",
        start_date: str = "19700101",
        end_date: str = "20500101",
        adjust: str = "",
) -> Union[pd.DataFrame, str]:
    """
    获取股票历史数据 DataFrame 或错误信息字符串。
    """
    valid_periods = ["daily", "weekly", "monthly"]
    valid_adjusts = ["qfq", "hfq", ""]

    if period not in valid_periods:
        return f"❌ 错误：无效的周期 '{period}'。支持: {', '.join(valid_periods)}"
    if adjust not in valid_adjusts:
        return f"❌ 错误：无效的复权类型 '{adjust}'。支持: qfq (前复权), hfq (后复权), '' (不复权)"

    try:
        logger.info(
            f"正在查询历史数据: code={stock_code}, period={period}, start={start_date}, end={end_date}, adjust={adjust}"
        )
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
        )

        if df.empty:
            return f"⚠️ 未能获取股票代码 {stock_code} 在指定条件下的历史数据。"

        # Ensure '日期' is datetime for potential sorting/filtering later
        df["日期"] = pd.to_datetime(df["日期"])
        df.sort_values(by="日期", inplace=True)

        return df
    except Exception as e:
        logger.error(f"查询股票 {stock_code} 历史数据时出错: {e}")
        return f"❌ 查询股票 {stock_code} 历史数据时出错: {e}"


def format_historical_data_text(
        df: pd.DataFrame,
        stock_code: str,
        period: str,
        adjust: str,
        max_rows: int = 30,
) -> str:
    """将 DataFrame 格式化为对齐的文本表格"""
    if df.empty:
        return f"⚠️ 没有为 {stock_code} 找到历史数据来格式化。"

    # 准备显示的数据
    df_display = df.tail(max_rows).copy()  # 使用 .copy() 避免 SettingWithCopyWarning

    # 移除重复的股票代码列
    if "股票代码" in df_display.columns:
        df_display.drop(columns=["股票代码"], inplace=True)

    # 转换日期格式以便显示
    df_display["日期"] = df_display["日期"].dt.strftime("%Y-%m-%d")

    # 设置标题 - 添加图标 📈
    actual_rows = len(df_display)
    title_period = f"{period}, {adjust or '不复权'}"
    if actual_rows < len(df):
        title = f"📈 股票 {stock_code} 最近 {actual_rows} 条历史数据 ({title_period}):"
    else:
        title = f"📈 股票 {stock_code} 历史数据 ({actual_rows} 条, {title_period}):"

    # 使用 tabulate 格式化表格
    # 注意：在表头中添加图标可能会影响对齐，所以这里保持表头干净
    headers = {  # 定义更易读的中文表头
        "日期": "📅 日期",
        "开盘": "开盘价",
        "收盘": "收盘价",
        "最高": "最高价",
        "最低": "最低价",
        "成交量": "成交量(手)",
        "成交额": "成交额(元)",
        "振幅": "振幅(%)",
        "涨跌幅": "涨跌幅(%)",
        "涨跌额": "涨跌额",
        "换手率": "换手率(%)",
    }
    # 重命名列以匹配新的表头
    df_display.rename(columns=headers, inplace=True)

    table_str = tabulate(
        df_display,
        headers="keys",  # 使用列名作为表头
        tablefmt="simple",  # 改用 'simple' 格式
        showindex=False,  # 不显示 DataFrame 索引
        numalign="left",  # 强制数字左对齐
        stralign="left",  # 字符串左对齐 (默认)
        floatfmt=".2f",  # 浮点数格式
    )

    response = f"{title}\n" f"-------------------------------------\n" f"{table_str}"

    # 再次检查总长度，如果太长可能需要进一步截断或提示
    if len(response) > 2000:
        logger.warning(
            f"格式化后的历史数据响应过长 ({len(response)} chars)，可能无法完整发送。"
        )
        response += "\n(⚠️ 数据过多，可能显示不全)"  # 添加提示

    return response


async def generate_historical_data_table_image(
        df: pd.DataFrame, stock_code: str, max_rows: int = 30
) -> Optional[str]:
    """将 DataFrame 渲染为历史数据表格图片并保存。"""
    if df.empty:
        logger.warning(f"无法为 {stock_code} 生成表格图片：数据为空。")
        return None

    df_display = df.tail(max_rows).copy()

    # --- Sort by date descending (most recent first) ---
    if "日期" in df_display.columns:
        # Ensure '日期' is datetime for sorting, then sort
        try:
            df_display["日期"] = pd.to_datetime(df_display["日期"])
            df_display.sort_values(by="日期", ascending=False, inplace=True)
        except Exception as sort_e:
            logger.error(f"Sorting by date failed for {stock_code}: {sort_e}")
            # Proceed without sorting if error occurs
    else:
        logger.warning(f"Cannot sort by date for {stock_code}: '日期' column missing.")
    # --- End Sorting ---

    # 选择并重命名列以匹配截图格式
    headers_map = {
        "日期": "日期",  # 移除 emoji 简化
        "开盘": "开盘价",
        "收盘": "收盘价",
        "最高": "最高价",
        "最低": "最低价",
        "成交量": "成交量(手)",
        "成交额": "成交额(亿元)",  # 改为亿元
        "振幅": "振幅(%)",
        "涨跌幅": "涨跌幅(%)",
        "涨跌额": "涨跌额",
        "换手率": "换手率(%)",
    }
    required_cols = list(headers_map.keys())
    missing_cols = [col for col in required_cols if col not in df_display.columns]
    if missing_cols:
        logger.error(f"无法为 {stock_code} 生成表格图片：缺少列 {missing_cols}。")
        return None

    # --- 数据格式化 --- Start
    # 转换成交额单位（在重命名映射之前操作原始列名）
    if "成交额" in df_display.columns:
        df_display["成交额"] = df_display["成交额"] / 100_000_000  # Convert to 亿元

    df_display = df_display[required_cols].copy()  # 按顺序选择列，使用 .copy()
    df_display.rename(columns=headers_map, inplace=True)

    df_display["日期"] = pd.to_datetime(df_display["日期"]).dt.strftime("%Y-%m-%d")

    # 格式化浮点数列
    float_cols_format = {
        "开盘价": "{:.2f}",
        "收盘价": "{:.2f}",
        "最高价": "{:.2f}",
        "最低价": "{:.2f}",
        "成交额(亿元)": "{:.2f}",  # 亿元保留两位小数
        "振幅(%)": "{:.2f}",
        "换手率(%)": "{:.2f}",
    }
    # 特殊处理带符号的列
    signed_cols = ["涨跌幅(%)", "涨跌额"]

    for col, fmt in float_cols_format.items():
        if col in df_display.columns:
            df_display[col] = df_display[col].map(
                lambda x: fmt.format(x) if pd.notna(x) else ""
            )

    for col in signed_cols:
        if col in df_display.columns:
            df_display[col] = df_display[col].apply(
                lambda x: (
                    f"+{x:.2f}"
                    if pd.notna(x) and x > 0
                    else (
                        f"{x:.2f}"
                        if pd.notna(x) and x < 0
                        else ("0.00" if pd.notna(x) else "")
                    )
                )
            )

    if "成交量(手)" in df_display.columns:
        df_display["成交量(手)"] = df_display["成交量(手)"].map(
            lambda x: "{:,.0f}".format(x) if pd.notna(x) else ""
        )  # 带逗号的整数
    # --- 数据格式化 --- End

    plugin_dir = Path(__file__).parent
    data_dir = plugin_dir / "data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"创建数据目录失败: {data_dir}, 错误: {e}")
        return None

    timestamp = int(time.time())
    filename = f"{stock_code}_hist_table_{timestamp}.png"
    filepath = data_dir / filename

    # --- Matplotlib 绘图 --- Start
    # 增加 figsize 宽度，并根据行数调整高度
    fig, ax = plt.subplots(figsize=(16, max(5, len(df_display) * 0.45)))
    ax.axis("tight")
    ax.axis("off")

    table_data = df_display.values.tolist()
    col_labels = df_display.columns.tolist()

    # 创建表格，调整 cellLoc 和 colWidths
    the_table = plt.table(
        cellText=table_data,
        colLabels=col_labels,
        loc="center",
        cellLoc="center",  # 尝试居中对齐所有单元格
        colLoc="center",
    )

    the_table.auto_set_font_size(False)
    the_table.set_fontsize(10)
    the_table.scale(1.1, 1.6)  # 微调缩放比例

    # 尝试自动设置列宽，可能需要手动调整或更复杂的逻辑
    # the_table.auto_set_column_width(col=list(range(len(col_labels))))

    # --- 添加涨跌颜色 --- Start
    cells = the_table.get_celld()
    # 获取列索引，确保列存在
    col_indices = {name: i for i, name in enumerate(col_labels)}
    涨跌幅_idx = col_indices.get("涨跌幅(%)", -1)
    涨跌额_idx = col_indices.get("涨跌额", -1)

    for i in range(len(df_display)):
        row_idx = i + 1  # Table cell row index starts from 1 (0 is header)
        if 涨跌幅_idx != -1:
            cell = cells[(row_idx, 涨跌幅_idx)]
            text = cell.get_text().get_text()
            if text.startswith("+"):
                cell.get_text().set_color("red")
            elif text.startswith("-"):
                cell.get_text().set_color("green")

        if 涨跌额_idx != -1:
            cell = cells[(row_idx, 涨跌额_idx)]
            text = cell.get_text().get_text()
            if text.startswith("+"):
                cell.get_text().set_color("red")
            elif text.startswith("-"):
                cell.get_text().set_color("green")
    # --- 添加涨跌颜色 --- End

    title_start_date = df_display["日期"].iloc[0]
    title_end_date = df_display["日期"].iloc[-1]
    plt.title(
        f"{stock_code} 历史数据 ({title_start_date} 至 {title_end_date})",
        fontsize=16,
        pad=20,
    )

    try:
        plt.savefig(filepath, bbox_inches="tight", dpi=120)
        plt.close(fig)
        logger.info(f"成功为 {stock_code} 生成表格图片并保存至: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.error(f"为 {stock_code} 保存表格图片时出错: {e}", exc_info=True)
        if fig:
            plt.close(fig)
        if filepath.exists():
            try:
                os.remove(filepath)
            except OSError:
                logger.error(f"尝试删除失败的表格文件失败: {filepath}")
        return None
    # --- Matplotlib 绘图 --- End


async def handle_historical_command(cmd: str) -> List[Dict[str, str]]:
    """
    处理历史数据命令，获取数据、生成表格图片，并返回待发送消息列表。
    返回格式: [{'image': path}] 或 [{'text': error_msg}]
    """
    hist_parts = cmd.strip().split()
    if not hist_parts:
        return [
            {
                "text": "❌ 历史命令错误：需要提供股票代码。\n格式：历史 <代码> [周期] [开始] [结束] [复权]"
            }
        ]

    stock_code = hist_parts[0]
    period = hist_parts[1] if len(hist_parts) > 1 else "daily"
    start_date = hist_parts[2] if len(hist_parts) > 2 else "19700101"
    end_date = hist_parts[3] if len(hist_parts) > 3 else "20500101"
    adjust = hist_parts[4] if len(hist_parts) > 4 else ""

    messages_to_send = []

    # 1. 获取数据
    data_result = await fetch_stock_historical_data(
        stock_code, period, start_date, end_date, adjust
    )

    # 2. 处理结果
    if isinstance(data_result, str):  # 如果返回的是错误字符串
        messages_to_send.append({"text": data_result})
    elif isinstance(data_result, pd.DataFrame):
        # 2.1 生成表格图片
        try:
            table_image_path = await generate_historical_data_table_image(
                data_result, stock_code, max_rows=75  # 最多显示75行
            )
            if table_image_path:
                messages_to_send.append({"image": table_image_path})
            else:
                # 如果图片生成失败，尝试发送原始文本（作为后备）
                logger.warning(
                    f"未能为 {stock_code} 生成历史数据表格图片。尝试发送文本。"
                )
                try:
                    text_table = format_historical_data_text(  # 需要保留或重新实现 format_historical_data_text
                        data_result, stock_code, period, adjust, max_rows=30
                    )
                    messages_to_send.append(
                        {"text": text_table + "\n(⚠️ 图片生成失败)"}
                    )
                except Exception as fmt_e:
                    logger.error(f"生成表格图片和文本均失败: {fmt_e}")
                    messages_to_send.append(
                        {"text": "❌ 生成历史数据表格图片和文本时均出错。"}
                    )

        except Exception as e:
            logger.error(f"生成历史数据表格图片时出错: {e}", exc_info=True)
            messages_to_send.append({"text": "❌ 生成历史数据表格图片时出错。"})

    return messages_to_send


async def get_stock_realtime_data(cmd: str) -> List[Dict[str, str]]:
    """查询实时数据并返回待发送消息列表"""
    stock_code = cmd.strip().split()[0] if cmd.strip() else None
    if not stock_code:
        return [{"text": "❌ 错误：需要提供股票代码。"}]
    try:
        # 注意：之前的代码用了 stock_bid_ask_em，这里改回 stock_zh_a_spot_em
        # 因为 stock_bid_ask_em 返回的是买卖盘，字段不同
        df_realtime = ak.stock_zh_a_spot_em()
        stock_data = df_realtime[df_realtime["代码"] == stock_code]
        if stock_data.empty:
            return [{"text": f"⚠️ 未能找到股票代码 {stock_code} 的实时数据。"}]

        data = stock_data.iloc[0]
        response = (
            f"**⏱️ {data['名称']} ({stock_code}) 实时数据**\n"
            f"---------------------------\n"
            f"💰 最新: {data['最新价']:.2f} | 涨跌: {data['涨跌额']:.2f} ({data['涨跌幅']:.2f}%)\n"
            f"📈 今开: {data['今开']:.2f} | 最高: {data['最高']:.2f}\n"
            f"📉 最低: {data['最低']:.2f} | 昨收: {data['昨收']:.2f}\n"
            f"📊 成交量: {data['成交量'] / 10000:.2f} 万手\n"
            f"📊 成交额: {data['成交额'] / 100000000:.2f} 亿元\n"
            f"🔄 换手率: {data['换手率']:.2f}%\n"
            f"💹 市盈(动): {data['市盈率-动态']:.2f} | 市净率: {data['市净率']:.2f}\n"
            f"🏦 总市值: {data['总市值'] / 100000000:.2f} 亿\n"
            f"🏦 流通值: {data['流通市值'] / 100000000:.2f} 亿"
        )
        return [{"text": response}]
    except Exception as e:
        logger.error(f"查询股票 {stock_code} 实时数据时出错: {e}")
        return [{"text": f"❌ 查询股票 {stock_code} 实时数据时出错: {e}"}]


async def get_stock_news(cmd: str) -> List[Dict[str, str]]:
    """查询个股新闻并返回格式化的消息列表"""
    stock_code = cmd.strip().split()[0] if cmd.strip() else None
    if not stock_code:
        return [{"text": "❌ 错误：需要提供股票代码。"}]

    try:
        logger.info(f"正在查询股票代码 {stock_code} 的新闻...")
        # 调用 akshare 获取新闻数据
        news_df = ak.stock_news_em(symbol=stock_code)

        if news_df.empty:
            return [{"text": f"⚠️ 未找到股票代码 {stock_code} 的相关新闻。"}]

        # 确保 '发布时间' 列存在且转换为 datetime 对象用于排序
        if "发布时间" in news_df.columns:
            # 创建一个临时列存储 datetime 对象，处理可能的转换错误
            news_df["发布时间_dt"] = pd.to_datetime(
                news_df["发布时间"], errors="coerce"
            )
            # 按 datetime 对象降序排序（最新在前）
            news_df.sort_values(
                by="发布时间_dt", ascending=False, inplace=True, na_position="last"
            )
            # 可以选择删除临时列，如果后续格式化不直接使用它
            # news_df.drop(columns=['发布时间_dt'], inplace=True)
        else:
            logger.warning(
                f"股票 {stock_code} 的新闻数据中缺少 '发布时间' 列，无法排序。"
            )

        # 只选取最新的 N 条新闻进行展示
        max_news = 20  # 使用之前设置的 20 条
        news_to_display = news_df.head(max_news)  # 在排序后进行截断

        response_lines = [f"📰 {stock_code} 相关新闻 (最近 {len(news_to_display)} 条):"]
        response_lines.append("---------------------------\n")

        for index, row in news_to_display.iterrows():
            # 格式化单条新闻：标题 (来源 @ 时间) \n 链接
            # 截断长标题
            title = row["新闻标题"]
            if len(title) > 40:
                title = title[:38] + "..."  # 限制标题长度

            # 格式化时间戳 (akshare 返回的是 YYYY-MM-DD HH:MM:SS 字符串)
            publish_time_str = row["发布时间"]
            # 尝试解析并格式化，如果失败则使用原始字符串
            try:
                # 尝试从 datetime 列获取格式化时间，如果该列不存在或值为 NaT，则回退到字符串列
                if "发布时间_dt" in row and pd.notna(row["发布时间_dt"]):
                    publish_time = row["发布时间_dt"].strftime("%Y-%m-%d %H:%M")
                else:
                    # 如果 dt 列无效，再尝试转换原始字符串
                    publish_time = pd.to_datetime(publish_time_str).strftime(
                        "%Y-%m-%d %H:%M"
                    )
            except (ValueError, TypeError):
                publish_time = publish_time_str  # 保留原始格式

            news_line = (
                f"▪️ {title} \n"
                f"  <来源: {row['文章来源']} @ {publish_time}>\n"
                f"  <链接: {row['新闻链接']}>"
            )
            response_lines.append(news_line)
            response_lines.append("---")  # 添加分隔符

        # 移除最后一个分隔符
        if response_lines and response_lines[-1] == "---":
            response_lines.pop()

        final_response = "\n".join(response_lines)

        # 检查最终消息长度
        if len(final_response) > 2000:
            logger.warning(
                f"新闻消息过长 ({len(final_response)} chars)，可能无法完整发送。"
            )
            # 可以考虑进一步减少新闻条数或截断内容
            # 估算截断位置，例如保留标题和 N 条新闻
            estimated_lines_per_news = 3  # 标题行+来源/时间行+链接行+分隔符 (大约)
            # lines_to_keep = 2 + max_news * estimated_lines_per_news
            # 为了安全，稍微减少一点
            lines_to_keep = min(
                len(response_lines),
                2 + (max_news - 2) * estimated_lines_per_news if max_news > 2 else 2,
            )
            final_response = (
                    "\n".join(response_lines[:lines_to_keep]) + "\n(⚠️ 新闻过多，已截断)"
            )

        return [{"text": final_response}]

    except Exception as e:
        logger.error(f"查询股票 {stock_code} 新闻时出错: {e}", exc_info=True)
        return [{"text": f"❌ 查询股票 {stock_code} 新闻时出错: {e}"}]


async def get_stock_deepseek_prediction(cmd: str) -> List[Dict[str, str]]:
    stock_code = cmd.strip().split()[0] if cmd.strip() else None
    if not stock_code:
        return [{"text": "❌ 错误：需要提供股票代码。"}]
    return [{"text": f"💡 获取股票代码 {stock_code} 的 DeepSeek 预测 (待实现)"}]


async def get_market_overview(cmd: str) -> List[Dict[str, str]]:
    """获取股市总貌信息并格式化返回"""
    results = []
    errors = []
    today_str = datetime.date.today().strftime("%Y%m%d")

    # --- 获取上交所数据 ---
    sse_summary_df = None
    sse_daily_df = None
    try:
        sse_summary_df = await asyncio.to_thread(ak.stock_sse_summary)
        sse_daily_df = await asyncio.to_thread(ak.stock_sse_deal_daily, date=today_str)
    except Exception as e:
        logger.error(f"获取上交所数据时出错: {e}", exc_info=True)
        errors.append("获取上交所数据失败")

    # --- 获取深交所数据 ---
    szse_summary_df = None
    try:
        szse_summary_df = await asyncio.to_thread(ak.stock_szse_summary, date=today_str)
    except Exception as e:
        logger.error(f"获取深交所数据时出错: {e}", exc_info=True)
        errors.append("获取深交所数据失败")

    # --- 辅助格式化函数 ---
    def format_to_trillion(raw_value, original_unit: str = "yuan"):
        """将元或亿元格式化为万亿"""
        if raw_value is None or pd.isna(raw_value):
            return "N/A"
        try:
            value = float(raw_value)
            if original_unit == "billion_yuan":
                # 原始单位是亿，除以 10000 转为万亿
                trillion_value = value / 10000
            elif original_unit == "yuan":
                # 原始单位是元，除以 1e12 转为万亿
                trillion_value = value / 1e12
            else:
                logger.warning(f"Unsupported original unit: {original_unit}")
                return "N/A"
            return f"{trillion_value:.2f} 万亿"
        except (ValueError, TypeError):
            logger.warning(
                f"Could not convert '{raw_value}' to float for trillion formatting."
            )
            return "N/A"

    # --- 格式化上交所数据 --- (原始单位：亿元)
    if sse_summary_df is not None and sse_daily_df is not None:
        sse_summary_dict = sse_summary_df.set_index("项目").to_dict()
        sse_daily_dict = sse_daily_df.set_index("单日情况").to_dict()

        # 使用图标 🏦
        sse_results = [f"🏦 上海证券交易所概览 ({today_str})"]
        sse_results.append("----------------------------")
        try:
            # 使用 format_to_trillion 并指定原始单位为 billion_yuan
            sse_total_cap_str = format_to_trillion(
                sse_summary_dict["股票"]["总市值"], original_unit="billion_yuan"
            )
            sse_flow_cap_str = format_to_trillion(
                sse_summary_dict["股票"]["流通市值"], original_unit="billion_yuan"
            )
            sse_turnover_str = format_to_trillion(
                sse_daily_dict["股票"]["成交金额"], original_unit="billion_yuan"
            )

            sse_results.append(
                f"  🏢 上市公司: {sse_summary_dict['股票']['上市公司']} 家"
            )
            sse_results.append(f"  💰 总市值: {sse_total_cap_str}")
            sse_results.append(f"  🏦 流通市值: {sse_flow_cap_str}")
            sse_results.append(f"  💸 成交金额: {sse_turnover_str}")

            # 单独处理成交量 (股数)
            sse_volume_raw = sse_daily_dict["股票"]["成交量"]
            try:
                sse_volume = float(sse_volume_raw)
                if abs(sse_volume) >= 1e8:
                    sse_volume_str = f"{sse_volume / 1e8:.2f} 亿股"
                elif abs(sse_volume) >= 1e4:
                    sse_volume_str = f"{sse_volume / 1e4:.2f} 万股"
                else:
                    sse_volume_str = f"{sse_volume:,.0f} 股"
            except (ValueError, TypeError):
                sse_volume_str = "N/A"

            sse_results.append(f"  📊 成交量: {sse_volume_str}")

            # PE 和换手率格式化
            try:
                avg_pe = float(sse_daily_dict["股票"]["平均市盈率"])
                avg_pe_str = f"{avg_pe:.2f}"
            except (ValueError, TypeError, KeyError):
                avg_pe_str = "N/A"
            sse_results.append(f"  📈 平均市盈率: {avg_pe_str}")

            try:
                turnover_rate = float(sse_daily_dict["股票"]["换手率"])
                turnover_rate_str = f"{turnover_rate:.2f}%"
            except (ValueError, TypeError, KeyError):
                turnover_rate_str = "N/A"
            sse_results.append(f"  🔄 换手率: {turnover_rate_str}")

            results.append("\n".join(sse_results))
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"格式化上交所数据时出错: {e}", exc_info=True)
            results.append(
                "🏦 上海证券交易所概览\n----------------------------\n  (部分数据提取失败)"
            )
            errors.append("格式化上交所数据失败")
    else:
        results.append(
            "🏦 上海证券交易所概览\n----------------------------\n  (数据获取失败)"
        )

    results.append("")  # 空行分隔

    # --- 格式化深交所数据 --- (原始单位：元)
    if szse_summary_df is not None:
        szse_results = [f"🏦 深圳证券交易所概览 ({today_str})"]
        szse_results.append("----------------------------")
        try:
            szse_summary_df = szse_summary_df.set_index("证券类别")
            if "股票" in szse_summary_df.index:
                stock_row = szse_summary_df.loc["股票"]

                # 使用 format_to_trillion 并指定原始单位为 yuan
                szse_turnover_str = format_to_trillion(
                    stock_row["成交金额"], original_unit="yuan"
                )
                szse_total_cap_str = format_to_trillion(
                    stock_row["总市值"], original_unit="yuan"
                )
                szse_flow_cap_str = format_to_trillion(
                    stock_row["流通市值"], original_unit="yuan"
                )

                szse_results.append(f"  🏢 股票数量: {int(stock_row['数量']):,} 家")
                szse_results.append(f"  💸 股票成交金额: {szse_turnover_str}")
                szse_results.append(f"  💰 股票总市值: {szse_total_cap_str}")
                szse_results.append(f"  🏦 流通市值: {szse_flow_cap_str}")
            else:
                szse_results.append("  (未找到'股票'类别数据)")

            results.append("\n".join(szse_results))
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"格式化深交所数据时出错: {e}", exc_info=True)
            results.append(
                "🏦 深圳证券交易所概览\n----------------------------\n  (部分数据提取失败)"
            )
            errors.append("格式化深交所数据失败")
    else:
        results.append(
            "🏦 深圳证券交易所概览\n----------------------------\n  (数据获取失败)"
        )

    # 如果有错误，附加错误信息
    if errors:
        results.append("\n" + "⚠️ 注意: " + ", ".join(errors))

    return [{"text": "\n".join(results)}]


def format_large_number(num):
    if num is None or pd.isna(num):
        return "N/A"
    try:
        num = float(num)  # 确保是数字
    except (ValueError, TypeError):
        return "N/A"

    if abs(num) >= 1e12:  # 万亿
        return f"{num / 1e12:.2f} 万亿"
    elif abs(num) >= 1e8:  # 亿
        return f"{num / 1e8:.2f} 亿"
    elif abs(num) >= 1e4:  # 万
        return f"{num / 1e4:.2f} 万"
    else:
        return f"{num:,.2f}"  # 带千位分隔符，保留两位小数


def safe_get_value(df, item_name, default="N/A"):
    try:
        value = df.loc[df["item"] == item_name, "value"].iloc[0]
        return value if pd.notna(value) else default
    except (IndexError, KeyError):
        return default


async def get_stock_details(cmd: str) -> List[Dict[str, str]]:
    stock_code = cmd.strip().split()[0] if cmd.strip() else None
    if not stock_code or not stock_code.isdigit():
        return [{"text": "❌ 错误：需要提供有效的股票代码（纯数字）。"}]

    # Determine market prefix for xueqiu API
    if stock_code.startswith("6"):
        xq_symbol = f"SH{stock_code}"
    elif stock_code.startswith(("0", "3")):
        xq_symbol = f"SZ{stock_code}"
    elif stock_code.startswith(("4", "8")):
        xq_symbol = f"BJ{stock_code}"  # Assuming BJ for Beijing Stock Exchange
    else:
        return [{"text": f"❌ 错误：无法识别的股票代码格式 {stock_code}。"}]

    results = []
    stock_name = "N/A"  # Default name

    # --- Section 1: Basic Info (EM) ---
    try:
        logging.info(f"Fetching EM basic info for {stock_code}")
        stock_individual_info_em_df = await asyncio.to_thread(
            ak.stock_individual_info_em, symbol=stock_code
        )
        info_em_dict = stock_individual_info_em_df.set_index("item")["value"].to_dict()
        stock_name = info_em_dict.get(
            "股票简称", stock_code
        )  # Use code if name not found
        industry = info_em_dict.get("行业", "N/A")
        list_date_str = str(info_em_dict.get("上市时间", "N/A"))
        list_date = (
            f"{list_date_str[:4]}-{list_date_str[4:6]}-{list_date_str[6:]}"
            if len(list_date_str) == 8
               and list_date_str.isdigit()  # Check if it's a valid date string
            else list_date_str
        )
        total_market_cap = format_large_number(info_em_dict.get("总市值", "N/A"))
        flow_market_cap = format_large_number(info_em_dict.get("流通市值", "N/A"))

        results.append(f"🏢 {stock_name} ({stock_code})")
        results.append("--------------------")
        results.append(f"   行业: {industry}")
        results.append(f"   上市: {list_date}")
        results.append(f"   总市值: {total_market_cap}")
        results.append(f"   流通值: {flow_market_cap}")

    except Exception as e:
        logging.error(f"Error fetching EM basic info for {stock_code}: {e}")
        # If basic info fails, still add header if possible, then the error
        if not results:  # Only add header if it wasn't added
            results.append(f"🏢 {stock_name} ({stock_code})")
            results.append("--------------------")
        results.append(f"⚠️ 获取东方财富基本信息失败: {e}")

    results.append("")  # Add a blank line separator

    # --- Section 2: Company Overview (XQ) ---
    try:
        logging.info(f"Fetching XQ company info for {xq_symbol}")
        stock_individual_basic_info_xq_df = await asyncio.to_thread(
            ak.stock_individual_basic_info_xq, symbol=xq_symbol
        )
        info_xq_dict = stock_individual_basic_info_xq_df.set_index("item")[
            "value"
        ].to_dict()
        main_business = info_xq_dict.get("main_operation_business", "N/A")
        controller = info_xq_dict.get("actual_controller", "N/A")

        results.append("ℹ️ 公司概况")
        results.append("--------------------")
        # Keep business description concise
        business_display = (
            f"{main_business[:70]}..." if len(main_business) > 70 else main_business
        )
        results.append(f"   主营: {business_display}")
        results.append(f"   实控: {controller}")

    except Exception as e:
        logging.error(f"Error fetching XQ company info for {xq_symbol}: {e}")
        results.append("ℹ️ 公司概况")
        results.append("--------------------")
        results.append(f"⚠️ 获取雪球公司信息失败: {e}")

    results.append("")  # Add a blank line separator

    # --- Section 3: Realtime Quote & Bid/Ask (EM) ---
    try:
        logging.info(f"Fetching EM bid/ask info for {stock_code}")
        stock_bid_ask_em_df = await asyncio.to_thread(
            ak.stock_bid_ask_em, symbol=stock_code
        )
        bid_ask_dict = stock_bid_ask_em_df.set_index("item")["value"].to_dict()

        latest_price = bid_ask_dict.get("最新", "N/A")
        price_change = bid_ask_dict.get("涨跌", "N/A")
        change_percent = bid_ask_dict.get("涨幅", "N/A")
        high_price = bid_ask_dict.get("最高", "N/A")
        low_price = bid_ask_dict.get("最低", "N/A")
        open_price = bid_ask_dict.get("今开", "N/A")
        prev_close = bid_ask_dict.get("昨收", "N/A")
        volume = format_large_number(
            bid_ask_dict.get("总手", 0)
            * 100  # EM 总手 is lots, multiply by 100 for shares
        )
        turnover = format_large_number(bid_ask_dict.get("金额", "N/A"))
        turnover_rate = bid_ask_dict.get("换手", "N/A")
        volume_ratio = bid_ask_dict.get("量比", "N/A")

        # Format price related numbers
        latest_price_f = (
            f"{latest_price:.2f}"
            if isinstance(latest_price, (int, float))
            else latest_price
        )
        open_price_f = (
            f"{open_price:.2f}" if isinstance(open_price, (int, float)) else open_price
        )
        prev_close_f = (
            f"{prev_close:.2f}" if isinstance(prev_close, (int, float)) else prev_close
        )
        high_price_f = (
            f"{high_price:.2f}" if isinstance(high_price, (int, float)) else high_price
        )
        low_price_f = (
            f"{low_price:.2f}" if isinstance(low_price, (int, float)) else low_price
        )
        turnover_rate_f = (
            f"{turnover_rate:.2f}%"
            if isinstance(turnover_rate, (int, float))
            else turnover_rate
        )

        # Determine emoji and format change/percent
        price_emoji = "⚪️"
        price_change_f = "N/A"
        change_percent_f = "N/A"
        if isinstance(price_change, (int, float)) and isinstance(
                change_percent, (int, float)
        ):
            if price_change > 0:
                price_emoji = "🔼"
                price_change_f = f"+{price_change:.2f}"
                change_percent_f = f"+{change_percent:.2f}%"
            elif price_change < 0:
                price_emoji = "🔽"
                price_change_f = f"{price_change:.2f}"
                change_percent_f = f"{change_percent:.2f}%"
            else:
                price_change_f = f"{price_change:.2f}"
                change_percent_f = f"{change_percent:.2f}%"

        results.append("📈 实时行情")
        results.append("--------------------")
        results.append(
            f"   {price_emoji} {latest_price_f} ({price_change_f} / {change_percent_f})"
        )
        results.append(f"   今开: {open_price_f} | 昨收: {prev_close_f}")
        results.append(f"   最高: {high_price_f} | 最低: {low_price_f}")
        results.append(
            f"   成交量: {volume} 股"
        )  # Changed '手' to '股' after multiplying
        results.append(f"   成交额: {turnover}")
        results.append(f"   换手率: {turnover_rate_f} | 量比: {volume_ratio}")

        results.append("")  # Blank line before bid/ask

        # --- Bid/Ask ---
        results.append("📊 买卖盘")
        # Sell side
        sell_lines = []
        for i in range(5, 0, -1):
            price = bid_ask_dict.get(f"sell_{i}", "-")
            vol = format_large_number(bid_ask_dict.get(f"sell_{i}_vol", 0))
            price_f = f"{price:.2f}" if isinstance(price, (int, float)) else price
            sell_lines.append(f"   卖{i}: {price_f} ({vol} 股)")
        results.extend(sell_lines)

        results.append("   -----------")  # Separator

        # Buy side
        buy_lines = []
        for i in range(1, 6):
            price = bid_ask_dict.get(f"buy_{i}", "-")
            vol = format_large_number(bid_ask_dict.get(f"buy_{i}_vol", 0))
            price_f = f"{price:.2f}" if isinstance(price, (int, float)) else price
            buy_lines.append(f"   买{i}: {price_f} ({vol} 股)")
        results.extend(buy_lines)

    except Exception as e:
        logging.error(f"Error fetching EM bid/ask info for {stock_code}: {e}")
        # Add section header even if fetch fails
        results.append("📈 实时行情 & 📊 买卖盘")
        results.append("--------------------")
        results.append(f"⚠️ 获取东方财富行情报价失败: {e}")

    # Final check if anything was added at all
    if len(results) <= 2:  # Only header and separator potentially
        return [{"text": f"❌ 未能获取股票 {stock_code} 的任何有效信息。"}]

    return [{"text": "\n".join(results)}]


async def get_financial_report(cmd: str) -> List[Dict[str, str]]:
    """获取今日所有财报发布信息"""
    try:
        today_date = datetime.date.today().strftime("%Y%m%d")
        logger.info(f"正在查询日期 {today_date} 的财报发布信息...")
        report_df = ak.news_report_time_baidu(date=today_date)

        if report_df.empty:
            return [{"text": f"ℹ️ 今日（{today_date}）无财报发布信息。"}]
        reports = [f"📅 今日 ({today_date}) 财报发布计划:"]
        reports.append("-------------------------------------")
        # 使用原始的 report_df 迭代
        for index, row in report_df.iterrows():
            code = row.get("股票代码", "未知代码")
            name = row.get("股票简称", "未知简称")
            period = row.get("财报期", "未知周期")
            reports.append(f"▪️ {name} ({code}) - {period}")

        response_text = "\n".join(reports)

        # 检查消息长度
        if len(response_text) > 1800:  # 留一些余量
            logger.warning(f"财报信息过长 ({len(response_text)} chars)，进行截断。")
            # 保留标题和部分内容
            lines_to_keep = 2 + int(1700 / 20)  # 估算每行20字符
            response_text = (
                    "\n".join(reports[:lines_to_keep]) + "\n... (内容过长已截断)"
            )

        return [{"text": response_text}]
    except Exception as e:
        logger.error(f"获取财报信息时出错: {e}", exc_info=True)
        return [{"text": f"❌ 获取财报信息时出错: {e}"}]


class StockPlugin(BasePlugin):
    name = "StockPlugin"  # 插件名称
    version = "0.0.1"  # 插件版本

    config = None
    config_path = None
    config_last_modified = 0

    async def on_load(self):
        """插件加载时执行的操作"""
        logger.info(f"{self.name} 插件已加载")
        logger.info(f"插件版本: {self.version}")

        # 初始化配置路径
        self.config_path = Path(__file__).parent / "config" / "config.toml"

        # 加载配置
        self.load_config()

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, "rb") as f:
                    config_data = tomllib.load(f)
                    self.config = Config.from_dict(config_data)
                self.config_last_modified = os.path.getmtime(self.config_path)
                logger.info(f"成功加载 {self.name} 配置")
            else:
                logger.warning(f"{self.name} 配置文件不存在: {self.config_path}")
                self.config = Config([], [])  # Corrected initialization
        except Exception as e:
            logger.error(f"加载 {self.name} 配置出错: {str(e)}")
            self.config = Config([], [])  # Corrected initialization

    def check_config_update(self) -> bool:
        """检查配置文件是否已更新"""
        try:
            if self.config_path.exists():
                last_modified = os.path.getmtime(self.config_path)
                if last_modified > self.config_last_modified:
                    logger.info(f"{self.name} 配置文件已更新，重新加载")
                    self.load_config()
                    return True
            return False
        except Exception as e:
            logger.error(f"检查 {self.name} 配置更新出错: {str(e)}")
            return False

    def is_user_authorized(self, user_id: int, group_id: Optional[int] = None) -> bool:
        """检查用户是否有权限使用此插件"""
        if not self.config:
            logger.warning("授权检查失败：配置未加载。")
            return False

        # 检查用户ID是否在白名单中
        if user_id in self.config.whitelist_users:
            return True

        # 如果提供了群组ID，检查群组是否在白名单中
        if group_id and group_id in self.config.whitelist_groups:
            return True

        logger.debug(f"用户 {user_id} (群: {group_id}) 未授权。")
        return False

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群消息事件"""
        self.check_config_update()  # Check for config updates on each event

        if not msg.raw_message.startswith("股票 "):
            return

        if not self.is_user_authorized(msg.user_id, msg.group_id):
            await self.api.post_group_msg(
                msg.group_id, text="🚫 您没有权限使用股票插件"
            )
            return

        command_full = msg.raw_message[3:].strip()
        if not command_full:
            await self.api.post_group_msg(
                msg.group_id,
                text="ℹ️ 请输入操作指令，例如：股票 历史 600519",
            )
            return

        command_handlers = {
            "历史": handle_historical_command,
            "实时": get_stock_realtime_data,
            "新闻": get_stock_news,
            "预测": get_stock_deepseek_prediction,
            "总貌": get_market_overview,
            "个股": get_stock_details,
            "财报": get_financial_report,
        }

        parts = command_full.split()
        command_keyword = parts[0] if parts else ""
        cmd_args = " ".join(parts[1:])

        if command_keyword in command_handlers:
            handler = command_handlers[command_keyword]
            try:
                # 调用处理器获取待发送消息列表
                messages_to_send = await handler(cmd_args)

                # 迭代处理消息列表
                for msg_data in messages_to_send:
                    try:
                        if "text" in msg_data:
                            await self.api.post_group_msg(
                                msg.group_id, text=msg_data["text"]
                            )
                        elif "image" in msg_data:
                            filepath = msg_data["image"]
                            await self.api.post_group_msg(msg.group_id, image=filepath)
                            logger.info(f"成功发送图片: {filepath}")
                    except Exception as send_error:
                        logger.error(f"发送消息失败: {send_error}", exc_info=True)
                        # 尝试发送一条错误提示给用户
                        try:
                            await self.api.post_group_msg(
                                msg.group_id, text=f"❌ 发送部分结果时出错。"
                            )
                        except Exception:
                            logger.error("发送错误提示也失败了。")
            except Exception as handler_error:
                logger.error(
                    f"执行命令 '{command_keyword}' 处理器时出错: {handler_error}",
                    exc_info=True,
                )
                await self.api.post_group_msg(
                    msg.group_id,
                    text=f"❌ 执行命令 '{command_keyword}' 时遇到内部错误。",
                )
        else:
            # 如果命令未被识别
            supported_commands = ", ".join(command_handlers.keys())
            await self.api.post_group_msg(
                msg.group_id,
                text=f"❓ 无法识别命令 '{command_keyword}'。\n支持：{supported_commands}。\n"
                     f"示例：股票 历史 600519 | 股票 实时 000001",
            )
