# Lang-to-NX

自然语言驱动 NX 2412 CAD 建模。输入文字描述，自动生成 3D 模型。

## 架构

```
用户输入 → LLM(DeepSeek) → JSON工具链 → journal_gen.py → C# → run_journal.exe → NX 2412
                                     ↓
                               Three.js 实时预览
```

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
# 后端
uvicorn src.fastapi_app:app --reload --port 8000

# 前端（另一个终端）
cd frontend && npm run dev
```

浏览器打开 `http://localhost:3000`

## 软件要求

- **Siemens NX 2412** — 建模引擎
- **Python 3.10+** — 后端和 LLM 解析
- **Node.js 18+** — 前端预览
- **DeepSeek API Key** — 自然语言解析

## 项目结构

```
src/
  fastapi_app.py       # FastAPI 后端
  config.py            # 配置
  llm_parser.py        # LLM 解析（自然语言→参数）
  session_manager.py   # 会话管理
  tools/
    nx_modeler.cs      # ⭐ NX 2412 API 固定封装（13个工具）
    journal_gen.py     # ⭐ JSON → C# 翻译器
frontend/              # Next.js + Three.js 3D 预览
docs/                  # 开发文档和 API 基准
```

## 🙏 致谢

本项目基于 [Text-to-CAD](https://github.com/congelation/Text-to-CAD) 的架构进行改造，感谢原作者的出色工作。

主要改动：
- NX 执行层从 **NX 2312 Python** → **NX 2412 C# + run_journal.exe**
- 默认 LLM 从 豆包 → **DeepSeek**（用户可自定义）
- 所有 NX API 调用通过 `nx_modeler.cs` 固定封装，不猜测 API
