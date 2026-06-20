import clr, sys, os
sys.path.append(r'E:\NX\NX\NXBIN\managed_core')
clr.AddReference('NXOpen')
import System
asm = System.Reflection.Assembly.LoadFrom(r'E:\NX\NX\NXBIN\managed_core\NXOpen.dll')

lines = []

def dump(cls_name):
    t = asm.GetType(cls_name)
    if t is None:
        lines.append('=== ' + cls_name + ' === NOT FOUND')
        return
    lines.append('=== ' + cls_name + ' ===')
    try:
        lines.append('  Properties:')
        for p in t.GetProperties():
            lines.append('    ' + p.Name + ' : ' + p.PropertyType.Name)
    except: pass
    try:
        lines.append('  Methods:')
        for m in t.GetMethods():
            if m.IsPublic and not m.IsSpecialName:
                tags = []
                for p in m.GetParameters():
                    tags.append(p.ParameterType.Name + ' ' + p.Name)
                lines.append('    ' + m.Name + '(' + ', '.join(tags) + ')')
    except: pass
    lines.append('')

dump('NXOpen.Features.EdgeBlendBuilder')
dump('NXOpen.Features.ShellBuilder')
dump('NXOpen.Features.PatternFeatureBuilder')
dump('NXOpen.Features.MoveObjectBuilder')
dump('NXOpen.Features.SweptBuilder1')
dump('NXOpen.GeometricUtilities.RectangularPattern')
dump('NXOpen.GeometricUtilities.CircularPattern')
dump('NXOpen.GeometricUtilities.ModlMotion')
dump('NXOpen.GeometricUtilities.PatternDefinition')
dump('NXOpen.GeometricUtilities.DistancePatternSpacing')
dump('NXOpen.GeometricUtilities.AngularPatternSpacing')
dump('NXOpen.CurveCollection')
dump('NXOpen.SectionList')
dump('NXOpen.Features.BaseFeatureCollection')

out = r'e:\NX\Lang-to-NX\nx_api_dump.txt'
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('Dumped ' + str(len(lines)) + ' lines to ' + out)

# Find how to access FreeformSurfaceCollection
print('=== FreeformSurfaceCollection property on Part ===')
for p in asm.GetType('NXOpen.Part').GetProperties():
    if p.PropertyType.Name == 'FreeformSurfaceCollection':
        print('  Part.' + p.Name)
        break

for p in asm.GetType('NXOpen.BasePart').GetProperties():
    if p.PropertyType.Name == 'FreeformSurfaceCollection':
        print('  BasePart.' + p.Name)
        break
else:
    # Search by property name containing Freeform
    print('  Searching by name...')
    for p in asm.GetType('NXOpen.Part').GetProperties():
        if 'Freeform' in p.PropertyType.Name:
            print('  Part.' + p.Name + ' : ' + p.PropertyType.Name)
