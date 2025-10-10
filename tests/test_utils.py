"""
测试辅助工具
提供测试脚本的通用功能
"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 配置文件路径
CONFIG_PATH = PROJECT_ROOT / "config.json"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 源代码目录
SRC_DIR = PROJECT_ROOT / "src"


def get_config_path() -> Path:
    """获取配置文件路径"""
    return CONFIG_PATH


def get_output_path(filename: str) -> Path:
    """获取输出文件路径"""
    return OUTPUT_DIR / filename


def get_src_path() -> Path:
    """获取源代码目录路径"""
    return SRC_DIR
