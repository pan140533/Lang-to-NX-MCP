v0.1 — 测试版0.1

# Lang-to-NX

自然语言驱动 **Siemens NX 2412** CAD 建模。输入文字描述，AI 自动分析并生成 3D 模型。

```
用户输入 → 意图识别 → 结构分解 → 任务规划 → C# Journal → run_journal.exe → NX 2412
                                          ↓
                                    Three.js 实时预览
```

---

## 已实现工具 (21个)

| 分类 | 工具 | 状态 |
|------|------|------|
| **文档** | new_document, save_model | ✅ |
| **草图** | create_sketch, close_sketch, create_sketch_on_face | ✅ |
| **绘图** | draw_circle, draw_line, draw_rectangle, draw_arc, draw_polyline, draw_spline | ✅ |
| **体素** | block, cylinder, cone, sphere, torus | ✅ |
| **布尔** | boolean_unite, boolean_subtract, boolean_intersect | ✅ |
| **细节** | chamfer, fillet, edge_blend, shell, hole, pocket, boss, pad, slot | ✅ |
| **阵列** | pattern_linear, pattern_circular | ✅ |
| **镜像** | mirror_feature | ✅ |
| **变换** | translate, rotate | ✅ |
| **旋转** | revolve | ✅ |

## 待实现工具 (15个)

| 分类 | 工具 | 说明 |
|------|------|------|
| 扫掠 | sweep | 需 FreeformSurfaceCollection API |
| 曲面 | through_curves ~ face_blend (9个) | NX曲面API复杂 |
| 同步建模 | move_face, delete_face, replace_face, resize_face | 同上 |
| 其他 | thread, scale, measure_distance, measure_volume, measure_mass | 低优先级 |

---

## 快速开始

### 1. 配置

```bash
cp .env.example .env
# 编辑 .env 填入你的 DeepSeek API Key
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 3. 启动

```bash
# 后端 (端口 8000)
python run.py

# 前端 (另一个终端)
cd frontend && npm run dev
```

浏览器打开 `http://localhost:3000`

---

## 软件要求

- **Siemens NX 2412** — 建模引擎（`run_journal.exe`）
- **Python 3.10+** — 后端 + Agent 管线
- **Node.js 18+** — 前端 Three.js 预览
- **DeepSeek API Key** — 自然语言解析

---

## 项目结构

```
Lang-to-NX/
├── backend/
│   ├── api.py              # FastAPI 入口
│   ├── config.py            # 配置
│   ├── llm_parser.py        # LLM 解析
│   ├── session_manager.py   # 会话管理
│   ├── geometry_utils.py    # 几何计算
│   ├── log_system.py        # 日志系统
│   ├── agent/               # AI 智能体管线
│   │   ├── intent.py        # 意图识别
│   │   ├── decomposer.py    # 结构分解
│   │   ├── memory.py        # 上下文记忆
│   │   ├── planner.py       # 任务规划
│   │   └── executor.py      # 执行调度
│   └── journal/
│       ├── nx_modeler.cs    # ⭐ NX 2412 C# API 封装 (21个已实现)
│       ├── generator.py     # ⭐ JSON → C# 翻译器
│       └── tools.json       # 工具定义清单
├── frontend/                # Next.js + Three.js 3D 预览
├── output/                  # 生成脚本和模型
├── CHANGELOG.md             # 版本更新日志
└── ARCHITECTURE.md          # 架构文档
```

---

## 提交规范

参考 `CHANGELOG.md`

| 类型 | 格式 | 示例 |
|------|------|------|
| 版本发布 | `vX.Y: 说明` | `v0.1: 测试版0.1` |
| Bug修复 | `修复: 说明` | `修复: sphere参数错误` |
| 小修改 | `修改: 说明` | `修改: 更新README` |
| 优化 | `优化: 说明` | `优化: 重构api接口` |

---

## 🙏 致谢

基于 [Text-to-CAD](https://github.com/congelation/Text-to-CAD) 架构改造。

**主要改动：**
- NX 执行层从 NX 2312 Python → NX 2412 C# + run_journal.exe
- 新增 Agent 管线（意图识别/分解/规划/执行）
- 所有 NX API 调用通过 nx_modeler.cs 固定封装，不猜测 API
