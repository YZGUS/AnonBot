#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试模块导入
"""

import importlib.util
import sys
from pathlib import Path


def is_importable(path):
    """测试文件是否可导入"""
    try:
        spec = importlib.util.spec_from_file_location(Path(path).stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True
    except Exception as e:
        print(f"  导入错误: {e}")
        return False


def main():
    """主函数"""
    base = Path('/Users/cengyi/Desktop/code/AnonBot')
    
    print('模块导入测试：')
    
    files_to_test = [
        'test/rebang_scraper.py',  # 测试目录中的模块
        'tests/test_scraper.py',   # 测试目录中的模块
        'plugins/baidu/main.py',   # 插件目录中的模块
        'rebang/scraper.py'        # 主模块
    ]
    
    for p in files_to_test:
        path = base / p
        print(f"\n测试导入: {p}")
        result = is_importable(path)
        print(f"  导入结果: {'成功' if result else '失败'}")


if __name__ == "__main__":
    main()