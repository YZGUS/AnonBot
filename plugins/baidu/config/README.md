# 百度热搜插件配置说明

本文件夹下的 `config.toml` 文件用于配置百度热搜插件的行为。

## 配置项说明

### 基本配置 (basic)

- `update_interval`：数据刷新间隔，单位为秒。设置多久获取一次新数据，减少频繁请求百度服务器。
  ```toml
  [basic]
  update_interval = 300  # 默认5分钟刷新一次
  ```

- `max_items`：默认展示的热榜条数。当用户不指定数量时，展示多少条热搜。
  ```toml
  max_items = 10  # 默认展示10条
  ```

- `log_level`：日志记录级别，可选值为 `DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`。
  ```toml
  log_level = "INFO"  # 默认INFO级别
  ```

### 访问控制 (access)

- `white_list`：用户白名单列表，只有在此列表中的用户才能使用此功能。若列表为空，则允许所有用户使用。
  ```toml
  [access]
  white_list = [12345678, 87654321]  # 允许的用户QQ号列表
  ```

- `group_white_list`：群组白名单列表，只有在此列表中的群组才能使用此功能。若列表为空，则允许所有群组使用。
  ```toml
  group_white_list = [12345678, 87654321]  # 允许的群组ID列表
  ```

### 存储设置 (storage)

- `max_files_per_day`：每天最多保存的数据文件数量。超过此数量会自动删除最早的文件。
  ```toml
  [storage]
  max_files_per_day = 20  # 每天最多保存20个数据文件
  ```

- `keep_days`：保留最近几天的数据文件。超过此天数的数据会被自动清理。
  ```toml
  keep_days = 7  # 保留最近7天的数据
  ```

### 界面设置 (ui)

- `header_template`：热搜榜单头部模板，支持 `{time}` 变量表示更新时间。
  ```toml
  [ui]
  header_template = "📊 百度热搜榜 ({time})\n\n"
  ```

- `item_template`：热搜条目模板，支持以下变量：
  - `{rank}`: 排名
  - `{highlight}`: 高亮标记
  - `{title}`: 标题
  - `{hot_tag}`: 热度标签
  ```toml
  item_template = "{rank}. {highlight}{title}{hot_tag}\n"
  ```

- `footer_template`：热搜榜单底部模板，通常包含使用提示信息。
  ```toml
  footer_template = "\n💡 提示: 发送「百度热搜 数字」可指定获取的条数，如「百度热搜 20」"
  ```

### 特定设置 (baidu_specific)

- `category_emoji`：热搜分类对应的表情符号映射，用于美化分类展示。
  ```toml
  [baidu_specific]
  category_emoji = { "热" = "🔥", "新" = "✨", "爆" = "💥", "沸" = "♨️", "商" = "🛒", "娱" = "🎬", "体" = "⚽", "情" = "💖" }
  ```

## 完整配置示例

```toml
[basic]
update_interval = 300  # 数据刷新间隔(秒)
max_items = 10         # 默认展示条数
log_level = "INFO"     # 日志级别

[access]
white_list = []        # 用户白名单，为空表示允许所有用户
group_white_list = []  # 群组白名单，为空表示允许所有群组

[storage]
max_files_per_day = 20 # 每天最多保存的文件数
keep_days = 7          # 保留最近几天的数据

[ui]
header_template = "📊 百度热搜榜 ({time})\n\n"
item_template = "{rank}. {highlight}{title}{hot_tag}\n"
footer_template = "\n💡 提示: 发送「百度热搜 数字」可指定获取的条数，如「百度热搜 20」"

[baidu_specific]
category_emoji = { "热" = "🔥", "新" = "✨", "爆" = "💥", "沸" = "♨️", "商" = "🛒", "娱" = "🎬", "体" = "⚽", "情" = "💖" }
```

## 使用说明

用户可以发送以下消息触发插件功能：

- `百度热搜`：获取默认条数的百度热搜榜
- `百度热搜 20`：获取指定条数（此例中为20条）的百度热搜榜
- `百度热搜 详情` 或 `百度热搜 -d`：获取带有详细信息和链接的热搜榜
- `百度热搜 20 详情`：组合使用，获取20条带详情的热搜数据

## 错误排查

如果遇到问题，请检查：

1. 确保网络连接正常，能够访问百度网站
2. 检查日志输出，查看是否有错误信息
3. 确认用户或群组是否在白名单内（如设置了白名单）
4. 检查配置文件格式是否正确，尤其是括号、引号等符号

## 高级使用

- 调整 `update_interval` 可以平衡实时性和服务器压力
- 通过 `log_level` 设置为 "DEBUG" 可以查看更详细的日志，方便排查问题
- 定制 `item_template` 可以改变热搜条目的展示样式 