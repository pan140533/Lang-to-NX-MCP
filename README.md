<p align="center">
  <img src="https://img.shields.io/badge/status-开发中-yellow" alt="Status">
  <img src="https://img.shields.io/badge/NX-2412-blue" alt="NX Version">
  <img src="https://img.shields.io/badge/python-3.10%2B-green" alt="Python">
  <img src="https://img.shields.io/badge/MCP-1.0-orange" alt="MCP">
</p>

<h1 align="center">Lang-to-NX MCP</h1>
<p align="center"><strong>让 AI 直接操控 Siemens NX 建模的 MCP 服务器</strong></p>
<p align="center">一句话描述自然语言需求 → AI 规划建模步骤 → 自动生成 3D 模型<br><i>自然语言 → 3D 模型，一步到位</i></p>

---

## 📖 项目简介

**Lang-to-NX MCP** 是一个基于 **MCP（Model Context Protocol）** 协议的服务器，它将通用 AI Agent（如 Claude、Cursor 等）与 Siemens NX CAD 系统连接起来。

你只需要用自然语言描述想要的模型，AI 就会：
1. 理解你的意图
2. 规划建模步骤（草图、拉伸、旋转、阵列等）
3. 生成 NX Journal 脚本
4. 调用 NX 自动执行建模
5. 输出 `.prt` 3D 模型文件


---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔌 **MCP 协议标准** | 任何支持 MCP 的 AI Agent（Claude、Cursor 等）即插即用 |
| 🚀 **外部进程执行** | 使用 NX 的 `run_journal.exe` 执行建模，用完即退，不占 License |
| 🏗️ **批量建模** | 一次性生成大量模型，适合自动化流水线 |
| 🔧 **分层架构** | AI 层 → 协议层 → 代码生成层 → NX 执行层，各层解耦 |
| 🌐 **HTTP API 可选** | 提供 FastAPI 接口，方便前端集成 |

---

## 🏗️ 架构总览

```
第1层: AI Agent 层
  Claude / Cursor / 任何 MCP Client
  理解用户意图、规划建模步骤、调用工具
      │ MCP 协议 (stdio)
      ▼
第2层: MCP 协议层（Python）
  工具注册 │ 参数校验 │ 错误格式化
  不涉及 CAD 操作，只做协议转换
      │
      ▼
第3层: C# Journal 生成层
  generator.py 将 JSON 建模步骤转为 C# 代码
  nx_modeler.cs 封装 NXOpen API 调用
      │ subprocess
      ▼
第4层: NX 执行层
  run_journal.exe 编译执行 C# 脚本
  输出 .prt 3D 模型文件，用完即退
```

### 数据流示例

```
用户输入："创建一个直径 60mm、高 20mm 的圆柱"

AI Agent 规划步骤 →
  nx_execute_plan({
    steps: [
      {"tool": "cylinder", "params": {"radius": 30, "height": 20}}
    ]
  })

  → JournalGenerator.generate(steps)
    → 生成 C# 脚本

  → subprocess → run_journal.exe
    → NX 执行建模
    → 输出 .prt 文件
```

---

## 🚀 快速开始

### 前置条件

| 依赖 | 版本要求 |
|------|---------|
| Siemens NX | 2412（含 NXOpen） |
| Python | 3.10+ |
| pip | 最新版 |

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/pan140533/lang-to-nx.git
cd lang-to-nx

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
```

编辑 `.env` 文件，设置你的 NX 安装路径：

```ini
# NX 安装路径
NX_ROOT=D:\Siemens\NX2412
RUN_JOURNAL_EXE=D:\Siemens\NX2412\NXBIN\run_journal.exe

# 输出目录
OUTPUT_DIR=./output
```

### 启动 MCP 服务器

```bash
# 标准 MCP 模式（stdio，供 AI Agent 连接）
python run.py
```

### 其他模式

```bash
# HTTP API 模式（供前端/Webhook 调用）
python run.py --api

