# 雪球客户端 (XueqiuClient)

`XueqiuClient`用于获取雪球平台热帖、新闻和公告数据。

## 导入

```python
from hotsearch.api import XueqiuClient
```

## 初始化

```python
# 使用默认配置
client = XueqiuClient()

# 自定义数据保存（使用标准目录）
client = XueqiuClient(
    save_data=True,
    data_dir="./examples/output"
)
```

## 方法

### 获取话题数据

```python
# 获取原始JSON数据
data = client.get_topic(page=1)

# 获取结构化数据模型
topic_data = client.get_topic(page=1, as_model=True)
```

### 获取新闻数据

```python
# 获取原始JSON数据
data = client.get_news(page=1)

# 获取结构化数据模型
news_data = client.get_news(page=1, as_model=True)
```

### 获取公告数据

```python
# 获取原始JSON数据
data = client.get_notice(page=1)

# 获取结构化数据模型
notice_data = client.get_notice(page=1, as_model=True)
```

### 获取数据条目列表

```python
# 获取话题条目
topic_items = client.get_items(sub_tab="topic", page=1, as_model=True)

# 获取新闻条目
news_items = client.get_items(sub_tab="news", page=1, as_model=True)

# 获取公告条目
notice_items = client.get_items(sub_tab="notice", page=1, as_model=True)
```

### 辅助属性

```python
# 获取话题条目列表
topic_items = client.topic_items

# 获取新闻条目列表
news_items = client.news_items

# 获取公告条目列表
notice_items = client.notice_items
```

### 增强方法

```python
# 按关键词搜索话题
keyword_topics = client.get_topics_by_keyword("股票")

# 获取按阅读量排序的话题
sorted_topics = client.get_topics_sorted_by_reads()  # 默认从高到低排序
sorted_topics = client.get_topics_sorted_by_reads(reverse=False)  # 从低到高排序

# 获取按时间排序的新闻
sorted_news = client.get_news_sorted_by_time()  # 默认从新到旧排序
sorted_news = client.get_news_sorted_by_time(reverse=False)  # 从旧到新排序

# 获取按时间排序的公告
sorted_notices = client.get_notice_sorted_by_time()  # 默认从新到旧排序

# 获取包含上涨股票的话题
positive_topics = client.get_topics_with_positive_stocks()

# 获取包含下跌股票的话题
negative_topics = client.get_topics_with_negative_stocks()
```

## 数据模型

### XueqiuHotSearchResponse

热帖响应模型，包含以下属性：

- `items`: 热帖条目列表（XueqiuTopicItem、XueqiuNewsItem或XueqiuNoticeItem的列表）
- `last_list_time`: 上次列表时间（整数，时间戳）
- `next_refresh_time`: 下次刷新时间（整数，时间戳）
- `version`: 版本号（整数）
- `current_page`: 当前页码（整数）
- `total_page`: 总页数（整数）

### XueqiuTopicItem

雪球话题条目模型，包含以下属性：

- `item_key`: 条目唯一标识（字符串）
- `title`: 标题（字符串）
- `desc`: 描述（字符串）
- `www_url`: 网页链接（字符串）
- `reason`: 热度原因（字符串，通常包含阅读量信息）
- `stocks`: 相关股票列表（XueqiuStock对象列表）

辅助属性和方法：

- `read_count`: 阅读数（从reason中提取的阅读量，整数）
- `top_stock`: 获取排名第一的股票（XueqiuStock对象或None）
- `get_positive_stocks()`: 获取涨幅为正的股票列表
- `get_negative_stocks()`: 获取涨幅为负的股票列表

### XueqiuNewsItem

雪球新闻条目模型，包含以下属性：

- `item_key`: 条目唯一标识（字符串）
- `title`: 标题（字符串）
- `www_url`: 网页链接（字符串）
- `created_at`: 创建时间戳（毫秒，整数）

辅助属性：

- `formatted_date`: 格式化的日期时间字符串（格式为'YYYY-MM-DD HH:MM:SS'）

### XueqiuNoticeItem

雪球公告条目模型，包含以下属性：

- `item_key`: 条目唯一标识（字符串）
- `title`: 标题（字符串）
- `www_url`: 网页链接（字符串）
- `created_at`: 创建时间戳（毫秒，整数）

