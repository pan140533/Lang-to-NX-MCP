# Lang-to-NX-MCP

> **A Model Context Protocol (MCP) server that lets Claude/AI drive Siemens NX part modelling from plain language.**

<p>
  <img src="https://img.shields.io/badge/status-active-success" alt="Status">
  <img src="https://img.shields.io/badge/NX-2412-blue" alt="NX">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/C%23-5.0-purple" alt="C#">
  <img src="https://img.shields.io/badge/MCP-stdio-orange" alt="MCP">
</p>

<p align="center"><strong>自然语言驱动 Siemens NX 自动建模</strong></p>
<p align="center">
  <i>"给我一个 17 齿的齿轮"  →  AI 自动规划  →  NX 生成 .prt 文件</i>
</p>

---

> [!IMPORTANT]
> **运行前必须手动配置，程序不会自动去找 NX。**
> 本项目依赖本机已安装的 **Siemens NX 2412**。NX 装在哪只有你知道——请把 `.env.example` 复制为 `.env`，
> **手动填写 `NX_ROOT`** 指向你自己的 NX 安装目录。没填或填错，任何建模调用都会失败。

---

## 这是什么？

**Lang-to-NX-MCP** 是一个 MCP（Model Context Protocol）服务器：Claude Desktop、Cursor 等 AI 客户端通过
**stdio** 连上它，就能用自然语言直接驱动 Siemens NX 建模。

它没有网页、没有 HTTP 接口、没有前端——**唯一的界面就是 MCP 工具**。

```
你说："做个三叶风扇，中心带孔"
     │
     ▼
MCP 客户端 → nx_create → 意图识别 → 结构分解 → 步骤规划
     ▼
生成 C# Journal → run_journal.exe → NX 2412 → output/models/*.prt
```

---

## 解决什么问题？

Siemens NX 是工业级闭源 CAD 软件，AI 无法直接操作其内部几何数据。**唯一入口是 NXOpen API**——
本质就是人类 CAD 操作（草图、拉伸、旋转、阵列）的编程封装。

> 核心思路：**让 AI 扮演一个"会写 NX 二次开发脚本的工程师"，但脚本永远由固定模板生成，不让模型瞎猜 API。**

---

## 能力

- **58 个建模工具**（36 个已实现，22 个占位）：草图、体素、拉伸/旋转、布尔、倒角圆角、阵列镜像、变换等
- **自然语言入口** `nx_create`：一句话 → 规划 → C# → NX
- **精确步骤入口** `nx_execute_plan`：直接传 JSON 步骤，适合可控场景
- **结构分解**：识别"3 片叶子""4 个孔""左右对称""旋转体"，用阵列/镜像/Revolve 完成，而不是逐个画

| 类别 | 代表工具 | 数量 |
|---|---|---|
| 文档 | `new_document` `save_model` | 2 |
| 草图 | `create_sketch_on_plane` `close_sketch` | 3 |
| 绘图 | `draw_closed_circle` `draw_rectangle` `draw_line` `draw_arc` `draw_polyline` | 6 |
| 体素 | `block` `cylinder` `cone` `sphere` `torus` | 5 |
| 特征 | `extrude` `extrude_from` `extrude_cut` `revolve` `hole` `pocket` `boss` `pad` `slot` `shell` | 12 |
| 布尔 | `boolean_unite` `boolean_subtract` `boolean_intersect` | 3 |
| 细节 | `chamfer` `fillet` `edge_blend` | 3 |
| 阵列 | `pattern_circular` `pattern_linear` `mirror_feature` | 3 |
| 变换 | `translate` `rotate` | 2 |
| 曲面 / 同步 / 测量 / 其他 | 多数为占位实现 | 19 |

调用 `nx_list_tools` 可拿到完整清单，`implemented=false` 的不要用。

---

## 架构

```
┌──────────────────────────────────────────────┐
│  MCP 客户端（Claude Desktop / Cursor / ...）   │
└───────────────────────┬──────────────────────┘
                        │ MCP over stdio
┌───────────────────────▼──────────────────────┐
│  backend/mcp/server.py    8 个 MCP 工具        │
│  backend/mcp/service.py   执行链路 + 结果封装   │
└───────────────────────┬──────────────────────┘
                        │
┌───────────────────────▼──────────────────────┐
│  backend/agent/  意图 → 结构分解 → 步骤规划     │
│  backend/journal/generator.py  步骤 → C#      │
└───────────────────────┬──────────────────────┘
                        │ 外部进程
┌───────────────────────▼──────────────────────┐
│  run_journal.exe → NX 2412 → output/models/   │
└──────────────────────────────────────────────┘
```

NX 用完即退，**不长期占用 License**；进程隔离，NX 崩了不影响 MCP 服务器。

---

## 快速开始

### 前置条件

- **Siemens NX 2412**（含 NXOpen，且本机有可用 License）—— 必须已安装，本项目不携带 NX
- Python 3.10+

### 安装

```bash
git clone https://github.com/pan140533/Lang-to-NX-MCP.git
cd Lang-to-NX-MCP
pip install -r requirements.txt
cp .env.example .env
```

### 配置（必须手动完成）

