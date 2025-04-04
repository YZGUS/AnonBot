# 知乎热榜插件

## 功能描述

知乎热榜插件用于获取知乎平台实时热榜数据，支持查看热门问题以及问题详情。

## 使用方法

在群聊或私聊中发送以下命令：

- `知乎热榜`：获取当前知乎热榜数据（默认前10条）
- `知乎热榜 [数量]`：获取指定数量的知乎热榜数据（例如：`知乎热榜 20`）
- `知乎问题 [问题ID]`：获取指定问题的详细信息和回答

## 配置文件

本插件有两个主要配置文件:

1. `config.toml` - 插件基本配置，包括白名单和数据限制
2. `headers.json` - 请求头配置，用于爬取知乎数据

## 配置项说明

### config.toml

```toml
# 白名单配置
[whitelist]
# 允许查看知乎热榜的群组ID列表
group_ids = [群号1, 群号2, ...]
# 允许查看知乎热榜的用户ID列表
user_ids = [QQ号1, QQ号2, ...]

# 数据配置
[data]
# 保存的热榜数量
hot_count = 50
# 每个问题保存的回答数量
answer_count = 10
```

### headers.json

包含爬取知乎网站所需的HTTP请求头，可根据需要自行修改以避免被反爬虫机制拦截。

## 使用方法

1. 将 `config.example.toml` 复制为 `config.toml` 并修改相应配置
2. 可以根据需要修改 `headers.json` 中的请求头信息

## 注意事项

- 请适当设置爬取频率，避免对知乎服务器造成过大压力
- 定期更新请求头信息可以降低被封禁的风险
- 数据仅用于个人学习和交流，请遵守知乎用户协议

### headers.json 配置说明

`headers.json` 文件包含访问知乎网站所需的HTTP请求头信息，**该文件不应提交到Git仓库**，因为它可能包含您的个人Cookie等敏感信息。

#### 使用方法

1. 复制 `config.example.toml` 为 `config.toml` 并根据需要修改
2. 创建 `headers.json` 文件，填入以下必要的请求头内容：

```json
{
  "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
  "accept-language": "zh-CN,zh;q=0.9",
  "cache-control": "max-age=0",
  "sec-ch-ua": "...",
  "sec-ch-ua-mobile": "?0",
  "sec-ch-ua-platform": "\"Windows\"",
  "sec-fetch-dest": "document",
  "sec-fetch-mode": "navigate",
  "sec-fetch-site": "none",
  "sec-fetch-user": "?1",
  "upgrade-insecure-requests": "1",
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
```

#### 获取最佳效果

为了获取更好的爬取效果，建议添加Cookie字段：

1. 使用浏览器登录知乎
2. 打开浏览器开发者工具(F12)，查看网络请求中的Headers
3. 复制请求头中的Cookie字段，添加到headers.json中
4. 完整的headers.json应类似于：

```json
{
  "accept": "...",
  "accept-language": "...",
  // 其他字段
  "user-agent": "...",
  "Cookie": "your_cookie_here"
}
```

**注意**: Cookie可能包含您的个人信息，请勿分享或提交到公共仓库。

### 调试模式

如果需要调试爬取过程，可在主要Python文件中修改`debug_mode`为`True`：

```python
# 在ZhihuPlugin类中设置
self.debug_mode = True  # 开启调试模式，会保存中间数据
```