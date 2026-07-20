<p align="center">
  <img src="https://img.shields.io/badge/status-active-success" alt="Status">
  <img src="https://img.shields.io/badge/NX-2412-blue" alt="NX">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/C%23-5.0-purple" alt="C#">
  <img src="https://img.shields.io/badge/MCP-1.0-orange" alt="MCP">
</p>

<h1 align="center">Lang-to-NX</h1>
<p align="center"><strong>自然语言驱动 Siemens NX 自动建模</strong></p>
<p align="center">
  <i>"给我一个 17 齿的齿轮"  →  AI 自动规划  →  NX 生成 .prt 文件</i>
</p>

---

## 这是什么？

**Lang-to-NX** 是一个 MCP（Model Context Protocol）服务器，让 Claude 等 AI Agent 能直接操控 Siemens NX 进行 3D 建模。你用自然语言描述想要的零件，AI 自动理解、规划步骤、生成 C# 脚本、驱动 NX 执行，最终输出 `.prt` 模型文件。

```
你说："做个三叶风扇，中心带孔"
     │
     ▼
AI 理解意图 → 识别圆形阵列模式 → 规划步骤 → 生成 C# → NX 执行 → 风扇.prt
```

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

- Siemens NX 2412（含 NXOpen）
- Python 3.10+

### 安装

```bash
git clone https://github.com/pan140533/lang-to-nx.git
cd lang-to-nx
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，设置 NX 安装路径：

```ini
NX_ROOT=C:\Program Files\Siemens\NX
RUN_JOURNAL_EXE=C:\Program Files\Siemens\NX\NXBIN\run_journal.exe
OUTPUT_DIR=./output
```

### 启动

```bash
python run.py                    # MCP Server（AI Agent 连接）
python run.py --list-tools       # 列出所有工具
python run.py --api              # HTTP API 模式
```

### 接入 Claude Desktop

```json
{
  "mcpServers": {
    "lang-to-nx": {
      "command": "python",
      "args": ["path/to/lang-to-nx/run.py"],
      "env": {
        "NX_ROOT": "C:\\Program Files\\Siemens\\NX",
        "RUN_JOURNAL_EXE": "C:\\Program Files\\Siemens\\NX\\NXBIN\\run_journal.exe"
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
lang-to-nx/
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
