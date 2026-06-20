# NX 2412 C# API 基准文档

> ⚠️ **此文件为基准，禁止修改。**
> 所有二次开发以此文档的 API 调用方式为唯一标准。
> 如有新 API 确认可用，追加在末尾，不修改已有内容。
> 记录日期：2026-06-16
> 验证工具：`run_journal.exe`

---

## 一、执行方式

所有 C# Journal 脚本通过 `run_journal.exe` 执行：

```
"E:\NX\NX\NXBIN\run_journal.exe" "<script.cs>"
```

成功标志：退出码 `0`，生成 `.prt` 模型文件。

---

## 二、脚本模板

```csharp
using System;
using NXOpen;
using NXOpen.Features;
using NXOpen.GeometricUtilities;

public class NXJournal
{
  public static void Main(string[] args)
  {
    Session theSession = Session.GetSession();
    Part workPart = theSession.Parts.Work;
    Part displayPart = theSession.Parts.Display;

    // ... API 调用 ...

    workPart.SaveAs(@"E:\model.prt");
  }
}
```

---

## 三、已验证的 API（不得修改）

### 3.1 新建部件

```csharp
FileNew fileNew1 = theSession.Parts.FileNew();
fileNew1.TemplateFileName = "model-plain-1-mm-template.prt";
fileNew1.UseBlankTemplate = false;
fileNew1.ApplicationName = "ModelTemplate";
fileNew1.Units = Part.Units.Millimeters;
fileNew1.TemplateType = FileNewTemplateType.Item;
fileNew1.NewFileName = @"E:\NX\model1.prt";
fileNew1.MakeDisplayedPart = true;
fileNew1.Commit();
fileNew1.Destroy();
workPart = theSession.Parts.Work;
displayPart = theSession.Parts.Display;
theSession.ApplicationSwitchImmediate("UG_APP_MODELING");
```

### 3.2 创建草图（在 XY 平面上）

```csharp
Sketch nullSk = null;
SketchInPlaceBuilder skBuilder = workPart.Sketches.CreateSketchInPlaceBuilder2(nullSk);
Point3d origin = new Point3d(0.0, 0.0, 0.0);
Vector3d normal = new Vector3d(0.0, 0.0, 1.0);
Plane plane = workPart.Planes.CreatePlane(origin, normal, SmartObject.UpdateOption.WithinModeling);
skBuilder.PlaneReference = plane;
NXObject skObj = skBuilder.Commit();
Sketch _sketch = (Sketch)skObj;
skBuilder.Destroy();
_sketch.Activate(Sketch.ViewReorient.True);
```

### 3.3 画圆（Arc）

> **注意：NX 2412 无 `CreateCircle`，使用 `CreateArc` 画完整圆。**

```csharp
Point3d center = new Point3d(0.0, 0.0, 0.0);
NXMatrix matrix = theSession.ActiveSketch.Orientation;
Arc _arc1 = workPart.Curves.CreateArc(center, matrix, 25.0, 0.0, 2.0 * Math.PI);
theSession.ActiveSketch.AddGeometry(_arc1, Sketch.InferConstraintsOption.InferNoConstraints);
theSession.ActiveSketch.Update();
```

参数说明：
- `CreateArc(center, matrix, radius, startAngle, endAngle)` — 角度为**弧度**
- `startAngle = 0.0`，`endAngle = 2.0 * Math.PI` 为完整圆
- `AddGeometry(curve, InferNoConstraints)` 将曲线添加到当前激活草图

### 3.4 画直线

```csharp
Line _line = workPart.Curves.CreateLine(
    new Point3d(x1, y1, 0.0),
    new Point3d(x2, y2, 0.0));
theSession.ActiveSketch.AddGeometry(_line, Sketch.InferConstraintsOption.InferNoConstraints);
theSession.ActiveSketch.Update();
```

### 3.5 画矩形

