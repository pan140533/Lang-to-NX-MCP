# 多CAD平台架构规划

> 将 Lang-to-NX-MCP 架构扩展到 CATIA、SolidWorks 等多款工程软件
> 同一个 AI 管线 + 同一个前端 → 不同 CAD 的执行层

---

## 一、现状：Lang-to-NX-MCP（已完成）

```
前端 (Next.js + Three.js)
    ↓
API (FastAPI)
    ↓
Agent 管线 (Python)     ← 与CAD无关，可直接复用
    ↓
NX 执行层 (C# run_journal.exe)
    ├── nx_modeler.cs    ← NX2412 专属
    ├── generator.py     ← 生成 C# 代码
    └── tools.json       ← 56个工具定义
```

---

## 二、多CAD架构设计

```
                        前端 (Next.js + Three.js)
                              ↓
                         API (FastAPI)
                              ↓
                       Agent 管线 (Python)
                     ┌───────┴───────┐
                     ↓               ↓
                CAD抽象层             tools.json
            (统一接口定义)          (CAD无关)
                     ↓
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       NX执行层   CATIA执行层  SolidWorks执行层
    run_journal   Automation    AddIn
       .exe        .NET COM     .NET DLL
```

### 核心思想

**Agent 管线、tools.json、前端全是CAD无关的。** 只需要换执行层。

tools.json 里的每个工具，在各个CAD里有对应的实现：

| 工具 | NX | CATIA | SolidWorks |
|------|----|-------|------------|
| `block` | `Tool_Block()` | `ShapeFactory.AddNewPad()` | `PartManager.CreateBox()` |
| `boolean_unite` | `BooleanBuilder.Unite` | `BooleanOperand.Unite` | `BodyManager.AddCombine()` |
| `fillet` | `EdgeBlendBuilder` | `Fillet` | `FeatureFillet3` |

---

## 三、CATIA 执行层

### 3.1 CATIA Automation API 基础

```
编程语言：C# (.NET COM Interop) 或 VBA 或 CAA (C++)
API 名称：CATIA Automation (INFITF / MECMOD / PARTITF)
调用方式：COM Interop，通过 .NET 引用 Interop.CATIA.dll
执行方式：进程内或进程外连接 CATIA Application
```

### 3.2 CATIA 工具对照表

| 分类 | NX | CATIA | 差异 |
|------|----|-------|------|
| 文档 | `Tool_NewDocument()` | `CATIA.Documents.Add("Part")` | CATIA 直接加文档，不需模板 |
| 草图 | `SketchInPlaceBuilder` | `Factory2D.OpenEdition()` | CATIA 草图在 body 内部 |
| 画圆 | `Curves.CreateArc` | `Factory2D.CreateClosedCircle()` | 类似 |
| 块 | `CreateSketch→DrawRect→Extrude` | `Part.ShapeFactory.AddNewPadFromRef()` | CATIA 的 Pad = NX 的 Block |
| 圆柱 | `DrawCircle→Extrude` | `Part.ShapeFactory.AddNewShafFromRef()` | 或者用 Revolve |
| 拉伸 | `ExtrudeBuilder` | `ShapeFactory.AddNewPadFromRef()` | 核心建模操作 |
| 旋转 | `RevolveBuilder` | `ShapeFactory.AddNewShafFromRef()` | 概念相同 |
| 布尔合并 | `BooleanBuilder.Unite` | `ShapeFactory.AddNewAssemble()` | CATIA 的 Assemble = NX 的 Boolean |
| 布尔减去 | `BooleanBuilder.Subtract` | `ShapeFactory.AddNewRemove()` | CATIA 的 Remove |
| 布尔相交 | `BooleanBuilder.Intersect` | `ShapeFactory.AddNewIntersect()` | 同上 |
| 倒角 | `ChamferBuilder` | `ShapeFactory.AddNewChamfer()` | 类似 |
| 圆角 | `EdgeBlendBuilder` | `ShapeFactory.AddNewFillet()` | CATIA 的 Fillet |
| 孔 | `DrawCircle→ExtrudeCut` | `ShapeFactory.AddNewHole()` | CATIA 有专用 Hole |
| 抽壳 | `ShellBuilder` | `ShapeFactory.AddNewShell()` | 类似 |
| 阵列 | `PatternFeatureBuilder` | `ShapeFactory.AddNewRectPattern()` | CATIA 分 RectPattern/CircPattern |
| 镜像 | `MirrorFeatureBuilder` | `ShapeFactory.AddNewMirror()` | 类似 |
| 平移 | `MoveObjectBuilder` | `ShapeFactory.AddNewAxisToAxis()` | 方式不同 |

### 3.3 CATIA 执行层代码示例

