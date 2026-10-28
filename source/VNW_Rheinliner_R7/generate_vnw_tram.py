#!/usr/bin/env python3
"""VNW RHEINLINER R7 revision R2 articulated Swiss tram procedural source.
Generate static all-interior/all-exterior GLB, separate UE collision GLB,
rig-control rest transforms and simple glTF showcase animations.
This is an original 3D game-asset prototype, not a manufacturer CAD replica.
Run: python generate_vnw_tram.py
Dependencies: numpy trimesh pillow scipy.
"""
from pathlib import Path
from collections import defaultdict
import json, math, struct, io, time
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parent
for sub in ('textures','exports','documentation','renders','qa'):(ROOT/sub).mkdir(exist_ok=True)
LENGTHS=[6.6,6.1,5.65,6.,5.65,6.1,6.76]
LENGTH=sum(LENGTHS) # 42.86
WIDTH=2.30
SECTION_GAP=.21
FLOOR=.49
ROOF=3.29
GAUGE=1.
np.random.seed(11)


def tex_wood(size=2048):
    h=w=size
    rng=np.random.default_rng(16)
    # Lengthwise quartersawn oak: subtle longitudinal fibers, warm real wood tones.
    y=np.arange(h,dtype=np.float32)
    x=np.arange(w,dtype=np.float32)
    rings=np.sin(x*.115 + np.sin(x*.017)*3.0)
    rings2=np.sin(x*.47+np.sin(x*.033)*1.4)
    broad=np.sin(x*.013+.25)
    noise=rng.normal(0,1,(w,)).astype(np.float32)
    base=182+10*rings+4*rings2+13*broad+4*noise
    img=np.empty((h,w,3),dtype=np.uint8)
    for row in range(h):
        v=base+3*np.sin(row*.034+x*.018)+rng.normal(0,1.3)
        img[row,:,0]=np.clip(v+14,0,255)
        img[row,:,1]=np.clip(v-9,0,255)
        img[row,:,2]=np.clip(v-40,0,255)
    Image.fromarray(img).save(ROOT/'textures'/'VNW_Oak_BaseColor_2K.png',optimize=True)
    return Image.fromarray(img)

def tex_floor(size=2048):
    rng=np.random.default_rng(23); y,x=np.indices((size,size));
    rib=np.where((x%17)<2,9,0)
    noise=rng.normal(0,2.2,(size,size)); val=np.clip(45+rib+noise,0,255).astype(np.uint8)
    im=Image.fromarray(np.dstack((val+3,val+5,val+8)))
    im.save(ROOT/'textures'/'VNW_Floor_BaseColor_2K.png',optimize=True)
    return im

def tex_metal(size=2048):
    rng=np.random.default_rng(55); y,x=np.indices((size,size));
    v=np.clip(115+5*np.sin(y*.11)+rng.normal(0,1.8,(size,size)),0,255).astype(np.uint8)
    im=Image.fromarray(np.dstack((v,v+2,v+3)))
    im.save(ROOT/'textures'/'VNW_BrushedSteel_BaseColor_2K.png',optimize=True)
    return im

print('Generating 2K original PBR albedo textures...', flush=True)
wood=tex_wood(); floorimg=tex_floor(); steelimg=tex_metal()

# Materials are PBR, textured where UVs are assigned; numeric values are 8-bit RGBA.
SPEC={
 'JADE':((20,142,76,255),.38,.55), 'JADE_DEEP':((10,85,55,255),.47,.47),
 'PALE':((222,228,219,255),.38,.35),'BLACK':((13,23,31,255),.65,.18),
 'RUBBER':((30,36,42,255),.92,.01), 'PANEL':((216,225,225,255),.66,.08),
 'WARM':((198,148,95,255),.66,.04),'GOLD':((201,176,101,255),.39,.58),
 'STEEL':((167,180,185,255),.27,.88),'DARK_STEEL':((64,74,82,255),.44,.76),
 'SILVER':((193,202,209,255),.28,.82), 'WHEEL':((38,43,47,255),.80,.29),
 'LAMP':((240,245,221,255),.23,.04),'RED_LAMP':((225,41,42,255),.22,.12),
 'LED':((169,234,233,255),.23,.12), 'DISPLAY':((7,13,17,255),.45,.07),
 'DISPLAY_CYAN':((32,221,197,255),.35,.05),'UPHOLSTERY':((69,84,90,255),.82,.01),
 'GROOVE':((123,87,58,255),.74,.09), 'HATCH':((74,86,89,255),.67,.25),
 'FLOOR':((52,55,58,255),.93,.01),'WOOD':((212,170,119,255),.58,.01),
 'GLASS':((86,134,156,77),.13,.03),'WINDSHIELD':((47,79,96,93),.11,.01),
}
MATS={}
for n,(c,r,m) in SPEC.items():
    args={'name':n,'baseColorFactor':c,'roughnessFactor':r,'metallicFactor':m,'doubleSided':True}
    if n in ('GLASS','WINDSHIELD'):args['alphaMode']='BLEND'
    if n in ('LAMP','LED','RED_LAMP','DISPLAY_CYAN'): args['emissiveFactor']=(.8,.8,.69) if n=='LAMP' else ((.04,.75,.67) if n in ('DISPLAY_CYAN','LED') else (.7,.04,.03))
    if n=='WOOD': args['baseColorTexture']=wood
    if n=='FLOOR': args['baseColorTexture']=floorimg
    if n=='STEEL': args['baseColorTexture']=steelimg
    MATS[n]=PBRMaterial(**args)

scene=trimesh.Scene(base_frame='world')
collision_scene=trimesh.Scene(base_frame='world')
# keyed by moving part/module parent and material
meshgroups=defaultdict(list)
FRAMES={}
animated_nodes={}
static_count=0

# Shared transforms / reusable geometry constructors.
def T(x=0,y=0,z=0):
    a=np.eye(4); a[:3,3]=[x,y,z]; return a

def cube(dim,center):
    o=trimesh.creation.box(extents=dim)
    o.apply_translation(center); return o

def thicken_nose_skin(mesh,inward,thickness=.017):
    """Close the shallow free-form front panels along their perimeter. Each zone
    remains separately materialized, with 17 mm construction thickness, avoiding
    six open surface meshes in earlier nose geometry. Not a welded full shell.
    """
    verts=np.asarray(mesh.vertices,float)
    n=len(verts)//2
    rear=verts.copy();rear[:,0]+=inward*thickness
    allv=np.vstack((verts,rear))
    faces=mesh.faces.tolist()
    faces.extend((tri+len(verts))[::-1].tolist() for tri in mesh.faces)
    edges=[(j,j+1) for j in range(n-1)] + [(n+j,n+j+1) for j in range(n-1)]
    edges.extend([(0,n),(n-1,2*n-1)])
    shift=len(verts)
    for a,b in edges:
        faces.extend([[a,b,b+shift],[a,b+shift,a+shift]])
    return trimesh.Trimesh(vertices=allv,faces=faces,process=False)

