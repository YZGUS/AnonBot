#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
澎湃新闻客户端示例

演示 ThePaperClient 的基本用法
"""

from hotsearch.api import ThePaperClient


def main():
    """演示ThePaperClient的基本功能。"""
    # 创建客户端实例
    client = ThePaperClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取澎湃新闻热门 =====")
    # 获取澎湃新闻热门数据
    hot_data = client.get_hot()
    # 获取条目模型数据
    hot_items = client.get_items(as_model=True)
    # 打印前5条
    for i, item in enumerate(hot_items[:5], 1):
        print(f"{i}. {item.title}")
        if item.desc:
            # 限制摘要长度
            desc = item.desc[:100] + "..." if len(item.desc) > 100 else item.desc
            print(f"   摘要: {desc}")
        if item.article_url:
            print(f"   链接: {item.article_url}")
        print()

    # 搜索特定关键词
    keyword = "政治"
    search_results = [
        item
        for item in hot_items
        if keyword in item.title or (item.desc and keyword in item.desc)
    ]
    if search_results:
        print(f"\n包含 '{keyword}' 的新闻:")
        for i, item in enumerate(search_results, 1):
            print(f"{i}. {item.title}")
    else:
        print(f"\n没有找到包含 '{keyword}' 的新闻")

    # 按发布时间排序
    sorted_items = sorted(
        [item for item in hot_items if item.pub_time],
        key=lambda x: x.pub_time,
        reverse=True,
    )
    if sorted_items:
        print("\n最新发布的5条新闻:")
        for i, item in enumerate(sorted_items[:5], 1):
            print(f"{i}. {item.title} - 发布时间: {item.pub_time}")

    # 结果保存在 ./examples/output/thepaper/ 目录下


if __name__ == "__main__":
    main()
