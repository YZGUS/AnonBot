# 热榜综合客户端 (TopClient)

`TopClient`用于获取热榜综合数据，包括今日、本周和本月的热榜。

## 导入

```python
from hotsearch.api import TopClient
```

## 初始化

```python
# 使用默认配置
client = TopClient()

# 提供自定义授权令牌（推荐）
client = TopClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = TopClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="./my_data"
)
```

## 基本方法

### 获取今日热榜

```python
# 获取原始数据
data = client.get_today(page=1)

# 获取结构化模型
topics = client.get_today(page=1, as_model=True)
```

### 获取本周热榜

```python
# 获取原始数据
data = client.get_weekly(page=1)

# 获取结构化模型
topics = client.get_weekly(page=1, as_model=True)
```

### 获取本月热榜

```python
# 获取原始数据
data = client.get_monthly(page=1)

# 获取结构化模型
topics = client.get_monthly(page=1, as_model=True)
```

### 获取热榜条目列表

```python
# 今日热榜条目
items = client.get_items(sub_tab="today", page=1)

# 本周热榜条目
items = client.get_items(sub_tab="weekly", page=1)

# 本月热榜条目
items = client.get_items(sub_tab="monthly", page=1)

# 获取结构化模型
model_items = client.get_items(sub_tab="today", page=1, as_model=True)

# 打印条目标题
for item in model_items:
    print(item.title)
```

## 辅助方法

### 排序和筛选

```python
# 按热度排序的条目（降序）
sorted_items = client.get_items_sorted(sub_tab="today")

# 按热度排序的条目（升序）
sorted_items = client.get_items_sorted(sub_tab="today", reverse=False)

# 搜索包含关键词的条目
keyword_items = client.search_items("关键词", sub_tab="today")

# 获取热度超过阈值的条目
popular_items = client.get_popular_items(sub_tab="today", threshold=10000)
```

### 数据处理和导出

```python
# 批量处理条目
def process_func(item):
    return {
        "标题": item.title,
        "热度值": item.hot_value,
        "链接": item.link
    }

processed_data = client.process_items(items, process_func)

# 导出为JSON
client.export_items(items, format="json", file_path="output.json")

# 导出为CSV
client.export_items(items, format="csv", file_path="output.csv")
```

## 数据模型

### TopHotSearchResponse

热榜综合响应模型，包含以下属性：

- `items`: 热榜条目列表
- `tab`: 标签名称，固定为"top"
- `sub_tab`: 子标签名称，可能为"today"、"weekly"或"monthly"
- `page`: 页码
- `total_page`: 总页数
- `current_page`: 当前页码
- `last_update_time`: 上次更新时间（时间戳）
- `next_refresh_time`: 下次刷新时间（时间戳）

辅助属性和方法：

- `has_next_page`: 是否有下一页
- `item_count`: 条目数量

### TopHotSearchItem

热榜条目模型，包含以下属性：

- `title`: 标题
- `link`: 链接（可能来自link、mobile_url或www_url字段）
- `item_key`: 条目唯一标识（可能来自item_key或id字段）
- `hot_value`: 热度值（整数，可能来自hot_value或heat_num字段）
- `hot_value_format`: 格式化的热度值（如"1.5万"）
- `icon`: 图标URL（可选，可能来自icon或img字段）
- `is_ad`: 是否广告（布尔值）

辅助属性和方法：

- `is_popular`: 是否热门条目（热度值 > 10000）
- `formatted_hot_value`: 格式化的热度值
- `get_full_icon_url()`: 获取完整图标URL

## 完整示例

### 基本用法

```python
from hotsearch.api import TopClient

# 初始化客户端
client = TopClient()

# 获取今日热榜
today_topics = client.get_today(as_model=True)

# 打印热榜信息
print(f"获取到{len(today_topics.items)}条热榜条目")
print(f"当前页: {today_topics.current_page}/{today_topics.total_page}")

# 打印热榜条目
for item in today_topics.items[:5]:
    print(f"{item.title} - 热度: {item.formatted_hot_value}")
```

### 高级用法

```python
# 热度排序
sorted_items = client.get_items_sorted()
print("热度最高的条目:", sorted_items[0].title)

# 搜索关键词
tech_items = client.search_items("科技")
print(f"找到{len(tech_items)}条包含'科技'的条目")

# 自定义处理和导出
def custom_format(item):
    return {
        "标题": item.title,
        "热度": item.hot_value_format,
        "链接": item.link,
        "是否热门": "是" if item.is_popular else "否"
    }

# 处理数据
processed = client.process_items(sorted_items, custom_format)

# 导出数据
client.export_items(processed, format="json", file_path="hot_topics.json")
```

## 参数说明

- `sub_tab`: 子分类，可选值：`today`（今日）, `weekly`（本周）, `monthly`（本月）
- `page`: 页码，通常为1
- `as_model`: 是否返回结构化模型，默认为False
- `threshold`: 热度阈值，用于筛选热门条目
- `format`: 导出格式，可选值：`json`、`csv`

## 注意事项

- API返回的热榜条目可能存储在"items"或"list"字段中，且可能以JSON字符串形式存储，客户端会自动处理
- 热度值可能来自"hot_value"或"heat_num"字段，客户端会自动识别并转换为整数
- 链接URL可能来自"link"、"mobile_url"或"www_url"字段，客户端会自动处理
- 条目ID可能来自"item_key"或"id"字段
- 图标URL可能来自"icon"或"img"字段，且可能为相对路径，需要使用`get_full_icon_url()`获取完整URL
- 如果API没有提供格式化的热度值，客户端会自动生成（超过1万自动转换为"X.X万"格式）