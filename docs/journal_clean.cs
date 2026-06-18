// NX 2412
// Journal created by 140533 on Tue Jun 16 18:50:19 2026 -NVhQe

//
using System;
using NXOpen;

public class NXJournal
{
  public static void Main(string[] args)
  {
    NXOpen.Session theSession = NXOpen.Session.GetSession();
    // ----------------------------------------------
    //   USeN(F)->e^(N)...
    // ----------------------------------------------
    NXOpen.Session.UndoMarkId markId1;
    markId1 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "_Y");
    
    NXOpen.FileNew fileNew1;
    fileNew1 = theSession.Parts.FileNew();
    
    theSession.SetUndoMarkName(markId1, "e^ [Fh");
    
    NXOpen.Session.UndoMarkId markId2;
    markId2 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "e^");
    
    theSession.DeleteUndoMark(markId2, null);
    
    NXOpen.Session.UndoMarkId markId3;
    markId3 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "e^");
    
    fileNew1.TemplateFileName = "model-plain-1-mm-template.prt";
    
    fileNew1.UseBlankTemplate = false;
    
    fileNew1.ApplicationName = "ModelTemplate";
    
    fileNew1.Units = NXOpen.Part.Units.Millimeters;
    
    fileNew1.RelationType = "";
    
    fileNew1.UsesMasterModel = "No";
    
    fileNew1.TemplateType = NXOpen.FileNewTemplateType.Item;
    
    fileNew1.TemplatePresentationName = "!jW";
    
    fileNew1.ItemType = "";
    
    fileNew1.Specialization = "";
    
    fileNew1.SetCanCreateAltrep(false);
    
    fileNew1.NewFileName = "E:\\NX\\NX\\model1.prt";
    
    fileNew1.MasterFileName = "";
    
    fileNew1.MakeDisplayedPart = true;
    
    fileNew1.DisplayPartOption = NXOpen.DisplayPartOption.AllowAdditional;
    
    NXOpen.NXObject nXObject1;
    nXObject1 = fileNew1.Commit();
    
    NXOpen.Part workPart = theSession.Parts.Work;
    NXOpen.Part displayPart = theSession.Parts.Display;
    theSession.DeleteUndoMark(markId3, null);
    
    fileNew1.Destroy();
    
    theSession.ApplicationSwitchImmediate("UG_APP_MODELING");
    
    // ----------------------------------------------
    //   USceQ(S)->WQ(D)->WQs^b(D)...
    // ----------------------------------------------
    NXOpen.Session.UndoMarkId markId4;
    markId4 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "_Y");
    
    NXOpen.Features.Feature nullNXOpen_Features_Feature = null;
    NXOpen.Features.DatumPlaneBuilder datumPlaneBuilder1;
    datumPlaneBuilder1 = workPart.Features.CreateDatumPlaneBuilder(nullNXOpen_Features_Feature);
    
    NXOpen.Plane plane1;
    plane1 = datumPlaneBuilder1.GetPlane();
    
    NXOpen.Unit unit1 = ((NXOpen.Unit)workPart.UnitCollection.FindObject("MilliMeter"));
    NXOpen.Expression expression1;
    expression1 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    NXOpen.Expression expression2;
    expression2 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    NXOpen.Point3d coordinates1 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point1;
    point1 = workPart.Points.CreatePoint(coordinates1);
    
    theSession.SetUndoMarkName(markId4, "WQs^b [Fh");
    
    plane1.SetUpdateOption(NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    plane1.SetMethod(NXOpen.PlaneTypes.MethodType.Distance);
    
    NXOpen.NXObject[] geom1 = new NXOpen.NXObject[1];
    NXOpen.DatumPlane datumPlane1 = ((NXOpen.DatumPlane)workPart.Datums.FindObject("DATUM_CSYS(0) XY plane"));
    geom1[0] = datumPlane1;
    plane1.SetGeometry(geom1);
    
    plane1.SetFlip(false);
    
    plane1.SetReverseSide(false);
    
    NXOpen.Expression expression3;
    expression3 = plane1.Expression;
    
    expression3.RightHandSide = "0";
    
    plane1.SetAlternate(NXOpen.PlaneTypes.AlternateType.One);
    
    plane1.Evaluate();
    
    plane1.SetMethod(NXOpen.PlaneTypes.MethodType.Distance);
    
    NXOpen.NXObject[] geom2 = new NXOpen.NXObject[1];
    geom2[0] = datumPlane1;
    plane1.SetGeometry(geom2);
    
    plane1.SetFlip(false);
    
    plane1.SetReverseSide(false);
    
    NXOpen.Expression expression4;
    expression4 = plane1.Expression;
    
    expression4.RightHandSide = "0";
    
    plane1.SetAlternate(NXOpen.PlaneTypes.AlternateType.One);
    
    plane1.Evaluate();
    
    NXOpen.Point3d coordinates2 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point2;
    point2 = workPart.Points.CreatePoint(coordinates2);
    
    workPart.Points.DeletePoint(point1);
    
    NXOpen.Point3d coordinates3 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point3;
    point3 = workPart.Points.CreatePoint(coordinates3);
    
    workPart.Points.DeletePoint(point2);
    
    NXOpen.Point3d coordinates4 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point4;
    point4 = workPart.Points.CreatePoint(coordinates4);
    
    workPart.Points.DeletePoint(point3);
    
    NXOpen.Point3d coordinates5 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point5;
    point5 = workPart.Points.CreatePoint(coordinates5);
    
    workPart.Points.DeletePoint(point4);
    
    NXOpen.Session.UndoMarkId markId5;
    markId5 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "WQs^b");
    
    theSession.DeleteUndoMark(markId5, null);
    
    NXOpen.Session.UndoMarkId markId6;
    markId6 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "WQs^b");
    
    plane1.RemoveOffsetData();
    
    plane1.Evaluate();
    
    NXOpen.Point3d corner1_1 = new NXOpen.Point3d(58.998282387935078, 58.998282387935078, 0.0);
    NXOpen.Point3d corner2_1 = new NXOpen.Point3d(-58.998282387935078, 58.998282387935078, 0.0);
    NXOpen.Point3d corner3_1 = new NXOpen.Point3d(-58.998282387935078, -58.998282387935078, 0.0);
    NXOpen.Point3d corner4_1 = new NXOpen.Point3d(58.998282387935078, -58.998282387935078, 0.0);
    datumPlaneBuilder1.SetCornerPoints(corner1_1, corner2_1, corner3_1, corner4_1);
    
    datumPlaneBuilder1.ResizeDuringUpdate = true;
    
    NXOpen.Features.Feature feature1;
    feature1 = datumPlaneBuilder1.CommitFeature();
    
    NXOpen.Features.DatumPlaneFeature datumPlaneFeature1 = ((NXOpen.Features.DatumPlaneFeature)feature1);
    NXOpen.DatumPlane datumPlane2;
    datumPlane2 = datumPlaneFeature1.DatumPlane;
    
    datumPlane2.SetReverseSection(false);
    
    theSession.DeleteUndoMark(markId6, null);
    
    theSession.SetUndoMarkName(markId4, "WQs^b");
    
    datumPlaneBuilder1.Destroy();
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression2);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression1);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    // ----------------------------------------------
    //   USceQ(S)->IV(S)
    // ----------------------------------------------
    NXOpen.Session.UndoMarkId markId7;
    markId7 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Enter Sketch");
    
    NXOpen.Session.UndoMarkId markId8;
    markId8 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Update Model from Sketch");
    
    theSession.BeginTaskEnvironment();
    
    NXOpen.Session.UndoMarkId markId9;
    markId9 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "_Y");
    
    NXOpen.Sketch nullNXOpen_Sketch = null;
    NXOpen.SketchInPlaceBuilder sketchInPlaceBuilder1;
    sketchInPlaceBuilder1 = workPart.Sketches.CreateSketchInPlaceBuilder2(nullNXOpen_Sketch);
    
    NXOpen.Point3d origin1 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Vector3d normal1 = new NXOpen.Vector3d(0.0, 0.0, 1.0);
    NXOpen.Plane plane2;
    plane2 = workPart.Planes.CreatePlane(origin1, normal1, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    sketchInPlaceBuilder1.PlaneReference = plane2;
    
    NXOpen.Expression expression5;
    expression5 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    NXOpen.Expression expression6;
    expression6 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    NXOpen.SketchAlongPathBuilder sketchAlongPathBuilder1;
    sketchAlongPathBuilder1 = workPart.Sketches.CreateSketchAlongPathBuilder(nullNXOpen_Sketch);
    
    NXOpen.SimpleSketchInPlaceBuilder simpleSketchInPlaceBuilder1;
    simpleSketchInPlaceBuilder1 = workPart.Sketches.CreateSimpleSketchInPlaceBuilder();
    
    theSession.SetUndoMarkName(markId9, "R^IV [Fh");
    
    simpleSketchInPlaceBuilder1.UseWorkPartOrigin = false;
    
    NXOpen.Point3d coordinates6 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point6;
    point6 = workPart.Points.CreatePoint(coordinates6);
    
    NXOpen.Point3d origin2 = new NXOpen.Point3d(75.909806488951418, 75.909806488951418, 0.0);
    NXOpen.Matrix3x3 matrix1 = new NXOpen.Matrix3x3();
    matrix1.Xx = 1.0;
    matrix1.Xy = 0.0;
    matrix1.Xz = 0.0;
    matrix1.Yx = 0.0;
    matrix1.Yy = 1.0;
    matrix1.Yz = 0.0;
    matrix1.Zx = 0.0;
    matrix1.Zy = 0.0;
    matrix1.Zz = 1.0;
    NXOpen.Plane plane3;
    plane3 = workPart.Planes.CreateFixedTypePlane(origin2, matrix1, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    NXOpen.Point3d coordinates7 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point7;
    point7 = workPart.Points.CreatePoint(coordinates7);
    
    NXOpen.Point3d origin3 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Vector3d vector1 = new NXOpen.Vector3d(0.0, 0.0, 1.0);
    NXOpen.Direction direction1;
    direction1 = workPart.Directions.CreateDirection(origin3, vector1, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    NXOpen.Point3d origin4 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Vector3d vector2 = new NXOpen.Vector3d(1.0, 0.0, 0.0);
    NXOpen.Direction direction2;
    direction2 = workPart.Directions.CreateDirection(origin4, vector2, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    NXOpen.Point3d origin5 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Matrix3x3 matrix2 = new NXOpen.Matrix3x3();
    matrix2.Xx = 1.0;
    matrix2.Xy = 0.0;
    matrix2.Xz = 0.0;
    matrix2.Yx = 0.0;
    matrix2.Yy = 1.0;
    matrix2.Yz = 0.0;
    matrix2.Zx = 0.0;
    matrix2.Zy = 0.0;
    matrix2.Zz = 1.0;
    NXOpen.Plane plane4;
    plane4 = workPart.Planes.CreateFixedTypePlane(origin5, matrix2, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    NXOpen.Xform xform1;
    xform1 = workPart.Xforms.CreateXformByPlaneXDirPoint(plane4, direction2, point7, NXOpen.SmartObject.UpdateOption.WithinModeling, 0.625, false, false);
    
    NXOpen.CartesianCoordinateSystem cartesianCoordinateSystem1;
    cartesianCoordinateSystem1 = workPart.CoordinateSystems.CreateCoordinateSystem(xform1, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    simpleSketchInPlaceBuilder1.CoordinateSystem = cartesianCoordinateSystem1;
    
    NXOpen.Point point8;
    point8 = simpleSketchInPlaceBuilder1.SketchOrigin;
    
    simpleSketchInPlaceBuilder1.SketchOrigin = point8;
    
    NXOpen.Session.UndoMarkId markId10;
    markId10 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "R^IV");
    
    theSession.DeleteUndoMark(markId10, null);
    
    NXOpen.Session.UndoMarkId markId11;
    markId11 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "R^IV");
    
    theSession.Preferences.Sketch.CreateInferredConstraints = false;
    
    theSession.Preferences.Sketch.ContinuousAutoDimensioning = false;
    
    theSession.Preferences.Sketch.DimensionLabel = NXOpen.Preferences.SketchPreferences.DimensionLabelType.Expression;
    
    theSession.Preferences.Sketch.TextSizeFixed = false;
    
    theSession.Preferences.Sketch.FixedTextSize = 3.0;
    
    theSession.Preferences.Sketch.DisplayParenthesesOnReferenceDimensions = true;
    
    theSession.Preferences.Sketch.DisplayReferenceGeometry = false;
    
    theSession.Preferences.Sketch.DisplayShadedRegions = true;
    
    theSession.Preferences.Sketch.FindMovableObjects = true;
    
    theSession.Preferences.Sketch.ConstraintSymbolSize = 3.0;
    
    theSession.Preferences.Sketch.DisplayObjectColor = false;
    
    theSession.Preferences.Sketch.DisplayObjectName = true;
    
    theSession.Preferences.Sketch.EditDimensionOnCreation = true;
    
    theSession.Preferences.Sketch.CreateDimensionForTypedValues = true;
    
    theSession.Preferences.Sketch.AddRemoteFindingAfterSnap = true;
    
    NXOpen.NXObject nXObject2;
    nXObject2 = simpleSketchInPlaceBuilder1.Commit();
    
    NXOpen.Sketch sketch1 = ((NXOpen.Sketch)nXObject2);
    NXOpen.Features.Feature feature2;
    feature2 = sketch1.Feature;
    
    NXOpen.Session.UndoMarkId markId12;
    markId12 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "update");
    
    int nErrs1;
    nErrs1 = theSession.UpdateManager.DoUpdate(markId12);
    
    sketch1.Activate(NXOpen.Sketch.ViewReorient.True);
    
    theSession.Preferences.Sketch.FindMovableObjects = true;
    
    NXOpen.SketchFindMovableObjectsBuilder sketchFindMovableObjectsBuilder1;
    sketchFindMovableObjectsBuilder1 = workPart.Sketches.CreateFindMovableObjectsBuilder();
    
    NXOpen.NXObject nXObject3;
    nXObject3 = sketchFindMovableObjectsBuilder1.Commit();
    
    sketchFindMovableObjectsBuilder1.Destroy();
    
    workPart.ModelingViews.WorkView.SetScale(0.22602352916509574);
    
    theSession.DeleteUndoMark(markId11, null);
    
    theSession.SetUndoMarkName(markId9, "R^IV");
    
    sketchInPlaceBuilder1.Destroy();
    
    sketchAlongPathBuilder1.Destroy();
    
    simpleSketchInPlaceBuilder1.Destroy();
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression6);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression5);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    plane2.DestroyPlane();
    
    theSession.DeleteUndoMarksUpToMark(markId8, null, true);
    
    NXOpen.Session.UndoMarkId markId13;
    markId13 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "Open Sketch");
    
    theSession.ActiveSketch.SetName("SKETCH_000");
    
    // ----------------------------------------------
    //   USceQ(S)->f~(C)->W(C)...
    // ----------------------------------------------
    NXOpen.Session.UndoMarkId markId14;
    markId14 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Profile short list");
    
    NXOpen.Session.UndoMarkId markId15;
    markId15 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Curve");
    
    theSession.SetUndoMarkVisibility(markId15, "Curve", NXOpen.Session.MarkVisibility.Visible);
    
    NXOpen.NXMatrix nXMatrix1;
    nXMatrix1 = theSession.ActiveSketch.Orientation;
    
    NXOpen.Point3d center1 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Arc arc1;
    arc1 = workPart.Curves.CreateArc(center1, nXMatrix1, 251.48173462530372, 0.0, ( 360.0 * Math.PI/180.0 ));
    
    theSession.ActiveSketch.AddGeometry(arc1, NXOpen.Sketch.InferConstraintsOption.InferNoConstraints);
    
    theSession.ActiveSketch.Update();
    
    theSession.ActiveSketch.UpdateNavigator();
    
    // ----------------------------------------------
    //   [_Y W
    // ----------------------------------------------
    // ----------------------------------------------
    //   USNR(K)->[bIV(K)
    // ----------------------------------------------
    NXOpen.SketchFindMovableObjectsBuilder sketchFindMovableObjectsBuilder2;
    sketchFindMovableObjectsBuilder2 = workPart.Sketches.CreateFindMovableObjectsBuilder();
    
    NXOpen.NXObject nXObject4;
    nXObject4 = sketchFindMovableObjectsBuilder2.Commit();
    
    sketchFindMovableObjectsBuilder2.Destroy();
    
    NXOpen.SketchFindIssuesBuilder sketchFindIssuesBuilder1;
    sketchFindIssuesBuilder1 = workPart.Sketches.CreateFindIssuesBuilder();
    
    sketchFindIssuesBuilder1.ZoomScale = 0.22602352916509574;
    
    NXOpen.NXObject nXObject5;
    nXObject5 = sketchFindIssuesBuilder1.Commit();
    
    sketchFindIssuesBuilder1.Destroy();
    
    theSession.ActiveSketch.CalculateStatus();
    
    theSession.Preferences.Sketch.SectionView = false;
    
    NXOpen.Session.UndoMarkId markId16;
    markId16 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "Deactivate Sketch");
    
    theSession.ActiveSketch.Deactivate(NXOpen.Sketch.ViewReorient.True, NXOpen.Sketch.UpdateLevel.Model);
    
    theSession.DeleteUndoMarksSetInTaskEnvironment();
    
    theSession.EndTaskEnvironment();
    
    // ----------------------------------------------
    //   USceQ(S)->yr_(E)->b8O(X)...
    // ----------------------------------------------
    NXOpen.Session.UndoMarkId markId17;
    markId17 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Visible, "_Y");
    
    NXOpen.Features.ExtrudeBuilder extrudeBuilder1;
    extrudeBuilder1 = workPart.Features.CreateExtrudeBuilder(nullNXOpen_Features_Feature);
    
    NXOpen.Section section1;
    section1 = workPart.Sections.CreateSection(0.0094999999999999998, 0.01, 0.5);
    
    extrudeBuilder1.Section = section1;
    
    extrudeBuilder1.AllowSelfIntersectingSection(true);
    
    NXOpen.Unit unit2;
    unit2 = extrudeBuilder1.Draft.FrontDraftAngle.Units;
    
    NXOpen.Expression expression7;
    expression7 = workPart.Expressions.CreateSystemExpressionWithUnits("2.00", unit2);
    
    extrudeBuilder1.DistanceTolerance = 0.01;
    
    NXOpen.Body[] targetBodies1 = new NXOpen.Body[1];
    NXOpen.Body nullNXOpen_Body = null;
    targetBodies1[0] = nullNXOpen_Body;
    extrudeBuilder1.BooleanOperation.SetTargetBodies(targetBodies1);
    
    extrudeBuilder1.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create;
    
    extrudeBuilder1.Limits.StartExtend.Value.SetFormula("0");
    
    extrudeBuilder1.Limits.EndExtend.Value.SetFormula("25");
    
    extrudeBuilder1.Offset.StartOffset.SetFormula("0");
    
    extrudeBuilder1.Offset.EndOffset.SetFormula("5");
    
    NXOpen.GeometricUtilities.SmartVolumeProfileBuilder smartVolumeProfileBuilder1;
    smartVolumeProfileBuilder1 = extrudeBuilder1.SmartVolumeProfile;
    
    smartVolumeProfileBuilder1.OpenProfileSmartVolumeOption = false;
    
    smartVolumeProfileBuilder1.CloseProfileRule = NXOpen.GeometricUtilities.SmartVolumeProfileBuilder.CloseProfileRuleType.Fci;
    
    theSession.SetUndoMarkName(markId17, "b8O [Fh");
    
    section1.DistanceTolerance = 0.01;
    
    section1.ChainingTolerance = 0.0094999999999999998;
    
    section1.SetAllowedEntityTypes(NXOpen.Section.AllowTypes.OnlyCurves);
    
    NXOpen.Session.UndoMarkId markId18;
    markId18 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, null);
    
    NXOpen.SelectionIntentRuleOptions selectionIntentRuleOptions1;
    selectionIntentRuleOptions1 = workPart.ScRuleFactory.CreateRuleOptions();
    
    selectionIntentRuleOptions1.SetSelectedFromInactive(false);
    
    NXOpen.ICurve[] curves1 = new NXOpen.ICurve[1];
    curves1[0] = arc1;
    NXOpen.Point3d seedPoint1 = new NXOpen.Point3d(-33.120579458640272, -16.503410398209571, 0.0);
    NXOpen.RegionBoundaryRule regionBoundaryRule1;
    regionBoundaryRule1 = workPart.ScRuleFactory.CreateRuleRegionBoundary(sketch1, curves1, seedPoint1, 0.01, selectionIntentRuleOptions1);
    
    selectionIntentRuleOptions1.Dispose();
    section1.AllowSelfIntersection(true);
    
    section1.AllowDegenerateCurves(false);
    
    NXOpen.SelectionIntentRule[] rules1 = new NXOpen.SelectionIntentRule[1];
    rules1[0] = regionBoundaryRule1;
    NXOpen.NXObject nullNXOpen_NXObject = null;
    NXOpen.Point3d helpPoint1 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    section1.AddToSection(rules1, nullNXOpen_NXObject, nullNXOpen_NXObject, nullNXOpen_NXObject, helpPoint1, NXOpen.Section.Mode.Create, false);
    
    theSession.DeleteUndoMark(markId18, null);
    
    NXOpen.Session.UndoMarkId markId19;
    markId19 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "section mark");
    
    NXOpen.Session.UndoMarkId markId20;
    markId20 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, null);
    
    theSession.DeleteUndoMark(markId20, null);
    
    NXOpen.Direction direction3;
    direction3 = workPart.Directions.CreateDirection(sketch1, NXOpen.Sense.Forward, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    extrudeBuilder1.Direction = direction3;
    
    NXOpen.Body[] targetBodies2 = new NXOpen.Body[1];
    targetBodies2[0] = nullNXOpen_Body;
    extrudeBuilder1.BooleanOperation.SetTargetBodies(targetBodies2);
    
    extrudeBuilder1.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create;
    
    NXOpen.Body[] targetBodies3 = new NXOpen.Body[0];
    extrudeBuilder1.BooleanOperation.SetTargetBodies(targetBodies3);
    
    theSession.DeleteUndoMark(markId19, null);
    
    NXOpen.Body[] targetBodies4 = new NXOpen.Body[1];
    targetBodies4[0] = nullNXOpen_Body;
    extrudeBuilder1.BooleanOperation.SetTargetBodies(targetBodies4);
    
    extrudeBuilder1.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create;
    
    NXOpen.Body[] targetBodies5 = new NXOpen.Body[0];
    extrudeBuilder1.BooleanOperation.SetTargetBodies(targetBodies5);
    
    extrudeBuilder1.Limits.EndExtend.Value.SetFormula("250");
    
    NXOpen.Body[] targetBodies6 = new NXOpen.Body[1];
    targetBodies6[0] = nullNXOpen_Body;
    extrudeBuilder1.BooleanOperation.SetTargetBodies(targetBodies6);
    
    extrudeBuilder1.BooleanOperation.Type = NXOpen.GeometricUtilities.BooleanOperation.BooleanType.Create;
    
    NXOpen.Body[] targetBodies7 = new NXOpen.Body[0];
    extrudeBuilder1.BooleanOperation.SetTargetBodies(targetBodies7);
    
    NXOpen.Session.UndoMarkId markId21;
    markId21 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "b8O");
    
    theSession.DeleteUndoMark(markId21, null);
    
    NXOpen.Session.UndoMarkId markId22;
    markId22 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "b8O");
    
    extrudeBuilder1.ParentFeatureInternal = false;
    
    NXOpen.Features.Feature feature3;
    feature3 = extrudeBuilder1.CommitFeature();
    
    theSession.DeleteUndoMark(markId22, null);
    
    theSession.SetUndoMarkName(markId17, "b8O");
    
    NXOpen.Expression expression8 = extrudeBuilder1.Limits.StartExtend.Value;
    NXOpen.Expression expression9 = extrudeBuilder1.Limits.EndExtend.Value;
    extrudeBuilder1.Destroy();
    
    workPart.Expressions.Delete(expression7);
    
    // ----------------------------------------------
    //   US]wQ(T)->RS(A)->[(R)->_YU_6R(R)...
    // ----------------------------------------------
    NXOpen.MeasurePrefsBuilder measurePrefsBuilder1;
    measurePrefsBuilder1 = theSession.Preferences.CreateMeasurePrefsBuilder();
    
    bool combineddisplay1;
    combineddisplay1 = measurePrefsBuilder1.CombinedDisplay;
    
    int decimalplaces1;
    decimalplaces1 = measurePrefsBuilder1.DecimalPlaces;
    
    bool flag1;
    flag1 = measurePrefsBuilder1.AllowReselectionOfObjects;
    
    int eulertype1;
    eulertype1 = measurePrefsBuilder1.EulerType;
    
    int boundingboxmethod1;
    boundingboxmethod1 = measurePrefsBuilder1.BoundingBoxMethod;
    
    int alternativemeasurementsmethod1;
    alternativemeasurementsmethod1 = measurePrefsBuilder1.AlternativeMeasurementsMethod;
    
    NXOpen.MeasurePrefsBuilder.JaMeasurePrefsSectionType sectioninertiatype1;
    sectioninertiatype1 = measurePrefsBuilder1.SectionInertiaType;
    
    double faceaccuracy1;
    faceaccuracy1 = measurePrefsBuilder1.FaceAccuracy;
    
    double bodyaccuracy1;
    bodyaccuracy1 = measurePrefsBuilder1.BodyAccuracy;
    
    bool deltaxyz1;
    deltaxyz1 = measurePrefsBuilder1.DeltaXyz;
    
    bool displaydistancestartpoint1;
    displaydistancestartpoint1 = measurePrefsBuilder1.DisplayDistanceStartPoint;
    
    bool displaydistanceendpoint1;
    displaydistanceendpoint1 = measurePrefsBuilder1.DisplayDistanceEndPoint;
    
    bool displaycurvelength1;
    displaycurvelength1 = measurePrefsBuilder1.DisplayCurveLength;
    
    bool displaycurveradius1;
    displaycurveradius1 = measurePrefsBuilder1.DisplayCurveRadius;
    
    bool displaycurvediameter1;
    displaycurvediameter1 = measurePrefsBuilder1.DisplayCurveDiameter;
    
    bool displaycurvestart1;
    displaycurvestart1 = measurePrefsBuilder1.DisplayCurveStart;
    
    bool displaycurveend1;
    displaycurveend1 = measurePrefsBuilder1.DisplayCurveEnd;
    
    bool displaycurvecenter1;
    displaycurvecenter1 = measurePrefsBuilder1.DisplayCurveCenter;
    
    bool displaycurveminradius1;
    displaycurveminradius1 = measurePrefsBuilder1.DisplayCurveMinRadius;
    
    int unitssystem1;
    unitssystem1 = measurePrefsBuilder1.UnitsSystem;
    
    int angleunits1;
    angleunits1 = measurePrefsBuilder1.AngleUnits;
    
    bool disableunits1;
    disableunits1 = measurePrefsBuilder1.DisableUnits;
    
    bool disableunits2;
    disableunits2 = measurePrefsBuilder1.DisableUnits;
    
    int errorcolor1;
    errorcolor1 = measurePrefsBuilder1.ErrorColor;
    
    int errorbgcolor1;
    errorbgcolor1 = measurePrefsBuilder1.ErrorBgColor;
    
    int warningcolor1;
    warningcolor1 = measurePrefsBuilder1.WarningColor;
    
    int warningbgcolor1;
    warningbgcolor1 = measurePrefsBuilder1.WarningBgColor;
    
    int infocolor1;
    infocolor1 = measurePrefsBuilder1.InfoColor;
    
    int infobgcolor1;
    infobgcolor1 = measurePrefsBuilder1.InfoBgColor;
    
    int linecolorfixtimestamp1;
    linecolorfixtimestamp1 = measurePrefsBuilder1.LineColorFixTimeStamp;
    
    int linecolornotfixtimestamp1;
    linecolornotfixtimestamp1 = measurePrefsBuilder1.LineColorNotFixTimeStamp;
    
    bool disableunits3;
    disableunits3 = measurePrefsBuilder1.DisableUnits;
    
    bool disableunits4;
    disableunits4 = measurePrefsBuilder1.DisableUnits;
    
    int nonassoclinecolor1;
    nonassoclinecolor1 = measurePrefsBuilder1.NonAssocLineColor;
    
    int color1;
    color1 = measurePrefsBuilder1.AnnotBackgroundColor;
    
    NXOpen.MeasurePrefsBuilder.JaMeasurePrefsAnnotBackgroundColorType type1;
    type1 = measurePrefsBuilder1.AnnotBackgroundColorType;
    
    bool disableunits5;
    disableunits5 = measurePrefsBuilder1.DisableUnits;
    
    bool disableunits6;
    disableunits6 = measurePrefsBuilder1.DisableUnits;
    
    bool displayparalleltoscreen1;
    displayparalleltoscreen1 = measurePrefsBuilder1.DisplayParallelToScreen;
    
    bool disableunits7;
    disableunits7 = measurePrefsBuilder1.DisableUnits;
    
    bool createpointexp1;
    createpointexp1 = measurePrefsBuilder1.CreatePointExp;
    
    bool displaypoints1;
    displaypoints1 = measurePrefsBuilder1.DisplayPoints;
    
    bool displaypointsoncurvelength1;
    displaypointsoncurvelength1 = measurePrefsBuilder1.DisplayPointsOnCurveLength;
    
    bool displayminimudistance1;
    displayminimudistance1 = measurePrefsBuilder1.DisplayMinimuDistance;
    
    bool displaymaximumdistance1;
    displaymaximumdistance1 = measurePrefsBuilder1.DisplayMaximumDistance;
    
    bool displaymaximumcentertoedge1;
    displaymaximumcentertoedge1 = measurePrefsBuilder1.DisplayMaximumCenterToEdge;
    
    bool displaymaximumedgetocenter1;
    displaymaximumedgetocenter1 = measurePrefsBuilder1.DisplayMaximumEdgeToCenter;
    
    bool displaycentertocenter1;
    displaycentertocenter1 = measurePrefsBuilder1.DisplayCenterToCenter;
    
    bool displayminimumperpendicular1;
    displayminimumperpendicular1 = measurePrefsBuilder1.DisplayMinimumPerpendicular;
    
    bool displaymaximumperpendicular1;
    displaymaximumperpendicular1 = measurePrefsBuilder1.DisplayMaximumPerpendicular;
    
    bool displayminimumdistancearcextension1;
    displayminimumdistancearcextension1 = measurePrefsBuilder1.DisplayMinimumDistanceArcExtension;
    
    bool displayminimumperpendiculararcextension1;
    displayminimumperpendiculararcextension1 = measurePrefsBuilder1.DisplayMinimumPerpendicularArcExtension;
    
    bool displayminimumprojectedclearance1;
    displayminimumprojectedclearance1 = measurePrefsBuilder1.DisplayMinimumProjectedClearance;
    
    bool displaymaximumprojectedclearance1;
    displaymaximumprojectedclearance1 = measurePrefsBuilder1.DisplayMaximumProjectedClearance;
    
    bool displayminimumprojectedcontact1;
    displayminimumprojectedcontact1 = measurePrefsBuilder1.DisplayMinimumProjectedContact;
    
    bool displaymaximumprojectedcontact1;
    displaymaximumprojectedcontact1 = measurePrefsBuilder1.DisplayMaximumProjectedContact;
    
    bool displayminimumprojectedorthogonal1;
    displayminimumprojectedorthogonal1 = measurePrefsBuilder1.DisplayMinimumProjectedOrthogonal;
    
    bool displaymaximumprojectedorthogonal1;
    displaymaximumprojectedorthogonal1 = measurePrefsBuilder1.DisplayMaximumProjectedOrthogonal;
    
    bool displaythickness1;
    displaythickness1 = measurePrefsBuilder1.DisplayThickness;
    
    bool displaydistancestartpoint2;
    displaydistancestartpoint2 = measurePrefsBuilder1.DisplayDistanceStartPoint;
    
    bool displaydistanceendpoint2;
    displaydistanceendpoint2 = measurePrefsBuilder1.DisplayDistanceEndPoint;
    
    bool displayinnerangle1;
    displayinnerangle1 = measurePrefsBuilder1.DisplayInnerAngle;
    
    bool displayouterangle1;
    displayouterangle1 = measurePrefsBuilder1.DisplayOuterAngle;
    
    bool displaysupplementaryangle1;
    displaysupplementaryangle1 = measurePrefsBuilder1.DisplaySupplementaryAngle;
    
    bool displaycomplementaryangle1;
    displaycomplementaryangle1 = measurePrefsBuilder1.DisplayComplementaryAngle;
    
    bool displayfacearea1;
    displayfacearea1 = measurePrefsBuilder1.DisplayFaceArea;
    
    bool displayfaceperimeter1;
    displayfaceperimeter1 = measurePrefsBuilder1.DisplayFacePerimeter;
    
    bool displayfaceradius1;
    displayfaceradius1 = measurePrefsBuilder1.DisplayFaceRadius;
    
    bool displayfacediameter1;
    displayfacediameter1 = measurePrefsBuilder1.DisplayFaceDiameter;
    
    bool displayfacecog1;
    displayfacecog1 = measurePrefsBuilder1.DisplayFaceCog;
    
    bool displayfaceminrad1;
    displayfaceminrad1 = measurePrefsBuilder1.DisplayFaceMinRad;
    
    bool displayfaceangle1;
    displayfaceangle1 = measurePrefsBuilder1.DisplayFaceAngle;
    
    bool displaybodyarea1;
    displaybodyarea1 = measurePrefsBuilder1.DisplayBodyArea;
    
    bool displaybodyvolume1;
    displaybodyvolume1 = measurePrefsBuilder1.DisplayBodyVolume;
    
    bool displaybodycog1;
    displaybodycog1 = measurePrefsBuilder1.DisplayBodyCog;
    
    bool displaybodymass1;
    displaybodymass1 = measurePrefsBuilder1.DisplayBodyMass;
    
    bool displaybodyweight1;
    displaybodyweight1 = measurePrefsBuilder1.DisplayBodyWeight;
    
    bool displaybodydensity1;
    displaybodydensity1 = measurePrefsBuilder1.DisplayBodyDensity;
    
    bool displaybodyfmoi1;
    displaybodyfmoi1 = measurePrefsBuilder1.DisplayBodyFmoi;
    
    bool displaybodymoiw1;
    displaybodymoiw1 = measurePrefsBuilder1.DisplayBodyMoiw;
    
    bool displaybodymoic1;
    displaybodymoic1 = measurePrefsBuilder1.DisplayBodyMoic;
    
    bool displaybodymois1;
    displaybodymois1 = measurePrefsBuilder1.DisplayBodyMois;
    
    bool displaybodypoiw1;
    displaybodypoiw1 = measurePrefsBuilder1.DisplayBodyPoiw;
    
    bool displaybodypoic1;
    displaybodypoic1 = measurePrefsBuilder1.DisplayBodyPoic;
    
    bool displaybodyrogw1;
    displaybodyrogw1 = measurePrefsBuilder1.DisplayBodyRogw;
    
    bool displaybodyrogc1;
    displaybodyrogc1 = measurePrefsBuilder1.DisplayBodyRogc;
    
    bool displaybodyrogs1;
    displaybodyrogs1 = measurePrefsBuilder1.DisplayBodyRogs;
    
    bool displaybodypaw1;
    displaybodypaw1 = measurePrefsBuilder1.DisplayBodyPaw;
    
    bool flag2;
    flag2 = measurePrefsBuilder1.DisplayInscribedCircleRadius;
    
    bool flag3;
    flag3 = measurePrefsBuilder1.DisplayInscribedCircleDiameter;
    
    bool flag4;
    flag4 = measurePrefsBuilder1.DisplayCircumscribedCircleRadius;
    
    bool flag5;
    flag5 = measurePrefsBuilder1.DisplayCircumscribedCircleDiameter;
    
    bool flag6;
    flag6 = measurePrefsBuilder1.DisplayArcCenterPointCoordinates;
    
    bool displayextremepolarradius1;
    displayextremepolarradius1 = measurePrefsBuilder1.DisplayExtremePolarRadius;
    
    bool displayextrememaxpolarradius1;
    displayextrememaxpolarradius1 = measurePrefsBuilder1.DisplayExtremeMaxPolarRadius;
    
    bool displayextremepolarangle1;
    displayextremepolarangle1 = measurePrefsBuilder1.DisplayExtremePolarAngle;
    
    bool displayextrememaxpolarangle1;
    displayextrememaxpolarangle1 = measurePrefsBuilder1.DisplayExtremeMaxPolarAngle;
    
    bool displayextremepoint1;
    displayextremepoint1 = measurePrefsBuilder1.DisplayExtremePoint;
    
    bool displayotherbbox1;
    displayotherbbox1 = measurePrefsBuilder1.DisplayOtherBbox;
    
    bool displaybboxcorner1point1;
    displaybboxcorner1point1 = measurePrefsBuilder1.DisplayBboxCorner1point;
    
    bool displaybboxcorner2point1;
    displaybboxcorner2point1 = measurePrefsBuilder1.DisplayBboxCorner2point;
    
    bool displayothercenterline1;
    displayothercenterline1 = measurePrefsBuilder1.DisplayOtherCenterline;
    
    bool displaycenterlinestartpoint1;
    displaycenterlinestartpoint1 = measurePrefsBuilder1.DisplayCenterlineStartPoint;
    
    bool displaycenterlineendpoint1;
    displaycenterlineendpoint1 = measurePrefsBuilder1.DisplayCenterlineEndPoint;
    
    bool displayothereuler1;
    displayothereuler1 = measurePrefsBuilder1.DisplayOtherEuler;
    
    bool displaysectioncentroid1;
    displaysectioncentroid1 = measurePrefsBuilder1.SectionCentroid;
    
    bool displaysectionsecondprincipalmomentsofinertia1;
    displaysectionsecondprincipalmomentsofinertia1 = measurePrefsBuilder1.SectionSecondPrincipalMomentsOfInertia;
    
    bool displaysectionlength1;
    displaysectionlength1 = measurePrefsBuilder1.SectionLength;
    
    bool displaysectionarea1;
    displaysectionarea1 = measurePrefsBuilder1.SectionArea;
    
    bool displayface2darea1;
    displayface2darea1 = measurePrefsBuilder1.DisplayFace2dArea;
    
    bool displayface2dperimeter1;
    displayface2dperimeter1 = measurePrefsBuilder1.DisplayFace2dPerimeter;
    
    bool displayfacefirstmoments1;
    displayfacefirstmoments1 = measurePrefsBuilder1.DisplayFaceFirstMoments;
    
    bool displayfacecentroid1;
    displayfacecentroid1 = measurePrefsBuilder1.DisplayFaceCentroid;
    
    bool displayfacemomentswcs1;
    displayfacemomentswcs1 = measurePrefsBuilder1.DisplayFaceMomentsWcs;
    
    bool displayfacemomentscent1;
    displayfacemomentscent1 = measurePrefsBuilder1.DisplayFaceMomentsCent;
    
    bool displayfacemomentspolar1;
    displayfacemomentspolar1 = measurePrefsBuilder1.DisplayFaceMomentsPolar;
    
    bool displayfaceproductcent1;
    displayfaceproductcent1 = measurePrefsBuilder1.DisplayFaceProductCent;
    
    bool displayfacegyrationwcs1;
    displayfacegyrationwcs1 = measurePrefsBuilder1.DisplayFaceGyrationWcs;
    
    bool displayfacegyrationcent1;
    displayfacegyrationcent1 = measurePrefsBuilder1.DisplayFaceGyrationCent;
    
    bool displayfacegyrationpolar1;
    displayfacegyrationpolar1 = measurePrefsBuilder1.DisplayFaceGyrationPolar;
    
    bool displayfaceaxeswcs1;
    displayfaceaxeswcs1 = measurePrefsBuilder1.DisplayFaceAxesWcs;
    
    bool displayfaceprincipalmomentwcs1;
    displayfaceprincipalmomentwcs1 = measurePrefsBuilder1.DisplayFacePrincipalMomentWcs;
    
    bool displayfacecirclecenter1;
    displayfacecirclecenter1 = measurePrefsBuilder1.DisplayFaceCircleCenter;
    
    bool displayfacecirclesize1;
    displayfacecirclesize1 = measurePrefsBuilder1.DisplayFaceCircleSize;
    
    int requireexactstate1;
    requireexactstate1 = measurePrefsBuilder1.RequireExactState;
    
    bool displayassociativebutton1;
    displayassociativebutton1 = measurePrefsBuilder1.DisplayAssociativeButton;
    
    bool displaycreateannotationbutton1;
    displaycreateannotationbutton1 = measurePrefsBuilder1.DisplayCreateAnnotationButton;
    
    bool displaycreategeometrybutton1;
    displaycreategeometrybutton1 = measurePrefsBuilder1.DisplayCreateGeometryButton;
    
    bool displayrequirementvalidationbutton1;
    displayrequirementvalidationbutton1 = measurePrefsBuilder1.DisplayRequirementValidationButton;
    
    bool displayproductinterfacebutton1;
    displayproductinterfacebutton1 = measurePrefsBuilder1.DisplayProductInterfaceButton;
    
    NXOpen.Weld.WeldPreferenceBuilder weldPreferenceBuilder1;
    weldPreferenceBuilder1 = workPart.Features.WeldManager.CreatePreferenceBuilder();
    
    weldPreferenceBuilder1.Destroy();
    
    NXOpen.Preferences.ViewSection viewSection1;
    viewSection1 = theSession.Preferences.CreateViewSectionPreference();
    
    viewSection1.Destroy();
    
    NXOpen.Preferences.ModelingPreferencesBuilder modelingPreferencesBuilder1;
    modelingPreferencesBuilder1 = theSession.Preferences.CreateModelingPreferencesBuilder();
    
    modelingPreferencesBuilder1.DensityUnitsValue = NXOpen.Preferences.ModelingPreferencesBuilder.DensityUnits.Kgm3;
    
    modelingPreferencesBuilder1.ModelingModeValue = NXOpen.Preferences.ModelingPreferencesBuilder.ModelingMode.History;
    
    modelingPreferencesBuilder1.FeatureDoubleClickActionValue = NXOpen.Preferences.ModelingPreferencesBuilder.FeatureDoubleClickAction.EditwithRollback;
    
    modelingPreferencesBuilder1.SketchDoubleClickActionValue = NXOpen.Preferences.ModelingPreferencesBuilder.SketchDoubleClickAction.DirectEdit;
    
    modelingPreferencesBuilder1.ModelDelayAndUpdateGranularityValue = NXOpen.Preferences.ModelingPreferencesBuilder.ModelDelayAndUpdateGranularity.Feature;
    
    modelingPreferencesBuilder1.SurfaceExtensionValue = NXOpen.Preferences.ModelingPreferencesBuilder.SurfaceExtension.Soft;
    
    modelingPreferencesBuilder1.PreviewResolutionValue = NXOpen.Preferences.ModelingPreferencesBuilder.PreviewResolution.Standard;
    
    modelingPreferencesBuilder1.PoleColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.PoleColor.SpecificColor;
    
    modelingPreferencesBuilder1.PoleStyleValue = NXOpen.Preferences.ModelingPreferencesBuilder.PoleStyle.OpenCircle;
    
    modelingPreferencesBuilder1.EditPoleColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.EditPoleColor.SpecificColor;
    
    modelingPreferencesBuilder1.PolylineColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.PolylineColor.SpecificColor;
    
    modelingPreferencesBuilder1.EditPolylineColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.EditPolylineColor.SpecificColor;
    
    modelingPreferencesBuilder1.GridLineColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.GridLineColor.SpecificColor;
    
    modelingPreferencesBuilder1.C0KnotLineColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.C0KnotLineColor.SpecificColor;
    
    modelingPreferencesBuilder1.C1KnotLineColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.C1KnotLineColor.SpecificColor;
    
    modelingPreferencesBuilder1.C2KnotLineColorValue = NXOpen.Preferences.ModelingPreferencesBuilder.C2KnotLineColor.SpecificColor;
    
    modelingPreferencesBuilder1.EndPointStyleValue = NXOpen.Preferences.ModelingPreferencesBuilder.EndPointStyle.FilledCircle;
    
    modelingPreferencesBuilder1.Destroy();
    
    NXOpen.Annotations.PmiPreferencesBuilder pmiPreferencesBuilder1;
    pmiPreferencesBuilder1 = workPart.PmiSettingsManager.CreatePreferencesBuilder();
    
    pmiPreferencesBuilder1.TableSection.ApplyToAllSections = true;
    
    pmiPreferencesBuilder1.Destroy();
    
    string studioMaterialDirectory1;
    studioMaterialDirectory1 = theSession.Preferences.AppearanceManagementPref.GetDirectoryOfStudioMaterial();
    
    bool showSeeThrough1;
    showSeeThrough1 = theSession.Preferences.AppearanceManagementPref.DispSeeThru;
    
    bool showSceneLable1;
    showSceneLable1 = theSession.Preferences.AppearanceManagementPref.DispSceneLabels;
    
    bool excludeFromSelection1;
    excludeFromSelection1 = theSession.Preferences.AppearanceManagementPref.ExcludeFromSelection;
    
    string designatorPrefix1;
    designatorPrefix1 = workPart.Preferences.AppearanceMgmtPreference.PrefixAppearanceSchemes;
    
    string designatorPrefix2;
    designatorPrefix2 = workPart.Preferences.AppearanceMgmtPreference.PrefixAppearanceDesignators;
    
    NXOpen.Display.Scene scene1;
    scene1 = workPart.Views.CreateScene(workPart.ModelingViews.WorkView, false);
    
    NXOpen.Display.Background background1;
    background1 = workPart.Views.CreateBackground(workPart.ModelingViews.WorkView, false);
    
    NXOpen.Display.Image image1;
    image1 = workPart.Views.CreateImage(workPart.ModelingViews.WorkView);
    
    NXOpen.Display.Image image2;
    image2 = workPart.Views.CreateImage(workPart.ModelingViews.WorkView);
    
    background1.Image = image1;
    
    NXOpen.Point3d coordinates8 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Point point9;
    point9 = workPart.Points.CreatePoint(coordinates8);
    
    background1.DomeOrigin = point9;
    
    background1.DomeImage = image2;
    
    background1.BackgroundShadedViewsType = 2;
    
    background1.BackgroundWireframeViewsType = 2;
    
    NXOpen.Display.Lighting lighting1;
    lighting1 = workPart.Views.CreateLighting(workPart.ModelingViews.WorkView);
    
    NXOpen.Light light1 = ((NXOpen.Light)workPart.Lights.FindObject("Scene Left Top"));
    NXOpen.Display.LightBuilder lightBuilder1;
    lightBuilder1 = workPart.Views.CreateLightBuilder(light1);
    
    lighting1.SetLightBuilderInList(0, lightBuilder1);
    
    NXOpen.Light light2 = ((NXOpen.Light)workPart.Lights.FindObject("Scene Right Top"));
    NXOpen.Display.LightBuilder lightBuilder2;
    lightBuilder2 = workPart.Views.CreateLightBuilder(light2);
    
    lighting1.SetLightBuilderInList(1, lightBuilder2);
    
    NXOpen.Light light3 = ((NXOpen.Light)workPart.Lights.FindObject("Scene Left Bottom"));
    NXOpen.Display.LightBuilder lightBuilder3;
    lightBuilder3 = workPart.Views.CreateLightBuilder(light3);
    
    lighting1.SetLightBuilderInList(2, lightBuilder3);
    
    NXOpen.Light light4 = ((NXOpen.Light)workPart.Lights.FindObject("Scene Right Bottom"));
    NXOpen.Display.LightBuilder lightBuilder4;
    lightBuilder4 = workPart.Views.CreateLightBuilder(light4);
    
    lighting1.SetLightBuilderInList(3, lightBuilder4);
    
    lighting1.LightsShadedViewsLightingCollection = NXOpen.Display.Lighting.LightingCollectionType.UserDefined;
    
    NXOpen.View.DisplayStyleType displayStyle1;
    displayStyle1 = workPart.ModelingViews.WorkView.DisplayStyle;
    
    NXOpen.Display.EnvironmentBuilder environmentBuilder1;
    environmentBuilder1 = workPart.Views.CreateEnvironmentBuilderForDisplayStyle(workPart.ModelingViews.WorkView, NXOpen.View.DisplayStyleType.Shaded, false);
    
    NXOpen.Point3d origin6 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Vector3d normal2 = new NXOpen.Vector3d(0.0, 0.0, 1.0);
    NXOpen.Plane plane5;
    plane5 = workPart.Planes.CreatePlane(origin6, normal2, NXOpen.SmartObject.UpdateOption.AfterModeling);
    
    NXOpen.Expression expression10;
    expression10 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    NXOpen.Expression expression11;
    expression11 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    NXOpen.Display.Image image3;
    image3 = workPart.Views.CreateImage(workPart.ModelingViews.WorkView);
    
    environmentBuilder1.SpecifyGroundPlane = plane5;
    
    NXOpen.Point3d origin7 = new NXOpen.Point3d(0.0, 0.0, 0.0);
    NXOpen.Vector3d normal3 = new NXOpen.Vector3d(0.0, 0.0, 1.0);
    NXOpen.Plane plane6;
    plane6 = workPart.Planes.CreatePlane(origin7, normal3, NXOpen.SmartObject.UpdateOption.WithinModeling);
    
    environmentBuilder1.EnvironmentShadedViewsGroundPlaneCustom = plane6;
    
    NXOpen.Expression expression12;
    expression12 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    NXOpen.Expression expression13;
    expression13 = workPart.Expressions.CreateSystemExpressionWithUnits("0", unit1);
    
    environmentBuilder1.Image = image3;
    
    environmentBuilder1.ViewFitToStage = true;
    
    environmentBuilder1.EnvironmentShadedViewsGroundPlane = 2;
    
    NXOpen.View.DisplayStyleType displayStyle2;
    displayStyle2 = workPart.ModelingViews.WorkView.DisplayStyle;
    
    NXOpen.Display.Shadows shadows1;
    shadows1 = workPart.Views.CreateShadowsForDisplayStyle(workPart.ModelingViews.WorkView, NXOpen.View.DisplayStyleType.Shaded);
    
    NXOpen.SelectNXObjectList selectNXObjectList1;
    selectNXObjectList1 = shadows1.ShadowCatcherSelection;
    
    selectNXObjectList1.Clear();
    
    scene1.Destroy();
    
    background1.Destroy();
    
    lighting1.Destroy();
    
    environmentBuilder1.Destroy();
    
    shadows1.Destroy();
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression11);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression13);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression10);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    plane5.DestroyPlane();
    
    try
    {
      // h_N6q(WO(u-N0
      workPart.Expressions.Delete(expression12);
    }
    catch (NXException ex)
    {
      ex.AssertErrorCode(1050029);
    }
    
    plane6.DestroyPlane();
    
    NXOpen.UI theUI = NXOpen.UI.GetUI();
    
    NXOpen.Preferences.SessionUserInterfaceUI.SpeechMode listeningModeSingle1;
    listeningModeSingle1 = theUI.UserInterfacePreferences.SpeechRecognitionMode;
    
    NXOpen.NXColor nXColor1;
    nXColor1 = workPart.Preferences.PartSketch.ShadedRegionColor;
    
    NXOpen.NXColor nXColor2;
    nXColor2 = workPart.Preferences.PartSketch.ConstantDimensionColor;
    
    NXOpen.NXColor nXColor3;
    nXColor3 = workPart.Preferences.PartSketch.RelationColor;
    
    NXOpen.NXColor nXColor4;
    nXColor4 = workPart.Preferences.PartSketch.GeometricConstraintColor;
    
    NXOpen.NXColor nXColor5;
    nXColor5 = workPart.Preferences.PartSketch.PreviewDimensionColor;
    
    NXOpen.NXColor nXColor6;
    nXColor6 = workPart.Preferences.PartSketch.LockedObjectColor;
    
    NXOpen.NXColor nXColor7;
    nXColor7 = workPart.Preferences.PartSketch.NonWorkRegionColor;
    
    NXOpen.NXColor nXColor8;
    nXColor8 = workPart.Preferences.PartSketch.WorkRegionBoundaryColor;
    
    NXOpen.NXColor nXColor9;
    nXColor9 = workPart.Preferences.PartSketch.MovableCurveColor;
    
    NXOpen.NXColor nXColor10;
    nXColor10 = workPart.Preferences.PartSketch.PersistentRelationColor;
    
    NXOpen.Weld.WeldPreferenceBuilder weldPreferenceBuilder2;
    weldPreferenceBuilder2 = workPart.Features.WeldManager.CreatePreferenceBuilder();
    
    weldPreferenceBuilder2.Destroy();
    
    NXOpen.Display.SelPref selPref1;
    selPref1 = workPart.SelPref.CreateSelPref();
    
    selPref1.Destroy();
    
    // ----------------------------------------------
    //   USeN(F)->	y(T)  ->OX[	y(S)...
    // ----------------------------------------------
    NXOpen.Preferences.SessionModeling.ShareGeometriesOnSaveType shareGeometryOnSave1;
    shareGeometryOnSave1 = theSession.Preferences.Modeling.ShareGeometriesOption;
    
    // ----------------------------------------------
    //   US]wQ(T)->5uq_(V)->U_6R(R)...
    // ----------------------------------------------
    theUI.MovieManager.Start("E:\\NX\\movie.avi", false);
    
    // ----------------------------------------------
    //   US]wQ(T)->5uq_(V)->\Pbk(S)
    // ----------------------------------------------
    theUI.MovieManager.End();
    
    // ----------------------------------------------
    //   USeN(F)->OX[(S)
    // ----------------------------------------------
    NXOpen.Session.UndoMarkId markId23;
    markId23 = theSession.SetUndoMark(NXOpen.Session.MarkVisibility.Invisible, "_Y");
    
    theSession.SetUndoMarkName(markId23, "}TTN [Fh");
    
    theSession.UndoToMark(markId23, null);
    
    theSession.DeleteUndoMark(markId23, null);
    
    theSession.DeleteUndoMark(markId23, null);
    
    // ----------------------------------------------
    //   USeN(F)->Q(X)
    // ----------------------------------------------
