# Lang-to-NX-MCP

> **A Model Context Protocol (MCP) server that lets Claude/AI drive Siemens NX part modelling from plain language.**

<p>
  <img src="https://img.shields.io/badge/status-active-success" alt="Status">
  <img src="https://img.shields.io/badge/NX-2412-blue" alt="NX">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/C%23-5.0-purple" alt="C#">
  <img src="https://img.shields.io/badge/MCP-1.0-orange" alt="MCP">
</p>

<p align="center"><strong>自然语言驱动 Siemens NX 自动建模</strong></p>
<p align="center">
  <i>"给我一个 17 齿的齿轮"  →  AI 自动规划  →  NX 生成 .prt 文件</i>
</p>

---

## 这是什么？

**Lang-to-NX-MCP** 是一个 MCP（Model Context Protocol）服务器，让 Claude 等 AI Agent 能直接操控 Siemens NX 进行 3D 建模。你用自然语言描述想要的零件，AI 自动理解、规划步骤、生成 C# 脚本、驱动 NX 执行，最终输出 `.prt` 模型文件。

```
你说："做个三叶风扇，中心带孔"
     │
     ▼
AI 理解意图 → 识别圆形阵列模式 → 规划步骤 → 生成 C# → NX 执行 → 风扇.prt
```

> [!IMPORTANT]
> **运行前必须手动配置，程序不会自动去找 NX。**
> 本项目依赖本机已安装的 **Siemens NX 2412**。NX 装在哪只有你知道——请把 `.env.example` 复制为 `.env`，**手动填写 `NX_ROOT`** 指向你自己的 NX 安装目录。
> 没填或填错，程序启动后每条建模指令都会失败（报 `WinError 2 系统找不到指定的文件`）。详见下方「配置（必须手动完成）」。

---

## 解决什么问题？

Siemens NX 是工业级闭源 CAD 软件，广泛用于航空航天、汽车制造。AI 无法直接操作其内部 3D 几何数据。**唯一入口是 NXOpen API**——NX 官方提供的二次开发接口，本质就是人类 CAD 操作（草图、拉伸、旋转、阵列）的编程封装。

