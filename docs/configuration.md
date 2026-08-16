# Joha 配置详解文档

## 1. 配置文件总览

| 配置文件 | 路径 | 用途 | 是否必填 |
|----------|------|------|----------|
| 连接配置 | `joha/adapter/connection.yaml` | NapCatQQ WebSocket 连接参数 | 是 |
| 主配置 | `joha/config/config.json` | LLM Provider、admin、消息队列等 | 是 |
| 回复决策配置 | `joha/config/reply_decision.json` | 回复概率参数（支持热加载） | 是 |
| 配置示例 | `joha/config/config.example.json` | 主配置模板 | 否 |

> **首次使用**: 复制示例配置文件并修改。

---

## 2. 连接配置 — `joha/adapter/connection.yaml`

```yaml
napcat:
  ws_url: "ws://127.0.0.1:3002"      # NapCatQQ WebSocket 地址
  access_token: ""                    # 鉴权 Token（如需要）
  bot_uin: 8888888888                 # 机器人 QQ 号
  root: ""                            # 超级管理员 QQ 号（可选）
  webui_uri: http://127.0.0.1:6099    # NapCat WebUI 地址（可选）
  webui_token: ""                     # WebUI Token（如需要）

settings:
  debug: true                         # 是否开启调试模式
  hot_reload: false                   # 开发热重载开关

logging:
  level: INFO                         # 日志级别
  log_dir: log                        # 日志目录
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `napcat.ws_url` | string | `ws://127.0.0.1:3002` | NapCatQQ 的 WebSocket 正向连接地址 |
| `napcat.access_token` | string | `""` | WebSocket 鉴权 Token，无鉴权留空 |
| `napcat.bot_uin` | int/string | `8888888888` | 机器人的 QQ 号码 |
| `napcat.root` | string | `""` | 超级管理员 QQ 号 |
| `napcat.webui_uri` | string | `http://127.0.0.1:6099` | NapCat WebUI 地址 |
| `settings.debug` | bool | `true` | 调试模式开关，开启会输出更多日志 |
| `settings.hot_reload` | bool | `false` | 开发热重载开关（监控 joha/ 目录） |
| `logging.level` | string | `INFO` | 日志级别（DEBUG/INFO/WARNING/ERROR） |
| `logging.log_dir` | string | `log` | 日志目录 |

---

## 3. 主配置 — `joha/config/config.json`

### 3.1 LLM 配置

```json
{
  "llm": {
    "active_provider": "deepseek",
    "providers": [
      {
        "name": "deepseek",
        "label": "深度求索",
        "role": "chat",
        "api_key": "sk-xxx",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "default": true
      },
      {
        "name": "alibaba",
        "label": "阿里云（通义千问）",
        "role": "chat",
        "api_key": "sk-xxx",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3.5-omni-flash-2026-03-15"
      }
    ]
  }
}
```

**Provider 字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | string | 是 | Provider 唯一标识，用于 `/切换模型` 命令 |
| `label` | string | 否 | 显示名称 |
| `role` | string | 否 | 用途角色：`chat`（对话）/ `classifier`（意图分类）/ `tool_calling`（工具调用） |
| `api_key` | string | 是 | API 密钥 |
| `base_url` | string | 是 | API 基础地址，需兼容 OpenAI 协议 |
| `model` | string | 是 | 模型名称 |
| `default` | bool | 否 | 是否为该 role 的默认 Provider |
| `disabled` | bool | 否 | 是否禁用（配合 `disabled_reason`） |

### 3.2 管理员配置

