# Lang-to-NX-MCP 项目架构

> NX 2412 智能建模助手 — 自然语言转 CAD 模型

---

## 一、整体架构（4层）

```
┌─────────────────────────────────────────────────────────────────────┐
│  第1层：前端层 (Frontend)                                            │
│  ─────────────────────────────                                      │
│  文件：frontend/app/page.tsx, components/                           │
│  功能：用户输入界面 / 3D预览 / 结果展示                               │
│  输入：用户文本 "创建一个三叶风扇"                                   │
│  输出：HTTP请求 → 后端API                                            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  第2层：后端层 (Backend API)                                         │
│  ─────────────────────────────                                      │
│  文件：backend/api.py                                                │
│  功能：接收请求 → 调用Agent Pipeline → 返回结果                       │
│  输入：HTTP POST 请求                                                │
│  输出：JSON 响应（状态 + 人类思维 + 步骤 + 模型文件）                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  第3层：Agent Pipeline (智能建模引擎)                                 │
│  ─────────────────────────────                                      │
│  文件：backend/agent/ + llm_parser.py + journal/generator.py        │
│                                                                     │
│  LLM 和 Generator 不是独立层，而是 Agent 在不同阶段调用的工具：        │
│  - LLM 是"理解阶段"的眼睛，帮 Agent 看懂用户想要什么                  │
│  - Generator 是"执行阶段"的手，把规划好的步骤翻译成 C# 代码           │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 阶段1: 理解 (Understand)                                     │   │
│  │                                                              │   │
│  │  intent.py     → 意图识别: CREATE / MODIFY / QUERY           │   │
│  │                     提取关键实体: "风扇", "3叶"               │   │
│  │                                                              │   │
│  │  llm_parser.py → LLM 辅助理解:                               │   │
│  │     - 模糊描述 → 自动补全默认尺寸和形状                       │   │
│  │     - 明确数值 → 严格使用指定参数                             │   │
│  │     - 生成结构描述: "中间圆柱 + 3片叶子围一圈"                │   │
│  │                                                              │   │
│  │  像人一样: "先看看这个要求长什么样，心里有个画面"              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↓                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 阶段2: 规划 (Plan)                                           │   │
│  │                                                              │   │
│  │  decomposer.py → 结构分解:                                    │   │
│  │     - 检测重复/对称/阵列模式                                  │   │
│  │     - 7种策略: 圆形阵列/线性阵列/镜像/旋转体/基体+细节/堆叠   │   │
│  │     - "3片叶子 → 画1片 + 阵列3份，不傻画3次"                  │   │
│  │                                                              │   │
│  │  planner.py    → 步骤规划:                                    │   │
│  │     - 决定先后顺序: 先中心圆柱 → 再1片叶子 → 阵列 → 打孔     │   │
│  │     - 选择具体工具: cylinder, extrude, pattern_circular       │   │
│  │     - 确定位置尺寸: 圆心在原点, 叶子从边缘出发                │   │
│  │                                                              │   │
│  │  memory.py     → 上下文记忆:                                  │   │
│  │     - 当前模型状态: 空白 → 有圆柱 → 有叶片...                 │   │
│  │     - 下一步建议: "你已经建了圆柱，接下来可以加叶片了"        │   │
│  │                                                              │   │
│  │  像人一样: "知道长什么样了，开始想怎么做、用什么工具、         │   │
│  │             先做哪个后做哪个、放在什么位置"                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↓                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 阶段3: 执行 (Execute)                                        │   │
│  │                                                              │   │
│  │  generator.py  → 代码生成: JSON步骤 → C# 脚本                │   │
│  │     - 56个 _gen_xxx 方法，每个对应一个建模工具                │   │
│  │     - 嵌入 nx_modeler.cs 的实现代码                           │   │
│  │     - 保存为 UTF-8 BOM 编码（NX 编译器要求）                  │   │
│  │                                                              │   │
│  │  executor.py   → 执行调度:                                    │   │
│  │     - 调用 run_journal.exe 执行 C# 脚本                       │   │
│  │     - 超时/错误处理                                           │   │
│  │                                                              │   │
│  │  像人一样: "规划好了，动手做，把想法变成代码跑起来"            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                          ↓                                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ 阶段4: 反馈 (Feedback)                                       │   │
│  │                                                              │   │
│  │     - 成功 → 更新 memory 状态, 展示模型结果                   │   │
│  │     - 失败 → 分析原因, 尝试修正后重试, 或报错给用户           │   │
│  │                                                              │   │
│  │  像人一样: "做完了，看看结果对不对，不对就改"                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│  第4层：NX执行层 (Siemens NX 2412)                                   │
│  ─────────────────────────────                                      │
│  文件：backend/journal/nx_modeler.cs, run_journal.exe               │
│  功能：C#脚本编译执行 → NXOpen API 调用 → 生成 .prt 模型文件          │
│                                                                     │
│  nx_modeler.cs：56个方法（17个已验证 + 12个组合实现 + 27个TODO）      │
│  run_journal.exe：NX官方C#脚本执行器（C# 5.0编译器，不支持 $"..."）   │
│                                                                     │
│  输入：C#脚本文件 (UTF-8 BOM)                                        │
│  输出：.prt 3D模型文件                                               │
└─────────────────────────────────────────────────────────────────────┘
```

