# Joha 配置详解文档

## 1. 配置文件总览

| 配置文件 | 路径 | 用途 | 是否必填 |
|----------|------|------|----------|
| 连接配置 | `adapter/connection.yaml` | NapCatQQ WebSocket 连接参数 | 是 |
| 主配置 | `joha/config/config.json` | LLM、决策参数、Provider 等 | 是 |
| 回复决策配置 | `joha/config/reply_decision.json` | 回复概率参数（支持热加载） | 是 |
| 配置示例 | `joha/config/config.example.json` | 主配置模板 | 否 |

> **首次使用**: 复制示例配置文件并修改。

---

## 2. 连接配置 — `adapter/connection.yaml`

```yaml
napcat:
  ws_url: "ws://127.0.0.1:3002"      # NapCatQQ WebSocket 地址
  access_token: ""                    # 鉴权 Token（如需要）
  bot_uin: 8888888888                 # 机器人 QQ 号

settings:
  debug: true                         # 是否开启调试模式
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `napcat.ws_url` | string | `ws://127.0.0.1:3002` | NapCatQQ 的 WebSocket 正向连接地址 |
| `napcat.access_token` | string | `""` | WebSocket 鉴权 Token，无鉴权留空 |
| `napcat.bot_uin` | int/string | `8888888888` | 机器人的 QQ 号码 |
| `settings.debug` | bool | `true` | 调试模式开关，开启会输出更多日志 |

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
        "api_key": "sk-xxx",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "default": true
      },
      {
        "name": "alibaba",
        "label": "阿里云（通义千问）",
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
| `api_key` | string | 是 | API 密钥 |
| `base_url` | string | 是 | API 基础地址，需兼容 OpenAI 协议 |
| `model` | string | 是 | 模型名称 |
| `default` | bool | 否 | 是否为默认 Provider，仅一个可设为 true |

### 3.2 消息队列配置

```json
{
  "message_queue": {
    "enabled": true,
    "merge_window": 120.0,
    "max_queue_size": 5
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 是否启用消息队列合并 |
| `merge_window` | float | `120.0` | 合并时间窗口（秒），此时间内多条消息会合并处理 |
| `max_queue_size` | int | `5` | 最大队列长度，超出后直接触发决策 |

### 3.3 人设配置（如支持）

```json
{
  "persona": {
    "default": "college_student",
    "traits": {
      "extraversion": 7,
      "agreeableness": 6,
      "conscientiousness": 5,
      "neuroticism": 4,
      "openness": 8
    }
  }
}
```

**性格维度（0-10）：**

| 维度 | 说明 |
|------|------|
| `extraversion` | 外向性：越高越活跃、爱发言 |
| `agreeableness` | 宜人性：越高越友善、配合 |
| `conscientiousness` | 尽责性：越高越严谨、有条理 |
| `neuroticism` | 神经质：越高情绪越丰富 |
| `openness` | 开放性：越高越好奇、接受新事物 |

---

## 4. 回复决策配置 — `joha/config/reply_decision.json`

这是 Joha 最核心的调参区域，影响机器人的"话多话少"。

```json
{
  "thresholds": {
    "group": 0.55,
    "private": 0.4,
    "admin": 0.25
  },
  "feedback_weights": {
    "at_bot": 2.5,
    "reply_to_bot": 2.0,
    "mention_nickname": 1.5,
    "question": 1.3,
    "command": 3.0
  },
  "group_dynamic": {
    "very_busy_score": -0.8,
    "busy_score": -0.3,
    "normal_score": 0.0,
    "quiet_score": 0.2,
    "dead_score": 0.3
  },
  "content_quality": {
    "min_length_reward": 0.1,
    "max_length_penalty": -0.2,
    "spam_penalty": -1.0
  },
  "cooldown": {
    "enabled": true,
    "group_cooldown_seconds": 5,
    "global_cooldown_seconds": 2
  }
}
```

### 4.1 阈值参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `thresholds.group` | `0.55` | 群聊回复概率阈值，**越高越不爱说话** |
| `thresholds.private` | `0.4` | 私聊回复阈值 |
| `thresholds.admin` | `0.25` | 管理员消息回复阈值（通常更低，优先响应） |

> **调节建议**：
> - 机器人不说话 → 适当调低 `group`（如 `0.55` → `0.45`）
> - 机器人话太多 → 适当调高 `group`（如 `0.55` → `0.75`）

### 4.2 反馈权重参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `feedback_weights.at_bot` | `2.5` | 消息中@机器人时的权重加成 |
| `feedback_weights.reply_to_bot` | `2.0` | 回复机器人消息时的权重加成 |
| `feedback_weights.mention_nickname` | `1.5` | 提及机器人昵称时的权重加成 |
| `feedback_weights.question` | `1.3` | 消息包含疑问句时的权重加成 |
| `feedback_weights.command` | `3.0` | 触发命令时的权重加成 |

### 4.3 群动态调节参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `group_dynamic.very_busy_score` | `-0.8` | 非常活跃群的减分（抑制刷屏） |
| `group_dynamic.busy_score` | `-0.3` | 活跃群的减分 |
| `group_dynamic.normal_score` | `0.0` | 正常群无调整 |
| `group_dynamic.quiet_score` | `0.2` | 安静群的加分 |
| `group_dynamic.dead_score` | `0.3` | 冷清群的加分（提高存在感） |

### 4.4 内容质量参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `content_quality.min_length_reward` | `0.1` | 消息过短时的惩罚/长消息的奖励 |
| `content_quality.max_length_penalty` | `-0.2` | 消息过长时的惩罚 |
| `content_quality.spam_penalty` | `-1.0` | 垃圾信息检测到的惩罚 |

### 4.5 冷却参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `cooldown.enabled` | `true` | 是否启用冷却系统 |
| `cooldown.group_cooldown_seconds` | `5` | 单群冷却时间（秒） |
| `cooldown.global_cooldown_seconds` | `2` | 全局冷却时间（秒） |

---

## 5. 环境变量覆盖

配置管理器支持 `JOHA_` 前缀的环境变量来覆盖 JSON 配置中的值。

**映射规则：**
- `JOHA_LLM_ACTIVE_PROVIDER=deepseek` → 覆盖 `llm.active_provider`
- `JOHA_LLM_PROVIDERS_0_API_KEY=sk-xxx` → 覆盖 `llm.providers[0].api_key`

**常用环境变量：**

| 环境变量 | 说明 |
|----------|------|
| `JOHA_LLM_ACTIVE_PROVIDER` | 当前使用的 Provider 名称 |
| `JOHA_LLM_PROVIDERS_0_API_KEY` | 第一个 Provider 的 API Key |
| `JOHA_NAPCAT_WS_URL` | NapCat WebSocket 地址 |
| `JOHA_NAPCAT_ACCESS_TOKEN` | WebSocket 鉴权 Token |
| `JOHA_SETTINGS_DEBUG` | 调试模式开关 |

---

## 6. 热加载

`reply_decision.json` 支持**热加载**，修改后无需重启机器人。

**触发方式：**
1. 管理员在群内发送 `/知识库刷新` 命令
2. 代码中调用 `reply_cfg.reload()`

```python
from joha.decision.reply_decision import reply_cfg

# 手动触发重载
reply_cfg.reload()
print(reply_cfg.thresholds.group)
```

---

## 7. 配置校验清单

首次部署时，按以下清单确认配置：

- [ ] `adapter/connection.yaml` 已创建并填写正确
- [ ] `joha/config/config.json` 已创建并填写正确
- [ ] `joha/config/reply_decision.json` 已创建
- [ ] LLM API Key 已填入且有效
- [ ] NapCatQQ 已启动且 WebSocket 端口可达
- [ ] `bot_uin` 与实际机器人 QQ 号一致
