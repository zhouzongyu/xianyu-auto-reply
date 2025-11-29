#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
闲鱼自动回复系统 - EXE打包脚本

使用方法:
    python build_exe.py

依赖:
    pip install pyinstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_step(step_name: str):
    """打印步骤信息"""
    print("\n" + "="*60)
    print(f"  {step_name}")
    print("="*60)

def check_dependencies():
    """检查打包依赖"""
    print_step("检查打包依赖")
    
    try:
        import PyInstaller
        version = PyInstaller.__version__
        print(f"✓ PyInstaller 已安装，版本: {version}")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("\n正在安装 PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller 安装成功")
            return True
        except Exception as e:
            print(f"✗ PyInstaller 安装失败: {e}")
            print("\n请手动安装: pip install pyinstaller")
            return False

def check_project_files():
    """检查项目文件"""
    print_step("检查项目文件")
    
    required_files = [
        'Start.py',
        'global_config.yml',
        'static',
        'reply_server.py',
    ]
    
    missing_files = []
    for file in required_files:
        path = Path(file)
        if not path.exists():
            missing_files.append(file)
        else:
            print(f"✓ {file} 存在")
    
    if missing_files:
        print(f"\n✗ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    # 检查static目录是否完整
    static_index = Path('static/index.html')
    if not static_index.exists():
        print(f"⚠ 警告: static/index.html 不存在，静态文件可能不完整")
    else:
        print(f"✓ static/index.html 存在")
    
    # 检查关键依赖
    print("\n检查关键依赖:")
    try:
        import numpy
        print(f"✓ numpy 已安装，版本: {numpy.__version__}")
    except ImportError:
        print("✗ numpy 未安装")
        print("  请运行: pip install numpy")
        return False
    
    try:
        import pandas
        print(f"✓ pandas 已安装，版本: {pandas.__version__}")
    except ImportError:
        print("✗ pandas 未安装")
        print("  请运行: pip install pandas")
        return False
    
    return True

def clean_build_dirs():
    """清理之前的构建目录"""
    print_step("清理构建目录")
    
    dirs_to_clean = ['build', 'dist']
    
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"✓ 已删除目录: {dir_name}")
            except Exception as e:
                print(f"⚠ 删除 {dir_name} 失败: {e}")

def build_exe():
    """执行打包"""
    print_step("开始打包EXE")
    
    spec_file = Path('build_exe.spec')
    if not spec_file.exists():
        print(f"✗ 找不到spec文件: {spec_file}")
        return False
    
    try:
        # 使用PyInstaller打包
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',  # 清理临时文件
            '--noconfirm',  # 覆盖输出目录
            str(spec_file)
        ]
        
        print(f"执行命令: {' '.join(cmd)}")
        print("\n打包中，请稍候...（这可能需要几分钟）\n")
        
        result = subprocess.run(cmd, check=False, capture_output=False)
        
        if result.returncode == 0:
            print("\n✓ EXE打包成功！")
            return True
        else:
            print(f"\n✗ 打包失败，返回码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n✗ 打包过程出错: {e}")
        return False

