# 单元测试目录

这个目录用于存放项目的单元测试和集成测试用例。

## 目录内容

- 单元测试：测试独立组件和函数
- 集成测试：测试多个组件之间的交互
- 测试工具：辅助测试的工具和脚本
- 测试输出：测试运行的输出数据和报告

## 运行测试

可以使用以下命令运行测试：

```bash
# 运行所有测试
python -m unittest discover tests

# 运行特定测试
python -m unittest tests.test_scraper
```

## 注意事项

1. 此目录已通过 `.ncatbotignore` 和 `.gitignore` 设置为忽略目录
2. 测试目录中的模块不会被加载为插件
3. 测试文件命名应遵循 `test_*.py` 的格式