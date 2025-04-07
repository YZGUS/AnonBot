#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
股票数据模块使用示例
"""

import os
import sys
import time
from datetime import datetime
from pprint import pprint

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import stock_data, StockDataError


def demo_stock_real_time():
    """
    演示获取股票实时行情数据
    """
    print("\n=== 演示获取股票实时行情数据 ===")
    try:
        # 获取招商银行实时行情
        stock_info = stock_data.get_stock_real_time("sh600036")
        print(f"招商银行实时行情:")
        pprint(stock_info)

        # 获取腾讯实时行情
        stock_info = stock_data.get_stock_real_time("sz000001")
        print(f"\n平安银行实时行情:")
        pprint(stock_info)
    except StockDataError as e:
        print(f"错误: {e}")


def demo_stock_history():
    """
    演示获取股票历史行情数据
    """
    print("\n=== 演示获取股票历史行情数据 ===")
    try:
        # 获取茅台最近30天的历史数据
        df = stock_data.get_stock_history(
            "sh600519",
            start_date=(datetime.now().replace(day=1)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d"),
        )
        print(f"贵州茅台近期历史数据，共{len(df)}条:")
        print(df.head())

        # 保存到CSV文件
        file_path = stock_data.save_data_to_file(df, "maotai_history", "csv")
        print(f"\n数据已保存至: {file_path}")
    except StockDataError as e:
        print(f"错误: {e}")


def demo_stock_list():
    """
    演示获取股票列表
    """
    print("\n=== 演示获取股票列表 ===")
    try:
        # 获取所有A股股票列表
        df = stock_data.get_stock_list()
        print(f"A股股票数量: {len(df)}")
        print("\n前5只股票:")
        print(df[["symbol", "name", "current_price", "change_percent"]].head())

        # 筛选涨幅大于5%的股票
        rise_stocks = df[df["change_percent"] > 5]
        print(f"\n涨幅大于5%的股票数量: {len(rise_stocks)}")
        if not rise_stocks.empty:
            print(
                rise_stocks[
                    ["symbol", "name", "current_price", "change_percent"]
                ].head()
            )
    except StockDataError as e:
        print(f"错误: {e}")


def demo_stock_info():
    """
    演示获取股票详细信息
    """
    print("\n=== 演示获取股票详细信息 ===")
    try:
        # 获取阿里巴巴的详细信息
        stock_info = stock_data.get_stock_info("sh601857")
        print(f"中国石油详细信息:")
        pprint({k: v for k, v in stock_info.items() if k not in ["symbol", "code"]})
    except StockDataError as e:
        print(f"错误: {e}")


def demo_index_data():
    """
    演示获取指数数据
    """
    print("\n=== 演示获取指数数据 ===")
    try:
        # 获取上证指数实时行情
        sh_index = stock_data.get_index_real_time("000001")
        print(f"上证指数实时行情:")
        pprint(sh_index)

        # 获取深证成指实时行情
        sz_index = stock_data.get_index_real_time("399001")
        print(f"\n深证成指实时行情:")
        pprint(sz_index)

        # 获取所有指数列表
        index_list = stock_data.get_index_list()
        print(f"\n总共有{len(index_list)}个指数")
        print("\n部分重要指数:")
        important_indices = ["000001", "399001", "399006", "000300", "000016", "000905"]
        print(
            index_list[index_list["code"].isin(important_indices)][
                ["code", "name", "current_price", "change_percent"]
            ]
        )
    except StockDataError as e:
        print(f"错误: {e}")


def demo_sector_data():
    """
    演示获取板块数据
    """
    print("\n=== 演示获取板块数据 ===")
    try:
        # 获取概念板块行情
        concept_sectors = stock_data.get_sector_real_time("gn")
        print(f"共有{len(concept_sectors)}个概念板块")

        # 筛选涨幅前5的概念板块
        top_sectors = concept_sectors.sort_values(
            by="change_percent", ascending=False
        ).head(5)
        print("\n涨幅前5的概念板块:")
        print(top_sectors[["name", "current_price", "change_percent", "leading_stock"]])

        # 获取行业板块行情
        industry_sectors = stock_data.get_sector_real_time("hy")
        print(f"\n共有{len(industry_sectors)}个行业板块")
        print("\n涨幅前3的行业板块:")
        print(
            industry_sectors.sort_values(by="change_percent", ascending=False).head(3)[
                ["name", "current_price", "change_percent", "leading_stock"]
            ]
        )
    except StockDataError as e:
        print(f"错误: {e}")


def run_all_demos():
    """
    运行所有演示函数
    """
    print("===== 股票数据模块使用示例 =====")
    print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    demo_stock_real_time()
    time.sleep(1)  # 避免频繁请求

    demo_stock_history()
    time.sleep(1)

    demo_stock_list()
    time.sleep(1)

    demo_stock_info()
    time.sleep(1)

    demo_index_data()
    time.sleep(1)

    demo_sector_data()

    print("\n===== 演示完成 =====")


if __name__ == "__main__":
    run_all_demos()
