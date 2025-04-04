#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试脚本：检查框架是否能正确忽略测试目录
"""

import importlib
import os
import sys
from pathlib import Path


def print_header(text):
    print("\n" + "=" * 50)
    print(f" {text} ".center(50, "="))
    print("=" * 50)


def check_path_importable(path):
    """检查指定路径是否可导入"""
    module_name = path.stem
    try:
        if str(path.parent) not in sys.path:
            sys.path.insert(0, str(path.parent))
        
        # 尝试导入
        importlib.import_module(module_name)
        return True
    except ImportError as e:
        print(f"无法导入 {path}: {e}")
        return False
    except Exception as e:
        print(f"导入 {path} 时发生错误: {e}")
        return False


def main():
    """主函数"""
    base_dir = Path(__file__).parent
    
    print_header("目录结构检查")
    test_dir = base_dir / "test"
    tests_dir = base_dir / "tests"
    
    print(f"test 目录存在: {test_dir.exists()}")
    print(f"tests 目录存在: {tests_dir.exists()}")
    
    # 检查测试目录中的Python文件
    print_header("测试目录文件")
    test_py_files = list(test_dir.glob("*.py"))
    tests_py_files = list(tests_dir.glob("*.py"))
    
    print(f"test 目录中的 Python 文件数量: {len(test_py_files)}")
    print(f"tests 目录中的 Python 文件数量: {len(tests_py_files)}")
    
    # 尝试导入测试目录中的Python文件
    if test_py_files:
        print_header("尝试导入 test 目录文件")
        for py_file in test_py_files[:3]:  # 只尝试前三个文件
            print(f"尝试导入 {py_file.stem}...")
            result = check_path_importable(py_file)
            print(f"  导入结果: {'成功' if result else '失败'}")
    
    # 检查 .ncatbotignore 文件
    print_header(".ncatbotignore 文件检查")
    ignore_file = base_dir / ".ncatbotignore"
    
    if ignore_file.exists():
        print(f".ncatbotignore 文件存在")
        with open(ignore_file, "r") as f:
            ignored_dirs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"忽略的目录列表: {', '.join(ignored_dirs)}")
    else:
        print(f".ncatbotignore 文件不存在")
    
    # 检查 ncatbot.toml 文件
    print_header("ncatbot.toml 文件检查")
    config_file = base_dir / "ncatbot.toml"
    
    if config_file.exists():
        print(f"ncatbot.toml 文件存在")
        try:
            import tomllib
            with open(config_file, "rb") as f:
                config = tomllib.load(f)
                if "ncatbot" in config and "ignored_directories" in config["ncatbot"]:
                    ignored_dirs = config["ncatbot"]["ignored_directories"]
                    print(f"配置中忽略的目录: {', '.join(ignored_dirs)}")
                else:
                    print("配置中未找到忽略目录设置")
        except Exception as e:
            print(f"读取配置文件出错: {e}")
    else:
        print(f"ncatbot.toml 文件不存在")
    
    print_header("测试完成")


if __name__ == "__main__":
    main()