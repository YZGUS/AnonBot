#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百度热搜客户端示例

演示 BaiduClient 的基本用法
"""

from hotsearch.api import BaiduClient


def main():
    """演示BaiduClient的基本功能。"""
    # 创建客户端实例
    client = BaiduClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取百度实时热点 =====")
    # 获取实时热点数据
    realtime_data = client.get_realtime()
    # 获取条目列表
    realtime_items = client.get_items(sub_tab="realtime")
    # 打印前5条
    for i, item in enumerate(realtime_items[:5], 1):
        # 检查item结构
        if isinstance(item, dict):
            title = item.get("word", item.get("title", "未知标题"))
            hot_score = item.get("hot_score", item.get("hotScore", "未知"))
            print(f"{i}. {title} - 热度: {hot_score}")
        else:
            print(f"{i}. {item} (类型: {type(item)})")

    print("\n===== 获取百度热搜词 =====")
    # 获取热搜词数据
    phrase_data = client.get_phrase()
    # 获取条目列表
    phrase_items = client.get_items(sub_tab="phrase")
    # 打印前5条
    for i, item in enumerate(phrase_items[:5], 1):
        if isinstance(item, dict):
            title = item.get("word", item.get("title", "未知标题"))
            hot_score = item.get("hot_score", item.get("hotScore", "未知"))
            print(f"{i}. {title} - 热度: {hot_score}")
        else:
            print(f"{i}. {item} (类型: {type(item)})")

    print("\n===== 获取百度小说热搜 =====")
    # 获取小说热搜数据
    novel_data = client.get_novel()
    # 获取条目列表
    novel_items = client.get_items(sub_tab="novel")
    # 打印前5条
    for i, item in enumerate(novel_items[:5], 1):
        if isinstance(item, dict):
            title = item.get("word", item.get("title", "未知标题"))
            hot_score = item.get("hot_score", item.get("hotScore", "未知"))
            print(f"{i}. {title} - 热度: {hot_score}")
        else:
            print(f"{i}. {item} (类型: {type(item)})")

    print("\n===== 获取百度游戏热搜 =====")
    # 获取游戏热搜数据
    game_data = client.get_game()
    # 获取条目列表
    game_items = client.get_items(sub_tab="game")
    # 打印前5条
    for i, item in enumerate(game_items[:5], 1):
        if isinstance(item, dict):
            title = item.get("word", item.get("title", "未知标题"))
            hot_score = item.get("hot_score", item.get("hotScore", "未知"))
            print(f"{i}. {title} - 热度: {hot_score}")
        else:
            print(f"{i}. {item} (类型: {type(item)})")

    # 结果保存在 ./examples/output/baidu/ 目录下


if __name__ == "__main__":
    main()