`.env` 不会随仓库上传（已在 `.gitignore` 中忽略），必须由你自己创建并填写。

| 变量 | 必填 | 说明 |
|---|---|---|
| `NX_ROOT` | ✅ **必填** | NX 安装目录，该目录下必须存在 `NXBIN\run_journal.exe` |
| `NX_TIMEOUT_SECONDS` | 可选 | 单次 NX 执行超时，默认 300 |
| `LLM_API_KEY` | 可选 | 兼容 OpenAI 协议的 Key；当前版规划由规则引擎完成，留空不影响建模 |
| `OUTPUT_DIR` | 可选 | 输出目录，默认 `output`（.prt 落在 `output/models/`） |

**怎么找到 `NX_ROOT`：**

1. 找到你机器上装 NX 的目录（例如 `C:\Program Files\Siemens\NX 2412` 或 `E:\NX\NX`）
2. 进入它下面的 `NXBIN`，确认里面有 `run_journal.exe`
3. 把 `NXBIN` 的**上一级**目录写进 `NX_ROOT`（不要带 `\NXBIN`）

```ini
NX_ROOT=E:\NX\NX
```

> 程序**不会**扫描磁盘自动定位 NX：机器磁盘大时全盘搜索既慢又不可靠，所以这一步必须由你手动完成。

### 检查配置

```bash
python run.py --check
```

`ready: true` 表示 NX 路径已就绪；`false` 会给出具体提示。

---

## 接入 MCP 客户端

### Claude Desktop

编辑 `claude_desktop_config.json`（Windows：`%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "lang-to-nx-mcp": {
      "command": "python",
      "args": ["C:\\path\\to\\Lang-to-NX-MCP\\run.py"],
      "env": {
        "NX_ROOT": "C:\\Program Files\\Siemens\\NX 2412"
      }
    }
  }
}
```

### Cursor / Claude Code

仓库根目录已提供 [`.mcp.json`](.mcp.json) 模板，把里面的 `args` 路径和 `NX_ROOT` 换成你机器上的即可。

> 首次调用通常需要 **30~120 秒**：NX 启动占大头。客户端超时请调到 3 分钟以上（`NX_TIMEOUT_SECONDS` 默认 300）。

---

## MCP 工具

| 工具 | 作用 |
|---|---|
| `nx_create` | **推荐入口**：一句自然语言 → 规划 → C# → NX |
| `nx_execute_plan` | 传 `steps` 数组直接执行，跳过规划 |
| `nx_create_block` | 直接建长方体（长宽高 + 起点） |
| `nx_create_cylinder` | 直接建圆柱（半径 + 高） |
| `nx_create_cone` | 直接建圆锥 |
| `nx_create_sphere` | 直接建球体 |
| `nx_list_tools` | 列出 58 个建模工具及其参数、是否已实现 |
| `nx_get_config` | 检查 NX 路径、输出目录、超时配置 |

---

## 项目结构

```
Lang-to-NX-MCP/
├── run.py                        # 入口：stdio MCP 服务器 / --check / --list-tools
├── .mcp.json                     # MCP 客户端配置模板
├── .env.example                  # 配置模板（NX_ROOT 必填）
│
├── backend/
│   ├── mcp/                      # MCP 协议层
│   │   ├── server.py             #   8 个 MCP 工具（FastMCP）
│   │   └── service.py            #   执行链路：C# → run_journal.exe → .prt
│   ├── agent/                    # 规则引擎
│   │   ├── intent.py             #   意图识别
│   │   ├── decomposer.py         #   结构分解（7 种策略）
│   │   ├── planner.py            #   步骤规划
│   │   ├── memory.py             #   上下文记忆
│   │   └── executor.py           #   执行调度 / 流水线
│   ├── journal/
│   │   ├── generator.py          #   JSON 步骤 → C#
│   │   ├── nx_modeler.cs         #   NXOpen 封装（58 个方法，36 实现）
│   │   └── tools.json            #   工具定义（58 个）
│   ├── config.py                 # .env 读取
│   ├── session_manager.py        # 会话持久化
│   ├── name_mapper.py            # ASCII 文件名 ↔ 中文项目名
│   ├── log_system.py             # 日志
│   └── llm_parser.py             # LLM 解析（预留，当前未接入）
│
├── docs/                         # 技术规范 / 多 CAD 规划
└── tests/                        # 测试
```

---

## 当前状态

| 模块 | 状态 |
|---|---|
| MCP 协议层（stdio） | ✅ 完成 |
| 自然语言 → 规划 → C# → NX | ✅ 可用 |
| 建模工具 | 🚧 58 个中 36 个已实现 |
| 曲面 / 同步建模 / 测量 | 🔜 22 个占位实现 |
| LLM 自由解析 | 🔜 代码预留，未接入主流程 |

---

## 设计原则

1. **MCP 单一入口** — 不提供 HTTP / 前端，只做 MCP
2. **固定 API，不让模型猜** — 步骤由规则生成，C# 只调用 `nx_modeler.cs` 里的固定方法
3. **外部进程隔离** — NX 用完即退，不占 License，崩溃不影响服务器
4. **先分解再执行** — 识别阵列/镜像/旋转体，避免重复建模

---

## License

MIT