```json
{
  "admin": {
    "admins": ["管理员QQ号1", "管理员QQ号2"],
    "target_users": ["不可删除的管理员QQ号"]
  }
}
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `admin.admins` | list[string] | 管理员 QQ 号列表 |
| `admin.target_users` | list[string] | 目标用户（不可被 `/删除管理员` 删除） |

### 3.3 消息队列配置

```json
{
  "message_queue": {
    "enabled": true,
    "merge_window": 120.0,
    "max_queue_size": 5,
    "min_messages_to_merge": 2
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 是否启用消息队列合并 |
| `merge_window` | float | `120.0` | 合并时间窗口（秒），此时间内多条消息会合并处理 |
| `max_queue_size` | int | `5` | 最大队列长度，超出后直接触发决策 |
| `min_messages_to_merge` | int | `2` | 最小合并消息数，至少 N 条消息才会因超时而处理 |

### 3.4 意图识别 / 工具调用配置（可选）

```json
{
  "intent_recognition": {
    "enabled": true,
    "provider_name": "teatop",
    "fallback_to_rules": true
  },
  "tool_calling": {
    "enabled": true,
    "provider_name": "deepseek"
  }
}
```

> 未配置时决策引擎自动回退到纯规则意图识别。

---

## 4. 回复决策配置 — `joha/config/reply_decision.json`

这是 Joha 最核心的调参区域，影响机器人的"话多话少"。完整结构：

```json
{
  "bot_nicknames": ["马苏", "joha", "机器人"],
  "thresholds": {
    "group": 0.55,
    "private": 0.4,
    "admin": 0.25,
    "busy": 0.7,
    "quiet": 0.45,
    "min": 0.15,
    "max": 0.85
  },
  "feedback_weights": {
    "at_bot": 2.5,
    "reply_to_bot": 2.0,
    "nickname": 2.0,
    "command": 3.0,
    "question": 1.5,
    "emotion": 1.2,
    "continuation": 1.0,
    "topic_relevance": 0.8,
    "spam_penalty": -1.5,
    "media_penalty": -0.5,
    "last_from_bot": -0.8,
    "active_human": -0.5
  },
  "group_dynamic": {
    "very_busy_mpm": 30,
    "very_busy_score": -0.8,
    "busy_mpm": 15,
    "busy_score": -0.4,
    "dead_mpm": 1,
    "dead_score": 0.3,
    "quiet_mpm": 3,
    "quiet_score": 0.1,
    "high_approval_rate": 0.7,
    "high_approval_score": 0.5,
    "low_approval_rate": 0.3,
    "low_approval_score": -0.4,
    "active_human_score": -0.5
  },
  "length_bonuses": {
    "too_short_max": 2,
    "too_short_score": -0.5,
    "good_short_max": 30,
    "good_short_score": 0.3,
    "too_long_min": 200,
    "too_long_score": -0.3,
    "rate_limit_score": -3.0
  },
  "spam_detection": {
    "block_intent_confidence": 0.5,
    "trigger_score": 0.5
  }
}
```

### 4.1 阈值参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `thresholds.group` | `0.55` | 群聊回复概率阈值，**越高越不爱说话** |
| `thresholds.private` | `0.4` | 私聊回复阈值 |
| `thresholds.admin` | `0.25` | 管理员消息回复阈值（通常更低，优先响应） |
| `thresholds.busy` | `0.7` | 活跃群回复阈值（消息频率 > busy_threshold_mpm 时使用） |
| `thresholds.quiet` | `0.45` | 冷清群回复阈值（消息频率 < quiet_threshold_mpm 时使用） |
| `thresholds.min` / `max` | `0.15` / `0.85` | 阈值调整的上下限 |

> **调节建议**：
> - 机器人不说话 → 适当调低 `group`（如 `0.55` → `0.45`）
> - 机器人话太多 → 适当调高 `group`（如 `0.55` → `0.75`）

### 4.2 反馈权重参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `feedback_weights.at_bot` | `2.5` | 消息中@机器人时的权重加成 |
| `feedback_weights.reply_to_bot` | `2.0` | 回复机器人消息时的权重加成 |
| `feedback_weights.nickname` | `2.0` | 提及机器人昵称时的权重加成 |
| `feedback_weights.command` | `3.0` | 触发命令时的权重加成 |
| `feedback_weights.question` | `1.5` | 消息包含疑问句时的权重加成 |
| `feedback_weights.emotion` | `1.2` | 情绪类消息的权重加成 |
| `feedback_weights.continuation` | `1.0` | 承接机器人上一条消息的权重 |
| `feedback_weights.topic_relevance` | `0.8` | 与群内热门话题相关的权重 |
| `feedback_weights.spam_penalty` | `-1.5` | 垃圾信息惩罚 |
| `feedback_weights.media_penalty` | `-0.5` | 纯媒体消息惩罚 |
| `feedback_weights.last_from_bot` | `-0.8` | 上一条是机器人回复时减分 |
| `feedback_weights.active_human` | `-0.5` | 活跃人工对话时减分 |

### 4.3 群动态调节参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `group_dynamic.very_busy_mpm` | `30` | 非常活跃群判定线（条/分钟） |
| `group_dynamic.very_busy_score` | `-0.8` | 非常活跃群的减分（抑制刷屏） |
| `group_dynamic.busy_mpm` | `15` | 活跃群判定线 |
| `group_dynamic.busy_score` | `-0.4` | 活跃群的减分 |
| `group_dynamic.quiet_mpm` | `3` | 安静群判定线 |
| `group_dynamic.quiet_score` | `0.1` | 安静群的加分 |
| `group_dynamic.dead_mpm` | `1` | 冷清群判定线 |
| `group_dynamic.dead_score` | `0.3` | 冷清群的加分（提高存在感） |
| `group_dynamic.high_approval_rate` | `0.7` | 高认可率判定线 |
| `group_dynamic.high_approval_score` | `0.5` | 高认可率加分 |
| `group_dynamic.low_approval_rate` | `0.3` | 低认可率判定线 |
| `group_dynamic.low_approval_score` | `-0.4` | 低认可率减分 |
| `group_dynamic.active_human_score` | `-0.5` | 活跃人工对话减分 |

### 4.4 内容质量参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `length_bonuses.too_short_max` | `2` | 过短消息判定上限（字） |
| `length_bonuses.too_short_score` | `-0.5` | 过短消息惩罚 |
| `length_bonuses.good_short_max` | `30` | 理想短消息上限（字） |
| `length_bonuses.good_short_score` | `0.3` | 理想短消息奖励 |
| `length_bonuses.too_long_min` | `200` | 过长消息判定下限（字） |
| `length_bonuses.too_long_score` | `-0.3` | 过长消息惩罚 |
| `length_bonuses.rate_limit_score` | `-3.0` | 用户被限流时的强惩罚 |

### 4.5 其他参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `bot_nicknames` | 列表 | 机器人昵称集合（提及即视为 @） |
| `continuation_coefficient` | `0.15` | 承接系数 |
| `topic_relevance_coefficient` | `0.15` | 话题相关系数 |
| `intent_pattern_multiplier` | `0.3` | 意图模式置信度乘数 |
| `feedback_adjustment_ratio` | `0.3` | 反馈调整幅度上限比例 |
| `feedback_side_multiplier` | `0.5` | 好评/差评的连带调整乘数 |
| `busy_threshold_mpm` | `25` | 切换到 busy 阈值的消息频率 |
| `quiet_threshold_mpm` | `2` | 切换到 quiet 阈值的消息频率 |

---

## 5. 环境变量

### 5.1 适配层环境变量

`joha/adapter/config.py` 会加载 `joha/adapter/.env` 文件（若存在），并支持系统环境变量：

| 环境变量 | 说明 |
|----------|------|
| `NAPCAT_WS_URL` | NapCat WebSocket 地址 |
| `NAPCAT_ACCESS_TOKEN` | WebSocket 鉴权 Token |
| `LOG_LEVEL` | 日志级别 |
| `LOG_DIR` | 日志目录 |
| `BOT_DEBUG` | 调试模式（true/false） |

### 5.2 主配置环境变量

`joha/config/config_manager.py` 的 `ConfigManager` 已**停用** JSON 环境变量覆盖（`_load_env_overrides()` 为空实现），LLM 等配置一律从 `config.json` 读取。

---

## 6. 热加载

`reply_decision.json` 支持**热加载**，修改后无需重启机器人。

```python
from joha.decision.reply_decision import reply_cfg

# 手动触发重载
reply_cfg.reload()
print(reply_cfg.thresholds.group)
```

> 决策配置采用懒加载：每次调用时读取最新值，`reload()` 用于清空缓存强制刷新。

另外，开发环境可在 `joha/adapter/connection.yaml` 中开启模块热重载：

```yaml
settings:
  hot_reload: true   # 监控 joha/ 目录，代码修改自动生效
```

---

## 7. 配置校验清单

首次部署时，按以下清单确认配置：

- [ ] `joha/adapter/connection.yaml` 已创建并填写正确
- [ ] `joha/config/config.json` 已创建并填写正确（复制自 config.example.json）
- [ ] `joha/config/reply_decision.json` 已存在
- [ ] LLM API Key 已填入且有效
- [ ] NapCatQQ 已启动且 WebSocket 端口可达
- [ ] `bot_uin` 与实际机器人 QQ 号一致