def prism_x(poly_yz,x0,x1):
    v=[]
    for x in (x0,x1):v.extend([[x,y,z] for y,z in poly_yz])
    n=len(poly_yz); f=[]
    for i in range(1,n-1): f.extend([[0,i+1,i],[n,n+i,n+i+1]])
    for i in range(n):
        j=(i+1)%n; f.extend([[i,j,n+j],[i,n+j,n+i]])
    return trimesh.Trimesh(vertices=v,faces=f,process=False)

def cylinder(p1,p2,r,sections=10):
    p1=np.array(p1,dtype=float); p2=np.array(p2,dtype=float)
    direction=p2-p1
    if np.linalg.norm(direction)<1e-7:return None
    mesh=trimesh.creation.cylinder(radius=r, height=np.linalg.norm(direction), sections=sections)
    mat=trimesh.geometry.align_vectors([0,0,1], direction)
    mesh.apply_transform(mat);mesh.apply_translation((p1+p2)*.5)
    return mesh

def frame_node(name,parent,offset=(0,0,0)):
    FRAMES[name]=(parent,offset)
    scene.graph.update(frame_to=name, frame_from=parent, matrix=T(*offset))

def emit(part,mat,mesh):
    if mesh is None:return
    meshgroups[(part,mat)].append(mesh)

def emit_cube(part,mat,dim,xyz):emit(part,mat,cube(dim,xyz))

def emit_rod(part,mat,p,q,r=.019,sections=10):emit(part,mat,cylinder(p,q,r,sections))

def emit_rod_chain(part,mat,points,r=.02,sections=12):
    for a,b in zip(points[:-1],points[1:]):emit_rod(part,mat,a,b,r,sections)

def texture_uv_box(dim,center,scale=1):
    mesh=cube(dim,center)
    v=mesh.vertices
    # Project XY for horizontal flooring, x-z mapping for side surfaces.
    uv=np.column_stack((v[:,0]/scale,v[:,1]/scale)).astype(np.float32)
    mesh.visual=TextureVisuals(uv=uv, material=MATS['FLOOR'])
    return mesh

def seat_shell(x,y,dir=1,wide=.42):
    # Molded wood sheet: bent in side elevation with 22 mm real thickness.
    shape=np.array([[-.245,.79],[-.195,.80],[-.10,.805],[.02,.815],[.130,.820],[.195,.838],
           [.213,.90],[.215,1.03],[.205,1.17],[.180,1.32],[.150,1.437],
           [.12,1.47],[.092,1.474]],float)
    # front of seat faces negative x; rear back towards positive x.
    xx=shape[:,0]*dir+x; zz=shape[:,1]
    n=len(shape); layers=5; vert=[];uv=[]
    path=np.concatenate(([0],np.cumsum(np.linalg.norm(np.diff(shape,axis=0),axis=1))))
    for side in (0,1):
        for k in range(layers):
            cy=y+(-wide*.5+(wide*k/(layers-1)))
            for j in range(n):
                vert.append([xx[j]-side*.021*dir,cy,zz[j]+side*.003])
                uv.append([k/(layers-1),path[j]/2])
    f=[];shift=n*layers
    for j in range(n-1):
        for k in range(layers-1):
            a=k*n+j;b=(k+1)*n+j
            f.extend([[a,b,a+1],[a+1,b,b+1]])
            a+=shift;b+=shift
            f.extend([[a,a+1,b],[a+1,b+1,b]])
    for k in (0,layers-1):
        for j in range(n-1):
            a=k*n+j;b=a+shift
            if k==0:f.extend([[a,a+1,b],[a+1,b+1,b]])
            else:f.extend([[a,b,a+1],[a+1,b,b+1]])
    for j in (0,n-1):
        for k in range(layers-1):
            a=k*n+j;b=(k+1)*n+j
            f.extend([[a,a+shift,b],[b,a+shift,b+shift]])
    mesh=trimesh.Trimesh(vertices=vert,faces=f,process=False)
    mesh.visual=TextureVisuals(uv=np.array(uv),material=MATS['WOOD'])
    return mesh

# Intercar passage bellows: corrugated continuous rectangular tunnel, fully open centrally.
def create_bellows(i,xmin,xmax):
    node='ARTICULATION_%02d'%i
    frame_node(node,'world',((xmin+xmax)*.5,0,0))
    w=xmax-xmin
    for k in range(11):
        x=-w*.5+w*k/10
        rw=1.04+(.045 if k%2==0 else -.025)
        z0=FLOOR-.015; z1=3.05+(.042 if k%2==0 else -.018)
        # U shaped framework, without a solid wall across the passenger aisle.
        emit_cube(node,'RUBBER',(.038,.05,z1-z0),(x,-rw,(z0+z1)/2))
        emit_cube(node,'RUBBER',(.038,.05,z1-z0),(x,rw,(z0+z1)/2))
        emit_cube(node,'RUBBER',(.038,2*rw,.05),(x,0,z1))
        # paired joints and internal concertina creases
        emit_rod(node,'DARK_STEEL',(x,-rw,1.05),(x,rw,1.05),.009,8) if k in (0,10) else None
    emit_cube(node,'FLOOR',(w+.08,1.84,.06),(0,0,FLOOR-.04))
    emit_cube(node,'DARK_STEEL',(w+.08,1.87,.035),(0,0,FLOOR-.089))
    emit_rod(node,'SILVER',(-w*.47,-.89,1.35),(-w*.47,-.89,2.5),.017)
    emit_rod(node,'SILVER',(w*.47,.89,1.35),(w*.47,.89,2.5),.017)

# x positions for sections including exact total bounding box length.
section_x=[]
x=-LENGTH/2
for l in LENGTHS:
    section_x.append(x+l/2)
    x+=l
SECTION_NODES=[]
DOOR_IDS=[]
WHEEL_IDS=[]
SEATS=0

