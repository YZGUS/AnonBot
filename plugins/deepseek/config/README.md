# DeepSeek插件配置说明

本目录包含DeepSeek插件的配置文件。

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