def copy_additional_files():
    """复制额外需要的文件到dist目录"""
    print_step("复制额外文件")
    
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("✗ dist目录不存在，请先完成打包")
        return False
    
    # 查找exe文件所在目录
    exe_dir = dist_dir / 'XianyuAutoReply'
    if not (exe_dir / 'XianyuAutoReply.exe').exists():
        # 尝试其他位置
        exe_files = list(dist_dir.rglob('XianyuAutoReply.exe'))
        if exe_files:
            exe_dir = exe_files[0].parent
        else:
            print("⚠ 找不到exe文件，跳过额外文件复制")
            return False
    
    print(f"✓ EXE文件位置: {exe_dir}")
    
    # 强制复制static目录（确保存在）
    static_source = Path('static')
    static_dest = exe_dir / 'static'
    
    if not static_source.exists():
        print(f"✗ 源static目录不存在: {static_source}")
        return False
    
    try:
        import shutil
        # 如果目标目录存在，先删除
        if static_dest.exists():
            print(f"删除已存在的static目录...")
            shutil.rmtree(static_dest)
        
        # 复制static目录
        print(f"正在复制static目录...")
        shutil.copytree(static_source, static_dest)
        
        # 验证关键文件
        if (static_dest / 'index.html').exists():
            file_count = len(list(static_dest.rglob('*')))
            print(f"✓ static目录复制成功")
            print(f"  位置: {static_dest}")
            print(f"  文件数量: {file_count} 个")
        else:
            print(f"⚠ static目录复制后缺少关键文件")
            return False
    except Exception as e:
        print(f"✗ 复制static目录失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 创建必要的目录
    data_dir = exe_dir / 'data'
    logs_dir = exe_dir / 'logs'
    
    for dir_path in [data_dir, logs_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ 创建目录: {dir_path.name}")
    
    return True

def install_playwright_browser():
    """安装Playwright浏览器到打包目录"""
    print_step("安装Playwright浏览器")
    
    dist_dir = Path('dist')
    exe_dir = dist_dir / 'XianyuAutoReply'
    
    if not (exe_dir / 'XianyuAutoReply.exe').exists():
        print("⚠ 找不到exe文件，跳过Playwright浏览器安装")
        return False
    
    # 检查是否已安装Playwright
    try:
        import playwright
    except ImportError:
        print("⚠ Playwright模块未安装，跳过浏览器安装")
        print("   请在打包环境中安装: pip install playwright")
        return False
    
    playwright_dir = exe_dir / 'playwright'
    
    # 检查是否已经存在
    if playwright_dir.exists():
        chromium_dirs = list(playwright_dir.glob('chromium-*'))
        if chromium_dirs:
            chrome_exe = chromium_dirs[0] / 'chrome-win' / 'chrome.exe'
            if chrome_exe.exists() and chrome_exe.stat().st_size > 0:
                print(f"✓ Playwright浏览器已存在: {chromium_dirs[0].name}")
                return True
    
    print("正在安装Playwright Chromium浏览器到打包目录...")
    print("这可能需要几分钟时间，请耐心等待...")
    
    try:
        # 设置环境变量，让Playwright安装到指定目录
        import os
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(playwright_dir.absolute())
        
        # 方法1: 尝试使用playwright的Python API安装
        try:
            from playwright._impl._driver import install_driver, install_browsers
            print("   正在安装Playwright驱动...")
            install_driver()
            print("   正在安装Chromium浏览器...")
            install_browsers(['chromium'])
            print(f"✓ Playwright浏览器安装成功（通过API）")
            print(f"  位置: {playwright_dir}")
            return True
        except ImportError:
            # API不可用，使用命令行方式
            print("   使用命令行方式安装...")
            result = subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', 'chromium'],
                capture_output=True,
                text=True,
                timeout=600,  # 10分钟超时
                env={**os.environ, 'PLAYWRIGHT_BROWSERS_PATH': str(playwright_dir.absolute())}
            )
            
            if result.returncode == 0:
                # 验证安装是否成功
                chromium_dirs = list(playwright_dir.glob('chromium-*'))
                if chromium_dirs:
                    chrome_exe = chromium_dirs[0] / 'chrome-win' / 'chrome.exe'
                    if chrome_exe.exists() and chrome_exe.stat().st_size > 0:
                        print(f"✓ Playwright浏览器安装成功")
                        print(f"  位置: {playwright_dir}")
                        print(f"  版本: {chromium_dirs[0].name}")
                        return True
                    else:
                        print(f"⚠ 浏览器文件不完整")
                        return False
                else:
                    print(f"⚠ 未找到浏览器目录")
                    return False
            else:
                print(f"✗ Playwright浏览器安装失败")
                if result.stdout:
                    print(f"   输出: {result.stdout[-500:]}")
                if result.stderr:
                    print(f"   错误: {result.stderr[-500:]}")
                return False
    except subprocess.TimeoutExpired:
        print(f"✗ Playwright浏览器安装超时（超过10分钟）")
        return False
    except Exception as e:
        print(f"✗ Playwright浏览器安装失败: {e}")
        import traceback
        print(f"   详细错误: {traceback.format_exc()}")
        return False
    finally:
        # 清除环境变量
        if 'PLAYWRIGHT_BROWSERS_PATH' in os.environ:
            del os.environ['PLAYWRIGHT_BROWSERS_PATH']

def create_launcher_script():
    """创建启动脚本"""
    print_step("创建启动脚本")
    
    dist_dir = Path('dist')
    exe_dir = dist_dir / 'XianyuAutoReply'
    
    if not (exe_dir / 'XianyuAutoReply.exe').exists():
        print("⚠ 找不到exe文件，跳过启动脚本创建")
        return
    
    # 创建批处理启动脚本
    bat_content = """@echo off
chcp 65001 >nul
title 闲鱼自动回复系统
echo ========================================
echo   闲鱼自动回复系统
echo ========================================
echo.
echo 正在启动...
echo.
echo 启动后请访问: http://localhost:8080
echo 默认账号: admin / admin123
echo.
echo 按 Ctrl+C 可以停止程序
echo.

cd /d "%~dp0"
XianyuAutoReply.exe

pause
"""
    
    bat_path = exe_dir / '启动.bat'
    bat_path.write_text(bat_content, encoding='gbk')
    print(f"✓ 创建启动脚本: 启动.bat")

def main():
    """主函数"""
    print("\n" + "="*60)
    print("  闲鱼自动回复系统 - EXE打包工具")
    print("="*60)
    
    # 1. 检查依赖
    if not check_dependencies():
        print("\n✗ 依赖检查失败，请先安装必要的依赖")
        sys.exit(1)
    
    # 2. 检查项目文件
    if not check_project_files():
        print("\n✗ 项目文件检查失败")
        sys.exit(1)
    
    # 3. 清理构建目录
    clean_build_dirs()
    
    # 4. 打包
    if not build_exe():
        print("\n✗ 打包失败")
        sys.exit(1)
    
    # 5. 复制额外文件
    if not copy_additional_files():
        print("\n✗ 复制额外文件失败")
        sys.exit(1)
    
    # 6. 安装Playwright浏览器到打包目录
    if not install_playwright_browser():
        print("\n⚠ 警告: Playwright浏览器安装失败")
        print("   程序可以运行，但Playwright功能可能不可用")
        print("   用户可以手动运行exe，程序会自动尝试安装")
    
    # 7. 创建启动脚本
    create_launcher_script()
    
    # 完成
    print_step("打包完成")
    
    exe_dir = Path('dist') / 'XianyuAutoReply'
    exe_path = exe_dir / 'XianyuAutoReply.exe'
    
    if exe_path.exists():
        print(f"\n✓ 打包成功！")
        print(f"\nEXE文件位置: {exe_path}")
        print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # 检查static目录
        static_dir = exe_dir / 'static'
        if static_dir.exists() and (static_dir / 'index.html').exists():
            print(f"\n✓ static目录存在: {static_dir}")
        else:
            print(f"\n⚠ 警告: static目录不存在或不完整！")
        
        # 检查Playwright浏览器
        playwright_dir = exe_dir / 'playwright'
        if playwright_dir.exists():
            chromium_dirs = list(playwright_dir.glob('chromium-*'))
            if chromium_dirs:
                chrome_exe = chromium_dirs[0] / 'chrome-win' / 'chrome.exe'
                if chrome_exe.exists() and chrome_exe.stat().st_size > 0:
                    print(f"\n✓ Playwright浏览器已安装: {chromium_dirs[0].name}")
                    print(f"  位置: {playwright_dir}")
                else:
                    print(f"\n⚠ 警告: Playwright浏览器文件不完整！")
            else:
                print(f"\n⚠ 警告: Playwright浏览器目录存在但未找到浏览器！")
        else:
            print(f"\n⚠ 警告: Playwright浏览器未安装！")
            print("  程序运行时会自动尝试安装，但首次安装可能需要几分钟")
        
        print(f"\n建议:")
        print("  1. 将整个 dist/XianyuAutoReply 文件夹复制到目标位置")
        print("  2. 运行 启动.bat 或直接运行 XianyuAutoReply.exe")
        print("  3. 首次运行会自动创建数据目录")
        print("  4. 如果Playwright浏览器未安装，程序会自动安装（需要几分钟）")
        print("  5. 访问 http://localhost:8080 使用系统")
    else:
        print("\n⚠ 未找到打包后的exe文件，请检查dist目录")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n打包已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
