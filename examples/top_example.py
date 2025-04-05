#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
热榜综合客户端示例

演示 TopClient 的基本用法
"""

from hotsearch.api import TopClient


def main():
    """演示TopClient的基本功能。"""
    # 创建客户端实例
    client = TopClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌（实际使用中建议使用自己的令牌）
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取今日热榜 =====")
    # 获取今日热榜数据
    today_data = client.get_today()
    # 获取条目列表
    today_items = client.get_items(sub_tab="today")
    # 打印前5条
    for i, item in enumerate(today_items[:5], 1):
        if isinstance(item, dict):
            title = item.get("title", "未知标题")
            # 来源可能是不同的字段名
            source = item.get(
                "source", item.get("domain", item.get("site_name", "未知来源"))
            )
            print(f"{i}. {title} - {source}")
        else:
            print(f"{i}. {item}")

    print("\n===== 获取本周热榜 =====")
    # 获取本周热榜数据
    weekly_data = client.get_weekly()
    # 获取条目列表
    weekly_items = client.get_items(sub_tab="weekly")
    # 打印前5条
    for i, item in enumerate(weekly_items[:5], 1):
        if isinstance(item, dict):
            title = item.get("title", "未知标题")
            # 来源可能是不同的字段名
            source = item.get(
                "source", item.get("domain", item.get("site_name", "未知来源"))
            )
            print(f"{i}. {title} - {source}")
        else:
            print(f"{i}. {item}")

    print("\n===== 获取本月热榜 =====")
    # 获取本月热榜数据
    monthly_data = client.get_monthly()
    # 获取条目列表
    monthly_items = client.get_items(sub_tab="monthly")
    # 打印前5条
    for i, item in enumerate(monthly_items[:5], 1):
        if isinstance(item, dict):
            title = item.get("title", "未知标题")
            # 来源可能是不同的字段名
            source = item.get(
                "source", item.get("domain", item.get("site_name", "未知来源"))
            )
            print(f"{i}. {title} - {source}")
        else:
            print(f"{i}. {item}")

    print("\n===== 使用模型对象 =====")
    # 获取结构化模型对象
    model_items = client.get_items(sub_tab="today", as_model=True)
    print(f"\n找到 {len(model_items)} 个热榜条目")
    # 打印前3条的结构化信息
    for i, item in enumerate(model_items[:3], 1):
        print(f"{i}. {item.title}")
        print(f"   热度: {item.formatted_hot_value}")
        print(f"   链接: {item.link}")
        print()

    # 结果保存在 ./examples/output/top/ 目录下


if __name__ == "__main__":
    main()
