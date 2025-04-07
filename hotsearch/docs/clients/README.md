# 热榜API客户端文档

本目录包含了所有热榜API客户端的详细使用文档。每个客户端对应一种热榜数据源。

## 客户端列表

- [热榜综合 (TopClient)](top.md)
- [腾讯新闻 (TencentNewsClient)](tencent_news.md)
- [澎湃新闻 (ThePaperClient)](thepaper.md)
- [今日头条 (ToutiaoClient)](toutiao.md)
- [网易新闻 (NetEaseNewsClient)](ne_news.md)
- [百度热搜 (BaiduClient)](baidu.md)
- [小红书 (XiaohongshuClient)](xiaohongshu.md)
- [雪球热帖 (XueqiuClient)](xueqiu.md)
- [掘金 (JuejinClient)](juejin.md)
- [B站热门 (BilibiliClient)](bilibili.md)

## 基础客户端类

所有特定热榜客户端都继承自`HotSearchClient`基础类。该类提供了与热榜API交互的核心功能。

### 初始化参数

```python
HotSearchClient(
    auth_token: Optional[str] = None,  # 授权令牌，格式为"Bearer xxx"
    save_data: bool = True,            # 是否保存请求的原始数据
    data_dir: str = "./data"           # 保存数据的目录
)
```

### 通用方法

- `get_items()`: 获取热榜条目列表
- `get_model_items()`: 获取强类型的模型对象列表（仅部分客户端支持，如B站客户端）
- `search_items()`: 搜索特定关键词的条目（增强型客户端）
- `export_items()`: 导出条目数据为JSON或CSV格式（增强型客户端）
- `process_items()`: 使用自定义函数批量处理条目数据（增强型客户端）

### 注意事项

- 强烈建议提供自己的`auth_token`，默认令牌可能会过期
- 使用`save_data=True`可以将数据保存到本地供分析使用
- 所有客户端共享相同的初始化参数
- 部分客户端（如B站客户端）提供了增强功能，包括条目筛选、排序和数据导出

## 数据模型

每个客户端都有对应的数据模型，用于结构化处理返回的数据。这些模型位于`hotsearch.api.models`包中，例如：

```python
from hotsearch.api.models.baidu import BaiduHotSearchItem, BaiduHotSearchResponse
from hotsearch.api.models.ne_news import NetEaseNewsHotSearchItem, NetEaseNewsHotSearchResponse
from hotsearch.api.models.tencent_news import TencentNewsHotSearchItem, TencentNewsHotSearchResponse
from hotsearch.api.models.xiaohongshu import XiaohongshuHotSearch, XiaohongshuHotSearchItem
```

### 模型结构

通常每个平台的数据模型包含两类：
1. **条目模型**：代表单个热搜/热榜条目，如`BaiduHotSearchItem`、`NetEaseNewsHotSearchItem`等
2. **响应模型**：包含完整的API响应，包括条目列表和元数据，如`BaiduHotSearchResponse`、`NetEaseNewsHotSearchResponse`等

这些模型提供了以下便利：
- 类型提示和自动补全
- 字段验证和默认值处理
- 辅助属性和方法，简化数据访问
- 统一的数据访问接口

### 使用模型数据

所有客户端都提供了`as_model=True`参数选项，可以直接返回结构化模型而非原始JSON数据：

```python
# 获取结构化模型数据
response = client.get_hot(as_model=True)

# 访问模型属性
for item in response.items:
    print(f"标题: {item.title}")
    print(f"链接: {item.www_url}")
```

## 响应格式

每个客户端文档中都包含了对应的请求方法、参数说明和响应示例。部分客户端还提供了示例代码，展示如何处理不同类型的数据。