**核心数据流：**
```
用户输入 → [理解] → [规划] → [执行] → [反馈] → NX模型
         LLM辅助   规则引擎   代码生成   状态更新
```

**为什么不是 7 层而是 4 层？**
- 旧架构把 Agent、LLM、Generator 拆成独立层，但它们是同一套流程的组成部分
- 就像人的大脑：理解、规划、执行是同一个大脑在做的事，不是一个器官看、一个器官想、一个器官做
- LLM 不是独立层，它是 Agent 在"理解"阶段用的眼睛
- Generator 不是独立层，它是 Agent 在"执行"阶段用的手
- 所以正确的架构是：**4 层，其中 Agent Pipeline 内部有 4 个阶段**

---

## 二、目录结构

```
Lang-to-NX-MCP/
│
├── backend/                    # 后端核心
│   ├── agent/                  # 智能体模块（已实现）
│   │   ├── __init__.py         # 包入口
│   │   ├── intent.py           # 意图识别：6种意图类型 + 关键词匹配
│   │   ├── decomposer.py       # 结构分解：7种策略（阵列/镜像/旋转体/基体+细节/堆叠/单体）
│   │   ├── memory.py           # 上下文记忆：模型状态 + 操作历史 + 关注焦点 + 下一步建议
│   │   ├── planner.py          # 任务规划：先分解结构，再生成最优建模步骤
│   │   └── executor.py         # 执行调度：AgentPipeline 串联全流程 + 错误处理
│   │
│   ├── journal/                # C# 工具层
│   │   ├── tools.json          # 工具定义（56个工具）
│   │   ├── generator.py        # JSON → C# 代码生成（56个 _gen_xxx 方法）
│   │   └── nx_modeler.cs       # NXOpen API 封装（56个方法）
│   │
│   ├── api.py                  # FastAPI 后端接口
│   ├── llm_parser.py           # LLM 解析模块（56个工具描述）
│   ├── config.py               # 配置管理
│   ├── session_manager.py      # 会话管理
│   ├── geometry_utils.py       # 几何计算工具
│   └── log_system.py           # 日志系统
│
├── frontend/                   # 前端界面 (Next.js)
│   ├── app/
│   │   ├── page.tsx            # 主页面
│   │   ├── layout.tsx          # 布局
│   │   ├── components/         # UI组件
│   │   │   ├── ThreeViewer.tsx # 3D预览
│   │   │   └── ViewControls.tsx# 视图控制
│   │   └── globals.css         # 样式
│   ├── lib/
│   │   └── csgOperations.ts    # CSG操作
│   └── package.json            # 依赖配置
│
├── tests/                      # 测试文件
│   ├── test_api.py             # API测试
│   ├── test_llm_parser.py      # LLM解析测试
│   └── test_benchmark_*.py     # 性能基准测试
│
├── run.py                      # 一键启动脚本
├── requirements.txt            # Python依赖
├── .env.example                # 环境变量示例
└── README.md                   # 项目说明
```

