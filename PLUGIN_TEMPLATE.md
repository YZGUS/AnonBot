# AnonBot 插件开发需求模板

## 一、插件基本信息

- **插件名称**：{请输入插件名称，例如：KnowledgeBase}
- **功能描述**：{请描述插件的主要功能，例如：知识库查询与管理插件，允许用户添加、查询和管理知识条目}
- **命令前缀**：{请指定主要命令，例如：知识库、kb}
- **权限控制**：
  - [ ] 用户白名单
  - [ ] 群组白名单
  - [ ] 其他权限机制
- **数据存储**：
  - [ ] 需要持久化存储
  - [ ] 需要缓存机制
  - [ ] 需要定期清理旧数据
- **API依赖**：
  - [ ] 需要外部API（请说明：{如有需要，请说明}）
  - [ ] 无外部API依赖

## 二、目录结构设计

```
plugins/{插件名称}/
├── __init__.py           # 插件初始化文件
├── main.py               # 插件主文件
├── config/               # 配置目录
│   ├── config.toml       # 配置文件（实际配置，被.gitignore排除）
│   ├── config.example.toml # 配置示例文件（提交到仓库）
│   └── README.md         # 配置说明
└── data/                 # 数据存储目录
    └── {按需设计子目录，推荐按日期-小时组织}
```

## 三、主要功能需求

### 3.1 基础功能

- [ ] 支持接收并响应群聊命令（@bot.group_event()）
- [ ] 支持接收并响应私聊命令（@bot.private_event()）
- [ ] 支持白名单验证（is_user_authorized()）
- [ ] 支持配置文件加载（load_config()）
- [ ] 支持配置文件更新检测（check_config_update()）
- [ ] 支持退出清理（on_exit()）

### 3.2 高级功能

- [ ] 支持定时任务（scheduler.add_task()）
- [ ] 支持自动数据获取与更新
- [ ] 支持数据解析与处理
- [ ] 支持复杂命令参数解析（例如：`命令 子命令 -p 参数`）
- [ ] 支持数据持久化与恢复
- [ ] 支持错误处理与日志记录
- [ ] 支持用户交互（多轮对话或按步骤引导）
- [ ] 支持富文本消息格式化（如添加表情符号、分隔符等）

## 四、配置项需求

- **基础配置**：
  - [ ] update_interval: 数据更新间隔（秒）
  - [ ] max_items: 默认展示条数
  - [ ] log_level: 日志级别
  
- **访问控制**：
  - [ ] white_list: 用户白名单
  - [ ] group_white_list: 群组白名单
  
- **存储设置**：
  - [ ] max_files_per_day: 每日最大文件数（若按小时存储，建议至少24）
  - [ ] keep_days: 保留数据天数
  
- **UI设置**：
  - [ ] 消息模板配置（头部、条目、底部）
  - [ ] 表情符号映射
  
- **特定设置**：
  - [ ] {根据插件特点添加特定配置项}
  - [ ] {如：热度值显示格式、特殊分类标签等}

## 五、输出格式需求

### 5.1 消息头部格式

```
📊 {标题} ({时间})

共{总数}条数据，{特殊项}条特别标记
━━━━━━━━━━━━━━━━━━

```

### 5.2 消息主体格式

```
{排名前缀}{高亮标记}{标题}{分类标签}{数值标签}
{详情描述（可选）}
{链接（可选）}

┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈（每三条添加分隔符）
```

### 5.3 消息底部格式

```
━━━━━━━━━━━━━━━━━━
📊 更新时间: {时间}
💡 提示: 发送「{命令} 数字」可指定获取的条数，如「{命令} 20」
```

## 六、类设计需求

### 6.1 配置类

```python
@dataclass
class Config:
    """配置类"""
    white_list: List[int]
    group_white_list: List[int]
    update_interval: int
    max_items: int
    max_files_per_day: int
    keep_days: int
    log_level: str
    templates: Dict[str, str]
    # 其他配置项...
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """从字典创建配置"""
        # 实现配置加载逻辑
```

### 6.2 数据收集器类

```python
class DataCollector:
    """数据收集器"""
    def __init__(self, data_dir: Path):
        """初始化数据收集器"""
        self.data_dir = data_dir
        
    def collect_data(self) -> Dict[str, Any]:
        """收集数据"""
        # 数据获取逻辑
        
    def parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据"""
        # 数据解析逻辑
        
    def save_data(self, data: Dict[str, Any]) -> str:
        """保存数据到按小时组织的文件中"""
        # 使用年月日-小时格式，如 "YYYYMMDD-HH"
        now = datetime.now()
        folder_name = now.strftime("%Y%m%d-%H")
        folder_path = self.data_dir / folder_name
        folder_path.mkdir(exist_ok=True, parents=True)
        
        # 保存逻辑
```