for i,(l,global_x) in enumerate(zip(LENGTHS,section_x)):
    node='SECTION_%02d'%i;SECTION_NODES.append(node)
    frame_node(node,'world',(global_x,0,0))
    a=-l*.5+(0.0 if i==0 else SECTION_GAP*.5)
    b=l*.5-(0.0 if i==6 else SECTION_GAP*.5)
    left_end=(i==0)
    right_end=(i==6)
    # End modules have a full driver cockpit at their outermost end.
    pane_a=a+(1.45 if left_end else .0)
    pane_b=b-(1.45 if right_end else .0)
    # Main floor and realistic waterproof skirting.
    emit(node,'FLOOR',texture_uv_box((b-a,2.13,.075),((a+b)/2,0,FLOOR-.028),scale=1.8))
    emit_cube(node,'DARK_STEEL',(b-a,2.25,.12),((a+b)/2,0,.41))
    if i in (0,2,4,6):
        bay=(-.49 if i==0 else .49 if i==6 else 0.)
        # Deliberate OPEN clearance only around the bogie.
        # Unbroken body slab previously concealed all wheels, incorrect in side references.
        for s0,s1 in ((a,bay-1.22),(bay+1.22,b)):
            if s1-s0>.05:emit_cube(node,'JADE',(s1-s0,2.28,.27),((s0+s1)/2,0,.29))
        # Black wheel arches are visible even from low viewing angles.
        for sy in (-1,1):
            emit_cube(node,'RUBBER',(2.44,.055,.075),(bay,sy*1.101,.56))
    else:
        emit_cube(node,'JADE',(b-a,2.28,.27),((a+b)/2,0,.29))
    for side in (-1,1):
        emit_cube(node,'BLACK',(b-a,.04,.12),((a+b)*.5,side*1.12,.49))
        emit_cube(node,'JADE_DEEP',(b-a,.025,.11),((a+b)*.5,side*1.119,.63))
    # Roof skin, deep side fascia, actual wall thickness and realistic stepped crown.
    roof_profile=[(-1.147,2.95),(-1.14,3.115),(-1.09,3.22),(-.88,3.29),
                  (.88,3.29),(1.09,3.22),(1.14,3.115),(1.147,2.95)]
    emit(node,'JADE',prism_x(roof_profile,a,b))
    emit_cube(node,'PANEL',(b-a,1.83,.08),((a+b)/2,0,2.91))
    emit_cube(node,'WARM',(b-a,1.25,.025),((a+b)/2,0,2.861))
    # Side ceiling trim and 2 long diffuser lights per module.
    for side in (-1,1):
        emit_cube(node,'PANEL',(b-a,.30,.027),((a+b)/2,side*.87,2.842))
        emit_cube(node,'DARK_STEEL',(b-a,.11,.018),((a+b)/2,side*.70,2.831))
        emit_cube(node,'LED',(max(.18,b-a-.48),.039,.007),((a+b)/2,side*.93,2.821))
        emit_cube(node,'BLACK',(b-a,.10,.11),((a+b)/2,side*1.08,2.819))
        emit_cube(node,'STEEL',(b-a,.018,.025),((a+b)/2,side*1.07,2.749))
        emit_cube(node,'JADE',(b-a,.035,.29),((a+b)/2,side*1.122,2.80))
    # Original shallow roof grille units, power electronics housings and roof fasteners.
    for j in range(max(1,int((b-a)/1.95))):
        xx=a+0.8+j*1.95
        if xx>b-.5:continue
        emit_cube(node,'JADE_DEEP',(.84,1.08,.082),(xx,0,3.341))
        for gg in range(8):
            emit_cube(node,'DARK_STEEL',(.035,.91,.012),(xx-.35+gg*.1,0,3.386))
    # 1.32m wide double doors, one pair per passenger section, plus extra center pair.
    # Seven-section Be6/8 REFERENCE: 8 one-sided passenger entrances,
    # two single-leaf 0.80 m end doors and six double-leaf 1.30 m doors.
    doors=([.7] if i==0 else ([-.7] if i==6 else ([-1.35,1.35] if i==3 else [0.])))
    doors=[d for d in doors if pane_a+.82<=d<=pane_b-.82]
    door_widths={d:(.80 if i in (0,6) else 1.30) for d in doors}
    # Window repetition. Main shell cannot block glazed areas or doorways.
    for side in (-1,1):
        y=side*1.106
        side_doors=doors if side==1 else [] # Doors on right-hand side only (front=-X).
        # Black strip surrounding all windows except at door boundaries.
        emit_cube(node,'BLACK',(pane_b-pane_a,.068,.051),((pane_a+pane_b)/2,y,1.058))
        emit_cube(node,'BLACK',(pane_b-pane_a,.068,.060),((pane_a+pane_b)/2,y,2.553))
        # Break up window into glazed spans and operable door cutouts.
        cuts=[pane_a,pane_b]
        for d in side_doors:cuts.extend([d-door_widths[d]/2-.018,d+door_widths[d]/2+.018])
        for k in range(1,int((pane_b-pane_a)/1.32)+1):
            v=pane_a+k*1.32
            if pane_a+.16<v<pane_b-.16 and not any(abs(v-d)<door_widths[d]*.5+.16 for d in side_doors):cuts.append(v)
        cuts=sorted(set(round(max(pane_a,min(pane_b,c)),5) for c in cuts))
        for st,en in zip(cuts[:-1],cuts[1:]):
            if en-st<.035:continue
            cx=(st+en)*.5
            is_door=any(abs(cx-d)<door_widths[d]*.5 for d in side_doors)
            if not is_door:
                # Opaque lower sill and upper lintel, clear glazing with subtle frames.
                emit_cube(node,'JADE',(en-st,.09,.57),(cx,side*1.105,.795))
                emit_cube(node,'JADE_DEEP',(en-st,.057,.058),(cx,side*1.105,1.113))
                emit_cube(node,'JADE',(en-st,.077,.45),(cx,side*1.105,2.775))
                emit_cube(node,'GLASS',(max(.02,en-st-.07),.018,1.37),(cx,side*1.128,1.805))
                emit_cube(node,'BLACK',(.037,.11,1.43),(st,side*1.095,1.815))
            else:
                # Remove entire black backing in door opening and replace with operable panels.
                # This gap is real, supported by independent door collision in secondary asset.
                emit_cube(node,'DARK_STEEL',(en-st,.046,.12),(cx,side*1.105,2.492))
                emit_cube(node,'SILVER',(en-st,.11,.03),(cx,side*1.095,.525))
        emit_cube(node,'DARK_STEEL',(.07,.13,2.15),(pane_a,side*1.084,1.525))
        emit_cube(node,'DARK_STEEL',(.07,.13,2.15),(pane_b,side*1.084,1.525))
        # long cream belt across mid-lower side body, thin original graphic identity line.
        for st,en in zip(cuts[:-1],cuts[1:]):
            cx=(st+en)*.5
            if not any(abs(cx-d)<door_widths[d]*.5 for d in side_doors):
                emit_cube(node,'PALE',(max(.02,en-st-.09),.011,.055),(cx,side*1.095,1.014))
        # Vertical seams and screw details in lower underfloor access panels.
        for xx in np.arange(pane_a+.9,pane_b-.2,1.48):
            if any(abs(xx-d)<door_widths[d]*.5+.07 for d in side_doors):continue
            emit_cube(node,'JADE_DEEP',(.009,.006,.40),(xx,side*1.1199,.72))
            emit_cube(node,'SILVER',(.032,.008,.025),(xx,side*1.1198,.89))
    # Full-height vertical framing and doors: each leaf slides away from doorway center.
    for door_n,d in enumerate(doors):
        for side in (1,):
            y=side*1.095
            for leaf in ((1,) if door_widths[d]<1 else (-1,1)):
                wleaf=(.755 if door_widths[d]<1 else .645)
                offleaf=(0 if door_widths[d]<1 else leaf*.337)
                leafid=f'DOOR_S{i:02d}_D{door_n}_{"L" if side<0 else "R"}_{"A" if leaf<0 else "B"}'
                DOOR_IDS.append((leafid,leaf))
                frame_node(leafid,node,(d+offleaf,y,0))
                emit_cube(leafid,'DARK_STEEL',(wleaf,.075,.085),(0,0,2.482))
                emit_cube(leafid,'DARK_STEEL',(wleaf,.075,.076),(0,0,1.045))
                for e in (-1,1):emit_cube(leafid,'DARK_STEEL',(.044,.077,1.470),(e*(wleaf/2-.018),0,1.747))
                emit_cube(leafid,'GLASS',(wleaf-.072,.032,1.395),(0,0,1.758))
                emit_cube(leafid,'JADE',(wleaf-.026,.080,.39),(0,0,.736))
                emit_cube(leafid,'PALE',(.016,.091,1.43),(leaf*(wleaf*.43),0,1.758))
                emit_cube(leafid,'STEEL',(.025,.14,.28),(leaf*(wleaf*.42),-side*.05,1.275))
                emit_cube(leafid,'GOLD',(.12,.014,.08),(leaf*(wleaf*.36),side*.045,1.23))
                # Inner door push button/arrow.
                emit_cube(leafid,'LED',(.075,.02,.075),(leaf*(wleaf*.36),-side*.07,1.23))
            for ed in (-door_widths[d]/2-.025,door_widths[d]/2+.025):
                emit_cube(node,'DARK_STEEL',(.060,.115,2.10),(d+ed,y,1.527))
            emit_cube(node,'DARK_STEEL',(door_widths[d]+.12,.13,.08),(d,side*1.084,2.54))
            emit_cube(node,'SILVER',(door_widths[d]+.12,.10,.035),(d,y,.52))
            # metal vertical poles and transverse upper strap.
            for xx in (d-door_widths[d]*.5-.08,d+door_widths[d]*.5+.08):
                emit_rod(node,'STEEL',(xx,side*.83,.50),(xx,side*.83,2.82),.024)
            emit_rod(node,'STEEL',(d-door_widths[d]*.5-.07,side*.83,2.55),(d+door_widths[d]*.5+.07,side*.83,2.55),.025)
            emit_cube(node,'DARK_STEEL',(.14,.15,.22),(d+door_widths[d]*.5+.07,side*.81,1.20))
            emit_cube(node,'LED',(.075,.045,.075),(d+door_widths[d]*.5+.07,side*.78,1.20))
        # wide open multipurpose area next to door, modest handrail fence at one side.
        emit_rod_chain(node,'STEEL',[(d-.74,-.92,.65),(d-.74,-.92,1.32),(d-.74,-.45,1.32)],.024)
    # Repeated passenger furniture: no seats block the real door opening or articulation tunnel.
    xrows=np.arange(pane_a+.58,pane_b-.24,.83)
    for j,xx in enumerate(xrows):
        if any(abs(xx-d)<.87 for d in doors):continue
        for side in (-1,1):
            yy=side*.777
            if (i in (0,6)) and (xx<pane_a+.45 or xx>pane_b-.45): continue
            emit(node,'WOOD',seat_shell(xx,yy,dir=(-1 if (j+i)%5 else 1),wide=.435))
            SEATS+=1
            emit_rod(node,'STEEL',(xx+.13,yy-.15,.52),(xx+.13,yy-.15,.79),.018)
            emit_rod(node,'STEEL',(xx+.13,yy+.15,.52),(xx+.13,yy+.15,.79),.018)
            emit_rod(node,'STEEL',(xx+.14,yy-.175,.78),(xx+.16,yy-.175,1.20),.010)
            emit_rod(node,'STEEL',(xx+.14,yy+.175,.78),(xx+.16,yy+.175,1.20),.010)
            # hardware underneath the seat has real thickness
            emit_cube(node,'DARK_STEEL',(.25,.26,.045),(xx+.12,yy,.764))
        # Third transverse seat on doorless side, leaving ~0.68m center aisle.
        # Layout based on functional 2+1 row, not random furniture duplication.
        emit(node,'WOOD',seat_shell(xx,-.338,dir=(-1 if (j+i)%5 else 1),wide=.435))
        SEATS+=1
        emit_rod(node,'STEEL',(xx+.13,-.48,.52),(xx+.13,-.48,.79),.018)
        emit_rod(node,'STEEL',(xx+.13,-.20,.52),(xx+.13,-.20,.79),.018)
        emit_cube(node,'DARK_STEEL',(.25,.26,.045),(xx+.12,-.338,.764))
        # Ceiling suspended bars at every second seating row.
        if j%2==0:
            emit_rod(node,'STEEL',(xx,-.86,2.58),(xx,.86,2.58),.023)
            for sy in (-.79,.79):
                emit_rod(node,'STEEL',(xx,sy,2.58),(xx,sy,2.83),.024)
                emit_rod_chain(node,'SILVER',[(xx-.07,sy,2.41),(xx-.09,sy,2.34),(xx+.07,sy,2.34),(xx+.09,sy,2.41)],.011)
    # Passenger information monitors, emergency panel housings and roof cameras.
    emit_cube(node,'BLACK',(.54,.09,.29),(b-.43,0,2.55))
    emit_cube(node,'DISPLAY',(.46,.016,.22),(b-.43,-.05,2.55))
    emit_cube(node,'DISPLAY_CYAN',(.33,.008,.032),(b-.43,-.063,2.565))
    emit_cube(node,'STEEL',(.06,.06,.19),(b-.43,0,2.77))
    emit_cube(node,'BLACK',(.15,.16,.10),(b-.29,0,2.80))
    emit_cube(node,'GLASS',(.055,.05,.047),(b-.29,-.095,2.78))
    emit_cube(node,'GOLD',(.10,.022,.14),(a+.30,-1.05,1.36))
    # Curved passenger grab rail along longitudinal aisle (keeps aisle uncluttered).
    for sy in (-.35,.35):
        emit_rod(node,'STEEL',(pane_a+.18,sy,2.76),(pane_b-.18,sy,2.76),.015)
    # Cab at two ends: original control desk, display, controls and partition.
    if i in (0,6):
        if i==0:front=a;cab_back=a+1.46;cabcenter=a+.73;driver_x=a+.83
        else:front=b;cab_back=b-1.46;cabcenter=b-.73;driver_x=b-.83
        # Cab partition is largely transparent but retained protective bulkhead.
        emit_cube(node,'DARK_STEEL',(.060,2.16,.10),(cab_back,0,2.83))
        emit_cube(node,'DARK_STEEL',(.060,.10,2.2),(cab_back,-1.03,1.69))
        emit_cube(node,'DARK_STEEL',(.060,.10,2.2),(cab_back,1.03,1.69))
        emit_cube(node,'GLASS',(.043,1.86,1.67),(cab_back,0,1.68))
        emit_cube(node,'PANEL',(.13,2.13,.42),(cab_back,0,.765))
        # lower cockpit dashboard sloping inward, multiple readable console surfaces
        emit_cube(node,'DARK_STEEL',(.87,1.61,.44),(cabcenter,0,1.03))
        emit_cube(node,'BLACK',(.47,1.2,.15),(cabcenter,0,1.31))
        emit_cube(node,'DISPLAY',(.21,.44,.045),(cabcenter,.09,1.42))
        emit_cube(node,'DISPLAY_CYAN',(.04,.24,.019),(cabcenter,.09,1.455))
        for k in range(12):
            xx=cabcenter+.10*math.cos(k*2*math.pi/12)
            yy=-.23+.13*math.sin(k*2*math.pi/12)
            emit_cube(node,'GOLD',(.035,.035,.017),(xx,yy,1.409))
        emit_rod(node,'DARK_STEEL',(cabcenter-.22,-.24,1.37),(cabcenter-.28,-.24,1.52),.018)
        emit_cube(node,'BLACK',(.09,.085,.065),(cabcenter-.28,-.24,1.51))
        emit_cube(node,'DARK_STEEL',(.54,.48,.13),(driver_x,.38,.72))
        emit_cube(node,'UPHOLSTERY',(.46,.43,.11),(driver_x,.38,.80))
        emit_cube(node,'UPHOLSTERY',(.11,.47,.56),(driver_x+.18,.38,1.08))
        emit_rod(node,'SILVER',(driver_x,.38,.56),(driver_x,.38,.76),.044)
        emit_cube(node,'PANEL',(.22,.22,.20),(driver_x,.38,.49))
        emit_cube(node,'JADE_DEEP',(.11,2.13,.60),(cab_back,0,2.59))
        # Cab sidewalls/side glass are kept separate from passenger windows.
        for sy in (-1,1):
            emit_cube(node,'JADE',(abs(cab_back-front),.07,.55),(cabcenter,sy*1.105,.80))
            emit_cube(node,'WINDSHIELD',(abs(cab_back-front)-.1,.03,1.25),(cabcenter,sy*1.127,1.87))
            emit_cube(node,'JADE',(.07,.09,1.57),(cab_back,sy*1.105,1.83))
    # Distinctive original identity side line and 4 geometrical chevron accents.
    if i in (0,3,6):
        for side in (-1,1):
            for j in range(4):
                xx=(pane_a+pane_b)/2 - .45+j*.24
                emit_rod(node,'PALE',(xx,side*1.127,.78),(xx+.135,side*1.125,.89),.014,8)
    if i in (0,3,6):
        # VNW operator emblem: three bespoke single-line glyphs on the opaque teal fascia.
        emblem_x=0 if i==3 else (.28 if i==0 else -.28)
        for sign in (-1,1):
            ypos=sign*1.125
            zhi,zlo=2.91,2.73
            dx=.16
            glyphs=[ [('v',[(0,zhi),(.075,zlo),(.15,zhi)])],
                     [('n',[(0,zlo),(0,zhi),(.15,zlo),(.15,zhi)])],
                     [('w',[(0,zhi),(.04,zlo),(.08,zhi-.07),(.12,zlo),(.16,zhi)])] ]
            for h,glyph in enumerate(glyphs):
                for letter,points in glyph:
                    coords=[(emblem_x+(h-1)*.25+px,ypos,pz) for px,pz in points]
                    emit_rod_chain(node,'PALE',coords,.014,10)
    print(f'Completed module {i+1}/7; center x={global_x:.2f} m; doors {len(doors)}',flush=True)