---

## 三、核心文件说明

### 3.1 tools.json — 工具定义

**作用：** 定义所有可用建模工具的名称、参数、描述

**结构：**
```json
{
  "name": "cylinder",
  "description": "创建圆柱体",
  "category": "primitive",
  "params": {
    "x": {"type": "number"}, "y": {"type": "number"},
    "z": {"type": "number"}, "radius": {"type": "number"},
    "height": {"type": "number"}
  }
}
```

**当前工具数量：** 56个

**工具分类：**
| 分类 | 工具 |
|------|------|
| 文档操作 | `new_document`, `save_model` |
| 草图操作 | `create_sketch_on_plane`, `create_sketch_on_face`, `close_sketch` |
| 绘图工具 | `draw_closed_circle`, `draw_arc`, `draw_rectangle`, `draw_line`, `draw_polyline`, `draw_spline` |
| 基本体素 | `block`, `cylinder`, `cone`, `sphere`, `torus` |
| 拉伸 | `extrude`, `extrude_from`, `extrude_cut` |
| 旋转 | `revolve` |
| 扫描/放样 | `sweep`, `loft` |
| 布尔操作 | `boolean_unite`, `boolean_subtract`, `boolean_intersect` |
| 边缘处理 | `chamfer`, `fillet`, `edge_blend` |
| 细节特征 | `shell`, `hole`, `pocket`, `boss`, `pad`, `slot`, `groove`, `thread` |
| 阵列镜像 | `pattern_linear`, `pattern_circular`, `mirror_feature` |
| 曲面建模 | `through_curves`, `through_curve_mesh`, `ruled`, `bounded_plane`, `fill_surface`, `offset_surface`, `extension`, `trim_surface`, `face_blend` |
| 同步建模 | `move_face`, `delete_face`, `replace_face`, `resize_face` |
| 变换操作 | `translate`, `rotate`, `scale` |
| 测量查询 | `measure_distance`, `measure_volume`, `measure_mass` |

---

### 3.2 generator.py — 代码生成

**作用：** 将 JSON 工具调用转换为 C# 代码

**示例：**
```python
# 输入 JSON
{"tool": "extrude", "params": {"length": 50}}

# 输出 C#
m.Tool_Extrude(50.0);
```

---

### 3.3 nx_modeler.cs — NX API 封装

**作用：** 封装 NXOpen API，提供稳定的建模接口

**核心类：** `NXModeler`，56个方法

| 状态 | 数量 | 说明 |
|------|------|------|
| 已验证 | 17个 | 已在NX中跑通（NewDocument/CreateSketch/DrawCircle/DrawLine/DrawRectangle/CloseSketch/Extrude/ExtrudeFrom/ExtrudeCut/Revolve/Chamfer/Fillet/Cone/Sphere/SaveModel/Init/CalcSeed） |
| 组合实现 | 12个 | 由已验证方法组合（Block/Cylinder/Torus/DrawArc/DrawPolyline/DrawSpline/Hole/Pocket/Boss/Pad/Slot/Groove） |
| TODO标记 | 27个 | 预留接口，需要NXOpen API（Sweep/Loft/Boolean/Pattern/Shell/Thread/Surface/SyncModel/Transform/Measure） |

---

### 3.4 llm_parser.py — LLM 解析

**作用：** 将自然语言转换为结构化建模步骤，作为 Agent 的补充

**TOOL_DESCRIPTIONS：** 56个工具的描述，供 LLM 参考

---

### 3.5 api.py — 后端接口

**主要接口：**
- `POST /api/command` — 执行建模指令
- `POST /api/session/new` — 创建新会话

---

## 四、Agent 智能体模块（已实现）

### 4.1 模块结构

```
backend/agent/
├── __init__.py         # 包入口，导出所有类
├── intent.py           # 意图识别（6种意图类型）
├── decomposer.py       # 结构分解（7种策略）
├── memory.py           # 上下文记忆
├── planner.py          # 任务规划（先分解，再生成步骤）
└── executor.py         # 执行调度（AgentPipeline）
```

