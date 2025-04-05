# 澎湃新闻客户端 (ThePaperClient)

`ThePaperClient` 用于获取澎湃新闻热门新闻数据。

## 导入

```python
from hotsearch.api import ThePaperClient
```

## 初始化

```python
# 默认配置
client = ThePaperClient()

# 自定义数据保存
client = ThePaperClient(
    save_data=True,
    data_dir="examples/output"
)
```

## 方法

### 获取热门新闻

```python
# 获取原始JSON数据
data = client.get_hot(page=1)

# 获取结构化数据模型
data_model = client.get_hot(page=1, as_model=True)
```

### 获取热门新闻条目列表

```python
# 获取原始条目数据
items = client.get_items(page=1)

# 获取结构化条目模型
items_model = client.get_items(page=1, as_model=True)
```

### 辅助方法

```python
# 关键词搜索
keyword_items = client.search_items("关键词")

# 获取按评论数排序的话题
sorted_items = client.get_items_sorted(sort_by="comment_num")  # 默认从高到低

# 批量处理
processed_items = client.process_items(items, process_func)

# 数据导出
client.export_items(items, format="json", file_path="output.json")
```

## 数据模型

### ThePaperHotTopics

澎湃新闻热门话题集合模型，包含以下属性：

- `items`: 热门新闻条目列表
- `last_list_time`: 上次列表时间
- `next_refresh_time`: 下次刷新时间
- `version`: 版本号
- `current_page`: 当前页码
- `total_page`: 总页数
- `code`: 状态码
- `msg`: 状态信息

### ThePaperItem

澎湃新闻条目模型，包含以下属性：

- `item_key`: 条目唯一标识
- `id`: 新闻ID
- `title`: 新闻标题
- `desc`: 新闻描述
- `comment_num`: 评论数量（整数）
- `image`: 图片URL
- `pub_time`: 发布时间（时间戳）

辅助属性和方法：

- `article_url`: 文章完整URL
- `full_image_url`: 完整图片URL

## 示例

### 基本用法

```python
from hotsearch.api import ThePaperClient

# 创建客户端
client = ThePaperClient()

# 获取热门新闻数据
topics = client.get_hot(as_model=True)
print(f"获取到 {len(topics.items)} 条热门新闻")

# 遍历新闻条目
for item in topics.items[:5]:
    print(f"{item.title} - 评论数: {item.comment_num}")
```

### 数据筛选与排序

```python
# 关键词搜索
keyword_items = client.search_items("关键词")

# 按评论数排序
sorted_items = client.get_items_sorted(sort_by="comment_num")

# 按发布时间排序
time_sorted = client.get_items_sorted(sort_by="pub_time")

# 按标题排序（升序）
title_sorted = client.get_items_sorted(sort_by="title", reverse=False)
```

### 数据处理与保存

```python
import os
import json

# 获取数据
items = client.get_items(as_model=True)

# 自定义处理
def process_news(item):
    return {
        "标题": item.title,
        "评论数": item.comment_num,
        "描述": item.desc[:50] + "...",
        "链接": item.article_url
    }

# 批量处理
processed_data = client.process_items(items, process_news)

# 保存处理后的数据
os.makedirs("examples/output", exist_ok=True)
with open("examples/output/processed_news.json", "w", encoding="utf-8") as f:
    json.dump(processed_data, f, ensure_ascii=False, indent=2)

# 使用内置导出方法
client.export_items(items, format="json", file_path="examples/output/news.json")
client.export_items(items, format="csv", file_path="examples/output/news.csv")
```

## 注意事项

- API返回的新闻列表存储在JSON字符串中，客户端会自动解析
- 评论数(`comment_num`)在原始数据中为字符串，模型会自动转为整数
- 图片URL可能需要拼接完整路径，使用`full_image_url`属性可以获取完整URL

## 常见问题

### Q: 获取到的数据为空怎么办？
A: 检查网络连接和API状态，确保参数正确。

### Q: 如何处理API返回的特殊格式？
A: 客户端已内置特殊格式处理逻辑，如有其他需求可继承重写相关方法。

### Q: 如何自定义数据保存？
A: 初始化时设置`save_data=True`和`data_dir="自定义路径"`。

### Q: 如何扩展模型？
A: 继承现有模型类并添加自定义属性和方法。