#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
掘金客户端示例

演示 JuejinClient 的基本用法
"""

from hotsearch.api.juejin import JuejinClient


def main():
    """演示JuejinClient的基本功能。"""
    # 创建客户端实例
    client = JuejinClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取掘金全部热门 =====")
    # 获取掘金全部热门数据
    all_data = client.get_hot_topics(sub_tab="all")
    # 获取条目模型数据
    all_items = client.get_items(sub_tab="all", as_model=True)
    # 打印前5条
    for i, item in enumerate(all_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   作者: {item.author_name}")
        print(f"   点赞: {item.like} | 评论: {item.comment_count}")
        print(f"   链接: {item.article_url}")
        print()

    print("\n===== 获取掘金前端分类 =====")
    # 获取掘金前端分类数据
    frontend_items = client.get_items(sub_tab="frontend", as_model=True)
    # 打印前5条
    for i, item in enumerate(frontend_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   作者: {item.author_name}")
        print(f"   点赞: {item.like} | 评论: {item.comment_count}")
        print()

    print("\n===== 获取掘金后端分类 =====")
    # 获取掘金后端分类数据
    backend_items = client.get_items(sub_tab="backend", as_model=True)
    # 打印前5条
    for i, item in enumerate(backend_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   作者: {item.author_name}")
        print(f"   点赞: {item.like} | 评论: {item.comment_count}")
        print()

    print("\n===== 获取掘金人工智能分类 =====")
    # 获取掘金人工智能分类数据
    ai_items = client.get_items(sub_tab="ai", as_model=True)
    # 打印前5条
    for i, item in enumerate(ai_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   作者: {item.author_name}")
        print(f"   点赞: {item.like} | 评论: {item.comment_count}")
        print()

    print("===== 掘金数据筛选与排序示例 =====")
    # 按点赞数排序
    sorted_items = sorted(all_items, key=lambda x: x.like, reverse=True)
    print(f"\n点赞数最多的前3篇文章:")
    for i, item in enumerate(sorted_items[:3], 1):
        print(f"{i}. {item.title} - 点赞数: {item.like}")

    # 搜索特定关键词
    keyword = "Python"
    search_results = client.search_items(keyword)
    if search_results:
        print(f"\n包含 '{keyword}' 的文章:")
        for i, item in enumerate(search_results[:3], 1):
            print(f"{i}. {item.title}")
    else:
        print(f"\n没有找到包含 '{keyword}' 的文章")

    # 按热度指数排序
    popularity_items = client.get_items_sorted_by_popularity()
    if popularity_items:
        print(f"\n热度指数最高的前3篇文章:")
        for i, item in enumerate(popularity_items[:3], 1):
            print(f"{i}. {item.title} - 热度指数: {item.popularity_index:.2f}")

    # 按浏览量排序
    view_items = client.get_items_sorted_by_views()
    if view_items:
        print(f"\n浏览量最高的前3篇文章:")
        for i, item in enumerate(view_items[:3], 1):
            print(f"{i}. {item.title} - 浏览量: {item.view}")

    # 结果保存在 ./examples/output/juejin/ 目录下


if __name__ == "__main__":
    main()
