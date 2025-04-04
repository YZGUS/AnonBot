# DeepSeek AI插件

本目录包含DeepSeek AI插件的配置文件。

## 主要配置文件

- `config.toml` - 包含插件的核心配置
  - API密钥
  - 白名单用户和群组
  - 模型参数设置

注意：该配置文件包含敏感信息（API密钥等），已在 `.gitignore` 中设置为不进行版本控制。

## 配置参数说明

### API配置
- `api_key` - DeepSeek API密钥

### 白名单配置
- `group_ids` - 允许使用API的群组ID列表
- `user_ids` - 允许使用API的用户ID列表

### 模型配置
- `default` - 默认使用的模型，可选值：`deepseek-chat`或`deepseek-reasoner`
- `temperature` - 温度参数，控制输出的随机性，范围0-2.0

## 使用方式

请复制`config.example.toml`并重命名为`config.toml`，然后按需修改配置。

## 指令说明

插件支持以下两种方式触发：

### 1. 前缀命令方式
- 格式：`ds [问题]`
- 例如：`ds 请介绍一下量子力学`

### 2. @机器人方式
- 格式：`@机器人 [问题]`
- 例如：`@机器人 今天天气怎么样？`

### 记忆功能指令
插件支持对话记忆功能，可以使用以下指令控制：

- `ds memory on` - 开启记忆模式，AI会记住对话上下文
- `ds memory off` - 关闭记忆模式，每次对话都是独立的
- `ds memory clear` - 清空当前存储的对话记忆
- `ds memory status` - 查看当前记忆模式状态和已存储的消息数量 