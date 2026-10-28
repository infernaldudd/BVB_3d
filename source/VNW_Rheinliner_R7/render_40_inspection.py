#!/usr/bin/env python3
"""Render exactly 40 non-identical diagnostic perspectives from the actual GLB geometry.
Reference photos are NEVER reused as model renders; these are offscreen VTK images.
"""
from pathlib import Path
from collections import defaultdict
from PIL import Image,ImageDraw,ImageFont
import vtk,trimesh,numpy as np,math,json
from vtkmodules.util.numpy_support import numpy_to_vtk,numpy_to_vtkIdTypeArray
R=Path(__file__).resolve().parent
s=trimesh.load(R/'exports'/'VNW_Rheinliner_R7_Complete.glb',force='scene')
groups=defaultdict(list)
for node in s.graph.nodes_geometry:
    tm,geomname=s.graph.get(node);m=s.geometry[geomname].copy();m.apply_transform(tm)
    mat=getattr(m.visual,'material',None); c=getattr(mat,'baseColorFactor',None)
    if c is None:c=[150,150,150,255]
    groups[(getattr(mat,'name','DEFAULT'),tuple(c))].append(m)
ren=vtk.vtkRenderer();ren.SetBackground(.90,.92,.94);ren.SetBackground2(.68,.74,.80);ren.GradientBackgroundOn()
for (name,col),mlist in groups.items():
    m=trimesh.util.concatenate(mlist);points=vtk.vtkPoints();points.SetData(numpy_to_vtk(m.vertices.astype(np.float32),deep=True)); faces=np.column_stack((np.full(len(m.faces),3),m.faces)).astype(np.int64).ravel()
    ca=vtk.vtkCellArray();ca.SetCells(len(m.faces),numpy_to_vtkIdTypeArray(faces,deep=True))
    pd=vtk.vtkPolyData();pd.SetPoints(points);pd.SetPolys(ca)
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(pd)
    actor=vtk.vtkActor();actor.SetMapper(mapper)
    prop=actor.GetProperty();prop.SetColor(*(np.array(col[:3])/255));prop.SetAmbient(.37);prop.SetDiffuse(.63);prop.SetSpecular(.17 if name in ['JADE','SILVER','STEEL'] else .04);prop.SetSpecularPower(24)
    if name in ['GLASS','WINDSHIELD']:prop.SetOpacity(.26)
    ren.AddActor(actor)
win=vtk.vtkEGLRenderWindow();win.SetOffScreenRendering(1);win.SetSize(720,432);win.AddRenderer(ren)
lights=[]
for loc,intensity in [((-12,-30,30),1.0),((25,30,28),.8)]:
    light=vtk.vtkLight();light.SetPosition(*loc);light.SetFocalPoint(0,0,1);light.SetIntensity(intensity);ren.AddLight(light)
views=[]
def add(label,at,eye,parallel=False,scale=3.3):views.append((label,at,eye,parallel,scale))
# 6 global orthographic reference angles
add('01_Reference_Front',(-21.05,0,1.85),(-34,0,1.85),True,2.05)
add('02_Reference_Back',(21.05,0,1.85),(34,0,1.85),True,2.05)
add('03_Reference_DoorSide',(0,0,1.7),(0,72,1.7),True,4.3)
add('04_Reference_BlankSide',(0,0,1.7),(0,-72,1.7),True,4.3)
add('05_Reference_Top',(0,0,1.5),(0,0,58),True,3.7)
add('06_Reference_Underside',(0,0,1.1),(0,0,-42),True,3.7)
# front/rear 3/4 view under different sun angles
for n,x in enumerate([-1,1]):
    for j,sy in enumerate([-1,1]):
        add(f'{7+n*2+j:02d}_End_{n}_Side_{j}',(x*19.6,0,1.75),(x*30,sy*10.2,4.25))
# intermediate doors, joints each side from player standing height and elevated angle
for j,x in enumerate([-18.3,-11.8,-5.9,-1.5,1.5,5.75,11.62,18.1]):
    for side in (-1,1):
        idx=11+j*2+(1 if side==1 else 0)
        add(f'{idx:02d}_Section_{j}_{"door" if side==1 else "blank"}',(x,0,1.45),(x+1.15,side*6,2.48),False)
# roof / undercarriage actual close-ups
for j,x in enumerate([-18,-10,-1,8,17]):
    add(f'{27+j:02d}_Roof_{j}',(x,0,3.24),(x+2,4,9.5))
for j,x in enumerate([-18.6,-11.6,-5.7,.0,5.7,11.6,18.4]):
    add(f'{32+j:02d}_UnderJoint_{j}',(x,0,.62),(x+1.55,3,-1.65))
# two passenger interior corridor views
add('39_Interior_Front',(-12.2,0,1.67),(-3,.05,1.67))
add('40_Interior_Back',(11.2,0,1.67),(3,-.05,1.67))
assert len(views)==40,len(views)
outdir=R/'qa'/'40_views';outdir.mkdir(parents=True,exist_ok=True)
manifest=[]
for i,(label,look,eye,parallel,scale) in enumerate(views):
    cam=ren.GetActiveCamera();cam.SetPosition(*eye);cam.SetFocalPoint(*look);cam.SetViewUp(0,0,1)
    if label.endswith('Top'):cam.SetViewUp(1,0,0)
    if label.endswith('Underside'):cam.SetViewUp(-1,0,0)
    if parallel:cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    else:cam.ParallelProjectionOff();cam.SetViewAngle(55 if i>=10 else 40)
    ren.ResetCameraClippingRange();win.Render()
    w=vtk.vtkWindowToImageFilter();w.SetInput(win);w.SetInputBufferTypeToRGB();w.ReadFrontBufferOff();w.Update()
    writer=vtk.vtkPNGWriter();writer.SetInputConnection(w.GetOutputPort());writer.SetFileName(str(outdir/(label+'.png')));writer.Write()
    manifest.append({'id':i+1,'label':label,'look_at_m':look,'camera_m':eye,'file':f'qa/40_views/{label}.png'})
    if i%10==9:print('rendered',i+1,'of 40',flush=True)
(R/'qa'/'view_manifest.json').write_text(json.dumps(manifest,indent=2))
for page in (0,1):
    part=views[page*20:(page+1)*20]
    sheet=Image.new('RGB',(5*368,4*252),'#edf0f2');d=ImageDraw.Draw(sheet)
    for j,(label,*rest) in enumerate(part):
        img=Image.open(outdir/(label+'.png')).convert('RGB');img.thumbnail((356,214));x=(j%5)*368+6;y=(j//5)*252+25;sheet.paste(img,(x,y));d.text((x,y-18),label,fill='#111111')
    sheet.save(R/'qa'/f'40_perspectives_contact_{page+1}.jpg',quality=86,optimize=True)
print('Saved 40 image files, two contact sheets, view_manifest')