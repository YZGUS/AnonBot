# 情感支持插件 (Emotional Support Plugin)

这个插件用于检测用户消息中的抑郁或负面情绪，并自动生成安慰回复。

## 功能特点

- 自动检测群聊和私聊消息中的负面情绪
- 使用 SnowNLP 进行情感分析，识别可能需要安慰的用户
- 调用 DeepSeek AI 生成符合千早爱音角色设定的安慰回复
- 支持白名单机制，只对特定群聊或用户生效
- 可自定义情感阈值，调整触发条件

## 安装要求

- Python 3.8+
- SnowNLP 库：`pip install snownlp`
- Requests 库：`pip install requests`

## 配置方法

1. 复制 `config/config.toml.example` 到 `config/config.toml`
2. 编辑 `config.toml` 文件：
   - 填入 DeepSeek API 密钥
   - 设置白名单群组和用户ID
   - 调整情感阈值和模型参数

```toml
# 示例配置
api_key = "your_deepseek_api_key"

[whitelist]
group_ids = [123456789]
user_ids = [987654321]

[sentiment]
threshold = 0.2

[model]
default = "deepseek-chat"
temperature = 0.7
```

## 使用说明

插件会自动运行，无需手动触发。当白名单中的用户发送情感值低于阈值的消息时，会自动回复安慰文本。

## 工作原理

1. 插件接收到消息后检查是否为白名单用户/群组
2. 使用 SnowNLP 分析消息情感值（0-1之间，越低越消极）
3. 当情感值低于设定阈值时，调用 DeepSeek API 生成安慰回复
4. 将生成的安慰文本直接回复给用户

## 安慰文本生成

安慰文本基于千早爱音角色设定，包含以下特点：
- 表面轻快但隐含细腻观察的语气
- 适当穿插英语短语
- 包含肢体动作描写和台词组合
- 引用乐队相关元素
- 体现角色背景和成长弧线

## 注意事项

- API 密钥不应该提交到代码仓库
- 确保 SnowNLP 库正确安装并能够运行
- 插件目前使用文本回复，未来可能支持语音回复功能