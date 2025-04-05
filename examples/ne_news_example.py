#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网易新闻客户端示例

演示 NetEaseNewsClient 的基本用法
"""

from hotsearch.api import NetEaseNewsClient


def main():
    """演示NetEaseNewsClient的基本功能。"""
    # 创建客户端实例
    client = NetEaseNewsClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取网易新闻热门 =====")
    # 获取网易新闻热门数据
    news_data = client.get_news()
    # 获取条目列表
    news_items = client.get_items(sub_tab="news", as_model=True)
    # 打印前5条
    for i, item in enumerate(news_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   链接: {item.www_url}")
        if item.hot_score:
            print(f"   热度: {item.hot_score}")
        if item.source:
            print(f"   来源: {item.source}")
        print()

    print("\n===== 获取网易热度榜 =====")
    # 获取网易热度榜数据
    htd_data = client.get_hot()
    # 获取条目列表
    htd_items = client.get_items(sub_tab="htd", as_model=True)
    # 打印前5条
    for i, item in enumerate(htd_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   链接: {item.www_url}")
        if item.hot_score:
            print(f"   热度: {item.hot_score}")
        if item.reply_count:
            print(f"   回复数: {item.reply_count}")
        print()

    # 搜索特定关键词
    keyword = "国际"
    search_results = [item for item in news_items if keyword in item.title]
    if search_results:
        print(f"\n包含 '{keyword}' 的新闻标题:")
        for i, item in enumerate(search_results, 1):
            print(f"{i}. {item.title}")
    else:
        print(f"\n没有找到包含 '{keyword}' 的新闻标题")

    # 按热度排序
    hot_sorted_items = sorted(
        [item for item in htd_items if item.hot_score is not None],
        key=lambda x: x.hot_score,
        reverse=True,
    )
    if hot_sorted_items:
        print("\n热度最高的前3条:")
        for i, item in enumerate(hot_sorted_items[:3], 1):
            print(f"{i}. {item.title} - 热度: {item.hot_score}")

    # 结果保存在 ./examples/output/ne-news/ 目录下


if __name__ == "__main__":
    main()
