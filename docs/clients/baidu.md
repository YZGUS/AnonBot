# 百度热搜客户端 (BaiduClient)

`BaiduClient`用于获取百度热搜数据，包括实时热点、热搜词、小说热搜等多个分类。

## 导入

```python
from hotsearch.api import BaiduClient
from hotsearch.api.models.baidu import BaiduHotSearchItem, BaiduHotSearchResponse
```

## 初始化

```python
# 使用默认配置
client = BaiduClient()

# 提供自定义授权令牌（推荐）
client = BaiduClient(auth_token="Bearer your-token-here")

# 自定义数据保存
client = BaiduClient(
    auth_token="Bearer your-token-here",
    save_data=True,
    data_dir="./my_data"
)
```

## 方法

### 获取实时热点

```python
# 获取原始数据
data = client.get_realtime(page=1)

# 获取结构化模型
response = client.get_realtime(page=1, as_model=True)
```

### 获取热搜词

```python
# 获取原始数据
data = client.get_phrase(page=1)

# 获取结构化模型
response = client.get_phrase(page=1, as_model=True)
```

### 获取小说热搜

```python
# 获取原始数据
data = client.get_novel(page=1)

# 获取结构化模型
response = client.get_novel(page=1, as_model=True)
```

### 获取游戏热搜

```python
# 获取原始数据
data = client.get_game(page=1)

# 获取结构化模型
response = client.get_game(page=1, as_model=True)
```

### 获取汽车热搜

```python
# 获取原始数据
data = client.get_car(page=1)

# 获取结构化模型
response = client.get_car(page=1, as_model=True)
```

### 获取电视剧热搜

```python
# 获取原始数据
data = client.get_teleplay(page=1)

# 获取结构化模型
response = client.get_teleplay(page=1, as_model=True)
```

### 获取热搜条目列表

```python
# 实时热点条目（原始数据）
items = client.get_items(sub_tab="realtime", page=1)

# 热搜词条目（结构化模型）
items = client.get_items(sub_tab="phrase", page=1, as_model=True)

# 打印原始数据条目标题
for item in items:
    if isinstance(item, dict):
        print(item["word"])
    else:
        print(item.word)
```

## 数据模型

### BaiduHotSearchItem

表示单个百度热搜条目的数据结构。

```python
@dataclass
class BaiduHotSearchItem:
    item_key: str
    word: str
    desc: str
    query: str
    hot_score: Optional[str] = None
    hot_tag: Optional[str] = None
    hot_change: Optional[str] = None
    img: Optional[str] = None
    expression: Optional[str] = None
    show: Optional[List[Any]] = None
```

### BaiduHotSearchResponse

表示完整的百度热搜响应，包含热搜条目列表和元数据。

```python
@dataclass
class BaiduHotSearchResponse:
    items: List[BaiduHotSearchItem]
    tab: str
    sub_tab: str
    page: int
    last_list_time: Optional[int] = None
    next_refresh_time: Optional[int] = None
    version: Optional[int] = None
```

## 使用示例

### 基本使用

```python
from hotsearch.api import BaiduClient
from hotsearch.api.models.baidu import BaiduHotSearchItem

# 初始化客户端
client = BaiduClient()

# 获取实时热点（结构化模型）
realtime = client.get_realtime(as_model=True)

# 打印热搜标题
for item in realtime.items:
    print(f"标题: {item.word}")
    print(f"描述: {item.desc}")
    print(f"热度: {item.hot_score}")
    print("---")
```

### 数据处理示例

```python
from hotsearch.api import BaiduClient

# 初始化客户端
client = BaiduClient()

# 获取不同分类的热搜条目
realtime_items = client.get_items(sub_tab="realtime", as_model=True)
novel_items = client.get_items(sub_tab="novel", as_model=True)
game_items = client.get_items(sub_tab="game", as_model=True)

# 打印所有分类的前3个热搜条目
print("实时热点前3条:")
for i, item in enumerate(realtime_items[:3], 1):
    print(f"{i}. {item.word}")

print("\n小说热搜前3条:")
for i, item in enumerate(novel_items[:3], 1):
    print(f"{i}. {item.word}")

print("\n游戏热搜前3条:")
for i, item in enumerate(game_items[:3], 1):
    print(f"{i}. {item.word}")
```

## 参数说明

- `sub_tab`: 子分类，可选值：`realtime`（实时热点）, `phrase`（热搜词）, `novel`（小说热搜）, `game`（游戏热搜）, `car`（汽车热搜）, `teleplay`（电视剧热搜）
- `page`: 页码，固定为1
- `as_model`: 是否返回结构化模型对象，默认为False

## 响应格式

### 原始响应格式

原始API响应的JSON格式如下：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "current_page": 1,
    "last_list_time": 1743823569,
    "next_refresh_time": 1743824169,
    "version": 1,
    "list": "[{\"item_key\":\"4c5b4a2e21a4427ce5a5a42ec23d3110\",\"word\":\"百度热榜\",\"desc\":\"一站式了解全网实时热点\",\"query\":\"百度热榜\",\"hot_score\":\"999999\",\"hot_tag\":\"沸\"}]"
  }
}
```

注意：`list`字段实际上是一个JSON字符串，需要使用`json.loads()`解析。

### 结构化响应格式

使用`as_model=True`时，返回的结构化对象可以序列化为以下JSON格式：

```json
{
  "tab": "baidu",
  "sub_tab": "realtime",
  "page": 1,
  "last_list_time": 1743823569,
  "next_refresh_time": 1743824169,
  "version": 1,
  "items": [
    {
      "item_key": "4c5b4a2e21a4427ce5a5a42ec23d3110",
      "word": "百度热榜",
      "desc": "一站式了解全网实时热点",
      "query": "百度热榜",
      "hot_score": "999999",
      "hot_tag": "沸",
      "hot_change": null,
      "img": null,
      "expression": null,
      "show": []
    }
  ]
}
```

## 数据字段说明

- `item_key`: 条目唯一标识
- `word`: 热搜标题
- `desc`: 热搜描述
- `query`: 查询关键词
- `hot_score`: 热度分数
- `hot_tag`: 热度标签，如"沸"、"热"等
- `hot_change`: 热度变化情况
- `img`: 图片URL（如果有）
- `expression`: 表情符号（如果有）
- `show`: 显示属性列表（通常为空）