# B站客户端 (BilibiliClient)

`BilibiliClient`用于获取B站热门视频数据。

## 导入

```python
from hotsearch.api import BilibiliClient
```

## 初始化

```python
# 默认配置
client = BilibiliClient()

# 自定义授权令牌
client = BilibiliClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = BilibiliClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="examples/output"
)
```

## 方法

### 获取热门视频数据

```python
# 获取热门视频 - 原始JSON数据
popular_data = client.get_popular(page=1)

# 获取热门视频 - 结构化数据模型
popular_model = client.get_popular(page=1, as_model=True)

# 获取每周必看数据
weekly_data = client.get_weekly(page=1, as_model=True)

# 获取排行榜数据
rank_data = client.get_rank(page=1, as_model=True)
```

### 获取条目列表

```python
# 获取原始条目数据
items = client.get_items(sub_tab="popular", page=1)

# 获取条目模型数据
model_items = client.get_model_items(sub_tab="popular", page=1)

# 可用sub_tab: "popular"(热门), "weekly"(每周必看), "rank"(排行榜)
```

### 辅助方法

```python
# 搜索包含关键词的视频
keyword_items = client.search_items("游戏", sub_tab="popular")

# 获取指定播放量以上的视频
high_view_videos = client.get_items_by_views(min_views=1000000)

# 获取按不同字段排序的视频
view_sorted = client.get_items_sorted(sort_by="view", reverse=True)  # 按播放量排序
danmaku_sorted = client.get_items_sorted(sort_by="danmaku")  # 按弹幕量排序
title_sorted = client.get_items_sorted(sort_by="title", reverse=False)  # 按标题排序

# 获取特定UP主的视频
up_videos = client.get_items_by_up("UP主名称")

# 批量处理视频数据
def extract_info(item):
    return {"title": item.title, "views": item.view}
processed = client.process_items(items, extract_info)

# 导出数据
client.export_items(items, format="json", file_path="output.json")
client.export_items(items, format="csv", file_path="output.csv")
```

## 数据模型

### BilibiliHotTopics

热门视频集合模型，包含以下属性：

- `items`: 热门视频条目列表
- `last_list_time`: 上次列表时间戳
- `next_refresh_time`: 下次刷新时间戳
- `version`: 版本号
- `current_page`: 当前页码
- `total_page`: 总页数
- `code`: 状态码
- `msg`: 状态消息

### BilibiliItem

热门视频条目模型，包含以下基本属性：

- `item_key`: 条目唯一标识
- `title`: 视频标题
- `describe`: 视频描述
- `bvid`: B站视频ID
- `pic`: 封面图片路径
- `owner_name`: UP主名称
- `owner_mid`: UP主ID（整数）
- `danmaku`: 弹幕数量（整数）
- `view`: 播放量（整数）

辅助属性和方法：

- `video_url`: 视频完整URL
- `owner_url`: UP主主页URL
- `full_pic_url`: 完整封面图片URL
- `popularity_level`: 热门程度等级（"极热门"、"很热门"、"热门"、"较热门"、"一般"）

## 示例

### 基本用法

```python
from hotsearch.api import BilibiliClient

# 创建客户端
client = BilibiliClient()

# 获取热门视频数据
popular = client.get_popular(as_model=True)
print(f"获取到 {len(popular.items)} 条热门视频")

# 遍历视频条目
for item in popular.items[:5]:
    print(f"{item.title} - UP主: {item.owner_name} - 播放量: {item.view:,}")
```

### 数据筛选与排序

```python
# 获取高播放量视频
high_view_videos = client.get_items_by_views(min_views=1000000)

# 获取按弹幕量排序的视频
danmaku_sorted = client.get_items_sorted(sort_by="danmaku")

# 搜索特定关键词
game_videos = client.search_items("游戏")

# 获取特定UP主视频
up_videos = client.get_items_by_up("某UP主")
```

### 数据处理与保存

```python
import os

# 获取并处理数据
items = client.get_model_items("popular")

# 自定义处理
def process_for_display(item):
    return {
        "标题": item.title,
        "UP主": item.owner_name,
        "播放量": f"{item.view:,}",
        "链接": item.video_url,
        "热门程度": item.popularity_level
    }

# 处理并保存
processed_items = client.process_items(items, process_for_display)
client.export_items(items, format="json", file_path="examples/output/bilibili_videos.json")
```

### 合并不同来源数据

```python
# 获取不同分类数据
popular_items = client.get_model_items("popular")
weekly_items = client.get_model_items("weekly")
rank_items = client.get_model_items("rank")

# 合并数据
all_items = popular_items + weekly_items + rank_items

# 统计分析
total_views = sum(item.view for item in all_items)
avg_views = total_views / len(all_items) if all_items else 0
print(f"所有视频平均播放量: {avg_views:,.1f}")
```

## 注意事项

- API返回的条目列表通常存储在JSON字符串中，客户端会自动解析
- 图片URL需要拼接完整域名，已通过`full_pic_url`属性实现
- 不同子分类（popular、weekly、rank）数据格式相同，但内容不同
- 播放量、弹幕量等数值型字段已自动处理类型转换

## 常见问题

### Q: 获取到的数据为空怎么办？
A: 检查网络连接和API状态，确保授权令牌正确，并验证请求的sub_tab是否有效。

### Q: 如何获取更多页的数据？
A: 所有获取数据的方法都支持page参数，可以设置不同页码获取更多数据。

### Q: 视频URL和UP主URL如何构建？
A: 使用条目的`video_url`和`owner_url`属性可以直接获取完整的URL。

### Q: 如何自定义数据保存？
A: 初始化时设置`save_data=True`和`data_dir="自定义路径"`，或使用`export_items`方法导出。