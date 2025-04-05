#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
雪球热帖客户端示例

演示 XueqiuClient 的基本用法
"""

from hotsearch.api import XueqiuClient


def main():
    """演示XueqiuClient的基本功能。"""
    # 创建客户端实例
    client = XueqiuClient(
        auth_token="Bearer b4abc833-112a-11f0-8295-3292b700066c",  # 使用默认令牌
        save_data=True,  # 保存原始数据
        data_dir="./examples/output",  # 数据保存目录
    )

    # 创建输出目录
    import os

    os.makedirs("./examples/output", exist_ok=True)

    print("===== 获取雪球话题 =====")
    # 获取雪球话题数据
    topic_data = client.get_topic()
    # 获取条目模型数据
    topic_items = client.get_items(sub_tab="topic", as_model=True)
    # 打印前5条
    for i, item in enumerate(topic_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   描述: {item.desc[:50]}...")
        print(f"   热度: {item.reason}")
        print(f"   链接: {item.www_url}")
        # 显示相关股票
        if item.stocks:
            print(f"   相关股票: ", end="")
            stock_info = [f"{s.name}({s.percentage:+.2f}%)" for s in item.stocks[:3]]
            print(", ".join(stock_info))
        print()

    print("===== 获取雪球新闻 =====")
    # 获取雪球新闻数据
    news_data = client.get_news()
    # 获取条目模型数据
    news_items = client.get_items(sub_tab="news", as_model=True)
    # 打印前5条
    for i, item in enumerate(news_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   时间: {item.formatted_date}")
        print(f"   链接: {item.www_url}")
        print()

    print("===== 获取雪球公告 =====")
    # 获取雪球公告数据
    notice_data = client.get_notice()
    # 获取条目模型数据
    notice_items = client.get_items(sub_tab="notice", as_model=True)
    # 打印前5条
    for i, item in enumerate(notice_items[:5], 1):
        print(f"{i}. {item.title}")
        print(f"   时间: {item.formatted_date}")
        print(f"   链接: {item.www_url}")
        print()

    print("===== 雪球数据筛选与排序示例 =====")
    # 按阅读数排序话题
    topics_by_reads = client.get_topics_sorted_by_reads()
    if topics_by_reads:
        print(f"\n阅读数最多的前3个话题:")
        for i, item in enumerate(topics_by_reads[:3], 1):
            read_count = f"{item.read_count/10000:.1f}万" if item.read_count else "未知"
            print(f"{i}. {item.title} - 阅读数: {read_count}")

    # 按发布时间排序新闻
    news_by_time = client.get_news_sorted_by_time()
    if news_by_time:
        print(f"\n最新发布的3条新闻:")
        for i, item in enumerate(news_by_time[:3], 1):
            print(f"{i}. {item.title} - 时间: {item.formatted_date}")

    # 获取含有上涨股票的话题
    positive_topics = client.get_topics_with_positive_stocks()
    if positive_topics:
        print(f"\n包含上涨股票的话题:")
        for i, item in enumerate(positive_topics[:3], 1):
            pos_stocks = [
                f"{s.name}(+{s.percentage:.2f}%)"
                for s in item.get_positive_stocks()[:2]
            ]
            print(f"{i}. {item.title} - 上涨股票: {', '.join(pos_stocks)}")

    # 结果保存在 ./examples/output/xueqiu/ 目录下


if __name__ == "__main__":
    main()
