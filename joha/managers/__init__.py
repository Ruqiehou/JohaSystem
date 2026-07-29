# 数据管理模块 - 用户数据和状态管理
from .history_manager import history_manager, load_history
from .user_profile import user_profile_manager, UserProfile
from .style_learner import style_learner
from .personas import (
    persona_manager, get_persona, get_persona_by_group,
    list_personas, persona_info, switch_persona,
    create_persona, delete_persona, rename_persona,
    set_group_persona, get_group_persona_name, get_bindings,
    update_traits, get_traits, apply_preset,
)
from .admin import admin_manager
from .group_conversation import group_conversation
from .group_memory import group_memory_manager

__all__ = [
    'history_manager', 'load_history',
    'user_profile_manager', 'UserProfile',
    'style_learner',
    'persona_manager', 'get_persona', 'get_persona_by_group',
    'list_personas', 'persona_info', 'switch_persona',
    'create_persona', 'delete_persona', 'rename_persona',
    'set_group_persona', 'get_group_persona_name', 'get_bindings',
    'update_traits', 'get_traits', 'apply_preset',
    'admin_manager',
    'group_conversation',
    'group_memory_manager',
]