# Curved original nose geometry at front and rear, windshield non-spherical / tapered.
def front_end(forward=True):
    i=0 if forward else 6
    node=SECTION_NODES[i]
    length=LENGTHS[i];face=(-length*.5) if forward else length*.5
    inward=1 if forward else -1
    # 5 z contour surfaces, with unique diamond-shaped lamp surround.
    levels=[(.40,.90,.94),(.71,.98,1.08),(1.12,1.065,1.14),
            (2.58,1.09,1.17),(2.89,1.00,1.13),(3.16,.84,.83)]
    # Each ring point gets a mild smooth curved forward surface.
    for k in range(len(levels)-1):
        z0,hw0,xb0=levels[k];z1,hw1,xb1=levels[k+1]
        # forward x projection: lower bumper slightly inset, aerodynamic canopy top swept back
        # cross section width along windscreen: 9 points (rounded nose, no blocky edge)
        verts=[];faces=[]
        for z,hw,back in ((z0,hw0,xb0),(z1,hw1,xb1)):
            for s in np.linspace(-1,1,15):
                xx=face+inward*(.08+(.11 if abs(s)>.9 else 0)+.22*abs(s)**2 + .17*max(0,z-2.35))
                yy=s*hw
                verts.append([xx,yy,z])
        for a in range(14):
            faces.extend([[a,a+1,15+a+1],[a,15+a+1,15+a]])
        skin=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
        if k in (2,):material='WINDSHIELD'
        elif k in (3,):material='BLACK'
        else:material='JADE'
        emit(node,material,thicken_nose_skin(skin,inward))
    # panoramic glass broad band and sweeping original cream eyebrow
    emit_rod_chain(node,'PALE',[(face+inward*.21,-1.04,1.56),(face+inward*.14,-.94,1.23),
      (face+inward*.085,-.72,1.115),(face+inward*.072,0,1.070),
      (face+inward*.085,.72,1.115),(face+inward*.14,.94,1.23),(face+inward*.21,1.04,1.56)],.040,16)
    emit_rod_chain(node,'DARK_STEEL',[(face+inward*.18,-1.00,1.61),(face+inward*.10,-.91,1.28),
      (face+inward*.075,0,1.12),(face+inward*.10,.91,1.28),(face+inward*.18,1.00,1.61)],.018,16)
    # Distinctive custom lamp design: 3 oblique polygonal stripes on either side.
    for sy in (-1,1):
        for k in range(3):
            yy=sy*(.65+k*.10)
            emit_rod(node,'LAMP',(face+inward*.11,yy,1.025-k*.016),(face+inward*.12,yy+sy*.055,1.11-k*.01),.026,10)
        emit_cube(node,'RED_LAMP',(.035,.075,.18),(face+inward*.04,sy*.91,.76)) if not forward else None
    emit_cube(node,'DISPLAY',(.055,1.31,.235),(face+inward*.25,0,2.72))
    # Vertical geometric lines depict route readout in custom-designed typography.
    for bar in range(8):
        yy=-.59+.16*bar
        emit_cube(node,'DISPLAY_CYAN',(.032,.045,.047),(face+inward*.214,yy,2.74))
    emit_cube(node,'BLACK',(.14,.38,.17),(face+inward*.22,0,.83))
    emit_cube(node,'GOLD',(.151,.24,.068),(face+inward*.13,0,.83))
    # illuminated original chevron logo, not real BVB icon
    for sy in (-1,1):
        emit_rod(node,'LED',(face+inward*.10,sy*.17,.83),(face+inward*.10,0,.71),.021,10)
    # durable polymer bumper edging and coupler
    emit_cube(node,'RUBBER',(.16,1.85,.14),(face+inward*.085,0,.49))
    emit_cube(node,'DARK_STEEL',(.28,.30,.16),(face+inward*.27,0,.43))
    emit_cube(node,'PALE',(.054,1.76,.049),(face+inward*.09,0,1.12))

