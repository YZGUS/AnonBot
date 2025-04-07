# 掘金客户端 (JuejinClient)

`JuejinClient`用于获取掘金平台热榜数据。

## 导入

```python
from hotsearch.api.juejin import JuejinClient
```

## 初始化

```python
# 默认配置
client = JuejinClient()

# 自定义授权令牌
client = JuejinClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = JuejinClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="examples/output"
)
```

## 方法

### 获取热门话题

```python
# 获取原始JSON数据
data = client.get_hot_topics(sub_tab="all", page=1)

# 获取结构化数据模型
data_model = client.get_hot_topics(sub_tab="all", page=1, as_model=True)
```

可用的分类参数 (`sub_tab`):
- `all`: 全部
- `backend`: 后端
- `frontend`: 前端
- `android`: 安卓
- `ios`: iOS
- `ai`: 人工智能
- `dev-tools`: 开发工具
- `code-life`: 代码人生
- `read`: 阅读

### 获取热门话题条目列表

```python
# 获取原始条目数据
items = client.get_items(sub_tab="all", page=1)

# 获取结构化条目模型
items_model = client.get_items(sub_tab="all", page=1, as_model=True)
```

### 筛选与排序

```python
# 获取前N个热门条目
top_items = client.get_top_items(limit=10)

# 按热度指数排序
sorted_items = client.get_items_sorted_by_popularity(reverse=True)

# 按浏览量排序
view_sorted_items = client.get_items_sorted_by_views(reverse=True)

# 关键词搜索
keyword_items = client.search_items("Python")

# 按作者筛选
author_items = client.get_items_by_author("作者名称")
```

### 数据导出

```python
# 导出为JSON
client.export_items(items, format="json", file_path="output.json")

# 导出为CSV
client.export_items(items, format="csv", file_path="output.csv")
```

## 数据模型

### JuejinHotTopics

热门话题列表模型，包含以下属性：

- `items`: 热门话题条目列表
- `last_list_time`: 上次列表时间
- `next_refresh_time`: 下次刷新时间
- `version`: 版本号
- `current_page`: 当前页码
- `total_page`: 总页数

方法:
- `get_top_items(limit=10)`: 获取前N个热门条目
- `get_by_author(author_name)`: 按作者名称筛选条目
- `search_by_title(keyword)`: 按标题关键词搜索条目
- `sort_by_popularity(reverse=True)`: 按热度指数排序条目
- `sort_by_views(reverse=True)`: 按浏览量排序条目
- `to_dict()`: 转换为字典

### JuejinHotItem

热门话题条目模型，包含以下属性：

- `item_key`: 条目唯一标识
- `id`: 文章ID
- `title`: 文章标题
- `author_id`: 作者ID
- `author_name`: 作者名称
- `author_avatar`: 作者头像URL
- `view`: 浏览量（整数）
- `collect`: 收藏数（整数）
- `hot_rank`: 热度排名（整数）
- `interact_count`: 互动数量（整数）
- `comment_count`: 评论数量（整数）
- `like`: 点赞数（整数）

辅助属性:
- `article_url`: 文章完整URL
- `author_url`: 作者主页URL
- `full_avatar_url`: 完整头像URL
- `popularity_index`: 热度指数
- `interaction_rate`: 互动率

方法:
- `to_dict()`: 转换为字典

## 示例

### 基本用法

```python
from hotsearch.api.juejin import JuejinClient

# 创建客户端
client = JuejinClient()

# 获取热门话题数据
topics = client.get_hot_topics(as_model=True)
print(f"获取到 {len(topics.items)} 条热门话题")

# 遍历话题条目
for item in topics.items[:5]:
    print(f"{item.title} - 浏览量: {item.view}")
```

### 数据筛选与排序

```python
# 按热度排序
popular_items = client.get_items_sorted_by_popularity()
for item in popular_items[:3]:
    print(f"{item.title} - 热度指数: {item.popularity_index:.2f}")
    
# 关键词搜索
python_items = client.search_items("Python")
for item in python_items:
    print(f"{item.title} - {item.article_url}")
```

### 数据比较分析

```python
# 获取不同分类的数据
frontend_items = client.get_items(sub_tab="frontend", as_model=True)
backend_items = client.get_items(sub_tab="backend", as_model=True)

# 计算平均浏览量
frontend_avg = sum(item.view for item in frontend_items) / len(frontend_items)
backend_avg = sum(item.view for item in backend_items) / len(backend_items)

print(f"前端文章平均浏览量: {frontend_avg:.1f}")
print(f"后端文章平均浏览量: {backend_avg:.1f}")
```

### 数据导出

```python
# 导出热门话题
items = client.get_items(as_model=True)
client.export_items(items, format="json", file_path="juejin_topics.json")
```

## 注意事项

- 掘金API返回的列表数据存储在JSON字符串中，客户端会自动解析
- 热度指数 (`popularity_index`) 计算公式：(点赞数 * 2 + 评论数 * 3 + 收藏数 * 4) / 100
- 互动率 (`interaction_rate`) 计算公式：互动数 / 浏览量
- 头像URL可能是相对路径，使用 `full_avatar_url` 获取完整URL

## 常见问题

### Q: 获取到的数据为空怎么办？
A: 检查网络连接和API状态，确保授权令牌正确。某些分类可能暂时没有数据。

### Q: 如何处理分页数据？
A: 使用 `page` 参数获取不同页的数据，可以通过 `total_page` 属性了解总页数。

### Q: 如何自定义数据保存？
A: 初始化时设置 `save_data=True` 和 `data_dir="自定义路径"`。

### Q: 如何扩展模型？
A: 继承 `JuejinHotItem` 或 `JuejinHotTopics` 类并添加自定义属性和方法。