辅助属性：

- `formatted_date`: 格式化的日期时间字符串（格式为'YYYY-MM-DD HH:MM:SS'）

### XueqiuStock

雪球股票模型，包含以下属性：

- `name`: 股票名称（字符串）
- `percentage`: 涨跌幅（浮点数）

## 示例

### 基本用法

```python
from hotsearch.api import XueqiuClient

# 创建客户端
client = XueqiuClient()

# 获取话题数据
topic_data = client.get_topic(as_model=True)
print(f"获取到 {len(topic_data.items)} 条话题")

# 遍历话题条目
for item in topic_data.items[:3]:
    print(f"标题: {item.title}")
    print(f"描述: {item.desc}")
    print(f"热度原因: {item.reason}")
    print(f"阅读数: {item.read_count}")
    print()
```

### 数据筛选与排序

```python
# 获取按阅读量排序的话题
sorted_topics = client.get_topics_sorted_by_reads()
print("阅读量最高的话题:")
for i, item in enumerate(sorted_topics[:3], 1):
    print(f"{i}. {item.title} - 阅读数: {item.read_count}")

# 获取包含上涨股票的话题
positive_topics = client.get_topics_with_positive_stocks()
print(f"\n包含上涨股票的话题数: {len(positive_topics)}")
for i, item in enumerate(positive_topics[:2], 1):
    print(f"{i}. {item.title}")
    positive_stocks = item.get_positive_stocks()
    for stock in positive_stocks[:2]:
        print(f"   - {stock.name}: +{stock.percentage}%")

# 获取按关键词筛选的话题
keyword_topics = client.get_topics_by_keyword("股票")
print(f"\n包含'股票'关键词的话题数: {len(keyword_topics)}")
for i, item in enumerate(keyword_topics[:3], 1):
    print(f"{i}. {item.title}")
```

### 处理新闻数据

```python
# 获取按时间排序的新闻
sorted_news = client.get_news_sorted_by_time()
print("最新的新闻:")
for i, item in enumerate(sorted_news[:3], 1):
    print(f"{i}. {item.title}")
    print(f"   发布时间: {item.formatted_date}")
    print(f"   链接: {item.www_url}")
    print()
```

### 数据处理与保存

```python
import os
import json

# 处理并保存话题数据
def save_processed_topics(items):
    """保存处理后的话题数据。"""
    os.makedirs("./examples/output", exist_ok=True)
    
    processed_data = []
    for item in items:
        # 获取股票信息
        stocks_info = []
        for stock in item.stocks:
            stocks_info.append({
                "name": stock.name,
                "percentage": stock.percentage,
                "trend": "上涨" if stock.percentage > 0 else "下跌" if stock.percentage < 0 else "持平"
            })
            
        # 构建处理后的数据
        processed_data.append({
            "title": item.title,
            "description": item.desc,
            "url": item.www_url,
            "reason": item.reason,
            "read_count": item.read_count,
            "stocks": stocks_info,
            "has_positive_stocks": len(item.get_positive_stocks()) > 0,
            "has_negative_stocks": len(item.get_negative_stocks()) > 0,
            "item_key": item.item_key
        })
    
    # 保存到JSON文件
    with open("./examples/output/processed_topics.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

# 调用保存函数
topics = client.topic_items
save_processed_topics(topics)
```

## 注意事项

- API返回的数据列表存储在JSON字符串中，客户端会自动解析
- 阅读数从热度原因中提取，格式通常为"xxx万阅读"
- 创建时间戳(created_at)是毫秒级时间戳
- 如果请求无效页码或出现网络错误，客户端会返回空列表而非抛出异常

## 常见问题解答

### Q: 获取到的数据为空怎么办？
A: 检查网络连接和API服务状态。也可能是当前平台暂无内容数据。

### Q: 为什么有些话题没有阅读数？
A: 不是所有话题的热度原因都包含阅读量信息。如果提取不到，read_count属性会返回None。

### Q: 如何自定义数据保存路径？
A: 初始化客户端时设置`save_data=True`和`data_dir="自定义路径"`。

### Q: 如何扩展或自定义模型？
A: 可以继承现有模型类并添加自定义属性和方法，然后在客户端中使用自定义模型。