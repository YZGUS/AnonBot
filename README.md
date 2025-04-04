# AnonBot

AnonBot是一个基于NapCatQQ框架的QQ机器人，提供多种实用功能插件。

## 使用方式

- 如果使用Mac系统，请安装 dist 目录中的 [ncatbot-3.5.7-py3-none-any.whl](dist/ncatbot-3.5.7-py3-none-any.whl)，本项目来源 [NCatBot](https://docs.ncatbot.xyz/guide/kfcvme50/)。
- 服务启动前需要先启动 [NapCatQQ 服务](https://napneko.github.io/guide/napcat)

## 功能插件

AnonBot 包含以下插件：

### 1. 情感支持插件

自动检测消息中的负面情绪，并生成符合千早爱音角色设定的安慰回复。

- **指令**：无需手动触发，自动监测情绪值低的消息
- **配置**：需要设置 DeepSeek API 密钥和白名单
- **目录**：`plugins\emotional_support`
- **特性**：
  - 使用 SnowNLP 进行情感分析，阈值可配置
  - 通过 DeepSeek API 生成符合角色设定的回复
  - 提供丰富的表情符号和多层次情感互动
  - 会自动忽略多种命令前缀，避免误触发，包括：
    - 音乐相关：`点歌`、`music`、`歌曲`
    - AI相关：`ds `、`ai `
    - 社交平台：`Github`、`微博热榜`、`抖音热榜`等
    - 查询类命令：`查询记录`、`搜索`、`帮助`等
    - 特殊字符开头：`/`、`@`、`#`、`.`
    - 系统功能相关：`/cr_`、`设置`、`config`等
    - 热榜相关：`热榜`、`热搜`、`排行榜`等
    - 其他功能：`天气`、`提醒`、`翻译`等

### 2. GitHub插件

获取 GitHub 趋势项目信息，展示热门开源仓库。

- **指令**：
  - `Github` - 测试插件是否正常工作
  - `Github Trending` - 获取并展示当前GitHub热门项目
- **配置**：无需特殊配置，自动获取数据
- **目录**：`plugins\github`

### 3. KFC疯狂星期四插件

在星期四自动响应相关关键词，发送随机KFC文案。

- **指令**：无需特定指令，星期四时包含关键词自动触发
- **关键词**：KFC、kfc、肯德基、兄弟、垃圾
- **目录**：`plugins\kfc`

### 4. 微博热榜插件

定时获取微博热搜榜单，可查询当前热门话题。

- **指令**：`微博热榜` - 获取最新的微博热搜榜单
- **配置**：需要设置有效的微博Cookie和白名单
- **目录**：`plugins\weibo`

### 5. 抖音热榜插件

获取抖音热门视频和话题。

- **指令**：
  - `抖音热榜` - 获取当前抖音热榜数据（默认前10条）
  - `抖音热榜 [数量]` - 获取指定数量的抖音热榜数据（如：`抖音热榜 20`）
  - `抖音热榜话题` - 获取当前热门话题
  - `抖音话题详情 [关键词]` - 获取指定话题的详细信息和评论
- **目录**：`plugins\douyin`

### 6. 知乎热榜插件

获取知乎热门问题和话题。

- **指令**：
  - `知乎热榜` - 获取知乎热门问题（默认前10条）
  - `知乎热榜 [数量]` - 获取指定数量的知乎热榜问题
  - `知乎问题 [问题ID]` - 获取特定问题的详细信息和回答
- **目录**：`plugins\zhihu`

### 7. 百度热搜插件

获取百度实时热搜榜数据，了解当前热门话题和事件。

- **指令**：
  - `百度热搜` - 获取默认数量的百度热搜数据（默认10条）
  - `百度热搜 [数量]` - 获取指定数量的热搜数据（如：`百度热搜 20`）
  - `百度热搜 详情` 或 `百度热搜 -d` - 获取带有详细信息的热搜数据，包括链接
  - `百度热搜 20 详情` - 组合使用，获取20条带详情的热搜数据
- **特性**：
  - 支持缓存机制，减少请求次数，缓存时间可配置
  - 自动识别热搜分类并添加相应表情标签
  - 高亮显示特别关注的热点话题
  - 美观的排版，前三名使用奖牌表情
  - 数据持久化存储，支持按日期归档和自动清理
  - 权限控制，支持用户和群组白名单
- **配置**：
  - 可配置刷新间隔、最大显示条数、日志级别等
  - 可自定义模板和表情映射
- **目录**：`plugins\baidu`

### 8. 音乐卡片插件

生成并发送音乐分享卡片。

- **指令**：
  - `点歌 [歌名]` - 使用指定关键词搜索并发送音乐卡片
  - `/msearch [歌名]` - 旧版命令，功能同上
- **目录**：`plugins\musiccard`

### 9. DeepSeek AI插件

调用DeepSeek AI接口进行对话。

- **指令**：
  - `ds [问题]` - 通过前缀命令触发AI对话
  - `@机器人 [问题]` - 通过@机器人触发AI对话
  - **记忆控制**：
    - `ds memory on` - 开启记忆模式
    - `ds memory off` - 关闭记忆模式
    - `ds memory clear` - 清空对话历史
    - `ds memory status` - 查看记忆状态
- **配置**：需要设置DeepSeek API密钥
- **目录**：`plugins\deepseek`

### 10. 聊天记录插件

保存和查询群聊聊天记录。

- **群聊功能**：自动记录群聊消息，包括文本、图片、音频等
- **私聊命令**（仅限超级管理员）：
  - `/cr_list_users` - 列出所有有记录的用户
  - `/cr_select_user [用户ID]` - 选择要锐评的用户
  - `/cr_set_style [风格]` - 设置锐评风格 (sunba/nuclear/nga/zhihu)
  - `/cr_criticize` - 对选中的用户进行锐评
  - `/cr_help` - 显示帮助信息
- **目录**：`plugins\chatrecord`

## 插件开发规范

如果您希望为AnonBot开发新插件，请遵循以下规范：

### 文件结构

```
plugins\插件名称\
├── __init__.py      # 插件初始化文件
├── main.py          # 插件主文件
├── config\          # 配置目录
│   ├── config.toml  # 配置文件
│   └── README.md    # 配置说明
└── data\            # 数据存储目录
```

### 命名规范

- 插件名称使用全小写英文，如 `emotional_support`
- 类名使用驼峰命名法，如 `EmotionalSupportPlugin`
- 函数名使用下划线命名法，如 `get_content`

### 文档规范

- 每个插件必须在 `config\README.md` 中提供完整的使用说明
- 说明文档应包含：功能介绍、配置方法、使用示例、注意事项等

### 代码风格

- 使用中文作为注释和输出文本
- 避免使用斜杠"/"作为路径分隔符，优先使用反斜杠"\"
- 提供清晰的错误处理和日志输出

## 风格指南

为保持一致的用户体验，所有插件应遵循以下风格指引：

```
# 提示词风格指南

## 文本格式
1. 使用中文进行交流，专业术语除外
2. 避免使用斜杠"/"，使用反斜杠"\"作为路径分隔符
3. 多使用表情符号增强表达，如"✅ 成功"、"❌ 失败"

## 回复格式
1. 使用简明扼要的语句
2. 关键信息使用加粗或引用突出
3. 列表项使用中文序号或符号（一、二、三或•）
4. 错误信息应包含解决建议

## 示例指令风格
✅ 正确：`微博热榜`、`点歌 千本樱`
❌ 错误：`/weibo/hot`、`/music 千本樱`

## 文档风格
1. 使用二级标题作为主要分隔
2. 配置示例使用代码块格式
3. 重要提示使用引用格式
4. 避免过长的段落，保持简洁
```

## 许可证

本项目采用 [LICENSE](LICENSE) 许可证。

# 热榜 Today 爬虫工具

这是一个用于抓取 [热榜 Today](https://rebang.today) 网站各个标签页热榜数据的Python工具。该工具支持抓取网站上所有可用的标签页数据，并能识别带有红框标记的特别关注内容。

## 功能特点

- 支持抓取所有标签页的热榜数据
- 能够识别带有红框标记的特别关注内容
- 提供Python API和命令行接口
- 返回JSON格式的数据便于处理和分析
- 完善的错误处理和日志记录

## 安装

### 环境要求

- Python 3.6+
- 需要安装的依赖包：selenium, beautifulsoup4, requests

### 使用Conda环境安装

1. 创建并激活Conda环境

```bash
conda env create -f environment.yml
conda activate AnonBot
```

2. 安装模块（开发模式）

```bash
pip install -e .
```

## 使用方法

### Python API

```python
from rebang.scraper import get_tab_data, get_tab_data_json

# 获取数据（返回字典）
data = get_tab_data("hupu")
print(f"共获取到 {len(data['hot_items'])} 条虎扑热榜内容")

# 获取数据（返回JSON字符串）
json_data = get_tab_data_json("tencent-news")
print(json_data)
```

### 命令行接口

```bash
# 获取虎扑热榜数据并保存到文件
python -m rebang.cli --tab hupu --output hupu_data.json

# 获取腾讯新闻热榜并输出到控制台
python -m rebang.cli --tab tencent-news

# 列出所有可用的标签
python -m rebang.cli --tab hupu --list

# 详细模式（显示更多日志信息）
python -m rebang.cli --tab douban-community --verbose

# 安静模式（只显示错误信息）
python -m rebang.cli --tab zhihu --quiet
```

## 可用标签列表

热榜 Today 网站目前支持以下标签：

### 社交媒体
- weibo - 微博
- douyin - 抖音
- xiaohongshu - 小红书
- bilibili - B站

### 科技
- ithome - IT之家
- ifanr - 爱范儿
- 36kr - 36氪
- landian - 蓝点网
- appinn - 小众软件
- apprcn - 反斗软件
- journal-tech - 技术期刊
- github - GitHub
- juejin - 掘金

### 社区论坛
- douban-community - 豆瓣社区
- hupu - 虎扑
- baidu-tieba - 百度贴吧
- douban-media - 豆瓣影视
- 52pojie - 吾爱破解
- guancha-user - 观察者网

### 新闻资讯
- tencent-news - 腾讯新闻
- thepaper - 澎湃新闻
- toutiao - 今日头条
- ne-news - 网易新闻
- penti - 喷嚏网

### 财经
- xueqiu - 雪球
- smzdm - 什么值得买

### 知识文化
- zhihu - 知乎
- zhihu-daily - 知乎日报
- weread - 微信读书
- huxiu - 虎嗅
- sspai - 少数派

### 体育游戏
- zhibo8 - 直播吧
- gamersky - 游民星空
- xmyp - 小米有品

### 综合
- top - 热榜首页
- baidu - 百度

## 测试

运行测试用例以验证模块功能：

```bash
# 运行所有测试
python -m unittest discover tests

# 运行特定测试
python -m tests.test_scraper
```

## 贡献

欢迎提交问题报告和功能建议，也欢迎提交代码贡献。

## 许可证

MIT License