front_end(True);front_end(False)

# 4 articulated low-floor bogies with independent axle/wheel nodes and tracks 1000 mm apart.
bogies=[(0,-.49),(2,0.),(4,0.),(6,.49)]
for n,(section,xx) in enumerate(bogies):
    parent=SECTION_NODES[section]
    bog=f'BOGIE_{n:02d}'
    frame_node(bog,parent,(xx,0,0))
    emit_cube(bog,'DARK_STEEL',(2.65,1.42,.19),(0,0,.31))
    emit_cube(bog,'BLACK',(2.28,1.29,.21),(0,0,.46))
    for offs in (-.925,.925):
        axle=f'AXLE_B{n:02d}_{"A" if offs<0 else "B"}'
        frame_node(axle,bog,(offs,0,.32))
        WHEEL_IDS.append(axle)
        emit_rod(axle,'SILVER',(0,-.55,0),(0,.55,0),.062,20)
        for yy in (-.51,.51):
            emit(axle,'WHEEL',cylinder((0,yy-.045,0),(0,yy+.045,0),.305,40))
            emit(axle,'DARK_STEEL',cylinder((0,yy-.058,0),(0,yy+.058,0),.145,28))
            emit(axle,'STEEL',cylinder((0,yy-.060,0),(0,yy+.06,0),.071,20))
        emit_cube(bog,'DARK_STEEL',(.32,1.39,.10),(offs,0,.29))
        for yy in (-.68,.68):
            emit_rod(bog,'SILVER',(offs-.18,yy,.23),(offs-.18,yy,.51),.040)
            emit_rod(bog,'SILVER',(offs+.18,yy,.23),(offs+.18,yy,.51),.040)
    for sy in (-1,1):
        for xx2 in (-.55,.55):
            emit_rod(bog,'SILVER',(xx2,sy*.71,.32),(xx2,sy*.71,.48),.08,12)
    emit_cube(bog,'BLACK',(1.30,1.38,.25),(0,0,.55))
    emit_cube(bog,'STEEL',(.80,.25,.045),(0,0,.71))

