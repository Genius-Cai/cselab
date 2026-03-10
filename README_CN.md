<div align="center">

<img src="assets/zap-teal.png" alt="Zap — cselab 吉祥物" width="80" />

# cselab

**在本地运行 UNSW CSE 服务器命令 — 快速、可靠、支持交互**

<p>
  <img src="https://img.shields.io/pypi/v/cselab?style=flat&color=4ecdc4&label=PyPI" alt="PyPI version" />
  <img src="https://img.shields.io/badge/Python-3.10+-4ecdc4?style=flat&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/License-MIT-4ecdc4?style=flat" alt="MIT License" />
  <img src="https://img.shields.io/badge/SSH-ControlMaster-4ecdc4?style=flat" alt="SSH ControlMaster" />
  <img src="https://img.shields.io/badge/Sync-rsync-4ecdc4?style=flat" alt="rsync" />
</p>

[English](README.md) | 简体中文

[为什么选 cselab](#为什么需要-cselab) · [方案对比](#方案对比) · [快速开始](#快速开始) · [给 CSE 教职工](#给-cse-教职工与管理员) · [AI 集成](#ai-平台集成)

<p><img src="assets/demo-repl.gif" alt="cselab REPL — 交互模式演示" width="700" /></p>

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
│                         │   1. SSH     │                      │
│  ~/COMP1521/lab01/      │──────────────│  ControlMaster       │
│    hello.c              │  (仅一次)    │  (持久连接)          │
│    Makefile             │              │                      │
│                         │   2. rsync   │  ~/.cselab/          │
│                         │──────────────│    workspaces/       │
│                         │  (增量传输)  │      lab01-a3f2/     │
│                         │              │        hello.c       │
│                         │   3. ssh     │        Makefile      │
│                         │──────────────│                      │
│                         │  (执行)      │  $ 1521 autotest     │
│                         │              │                      │
│  终端:                  │   4. 输出    │                      │
│  ✅ All tests passed    │◄─────────────│                      │
│                         │  (实时流)    │                      │
└─────────────────────────┘              └──────────────────────┘
```

### 执行流程

运行 `cselab run "1521 autotest"` 时：

1. **连接** — 建立 SSH ControlMaster 连接（后续所有命令复用，密码只需输一次）
2. **同步** — `rsync` 增量上传本地文件到服务器（只传输变更部分）
3. **执行** — 在服务器同步目录中运行命令，支持完整的交互式终端
4. **输出** — 实时回传输出到本地终端，保留退出码

后续运行复用 SSH 连接（0ms 重连），rsync 仅传输变更（典型编辑场景下亚秒级完成）。

## 安装

**要求：** Python 3.10+、`rsync`、`ssh`（macOS 和大多数 Linux 已预装）

**一键安装（推荐）：**

```sh
curl -sSL https://raw.githubusercontent.com/Genius-Cai/cselab/master/install.sh | bash
```

**pip 安装：**

```sh
pip install cselab
```

**克隆安装：**

```sh
git clone https://github.com/Genius-Cai/cselab.git
cd cselab
pip install .
```

## 快速开始

```sh
# 1. 首次配置
cselab init
# 输入 zID 和密码

# 2. 进入作业目录
cd ~/COMP1521/lab01

# 3. 运行 CSE 命令
cselab run "1521 autotest"
```

就这么简单。本地文件自动同步，命令在 CSE 服务器执行。

## 交互模式

直接输入 `cselab`（不带参数）进入 REPL：

```
$ cd ~/COMP1521/lab01
$ cselab

  cselab v0.2.0
  z5555555@cse.unsw.edu.au

  输入任意 CSE 命令，Ctrl+C 退出。

  Connecting... OK

⚡ 1521 autotest collatz
[sync] OK (0.1s)
5 tests passed 0 tests failed

⚡ give cs1521 lab01 collatz.c
[sync] OK (0.1s)
Submission received.

⚡ exit
```

跟 CSE 服务器一样的命令 — 零学习成本。

单次执行模式同样可用（适合脚本和 CI）：

```bash
cselab run "1521 autotest collatz"
```

<p align="center"><img src="assets/demo-hero.gif" alt="cselab 命令行模式 — 运行任意 CSE 命令" width="700" /></p>

## 命令详解

### `cselab run <command>`

同步文件 + 在 CSE 服务器运行命令。

```sh
cselab run "1521 autotest"             # 同步 + autotest
cselab run "2521 autotest"             # 支持任意课程
cselab run "give cs1521 lab01 hello.c" # 提交作业
cselab run --no-sync "1521 classrun -sturec"  # 跳过同步，适合不需要文件的命令
```

输出示例：

```
[1/3] Connecting to cse.unsw.edu.au... OK (0.0s)
[2/3] Syncing files... OK (0.2s)
[3/3] Running: 1521 autotest
========================================
Test 1 - ... passed
Test 2 - ... passed
All tests passed!
========================================
Exit: OK
```

### `cselab pull`

从服务器拉取文件到本地。适合服务器生成输出文件的场景。

```sh
cselab run "make"        # 在服务器编译，生成二进制文件
cselab pull              # 拉取生成的文件
```

### `cselab watch <command>`

监听本地文件变化，自动运行命令。保存文件即触发 autotest。

```sh
cselab watch "1521 autotest"
# 在编辑器中修改 hello.c，保存后 autotest 自动运行
```

### `cselab ssh`

在同步的工作目录中打开交互式 SSH 会话。

```sh
cselab ssh
# 进入 CSE 服务器 shell，目录与本地文件一致
```

### `cselab sync`

仅同步文件，不运行命令。

```sh
cselab sync
```

### 其他命令

```sh
cselab config       # 显示配置文件路径和内容
cselab clean        # 清理所有远程工作目录
cselab disconnect   # 关闭 SSH 连接
cselab --help       # 完整帮助
```

## 配置

配置文件：`~/.config/cselab/config.toml`

```toml
[server]
host = "cse.unsw.edu.au"
port = 22
user = "z5555555"  # 你的 zID

[auth]
method = "password"
password = "your_password"  # 可选，留空则每次提示输入

# 也支持 SSH 密钥认证（无需密码）
# [auth]
# method = "key"
# key_path = "~/.ssh/id_rsa"

[sync]
# 同步时排除的目录（.gitignore 中的规则也会自动生效）
exclude = [".git", "__pycache__", "node_modules", ".venv", "target"]
```

cselab 会读取 `.gitignore` 和 `.ignore` 文件 — `node_modules/`、`__pycache__/` 等目录自动排除，无需手动配置。

## cselab 能帮你什么

### 痛点

CSE 学生每天都在忍受这些摩擦：

- **SSH + 远程编辑** — 失去 VS Code、插件、Copilot、肌肉记忆。在 SSH 里用 `vim` 编辑是一个与课程内容无关的额外门槛。
- **手动复制文件** — 每次 autotest 前都要 `scp`，容易忘记，容易测到旧代码。
- **迭代缓慢** — 编辑 → 复制 → 测试，每轮 30-60 秒。十周下来累计浪费数小时。
- **本地工具无法使用** — 本地调试器、linter、formatter 用不了，代码却必须在 CSE 运行。

### cselab 的解决方案

- **留在你的编辑器里。** 用 VS Code、Cursor 或任何本地编辑器写代码，享受完整的语言支持、插件和 AI 辅助。
- **一条命令测试。** `cselab run "1521 autotest"` 替代整个 SSH-复制-运行循环。
- **亚秒级迭代。** 首次运行后，同步一个文件改动只需约 0.1 秒。编辑、保存、测试 — 几乎即时反馈。
- **监听模式。** `cselab watch "1521 autotest"` 全自动 — 保存文件即看结果。
- **专注学习。** 消除工具摩擦，让学生专注于真正的课程内容：C 语言、数据结构、算法 — 而非 SSH 操作。

## 方案对比

每个 UNSW CSE 学生都需要在 CSE 服务器上运行 `autotest` 和 `give`。以下是各方案的对比：

| | VLAB | SSH FS | Remote-SSH | cserun | **cselab** |
|---|:---:|:---:|:---:|:---:|:---:|
| **使用本地编辑器**（VS Code, Cursor, Vim）| 否 | 部分 | 是 | 是 | **是** |
| **运行 autotest/give** | 是 | 需另开终端 | 是 | 是 | **是** |
| **服务器负载** | 高 | 低 | **极高** | 低 | **接近零** |
| **可靠性** | 闲置 2h 断连 | 良好 | 进程被 reaper 杀掉 | 45%（libssh2 故障）| **100%** |
| **监听模式**（保存即测试）| 否 | 否 | 否 | 否 | **是** |
| **安装难度** | 无（浏览器）| 中（FUSE）| 中（VS Code 扩展）| 高（Rust 工具链）| **简单**（`pip install`）|
| **AI 编辑器支持**（Cursor, Windsurf）| 否 | 否 | 否 | 否 | **是** |
| **离线编辑** | 否 | 否 | 否 | 否 | **是** |
| **从服务器拉取文件** | 不适用 | 自动 | 自动 | 否 | **是** |
| **交互式 SSH** | 是（完整桌面）| 否 | 是 | 否 | **是** |

> **关键区别：** VS Code Remote-SSH 编辑体验最好，但 CSE [明确不建议使用](https://taggi.cse.unsw.edu.au/FAQ/VS_Code_Remote-SSH/)，因为它会在登录节点上启动 Node.js 进程，每个学生占用约 200-500MB 内存。CSE 已部署 reaper 脚本来清理这些进程，学生可能面临账户限制。
>
> cselab 提供同样的本地编辑体验，**服务器端零占用**。

---

## 与 cserun 的对比

本项目受 [@xxxbrian](https://github.com/xxxbrian) 的 [cserun](https://github.com/xxxbrian/cserun) 启发。cserun 率先证明了本地运行 CSE 命令的可行性，为 UNSW 学生解决了实际痛点。

我们选择重新构建而非贡献 cserun，因为改进方向需要根本性的架构变更 — 不同的语言、不同的 SSH 传输、不同的同步机制。

### 架构差异

| | cselab | cserun |
|---|---|---|
| **语言** | Python | Rust |
| **SSH 库** | 原生 OpenSSH（subprocess）| libssh2（C 绑定）|
| **连接方式** | SSH ControlMaster（持久复用）| 每次新建 TCP+SSH |
| **文件同步** | `rsync`（增量压缩）| SFTP（逐文件上传）|
| **交互 I/O** | 完整 PTY（`ssh -tt`）| 非阻塞轮询，无 stdin |
| **依赖** | Python 3.10+（macOS 预装）| Rust 工具链 + C 编译器 |

### 性能测试（50 文件 x 10KB）

| 指标 | cselab | cserun | 提升 |
|------|--------|--------|------|
| 命令延迟（热连接）| **0.15s** | 0.73s | 4.9x |
| 文件同步 | **0.30s** | 2.13s | 7.1x |
| 端到端（同步 + 编译 + 运行）| **0.42s** | 2.14s | 5.0x |
| 冷连接 | **0.48s** | 0.73s | 1.5x |

### 可靠性测试（20 次连续调用）

| | cselab | cserun |
|---|---|---|
| 成功率 | **20/20 (100%)** | 9/20 (45%) |
| 失败原因 | — | `libssh2: Failed getting banner` |

可靠性问题源于 libssh2 的 SSH 握手实现，在快速重连场景下间歇性失败。cselab 通过 ControlMaster 维持持久连接，从根本上避免了这个问题。

### 功能对比

| 功能 | cselab | cserun |
|------|--------|--------|
| 运行命令 | 是 | 是 |
| 文件同步 | 是（rsync）| 是（SFTP）|
| .gitignore 支持 | 是 | 是 |
| 跳过同步（`--no-sync`）| 是 | 是 |
| 环境变量 | 计划中 | 是 |
| **从服务器拉取文件** | **是** | 否 |
| **交互式命令** | **是** | 否 |
| **监听模式** | **是** | 否 |
| **交互式 SSH** | **是** | 否 |
| **连接复用** | **是** | 否 |
| **工作目录清理** | **是** | 否 |

### 致谢

感谢 [@xxxbrian](https://github.com/xxxbrian) 创建 cserun，证明了本地运行 CSE 命令的可行性和价值。cselab 在此基础上采用了不同的技术方案。

## AI 平台集成

cselab 提供多平台 AI skill 文件，让 AI 助手帮你操作 CSE 命令：

| 平台 | 文件 | 安装方式 |
|------|------|----------|
| **Claude Code** | `skills/cselab.md` | `cp skills/cselab.md ~/.claude/commands/` |
| **Codex CLI** | `skills/AGENTS.md` | `cp skills/AGENTS.md ./AGENTS.md` |
| **Gemini CLI** | `skills/GEMINI.md` | `cp skills/GEMINI.md ./GEMINI.md` |
| **Claude.ai** | `skills/cselab.md` | 上传到 Project Knowledge |
| **Cursor** | `skills/cselab.md` | `cp skills/cselab.md .cursor/rules/` |
| **Windsurf** | `skills/cselab.md` | `cp skills/cselab.md .windsurfrules/` |

详细部署指南：[docs/deployment.md](docs/deployment.md)

## 给 CSE 教职工与管理员

如果你负责 CSE 基础设施或课程管理，以下是 cselab 对服务器环境的好处。

### 问题：Remote-SSH 正在拖垮登录服务器

越来越多学生使用 VS Code Remote-SSH 享受本地编辑体验。但每个 Remote-SSH 会话都会在登录节点上驻留一个 Node.js 服务器，导致：

- **每个学生占用 200-500MB 内存**（VS Code Server + 文件监视器 + 语言索引）
- 持久连接持续整个编程会话（数小时）
- CSE 不得不部署 **reaper 脚本**、专设 **vscode.cse/vscode2.cse** 服务器、实施 **SSH 速率限制**（20 次/分钟触发防火墙封禁）

学生使用 Remote-SSH 是因为其他方案（VLAB、SSH FS）无法提供满意的本地编辑体验。他们需要更好的选择。

### cselab 的不同之处

```
服务器资源对比（100 名学生同时在线）：

VS Code Remote-SSH:  Node.js 常驻进程 + 文件监视器 + 索引
                     约 200-500MB/学生 → 总计 20-50GB，持久占用

SSH FS (SSHFS):      SFTP 连接保持打开
                     约 50MB/学生 → 总计约 5GB，持久占用

cselab:              rsync (0.3s) + SSH exec (<10s) + 断开
                     空闲时约 0MB → 总计接近 0GB，仅脉冲式占用
```

cselab 使用 **rsync** 同步文件（0.3 秒增量传输）和 **短命 SSH** 执行命令。没有后台进程，没有持久连接，没有 Node.js。命令完成后，服务器资源完全释放。

### 对 CSE 的好处

1. **空闲零负载** — 无 Node.js，无持久连接
2. **更少 SSH 连接** — SSH ControlMaster 通过单个 socket 复用，不会触发速率限制
3. **开源（MIT）** — 完全可审计，无服务器端组件
4. **减少工单** — 学生不再因 SSH 断连和 VLAB 延迟提交支持请求
5. **兼容所有课程** — autotest、give、classrun 均可正常使用

### 建议

如需评估 cselab，源码在 [github.com/Genius-Cai/cselab](https://github.com/Genius-Cai/cselab)。它只需要学生机器上的标准 `ssh` 和 `rsync`，不会修改服务器环境。

我们欢迎将 cselab 纳入 [CSE Home Computing Guide](https://taggi.cse.unsw.edu.au/FAQ/Home_computing/) 的评估。

---

## 项目结构

```
cselab/
├── src/cselab/
│   ├── cli.py             # CLI 入口（9 个子命令）
│   ├── config.py          # 配置管理
│   ├── connection.py      # SSH/rsync 传输层
│   ├── repl.py            # 交互式 REPL 模式
│   ├── banner.py          # 欢迎横幅与吉祥物
│   ├── mascot.py          # Zap 吉祥物渲染（支持节日主题）
│   └── theme.py           # ANSI 颜色常量
├── skills/
│   ├── cselab.md          # Claude Code skill
│   ├── AGENTS.md          # Codex CLI 指令
│   └── GEMINI.md          # Gemini CLI 上下文
├── docs/
│   └── deployment.md      # 多平台部署指南
├── examples/
│   ├── autotest.sh        # 自动测试示例
│   ├── submit.sh          # 提交作业示例
│   └── watch-test.sh      # 监听模式示例
├── install.sh             # 一键安装脚本
├── README.md              # English docs
├── README_CN.md           # 中文文档
└── LICENSE                # MIT
```

## 作者

**Steven Cai** ([@Genius-Cai](https://github.com/Genius-Cai))

UNSW Sydney — Bachelor of Commerce / Computer Science

## 许可证

[MIT](LICENSE)
