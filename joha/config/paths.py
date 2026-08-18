"""
路径常量
所有数据存储路径集中定义，运行时自动创建目录
"""
import os

# 项目根目录（joha/ 的上一级）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 数据存储根目录（项目根目录下 johadata/）
STORAGE_ROOT = os.path.join(PROJECT_ROOT, "johadata")

# 各子目录
HISTORY_DIR = os.path.join(STORAGE_ROOT, "history")
STYLES_DIR = os.path.join(STORAGE_ROOT, "styles")
PERSONAS_DIR = os.path.join(STORAGE_ROOT, "personas")
JOHALOG_DIR = os.path.join(STORAGE_ROOT, "johalog")
CONVERSATIONS_DIR = os.path.join(STORAGE_ROOT, "conversations")
MEMORY_DIR = os.path.join(STORAGE_ROOT, "memory")
GROUP_STATES_FILE = os.path.join(STORAGE_ROOT, "group_states.json")
GROUP_MODES_FILE = os.path.join(STORAGE_ROOT, "group_modes.json")
COOLDOWN_FILE = os.path.join(STORAGE_ROOT, "cooldown.json")
USER_PROFILES_FILE = os.path.join(STORAGE_ROOT, "user_profiles.json")

# 需要运行时自动创建的子目录
_SUBDIRS = [HISTORY_DIR, STYLES_DIR, PERSONAS_DIR, JOHALOG_DIR, CONVERSATIONS_DIR, MEMORY_DIR]


def ensure_storage_dirs() -> None:
    """运行时自动创建 storage 及其子目录"""
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    for d in _SUBDIRS:
        os.makedirs(d, exist_ok=True)


ensure_storage_dirs()
