# 微博热榜插件

微博热榜插件可以定时获取微博热搜榜单，并通过机器人进行展示。

## 功能特点

- 每小时自动获取最新的微博热搜榜单
- 数据持久化存储，按照"年月日-小时"格式保存
- 支持白名单权限控制，可配置允许使用的群组和用户
- 支持定制显示条目数量

## 安装与配置

### 配置文件

插件使用两个主要配置文件：

#### 1. config.toml

```toml
# 微博热榜配置

# 白名单配置
[whitelist]
# 允许查看微博热榜的群组ID列表
group_ids = [123456789]
# 允许查看微博热榜的用户ID列表
user_ids = [987654321]

# 数据配置
[data]
# 保存的热榜数量
hot_count = 10
# 每个话题保存的评论数量
comment_count = 10
```

#### 2. headers.json

用于配置请求头信息，**必须包含有效的Cookie**才能正常访问微博API。

```json
{
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
  "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
  "Accept-Encoding": "gzip, deflate, br",
  "Connection": "keep-alive",
  "Upgrade-Insecure-Requests": "1",
  "Cookie": "这里填入您的微博Cookie"
}
```

### 配置说明

1. **白名单配置**
   - `group_ids`: 允许使用插件的QQ群ID列表
   - `user_ids`: 允许使用插件的QQ用户ID列表

2. **数据配置**
   - `hot_count`: 热榜展示的条目数量
   - `comment_count`: 每个话题保存的相关微博或评论数量

### 获取微博Cookie

1. 使用Chrome或Edge浏览器登录微博网站(https://weibo.com)
2. 按F12打开开发者工具，切换到"网络"或"Network"标签页
3. 刷新页面，选择任意一个请求
4. 在请求头(Headers)中找到Cookie字段，复制完整内容
5. 将复制的内容粘贴到headers.json的Cookie字段中

> **重要提示**：Cookie中包含您的登录凭据，请勿分享给他人

## 使用方法

插件支持以下命令：

- `微博热榜`: 获取最新的微博热搜榜单

## 数据存储

热榜数据按照以下格式存储：

```
plugins\weibo\data\年月日-小时\weibo_hot_年月日_时分秒.json
```

例如：
```
plugins\weibo\data\20250402-23\weibo_hot_20250402_231035.json
```

## 常见问题

1. **无法获取微博热榜**
   - 检查Cookie是否有效
   - 检查网络连接是否正常
   - 查看日志文件了解详细错误信息

2. **插件无响应**
   - 确认用户或群组ID是否在白名单中
   - 检查机器人是否正常运行

3. **数据过期**
   - 插件每小时自动更新一次数据
   - 可以手动重启插件触发立即更新 