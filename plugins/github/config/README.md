# GitHub插件

本目录用于存放GitHub插件的相关配置文件。

## 目录说明

GitHub插件主要用于获取GitHub趋势项目信息，目前不需要特定配置文件。插件会自动获取GitHub Trending页面的内容并解析。

## 数据存储

- 获取的Trending数据会存储在 `trending` 目录下，以时间戳命名
- 日志信息会存储在 `logs` 目录下

## 插件功能

插件支持以下指令：

- `Github` - 测试插件是否正常工作
- `Github Trending` - 获取并展示当前GitHub热门项目

## 未来扩展

如需添加GitHub API访问功能，可在此目录中添加以下配置：

```toml
# GitHub API配置示例
[api]
token = "你的GitHub个人访问令牌"
``` 