# Accordion is physical geometry through every complete gap, not a solid membrane.
for i in range(6):
    x0=section_x[i]+LENGTHS[i]/2-SECTION_GAP*.5
    x1=section_x[i+1]-LENGTHS[i+1]/2+SECTION_GAP*.5
    create_bellows(i,(x0+x1)/2-.155,(x0+x1)/2+.155)

# Real articulated 4-bar pantograph: two lower parallelogram arms, top contact shoe.
# Parent/pivots allow lifting mechanism to be animated through external rig driver.
panto=SECTION_NODES[3]
frame_node('PANTOGRAPH_LIFT',panto,(-.10,0,3.345))
for sy in (-1,1):
    emit_cube('PANTOGRAPH_LIFT','RUBBER',(.20,.14,.08),(-.50,sy*.42,-.035))
    emit_rod('PANTOGRAPH_LIFT','DARK_STEEL',(-.54,sy*.42,.00),(.35,sy*.32,.155),.031,12)
    emit_rod('PANTOGRAPH_LIFT','DARK_STEEL',(.35,sy*.32,.155),(-.03,sy*.32,.30),.028,12)
    emit_rod('PANTOGRAPH_LIFT','STEEL',(-.49,sy*.43,.03),(-.02,sy*.31,.27),.017,10)
    emit_rod('PANTOGRAPH_LIFT','SILVER',(-.08,sy*.32,.29),(.57,sy*.40,.31),.016,10)
    emit_cube('PANTOGRAPH_LIFT','BLACK',(.18,.18,.04),(.52,sy*.41,.31))
emit_rod('PANTOGRAPH_LIFT','STEEL',(-.03,-.32,.3),(-.03,.32,.3),.033,12)
emit_rod('PANTOGRAPH_LIFT','STEEL',(.55,-.51,.315),(.55,.51,.315),.033,12)
emit_cube('PANTOGRAPH_LIFT','BLACK',(.06,1.25,.032),(.55,0,.34))

# Flush roof access doors with safety handgrips and connection cabling.
for i in (0,2,4,6):
    node=SECTION_NODES[i]
    x=.1
    emit_cube(node,'PALE',(.94,.62,.072),(x,0,3.335))
    emit_rod_chain(node,'DARK_STEEL',[(x-.32,-.25,3.39),(x-.32,-.25,3.43),(x+.29,-.25,3.43),(x+.29,-.25,3.39)],.014)

# Concatenate by frame+material for fewer draw calls, retaining all moving pivots as nodes.
for (part,mat),meshes in sorted(meshgroups.items()):
    combined=trimesh.util.concatenate(meshes) if len(meshes)>1 else meshes[0]
    if mat=='WOOD' and len(meshes)>1:
        # concatenate preserves texture UV on trimesh 4.11 when all source visuals match
        pass
    if not isinstance(combined.visual,TextureVisuals) or combined.visual.material.name!=mat:
        if mat in ('FLOOR','WOOD') and isinstance(combined.visual,TextureVisuals) and combined.visual.uv is not None:
            combined.visual.material=MATS[mat]
        else:
            combined.visual=TextureVisuals(material=MATS[mat])
    scene.add_geometry(combined,geom_name=f'GEOM_{part}_{mat}',node_name=f'{part}_{mat}',parent_node_name=part)
    static_count+=len(combined.faces)