```csharp
Line _ln1 = workPart.Curves.CreateLine(new Point3d(x, y, 0.0), new Point3d(x+w, y, 0.0));
theSession.ActiveSketch.AddGeometry(_ln1, Sketch.InferConstraintsOption.InferNoConstraints);
Line _ln2 = workPart.Curves.CreateLine(new Point3d(x+w, y, 0.0), new Point3d(x+w, y+h, 0.0));
theSession.ActiveSketch.AddGeometry(_ln2, Sketch.InferConstraintsOption.InferNoConstraints);
Line _ln3 = workPart.Curves.CreateLine(new Point3d(x+w, y+h, 0.0), new Point3d(x, y+h, 0.0));
theSession.ActiveSketch.AddGeometry(_ln3, Sketch.InferConstraintsOption.InferNoConstraints);
Line _ln4 = workPart.Curves.CreateLine(new Point3d(x, y+h, 0.0), new Point3d(x, y, 0.0));
theSession.ActiveSketch.AddGeometry(_ln4, Sketch.InferConstraintsOption.InferNoConstraints);
theSession.ActiveSketch.Update();
```

### 3.6 关闭草图

```csharp
theSession.ActiveSketch.Deactivate(Sketch.ViewReorient.True, Sketch.UpdateLevel.Model);
```

> **注意：** `Deactivate` 在 `theSession.ActiveSketch` 上，不在 `workPart.Sketches` 上。

### 3.7 拉伸

```csharp
// 创建截面
Section section = workPart.Sections.CreateSection(0.0095, 0.01, 0.5);
section.SetAllowedEntityTypes(Section.AllowTypes.OnlyCurves);

// 创建区域边界选择规则
SelectionIntentRuleOptions ruleOpts = workPart.ScRuleFactory.CreateRuleOptions();
ruleOpts.SetSelectedFromInactive(false);
Point3d seedPt = new Point3d(0.0, 0.0, 0.0);
RegionBoundaryRule boundaryRule = workPart.ScRuleFactory.CreateRuleRegionBoundary(
    _sketch, null, seedPt, 0.01, ruleOpts);
ruleOpts.Dispose();
section.AllowSelfIntersection(true);
section.AddToSection(new SelectionIntentRule[] { boundaryRule }, null, null, null, seedPt, Section.Mode.Create, false);

// 创建拉伸特征
ExtrudeBuilder extBuilder = workPart.Features.CreateExtrudeBuilder(null);
extBuilder.Section = section;
extBuilder.BooleanOperation.Type = BooleanOperation.BooleanType.Create;
extBuilder.Limits.StartExtend.Value.SetFormula("0");
extBuilder.Limits.EndExtend.Value.SetFormula("80");
extBuilder.AllowSelfIntersectingSection(true);
Feature _extrude = extBuilder.CommitFeature();
extBuilder.Destroy();
```

参数说明：
- `CreateRegionBoundary(sketch, curves, seedPoint, tolerance, options)` — sketch 是草图对象，curves 为 null 时自动检测封闭区域
- `AddToSection(rules, seed, start, end, helpPoint, mode, disableChaining)` — 严格 7 参数
- `Limits.EndExtend.Value.SetFormula("80")` — 拉伸长度用 `SetFormula` 设置
- `BooleanType.Create` — 新建实体（`Subtract` = 切除）

### 3.8 切除（拉伸切槽）

与 3.7 相同，仅改变：

```csharp
extBuilder.BooleanOperation.Type = BooleanOperation.BooleanType.Subtract;
```

### 3.9 保存模型

```csharp
workPart.SaveAs(@"E:\NX\model.prt");
```

---

## 四、枚举值对照

