#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小红书客户端示例

演示 XiaohongshuClient 的基本用法
"""

from hotsearch.api.xiaohongshu import XiaohongshuClient


def main():
    """演示XiaohongshuClient的基本功能。"""
    # 创建客户端实例
    client = XiaohongshuClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取小红书热搜 =====")
    # 获取小红书热搜数据
    data = client.get_hot_search()
    # 获取条目模型数据
    items = client.get_items(as_model=True)
    # 打印所有条目
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.title}")
        if item.tag:
            print(f"   类型: {item.tag_type}")
        if item.view_num:
            print(f"   热度: {item.view_num}")
        if item.www_url:
            print(f"   链接: {item.www_url}")
        print()

    # 搜索特定关键词
    keyword = "美食"
    search_results = client.search_items(keyword)
    if search_results:
        print(f"\n包含 '{keyword}' 的热搜词:")
        for i, item in enumerate(search_results, 1):
            print(f"{i}. {item.title}")
    else:
        print(f"\n没有找到包含 '{keyword}' 的热搜词")

    # 按热度排序
    sorted_items = client.get_items_sorted_by_views()
    if sorted_items:
        print("\n热度最高的前5条:")
        for i, item in enumerate(sorted_items[:5], 1):
            print(f"{i}. {item.title} - 热度: {item.view_num}")

    # 获取热门热搜条目
    hot_items = client.get_hot_items()
    if hot_items:
        print("\n热门标签条目:")
        for i, item in enumerate(hot_items[:3], 1):
            print(f"{i}. {item.title}")

    # 获取新上榜热搜条目
    new_items = client.get_new_items()
    if new_items:
        print("\n新上榜条目:")
        for i, item in enumerate(new_items[:3], 1):
            print(f"{i}. {item.title}")

    # 结果保存在 ./examples/output/xiaohongshu/ 目录下


if __name__ == "__main__":
    main()
