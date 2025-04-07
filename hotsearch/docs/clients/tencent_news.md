# 腾讯新闻客户端 (TencentNewsClient)

`TencentNewsClient`用于获取腾讯新闻热榜数据。

## 导入

```python
from hotsearch.api import TencentNewsClient
from hotsearch.api.models.tencent_news import TencentNewsHotSearchItem, TencentNewsHotSearchResponse
```

## 初始化

```python
# 使用默认配置
client = TencentNewsClient()

# 提供自定义授权令牌（推荐）
client = TencentNewsClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = TencentNewsClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="./my_data"
)
```

## 数据模型

### TencentNewsHotSearchItem

表示单个腾讯新闻热搜条目的数据结构。

```python
@dataclass
class TencentNewsHotSearchItem:
    item_key: str  # 条目唯一标识
    title: str  # 热搜标题
    www_url: str  # 链接地址
    desc: Optional[str] = None  # 描述
    img: Optional[str] = None  # 图片URL
    is_video: Optional[bool] = None  # 是否是视频
    hot_score: Optional[int] = None  # 热度分数
    comment_num: Optional[int] = None  # 评论数
    like_num: Optional[int] = None  # 点赞数
```

### TencentNewsHotSearchResponse

表示腾讯新闻热搜的完整响应数据结构。

```python
@dataclass
class TencentNewsHotSearchResponse:
    items: List[TencentNewsHotSearchItem]  # 热搜条目列表
    platform: str  # 平台
    category: str  # 分类
    page: int  # 页码
    last_list_time: Optional[int] = None  # 上次更新时间
    next_refresh_time: Optional[int] = None  # 下次更新时间
    version: Optional[int] = None  # 版本
    total_page: Optional[int] = None  # 总页数
```

## 方法

### 获取热门新闻

```python
# 获取原始数据
data = client.get_hot(page=1)

# 获取结构化数据模型
model_data = client.get_hot(page=1, as_model=True)
```

### 获取热门新闻条目列表

```python
# 获取原始热门新闻条目
items = client.get_items(page=1)

# 获取结构化的热门新闻条目
model_items = client.get_items(page=1, as_model=True)

# 打印条目标题
for item in model_items:
    print(item.title)
```

## 使用示例

### 基本使用示例

```python
from hotsearch.api import TencentNewsClient

# 初始化客户端
client = TencentNewsClient()

# 获取结构化热搜数据
response = client.get_hot(as_model=True)

# 打印所有热搜标题
for item in response.items:
    print(f"- {item.title}")
```

### 数据处理示例

```python
# 按热度排序新闻
sorted_news = sorted(response.items, key=lambda x: x.hot_score if x.hot_score else 0, reverse=True)

# 获取热度最高的5条新闻
top_5_news = sorted_news[:5]

# 打印热度最高的5条新闻
print("热度最高的5条新闻:")
for i, item in enumerate(top_5_news, 1):
    print(f"{i}. {item.title}")
    print(f"   热度: {item.hot_score}")
    print(f"   链接: {item.www_url}")
```

## 响应说明

腾讯新闻API实际响应中，热搜条目以JSON字符串形式存储在`list`字段中，客户端会自动解析并转换为对应的数据结构。

```json
{
  "data": {
    "last_list_time": 1743821126,
    "next_refresh_time": 1743821812,
    "version": 1,
    "current_page": 1,
    "total_page": 1,
    "list": "[{\"item_key\":\"...\",\"title\":\"...\",\"www_url\":\"...\",\"desc\":\"...\",\"img\":\"...\",\"is_video\":false,\"hot_score\":123456,\"comment_num\":123,\"like_num\":456}]"
  }
}
```

## 参数说明

- `page`: 页码，固定为1
- `as_model`: 是否返回结构化数据模型，默认为False