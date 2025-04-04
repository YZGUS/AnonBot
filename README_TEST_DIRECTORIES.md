# 测试目录屏蔽说明

为了确保 `test/` 和 `tests/` 目录不会被加载为插件，同时保留目录结构但忽略其内容，我们进行了以下配置：

## 1. 目录屏蔽机制

我们使用了多种机制来屏蔽测试目录：

### 1.1 Git 选择性忽略

在 `.gitignore` 文件中添加了以下内容：

```
# 测试目录内容忽略但保留结构
test/*
!test/README.md
tests/*
!tests/README.md
```

这种配置可以：
- 忽略 test/ 和 tests/ 目录下的所有文件
- 但保留 test/README.md 和 tests/README.md 两个文件
- 这样确保目录结构会被版本控制，但目录中的其他内容不会被提交

### 1.2 NCatBot 框架目录命名约定

NCatBot框架默认只加载名为 `plugins` 的目录中的插件，因此 `test/` 和 `tests/` 目录自然不会被加载为插件。

为了进一步明确这一点，我们创建了 `.ncatbotignore` 文件，作为文档记录不应被框架加载的目录：

```
test/
tests/
__pycache__/
.git/
.idea/
.DS_Store
```

### 1.3 配置文件文档

在 `ncatbot.toml` 配置文件中，我们记录了需要被忽略的目录：

```toml
[ncatbot]
# 核心设置
allow_plugins = true
auto_reload = true

# 屏蔽目录
ignored_directories = [
    "test",
    "tests",
    "__pycache__"
]
```

请注意：由于NCatBot框架本身并不支持通过配置文件指定忽略目录，这部分配置主要用作文档记录。

## 2. 启动文件实现

修改了 `bootstarp.py` 文件，读取配置并输出日志信息，但不再尝试设置忽略目录（因为框架不支持）：

```python
# 输出忽略目录信息（仅用于日志记录，不进行设置）
ignored_dirs = []

# 读取框架配置文件
try:
    if os.path.exists("ncatbot.toml"):
        with open("ncatbot.toml", "rb") as f:
            ncatbot_cfg = tomllib.load(f)
            
            # 从配置文件中读取忽略目录
            if "ncatbot" in ncatbot_cfg and "ignored_directories" in ncatbot_cfg["ncatbot"]:
                ignored_dirs.extend(ncatbot_cfg["ncatbot"]["ignored_directories"])
except Exception as e:
    print(f"读取框架配置文件出错: {e}")

# 读取 .ncatbotignore 文件
try:
    if os.path.exists(".ncatbotignore"):
        with open(".ncatbotignore", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    ignored_dirs.append(line)
except Exception as e:
    print(f"读取 .ncatbotignore 文件出错: {e}")

# 去重并输出日志
if ignored_dirs:
    ignored_dirs = list(set(ignored_dirs))
    print(f"注意: 以下目录不会被自动加载为插件（通过框架机制）: {', '.join(ignored_dirs)}")
```

## 3. 测试目录说明文件

在测试目录中添加了README文件，说明测试目录的用途：

- `test/README.md`: 说明测试脚本和数据的用途
- `tests/README.md`: 说明单元测试和集成测试的用途及运行方法

这些README文件也会被版本控制，使目录结构保留在仓库中。

## 4. 验证结果

通过 `git status` 命令验证：
1. test/ 和 tests/ 目录结构被保留（README.md文件被添加到Git）
2. 两个目录中的其他文件都被忽略
3. 由于命名约定，NCatBot框架不会将测试目录作为插件目录加载

## 5. 测试脚本

我们创建了两个测试脚本来验证目录屏蔽的效果：

### 5.1 `test_python_load.py`

这个脚本检查测试目录和忽略配置：
- 验证test/和tests/目录是否存在
- 统计这些目录中的Python文件数量
- 测试是否可以导入这些目录中的模块（Python层面）
- 检查.ncatbotignore和ncatbot.toml配置

### 5.2 `test_module_import.py`

这个脚本专门测试模块导入：
- 测试是否可以导入测试目录中的模块
- 测试是否可以导入插件和主程序中的模块
- 输出导入结果和可能的错误

### 5.3 重要说明

需要注意，Python解释器本身可以导入任何目录中的模块，因为Python不关心目录名称。测试目录不会被加载为插件的原因是：

1. NCatBot框架默认只从 `plugins` 目录加载插件
2. 测试目录使用了不同的命名（`test` 和 `tests`）
3. Git忽略规则只影响版本控制，不影响Python的导入机制

测试结果表明：
1. 测试目录中的模块可以手动导入（这是预期行为）
2. 但框架只会从 `plugins` 目录加载插件，不会将测试目录中的Python文件作为插件加载
3. Git也会根据.gitignore规则忽略这些目录中的大部分内容，只保留README文件

## 注意事项

- 如果需要修改忽略规则，可以编辑 `.gitignore`、`.ncatbotignore` 或 `ncatbot.toml` 文件
- 如果需要在测试目录中添加要提交的文件，需要在 `.gitignore` 中添加例外规则，如：
  ```
  !test/important_file.py
  ```
- 这种机制只影响Git的版本控制，不会影响手动导入模块的能力
- 框架不会加载非 `plugins` 目录的Python文件作为插件