#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
腾讯新闻客户端示例

演示 TencentNewsClient 的基本用法
"""

from hotsearch.api import TencentNewsClient


def main():
    """演示TencentNewsClient的基本功能。"""
    # 创建客户端实例
    client = TencentNewsClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取腾讯新闻热门 =====")
    # 获取腾讯新闻热门数据
    hot_data = client.get_hot()
    # 获取条目列表
    hot_items = client.get_items(as_model=True)
    # 打印前5条
    for i, item in enumerate(hot_items[:5], 1):
        print(f"{i}. {item.title}")
        if item.www_url:
            print(f"   链接: {item.www_url}")
        if item.hot_score:
            print(f"   热度评分: {item.hot_score}")
        if item.comment_num:
            print(f"   评论数: {item.comment_num}")
        print()

    # 搜索特定关键词
    keyword = "国际"
    search_results = [item for item in hot_items if keyword in item.title]
    if search_results:
        print(f"\n包含 '{keyword}' 的新闻标题:")
        for i, item in enumerate(search_results, 1):
            print(f"{i}. {item.title}")
    else:
        print(f"\n没有找到包含 '{keyword}' 的新闻标题")

    # 按热度排序
    sorted_items = sorted(
        [item for item in hot_items if item.hot_score is not None],
        key=lambda x: x.hot_score,
        reverse=True,
    )
    if sorted_items:
        print("\n热度评分最高的前3条:")
        for i, item in enumerate(sorted_items[:3], 1):
            print(f"{i}. {item.title} - 热度评分: {item.hot_score}")

    # 结果保存在 ./examples/output/tencent-news/ 目录下


if __name__ == "__main__":
    main()
