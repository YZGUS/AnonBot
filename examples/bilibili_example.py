#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B站热门客户端示例

演示 BilibiliClient 的基本用法
"""

from hotsearch.api import BilibiliClient


def main():
    """演示BilibiliClient的基本功能。"""
    # 创建客户端实例
    client = BilibiliClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output"  # 数据保存目录
    )

    # 创建输出目录
    import os
    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取B站热门视频 =====")
    # 获取热门视频数据
    popular_data = client.get_popular()
    # 获取条目模型数据
    popular_items = client.get_model_items(sub_tab="popular")
    # 打印前5条
    for i, item in enumerate(popular_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   UP主: {item.owner_name}")
        print(f"   播放量: {item.view:,} | 弹幕量: {item.danmaku:,}")
        print(f"   链接: {item.video_url}")
        print()

    print("===== 获取B站每周必看 =====")
    # 获取每周必看数据
    weekly_data = client.get_weekly()
    # 获取条目模型数据
    weekly_items = client.get_model_items(sub_tab="weekly")
    # 打印前5条
    for i, item in enumerate(weekly_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   UP主: {item.owner_name}")
        print(f"   播放量: {item.view:,} | 弹幕量: {item.danmaku:,}")
        print(f"   链接: {item.video_url}")
        print()

    print("===== 获取B站排行榜 =====")
    # 获取排行榜数据
    rank_data = client.get_rank()
    # 获取条目模型数据
    rank_items = client.get_model_items(sub_tab="rank")
    # 打印前5条
    for i, item in enumerate(rank_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   UP主: {item.owner_name}")
        print(f"   播放量: {item.view:,} | 弹幕量: {item.danmaku:,}")
        print(f"   链接: {item.video_url}")
        print()
        
    print("===== B站数据筛选与排序示例 =====")
    # 按播放量排序
    sorted_items = client.get_items_sorted(sort_by="view", reverse=True)
    print(f"\n播放量最高的前3个视频:")
    for i, item in enumerate(sorted_items[:3], 1):
        print(f"{i}. {item.title} - 播放量: {item.view:,}")
        
    # 搜索特定关键词
    keyword = "游戏"
    keyword_items = client.search_items(keyword)
    print(f"\n包含关键词 '{keyword}' 的前3个视频:")
    for i, item in enumerate(keyword_items[:3], 1):
        print(f"{i}. {item.title}")
        
    # 按观看量筛选
    high_views = client.get_items_by_views(min_views=1000000)
    print(f"\n播放量超过一百万的视频数量: {len(high_views)}")

    # 结果保存在 ./examples/output/bilibili/ 目录下


if __name__ == "__main__":
    main()