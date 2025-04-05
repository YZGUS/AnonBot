#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
热榜API客户端示例运行脚本

运行所有示例文件
"""

import os
import subprocess
import sys


def main():
    """运行所有示例文件。"""
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取所有示例文件
    example_files = [f for f in os.listdir(current_dir) 
                     if f.endswith('_example.py') and os.path.isfile(os.path.join(current_dir, f))]
    
    # 创建输出目录
    output_dir = os.path.join(current_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 打印找到的示例文件
    print(f"找到 {len(example_files)} 个示例文件:")
    for i, file in enumerate(example_files, 1):
        print(f"{i}. {file}")
    
    # 询问用户选择
    print("\n选择操作:")
    print("1. 运行所有示例")
    print("2. 选择特定示例运行")
    print("3. 退出")
    
    choice = input("请输入选项 (1-3): ").strip()
    
    if choice == '1':
        # 运行所有示例
        print("\n开始运行所有示例...\n")
        for file in example_files:
            run_example(os.path.join(current_dir, file))
    elif choice == '2':
        # 选择特定示例运行
        print("\n请选择要运行的示例文件:")
        for i, file in enumerate(example_files, 1):
            print(f"{i}. {file}")
        
        try:
            file_choice = int(input("请输入文件序号: ").strip())
            if 1 <= file_choice <= len(example_files):
                selected_file = example_files[file_choice - 1]
                print(f"\n运行示例: {selected_file}\n")
                run_example(os.path.join(current_dir, selected_file))
            else:
                print("无效的选择!")
        except ValueError:
            print("请输入有效的数字!")
    elif choice == '3':
        print("退出程序")
        return
    else:
        print("无效的选择!")


def run_example(file_path):
    """运行指定的示例文件。"""
    print(f"正在运行: {os.path.basename(file_path)}")
    print("-" * 50)
    
    try:
        # 使用Python解释器运行示例文件
        subprocess.run([sys.executable, file_path], check=True)
        print("\n示例运行完成!")
    except subprocess.CalledProcessError as e:
        print(f"\n示例运行失败: {e}")
    except Exception as e:
        print(f"\n发生错误: {e}")
    
    print("-" * 50)
    print()


if __name__ == "__main__":
    main()