# A separate UE-style UCX low-cost collision package: no dynamic collision in visible mesh.
for i,(l,x) in enumerate(zip(LENGTHS,section_x)):
    node=f'COLLISION_S{i:02d}'
    collision_scene.graph.update(frame_to=node,frame_from='world',matrix=T(x,0,0))
    usable=l-SECTION_GAP
    parts=[('FLOOR',cube((usable,2.11,.11),(0,0,.43))),
           ('ROOF',cube((usable,2.1,.12),(0,0,3.21))),
           ('LOW_L',cube((usable,.095,.53),(0,-1.11,.80))),
           ('LOW_R',cube((usable,.095,.53),(0,1.11,.80)))]
    for j,(lab,mesh) in enumerate(parts):
        collision_scene.add_geometry(mesh,geom_name=f'UCX_S{i:02d}_{lab}',node_name=f'UCX_S{i:02d}_{lab}',parent_node_name=node)
for i in range(6):
    x=(section_x[i]+LENGTHS[i]*.5+section_x[i+1]-LENGTHS[i+1]*.5)*.5
    collision_scene.add_geometry(cube((.31,1.86,.11),(x,0,.43)),geom_name=f'UCX_BELLOWS_{i:02d}',node_name=f'UCX_BELLOWS_{i:02d}')
# Doors need runtime toggled collision, exported separately as UCX DOOR pieces in collision GLB.
for label,sgn in DOOR_IDS:
    # position from authoritative rest world transforms, not guessed.
    try:mat,_=scene.graph.get(label)
    except Exception as e:print('Collision door skipped:',e);continue
    collision_scene.add_geometry(cube((.63,.10,1.97),(0,0,1.50)),geom_name='UCX_'+label,node_name='UCX_'+label,transform=mat)

OUTPUT=ROOT/'exports'/'VNW_Rheinliner_R7_Complete.glb'
COLL=ROOT/'exports'/'VNW_Rheinliner_R7_Collisions.glb'
print('Exporting GLBs...',flush=True)
OUTPUT.write_bytes(scene.export(file_type='glb'))
COLL.write_bytes(collision_scene.export(file_type='glb'))

# Attach valid glTF animation samplers and channels to exported .glb without fragile external deps.
# glTF/GLB has quaternion [x,y,z,w] and sampler translation VEC3, seconds as float32.
def inject_animations(path):
    blob=path.read_bytes()
    magic,ver,length=struct.unpack_from('<III',blob,0)
    assert magic==0x46546C67 and ver==2
    ln,chunkid=struct.unpack_from('<II',blob,12)
    assert chunkid==0x4E4F534A
    gltf=json.loads(blob[20:20+ln].decode('utf8'))
    ptr=20+((ln+3)//4)*4
    binlen,bintype=struct.unpack_from('<II',blob,ptr);ptr+=8
    assert bintype==0x004E4942
    binbuf=bytearray(blob[ptr:ptr+binlen])
    idx={n.get('name'):i for i,n in enumerate(gltf['nodes'])}
    names=[n.get('name') for n in gltf['nodes']]
    # glTF forbids matrix on nodes receiving TRS animation channels.
    for animated in list(SECTION_NODES)+list(WHEEL_IDS)+['PANTOGRAPH_LIFT']+[d for d,_ in DOOR_IDS]:
        if animated not in idx:continue
        n=gltf['nodes'][idx[animated]]
        if 'matrix' in n:
            tm=np.array(n.pop('matrix'),float).reshape((4,4),order='F')
            n['translation']=tm[:3,3].tolist()
            n['rotation']=[0.,0.,0.,1.]
            n['scale']=[1.,1.,1.]
    print('gLTF nodes',len(names),'doors indexed',sum(d in idx for d,_ in DOOR_IDS),'pantograph indexed', 'PANTOGRAPH_LIFT' in idx,flush=True)
    def accessory(arr,kind):
        nonlocal binbuf
        a=np.asarray(arr,np.float32)
        pad=(-len(binbuf))%4
        binbuf.extend(b'\0'*pad)
        offset=len(binbuf)
        binbuf.extend(a.tobytes())
        vindex=len(gltf['bufferViews'])
        gltf['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':a.nbytes})
        ai=len(gltf['accessors'])
        aflat=a.reshape((-1,a.shape[-1])) if a.ndim==2 else a
        gltf['accessors'].append({'bufferView':vindex,'componentType':5126,'count':len(a), 'type':kind,
             'min':list(np.min(aflat,axis=0).astype(float)) if a.ndim>1 else [float(np.min(a))],
             'max':list(np.max(aflat,axis=0).astype(float)) if a.ndim>1 else [float(np.max(a))]})
        return ai
    def anim(name, tracks):
        times=accessory(np.array([0.,.20,.92,2.1,2.65,3.30],dtype=np.float32),'SCALAR')
        samplers=[];channels=[]
        for n,prop,samples in tracks:
            if n not in idx:continue
            value_acc=accessory(samples,'VEC3' if prop=='translation' else 'VEC4')
            sid=len(samplers)
            samplers.append({'input':times,'output':value_acc,'interpolation':'LINEAR'})
            channels.append({'sampler':sid,'target':{'node':idx[n],'path':prop}})
        if channels:gltf.setdefault('animations',[]).append({'name':name,'samplers':samplers,'channels':channels})
    open_tracks=[]
    for name,side in DOOR_IDS:
        if name not in idx:continue
        pos=np.asarray(gltf['nodes'][idx[name]].get('translation',[0,0,0]),float)
        # glTF node may have a matrix instead of translation; in that case animation supplies original translation.
        if 'matrix' in gltf['nodes'][idx[name]]:
            m=np.array(gltf['nodes'][idx[name]]['matrix'],float).reshape((4,4),order='F')
            pos=m[:3,3]
            del gltf['nodes'][idx[name]]['matrix']
            gltf['nodes'][idx[name]]['translation']=pos.tolist()
        aa=np.repeat(pos.reshape(1,3),6,axis=0)
        aa[2:4,0]+=side*.57
        aa[4,0]+=side*.19
        open_tracks.append((name,'translation',aa))
    anim('DEMO_Doors_Open_Close_3p3s',open_tracks)
    rot=lambda a: [0.,float(math.sin(a*.5)),0.,float(math.cos(a*.5))]
    # Bogie axle cylinders rotate about local Y.
    rottracks=[]
    for name in WHEEL_IDS:
        rottracks.append((name,'rotation',[rot(0),rot(0.6),rot(2.4),rot(7.4),rot(8.8),rot(10.4)]))
    anim('DEMO_Wheels_Turn',rottracks)
    if 'PANTOGRAPH_LIFT' in idx:
        # Real-time pantograph actuation will require IK/4-bar driver in UE.
        anim('DEMO_Pantograph_Deploy', [('PANTOGRAPH_LIFT','rotation',[rot(0),rot(0),rot(-.12),rot(-.24),rot(-.12),rot(0)])])
    # Demonstrate individual section turning (small yaw about local vertical z).
    turn=[]
    for ii,n in enumerate(SECTION_NODES):
        aa=np.array([0,0,0,.04*(ii-3),.06*(ii-3),0],float)
        qs=np.array([[0,0,math.sin(t*.5),math.cos(t*.5)] for t in aa])
        turn.append((n,'rotation',qs))
    anim('DEMO_Section_Yaw_Rig',turn)
    gltf['buffers'][0]['byteLength']=len(binbuf)
    j=json.dumps(gltf,separators=(',',':')).encode()
    j+=b' '*((-len(j))%4)
    binbuf.extend(b'\x00'*((-len(binbuf))%4))
    out=struct.pack('<III',0x46546C67,2,12+8+len(j)+8+len(binbuf))
    out+=struct.pack('<II',len(j),0x4E4F534A)+j
    out+=struct.pack('<II',len(binbuf),0x004E4942)+bytes(binbuf)
    path.write_bytes(out)
    return gltf

