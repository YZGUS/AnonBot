# 热榜API客户端文档

## 简介

热榜API客户端库提供了访问各类热榜数据的简单接口，支持多种热榜源，如热榜综合、腾讯新闻、澎湃新闻等。本文档详细介绍了客户端库的使用方法和API接口。

## 安装

```bash
# 从PyPI安装（待发布）
pip install hotsearch

# 从源码安装
git clone https://github.com/cengy/hotsearch.git
cd hotsearch
pip install -e .
```

## 基础用法

所有客户端都遵循一致的使用模式：

```python
# 1. 导入客户端类
from hotsearch.api import TopClient

# 2. 创建客户端实例
client = TopClient(
    auth_token="Bearer your-token-here",  # 授权令牌（推荐提供自己的令牌）
    save_data=True,                        # 是否保存原始数据
    data_dir="./data"                      # 数据保存目录
)

# 3. 获取数据
data = client.get_today()  # 获取今日热榜

# 4. 提取热榜条目
items = client.get_items(sub_tab="today")
for item in items[:5]:
    print(f"{item['title']} - {item['source']}")
```

## 授权令牌

所有客户端都需要授权令牌才能访问API。有两种方式提供授权令牌：

1. 初始化时传入（推荐）：
   ```python
   client = TopClient(auth_token="Bearer your-token-here")
   ```

2. 使用环境变量：
   ```python
   import os
   auth_token = os.environ.get("HOTSEARCH_AUTH_TOKEN")
   client = TopClient(auth_token=auth_token)
   ```

注意：授权令牌格式为 `"Bearer xxx"`，其中 `xxx` 是实际的令牌值。

## 客户端类层次结构

热榜API客户端采用了继承体系，为所有客户端提供一致的接口：

```
HotSearchClient (基础客户端类)
├── TopClient (热榜综合)
├── BaiduClient (百度热搜)
├── BaiduTiebaClient (百度贴吧)
├── BilibiliClient (B站热门)
├── JuejinClient (掘金)
├── NetEaseNewsClient (网易新闻)
├── TencentNewsClient (腾讯新闻)
├── ThePaperClient (澎湃新闻)
├── ToutiaoClient (今日头条)
├── XiaohongshuClient (小红书)
└── XueqiuClient (雪球热帖)
```

## 通用方法

所有客户端都提供以下通用方法：

| 方法                | 描述                                              | 参数                                           |
|--------------------|--------------------------------------------------|------------------------------------------------|
| `request()`        | 发送API请求                                       | `tab`, `sub_tab`, `page`, `version`, `date_type` |
| `get_items()`      | 获取热榜条目列表                                   | `sub_tab`, `page`, `as_model`                   |
| `get_model_items()`| 获取强类型的模型对象列表                            | `sub_tab`, `page`                              |

## 示例用法

以下是各种客户端的示例用法：

### 获取今日热榜

```python
from hotsearch.api import TopClient

client = TopClient()
data = client.get_today()
items = client.get_items(sub_tab="today")

# 打印结果
for item in items[:5]:
    print(f"{item['title']} - {item['source']}")
```

### 获取B站热门视频

```python
from hotsearch.api import BilibiliClient

client = BilibiliClient()
popular_items = client.get_model_items(sub_tab="popular")

# 打印热门视频
for item in popular_items[:5]:
    print(f"{item.title} - UP主: {item.owner_name}")
    print(f"播放量: {item.view:,} | 弹幕: {item.danmaku:,}")
```

### 获取掘金技术文章

```python
from hotsearch.api import JuejinClient

client = JuejinClient()
# 获取不同分类的文章
frontend_items = client.get_model_items(sub_tab="frontend")  # 前端
backend_items = client.get_model_items(sub_tab="backend")    # 后端
ai_items = client.get_model_items(sub_tab="ai")              # 人工智能
```

## 数据处理工具

热榜API客户端库提供了数据处理工具，用于分析保存的数据：

```python
from hotsearch.utils import HotSearchDataProcessor

# 创建数据处理器
processor = HotSearchDataProcessor(data_dir="./data")

# 加载保存的数据
data = processor.load_data("top", "today")

# 分析数据结构
structure = processor.analyze_structure(data)
print(structure)

# 提取热榜条目
items = processor.extract_items(data)
```

## 数据模型

客户端库提供了强类型的数据模型，方便进行类型检查和IDE自动补全：

```python
# 获取带类型的模型数据
bilibili_client = BilibiliClient()
videos = bilibili_client.get_model_items(sub_tab="popular")

# 使用模型属性
for video in videos[:3]:
    print(f"标题: {video.title}")
    print(f"UP主: {video.owner_name}")
    print(f"播放量: {video.view:,}")
    print(f"链接: {video.video_url}")  # 辅助属性，构建完整URL
```

## 错误处理

客户端库会处理常见的错误情况：

```python
from hotsearch.api import TopClient
import requests

try:
    client = TopClient()
    data = client.get_today()
except requests.HTTPError as e:
    print(f"HTTP错误: {e}")
except requests.ConnectionError:
    print("连接错误: 无法连接到API服务器")
except Exception as e:
    print(f"未知错误: {e}")
```

## 扩展功能

部分客户端提供了额外的扩展功能：

### 搜索和筛选

```python
# B站客户端搜索示例
bilibili_client = BilibiliClient()
game_videos = bilibili_client.search_items("游戏")
high_views = bilibili_client.get_items_by_views(min_views=1000000)
```

### 排序

```python
# B站客户端排序示例
view_sorted = bilibili_client.get_items_sorted(sort_by="view", reverse=True)
```

### 数据导出

```python
# B站客户端数据导出示例
bilibili_client.export_items(items, format="json", file_path="output.json")
bilibili_client.export_items(items, format="csv", file_path="output.csv")
```

## 详细文档

查看[客户端文档](./clients/README.md)了解每个热榜客户端的详细用法。