| C# 枚举（Journal自动生成） | Python 对应 | 说明 |
|---------------------------|-------------|------|
| `Sketch.ViewReorient.True` | `NXOpen.SketchViewReorient.TrueValue` | Python 中 True 为关键字 |
| `Sketch.UpdateLevel.Model` | `NXOpen.SketchUpdateLevel.Model` | — |
| `Sketch.InferConstraintsOption.InferNoConstraints` | `NXOpen.SketchInferConstraintsOption.InferNoConstraints` | — |
| `BooleanOperation.BooleanType.Create` | `NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create` | — |
| `BooleanOperation.BooleanType.Subtract` | 同上 `.Subtract` | — |
| `Part.Units.Millimeters` | `NXOpen.Part.Units.Millimeters` | — |
| `SmartObject.UpdateOption.WithinModeling` | `NXOpen.SmartObject.UpdateOption.WithinModeling` | — |

---

## 五、已验证的完整流程

### 流程 1：圆柱体 ✅ 通过

```
new_document → create_sketch_on_plane → draw_closed_circle(25)
  → close_sketch → extrude(80) → save_model
```

生成：`output/models/cyl_final.prt`（72KB）

### 流程 2：长方体 ✅ 通过

```
new_document → create_sketch_on_plane → draw_rectangle(100×60)
  → close_sketch → extrude(30) → save_model
```

生成：`output/models/rect_test.prt`（72KB）

---

## 六、注意事项

1. **路径不能含中文** — `run_journal.exe` 打开含中文路径的文件会失败
2. **先关闭草图再拉伸** — `ActiveSketch` 在激活状态下才能画图，但拉伸前必须 Deactivate
3. **`CreateCircle` 不存在** — NX 2412 删除了此 API，用 `CreateArc` 画 360° 圆弧代替
4. **所有 `Builder` 必须 `Destroy()`** — 否则 NX 会泄漏内存
5. **长度参数用字符串** — `.SetFormula("数值")`，不是直接赋数值

---

## 七、已验证的 API

以下 API 已在 nx_modeler.cs 中实现并验证通过：

| API | 状态 | 说明 |
|-----|:----:|------|
| `FileNew` — 新建部件 | ✅ | |
| `CreateSketchInPlaceBuilder2` — 创建草图 | ✅ | |
| `CreateArc` — 画圆 | ✅ | |
| `CreateLine` — 画直线 | ✅ | |
| `ExtrudeBuilder` — 拉伸（Create） | ✅ | |
| `ExtrudeBuilder + BooleanBuilder` — 切除（Subtract） | ✅ | |
| `RevolveBuilder` — 旋转体 | ✅ | |
| `ChamferBuilder` — 倒角 | ✅ | |
| `EdgeBlendBuilder` — 圆角 | ✅ | |
| `BooleanBuilder` — 布尔运算 | ✅ | |
| `DatumPlaneBuilder` — 偏移平面 | ❌ 未验证 | |

---

## 八、开发方式参考（附录）

> 当前以 **C# + run_journal.exe** 为唯一开发方式。
> 以下列出其他可选方式，供未来重构参考。

| 方式 | 语言 | 适用场景 | 当前状态 |
|------|------|---------|:--------:|
| **Open C API** | C | 底层操作、旧代码维护 | ⚠️ 备选 |
| **NXOpen C++** | C++ | 大型商业应用、高性能 | ⚠️ 备选 |
| **NXOpen .NET** | C# | **当前正在使用** | ✅ **主力** |
| **NXOpen Java** | Java | 跨平台、Java 集成 | ❌ 未使用 |
| **NXOpen Python** | Python | 快速原型、AI 集成 | ❌ 已弃用（API 不稳定） |
| **SNAP** | VB.NET | 初学者入门 | ❌ 不适用 |

### 如果未来要重构

1. **换回 Python**：需重新录制 NX 2412 Journal 确认 API 签名（Python 绑定与 C# 不同）
2. **换 C++**：直接使用 `E:\NX\NX\UGOPEN\NXOpen\` 头文件，签名与 C# 基本一致
3. **换 Open C API**：使用 `E:\NX\NX\UGOPEN\` 下的 C 头文件（`uf_*.h`）