# 列出所有注册的工具
python run.py --list-tools
```

---

## 🔧 MCP 工具清单

| 工具 | 描述 |
|------|------|
| `nx_execute_plan` | **核心工具** — 接收一组建模步骤，生成 C# Journal 并执行 |
| `nx_create_block` | 快捷创建方块体素 |
| `nx_create_cylinder` | 快捷创建圆柱体素 |
| `nx_create_cone` | 快捷创建圆锥体素 |
| `nx_create_sphere` | 快捷创建球体体素 |
| `nx_create_torus` | 快捷创建圆环体素 |

### 支持的建模步骤

`nx_execute_plan` 的 `steps` 数组支持以下操作：

| 步骤工具 | 说明 |
|----------|------|
| `new_document` | 创建新文档（毫米） |
| `create_sketch_on_plane` | 在指定平面创建草图 |
| `close_sketch` | 关闭草图 |
| `draw_line` | 画直线 |
| `draw_rectangle` | 画矩形 |
| `draw_circle` | 画圆 |
| `draw_arc` | 画弧 |
| `extrude` | 拉伸 |
| `extrude_cut` | 拉伸切除 |
| `revolve` | 旋转 |
| `pattern_circular` | 圆形阵列 |
| `pattern_rectangular` | 矩形阵列 |
| `boolean_unite` | 布尔求和 |
| `boolean_subtract` | 布尔求差 |
| `edge_blend` | 边倒圆 |
| `chamfer` | 倒角 |
| `helix` | 螺旋线 |
| `sweep` | 扫掠 |
| `cylinder` | 圆柱体（体素） |
| `block` | 方块体（体素） |
| `save_document` | 保存文档 |

---

## 📁 项目结构

```
lang-to-nx/
├── backend/
│   ├── __init__.py
│   ├── config.py              # 配置管理（NX 路径等）
│   ├── journal/
│   │   ├── generator.py       # JSON 步骤 → C# 代码生成器
│   │   └── nx_modeler.cs      # NXOpen C# API 封装
│   └── mcp/
│       ├── server.py          # MCP 服务器主入口
│       ├── registry.py        # 工具注册中心
│       ├── response.py        # 响应格式化
│       ├── executor.py        # 执行器（subprocess 调用 run_journal）
│       └── tools/
│           ├── execute.py     # nx_execute_plan 工具
│           └── primitives.py  # 体素快捷工具
├── docs/                      # 项目文档
│   ├── 01-项目介绍.md
│   ├── 02-现状与问题.md
│   └── 03-技术规范.md
├── output/                    # 输出目录
│   ├── models/                # 生成的 .prt 文件
│   └── scripts/               # 生成的 .cs journal 脚本
├── .env.example               # 环境变量模板
├── .mcp.json                  # MCP 客户端配置示例
├── CLAUDE.md                  # AI Agent 行为指令
├── requirements.txt           # Python 依赖
└── run.py                     # 启动入口
```

---

## 📋 使用示例

### 与 Claude Desktop 集成

在 Claude Desktop 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "lang-to-nx": {
      "command": "python",
      "args": ["D:\\projects\\lang-to-nx\\run.py"],
      "env": {
        "NX_ROOT": "D:\\Siemens\\NX2412",
        "RUN_JOURNAL_EXE": "D:\\Siemens\\NX2412\\NXBIN\\run_journal.exe",
        "OUTPUT_DIR": "D:\\projects\\lang-to-nx\\output"
      }
    }
  }
}
```

### 场景：AI 生成一个齿轮

> **用户输入：** _"创建一个 17 齿的直齿轮，模数 1.5，厚度 15mm"_

AI Agent 会自动规划：
1. 创建圆柱体作为齿轮毛坯
2. 在端面画一个齿廓草图
3. 拉伸切除形成齿槽
4. 圆形阵列 17 个齿槽
5. 保存模型

---

## 📄 文档

- [01. 项目介绍](docs/01-项目介绍.md) — 项目定位、设计原则、与同类项目对比
- [02. 现状与问题](docs/02-现状与问题.md) — 当前阶段、已知问题、下一步计划
- [03. 技术规范](docs/03-技术规范.md) — 技术细节、坐标系统、注意事项

---

## 🗺️ 路线图

- [x] MCP 协议层搭建
- [x] 基础体素工具（方块、圆柱、圆锥、球体、圆环）
- [x] C# Journal 代码生成器
- [ ] 草图+拉伸/旋转流程稳定（调试中）
- [ ] 错误恢复与重试机制
- [ ] 前端 Three.js 3D 预览
- [ ] 批量建模流水线

---

## 📝 License

MIT

---

<p align="center">Made with ❤️ for the NX CAD community</p>