> 核心思路：**让 AI 扮演一个"会写 NX 二次开发脚本的工程师"。**

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│  第1层 · AI Agent                                        │
│  Claude / Cursor / 任何支持 MCP 的 AI                    │
│  理解意图、规划建模步骤、调用 MCP 工具                     │
├─────────────────────────────────────────────────────────┤
│  第2层 · MCP 协议层 (Python)                             │
│  工具注册 · 参数校验 · 错误处理                            │
│  53 种建模操作封装为标准化工具                             │
├─────────────────────────────────────────────────────────┤
│  第3层 · C# Journal 生成                                 │
│  generator.py   JSON 步骤 → C# 代码                      │
│  nx_modeler.cs  NXOpen API 封装（58 个方法）              │
├─────────────────────────────────────────────────────────┤
│  第4层 · NX 执行层                                       │
│  run_journal.exe 编译执行 C# 脚本                        │
│  NX 用完即退出，不占用 License                            │
└─────────────────────────────────────────────────────────┘
```

### 为什么用外部进程而不是 Python NXOpen API？

| | Python NXOpen API | **本项目** |
|---|---|---|
| NX 状态 | 必须一直打开 | **用完即退，不占 License** |
| 稳定性 | 进程内逻辑不稳定 | **进程隔离，崩不影响主系统** |
| 批量建模 | 不适合 | **天然适合** |

---

## 能做什么

### 53 种建模操作

| 类别 | 操作 | 数量 |
|------|------|------|
| 📐 草图 | 创建草图、画圆/矩形/线/弧/样条曲线 | 10 |
| 📦 体素 | 方块、圆柱、圆锥、球体、圆环 | 5 |
| 🔧 特征 | 拉伸、旋转、扫掠、放样、抽壳、打孔 | 12 |
| 🧩 布尔 | 求和、求差、求交 | 3 |
| ✨ 细节 | 倒角、圆角、边倒圆 | 3 |
| 🔄 阵列 | 圆形阵列、线性阵列、镜像 | 3 |
| 🏗️ 曲面 | 直纹面、通过曲线组、填充面、修剪面 | 8 |
| 🔀 变换 | 移动、旋转、缩放 | 3 |
| 📏 测量 | 距离、体积、质量 | 3 |
| 📄 文档 | 新建、保存 | 2 |

### 标准件自动识别

系统能通过模式匹配识别以下结构：

- **齿轮**：识别齿数/模数 → 毛坯 + 齿廓 + 圆形阵列
- **法兰**：识别孔数 → 底板 + 孔 + 圆形阵列
- **旋转体**：花瓶/杯子/轴 → 截面轮廓 + Revolve
- **阶梯轴**：多段直径 → 逐段堆叠
- **阵列件**："N个X绕一圈" → 单体 + 圆形阵列

---

## 快速开始

### 前置条件

- **Siemens NX 2412**（含 NXOpen，且本机有可用 License）—— 必须已安装，本项目不携带 NX
- Python 3.10+
- Node.js 18+（前端）

### 安装

```bash
git clone https://github.com/pan140533/Lang-to-NX-MCP.git
cd Lang-to-NX-MCP
pip install -r requirements.txt
cp .env.example .env
```

### 配置（必须手动完成）

`.env` 不会随仓库上传（已在 `.gitignore` 中忽略），必须由你自己创建并填写。

1. 把 `.env.example` 复制成 `.env`
2. 用文本编辑器打开 `.env`，把 `NX_ROOT` 改成**你自己机器上**的 NX 安装目录

| 变量 | 必填 | 说明 |
|---|---|---|
| `NX_ROOT` | ✅ **必填** | NX 安装目录。该目录下必须存在 `NXBIN\run_journal.exe` |
| `LLM_API_KEY` | 可选 | 兼容 OpenAI 协议的 Key；当前版步骤规划由规则引擎完成，留空不影响建模 |
| `OUTPUT_DIR` | 可选 | 输出目录，默认 `output`（.prt 实际落在 `output/models/`） |
| `SESSION_DIR` | 可选 | 会话数据目录，默认 `sessions` |

**怎么找到你的 `NX_ROOT`：**

1. 找到你机器上装 NX 的目录（例如 `C:\Program Files\Siemens\NX 2412` 或 `E:\NX\NX`）
2. 进入它下面的 `NXBIN`，确认里面有 `run_journal.exe`
3. 把 `NXBIN` 的**上一级**目录写进 `NX_ROOT`（注意不要带 `\NXBIN`）

```ini
# .env 示例
NX_ROOT=E:\NX\NX
OUTPUT_DIR=output
SESSION_DIR=sessions
```

> 程序**不会**扫描磁盘自动定位 NX：机器磁盘大时全盘搜索既慢又不可靠，所以这一步必须由你手动完成。
> 路径没配或配错时，接口会直接返回「找不到 run_journal.exe」并提示检查 `NX_ROOT`，而不是只丢一个 `WinError 2`。

### 启动

```bash
python run.py
```

该命令会同时启动：

- 后端 FastAPI → http://localhost:8000
- 前端 Next.js → http://localhost:3000

浏览器打开 http://localhost:3000 使用。

### 接入 Claude Desktop

```json
{
  "mcpServers": {
    "lang-to-nx-mcp": {
      "command": "python",
      "args": ["path/to/Lang-to-NX-MCP/run.py"],
      "env": {
        "NX_ROOT": "C:\\Program Files\\Siemens\\NX"
      }
    }
  }
}
```

---

## 演示

### 基础体素
> "创建一个直径 60mm、高 20mm 的圆柱"
> → `nx_create_cylinder(radius=30, height=20)` → `cylinder.prt`

### 齿轮
> "做一个 17 齿的直齿轮，模数 1.5，厚度 15mm"
> → 圆柱毛坯 → 画齿廓 → 拉伸切除 → 圆形阵列×17 → `gear.prt`

### 三叶风扇
> "做一个三叶风扇，中心带轴孔"
> → 中心轮毂 → 1片叶片 → 圆形阵列×3 → 中心孔切除 → `fan.prt`

---

## 项目结构

```
Lang-to-NX-MCP/
├── run.py                        # 启动入口
├── CLAUDE.md                     # AI 行为指南（53种工具文档）
├── .mcp.json                     # MCP 配置示例
│
├── backend/
│   ├── config.py                 # 配置管理
│   ├── mcp/                      # MCP 协议层
│   │   ├── server.py             #   MCP Server
│   │   ├── registry.py           #   工具注册
│   │   ├── executor.py           #   执行引擎
│   │   └── tools/
│   │       ├── execute.py        #     nx_execute_plan（核心）
│   │       └── primitives.py     #     体素快捷工具
│   └── journal/                  # C# 代码生成
│       ├── generator.py          #   JSON → C#（53个方法）
│       └── nx_modeler.cs         #   NXOpen API（58个方法）
│
└── docs/                         # 项目文档
```

---

## 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| MCP 协议层 | ✅ 完成 | 工具注册、自动发现、参数校验 |
| C# NXOpen 封装 | ✅ 完成 | 58 个方法全部实现 |
| Journal 生成器 | ✅ 完成 | 53 个 `_gen_` 方法 |
| P0 Bug 修复 | ✅ 完成 | Revolve / Translate / Rotate |
| 体素工具 | ✅ 完成 | 方块/圆柱/圆锥/球/圆环 |
| NX 实测 | 🚧 ~25/58 | 剩余需 Journal 验证 |
| Agent 管线 | 🔜 下一步 | 规则引擎 + LLM 回退 |
| Web 前端 | 🔜 规划中 | Next.js + Three.js |

---

## 设计原则

1. **外部进程隔离** — NX 用完即退，不占 License，崩不影响主系统
2. **MCP 标准协议** — 任何 MCP 客户端即插即用
3. **分层解耦** — 协议层不涉及 CAD，执行层不涉及 AI
4. **先分解再执行** — 识别阵列/镜像/旋转体，避免重复建模

---

## License

MIT
