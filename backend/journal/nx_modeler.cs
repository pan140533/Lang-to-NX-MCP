using System;
using System.Collections.Generic;
using NXOpen;
using NXOpen.Features;
using NXOpen.GeometricUtilities;

public class NXModeler
{
  public Session ses; public Part wp; public Part dp;
  public Sketch curSketch; public Arc curArc; public Body curBody;
  public List<ICurve> curCurves = new List<ICurve>();
  public string outPath = "./output/models";
  private Feature _lastFeature = null;  // 追踪最后创建的特征（用于阵列）
  private Body _previousBody = null;    // 追踪上一个体（用于布尔操作）

  public void Init()
  { ses = Session.GetSession(); wp = ses.Parts.Work; dp = ses.Parts.Display; }

  public void Tool_NewDocument(string name)
  {
    string tmp = outPath + "\\tmp_" + Guid.NewGuid().ToString("N").Substring(0, 8) + ".prt";
    FileNew fn = ses.Parts.FileNew();
    fn.TemplateFileName = "model-plain-1-mm-template.prt";
    fn.UseBlankTemplate = false; fn.ApplicationName = "ModelTemplate";
    fn.Units = Part.Units.Millimeters; fn.NewFileName = tmp;
    fn.MakeDisplayedPart = true; fn.Commit(); fn.Destroy();
    wp = ses.Parts.Work; dp = ses.Parts.Display;
    ses.ApplicationSwitchImmediate("UG_APP_MODELING");
    curArc = null; curCurves.Clear();
  }

  public void Tool_CreateSketch()
  {
    Sketch sn = null;
    SketchInPlaceBuilder sb = wp.Sketches.CreateSketchInPlaceBuilder2(sn);
    sb.PlaneReference = wp.Planes.CreatePlane(
        new Point3d(0,0,0), new Vector3d(0,0,1), SmartObject.UpdateOption.WithinModeling);
    NXObject o = sb.Commit(); curSketch = (Sketch)o; sb.Destroy();
    curSketch.Activate(Sketch.ViewReorient.True);
    curArc = null; curCurves.Clear();
  }

  public void Tool_DrawCircle(double x, double y, double r)
  {
    NXMatrix mx = ses.ActiveSketch.Orientation;
    curArc = wp.Curves.CreateArc(new Point3d(x,y,0), mx, r, 0.0, 2.0*Math.PI);
    curCurves.Add(curArc);
    ses.ActiveSketch.AddGeometry(curArc, Sketch.InferConstraintsOption.InferNoConstraints);
    ses.ActiveSketch.Update();
  }

  public void Tool_DrawLine(double x1, double y1, double x2, double y2)
  {
    Line ln = wp.Curves.CreateLine(new Point3d(x1,y1,0), new Point3d(x2,y2,0));
    curCurves.Add(ln);
    ses.ActiveSketch.AddGeometry(ln, Sketch.InferConstraintsOption.InferNoConstraints);
    ses.ActiveSketch.Update();
  }

  public void Tool_DrawRectangle(double x, double y, double w, double h)
  {
    Tool_DrawLine(x, y, x+w, y); Tool_DrawLine(x+w, y, x+w, y+h);
    Tool_DrawLine(x+w, y+h, x, y+h); Tool_DrawLine(x, y+h, x, y);
  }

  public void Tool_CloseSketch()
  { ses.ActiveSketch.Deactivate(Sketch.ViewReorient.True, Sketch.UpdateLevel.Model); }

  Point3d CalcSeed()
  {
    double sx=0,sy=0; int n=0;
    foreach (ICurve cv in curCurves) {
      Arc a = cv as Arc; Line l = cv as Line;
      if (a != null) { sx+=a.CenterPoint.X; sy+=a.CenterPoint.Y; n++; }
      else if (l != null) { sx+=(l.StartPoint.X+l.EndPoint.X)/2; sy+=(l.StartPoint.Y+l.EndPoint.Y)/2; n++; }
    }
    return n>0 ? new Point3d(sx/n,sy/n,0) : new Point3d(0,0,0);
  }

  public void Tool_Extrude(double len)
  {
    Tool_ExtrudeFrom(0, len);
  }

