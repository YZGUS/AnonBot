# 今日头条客户端 (ToutiaoClient)

`ToutiaoClient`用于获取今日头条平台热门话题数据。

## 导入

```python
from hotsearch.api import ToutiaoClient
```

## 初始化

```python
# 默认配置
client = ToutiaoClient()

# 自定义授权令牌
client = ToutiaoClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = ToutiaoClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="examples/output"
)
```

## 方法

### 获取热门话题

```python
# 获取原始JSON数据
data = client.get_hot(page=1)

# 获取结构化数据模型
data_model = client.get_hot(page=1, as_model=True)
```

### 获取热门话题条目列表

```python
# 获取原始条目数据
items = client.get_items(page=1)

# 获取结构化条目模型
items_model = client.get_items(page=1, as_model=True)
```

### 辅助方法

```python
# 获取特定标签的话题
boom_topics = client.get_items_by_label(label="boom")  # 爆点话题
hot_topics = client.get_items_by_label(label="hot")    # 热点话题
new_topics = client.get_items_by_label(label="new")    # 新话题

# 获取按热度排序的话题
sorted_items = client.get_items_sorted()  # 默认从高到低

# 关键词搜索
keyword_items = client.search_items("关键词")

# 批量处理
processed_items = client.process_items(items, process_func)

# 数据导出
client.export_items(items, format="json", file_path="output.json")
```

## 数据模型

### ToutiaoHotTopics

热门话题列表模型，包含以下属性：

- `items`: 热门话题条目列表
- `last_list_time`: 上次列表时间
- `next_refresh_time`: 下次刷新时间
- `version`: 版本号
- `current_page`: 当前页码
- `total_page`: 总页数

### ToutiaoHotSearchItem

热门话题条目模型，包含以下属性：

- `item_key`: 条目唯一标识
- `title`: 话题标题
- `www_url`: 话题链接
- `label`: 话题标签（boom=爆, hot=热, new=新, refuteRumors=辟谣, interpretation=解读）
- `hot_value`: 热度值（字符串）

辅助属性和方法：

- `hot_value_int`: 热度值整数
- `label_name`: 标签中文名称

## 示例

### 基本用法

```python
from hotsearch.api import ToutiaoClient

# 创建客户端
client = ToutiaoClient()

# 获取热门话题数据
topics = client.get_hot(as_model=True)
print(f"获取到 {len(topics.items)} 条热门话题")

# 遍历话题条目
for item in topics.items[:5]:
    print(f"{item.title} - 热度: {item.hot_value_int:,}")
```

### 数据筛选与排序

```python
# 获取爆点话题
boom_topics = client.get_items_by_label(label="boom")

# 获取按热度排序的话题
sorted_items = client.get_items_sorted()

# 关键词筛选
keyword_items = client.search_items("中国")
```

### 数据处理与保存

```python
import os
import json

# 处理并保存数据
def save_processed_data(items):
    os.makedirs("examples/output", exist_ok=True)
    
    processed_data = []
    for item in items:
        processed_data.append({
            "标题": item.title,
            "热度": f"{item.hot_value_int:,}",
            "标签": item.label_name or "普通",
            "链接": item.www_url
        })
    
    with open("examples/output/processed_topics.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

# 调用保存函数
save_processed_data(topics.items)
```

## 注意事项

- API返回的话题列表存储在JSON字符串中，客户端会自动解析
- 话题标签含义：
  - `boom`: 爆点话题
  - `hot`: 热点话题
  - `new`: 新话题
  - `refuteRumors`: 辟谣
  - `interpretation`: 解读
- 热度值(`hot_value`)为字符串类型，使用`hot_value_int`属性获取整数

## 常见问题

### Q: 获取到的数据为空怎么办？
A: 检查网络连接和API状态，确保授权令牌正确。

### Q: 为什么有些话题没有标签？
A: 普通话题没有特定标签，只有热点、爆点等特殊话题才有标签。

### Q: 如何自定义数据保存？
A: 初始化时设置`save_data=True`和`data_dir="自定义路径"`。

### Q: 如何扩展模型？
A: 继承现有模型类并添加自定义属性和方法。