```csharp
// 伪代码：CATIA 版的 nx_modeler.cs
// 需要 COM 引用：Interop.CATIA.dll

public class CATIAModeler
{
    public CATIA.Application app;
    public PartDocument doc;
    public Part part;
    public Body body;
    public Sketch sketch;
    public Factory2D factory2D;

    public void Init()
    {
        app = (CATIA.Application)Marshal.GetActiveObject("CATIA.Application");
        doc = app.ActiveDocument;
        part = doc.Part;
        body = part.Bodies.Item("PartBody");
    }

    public void Tool_NewDocument()
    {
        doc = app.Documents.Add("Part");
        part = doc.Part;
        body = part.Bodies.Item("PartBody");
    }

    public void Tool_Block(double x, double y, double z, double l, double w, double h)
    {
        // 创建草图
        sketch = body.Sketches.Add(part.ReferencePlanes.Item("XY"));
        factory2D = sketch.OpenEdition();
        
        // 画矩形
        factory2D.CreateLine(0, 0, l, 0);
        factory2D.CreateLine(l, 0, l, w);
        factory2D.CreateLine(l, w, 0, w);
        factory2D.CreateLine(0, w, 0, 0);
        
        sketch.CloseEdition();
        part.Update();

        // 拉伸成块 (Pad)
        ShapeFactory sf = part.ShapeFactory;
        Pad pad = sf.AddNewPadFromRef(sketch, h);
        part.Update();
    }

    public void Tool_BooleanUnite()
    {
        // CATIA 的布尔合并 = 装配体操作
        ShapeFactory sf = part.ShapeFactory;
        Assemble assemble = sf.AddNewAssemble(body);
        assemble.ParentBody = body;
        // 需要选第二个体
        part.Update();
    }

    // 更多方法...
}
```

### 3.4 generator.py 的 CATIA 版本

```python
# 当前 NX 版
def _gen_block(self, p: dict) -> str:
    return f"    m.Tool_Block({x}, {y}, {z}, {l}, {w}, {h});"

# CATIA 版
def _gen_block_catia(self, p: dict) -> str:
    return f"    cm.Tool_Block({x}, {y}, {z}, {l}, {w}, {h});"
# 只是方法名前缀从 m. 变成 cm.，参数完全一样
```

---

## 四、SolidWorks 执行层

### 4.1 基础信息

```
编程语言：C# (.NET COM Interop)
API 名称：SolidWorks.Interop.sldworks.dll
执行方式：COM 连接 SolidWorks 进程，创建 AddIn 或直接执行
```

### 4.2 工具对照表

| 工具 | SolidWorks API | 说明 |
|------|---------------|------|
| `block` | `PartDoc.Extension.SelectByID` + `FeatureManager.Extrude2` | 草图+拉伸 |
| `cylinder` | 同上，画圆再拉伸 | 同 NX |
| `boolean_unite` | `BodyManager.AddCombine` | 组合特征 |
| `boolean_subtract` | `BodyManager.AddCombine` + `CombineFeature.Subtract` | 同上 |
| `fillet` | `FeatureManager.Fillet3` | 圆角 |
| `shell` | `FeatureManager.Shell2` | 抽壳 |
| `pattern_linear` | `FeatureManager.GetPatternManager` | 阵列 |

---

## 五、统一 tools.json 设计

tools.json **不需要改**，因为工具名、参数是CAD无关的：

```json
{
  "name": "block",
  "description": "创建长方体",
  "params": {
    "x": {"type": "number"},
    "y": {"type": "number"},
    "z": {"type": "number"},
    "length": {"type": "number"},
    "width": {"type": "number"},
    "height": {"type": "number"}
  }
}
```

NX 执行层收到 `{"tool":"block","params":{...}}` → 生成 C# journal
CATIA 执行层收到同一个 JSON → 生成 CATIA COM 调用代码
SolidWorks 执行层收到同一个 JSON → 生成 SolidWorks API 调用代码

**前端、API、Agent 管线一概不用改。**

---

## 六、扩展示意

```
Lang-to-CAD/
├── frontend/                  ← 共用
├── backend/
│   ├── api.py                 ← 共用
│   ├── agent/                 ← 共用
│   ├── tools.json             ← 共用
│   ├── journal/               ← NX 执行层（当前）
│   │   ├── nx_modeler.cs
│   │   └── generator.py
│   ├── catia/                 ← CATIA 执行层（未来）
│   │   ├── catia_modeler.cs
│   │   └── generator_catia.py
│   └── solidworks/            ← SW 执行层（未来）
│       ├── sw_modeler.cs
│       └── generator_sw.py
└── output/
```

---

## 七、实现优先级

| 阶段 | 内容 | 预估 |
|------|------|------|
| Phase 1 | 补齐 NX 23 个 TODO（录 Journal） | ~2天 |
| Phase 2 | 智能体增强（多特征拆解） | ~3天 |
| **Phase 3** | **CATIA 原型**（只做 Block+Cylinder+Boolean 验证可行性） | **~1周** |
| Phase 4 | CATIA 全部工具对齐 | ~2周 |
| Phase 5 | SolidWorks | ~2周 |

**建议：先把 NX 的 23 个 TODO 补完，让 NX 版本功能完整，再考虑其他 CAD。** 换 CAD 要学的 API 复杂度不比你现在面对的小。
