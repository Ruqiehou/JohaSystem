# Joha 故障排查文档

## 1. 机器人不说话

### 1.1 现象描述

群内正常聊天，但机器人没有任何回复。

### 1.2 排查步骤

**步骤 1：检查运行模式**

在群里发送 `/模式`，查看是否处于"被动模式"或"全局关闭"状态。

```
# 解决方式
/全局启动    # 切换为全局主动模式
/本群启动    # 当前群切换为主动模式
```

**步骤 2：检查回复决策配置**

```bash
# 查看回复阈值
cat joha/config/reply_decision.json | grep -A 5 thresholds
```

如果 `thresholds.group` 过高（如 > 0.75），机器人会非常沉默。尝试调低：

```json
{
  "thresholds": {
    "group": 0.45
  }
}
```

修改后通过 `reply_cfg.reload()` 热加载（代码内调用），或重启机器人。

**步骤 3：检查 LLM 配置**

```bash
# 查看配置
cat joha/config/config.json | grep -A 5 "active_provider"

# 测试 API 连接
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     https://api.deepseek.com/v1/chat/completions \
     -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"你好"}]}'
```

如果 API 报错：
- 检查 API Key 是否正确
- 检查 `base_url` 是否可访问
- 检查模型名称是否正确

**步骤 4：检查 NapCatQQ 连接**

```bash
# 查看日志
tail -f storage/johalog/ai.log

# 查找连接状态
grep -i "connect\|websocket\|error" storage/johalog/ai.log
```

确认：
- NapCatQQ 是否在运行
- WebSocket 端口（默认 3002）是否开放
- `joha/adapter/connection.yaml` 中的 `ws_url` 是否正确

**步骤 5：检查冷却状态**

如果机器人刚回复过，可能处于冷却期：

```
/群状态   # 查看冷却剩余时间
```

---

## 2. 机器人回复异常

### 2.1 回复内容混乱/答非所问

**可能原因：**

1. **上下文窗口溢出**：历史消息过多导致 LLM 丢失上下文
2. **人设参数异常**：人设配置被意外修改
3. **风格学习数据异常**：学到的异常风格干扰回复

**解决方式：**

```bash
/人设          # 检查人设稳定性报告
/人设信息      # 查看人设参数详情
/清除风格 <ID> # 清理异常的风格学习数据
```

### 2.2 回复过于频繁（刷屏）

**解决方式：**

```
/全局关闭    # 切换到被动模式
/本群关闭    # 当前群切换到被动模式
```

或调整 `reply_decision.json`：

```json
{
  "thresholds": {
    "group": 0.75
  },
  "feedback_weights": {
    "at_bot": 2.5,
    "command": 3.0
  }
}
```

### 2.3 回复内容被截断

检查 LLM 的 `max_tokens` 配置（`joha/ai/generator.py` 中 `generator.chat()` 的 `max_tokens` 参数，默认 1024）。

---

## 3. 命令无响应

### 3.1 排查步骤

**步骤 1：确认命令格式**

Joha 的命令必须以 `/` 开头，如 `/帮助`、`/模式`。也支持自然语言别名（如"帮助"、"模型列表"）。

**步骤 2：检查权限**

```
/管理员列表    # 确认发送者是否为管理员
```

部分命令仅管理员可用：
- `/全局启动`、`/全局关闭`
- `/添加管理员`、`/删除管理员`
- `/切换模型`
- 人设管理类命令

**步骤 3：查看日志**

```bash
tail -f storage/johalog/ai.log | grep -i "command\|命令"
```

---

## 4. 连接问题

### 4.1 WebSocket 连接失败

**现象：** 机器人启动后立即退出或报连接错误。

**排查：**

```bash
# 1. 确认 NapCatQQ 是否在运行
ps -ef | grep napcat    # Linux
tasklist | findstr napcat    # Windows

# 2. 确认端口是否开放
netstat -an | grep 3002       # Linux
netstat -an | findstr 3002    # Windows

# 3. 检查防火墙
# 确保 3002 端口未被防火墙阻止
```

**常见原因及解决：**

