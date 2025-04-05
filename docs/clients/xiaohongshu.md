# 小红书客户端 (XiaohongshuClient)

`XiaohongshuClient` 用于获取小红书热搜数据。

## 导入

```python
from hotsearch.api.xiaohongshu import XiaohongshuClient
```

## 初始化

```python
# 使用默认配置
client = XiaohongshuClient()

# 自定义授权令牌
client = XiaohongshuClient(auth_token="Bearer your-token-here")

# 自定义数据保存（使用标准目录）
client = XiaohongshuClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="/Users/cengyi/Desktop/code/HotSearchAPI/examples/output"
)
```

## 方法

### 获取热搜数据

```python
# 获取原始JSON数据
data = client.get_hot_search(page=1)

# 获取结构化数据模型
data_model = client.get_hot_search(page=1, as_model=True)
```

### 获取热搜条目列表

```python
# 获取原始条目数据
items = client.get_items(page=1)

# 获取结构化条目模型
items_model = client.get_items(page=1, as_model=True)
```

### 辅助方法

```python
# 获取特定标签的热搜
new_items = client.get_items_by_tag(tag="新")  # 新上榜热搜
hot_items = client.get_hot_items()  # 热门热搜
exclusive_items = client.get_exclusive_items()  # 独家热搜

# 获取按浏览量排序的热搜
sorted_items = client.get_items_sorted_by_views()  # 默认从高到低排序
sorted_asc = client.get_items_sorted_by_views(reverse=False)  # 从低到高排序

# 搜索包含关键词的热搜
keyword_items = client.search_items(keyword="关键词")
```

## 数据模型

### XiaohongshuHotSearch

热搜数据模型，包含以下属性：

- `items`: 热搜条目列表，包含 `XiaohongshuHotSearchItem` 对象
- `last_list_time`: 上次列表时间戳
- `next_refresh_time`: 下次刷新时间戳
- `version`: 版本号
- `current_page`: 当前页码
- `total_page`: 总页数

### XiaohongshuHotSearchItem

热搜条目模型，包含以下属性：

- `item_key`: 条目唯一标识
- `title`: 热搜标题
- `view_num`: 浏览数量（原始字符串，如"936.1万"）
- `tag`: 标签（如"新"、"热"、"无"、"独家"等）
- `www_url`: 网页链接

辅助属性和方法：

- `views`: 浏览数量（解析后的整数值）
- `is_new`: 是否为新上榜热搜
- `is_hot`: 是否为热门热搜
- `is_exclusive`: 是否为独家热搜
- `tag_type`: 标签类型的描述文字

## 示例

### 基本用法

```python
from hotsearch.api.xiaohongshu import XiaohongshuClient

# 创建客户端
client = XiaohongshuClient()

# 获取热搜数据
hot_search = client.get_hot_search(as_model=True)
print(f"获取到 {len(hot_search.items)} 条热搜")

# 遍历热搜条目
for item in hot_search.items[:5]:
    print(f"{item.title} - 浏览量: {item.view_num}({item.tag_type})")
```

### 数据筛选与排序

```python
# 获取新上榜的热搜
new_items = client.get_new_items()
print(f"新上榜热搜数量: {len(new_items)}")

# 获取热门热搜
hot_items = client.get_hot_items()
print(f"热门热搜数量: {len(hot_items)}")

# 获取按浏览量排序的热搜
sorted_items = client.get_items_sorted_by_views()
print("浏览量最高的热搜:")
for item in sorted_items[:3]:
    print(f"{item.title} - 浏览量: {item.views}")

# 自定义筛选 - 筛选包含特定关键词的热搜
keyword = "新"
keyword_items = client.search_items(keyword)
print(f"包含'{keyword}'的热搜: {len(keyword_items)}")
```

### 数据处理与保存

```python
import os
import json
from datetime import datetime

# 处理并保存数据
def save_processed_data(items):
    os.makedirs("/Users/cengyi/Desktop/code/HotSearchAPI/examples/output", exist_ok=True)
    
    processed_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "items": []
    }
    
    for item in items:
        processed_data["items"].append({
            "title": item.title,
            "views": item.views,
            "view_format": item.view_num,
            "tag": item.tag,
            "tag_type": item.tag_type,
            "url": item.www_url
        })
    
    with open("/Users/cengyi/Desktop/code/HotSearchAPI/examples/output/xiaohongshu_processed.json", "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

# 调用保存函数
save_processed_data(client.get_items(as_model=True))
```

## 注意事项

- API返回的热搜列表存储在JSON字符串中，客户端会自动解析
- 热搜标签含义：
  - "新": 新上榜的热搜
  - "热": 热门热搜
  - "独家": 独家热搜
  - "无": 普通热搜
- `view_num`字段为字符串类型，如"936.1万"，可以通过`views`属性获取解析后的整数值

## 常见问题解答

### Q: 获取到的数据为空怎么办？
A: 检查网络连接和API服务状态，确保提供了正确的授权令牌（如需要）。API可能临时不可用或没有返回数据。

### Q: 如何处理浏览量中的"万"单位？
A: 数据模型已经提供了`views`属性，它会自动将"936.1万"这样的格式转换为整数(9361000)。

### Q: 如何自定义数据保存路径？
A: 初始化客户端时设置`save_data=True`和`data_dir="自定义路径"`。

### Q: 如何扩展现有功能？
A: 可以继承`XiaohongshuClient`类并添加自定义方法，或者继承`XiaohongshuHotSearchItem`类添加更多辅助属性和方法。