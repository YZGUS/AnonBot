# 网易新闻热榜插件

## 功能描述

网易新闻热榜插件用于自动获取网易新闻平台实时热榜数据，支持以下功能：

1. 获取实时热搜前50条（排名、标题、热度值、标签类型）
2. 获取热门话题前10条（标题、热度趋势、关联内容）
3. 每个话题下前10条高互动评论（内容、点赞量、用户昵称、发布时间）
4. 支持新闻详情查询（标题、内容摘要、来源、发布时间）

## 使用方法

在群聊或私聊中发送以下命令：

- `网易热榜`：获取当前网易新闻热榜数据（默认前10条）
- `网易热榜 20`：获取前20条网易新闻热榜数据
- `网易热点`：获取当前热门话题
- `网易新闻 [关键词]`：获取指定关键词的新闻详情

## 配置说明

配置文件位于`config/config.toml`，包含以下配置项：

```toml
# 白名单配置
[whitelist]
# 允许查看网易新闻热榜的群组ID列表
group_ids = [123456789]
# 允许查看网易新闻热榜的用户ID列表
user_ids = [123456789]

# 数据配置
[data]
# 保存的热榜数量
hot_count = 50
# 热门话题数量
hot_topic_count = 10
# 每个话题保存的评论数量
comment_count = 10
# 数据更新间隔(秒)
update_interval = 300
```

## 请求头配置

请求头配置文件位于`config/headers.json`，用于配置访问网易新闻API的HTTP请求头信息。默认已包含基本的请求头设置，一般情况下无需修改。

如需自定义，请参考以下格式：

```json
{
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
  "Accept-Encoding": "gzip, deflate, br",
  "Connection": "keep-alive",
  "Upgrade-Insecure-Requests": "1",
  "Referer": "https://news.163.com/"
}
```

## 数据存储

热榜数据会按照`年月日-小时`的格式保存在`data`目录下的子文件夹中，采用JSON格式存储，文件名格式为`netease_news_年月日_时分秒.json`。

## 注意事项

1. 请确保网络环境能够正常访问网易新闻网站
2. 如遇到API访问限制，可能需要更新请求头配置
3. 为避免请求过于频繁导致IP被限制，请合理设置更新间隔 