### 4.2 数据流

```
用户输入："三叶风扇"
    ↓
┌─────────────────────────────────────────────────┐
│  intent.py: 意图识别                              │
│  意图=CREATE, 实体=[风扇, 3叶], 策略=extrude      │
│  → "用户想创建一个带有3个叶片的风扇"               │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  decomposer.py: 结构分解（像人一样思考）           │
│  检测到 "3叶" → 圆形阵列策略                      │
│  人类思维：                                      │
│   "这个模型有 3 个相同的 blade 围绕中心均匀分布。   │
│    我不会傻到分别画 3 个 blade。                   │
│    正确做法：先画中心 hub → 再画1个 blade →        │
│    用圆形阵列把 blade 绕中心复制 3 份。             │
│    这样只需建 2 个部件，而不是 4 个。"              │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  memory.py: 上下文记忆                            │
│  当前模型：空白，phase=EMPTY                       │
│  建议：创建第一个特征                              │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  planner.py: 任务规划                             │
│  步骤1: new_document                              │
│  步骤2: 创建中心圆柱 (hub)                         │
│  步骤3: 创建一片叶子 (blade)                       │
│  步骤4: pattern_circular(count=3) ← 关键！        │
│  步骤5: save_model                                │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  executor.py: 执行调度                            │
│  调用 generator → 生成 C# → 跑 NX                 │
│  记录结果 → 更新 memory                           │
└─────────────────────────────────────────────────┘
    ↓
NX 建模结果
```

### 4.3 意图类型（intent.py）

| 意图 | 触发关键词 | 示例 |
|------|-----------|------|
| CREATE | 创建/画/做/建/给我 | "画一个圆柱" |
| MODIFY | 修改/打孔/开槽/倒角 | "在这个圆柱上打孔" |
| QUERY | 多少/多大/多重/体积 | "体积是多少" |
| DELETE | 删除/去掉/移除 | "删掉那个孔" |
| ANALYZE | 分析/仿真/受力/强度 | "这个零件能承受多大压力" |
| CHAT | 帮助/你能做什么/你好 | "你能做什么" |

### 4.4 分解策略（decomposer.py）

核心原则：**遇到可以镜像、旋转、阵列完成的重复性任务，绝不要一个一个去画。**

| 策略 | 触发条件 | 模型示例 |
|------|---------|---------|
| 圆形阵列 | `3叶` `4个孔` `6螺栓` `8齿` | 三叶风扇 → 1片叶 + 圆形阵列3份 |
| 线性阵列 | `5级阶梯` `一排栅栏` `散热片` | 阶梯 → 1级 + 线性阵列5份 |
| 镜像 | `左右对称` `翅膀` `两侧支架` | 机翼 → 一侧 + 镜像到另一侧 |
| 旋转体 | `花瓶` `碗` `轮子` `轴` `杯子` | 花瓶 → 截面轮廓 + revolve 360° |
| 基体+细节 | `上面打孔` `开槽` `倒角` | 方块 → 先建主体 → 再打孔 |
| 多层堆叠 | `底座上` `上面` | 底座+圆柱 → 从下往上建 |
| 简单单体 | 回退策略 | 圆柱/方块 → 直接建 |

### 4.5 关键技术点

- **先分解再规划**：不管用户输入多复杂，先分析结构，再生成步骤
- **人类思维输出**：每个规划都带 `human_thought` 字段，让 AI 透明地展示思考过程
- **规则优先 + LLM 回退**：规则能匹配的先用规则，匹配不了的交给 LLM 自由解析
- **上下文记忆**：记住当前模型状态、最近操作、关注焦点，支持多轮对话
- **下一步建议**：根据当前模型阶段，自动生成下一步操作建议

---

## 五、技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js + TypeScript + Three.js |
| 后端 | Python + FastAPI |
| Agent | Python 规则引擎 + 模式匹配 |
| LLM | DeepSeek（作为 Agent 的补充） |
| CAD | Siemens NX 2412 + NXOpen C# API |
| 执行 | run_journal.exe |

