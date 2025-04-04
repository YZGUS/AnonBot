# AnonBot 插件开发指南

本文档提供了开发 AnonBot 插件的详细指南和最佳实践，可以帮助开发者快速创建符合规范的高质量插件。

## 目录

- [基础结构](#基础结构)
- [插件开发流程](#插件开发流程)
- [核心组件](#核心组件)
- [消息处理](#消息处理)
- [定时任务](#定时任务)
- [数据持久化](#数据持久化)
- [错误处理与日志](#错误处理与日志)
- [配置管理](#配置管理)
- [插件示例](#插件示例)
- [测试与调试](#测试与调试)
- [发布与维护](#发布与维护)

## 基础结构

每个插件应遵循以下目录结构：

```
plugins/插件名称/
├── __init__.py      # 插件初始化文件
├── main.py          # 插件主文件
├── config/          # 配置目录
│   ├── config.toml  # 配置文件
│   └── README.md    # 配置说明
└── data/            # 数据存储目录
```

### `__init__.py` 示例内容

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .main import 插件类名

__all__ = ["插件类名"]
```

## 插件开发流程

1. **规划插件功能**: 明确插件的主要功能和用户交互方式
2. **设计数据结构**: 确定配置结构和数据模型
3. **创建基础框架**: 按照标准目录结构创建文件
4. **实现核心功能**: 开发主要功能逻辑
5. **添加消息处理**: 实现消息响应机制
6. **配置持久化**: 处理数据存储和加载
7. **添加错误处理**: 增强插件的健壮性
8. **编写文档**: 完成README和配置说明
9. **测试与调试**: 全面测试各种使用场景
10. **发布与维护**: 发布插件并根据反馈持续优化

## 核心组件

### 配置类

使用`dataclass`创建结构化的配置类：

```python
@dataclass
class Config:
    """配置类"""
    white_list: List[int]          # 用户白名单
    group_white_list: List[int]    # 群组白名单
    update_interval: int           # 更新间隔(秒)
    max_items: int                 # 最大显示条数
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置实例"""
        return cls(
            white_list=config_dict.get("whitelist", {}).get("user_ids", []),
            group_white_list=config_dict.get("whitelist", {}).get("group_ids", []),
            update_interval=config_dict.get("basic", {}).get("update_interval", 300),
            max_items=config_dict.get("basic", {}).get("max_items", 10),
        )
```

### 数据收集器

分离数据获取逻辑，便于单独测试和维护：

```python
class DataCollector:
    """数据收集器"""
    
    def __init__(self, data_dir: Path):
        """初始化"""
        self.data_dir = data_dir
        
    def fetch_data(self) -> Dict[str, Any]:
        """获取数据"""
        # 实现数据获取逻辑
        pass
        
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据"""
        # 实现数据解析逻辑
        pass
        
    def save_data(self, data: Dict[str, Any]) -> str:
        """保存数据到文件"""
        # 实现数据保存逻辑
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        date_dir = self.data_dir / date_str
        date_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = now.strftime("%Y%m%d%H%M%S")
        filename = f"data_{timestamp}.json"
        filepath = date_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return str(filepath)
```

### 插件主类

```python
class YourPlugin(BasePlugin):
    """插件主类"""
    name = "YourPlugin"  # 插件名称
    version = "1.0.0"    # 插件版本
    
    # 类变量
    config = None
    config_path = None
    data_dir = None
    latest_data_file = None
    
    async def on_load(self):
        """插件加载时执行"""
        # 初始化路径
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.load_config()
        
        # 设置定时任务
        scheduler.add_random_minute_task(self.fetch_data, 0, 5)
        
        # 立即执行一次
        await self.fetch_data()
```

## 消息处理

使用装饰器处理消息：

```python
@bot.group_event()
async def on_group_event(self, msg: GroupMessage):
    """处理群聊消息"""
    # 检查白名单权限
    if not self.is_user_authorized(msg.sender.user_id, msg.group_id):
        return
        
    content = msg.raw_message.strip()
    
    # 解析命令和参数
    if content == "命令前缀":
        # 处理基本命令
        response = self.format_response_message()
        await msg.reply(text=response)
    elif content.startswith("命令前缀 "):
        # 处理带参数的命令
        try:
            # 解析参数
            param = content.replace("命令前缀 ", "").strip()
            # 处理命令
            response = self.handle_command_with_param(param)
            await msg.reply(text=response)
        except Exception as e:
            # 错误处理
            logger.error(f"处理命令出错: {e}")
            await msg.reply(text=f"处理命令时出现错误: {str(e)}")
```

私聊消息处理类似：

```python
@bot.private_event()
async def on_private_event(self, msg: PrivateMessage):
    """处理私聊消息"""
    # 检查白名单权限
    if not self.is_user_authorized(msg.sender.user_id):
        return
        
    # 类似群聊的消息处理逻辑
```

## 定时任务

使用调度器添加定时任务：

```python
# 插件加载时设置
scheduler.add_random_minute_task(self.fetch_data, 0, 5)  # 每小时0-5分钟时随机执行一次

# 定时任务实现
async def fetch_data(self) -> None:
    """定时获取数据"""
    try:
        # 创建数据收集器
        collector = DataCollector(data_dir=self.data_dir)
        # 获取数据
        data = collector.fetch_data()
        # 解析数据
        parsed_data = collector.parse_data(data)
        
        if parsed_data:
            # 保存数据
            data_file = collector.save_data(parsed_data)
            if data_file:
                self.latest_data_file = data_file
                logger.info(f"成功获取并保存数据: {data_file}")
                
            # 清理旧数据
            await self.clean_old_files()
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
```

## 数据持久化

### 文件存储格式

推荐按日期组织文件：

```
data/
├── 20230401/
│   ├── data_20230401123045.json
│   └── data_20230401183012.json
└── 20230402/
    └── data_20230402093022.json
```

### 清理旧数据

定期清理过期数据：

```python
async def clean_old_files(self) -> None:
    """清理旧数据文件"""
    try:
        # 清理过期数据：保留最近N天的数据
        all_date_dirs = [d for d in self.data_dir.iterdir() if d.is_dir()]
        all_date_dirs.sort(reverse=True)  # 按日期倒序排列
        
        # 保留最近N天的数据目录
        keep_days = self.config.keep_days  # 从配置中获取保留天数
        if len(all_date_dirs) > keep_days:
            for old_dir in all_date_dirs[keep_days:]:
                # 删除旧目录及其内容
                for file in old_dir.iterdir():
                    file.unlink()
                old_dir.rmdir()
                logger.debug(f"已删除旧数据目录: {old_dir}")
    except Exception as e:
        logger.error(f"清理旧文件失败: {e}")
```

## 错误处理与日志

### 日志设置

```python
import logging
logger = logging.getLogger("插件名称")

# 在插件加载时设置日志级别
log_level = self.config.log_level.upper()
logger.setLevel(getattr(logging, log_level, logging.INFO))
```

### 错误处理最佳实践

```python
try:
    # 可能出错的代码
    result = process_data(data)
    return result
except ConnectionError as e:
    # 处理特定类型的错误
    logger.warning(f"连接错误: {e}")
    return "网络连接出现问题，请稍后再试"
except ValueError as e:
    # 处理值错误
    logger.warning(f"参数错误: {e}")
    return f"参数格式不正确: {str(e)}"
except Exception as e:
    # 处理其他未预期的错误
    logger.error(f"未预期的错误: {e}", exc_info=True)
    return "处理请求时出现错误，请联系管理员"
```

## 配置管理

### 加载配置

```python
def load_config(self) -> None:
    """加载配置文件"""
    if self.config_path.exists():
        try:
            with open(self.config_path, "rb") as f:
                config_dict = tomllib.load(f)
            self.config = Config.from_dict(config_dict)
            self.config_last_modified = self.config_path.stat().st_mtime
            logger.info(f"成功加载配置文件: {self.config_path}")
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            self.config = Config.from_dict({})  # 使用默认配置
    else:
        logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
        self.config = Config.from_dict({})  # 使用默认配置
```

### 监控配置变更

```python
def check_config_update(self) -> bool:
    """检查配置文件是否更新"""
    if not self.config_path.exists():
        return False
        
    current_mtime = self.config_path.stat().st_mtime
    if current_mtime > self.config_last_modified:
        self.load_config()
        return True
    return False
```

## 插件示例

### 1. 情感支持插件

通过情感分析监测用户消息情绪，在发现负面情绪时自动提供安慰回复：

- 文件位置：`plugins/emotional_support`
- 核心功能：使用 SnowNLP 进行情感分析，通过 DeepSeek API 生成角色化回复
- 特点：无需指令触发，自动工作

### 2. 抖音热榜插件 

提供抖音热搜和热门话题的查询功能：

- 文件位置：`plugins/douyin`
- 命令：`抖音热榜`、`抖音热榜 [数量]`、`抖音热榜话题`等
- 特点：定时获取数据并缓存，支持多种命令参数

### 3. 百度热搜插件

获取并展示百度实时热搜榜：

- 文件位置：`plugins/baidu`
- 命令：`百度热搜`、`百度热搜 [数量]`、`百度热搜 详情`等
- 特点：精美的数据展示，支持详情查看，定期数据归档

## 测试与调试

### 测试清单

1. **基础功能测试**：验证插件的核心功能是否正常工作
2. **参数处理测试**：测试不同格式的命令参数是否正确解析
3. **权限控制测试**：验证白名单机制是否生效
4. **错误处理测试**：测试各种错误情况的响应
5. **性能测试**：检查插件在高负载下的表现
6. **持久化测试**：验证数据存储和加载是否正确

### 调试技巧

1. 使用详细的日志记录关键操作
2. 设置配置中的`log_level`为`DEBUG`获取更多信息
3. 在关键函数中添加打印语句输出状态信息
4. 使用 try-except 块捕获并记录详细错误信息

## 发布与维护

### 发布前检查清单

1. 确保插件遵循标准目录结构
2. 验证所有功能正常运行
3. 确认配置文件格式正确并包含注释
4. 检查是否有详细的文档说明
5. 验证错误处理机制是否完善
6. 检查代码质量和注释

### 维护最佳实践

1. 定期检查插件是否正常工作
2. 监控用户反馈并及时响应
3. 更新插件以适应API或服务变更
4. 定期优化性能和用户体验
5. 保持文档的更新与代码同步