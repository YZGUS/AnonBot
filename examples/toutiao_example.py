#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
今日头条客户端示例

演示 ToutiaoClient 的基本用法
"""

from hotsearch.api import ToutiaoClient


def main():
    """演示ToutiaoClient的基本功能。"""
    # 创建客户端实例
    client = ToutiaoClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取今日头条热搜 =====")
    # 获取今日头条热搜数据
    hot_data = client.get_hot()
    # 获取条目模型数据
    hot_items = client.get_items(as_model=True)
    # 打印前5条
    for i, item in enumerate(hot_items[:5], 1):
        print(f"{i}. {item.title}")
        if item.hot_value:
            print(f"   热度: {item.hot_value}")
        if item.www_url:
            print(f"   链接: {item.www_url}")
        print()

    # 按热度排序
    sorted_items = sorted(
        [item for item in hot_items if item.hot_value],
        key=lambda x: x.hot_value_int,
        reverse=True,
    )
    if sorted_items:
        print("\n热度最高的前5条:")
        for i, item in enumerate(sorted_items[:5], 1):
            print(f"{i}. {item.title} - 热度: {item.hot_value}")

    # 搜索特定关键词
    keyword = "财经"
    search_results = [item for item in hot_items if keyword in item.title]
    if search_results:
        print(f"\n包含 '{keyword}' 的热搜标题:")
        for i, item in enumerate(search_results, 1):
            print(f"{i}. {item.title}")
    else:
        print(f"\n没有找到包含 '{keyword}' 的热搜标题")

    # 结果保存在 ./examples/output/toutiao/ 目录下


if __name__ == "__main__":
    main()
