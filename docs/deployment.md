# Joha 部署运维文档

## 1. 环境准备

### 1.1 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows / Linux / macOS | Linux (Ubuntu 20.04+) |
| Python | >= 3.10 | >= 3.11 |
| 内存 | 1 GB | 2 GB+ |
| 磁盘 | 500 MB | 2 GB+ |
| 网络 | 需访问 LLM API 端点 | 稳定的公网连接 |

### 1.2 前置软件

- **NapCatQQ**: 需在机器上运行 NapCatQQ 实例，并开启 WebSocket 正向连接
- **Python**: 确保 `python3 --version` >= 3.10
- **pip**: 用于安装依赖包

---

## 2. Python 环境配置

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 3. 配置文件部署

### 3.1 创建配置文件

```bash
# 主配置（复制示例文件）
cp joha/config/config.example.json joha/config/config.json

# joha/adapter/connection.yaml 已存在，直接编辑即可
```

### 3.2 编辑 connection.yaml

```yaml
napcat:
  ws_url: ws://127.0.0.1:3002           # NapCat WebSocket 地址
  access_token: ""                       # Token，无鉴权留空
  bot_uin: "你的机器人QQ号"              # 必填
  root: "你的管理员QQ号"                  # 超级管理员

settings:
  debug: true                            # 首次运行建议开启
  hot_reload: false                      # 生产环境建议关闭

logging:
  level: INFO                            # DEBUG/INFO/WARNING/ERROR
  log_dir: log                           # 日志目录
```

### 3.3 编辑 config.json

```json
{
  "llm": {
    "active_provider": "deepseek",
    "providers": [
      {
        "name": "deepseek",
        "label": "深度求索",
        "role": "chat",
        "api_key": "sk-你的密钥",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-v4-flash",
        "default": true
      }
    ]
  },
  "admin": {
    "admins": ["你的管理员QQ号", "另外的管理员QQ号"]
  }
}
```

---

## 4. NapCatQQ 部署

### 4.1 下载 NapCatQQ

从 [NapCatQQ GitHub](https://github.com/NapNeko/NapCatQQ) 下载最新版本。

### 4.2 配置 WebSocket

在 NapCatQQ 配置中启用 WebSocket 正向连接：

```json
{
  "ws": {
    "enable": true,
    "host": "0.0.0.0",
    "port": 3002
  }
}
```

### 4.3 登录

在 NapCatQQ WebUI（默认 http://localhost:6099）完成登录。

---

## 5. 启动机器人

### 5.1 开发模式（前台运行）

```bash
python run.py
```

### 5.2 后台运行

**Linux (使用 nohup):**

```bash
nohup python run.py > joha.out 2>&1 &
```

**Linux (使用 systemd):**

创建 `/etc/systemd/system/joha.service`：

```ini
[Unit]
Description=Joha Bot Service
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/JohaChat
ExecStart=/path/to/JohaChat/venv/bin/python run.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable joha
sudo systemctl start joha
sudo systemctl status joha
```

**Windows (使用任务计划程序):**

1. 打开"任务计划程序"
2. 创建基本任务 → 触发器：系统启动时
3. 操作：启动程序 `python run.py`
4. 起始于：`C:\Users\ASUS\Desktop\JohaChat`

---

## 6. 运行监控

### 6.1 查看实时日志

```bash
# Linux/macOS  
tail -f johadata/johalog/ai.log

# Windows PowerShell
Get-Content johadata/johalog/ai.log -Wait
```

### 6.2 在群内监控

```
/统计     # 查看运行统计
/群状态   # 查看当前群状态
/模式     # 查看当前模式
```

### 6.3 健康检查

```python
# 检查机器人是否在线
from joha.adapter import MessageClient

# 如果 MessageClient 正常运行且 WebSocket 连接正常，机器人即在线
```

---

## 7. 数据备份

### 7.1 需要备份的目录

| 路径 | 内容 | 重要程度 |
|------|------|----------|
| `johadata/styles/` | 风格学习数据 | 高 |
| `johadata/personas/` | 人设数据 | 高 |
| `johadata/history/` | 聊天历史 | 中 |
| `johadata/conversations/` | 群对话记忆 | 中 |
| `johadata/memory/` | 群长期记忆 | 中 |
| `johadata/user_profiles.json` | 用户画像 | 中 |
| `johadata/group_modes.json` | 群组模式 | 低 |
| `joha/config/config.json` | 配置文件 | 高 |

### 7.2 备份脚本（Linux）

```bash
#!/bin/bash
# backup.sh - Joha 数据备份脚本

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp -r johadata/styles "$BACKUP_DIR/"
cp -r johadata/personas "$BACKUP_DIR/"
cp -r johadata/history "$BACKUP_DIR/"
cp -r johadata/conversations "$BACKUP_DIR/"
cp -r johadata/memory "$BACKUP_DIR/"
cp joha/config/config.json "$BACKUP_DIR/"
cp johadata/user_profiles.json "$BACKUP_DIR/"

echo "备份完成: $BACKUP_DIR"
```

### 7.3 定时备份

```bash
# crontab -e
# 每天凌晨 2 点备份
0 2 * * * /path/to/JohaChat/backup.sh
```

---

## 8. 更新升级

### 8.1 更新步骤

```bash
# 1. 停止机器人
sudo systemctl stop joha

# 2. 备份数据
./backup.sh

# 3. 拉取最新代码
git pull origin main

# 4. 更新依赖
pip install -r requirements.txt

# 5. 检查配置文件变更
# 对比 config.example.json 看是否有新增配置项

# 6. 重启机器人
sudo systemctl start joha
```

### 8.2 配置文件合并

升级后，检查示例配置文件中是否有新增字段，手动合并到你的 `config.json` 中：

```bash
diff joha/config/config.example.json joha/config/config.json
```

---

## 9. 安全建议

1. **不要提交密钥**: 确保 `config.json` 和 `connection.yaml` 在 `.gitignore` 中
2. **使用环境变量**: 适配层敏感信息可通过 `.env` 或环境变量覆盖（`NAPCAT_WS_URL` 等）
3. **限制管理员**: 管理员 QQ 号应控制在最小范围
4. **定期更换密钥**: LLM API Key 定期更换
5. **日志清理**: 定期清理 `johadata/johalog/` 中的旧日志文件

---

## 10. 性能优化

### 10.1 冷却时间调优

如果 API 调用频繁，可增大冷却间隔（`joha/decision/cooldown.py` 中 `min_interval` 参数，默认 2 秒），或调整 `reply_decision.json` 中 `length_bonuses.rate_limit_score`（默认 -3.0，越负限制越强）。

### 10.2 消息队列优化

```json
{
  "message_queue": {
    "merge_window": 180.0,     // 增大窗口减少调用
    "max_queue_size": 8         // 增大队列容量
  }
}
```

### 10.3 LLM 选型建议

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 日常闲聊 | DeepSeek-V4-Flash | 性价比高，中文优秀 |
| 技术问答 | Qwen-Plus / DeepSeek | 技术能力强劲 |
| 高并发群 | 轻量模型 | 响应快，成本低 |
