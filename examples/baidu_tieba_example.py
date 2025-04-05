#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百度贴吧客户端示例

演示 BaiduTiebaClient 的基本用法
"""

from hotsearch.api import BaiduTiebaClient


def main():
    """演示BaiduTiebaClient的基本功能。"""
    # 创建客户端实例
    client = BaiduTiebaClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取百度贴吧热门话题 =====")
    # 获取百度贴吧热门话题数据
    data = client.get_items()
    # 获取条目模型数据
    items = client.get_items(as_model=True)
    # 打印所有热门话题
    for i, item in enumerate(items, 1):
        print(f"{i}. {item.name}")
        print(f"   描述: {item.desc}")
        print(f"   讨论数: {item.discuss_num}")
        if hasattr(item, "hot_value") and item.hot_value:
            print(f"   热度: {item.hot_value}")
        print()

    # 搜索特定关键词
    keyword = "游戏"
    search_results = [item for item in items if keyword in item.name]
    if search_results:
        print(f"\n包含 '{keyword}' 的热门话题:")
        for i, item in enumerate(search_results, 1):
            print(f"{i}. {item.name}")
    else:
        print(f"\n没有找到包含 '{keyword}' 的热门话题")

    # 结果保存在 ./examples/output/baidu-tieba/ 目录下


if __name__ == "__main__":
    main()