---

## 六、环境配置

### 必需环境

1. **NX 2412** — Siemens NX 软件
2. **Python 3.10+** — 后端运行环境
3. **Node.js 18+** — 前端运行环境
4. **DeepSeek API Key** — LLM 服务

`.env` 示例：
```
DEEPSEEK_API_KEY=your_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
NX_PATH=C:\Program Files\Siemens\NX 2412
RUN_JOURNAL_PATH=C:\Program Files\Siemens\NX 2412\NXBIN\run_journal.exe
```

---

## 七、开发计划

### Phase 1: 基础功能（已完成）
- 56个工具注册
- JSON → C# 代码生成
- LLM 解析模块
- 前端界面

### Phase 2: Agent 智能体（已完成）
- 意图识别模块（6种意图类型）
- 结构分解模块（7种策略，像人一样思考）
- 上下文记忆模块（状态跟踪 + 操作历史 + 下一步建议）
- 任务规划模块（先分解再规划，规则优先 + LLM回退）
- 执行调度模块（AgentPipeline 全流程串联）

### Phase 3: 增强能力（规划中）
- 图片理解（上传零件图分析）
- 更多 NXOpen API 实现（27个 TODO 方法）
- 错误自动修正
- 多轮对话增强

---

## 八、快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt
cd frontend && npm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 3. 启动
python run.py
```

---

## 九、常见问题

### Q1: 如何添加新工具？
需要更新4个文件：
1. `tools.json` — 定义工具参数 schema
2. `generator.py` — 添加 `_gen_xxx` 方法（JSON → C#）
3. `nx_modeler.cs` — 添加 `Tool_xxx` 方法（NXOpen API 调用）
4. `llm_parser.py` — 更新 `TOOL_DESCRIPTIONS`（让LLM知道新工具）

### Q2: 为什么用 C# 而不是 Python 直接调用 NXOpen？
- C# Journal 模式更稳定
- run_journal.exe 是 NX 官方执行方式
- 避免 Python NXOpen 的版本兼容问题

### Q3: Agent 和 LLM 的关系是什么？
- **Agent（规则引擎）**：处理结构化场景（阵列/镜像/旋转体/基体+细节），速度快、可预测
- **LLM**：处理复杂/模糊描述，作为 Agent 的补充和回退方案
- **协作模式**：Agent 先尝试匹配规则 → 匹配失败则交给 LLM 自由解析

---

## 十、项目定位（核心认知）

**本项目本质是「智能化 NX 二次开发」，而非 AI 原生建模。**

### 根本约束

NX 是闭源软件，AI 无法直接操作内部 3D 几何数据。唯一入口是 NXOpen C# API（即二次开发接口），而 NXOpen API 本身就是人类 CAD 操作的编程化封装——草图、拉伸、旋转、阵列。

```
AI 想建模 → 无法直接操作 3D 几何数据（点云/体素/网格/隐式曲面）
          → 只能调用 NXOpen API
          → 等于让 AI 扮演一个"会写 NX 二次开发脚本的人"
```

### 这意味着什么

- AI 原生建模的理想（空间占据思维、约束求解、多路径并行探索、自我质疑闭环）在当前架构下无法实现，因为输出格式被 NXOpen 锁死在"特征操作序列"。
- Agent 的智能体现在**把二次开发脚本写得更合理**——识别阵列、避免重复、结构先行——但改变不了输出格式。
- 如果要走向真正的 AI 原生建模，需要绕过 NXOpen，直接接触几何数据。这需要 NX 开放内部数据接口，或换用开源几何内核。

### 当前定位

做的是：**让 AI 作为一个聪明的 NX 二次开发者，理解自然语言需求，生成最优的建模脚本。**

---

## 十一、参考资料

- [NX2412_API_Reference.md](./NX2412_API_Reference.md) — NX API 参考
- [NX2412_CSharp_API_基准.md](./NX2412_CSharp_API_基准.md) — C# API 基准测试
- [README.md](./README.md) — 项目说明

---

*最后更新: 2026-06-20*