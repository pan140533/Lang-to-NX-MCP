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
    if (f.GetBodies().Length > 0) curBody = f.GetBodies()[0];
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
    try { NXObject[] objs = fr.GetEntities(); if (objs != null) foreach (NXObject o in objs) { Body b = o as Body; if (b != null) { curBody = b; break; } } } catch { }
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
    var fb = wp.Features.CreateEdgeBlendBuilder(null);
    var coll = wp.ScCollectors.CreateCollector();
    coll.ReplaceRules(new SelectionIntentRule[]{wp.ScRuleFactory.CreateRuleEdgeDumb(curBody.GetEdges())}, false);
    fb.CommitFeature(); fb.Destroy();
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
}
