# 网易新闻客户端 (NetEaseNewsClient)

`NetEaseNewsClient`用于获取网易新闻热榜数据。

## 导入

```python
from hotsearch.api import NetEaseNewsClient
from hotsearch.api.models.ne_news import NetEaseNewsHotSearchItem, NetEaseNewsHotSearchResponse
```

## 初始化

```python
# 使用默认配置
client = NetEaseNewsClient()

# 提供自定义授权令牌（推荐）
client = NetEaseNewsClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = NetEaseNewsClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="./my_data"
)
```

## 方法

### 获取热门新闻

```python
# 获取原始数据
data = client.get_hot(page=1)

# 获取结构化数据
response = client.get_hot(page=1, as_model=True)
```

### 获取新闻

```python
# 获取原始数据
data = client.get_news(page=1)

# 获取结构化数据
response = client.get_news(page=1, as_model=True)
```

### 获取新闻条目列表

```python
# 获取原始数据条目
items = client.get_items(sub_tab="news", page=1)

# 获取结构化数据条目
items = client.get_items(sub_tab="news", page=1, as_model=True)

# 打印条目标题
for item in items:
    if isinstance(item, dict):
        print(item["title"])
    else:
        print(item.title)
```

## 数据模型

### NetEaseNewsHotSearchItem

表示单个网易新闻热搜条目的数据结构。

```python
@dataclass
class NetEaseNewsHotSearchItem:
    item_key: str  # 条目唯一标识
    title: str  # 热搜标题
    www_url: str  # 链接地址
    source: Optional[str] = None  # 来源
    img: Optional[str] = None  # 图片URL
    reply_count: Optional[int] = None  # 回复数
    hot_score: Optional[int] = None  # 热度分数
    hot_comment: Optional[str] = None  # 热门评论
    is_video: Optional[bool] = None  # 是否视频
    duration_str: Optional[str] = None  # 视频时长
```

### NetEaseNewsHotSearchResponse

表示完整的网易新闻热搜响应，包含热搜条目列表和元数据。

```python
@dataclass
class NetEaseNewsHotSearchResponse:
    items: List[NetEaseNewsHotSearchItem]  # 热搜条目列表
    platform: str  # 平台名称
    category: str  # 分类
    page: int  # 页码
    last_list_time: Optional[int] = None  # 上次列表时间
    next_refresh_time: Optional[int] = None  # 下次刷新时间
    version: Optional[int] = None  # 版本
    total_page: Optional[int] = None  # 总页数
```

## 使用示例

### 基本使用

```python
from hotsearch.api import NetEaseNewsClient

# 初始化客户端
client = NetEaseNewsClient()

# 获取热门新闻
hot_news = client.get_hot(as_model=True)

# 打印热门新闻标题
for item in hot_news.items:
    print(f"标题: {item.title}")
    if item.hot_score:
        print(f"热度: {item.hot_score}")
    print(f"链接: {item.www_url}")
    print("---")
```

### 数据处理示例

```python
from hotsearch.api import NetEaseNewsClient

# 初始化客户端
client = NetEaseNewsClient()

# 获取热门新闻
response = client.get_hot(as_model=True)

# 按热度排序新闻
sorted_news = sorted(response.items, key=lambda x: x.hot_score if x.hot_score else 0, reverse=True)

# 过滤视频新闻
video_news = [item for item in response.items if item.is_video]

# 打印热度最高的5条新闻
print("热度最高的5条新闻:")
for i, item in enumerate(sorted_news[:5], 1):
    print(f"{i}. {item.title}")
    print(f"   热度: {item.hot_score}")
    print(f"   链接: {item.www_url}")
    print("---")
```

## 参数说明

- `page`: 页码，固定为1
- `as_model`: 是否返回结构化模型对象，默认为False
- `sub_tab`: 子分类，可选值：news(新闻), htd(热度榜)

## 响应格式

### 原始响应格式

原始API响应的JSON格式如下：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "last_list_time": 1743820475,
    "next_refresh_time": 1743821088,
    "version": 1,
    "current_page": 1,
    "total_page": 1,
    "list": "[{\"item_key\":\"d07e8dc000adcf6d1b89efe934a2f28d\",\"title\":\"中方：对原产于美国的进口商品加征34%关税\",\"www_url\":\"https://c.m.163.com/news/a/JSAOFGBE0001899O.html\",\"img\":\"short-lived/2025/04/ne_news/a9151153782a47077fcde3e33d05b9bf.png\",\"hot_comment\":\"\",\"source\":\"北京日报客户端\",\"reply_count\":35290,\"hot_score\":6000,\"is_video\":false,\"duration_str\":\"\"}]"
  }
}
```

注意：`list`字段实际上是一个JSON字符串，需要使用`json.loads()`解析。

### 结构化响应格式

使用`as_model=True`时，返回的结构化对象可以序列化为以下JSON格式：

```json
{
  "platform": "ne-news",
  "category": "htd",
  "page": 1,
  "last_list_time": 1743820475,
  "next_refresh_time": 1743821088,
  "version": 1,
  "total_page": 1,
  "items": [
    {
      "item_key": "d07e8dc000adcf6d1b89efe934a2f28d",
      "title": "中方：对原产于美国的进口商品加征34%关税",
      "www_url": "https://c.m.163.com/news/a/JSAOFGBE0001899O.html",
      "source": "北京日报客户端",
      "img": "short-lived/2025/04/ne_news/a9151153782a47077fcde3e33d05b9bf.png",
      "reply_count": 35290,
      "hot_score": 6000,
      "hot_comment": "",
      "is_video": false,
      "duration_str": ""
    }
  ]
}
```

## 数据字段说明

- `item_key`: 条目唯一标识
- `title`: 新闻标题
- `www_url`: 新闻链接
- `source`: 新闻来源
- `img`: 图片URL
- `reply_count`: 回复数
- `hot_score`: 热度分数
- `hot_comment`: 热门评论
- `is_video`: 是否是视频
- `duration_str`: 视频时长