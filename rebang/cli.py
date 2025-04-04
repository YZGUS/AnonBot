#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
热榜 Today 爬虫命令行接口

使用示例:
    python -m rebang.cli --tab hupu --output hupu_data.json
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

from rebang.constants import AVAILABLE_TABS, TAB_CATEGORIES
from rebang.scraper import get_tab_data, get_tab_data_json


def setup_logger(level=logging.INFO):
    """
    设置日志配置

    Args:
        level: 日志级别
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_args():
    """
    解析命令行参数

    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description="热榜 Today 网站爬虫工具",
        epilog="示例: python -m rebang.cli --tab hupu --output hupu_data.json",
    )

    # 添加参数
    parser.add_argument(
        "--tab",
        "-t",
        required=True,
        help=f"要抓取的标签，可用值: {', '.join(AVAILABLE_TABS)}",
    )

    parser.add_argument(
        "--output", "-o", default=None, help="输出文件路径，默认为标准输出"
    )

    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用的标签")

    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    parser.add_argument(
        "--quiet", "-q", action="store_true", help="静默模式，只显示错误日志"
    )

    return parser.parse_args()


def list_available_tabs():
    """列出所有可用的标签分类"""
    print("热榜 Today 网站可用标签列表:")
    print()

    for category, tabs in TAB_CATEGORIES.items():
        print(f"● {category}:")
        for tab in tabs:
            print(f"  - {tab}")
        print()

    print(f"共计 {len(AVAILABLE_TABS)} 个标签")


def main():
    """主函数"""
    args = parse_args()

    # 设置日志级别
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.ERROR
    else:
        log_level = logging.INFO

    setup_logger(log_level)

    # 如果只是列出标签，则执行后退出
    if args.list:
        list_available_tabs()
        return 0

    try:
        # 获取数据
        json_data = get_tab_data_json(args.tab)

        # 输出数据
        if args.output:
            # 确保输出目录存在
            output_dir = os.path.dirname(args.output)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # 写入文件
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_data)

            print(f"数据已保存到: {args.output}")
        else:
            # 输出到标准输出
            print(json_data)

        return 0

    except Exception as e:
        logging.error(f"抓取数据失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
