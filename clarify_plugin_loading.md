# NCatBot 插件加载机制说明

## 插件目录约定

NCatBot 框架遵循明确的目录命名约定来加载插件。以下是关键点：

1. **默认只加载 `plugins` 目录中的模块作为插件**
2. 每个插件必须是 `plugins` 目录的直接子目录
3. 每个插件目录必须包含 `__init__.py` 文件
4. `test/`、`tests/` 等非插件目录不会被框架加载为插件

## 正确配置

在 `ncatbot.toml` 中，正确的插件配置方式为：

```toml
[plugins]
auto_load = true
paths = ["plugins"]  # 指定插件目录，只有此目录下的模块会被加载为插件
```

## 框架加载机制

NCatBot 框架在启动时会：

1. 读取 `ncatbot.toml` 中的 `plugins.paths` 配置
2. 只扫描指定的目录（默认为 `plugins`）
3. 查找这些目录下包含 `__init__.py` 的子目录
4. 将这些子目录作为插件加载

## 不再支持的功能

之前在 `bootstarp.py` 中尝试使用的 `config.set_ignored_directories()` 方法已**不再可用**。
框架没有提供显式指定忽略目录的能力，因为基于目录命名约定的机制已经足够：

```python
# 以下代码无效，已被删除
config.set_ignored_directories(ignored_dirs)  # 此方法不存在
```

## 测试目录处理

对于 `test/` 和 `tests/` 目录：

1. **自动排除**：它们不在 `plugins` 目录下，因此自然不会被加载为插件
2. **版本控制**：通过 `.gitignore` 规则，可以保留目录结构但忽略目录内容
3. **手动导入**：可以在代码中手动导入这些目录中的模块进行测试

## 建议与最佳实践

1. 所有插件都放在 `plugins` 目录下
2. 测试代码放在 `test` 或 `tests` 目录下
3. 如需添加新目录类型，只要不命名为 `plugins`，就不会被框架自动加载
4. 在 `.gitignore` 中正确配置测试目录，可以保留结构但忽略内容
5. 使用 `test/README.md` 和 `tests/README.md` 文件说明测试目录的用途