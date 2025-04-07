# 百度贴吧客户端 (BaiduTiebaClient)

`BaiduTiebaClient`用于获取百度贴吧热门话题数据。

## 导入

```python
from hotsearch.api import BaiduTiebaClient
```

## 初始化

```python
# 使用默认配置
client = BaiduTiebaClient()

# 提供自定义授权令牌（推荐）
client = BaiduTiebaClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = BaiduTiebaClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="./my_data"
)
```

## 方法

### 获取热门话题

```python
# 获取原始JSON数据
data = client.get_hot_topics(page=1)

# 获取结构化数据模型
data_model = client.get_hot_topics(page=1, as_model=True)
```

### 获取热门话题条目列表

```python
# 获取原始条目数据
items = client.get_items(page=1)

# 获取结构化条目模型
items_model = client.get_items(page=1, as_model=True)

# 打印条目标题
for item in items_model:
    print(item.name)
```

## 参数说明

- `page`: 页码，默认为1
- `as_model`: 是否返回结构化数据模型，默认为False

## 数据模型

### BaiduTiebaHotTopics

热门话题列表模型，包含以下属性：

- `items`: 热门话题条目列表 (`List[BaiduTiebaHotTopicItem]`)
- `last_list_time`: 上次列表时间
- `next_refresh_time`: 下次刷新时间
- `version`: 版本号
- `current_page`: 当前页码
- `total_page`: 总页数

### BaiduTiebaHotTopicItem

热门话题条目模型，包含以下属性：

- `item_key`: 条目唯一标识
- `id`: 话题ID
- `name`: 话题标题
- `desc`: 话题描述
- `discuss_num`: 讨论数量
- `image`: 图片URL
- `topic_tag`: 话题标签（整数）
- `is_video_topic`: 是否为视频话题（"0"或"1"）

## 使用示例

### 按讨论量排序

```python
# 获取结构化条目
items = client.get_items(as_model=True)

# 按讨论量排序
sorted_items = sorted(items, key=lambda x: x.discuss_num, reverse=True)

# 打印排序结果
for item in sorted_items[:5]:  # 前5条最热话题
    print(f"{item.name}: {item.discuss_num} 讨论")
```

### 按话题标签筛选

```python
# 获取结构化条目
items = client.get_items(as_model=True)

# 筛选特定标签的话题
# 标签说明：0=普通, 1=热点, 2=重大, 3=体育
hot_items = [item for item in items if item.topic_tag == 1]  # 热点话题
important_items = [item for item in items if item.topic_tag == 2]  # 重大话题
sports_items = [item for item in items if item.topic_tag == 3]  # 体育话题

print(f"热点话题数: {len(hot_items)}")
print(f"重大话题数: {len(important_items)}")
print(f"体育话题数: {len(sports_items)}")
```

## 注意事项

- API返回的话题列表存储在JSON字符串中，客户端会自动解析
- 话题标签(topic_tag)含义：0=普通, 1=热点, 2=重大, 3=体育
- is_video_topic字段为字符串类型的"0"或"1"，而非布尔值
- 返回的图片URL需要拼接完整路径才能访问