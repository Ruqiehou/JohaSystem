# Joha（约哈）— 智能群聊机器人

> 🤖 基于 LLM 的智能群聊机器人框架，支持多模型切换、智能回复决策、风格学习。

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-3.7.0-green.svg)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [配置说明](#-配置说明) • [命令参考](#-命令参考) • [架构说明](#-架构说明) • [更新日志](CHANGELOG.md)

</div>

***

## ✨ 功能特性

### 🎯 核心能力

| 特性         | 说明                                          |
| ---------- | ------------------------------------------- |
| **智能决策**   | 基于概率计算（Logit 累加 + Sigmoid 归一化）判断是否回复，避免废话刷屏 |
| **多模型切换**  | 运行时动态切换 AI 模型（DeepSeek / 通义千问 / Gemini 等）   |
| **消息队列合并** | 短时间内的多条消息自动合并，减少不必要的回复                      |
| **多模态支持**  | 支持图片理解（Qwen-VL、GPT-4o 等视觉模型）需自行配置           |
| **群组动态调节** | 根据群活跃度、消息频率、认可率自动调整回复阈值                     |

### 🚀 进阶能力

| 特性          | 说明                                      |
| ----------- | --------------------------------------- |
| **风格学习**    | 自动学习群成员说话风格，使回复更自然融入群聊                  |
| **人设管理**    | 基于多维度参数的精细化人设系统，支持动态调整性格特质、表达风格、社交行为等参数 |
| **工具调用**    | 支持搜索、网页抓取等工具                            |
| **主动/被动模式** | 支持全局和逐群设置主动/被动回复模式                      |
| **冷却系统**    | 防刷屏机制，避免频繁回复                            |
| **用户画像**    | 记录用户偏好和聊天习惯                             |
| **管理员系统**   | 多级权限管理，管理员专属命令                          |

***

## 🚀 快速开始

### 📋 环境要求

- **Python**: >= 3.10

- **消息平台**: 运行中的 NapCatQQ（或其他兼容 OneBot 协议的消息平台）

  - 下载: [NapCatQQ GitHub](https://github.com/NapNeko/NapCatQQ)

  - 确保 WebSocket 端口（默认 3002）开放

### 📦 安装步骤

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd JohaChat

# 2. 安装依赖
pip install -r requirements.txt

# 3. 先配置并启动 NapCat
#    在 NapCat 中开启 OneBot WebSocket 正向连接
#    记下 ws_url、access_token（如有）、机器人 QQ 号

# 4. 配置 AI API Key
#    复制配置示例文件
cp joha/config/config.example.json joha/config/config.json
#    编辑 joha/config/config.json，填入你的 API Key

# 5. 修改 joha/adapter/connection.yaml 中的连接参数
#    napcat:
#      ws_url: ws://127.0.0.1:3002
#      access_token: ""
#      bot_uin: "你的机器人QQ号"

# 6. 如需临时覆盖连接配置，可直接编辑 run.py 中的 RUN_CONNECT_CONFIG
#    例如：
#    RUN_CONNECT_CONFIG = {
#        "ws_url": "ws://127.0.0.1:3002",
#        "access_token": "",
#        "bot_uin": "1234567890",
#        "debug": True,
#    }

# 7. 运行机器人
python run.py
```

> 如果 `run.py` 中的 `bot_uin` 与当前 NapCat 登录账号不一致，程序会直接停止连接，避免接错机器人账号。

### 📚 依赖清单

| 依赖              | 版本      | 用途                              |
| --------------- | ------- | ------------------------------- |
| `websockets`    | >=12.0  | WebSocket 客户端（连接 NapCatQQ 消息平台） |
| `openai`        | >=1.0.0 | LLM API 调用（兼容 OpenAI 协议）        |
| `pyyaml`        | >=6.0   | YAML 配置解析                       |
| `python-dotenv` | >=1.0.0 | 环境变量管理（可选）                      |
| `watchdog`      | >=3.0.0 | 开发热重载（可选）                       |

***

## ⚙️ 配置说明

### 📝 配置文件概览

| 配置文件                                 | 用途                                  |
| ------------------------------------ | ----------------------------------- |
| **joha/adapter/connection.yaml**     | NapCat 连接配置（WebSocket 地址、机器人 QQ 号等） |
| **joha/config/config.json**          | 机器人主配置（LLM Provider、API Key 等）      |
| **joha/config/reply\_decision.json** | 回复决策参数（独立配置，热加载）                    |

> 💡 **首次使用**: 复制示例配置文件并修改：
>
> ```bash
> cp joha/config/config.example.json joha/config/config.json
> ```

### 1️⃣ 连接配置 — `joha/adapter/connection.yaml`

NapCat WebSocket 连接参数：

```yaml
napcat:
  ws_url: ws://127.0.0.1:3002    # NapCat WebSocket 地址
  access_token: ""                # 鉴权 Token（如需要）
  bot_uin: "8888888888"           # 机器人 QQ 号
  root: ""                        # 超级管理员 QQ 号
  webui_uri: http://127.0.0.1:6099  # NapCat WebUI 地址
  webui_token: ""                 # WebUI Token（如需要）

settings:
  debug: true                     # 调试模式
  hot_reload: false               # 开发热重载开关

logging:
  level: INFO                     # 日志级别
  log_dir: log                    # 日志目录
```

### 2️⃣ LLM 配置 — `joha/config/config.json`

可配置多个 Provider，运行时通过命令切换：

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
  },
  "admin": {
    "admins": ["你的管理员QQ号"]
  },
  "message_queue": {
    "enabled": true,
    "merge_window": 120.0,
    "max_queue_size": 5,
    "min_messages_to_merge": 2
  }
}
```

### 3️⃣ 回复决策参数 — `joha/config/reply_decision.json`

核心调参区域，影响机器人的"话多话少"：

| 参数                              | 默认值  | 说明                |
| ------------------------------- | ---- | ----------------- |
| `thresholds.group`              | 0.55 | 群聊回复概率阈值（越高越不爱说话） |
| `thresholds.private`            | 0.4  | 私聊回复阈值            |
| `thresholds.admin`              | 0.25 | 管理员回复阈值           |
| `thresholds.busy`               | 0.7  | 活跃群回复阈值           |
| `thresholds.quiet`              | 0.45 | 冷清群回复阈值           |
| `feedback_weights.at_bot`       | 2.5  | @机器人时的权重加成        |
| `feedback_weights.command`      | 3.0  | 触发命令时的权重加成        |
| `group_dynamic.very_busy_score` | -0.8 | 非常活跃群减分           |
| `group_dynamic.dead_score`      | 0.3  | 冷清群加分             |

> 💡 修改后无需重启，执行 `reply_cfg.reload()` 即可热加载

### 📨 消息队列配置

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

- `merge_window`: 合并时间窗口（秒），此时间内多条消息会合并处理

- `max_queue_size`: 最大队列长度，超出后直接触发决策

- `min_messages_to_merge`: 最小合并消息数（至少 N 条消息才会因超时而处理）

***

## 📖 命令参考

### 👥 全员可用命令

| 命令     | 别名      | 说明            |
| ------ | ------- | ------------- |
| `/好评`  | `/good` | 记录正面反馈，调整决策参数 |
| `/差评`  | `/bad`  | 记录负面反馈，调整决策参数 |
| `/群状态` | —       | 查看当前群的运行状态详情  |

### 🔧 管理员命令

| 命令                | 说明                | <br /> | <br /> |
| ----------------- | ----------------- | :----- | :----- |
| `/帮助`             | 显示命令帮助列表          | <br /> | <br /> |
| `/全局启动`           | 全局切换到主动模式（主动回复）   | <br /> | <br /> |
| `/全局关闭`           | 全局切换到被动模式（仅被@时回复） | <br /> | <br /> |
| `/本群启动`           | 本群切换到主动模式         | <br /> | <br /> |
| `/本群关闭`           | 本群切换到被动模式         | <br /> | <br /> |
| `/模式`             | 查看当前全局模式          | <br /> | <br /> |
| `/模式 <群号>`        | 查看指定群的模式          | <br /> | <br /> |
| `/管理员列表`          | 查看所有管理员           | <br /> | <br /> |
| `/添加管理员 <ID>`     | 添加管理员             | <br /> | <br /> |
| `/删除管理员 <ID>`     | 删除管理员             | <br /> | <br /> |
| `/模型`             | 查看可用模型列表          | <br /> | <br /> |
| `/当前模型`           | 查看当前使用的模型         | <br /> | <br /> |
| `/模型状态`           | 模型状态提示            | <br /> | <br /> |
| `/切换模型 <名称>`      | 切换到指定模型           | <br /> | <br /> |
| `/风格 <ID>`        | 查看用户的风格学习数据       | <br /> | <br /> |
| `/清除风格 <ID>`      | 清除用户的风格数据         | <br /> | <br /> |
| `/统计`             | 查看机器人运行统计         | <br /> | <br /> |
| `/人设列表`           | 查看所有人设            | <br /> | <br /> |
| `/人设信息 [名称]`      | 查看人设详情            | <br /> | <br /> |
| `/切换人设 <名称>`      | 切换全局活跃人设          | <br /> | <br /> |
| `/绑定人设 [群号] <名称>` | 绑定群到指定人设          | <br /> | <br /> |
| \`/创建人设 <名称>      | 显示名               | 描述\`   | 创建新人设  |
| `/删除人设 <名称>`      | 删除人设（不可删除默认人设）    | <br /> | <br /> |
| `/人设`             | 查看人设稳定性报告         | <br /> | <br /> |

> 💡 **提示**: 许多命令支持自然语言别名触发，例如发送"帮助"会自动转为`/帮助`，发送"模型列表"会自动转为`/模型`。

***

## 🏗️ 架构说明

### 项目结构

```
run.py                     ← 统一启动入口
  │
  ├─ storage/              ← 运行时数据（自动创建）
  │    ├─ history/             — 聊天历史
  │    ├─ conversations/       — 群对话记忆
  │    ├─ memory/              — 群长期记忆
  │    ├─ styles/              — 风格学习数据
  │    ├─ personas/            — 人设数据
  │    └─ johalog/             — 运行日志
  │
  └─ joha/                 ← 核心包
       ├─ adapter/         ← NapCat 适配层
       │    ├─ transport/      — 传输层：NapCatClient（WebSocket 连接管理）
       │    ├─ protocol/       — 协议层：BotAPI、事件模型、消息段构建
       │    ├─ core/           — 兼容导出层（re-export）
       │    ├─ message_client.py — 封装层：MessageClient（事件注册与路由）
       │    ├─ config.py       — YAML 配置管理、日志系统
       │    └─ connection.yaml — 连接配置文件
       │
       ├─ core/            ← 编排入口层（扁平结构）
       │    ├─ message_handler.py   — 消息接收、@/回复检测、队列合并
       │    ├─ service.py           — 核心业务逻辑（学习 + 回复分离）
       │    ├─ commands.py          — 命令处理
       │    ├─ message_builder.py   — 上下文组装
       │    ├─ message_queue.py     — 消息队列合并
       │    ├─ runtime_context.py   — 运行时上下文
       │    ├─ persona_monitor.py   — 人设监控
       │    ├─ tool_registry.py     — 工具注册表（自动发现）
       │    ├─ response_postprocessor.py — 回复后处理
       │    ├─ image_utils.py       — 图片格式转换
       │    ├─ clean_history.py     — 历史记录清洗
       │    └─ hot_reload.py        — 开发热重载
       │
       ├─ ai/              ← AI 驱动层
       │    ├─ clients.py        — AI 客户端抽象（多 Provider 适配）
       │    ├─ providers.py      — Provider 管理器
       │    ├─ bot.py            — ChatEngine 聊天引擎
       │    ├─ generator.py      — 回复生成器
       │    └─ classifier.py     — 意图分类器
       │
       ├─ decision/        ← 决策大脑层
       │    ├─ decision_engine.py  — 决策引擎（总分架构"总"，含 CommandAnalyzer）
       │    ├─ reply_decision.py   — 回复决策（Logit + Sigmoid，含配置）
       │    ├─ intent_classifier.py— 意图识别（纯规则）
       │    ├─ group_state.py      — 群组状态追踪
       │    └─ cooldown.py         — 冷却管理
       │
       ├─ tools/           ← 工具层
       │    ├─ search/           — 网络搜索工具
       │    └─ webpage/          — 网页抓取工具
       │
       ├─ managers/        ← 数据管理层
       │    ├─ personas.py       — 人设管理
       │    ├─ style_learner.py  — 风格学习
       │    ├─ history_manager.py— 历史记录
       │    ├─ user_profile.py   — 用户画像
       │    ├─ group_conversation.py — 群对话记忆
       │    ├─ group_memory.py    — 群长期记忆
       │    └─ admin.py          — 管理员管理
       │
       └─ config/         ← 配置与基础设施（扁平结构）
            ├─ config_manager.py  — 主配置管理器
            ├─ group_mode_config.py — 群组模式配置
            ├─ logger.py          — 日志系统
            ├─ cache.py           — LRU 缓存
            ├─ paths.py           — 存储路径定义
            └─ reply_decision.json — 回复决策参数
```

### 🔄 消息处理流程

```
群消息 → NapCatQQ
         → WebSocket → NapCatClient (传输层)
         → MessageClient (封装层)
         → MessageHandler.process_group_message()
            → 消息文本/图片提取
            → 命令预处理（斜杠命令直通返回）
            → @/回复检测
            → 消息队列合并（短时间多条消息）
            → MessageService.process_message()
                → 判断群组模式（active/passive）
                → 学习阶段：记录历史 + 学习风格
                → 决策阶段：DecisionEngine.process() 流水线
                   (build_context → intent 检测 → compute_reply_prob → should_reply)
                → 生成阶段：构建上下文 → 调用 Generator → 返回回复
            → BotAPI.send_group_message() 发送回复到群聊
```

### 🎲 回复决策引擎

决策引擎是 Joha 的核心亮点，采用**总分架构**：决策引擎（总）编排全局，各子模块（分）专注单一职责。

1. **反馈权重层**：是否被@、是否被回复、是否提及昵称、是否包含疑问
2. **场景阈值层**：根据群活跃度、消息频率动态调整阈值（busy/quiet 阈值切换）
3. **群动态调节**：非常活跃群降低回复概率，冷清群提高回复概率，认可率调节
4. **内容质量**：消息长度奖励/惩罚、垃圾信息检测
5. **意图融合**：纯规则意图识别 + 可选 AI 意图分类，加权融合
6. **冷却管理**：防止短时间内连续回复（群级 + 用户级）

最终概率通过 Sigmoid 函数归一化到 \[0, 1]，与阈值比较决定是否回复。

### 🧰 工具系统

工具层 `joha/tools/` 采用**模块化**模式，每个工具独立封装，支持两种风格：

| 工具          | 说明              |
| ----------- | --------------- |
| **search**  | 网络搜索（可配置搜索 API） |
| **webpage** | 网页内容抓取          |

- **类风格**: `SearchTool` / `WebpageTool`

- **函数+元信息风格**: `execute()` + `TOOL_META`（供 ToolRegistry 自动发现）

### ⚙️ Config 模块结构

Config 模块采用扁平结构，所有模块直接在 `joha/config/` 下：

| 子模块                    | 职责                              |
| ---------------------- | ------------------------------- |
| config\_manager.py     | JSON 配置管理（LLM Provider、admin 等） |
| group\_mode\_config.py | 逐群 active/passive 模式管理          |
| logger.py              | 多级别日志、文件轮转、预定义记录器               |
| cache.py               | LRU 缓存、TTL 过期、函数结果缓存装饰器         |
| paths.py               | 存储路径集中定义，运行时自动创建目录              |

***

## 🔧 高级配置

### 🌍 环境变量

适配层支持 `.env` 文件（位于 `joha/adapter/.env`）加载环境变量，也可直接使用系统环境变量（如 `NAPCAT_WS_URL`、`NAPCAT_ACCESS_TOKEN`、`LOG_LEVEL`、`LOG_DIR`、`BOT_DEBUG`）。

### 🎮 运行模式

| 模式                 | 说明                |
| ------------------ | ----------------- |
| **主动模式 (active)**  | 机器人根据决策引擎自动判断是否回复 |
| **被动模式 (passive)** | 仅在被@、被回复或触发命令时回复  |

可通过 `/全局启动`、`/全局关闭`、`/本群启动`、`/本群关闭` 命令切换。

### 🔄 多 Provider 策略

配置多个 LLM Provider 后，可在运行时通过 `/切换模型 <名称>` 动态切换，无需重启机器人。不同的 Provider 可用于不同的角色（`role` 字段）：

- **chat**：主动聊天使用的模型

- **classifier**：可单独配置意图分类专用模型

- **tool\_calling**：可单独配置工具调用专用模型

### 👤 人设系统

Joha 使用基于多维度参数的精细化人设系统，通过调整性格特质、表达风格、社交行为等参数来塑造角色：

- **性格维度**：外向性、宜人性、尽责性、神经质、开放性（0-10）

- **表达风格**：话痨程度、正式度、情感表达、幽默感、自信度（0-10）

- **社交行为**：热情度、礼貌度、好奇心、共情力、耐心值（0-10）

- **语言特征**：表情符号、网络用语、语气词、打字错误容忍、句子长度

- **话题偏好**：感兴趣的话题、避免的话题、情绪倾向

支持多人设管理：通过 `/人设列表`、`/切换人设`、`/创建人设`、`/绑定人设` 等命令管理，可为不同群绑定不同人设。默认人设为"大学生"角色，可通过 `/人设` 命令查看当前人设稳定性报告。

***

## 📁 目录结构

```
JohaChat/
├── run.py                   # 统一启动入口
├── requirements.txt         # Python 依赖
├── README.md                # 本文件
├── CHANGELOG.md             # 更新日志
│
├── storage/                 # 运行时数据（自动创建）
│
├── joha/                    # 核心代码包
│   ├── adapter/            # NapCat 适配层（传输/协议/兼容导出）
│   ├── core/               # 编排入口层
│   ├── ai/                 # AI 驱动层
│   ├── decision/           # 决策大脑层
│   ├── tools/              # 工具层
│   ├── managers/           # 数据管理层
│   └── config/             # 配置与基础设施
│
├── tests/                   # 单元测试
└── docs/                    # 文档目录
```

### 💾 存储目录 `storage/`

| 文件                   | 说明             |
| -------------------- | -------------- |
| `group_states.json`  | 群组状态持久化        |
| `group_modes.json`   | 群组模式配置         |
| `user_profiles.json` | 用户画像数据         |
| `cooldown.json`      | 冷却状态           |
| `history/`           | 聊天历史记录（按用户分文件） |
| `conversations/`     | 群对话记忆（按群分文件）   |
| `memory/`            | 群长期记忆（按群分文件）   |
| `styles/`            | 风格学习数据         |
| `personas/`          | 人设数据           |
| `johalog/`           | 运行日志文件         |

***

## ❓ 常见问题

<details>
<summary><b>🤔 Q: 机器人不说话？</b></summary>

- 检查是否处于被动模式（使用 `/模式` 查看）

- 检查 `reply_decision.json` 中 `thresholds.group` 是否过高，可适当调低（如从 0.55 调到 0.45）

- 检查 API Key 是否正确配置

- 检查 NapCatQQ 是否正常运行且 WebSocket 端口开放

- 查看日志文件 `storage/johalog/ai.log` 排查错误

</details>

<details>
<summary><b>💬 Q: 机器人话太多？</b></summary>

- 调高 `thresholds.group`（如 0.55 → 0.75）

- 切换到被动模式：`/全局关闭`

- 调大冷却时间

- 启用消息队列合并功能

</details>

<details>
<summary><b>🔄 Q: 如何添加更多 AI 模型？</b></summary>

在 `joha/config/config.json` 的 `llm.providers` 数组中添加新的 Provider 配置，只需 API 兼容 OpenAI 协议即可。

示例：

```json
{
  "name": "your_provider",
  "label": "自定义模型",
  "role": "chat",
  "api_key": "your-api-key",
  "base_url": "https://api.example.com/v1",
  "model": "model-name",
  "default": false
}
```

</details>

<details>
<summary><b> Q: 消息平台怎么连接？</b></summary>

Joha 通过 adapter 模块直连 NapCatQQ，无需第三方消息适配器库。在 `joha/adapter/connection.yaml` 中配置 WebSocket 地址：

```yaml
napcat:
  ws_url: ws://127.0.0.1:3002    # 与 NapCatQQ 设置的端口一致
  bot_uin: "你的机器人QQ号"
```

确保 NapCatQQ 已启动且 WebSocket 服务正常，然后运行 `python run.py`。

</details>

***

## 📄 许可证

本项目基于 MIT 许可证开源。

***

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，欢迎通过 GitHub Issues 联系。

***

<div align="center">

**Made with ❤️ by Joha Team**

⭐ 如果这个项目对你有帮助，请给我们一个 Star！

</div>