  public void Tool_ExtrudeFrom(double start, double len)
  {
    Section sec = wp.Sections.CreateSection(0.0095, 0.01, 0.5);
    sec.SetAllowedEntityTypes(Section.AllowTypes.OnlyCurves);
    SelectionIntentRuleOptions ro = wp.ScRuleFactory.CreateRuleOptions();
    ro.SetSelectedFromInactive(false);
    Point3d seed = CalcSeed();
    RegionBoundaryRule br = wp.ScRuleFactory.CreateRuleRegionBoundary(curSketch, curCurves.ToArray(), seed, 0.01, ro);
    ro.Dispose(); sec.AllowSelfIntersection(true);
    sec.AddToSection(new SelectionIntentRule[]{br}, null, null, null, seed, Section.Mode.Create, false);
    ExtrudeBuilder eb = wp.Features.CreateExtrudeBuilder(null);
    eb.Section = sec;
    eb.Direction = wp.Directions.CreateDirection(curSketch, Sense.Forward, SmartObject.UpdateOption.WithinModeling);
    eb.BooleanOperation.SetTargetBodies(new Body[0]);
    eb.BooleanOperation.Type = BooleanOperation.BooleanType.Create;
    eb.Limits.StartExtend.Value.SetFormula(start.ToString());
    eb.Limits.EndExtend.Value.SetFormula((start + len).ToString());
    eb.AllowSelfIntersectingSection(true);
    Feature f = eb.CommitFeature(); eb.Destroy();
    _lastFeature = f;
    if (f.GetBodies().Length > 0) { _previousBody = curBody; curBody = f.GetBodies()[0]; }
  }

  public void Tool_ExtrudeCut(double len)
  {
    Section sec = wp.Sections.CreateSection(0.0095, 0.01, 0.5);
    sec.SetAllowedEntityTypes(Section.AllowTypes.OnlyCurves); sec.DistanceTolerance = 0.01;
    SelectionIntentRuleOptions ro = wp.ScRuleFactory.CreateRuleOptions();
    ro.SetSelectedFromInactive(false); sec.AllowSelfIntersection(true);
    Point3d seed = CalcSeed();
    bool allArcs = true;
    foreach (ICurve cv in curCurves) { if (!(cv is Arc)) { allArcs = false; break; } }
    if (allArcs && curCurves.Count > 1) {
      foreach (ICurve cv in curCurves) {
        Arc a = cv as Arc; Point3d aseed = (a != null) ? a.CenterPoint : CalcSeed();
        var br = wp.ScRuleFactory.CreateRuleRegionBoundary(curSketch, new ICurve[]{cv}, aseed, 0.01, ro);
        sec.AddToSection(new SelectionIntentRule[]{br}, null, null, null, aseed, Section.Mode.Create, false);
      }
    } else {
      var br = wp.ScRuleFactory.CreateRuleRegionBoundary(curSketch, curCurves.ToArray(), seed, 0.01, ro);
      sec.AddToSection(new SelectionIntentRule[]{br}, null, null, null, seed, Section.Mode.Create, false);
    }
    ro.Dispose();
    ExtrudeBuilder eb2 = wp.Features.CreateExtrudeBuilder(null);
    eb2.Section = sec;
    eb2.Direction = wp.Directions.CreateDirection(curSketch, Sense.Forward, SmartObject.UpdateOption.WithinModeling);
    eb2.BooleanOperation.Type = BooleanOperation.BooleanType.Create;
    eb2.Limits.StartExtend.Value.SetFormula("0"); eb2.Limits.EndExtend.Value.SetFormula(len.ToString());
    eb2.AllowSelfIntersectingSection(true);
    Feature ft = eb2.CommitFeature(); eb2.Destroy();
    if (curBody != null && ft.GetBodies().Length > 0) {
      Body toolBody = ft.GetBodies()[0];
      var boolB = wp.Features.CreateBooleanBuilder(null);
      boolB.Operation = Feature.BooleanType.Subtract; boolB.Target = curBody;
      ScCollector coll = wp.ScCollectors.CreateCollector();
      coll.ReplaceRules(new SelectionIntentRule[]{wp.ScRuleFactory.CreateRuleBodyDumb(new Body[]{toolBody})}, false);
      boolB.ToolBodyCollector = coll;
      boolB.CommitFeature(); boolB.Destroy();
    }
  }

  public void Tool_Revolve(double angle)
  {
    Section sec = wp.Sections.CreateSection(0.0095, 0.01, 0.5);
    sec.SetAllowedEntityTypes(Section.AllowTypes.OnlyCurves);
    SelectionIntentRuleOptions ro = wp.ScRuleFactory.CreateRuleOptions();
    ro.SetSelectedFromInactive(false);
    Point3d seed = CalcSeed();
    RegionBoundaryRule br = wp.ScRuleFactory.CreateRuleRegionBoundary(curSketch, curCurves.ToArray(), seed, 0.01, ro);
    ro.Dispose(); sec.AllowSelfIntersection(true);
    sec.AddToSection(new SelectionIntentRule[]{br}, null, null, null, seed, Section.Mode.Create, false);
    Axis axis = wp.Axes.CreateAxis(new Point3d(0,0,0), new Vector3d(0,0,1), SmartObject.UpdateOption.WithinModeling);
    RevolveBuilder rb = wp.Features.CreateRevolveBuilder(null);
    rb.Section = sec; rb.Axis = axis;
    rb.BooleanOperation.Type = BooleanOperation.BooleanType.Create;
    rb.Limits.StartExtend.Value.SetFormula("0"); rb.Limits.EndExtend.Value.SetFormula(angle.ToString());
    Feature fr = rb.CommitFeature(); rb.Destroy();
    try { NXObject[] objs = fr.GetEntities(); if (objs != null) foreach (NXObject o in objs) { Body b = o as Body; if (b != null) { _previousBody = curBody; curBody = b; break; } } } catch { }
  }