### 6.3 插件主类

```python
class YourPlugin(BasePlugin):
    """插件主类"""
    name = "YourPlugin"
    version = "1.0.0"
    
    # 类变量
    config = None
    config_path = None
    data_dir = None
    latest_data_file = None
    
    async def on_load(self):
        """插件加载时执行"""
        # 初始化逻辑
        base_path = Path(__file__).parent
        self.config_path = base_path / "config" / "config.toml"
        self.data_dir = base_path / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 加载配置
        self.load_config()
        
        # 设置定时任务
        scheduler.add_random_minute_task(self.fetch_data, 0, 5)
        
        # 立即执行一次数据获取
        await self.fetch_data()
        
    def load_config(self) -> None:
        """加载配置"""
        # 配置加载逻辑
        
    async def clean_old_files(self) -> None:
        """清理旧数据文件（按日期-小时组织）"""
        # 按日期前缀分组，然后清理
        # 1. 清理超过keep_days的日期目录
        # 2. 对保留的日期目录，控制每小时文件夹的文件数量
        
    async def fetch_data(self) -> None:
        """获取数据"""
        # 数据获取逻辑
        # 1. 使用DataCollector收集数据
        # 2. 保存数据
        # 3. 更新latest_data_file
        # 4. 清理旧文件
        
    def format_message(self, data: Dict[str, Any], count: int = None, show_detail: bool = False) -> str:
        """格式化消息，支持详情视图和数量自定义"""
        # 消息格式化逻辑
        # 1. 添加头部（标题、统计信息）
        # 2. 添加主体（条目列表，支持排名美化、高亮标记等）
        # 3. 添加底部（更新时间、使用提示）
        
    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        """处理群聊消息"""
        # 群聊消息处理逻辑
        
    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        """处理私聊消息"""
        # 私聊消息处理逻辑
```

## 七、文档需求

### 7.1 README.md 格式

1. 插件名称和简介
2. 功能特性列表
3. 使用方法（命令格式和示例）
4. 配置说明（链接到配置文档）
5. 常见问题解答

### 7.2 配置文档 (config/README.md) 格式

1. 配置项分类介绍
2. 每个配置项的详细说明（含默认值和可选值）
3. 数据存储结构说明（如按小时组织的目录结构）
4. 完整配置示例
5. 高级配置技巧

### 7.3 配置示例文件 (config.example.toml)

1. 提供一个包含所有配置项的示例文件
2. 使用明确的示例值（而非默认空值）
3. 添加详细注释解释每个配置项的作用和可选值
4. 在文件开头添加使用说明（如"将此文件复制为config.toml并按需修改"）

## 八、代码风格要求

1. 使用类型提示增强代码可读性
2. 为所有类和公共方法提供文档字符串
3. 遵循PEP 8代码风格规范
4. 使用异常处理增强代码健壮性
5. 使用日志而非print语句
6. 使用有意义的变量和函数名称
7. 正确处理异步函数
8. 分离业务逻辑和展示层，便于后期维护

## 九、测试要求

1. 基础功能测试
2. 错误处理测试
3. 性能测试（响应时间）
4. 持久性测试（配置加载与保存）
5. 边界条件测试（如空数据、超大数据量等）

## 十、参考示例

1. 百度热搜插件：`plugins/baidu`
2. 百度贴吧插件：`plugins/tieba`
3. 抖音热榜插件：`plugins/douyin`
4. 情感支持插件：`plugins/emotional_support`

## 十一、安全与隐私注意事项

1. 敏感配置文件不应提交到版本控制系统
   - 实际配置文件（如`config.toml`）应在`.gitignore`中排除
   - 提供示例配置文件（如`config.example.toml`）供用户参考
   
2. 数据存储与清理
   - 按时间组织数据，便于管理和清理
   - 实现自动清理机制，避免数据无限增长
   - 考虑将敏感数据加密存储

3. 错误处理与日志记录
   - 避免在日志中记录敏感信息
   - 日志级别可配置，生产环境推荐使用INFO或更高级别
   - 错误信息应对用户友好，不暴露系统细节