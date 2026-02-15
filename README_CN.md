<div align="center">

# cselab

**在本地运行 UNSW CSE 服务器命令 — 快速、可靠、支持交互**

English | [简体中文](README_CN.md)

</div>

---

## 为什么需要 cselab？

UNSW CSE 学生需要在 CSE 服务器 (`cse.unsw.edu.au`) 上运行 `autotest`、`give` 等课程命令。传统流程：

1. SSH 连接到 CSE 服务器
2. 在服务器上编辑代码（或来回手动复制文件）
3. 运行命令
4. 重复以上步骤

这很痛苦。你无法使用本地编辑器、插件和工具，或者浪费大量时间手动复制文件。

**cselab 让你在本地写代码，像在服务器上一样运行 CSE 命令。** 一条命令同步文件并远程执行 — 你的 VS Code / Vim 环境完全不受影响。

## 工作原理

```
本地机器（你的笔记本）                  CSE 服务器
┌─────────────────────────┐              ┌──────────────────────┐
│  ~/COMP1521/lab01/      │   1. SSH     │  ControlMaster       │
│    hello.c              │──────────────│  (持久连接)          │
│    Makefile             │              │                      │
│                         │   2. rsync   │  ~/.cselab/          │
│                         │──────────────│    workspaces/       │
│                         │  (增量传输)  │      lab01-a3f2/     │
│                         │              │        hello.c       │
│                         │   3. ssh     │        Makefile      │
│                         │──────────────│                      │
│                         │  (执行)      │  $ 1521 autotest     │
│  终端:                  │   4. 输出    │                      │
│  ✅ All tests passed    │◄─────────────│                      │
└─────────────────────────┘              └──────────────────────┘
```

## 安装

**要求：** Python 3.10+、`rsync`、`ssh`（macOS 和大多数 Linux 已预装）

### 一键安装（推荐）

```bash
curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/master/install.sh | bash
```

### pip 安装

```bash
pip install git+https://github.com/Genius-Cai/cselab.git
```

### 克隆安装

```bash
git clone https://github.com/Genius-Cai/cselab.git
cd cselab && pip install .
```

## 快速开始

```bash
# 1. 首次配置
cselab init
# 输入 zID 和密码

# 2. 进入作业目录
cd ~/COMP1521/lab01

# 3. 运行 CSE 命令
cselab run "1521 autotest"
```

## 命令一览

| 命令 | 说明 |
|------|------|
| `cselab init` | 初始化配置（zID + 密码）|
| `cselab run "<命令>"` | 同步文件 + 在 CSE 运行命令 |
| `cselab run --no-sync "<命令>"` | 跳过同步，直接运行 |
| `cselab sync` | 仅同步文件 |
| `cselab pull` | 从服务器拉取文件到本地 |
| `cselab ssh` | 打开交互式 SSH 会话 |
| `cselab watch "<命令>"` | 监听文件变化，自动运行 |
| `cselab clean` | 清理远程工作目录 |
| `cselab config` | 显示配置文件 |
| `cselab disconnect` | 关闭 SSH 连接 |

## 使用示例

```bash
# 自动测试
cselab run "1521 autotest"

# 提交作业
cselab run "give cs1521 lab01 hello.s"

# 编译 + 运行
cselab run "make && ./test"

# 监听模式（保存即测试）
cselab watch "1521 autotest"

# 拉取服务器生成的文件
cselab run "make"
cselab pull

# 交互式调试
cselab ssh

# 无需文件同步的命令
cselab run --no-sync "1521 classrun -sturec"
```

## 配置

配置文件：`~/.config/cselab/config.toml`

```toml
[server]
host = "cse.unsw.edu.au"
port = 22
user = "z5555555"

[auth]
method = "password"
password = "your_password"

[sync]
exclude = [".git", "__pycache__", "node_modules", ".venv", "target"]
```

## AI 平台集成

cselab 提供多平台 AI skill 文件，让 AI 助手帮你操作 CSE 命令：

| 平台 | 文件 | 安装方式 |
|------|------|----------|
| Claude Code | `skills/cselab.md` | `cp skills/cselab.md ~/.claude/commands/` |
| Codex CLI | `skills/AGENTS.md` | `cp skills/AGENTS.md ./AGENTS.md` |
| Gemini CLI | `skills/GEMINI.md` | `cp skills/GEMINI.md ./GEMINI.md` |
| Claude.ai | `skills/cselab.md` | 上传到 Project Knowledge |
| Cursor | `skills/cselab.md` | `cp skills/cselab.md .cursor/rules/` |
| Windsurf | `skills/cselab.md` | `cp skills/cselab.md .windsurfrules/` |

详细部署指南：[docs/deployment.md](docs/deployment.md)

## 性能对比

与 [cserun](https://github.com/xxxbrian/cserun) 的对比（50 文件 x 10KB）：

| 指标 | cselab | cserun | 提升 |
|------|--------|--------|------|
| 命令延迟（热连接）| **0.15s** | 0.73s | 4.9x |
| 文件同步 | **0.30s** | 2.13s | 7.1x |
| 端到端 | **0.42s** | 2.14s | 5.0x |
| 可靠性 (20次连续) | **100%** | 45% | — |

## 项目结构

```
cselab/
├── README.md              # English docs
├── README_CN.md           # 中文文档
├── LICENSE                # MIT
├── install.sh             # 一键安装脚本
├── pyproject.toml         # Python 项目配置
├── src/cselab/
│   ├── cli.py             # CLI 命令入口
│   ├── config.py          # 配置管理
│   └── connection.py      # SSH/rsync 传输层
├── skills/
│   ├── cselab.md          # Claude Code skill
│   ├── AGENTS.md          # Codex CLI 指令
│   └── GEMINI.md          # Gemini CLI 上下文
├── docs/
│   └── deployment.md      # 部署指南
└── examples/
    ├── autotest.sh        # 自动测试示例
    ├── submit.sh          # 提交作业示例
    └── watch-test.sh      # 监听模式示例
```

## 致谢

感谢 [@xxxbrian](https://github.com/xxxbrian) 创建 [cserun](https://github.com/xxxbrian/cserun)，证明了本地运行 CSE 命令的可行性和价值。cselab 在此基础上采用了不同的技术方案。

## 许可证

MIT