  public void Tool_Chamfer(double len)
  {
    if (curBody == null) return;
    var cb = wp.Features.CreateChamferBuilder(null);
    cb.Option = ChamferBuilder.ChamferOption.SymmetricOffsets;
    cb.FirstOffset = len.ToString();
    var coll = wp.ScCollectors.CreateCollector();
    coll.ReplaceRules(new SelectionIntentRule[]{wp.ScRuleFactory.CreateRuleEdgeDumb(curBody.GetEdges())}, false);
    cb.SmartCollector = coll;
    cb.CommitFeature(); cb.Destroy();
  }

  public void Tool_Fillet(double rad)
  {
    if (curBody == null) return;
    try
    {
      var fb = wp.Features.CreateEdgeBlendBuilder(null);
      var coll = wp.ScCollectors.CreateCollector();
      coll.ReplaceRules(new SelectionIntentRule[]{wp.ScRuleFactory.CreateRuleEdgeDumb(curBody.GetEdges())}, false);
      fb.NonCliffEdges = coll;
      fb.AddChainset(coll, rad.ToString());
      Feature f = fb.CommitFeature();
      fb.Destroy();
      _lastFeature = f;
      Console.WriteLine("[OK] Fillet: radius={0}", rad);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] Fillet failed: {0}", ex.Message);
    }
  }

  public void Tool_Cone(double r, double h)
  {
    // 圆锥：多层圆柱递减逼近
    int layers = 10;
    for (int i = 0; i < layers; i++)
    {
      double bot = (double)h * i / layers;
      double top = (double)h * (i + 1) / layers;
      double radius = r * (1.0 - (double)(i + 0.5) / layers);
      Tool_CreateSketch();
      Tool_DrawCircle(0, 0, radius);
      Tool_CloseSketch();
      Tool_ExtrudeFrom(bot, top - bot);
    }
  }
  public void Tool_Sphere(double r)
  {
    // 球体：多层圆盘堆叠逼近
    int layers = 16;
    for (int i = 0; i < layers; i++)
    {
      double bot = -r + 2.0 * r * i / layers;
      double top = -r + 2.0 * r * (i + 1) / layers;
      double midY = (bot + top) / 2.0;
      double radius = Math.Sqrt(r * r - midY * midY);
      Tool_CreateSketch();
      Tool_DrawCircle(0, 0, radius);
      Tool_CloseSketch();
      Tool_ExtrudeFrom(bot, top - bot);
    }
  }
  public void Tool_SaveModel(string path)
  {
    if (wp == null) wp = ses.Parts.Work;
    wp.SaveAs(path); Console.WriteLine("Saved: " + path);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 草图操作（补充）
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_CreateSketchOnFace(int faceIndex)
  {
    // TODO: 在指定面上创建草图（需要 NXOpen Face API）
    Console.WriteLine("[TODO] Tool_CreateSketchOnFace: face_index={0}", faceIndex);
    // 暂时回退到默认草图
    Tool_CreateSketch();
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 绘图工具（补充）
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_DrawArc(double x, double y, double r, double startAngle, double endAngle)
  {
    NXMatrix mx = ses.ActiveSketch.Orientation;
    double sa = startAngle * Math.PI / 180.0;
    double ea = endAngle * Math.PI / 180.0;
    curArc = wp.Curves.CreateArc(new Point3d(x, y, 0), mx, r, sa, ea);
    curCurves.Add(curArc);
    ses.ActiveSketch.AddGeometry(curArc, Sketch.InferConstraintsOption.InferNoConstraints);
    ses.ActiveSketch.Update();
  }

  public void Tool_DrawPolyline(Point3d[] points)
  {
    for (int i = 0; i < points.Length - 1; i++)
    {
      Line ln = wp.Curves.CreateLine(
        new Point3d(points[i].X, points[i].Y, 0),
        new Point3d(points[i+1].X, points[i+1].Y, 0));
      curCurves.Add(ln);
      ses.ActiveSketch.AddGeometry(ln, Sketch.InferConstraintsOption.InferNoConstraints);
    }
    ses.ActiveSketch.Update();
  }

  public void Tool_DrawSpline(Point3d[] points)
  {
    // TODO: 样条曲线（需要 NXOpen Spline API）
    Console.WriteLine("[TODO] Tool_DrawSpline: {0} points", points.Length);
    // 回退：用多段线近似
    Tool_DrawPolyline(points);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 基本体素（补充）
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_Block(double x, double y, double z, double l, double w, double h)
  {
    // 块：矩形截面 + 从指定高度拉伸
    Tool_CreateSketch();
    Tool_DrawRectangle(x, y, l, w);
    Tool_CloseSketch();
    Tool_ExtrudeFrom(z, h);
  }

  public void Tool_Cylinder(double x, double y, double z, double r, double h)
  {
    // 圆柱：圆截面 + 从指定高度拉伸
    Tool_CreateSketch();
    Tool_DrawCircle(x, y, r);
    Tool_CloseSketch();
    Tool_ExtrudeFrom(z, h);
  }

  public void Tool_Torus(double majorR, double minorR)
  {
    try
    {
      // Create a circular guide curve in XY plane
      NXMatrix mx = null;
      Arc guideArc = null;
      try { mx = ses.ActiveSketch.Orientation; } catch { }
      if (mx == null)
        guideArc = wp.Curves.CreateArc(new Point3d(0, 0, 0),
            new Vector3d(1, 0, 0), new Vector3d(0, 1, 0),
            majorR, 0.0, 2.0 * Math.PI);
      else
        guideArc = wp.Curves.CreateArc(new Point3d(0, 0, 0), mx,
            majorR, 0.0, 2.0 * Math.PI);

      TubeBuilder tb = wp.Features.CreateTubeBuilder(null);
      Section guideSec = wp.Sections.CreateSection(0.0095, 0.01, 0.5);
      guideSec.SetAllowedEntityTypes(Section.AllowTypes.OnlyCurves);
      SelectionIntentRuleOptions ro = wp.ScRuleFactory.CreateRuleOptions();
      ro.SetSelectedFromInactive(false);
      CurveDumbRule cr = wp.ScRuleFactory.CreateRuleCurveDumb(new Curve[]{guideArc});
      guideSec.AddToSection(new SelectionIntentRule[]{cr}, guideArc, null, null,
          new Point3d(majorR, 0, 0), Section.Mode.Create, false);
      ro.Dispose();
      tb.OuterDiameter.RightHandSide = (minorR * 2.0).ToString();

      Feature f = tb.CommitFeature();
      tb.Destroy();
      _lastFeature = f;
      if (f.GetBodies().Length > 0) { _previousBody = curBody; curBody = f.GetBodies()[0]; }
      Console.WriteLine("[OK] Torus: major={0}, minor={1}", majorR, minorR);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] Torus failed: {0}", ex.Message);
      // Fallback: sketch + revolve approach
      try
      {
        Tool_CreateSketch();
        Tool_DrawCircle(majorR, 0, minorR);
        Tool_CloseSketch();
        Tool_Revolve(360);
        Console.WriteLine("[OK] Torus (fallback via revolve): major={0}, minor={1}", majorR, minorR);
      }
      catch (Exception ex2)
      {
        Console.WriteLine("[!] Torus fallback also failed: {0}", ex2.Message);
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 扫描特征（补充）
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_Sweep(Point3d[] pathPoints)
  {
    // TODO: 扫掠（NX2412 需用 FreeformSurfaceCollection.CreateSweptBuilder1）
    Console.WriteLine("[TODO] Tool_Sweep: {0} path points",
        pathPoints != null ? pathPoints.Length : 0);
  }

  public void Tool_Loft(string[] sectionRefs)
  {
    // TODO: 放样（需要 NXOpen LoftBuilder API）
    Console.WriteLine("[TODO] Tool_Loft: {0} sections", sectionRefs.Length);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 布尔操作
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_BooleanUnite(string targetRef, string toolRef)
  {
    Body targetBody = curBody;
    Body toolBody = _previousBody;
    if (targetBody == null || toolBody == null)
    {
      Console.WriteLine("[!] BooleanUnite: need two bodies (curBody and _previousBody)");
      return;
    }
    try
    {
      BooleanBuilder bb = wp.Features.CreateBooleanBuilder(null);
      bb.Operation = Feature.BooleanType.Unite;
      bb.Target = targetBody;
      ScCollector coll = wp.ScCollectors.CreateCollector();
      coll.ReplaceRules(new SelectionIntentRule[]{wp.ScRuleFactory.CreateRuleBodyDumb(new Body[]{toolBody})}, false);
      bb.ToolBodyCollector = coll;
      Feature f = bb.CommitFeature();
      bb.Destroy();
      _lastFeature = f;
      if (f.GetBodies().Length > 0) curBody = f.GetBodies()[0];
      _previousBody = null;
      Console.WriteLine("[OK] BooleanUnite");
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] BooleanUnite failed: {0}", ex.Message);
    }
  }

  public void Tool_BooleanSubtract(string targetRef, string toolRef)
  {
    Body targetBody = _previousBody;
    Body toolBody = curBody;
    if (targetBody == null || toolBody == null)
    {
      Console.WriteLine("[!] BooleanSubtract: need two bodies");
      return;
    }
    try
    {
      BooleanBuilder bb = wp.Features.CreateBooleanBuilder(null);
      bb.Operation = Feature.BooleanType.Subtract;
      bb.Target = targetBody;
      ScCollector coll = wp.ScCollectors.CreateCollector();
      coll.ReplaceRules(new SelectionIntentRule[]{wp.ScRuleFactory.CreateRuleBodyDumb(new Body[]{toolBody})}, false);
      bb.ToolBodyCollector = coll;
      Feature f = bb.CommitFeature();
      bb.Destroy();
      _lastFeature = f;
      if (f.GetBodies().Length > 0) curBody = f.GetBodies()[0];
      _previousBody = null;
      Console.WriteLine("[OK] BooleanSubtract");
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] BooleanSubtract failed: {0}", ex.Message);
    }
  }

  public void Tool_BooleanIntersect(string targetRef, string toolRef)
  {
    Body targetBody = curBody;
    Body toolBody = _previousBody;
    if (targetBody == null || toolBody == null)
    {
      Console.WriteLine("[!] BooleanIntersect: need two bodies");
      return;
    }
    try
    {
      BooleanBuilder bb = wp.Features.CreateBooleanBuilder(null);
      bb.Operation = Feature.BooleanType.Intersect;
      bb.Target = targetBody;
      ScCollector coll = wp.ScCollectors.CreateCollector();
      coll.ReplaceRules(new SelectionIntentRule[]{wp.ScRuleFactory.CreateRuleBodyDumb(new Body[]{toolBody})}, false);
      bb.ToolBodyCollector = coll;
      Feature f = bb.CommitFeature();
      bb.Destroy();
      _lastFeature = f;
      if (f.GetBodies().Length > 0) curBody = f.GetBodies()[0];
      _previousBody = null;
      Console.WriteLine("[OK] BooleanIntersect");
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] BooleanIntersect failed: {0}", ex.Message);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 细节特征（补充）
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_EdgeBlend(double radius, int[] edgeIndices)
  {
    if (curBody == null)
    {
      Console.WriteLine("[!] EdgeBlend: no curBody");
      return;
    }
    try
    {
      EdgeBlendBuilder eb = wp.Features.CreateEdgeBlendBuilder(null);

      Edge[] allEdges = curBody.GetEdges();
      ScCollector coll = wp.ScCollectors.CreateCollector();
      if (edgeIndices != null && edgeIndices.Length > 0)
      {
        List<Edge> selEdges = new List<Edge>();
        foreach (int idx in edgeIndices)
          if (idx >= 0 && idx < allEdges.Length) selEdges.Add(allEdges[idx]);
        coll.ReplaceRules(new SelectionIntentRule[]{
            wp.ScRuleFactory.CreateRuleEdgeDumb(selEdges.ToArray())}, false);
      }
      else
      {
        coll.ReplaceRules(new SelectionIntentRule[]{
            wp.ScRuleFactory.CreateRuleEdgeDumb(allEdges)}, false);
      }
      eb.NonCliffEdges = coll;
      eb.AddChainset(coll, radius.ToString());

      Feature f = eb.CommitFeature();
      eb.Destroy();
      _lastFeature = f;
      Console.WriteLine("[OK] EdgeBlend: radius={0}, edges={1}",
          radius, edgeIndices != null ? edgeIndices.Length : 0);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] EdgeBlend failed: {0}", ex.Message);
    }
  }

  public void Tool_Shell(double thickness, int removeFaceIndex)
  {
    if (curBody == null)
    {
      Console.WriteLine("[!] Shell: no curBody");
      return;
    }
    try
    {
      ShellBuilder sb = wp.Features.CreateShellBuilder(null);
      sb.Body = curBody;
      sb.DefaultThickness.RightHandSide = thickness.ToString();
      sb.Tolerance = 0.1;

      Face[] faces = curBody.GetFaces();
      if (removeFaceIndex >= 0 && removeFaceIndex < faces.Length)
      {
        ScCollector faceColl = wp.ScCollectors.CreateCollector();
        faceColl.ReplaceRules(new SelectionIntentRule[]{
            wp.ScRuleFactory.CreateRuleFaceDumb(new Face[]{faces[removeFaceIndex]})}, false);
        sb.RemovedFacesCollector = faceColl;
      }
      // else: shell entire body without removing faces

      Feature f = sb.CommitFeature();
      sb.Destroy();
      _lastFeature = f;
      Console.WriteLine("[OK] Shell: thickness={0}, remove_face={1}", thickness, removeFaceIndex);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] Shell failed: {0}", ex.Message);
    }
  }

  public void Tool_Hole(double x, double y, double diameter, double depth, string holeType)
  {
    // 孔：圆截面 + 切除
    Tool_CreateSketch();
    Tool_DrawCircle(x, y, diameter / 2.0);
    Tool_CloseSketch();
    Tool_ExtrudeCut(depth);
  }

  public void Tool_Pocket(double x, double y, double length, double width, double depth)
  {
    // 矩形槽：矩形截面 + 切除
    Tool_CreateSketch();
    Tool_DrawRectangle(x - length / 2.0, y - width / 2.0, length, width);
    Tool_CloseSketch();
    Tool_ExtrudeCut(depth);
  }

  public void Tool_Boss(double x, double y, double diameter, double height)
  {
    // 凸台：圆截面 + 拉伸叠加
    Tool_CreateSketch();
    Tool_DrawCircle(x, y, diameter / 2.0);
    Tool_CloseSketch();
    Tool_Extrude(height);
  }

  public void Tool_Pad(double x, double y, double length, double width, double height)
  {
    // 凸垫：矩形截面 + 拉伸叠加
    Tool_CreateSketch();
    Tool_DrawRectangle(x - length / 2.0, y - width / 2.0, length, width);
    Tool_CloseSketch();
    Tool_Extrude(height);
  }

  public void Tool_Slot(double x, double y, double length, double width, double depth)
  {
    // 直线槽：矩形截面 + 切除
    Tool_CreateSketch();
    Tool_DrawRectangle(x, y - width / 2.0, length, width);
    Tool_CloseSketch();
    Tool_ExtrudeCut(depth);
  }

  public void Tool_Groove(double diameter, double width, double depth)
  {
    // TODO: 环形沟槽（需要 NXOpen GrooveBuilder API）
    Console.WriteLine("[TODO] Tool_Groove: dia={0}, w={1}, d={2}", diameter, width, depth);
    // 简易逼近：在圆柱面上画一圈矩形槽
    Tool_CreateSketch();
    Tool_DrawRectangle(diameter / 2.0 - depth, -width / 2.0, depth, width);
    Tool_CloseSketch();
    Tool_Revolve(360);
  }

  public void Tool_Thread(string cylinderRef, string threadType, double length)
  {
    // TODO: 螺纹（需要 NXOpen ThreadBuilder API）
    Console.WriteLine("[TODO] Tool_Thread: ref={0}, type={1}, len={2}", cylinderRef, threadType, length);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 阵列与镜像
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_PatternLinear(string featureRef, int countX, double spacingX, int countY, double spacingY)
  {
    if (_lastFeature == null)
    {
      Console.WriteLine("[!] PatternLinear: no feature to pattern");
      return;
    }

    try
    {
      var builder = wp.Features.CreatePatternFeatureBuilder(null);
      builder.FeatureList.Add(_lastFeature);

      var patternDef = builder.PatternService;
      patternDef.PatternType = PatternDefinition.PatternEnum.Linear;

      var rectDef = patternDef.RectangularDefinition;
      rectDef.XSpacing.NCopies.RightHandSide = countX.ToString();
      rectDef.XSpacing.PitchDistance.RightHandSide = spacingX.ToString();
      rectDef.XDirection = wp.Directions.CreateDirection(
          new Point3d(0, 0, 0), new Vector3d(1, 0, 0), SmartObject.UpdateOption.WithinModeling);
      if (countY > 1)
      {
        rectDef.YSpacing.NCopies.RightHandSide = countY.ToString();
        rectDef.YSpacing.PitchDistance.RightHandSide = spacingY.ToString();
        rectDef.YDirection = wp.Directions.CreateDirection(
            new Point3d(0, 0, 0), new Vector3d(0, 1, 0), SmartObject.UpdateOption.WithinModeling);
        rectDef.UseYDirectionToggle = true;
      }

      var result = builder.CommitFeature();
      builder.Destroy();
      Console.WriteLine("[OK] LinearPattern: {0} x {1} (dx={2}, dy={3})", countX, countY, spacingX, spacingY);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] LinearPattern failed: {0}", ex.Message);
    }
  }

  public void Tool_PatternCircular(string featureRef, int count, double angle)
  {
    if (_lastFeature == null)
    {
      Console.WriteLine("[!] PatternCircular: no feature to pattern");
      return;
    }

    try
    {
      var builder = wp.Features.CreatePatternFeatureBuilder(null);
      builder.FeatureList.Add(_lastFeature);

      // 设置为圆形阵列
      var patternDef = builder.PatternService;
      patternDef.PatternType = PatternDefinition.PatternEnum.Circular;

      // 设置数量和角度
      var circularDef = patternDef.CircularDefinition;
      circularDef.AngularSpacing.NCopies.RightHandSide = count.ToString();
      circularDef.AngularSpacing.PitchAngle.RightHandSide = angle.ToString();

      // 旋转中心：原点
      circularDef.RotationCenter = wp.Points.CreatePoint(new Point3d(0, 0, 0));
      // 旋转轴：Z 轴
      Point3d origin = new Point3d(0, 0, 0);
      Vector3d zDir = new Vector3d(0, 0, 1);
      circularDef.RotationAxis = wp.Axes.CreateAxis(origin, zDir, SmartObject.UpdateOption.WithinModeling);

      var result = builder.CommitFeature();
      builder.Destroy();
      Console.WriteLine("[OK] CircularPattern: {0} instances, {1}°", count, angle);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] CircularPattern failed: {0}", ex.Message);
    }
  }

  public void Tool_MirrorFeature(string featureRef, string mirrorPlane)
  {
    if (_lastFeature == null)
    {
      Console.WriteLine("[!] MirrorFeature: no feature to mirror");
      return;
    }

    try
    {
      MirrorFeatureBuilder mb = wp.Features.CreateMirrorFeatureBuilder(null);
      mb.FeatureSet.Add(_lastFeature);

      // Determine mirror plane based on string
      Plane mirrorPlaneObj = null;
      string plane = (mirrorPlane ?? "YZ").ToUpper();
      if (plane == "XY")
        mirrorPlaneObj = wp.Planes.CreatePlane(
            new Point3d(0, 0, 0), new Vector3d(0, 0, 1), SmartObject.UpdateOption.WithinModeling);
      else if (plane == "YZ")
        mirrorPlaneObj = wp.Planes.CreatePlane(
            new Point3d(0, 0, 0), new Vector3d(1, 0, 0), SmartObject.UpdateOption.WithinModeling);
      else if (plane == "XZ")
        mirrorPlaneObj = wp.Planes.CreatePlane(
            new Point3d(0, 0, 0), new Vector3d(0, 1, 0), SmartObject.UpdateOption.WithinModeling);
      else
      {
        Console.WriteLine("[!] MirrorFeature: unknown plane '{0}', using YZ", mirrorPlane);
        mirrorPlaneObj = wp.Planes.CreatePlane(
            new Point3d(0, 0, 0), new Vector3d(1, 0, 0), SmartObject.UpdateOption.WithinModeling);
      }
      mb.PlaneConstructor = mirrorPlaneObj;

      Feature f = mb.CommitFeature();
      mb.Destroy();
      _lastFeature = f;
      Console.WriteLine("[OK] MirrorFeature: plane={0}", plane);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] MirrorFeature failed: {0}", ex.Message);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 曲面建模
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_ThroughCurves(string[] sections)
  {
    // TODO: 通过曲线组（需要 NXOpen ThroughCurvesBuilder API）
    Console.WriteLine("[TODO] Tool_ThroughCurves: {0} sections", sections.Length);
  }

  public void Tool_ThroughCurveMesh(string[] primary, string[] cross)
  {
    // TODO: 通过曲线网格（需要 NXOpen ThroughCurveMeshBuilder API）
    Console.WriteLine("[TODO] Tool_ThroughCurveMesh: primary={0}, cross={1}", primary.Length, cross.Length);
  }

  public void Tool_Ruled(string curve1, string curve2)
  {
    // TODO: 直纹面（需要 NXOpen RuledBuilder API）
    Console.WriteLine("[TODO] Tool_Ruled: {0} → {1}", curve1, curve2);
  }

  public void Tool_BoundedPlane(string[] boundaryCurves)
  {
    // TODO: 有界平面（需要 NXOpen BoundedPlaneBuilder API）
    Console.WriteLine("[TODO] Tool_BoundedPlane: {0} curves", boundaryCurves.Length);
  }

  public void Tool_FillSurface(string[] boundaryCurves)
  {
    // TODO: 填充曲面（需要 NXOpen FillSurfaceBuilder API）
    Console.WriteLine("[TODO] Tool_FillSurface: {0} curves", boundaryCurves.Length);
  }

  public void Tool_OffsetSurface(string faceRef, double distance)
  {
    // TODO: 偏置曲面（需要 NXOpen OffsetSurfaceBuilder API）
    Console.WriteLine("[TODO] Tool_OffsetSurface: {0}, dist={1}", faceRef, distance);
  }

  public void Tool_Extension(string faceRef, string edgeRef, double length)
  {
    // TODO: 延伸曲面（需要 NXOpen ExtensionBuilder API）
    Console.WriteLine("[TODO] Tool_Extension: face={0}, edge={1}, len={2}", faceRef, edgeRef, length);
  }

  public void Tool_TrimSurface(string faceRef, string[] boundaryCurves)
  {
    // TODO: 修剪曲面（需要 NXOpen TrimSurfaceBuilder API）
    Console.WriteLine("[TODO] Tool_TrimSurface: {0}, {1} boundaries", faceRef, boundaryCurves.Length);
  }

  public void Tool_FaceBlend(string face1, string face2, double radius)
  {
    // TODO: 面圆角（需要 NXOpen FaceBlendBuilder API）
    Console.WriteLine("[TODO] Tool_FaceBlend: {0} ↔ {1}, r={2}", face1, face2, radius);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 同步建模
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_MoveFace(int[] faceIndices, double distance, string direction)
  {
    // TODO: 移动面（需要 NXOpen MoveFaceBuilder API）
    Console.WriteLine("[TODO] Tool_MoveFace: faces=[{0}], dist={1}, dir={2}", string.Join(",", faceIndices), distance, direction);
  }

  public void Tool_DeleteFace(int[] faceIndices)
  {
    // TODO: 删除面（需要 NXOpen DeleteFaceBuilder API）
    Console.WriteLine("[TODO] Tool_DeleteFace: faces=[{0}]", string.Join(",", faceIndices));
  }

  public void Tool_ReplaceFace(int[] targetFaces, int[] toolFaces)
  {
    // TODO: 替换面（需要 NXOpen ReplaceFaceBuilder API）
    Console.WriteLine("[TODO] Tool_ReplaceFace: target=[{0}], tool=[{1}]", string.Join(",", targetFaces), string.Join(",", toolFaces));
  }

  public void Tool_ResizeFace(int[] faceIndices, double newRadius)
  {
    // TODO: 调整面大小（需要 NXOpen ResizeFaceBuilder API）
    Console.WriteLine("[TODO] Tool_ResizeFace: faces=[{0}], r={1}", string.Join(",", faceIndices), newRadius);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 变换操作
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_Translate(double dx, double dy, double dz)
  {
    if (curBody == null)
    {
      Console.WriteLine("[!] Translate: no curBody");
      return;
    }
    try
    {
      MoveObjectBuilder mb = wp.BaseFeatures.CreateMoveObjectBuilder(null);
      mb.ObjectToMoveObject.Add(curBody);
      mb.TransformMotion.Option = ModlMotion.Options.DistanceAngle;
      mb.TransformMotion.DistanceValue.RightHandSide =
          Math.Sqrt(dx*dx + dy*dy + dz*dz).ToString();
      mb.TransformMotion.DistanceVector = wp.Directions.CreateDirection(
          new Point3d(0, 0, 0), new Vector3d(dx, dy, dz),
          SmartObject.UpdateOption.WithinModeling);

      NXObject obj = mb.Commit();
      mb.Destroy();
      Console.WriteLine("[OK] Translate: dx={0}, dy={1}, dz={2}", dx, dy, dz);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] Translate failed: {0}", ex.Message);
    }
  }

  public void Tool_Rotate(double angle, string axis)
  {
    if (curBody == null)
    {
      Console.WriteLine("[!] Rotate: no curBody");
      return;
    }
    try
    {
      MoveObjectBuilder mb = wp.BaseFeatures.CreateMoveObjectBuilder(null);
      mb.ObjectToMoveObject.Add(curBody);
      mb.TransformMotion.Option = ModlMotion.Options.Angle;
      mb.TransformMotion.Angle.RightHandSide = angle.ToString();

      string ax = (axis ?? "Z").ToUpper();
      Vector3d vec;
      if (ax == "X") vec = new Vector3d(1, 0, 0);
      else if (ax == "Y") vec = new Vector3d(0, 1, 0);
      else vec = new Vector3d(0, 0, 1);

      mb.TransformMotion.RotateVector = wp.Axes.CreateAxis(
          new Point3d(0, 0, 0), vec, SmartObject.UpdateOption.WithinModeling);

      NXObject obj = mb.Commit();
      mb.Destroy();
      Console.WriteLine("[OK] Rotate: angle={0}, axis={1}", angle, ax);
    }
    catch (Exception ex)
    {
      Console.WriteLine("[!] Rotate failed: {0}", ex.Message);
    }
  }

  public void Tool_Scale(double factor)
  {
    // TODO: 缩放（需要 NXOpen ScaleBodyBuilder API）
    Console.WriteLine("[TODO] Tool_Scale: factor={0}", factor);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // 测量与查询
  // ═══════════════════════════════════════════════════════════════════════

  public void Tool_MeasureDistance(double x1, double y1, double z1, double x2, double y2, double z2)
  {
    // TODO: 测量距离（需要 NXOpen Measure API）
    double dx = x2 - x1, dy = y2 - y1, dz = z2 - z1;
    double dist = Math.Sqrt(dx * dx + dy * dy + dz * dz);
    Console.WriteLine("[Measure] Distance: {0:F3} mm", dist);
  }

  public void Tool_MeasureVolume()
  {
    // TODO: 测量体积（需要 NXOpen MeasureBody API）
    Console.WriteLine("[TODO] Tool_MeasureVolume: body={0}", curBody);
  }

  public void Tool_MeasureMass()
  {
    // TODO: 测量质量（需要 NXOpen MeasureBody API）
    Console.WriteLine("[TODO] Tool_MeasureMass: body={0}", curBody);
  }
}