| 原因 | 解决方式 |
|------|----------|
| NapCatQQ 未启动 | 启动 NapCatQQ |
| 端口不正确 | 检查 NapCatQQ 配置中的 WebSocket 端口 |
| 防火墙阻止 | 放行对应端口或使用 127.0.0.1 |
| YAML 解析错误 | 检查 `joha/adapter/connection.yaml` 格式 |
| `access_token` 不匹配 | 留空或填写正确 Token |
| `bot_uin` 与 NapCat 登录账号不一致 | 修改 `run.py` 或 connection.yaml 中的 `bot_uin` |

### 4.2 连接频繁断开

**可能原因：**
- 网络不稳定
- NapCatQQ 重启/崩溃
- WebSocket 超时

**解决方式：**
- MessageClient 内置自动重连机制
- 使用 systemd/supervisor 守护进程

---

## 5. API 调用错误

### 5.1 错误码对照

| 错误码 | 含义 | 解决方式 |
|------|------|----------|
| `401` | API Key 无效 | 检查 `api_key` |
| `403` | 无权限/配额不足 | 检查 API 账户状态和余额 |
| `404` | 模型/端点不存在 | 检查 `model` 和 `base_url` |
| `429` | 请求速率限制 | 增大冷却时间或降频 |
| `500` | 服务端错误 | 等待后重试或切换 Provider |

### 5.2 调试 API 调用

```python
from joha.ai.clients import create_client_from_provider
from joha.ai.providers import provider_manager
import asyncio

async def test_api():
    provider = provider_manager.get_default("chat")
    if not provider:
        print("未配置 LLM Provider")
        return
    client = create_client_from_provider(provider, client_type="chat", enable_tools=False)
    try:
        resp = await client.call_with_context(
            messages=[{"role": "user", "content": "你好"}],
            temperature=0.7,
            max_tokens=100,
        )
        print(resp)
    except Exception as e:
        print(f"API 调用失败: {e}")

asyncio.run(test_api())
```

---

## 6. 性能问题

### 6.1 消息处理变慢

**排查：**

1. 历史记录是否过多（检查 `storage/history/` 下的文件数量和大小）
2. 群对话记忆 / 长期记忆是否过大（`storage/conversations/`、`storage/memory/`）
3. 系统资源是否充足（CPU、内存）

**解决：**

```bash
# 清理旧历史记录
rm -rf storage/history/old_*.json   # 谨慎操作
```

### 6.2 内存占用过高

**检查：**

```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"内存占用: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

**解决：**
- 减少同时服务的群数量
- 启用消息历史上限
- 定期重启（可通过 systemd 的定时重启策略）

---

## 7. 数据丢失恢复

### 7.1 恢复损坏的配置

如果 `config.json` 损坏，基于 `config.example.json` 重新创建：

```bash
cp joha/config/config.example.json joha/config/config.json
# 然后重新填写 API Key 和管理员信息
```

### 7.2 恢复群组模式 / 冷却数据

这些数据为 JSON 文件，损坏时可直接删除让系统重建：

```bash
# 群组模式 / 冷却状态 / 用户画像
rm storage/group_modes.json
rm storage/cooldown.json
rm storage/user_profiles.json
```

> 删除后对应功能会自动重新初始化，不会导致崩溃。

---

## 8. 日志分析

### 8.1 关键日志关键词

| 关键词 | 含义 |
|------|------|
| `[connect]` | WebSocket 连接状态 |
| `[消息]` | 消息收发记录 |
| `[决策]` | 决策引擎计算过程 |
| `[AI]` | LLM API 调用记录 |
| `[Generator]` | 回复生成记录 |
| `[ToolRegistry]` | 工具注册状态 |
| `error` | 错误信息 |

### 8.2 快速诊断命令

```bash
# 最近 50 条错误
grep "error\|ERROR" storage/johalog/ai.log | tail -50

# 查看 API 调用延迟
grep "AI\|API" storage/johalog/ai.log | tail -20

# 查看命令执行历史
grep "command\|命令" storage/johalog/ai.log | tail -20
```