# A separate animated scene: avoid engine imports mishandling matrix animations.
GLTF=inject_animations(OUTPUT)

# Export actual reduced-detail variants; keep door/axle nodes for UE retargeting.
def make_lod(level,filename):
    alt=trimesh.Scene(base_frame='world')
    for name,(parent,offset) in FRAMES.items():
        alt.graph.update(frame_to=name,frame_from=parent,matrix=T(*offset))
    tris=0
    for (part,mat),items in meshgroups.items():
        selected=[]
        for mesh in items:
            if level=='LOW' and mat=='WOOD' and part.startswith('SECTION_'):
                # Two meshes per seat: simple low-LOD seat and inclined back profile.
                mn,mx=mesh.bounds
                cy=(mn[1]+mx[1])*.5;cx=(mn[0]+mx[0])*.5
                wy=mx[1]-mn[1]
                selected.append(cube((.42,wy,.055),(cx,cy,.82)))
                selected.append(cube((.052,wy,.62),(cx+.15,cy,1.125)))
                continue
            b=np.asarray(mesh.extents)
            length=float(np.max(b))
            f=len(mesh.faces)
            # Preserve critical moving parts and glass across all levels.
            critical=part.startswith(('DOOR_','AXLE_','BOGIE_','ARTICULATION_','PANTOGRAPH_'))
            if not critical:
                if level=='LOW' and ((length<.16 and f>16) or (length<.085 and mat in ('STEEL','SILVER','DARK_STEEL'))):continue
                if level=='MEDIUM' and length<.052 and f>14:continue
                if level=='HIGH' and length<.025 and f>14:continue
                if level=='LOW' and mat in ('DISPLAY_CYAN','GOLD','LED') and length<.15:continue
            selected.append(mesh)
        if not selected:continue
        m=trimesh.util.concatenate(selected) if len(selected)>1 else selected[0]
        if not isinstance(m.visual,TextureVisuals) or not m.visual.material or m.visual.material.name!=mat:
            m.visual=TextureVisuals(material=MATS[mat])
        alt.add_geometry(m,geom_name=f'{level}_{part}_{mat}',node_name=f'{part}_{mat}',parent_node_name=part)
        tris+=len(m.faces)
    path=ROOT/'exports'/filename
    path.write_bytes(alt.export(file_type='glb'))
    inject_animations(path)
    print(level,'triangles:',tris,flush=True)
    return path,tris

LOD_HIGH=ROOT/'exports'/'VNW_Rheinliner_R7_High.glb'
LOD_MED=ROOT/'exports'/'VNW_Rheinliner_R7_Medium.glb'
LOD_HIGH,HIGHF=make_lod('HIGH',LOD_HIGH.name)
LOD_MED,MEDF=make_lod('MEDIUM',LOD_MED.name)
LOD_LOW,LOWF=make_lod('LOW','VNW_Rheinliner_R7_Low.glb')

# Blender conversion/editable source helper: opens generated GLB, saves .blend, optionally FBX.
blenderscript='''# Run with Blender: blender --background --python import_to_blender.py\nimport bpy\nfrom pathlib import Path\np=Path(__file__).resolve().parent\nbpy.ops.object.select_all(action="SELECT")\nbpy.ops.object.delete(use_global=False)\nbpy.ops.import_scene.gltf(filepath=str(p/"exports"/"VNW_Rheinliner_R7_Complete.glb"))\nfor ob in bpy.context.scene.objects:\n    if ob.type=="MESH":\n        ob.name=ob.name.replace("GEOM_", "VNW_")\n        if not ob.data.materials:pass\nbpy.context.scene.unit_settings.system="METRIC"\nbpy.context.scene.unit_settings.scale_length=1.0\nbpy.ops.wm.save_as_mainfile(filepath=str(p/"exports"/"VNW_Rheinliner_R7_Editable.blend"))\n# Exporting FBX may require fixing axis/armature mapping in UE.\n# glTF animation channels are imported as object actions where supported.\nbpy.ops.export_scene.fbx(filepath=str(p/"exports"/"VNW_Rheinliner_R7.fbx"),use_selection=False,apply_unit_scale=True,add_leaf_bones=False)\n'''
(ROOT/'import_to_blender.py').write_text(blenderscript)

stats={'vehicle':'VNW Rheinliner R7 (fictional, original exterior identity)',
       'status':'Reference-informed R3 geometrical revision; NOT photorealistic or production complete',
       'dimensions_m':{'overall_length':round(LENGTH,3),'width':WIDTH,'target_lowered_height':3.70,'roof_height':ROOF,'track_gauge':GAUGE},
       'sections':7,'module_lengths_m':LENGTHS,'section_centers_m':section_x,
       'door_leaves':len(DOOR_IDS),'door_openings':8,'door_layout':'right side 6 double, 2 single',
       'passenger_seats':SEATS,'powered_bogie_models':len(bogies),'axle_assemblies':len(WHEEL_IDS),
       'articulations':6,'mesh_faces':static_count,'lod_triangles':{'high':HIGHF,'medium':MEDF,'low':LOWF},'nodes':len(scene.graph.nodes),
       'animations':[a['name'] for a in GLTF.get('animations',[])],
       'models':['exports/'+OUTPUT.name,'exports/'+COLL.name,'exports/'+LOD_HIGH.name,'exports/'+LOD_MED.name,'exports/'+LOD_LOW.name],
       'reference_basis':'Manufacturer Basel Flexity: seven modules, 8 passenger doors (6 double + 2 single), 2300mm width; model is original fictional styling, not identical replica.',
       'limitations':['No full Blender .blend or FBX until Blender import helper is run','No real kinematic curve following/IK; demonstration object animation only','Door collision state needs to be driven by UE actor','No actual UE game collision/performance testing','Three geometry-stripped LOD variants are provided but UE cross-LOD animation/collision is not tested','Procedural materials are representative, not scan-quality','No manufacturer-endorsed IP clearance']}
(ROOT/'documentation'/'asset_manifest.json').write_text(json.dumps(stats,indent=2))
print(json.dumps(stats,indent=2),flush=True)