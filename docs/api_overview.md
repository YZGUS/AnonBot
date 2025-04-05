# 热榜API概览

本文档提供了热榜API的大致分类和可用端点的概览。所有API通过统一的客户端接口访问，以提供一致的用户体验。

## API分类和可用端点

热榜API可以分为以下几个主要类别，每个类别下有不同的子分类（sub_tab）：

### 综合类

- **热榜综合** (`TopClient`)
  - 今日 (`today`)
  - 本周 (`weekly`)
  - 本月 (`monthly`)

### 新闻类

- **腾讯新闻** (`TencentNewsClient`)
  - 热门 (`hot`)
  
- **澎湃新闻** (`ThePaperClient`)
  - 热门 (`hot`)
  
- **今日头条** (`ToutiaoClient`)
  - 热门 (`hot`)
  
- **网易新闻** (`NetEaseNewsClient`)
  - 新闻 (`news`)
  - 热度榜 (`htd`)
  
- **百度热搜** (`BaiduClient`)
  - 实时热点 (`realtime`)
  - 热搜 (`phrase`)
  - 小说 (`novel`)
  - 游戏 (`game`)
  - 汽车 (`car`)
  - 电视剧 (`teleplay`)

### 财经类

- **雪球热帖** (`XueqiuClient`)
  - 话题 (`topic`)
  - 新闻 (`news`)
  - 公告 (`notice`)

### 科技类

- **掘金** (`JuejinClient`)
  - 全部 (`all`)
  - 后端 (`backend`)
  - 前端 (`frontend`)
  - 安卓 (`android`)
  - iOS (`ios`)
  - 人工智能 (`ai`)
  - 开发工具 (`dev-tools`)
  - 代码人生 (`code-life`)
  - 阅读 (`read`)

### 社区类

- **小红书** (`XiaohongshuClient`)
  - 热搜 (`hot-search`)
  
- **百度贴吧** (`BaiduTiebaClient`)
  - 热门话题 (不需要 sub_tab)

### 娱乐类

- **B站热门** (`BilibiliClient`)
  - 热门 (`popular`)
  - 每周必看 (`weekly`)
  - 排行榜 (`rank`)

## 数据模型

每个API端点返回的数据都有对应的数据模型，可以通过 `as_model=True` 参数获取结构化的模型对象：

```python
# 获取原始JSON数据
items = client.get_items(sub_tab="today")

# 获取结构化模型对象
model_items = client.get_model_items(sub_tab="today")
```

## 通用参数

大多数API支持以下通用参数：

| 参数名       | 描述                               | 默认值  | 可选值                  |
|-------------|-----------------------------------|--------|------------------------|
| `page`      | 页码                               | 1      | 正整数                  |
| `sub_tab`   | 子分类                             | 依赖API | 见各API支持的子分类      |
| `as_model`  | 是否返回结构化模型                  | False  | True/False             |
| `date_type` | 日期类型（部分API需要）             | None   | 根据API定义             |

## 客户端初始化参数

所有客户端类共享相同的初始化参数：

```python
client = XxxClient(
    auth_token=None,  # 授权令牌，格式为"Bearer xxx"
    save_data=True,   # 是否保存请求的原始数据
    data_dir="./data" # 保存数据的目录
)
```

## API请求流程

1. 客户端初始化
2. 调用特定API方法（如 `get_today`、`get_popular` 等）
3. API方法内部调用 `request` 方法向服务器发送请求
4. 处理响应数据并返回
5. 如果设置了 `save_data=True`，还会保存原始数据到指定目录

## 数据结构概览

大多数API返回的数据结构遵循以下模式：

```json
{
  "data": {
    "items": [
      {
        "title": "标题文本",
        "url": "链接地址",
        "hot_value": 12345,
        ...其他字段
      },
      ...更多条目
    ],
    "metadata": {
      ...元数据信息
    }
  },
  "code": 200,
  "message": "success"
}
```

具体的数据结构随API不同而有所差异，可使用 `HotSearchDataProcessor` 工具类分析数据结构：

```python
from hotsearch.utils import HotSearchDataProcessor

processor = HotSearchDataProcessor()
structure = processor.analyze_structure(data)
```

## 注意事项

- 所有API请求都需要授权令牌
- 大多数API支持分页，通过`page`参数指定页码
- 部分API需要额外的`date_type`参数
- 授权令牌可能会过期，建议使用自己的令牌
- 部分接口可能因上游变化而不可用
- 建议设置 `save_data=True` 保存数据以便后续分析

## 客户端列表

| 客户端类名 | 描述 | 数据源 |
|----------|------|--------|
| `TopClient` | 热榜综合 | rebang.today |
| `BaiduClient` | 百度热搜 | baidu.com |
| `BaiduTiebaClient` | 百度贴吧热门 | tieba.baidu.com |
| `BilibiliClient` | B站热门视频 | bilibili.com |
| `JuejinClient` | 掘金热门文章 | juejin.cn |
| `NetEaseNewsClient` | 网易新闻热门 | news.163.com |
| `TencentNewsClient` | 腾讯新闻热门 | news.qq.com |
| `ThePaperClient` | 澎湃新闻热门 | thepaper.cn |
| `ToutiaoClient` | 今日头条热搜 | toutiao.com |
| `XiaohongshuClient` | 小红书热搜 | xiaohongshu.com |
| `XueqiuClient` | 雪球热帖 | xueqiu.com |