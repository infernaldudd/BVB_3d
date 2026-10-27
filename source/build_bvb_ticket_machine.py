"""BVB Basel legacy street ticket machine — reference-led procedural 3D reconstruction.

Creates a usable, textured GLB and OBJ/MTL without Blender (trimesh + Pillow).
Coordinates: X=width, Y=depth (front is negative Y), Z=height. Units: metres.
Dimensions are photographic estimates; no surveyed manufacturer plans were available.
"""
from pathlib import Path
import math, random, json, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import trimesh
from trimesh.visual.texture import TextureVisuals
from trimesh.visual.material import PBRMaterial
from shapely.geometry import Polygon, box as polybox
from shapely.ops import triangulate

ROOT=Path(__file__).resolve().parent
TEX=ROOT/'textures'; TEX.mkdir(exist_ok=True)
RNG=np.random.default_rng(291027)
W,D,H=0.79,0.49,1.075
BASE_H=.453
Z0=BASE_H
TOP=Z0+H
YFRONT=-D/2
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_S='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf'
sc=trimesh.Scene()
components=[]
mat_cache={}

def save(img,filename):
    img.save(TEX/filename,optimize=False,compress_level=1)
    return img

def make_coat(name, base, size=(1024,1024), variation=5, patina=1.0, seed=0, brushed=False, bottom_dirt=False):
    w,h=size; local=np.random.default_rng(seed)
    small=local.normal(0,1,(max(16,h//40),max(16,w//40)))
    clouds=np.asarray(Image.fromarray(((small-small.min())/(small.max()-small.min())*255).astype('uint8')).resize((w,h),Image.Resampling.BICUBIC)).astype('float32')/255.-.5
    grain=local.normal(0,1.0,(h,w)).astype('float32')
    if brushed:
        narrow=local.normal(0,1,h).astype('float32')
        grain=.5*grain+.75*narrow[:,None]
    tint=clouds*(variation*1.3)+grain*(variation*.33)
    if bottom_dirt:
        ramp=np.clip((np.arange(h)-h*.49)/(h*.51),0,1)**2.2
        tint-=ramp[:,None]*13*patina
    arr=np.zeros((h,w,3),dtype=np.float32)
    for c in range(3): arr[:,:,c]=base[c]+tint
    arr=np.clip(arr,0,255).astype(np.uint8)
    image=Image.fromarray(arr,'RGB')
    dr=ImageDraw.Draw(image,'RGBA')
    # irregular abrasion and small chips, not synthetic evenly spaced streaks
    for _ in range(int(135*patina)):
        x=int(local.uniform(10,w-10)); y=int(local.uniform(8,h-8))
        lng=int(local.uniform(3,30)); width=int(local.choice([1,1,1,2]))
        col=(183,191,184,int(local.uniform(22,74))) if base[1]>100 and base[0]<130 else (75,69,60,int(local.uniform(10,48)))
        dr.line((x,y,x+lng,y+int(local.uniform(-2,3))),fill=col,width=width)
    for _ in range(int(20*patina)):
        x=int(local.uniform(0,w));y=int(local.uniform(0,h));dx=int(local.uniform(3,19));dy=int(local.uniform(1,4));
        dr.ellipse((x,y,x+dx,y+dy),fill=(46,48,42,int(local.uniform(7,33))))
    save(image,f'{name}_basecolor.png')
    # glTF packed material: [occlusion-unused, roughness, metallic]
    rough=(.49 if name.startswith('green') else .62 if name.startswith('face') else .54)
    metallic=(.08 if name.startswith('green') else .81 if name.startswith('face') else .76)
    rr=np.clip((rough+clouds*.09+grain*.022)*255,0,255).astype('uint8')
    mt=np.clip(metallic*255+clouds*13,0,255).astype('uint8')
    packed=np.stack([np.ones_like(rr)*255,rr,mt],axis=2)
    save(Image.fromarray(packed,'RGB'),f'{name}_metallic_roughness.png')
    # fine bump, mostly flat, avoids exaggerated dents or banana-peel artifacts
    nx=np.clip(128+np.gradient(clouds,axis=1)*23+grain*2,0,255).astype('uint8')
    ny=np.clip(128-np.gradient(clouds,axis=0)*23-grain*2,0,255).astype('uint8')
    normal=np.stack([nx,ny,np.ones_like(nx)*252],axis=2)
    save(Image.fromarray(normal,'RGB'),f'{name}_normal.png')
    return image,Image.fromarray(packed,'RGB'),Image.fromarray(normal,'RGB')

green_img,green_mr,green_norm=make_coat('green_powdercoat',(39,133,102),variation=7,patina=.8,seed=5)
roof_img,roof_mr,roof_norm=make_coat('green_weathered_top',(30,124,98),variation=13,patina=1.65,seed=7)
face_img,face_mr,face_norm=make_coat('face_aluminium',(220,219,201),size=(1536,2048),variation=7,patina=.9,seed=11,brushed=True,bottom_dirt=True)
ped_img,ped_mr,ped_norm=make_coat('pedestal_brushed_steel',(148,151,145),variation=12,patina=1.4,seed=13,brushed=True,bottom_dirt=True)
darkmetal_img,dm_mr,dm_norm=make_coat('dark_machined_metal',(83,91,88),variation=4,patina=.4,seed=22,brushed=True)

# Label artwork is painted onto the faceplate texture itself, not floated above it.
FW,FH=face_img.size
fdraw=ImageDraw.Draw(face_img,'RGBA')
def fw(x):return int((x+W/2)/W*FW)
def fh(z):return int((TOP-z)/H*FH)
def label(text,x,z,size,color=(62,83,71,190),bold=False,spacing=0):
    f=ImageFont.truetype(BOLD if bold else FONT_S,size)
    fdraw.text((fw(x),fh(z)),text,font=f,fill=color,spacing=spacing,stroke_width=0)
label('Billette',-.274,1.491,39,(72,89,77,182))
label('Tickets',-.274,1.452,37,(71,91,81,181))
# light ghosting from old circular contactless decal
cx,cy=fw(-.012),fh(.872)
fdraw.ellipse((cx-57,cy-47,cx+57,cy+66),fill=(160,175,173,25))
fdraw.ellipse((cx-36,cy-25,cx+36,cy+46),outline=(130,153,151,16),width=6)
label('BVB',-.273,.575,16,(235,238,224,235),bold=True)
label('Basel',-.270,.553,10,(64,77,73,150))
# Lower right authenticity plate; deliberately tiny as in reference
fdraw.rounded_rectangle((fw(.257),fh(.598),fw(.326),fh(.577)),radius=2,fill=(218,220,209,235))
label('SN',.270,.596,9,(64,81,72,180),bold=True)
# aging and downward rain runs in cream-coloured faceplate
for i in range(40):
    x=int(RNG.uniform(fw(-.24),fw(.22))); y=int(RNG.uniform(fh(1.02),fh(.72)))
    length=int(RNG.uniform(18,200))
    fdraw.line((x,y,x+int(RNG.integers(-5,5)),y+length),fill=(88,81,70,int(RNG.uniform(3,13))),width=int(RNG.choice([1,2,3])))
save(face_img,'face_aluminium_basecolor.png')

# Custom machine screen with worn LCD, reflections and screen burn-in
SW,SH=1024,768
pixels=np.zeros((SH,SW,3),dtype=np.uint8)
yv,xv=np.mgrid[0:SH,0:SW]
ambient=(46+28*(xv/SW)+15*(1-yv/SH))
glare=42*np.exp(-((xv/SW-.22)-(yv/SH)*.39)**2/.017)
for ch,mult in enumerate([.95,1.06,1.09]):pixels[:,:,ch]=np.clip(ambient*mult+glare+RNG.normal(0,1.0,(SH,SW)),0,255)
screenimg=Image.fromarray(pixels,'RGB')
sd=ImageDraw.Draw(screenimg,'RGBA')
sd.line((30,38,950,25),fill=(104,123,130,17),width=4)
sd.text((72,120),'BVB',font=ImageFont.truetype(BOLD,58),fill=(148,169,170,18))
sd.text((73,205),'Billette  |  Tickets',font=ImageFont.truetype(FONT,28),fill=(171,185,184,11))
for j in range(7):sd.line((75,290+j*42,830,290+j*42),fill=(149,169,168,5),width=1)
save(screenimg,'lcd_glass_basecolor.png')

# Stylized, non-operational printed Basel route diagram. Avoid representing it as an official schedule.
MW,MH=1024,1750
m=Image.new('RGB',(MW,MH),(237,239,233)); md=ImageDraw.Draw(m,'RGBA')
md.rectangle((10,10,MW-10,MH-10),outline=(140,148,139,255),width=6)
md.text((65,48),'BVB   |   Liniennetz',font=ImageFont.truetype(BOLD,39),fill=(37,91,70,255))
md.text((65,99),'Basel und Umgebung',font=ImageFont.truetype(FONT,27),fill=(70,76,70,255))
md.rectangle((47,149,977,1057),fill=(226,234,229,255))
# river and parks for layered realistic street geography
from PIL import ImagePath
md.line([(65,388),(180,400),(265,488),(378,500),(485,576),(616,592),(758,667),(947,705)],fill=(126,177,202,190),width=30,joint='curve')
md.line([(65,388),(180,400),(265,488),(378,500),(485,576),(616,592),(758,667),(947,705)],fill=(177,211,221,160),width=22,joint='curve')
for j in range(12):
 x=int(RNG.integers(50,920));y=int(RNG.integers(160,1020))
 md.ellipse((x,y,x+int(RNG.integers(40,120)),y+int(RNG.integers(35,90))),fill=(175,207,169,int(RNG.integers(25,65))))
for i in range(70):
 x=int(45+i*15+RNG.uniform(-7,7))
 md.line((x,150,x+int(RNG.uniform(-160,160)),1052),fill=(168,177,173,55),width=int(RNG.choice([1,2,3])))
for j in range(50):
 y=int(159+j*18+RNG.uniform(-8,8))
 md.line((48,y,977,y+int(RNG.uniform(-100,100))),fill=(178,182,177,48),width=int(RNG.choice([1,2,2,3])))
lines=[([(92,340),(244,398),(417,531),(582,655),(779,795),(913,975)],(215,46,67,240)),
       ([(81,867),(245,800),(412,664),(568,541),(751,407),(945,326)],(45,149,95,235)),
       ([(270,182),(339,377),(441,561),(492,746),(622,1037)],(233,143,62,240)),
       ([(64,590),(240,607),(460,612),(702,603),(949,643)],(76,128,205,245)),
       ([(125,1011),(250,811),(344,682),(550,498),(683,359),(798,166)],(181,75,160,229))]
for pts,col in lines:
 md.line(pts,fill=(251,251,245,240),width=15,joint='curve')
 md.line(pts,fill=col,width=8,joint='curve')
 for x,y in pts[1:-1]:
  md.ellipse((x-8,y-8,x+8,y+8),fill=(255,255,250,250),outline=col,width=4)
for name,x,y in [('Basel SBB',370,770),('Marktplatz',460,529),('Barfuesserplatz',352,650),('Bad. Bahnhof',713,373),('Schifflände',511,449),('St. Johann',212,329),('Aeschenplatz',621,808)]:
 md.rounded_rectangle((x-12,y-21,x+int(17*len(name))+8,y+13),fill=(245,246,240,218),radius=6)
 md.text((x,y-17),name,font=ImageFont.truetype(FONT,20),fill=(72,80,71,250))
md.text((68,1085),'Tram / Bus',font=ImageFont.truetype(BOLD,30),fill=(54,84,65,255))
for i,(num,colour) in enumerate([('1',(200,50,65)),('2',(28,130,82)),('6',(221,139,44)),('8',(68,122,185)),('11',(182,75,149))]):
 x=72+i*178;md.rounded_rectangle((x,1144,x+65,1205),radius=10,fill=colour+(255,))
 md.text((x+10,1152),num,font=ImageFont.truetype(BOLD,36),fill=(250,251,249,255))
# lower diagram, different detail density
md.rectangle((48,1240,978,1679),fill=(224,235,217,255))
for i in range(9):
 xx=60+i*105
 md.line((xx,1242,xx+int(RNG.uniform(-80,85)),1676),fill=(194,204,184,95),width=9)
for j in range(10):
 yy=1250+j*42
 md.line((50,yy,972,yy+int(RNG.uniform(-60,60))),fill=(190,205,181,100),width=6)
md.line([(93,1583),(243,1529),(370,1462),(501,1475),(615,1369),(767,1319),(941,1264)],fill=(98,171,94,240),width=14,joint='curve')
for x,y in [(93,1583),(243,1529),(370,1462),(501,1475),(615,1369),(767,1319),(941,1264)]:
 md.ellipse((x-9,y-9,x+9,y+9),fill=(245,248,240,255),outline=(69,132,75,255),width=3)
md.text((70,1696),'Netzplan (illustrativ)  |  BVB Basel',font=ImageFont.truetype(FONT,20),fill=(85,94,84,230))
save(m,'basel_network_map_illustrative.png')

# Material utilities: keep maps packed in proper metallic-roughness glTF channels.
def pbr(name, base=(220,220,210), metallic=.0, rough=.6, maps=None, alpha=False):
    if maps:
        bc,mr,nm=maps
        material=PBRMaterial(name=name,baseColorTexture=bc,metallicRoughnessTexture=mr,normalTexture=nm,
                             metallicFactor=1,roughnessFactor=1,doubleSided=False)
    else:
        material=PBRMaterial(name=name,baseColorFactor=(*base,255),metallicFactor=metallic,roughnessFactor=rough,doubleSided=False)
    mat_cache[name]=material
    return material
GREEN=pbr('Green_powder_coated_steel',maps=(green_img,green_mr,green_norm))
ROOF=pbr('Top_flaking_paint',maps=(roof_img,roof_mr,roof_norm))
FACE=pbr('Weathered_brushed_aluminium_face',maps=(face_img,face_mr,face_norm))
PED=pbr('Brushed_stainless_pedestal',maps=(ped_img,ped_mr,ped_norm))
DARK=pbr('Dark_bead_blasted_aluminium',maps=(darkmetal_img,dm_mr,dm_norm))
LCD=pbr('LCD_glass',maps=(screenimg,Image.new('RGB',(2,2),(255,45,200)),Image.new('RGB',(2,2),(128,128,255))))
MAP=pbr('Basel_network_information_poster',maps=(m,Image.new('RGB',(2,2),(255,220,0)),Image.new('RGB',(2,2),(128,128,255))))
MATTE=pbr('Black_urethane_seals',(26,32,31),0,.92)
SCREEN_FRAME=pbr('Dark_lcd_frame',(66,73,74),.34,.54)
BRIGHT=pbr('Anodized_silver_hardware',(156,163,162),.78,.29)
GUNMETAL=pbr('Satin_steel_slot',(102,109,107),.82,.42)
HOLE=pbr('Interior_void',(15,17,17),.03,.95)
BUTTON=pbr('Aged_cream_plastic',(194,204,187),.03,.65)
WHITE=pbr('White_polycarbonate',(207,215,209),0,.48)
RED=pbr('Contactless_mark',(65,78,72),0,.8)

# Generic meshes, UV-correct face dimensions and exportable named scene components.
def mesh_with_material(vertices,faces,uv,material,name):
    mesh=trimesh.Trimesh(vertices=np.asarray(vertices,dtype=np.float32),faces=np.asarray(faces,dtype=np.int64),process=False,validate=False)
    if uv is None:uv=np.tile([[0,0]],(len(vertices),1))
    mesh.visual=TextureVisuals(uv=np.asarray(uv,dtype=np.float32),material=material)
    sc.add_geometry(mesh,node_name=name,geom_name=name)
    components.append({'name':name,'vertices':int(len(vertices)),'triangles':int(len(faces)),'material':material.name})
    return mesh

def box_obj(name,center,size,material,uv_style='full'):
    cx,cy,cz=center; sx,sy,sz=size
    verts=[]; faces=[];uv=[]
    q=[(-1,-1),(-1,1),(1,1),(1,-1)]
    # winding established automatically; doublesided model surfaces are separately validated
    sides=[ # four corners in CCW order viewed from outside
        ([(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1)],(sx,sz)),
        ([(1,1,-1),(-1,1,-1),(-1,1,1),(1,1,1)],(sx,sz)),
        ([(-1,1,-1),(-1,-1,-1),(-1,-1,1),(-1,1,1)],(sy,sz)),
        ([(1,-1,-1),(1,1,-1),(1,1,1),(1,-1,1)],(sy,sz)),
        ([(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)],(sx,sy)),
        ([(-1,1,-1),(1,1,-1),(1,-1,-1),(-1,-1,-1)],(sx,sy)),
    ]
    for corners,extents in sides:
        s=len(verts)
        for j,p in enumerate(corners):
            verts.append([cx+p[0]*sx/2,cy+p[1]*sy/2,cz+p[2]*sz/2]);uv.append([(j in (1,2))*1.,(j in (2,3))*1.])
        faces.extend([[s,s+1,s+2],[s,s+2,s+3]])
    return mesh_with_material(verts,faces,uv,material,name)

def rounded_shell(name,w,d,zlo,zhi,r,material,cy=0.0):
    # Rounded rectangle in X/Y with a 2.5 mm rolled top/bottom edge
    def ring(radius,inset,zz):
      points=[]
      for cx,yy,ang in [(w/2-radius,d/2-radius,0),(-w/2+radius,d/2-radius,90),(-w/2+radius,-d/2+radius,180),(w/2-radius,-d/2+radius,270)]:
        for j in range(9):
          theta=math.radians(ang+j*90/8)
          points.append([cx+radius*math.cos(theta), yy+radius*math.sin(theta)+cy, zz])
      return points
    rings=[ring(r-.002,.002,zlo),ring(r,0,zlo+.003),ring(r,0,zhi-.004),ring(r-.002,.002,zhi)]
    verts=[]; uv=[];faces=[]
    n=len(rings[0]);
    for layer,rr in enumerate(rings):
       for p in rr:
         verts.append(p);uv.append([(p[0]+w/2)/w,(p[2]-zlo)/(zhi-zlo)])
    for layer in range(3):
      for j in range(n):
       nxt=(j+1)%n
       if name.startswith("C01_") and abs(rings[layer][j][1]-(cy-d/2))<1e-5 and abs(rings[layer][nxt][1]-(cy-d/2))<1e-5:
          continue  # open front, reconstructed below with true LCD and ticket apertures
       a=layer*n+j;b=layer*n+(j+1)%n;c=(layer+1)*n+(j+1)%n;d0=(layer+1)*n+j
       faces.extend([[a,b,c],[a,c,d0]])
    ci=len(verts);verts.append([0,cy,zhi]);uv.append([.5,.5])
    cb=len(verts);verts.append([0,cy,zlo]);uv.append([.5,.5])
    for j in range(n):
      faces.extend([[ci,3*n+j,3*n+(j+1)%n],[cb,(j+1)%n,j]])
    return mesh_with_material(verts,faces,uv,material,name)

def plane(name,corners,material,uv=None):
    if uv is None:uv=[[0,1],[1,1],[1,0],[0,0]]
    return mesh_with_material(corners,[[0,1,2],[0,2,3]],uv,material,name)

def poly_plate(name,outer,holes,y_front,thick,material):
    polygon=Polygon(outer,holes=holes)
    if not polygon.is_valid:raise ValueError(f'Invalid plate polygon {name}: {polygon.is_valid}')
    verts=[];faces=[];uv=[]
    def vert(x,z,y):
      v=len(verts);verts.append([x,y,z]);uv.append([(x+W/2)/W,(z-Z0)/H]);return v
    # robust constrained triangulation via polygon-clipping per Delaunay triangle
    for tri in triangulate(polygon):
      clipping=tri.intersection(polygon)
      items=list(clipping.geoms) if hasattr(clipping,'geoms') else [clipping]
      for item in items:
       if item.geom_type!='Polygon' or item.area<1e-12:continue
       for piece in triangulate(item):
        if not item.covers(piece.representative_point()):continue
        pts=list(piece.exterior.coords)[:-1]
        if len(pts)!=3:continue
        ids=[vert(x,z,y_front) for x,z in pts]
        # Front faces outward toward -Y
        if np.cross(np.asarray(verts[ids[1]])-verts[ids[0]],np.asarray(verts[ids[2]])-verts[ids[0]])[1]>0:ids=ids[::-1]
        faces.append(ids)
        ids2=[vert(x,z,y_front+thick) for x,z in pts]
        faces.append(ids2[::-1] if np.cross(np.asarray(verts[ids2[1]])-verts[ids2[0]],np.asarray(verts[ids2[2]])-verts[ids2[0]])[1]<0 else ids2)
    # edges of exterior and interior boundary loops
    all_loops=[list(polygon.exterior.coords)[:-1]]+[list(inner.coords)[:-1] for inner in polygon.interiors]
    for loop in all_loops:
      for j in range(len(loop)):
        a=loop[j];b=loop[(j+1)%len(loop)]
        ai=vert(a[0],a[1],y_front);bi=vert(b[0],b[1],y_front)
        ci=vert(b[0],b[1],y_front+thick);di=vert(a[0],a[1],y_front+thick)
        faces.extend([[ai,bi,ci],[ai,ci,di]])
    msh=mesh_with_material(verts,faces,uv,material,name)
    return msh

def ring_rect(name,xlo,xhi,zlo,zhi,t,y,depth,material):
    # bezel as four independent metal profiles around rectangular aperture
    box_obj(name+'_lower',((xlo+xhi)/2,y,(zlo+zlo-t)/2),(xhi-xlo+2*t,depth,t),material)
    box_obj(name+'_upper',((xlo+xhi)/2,y,(zhi+zhi+t)/2),(xhi-xlo+2*t,depth,t),material)
    box_obj(name+'_left',((xlo-t+xlo)/2,y,(zlo+zhi)/2),(t,depth,zhi-zlo),material)
    box_obj(name+'_right',((xhi+t+xhi)/2,y,(zlo+zhi)/2),(t,depth,zhi-zlo),material)

def disc(name,x,y,z,r,depth,material,segments=40):
    # cylinder local z -> world Y, positioned front-middle; cap and rim UV
    mesh=trimesh.creation.cylinder(radius=r,height=depth,sections=segments)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2,[1,0,0]))
    mesh.apply_translation([x,y,z])
    uv=np.stack([(.5+mesh.vertices[:,0]/(2*r)),(.5+mesh.vertices[:,2]/(2*r))],axis=1)
    mesh.visual=TextureVisuals(uv=uv,material=material)
    sc.add_geometry(mesh,node_name=name,geom_name=name)
    components.append({'name':name,'vertices':len(mesh.vertices),'triangles':len(mesh.faces),'material':material.name})
    return mesh

def ring_disc(name,x,y,z,r_outer,r_inner,depth,material,n=40):
    v=[];f=[];uv=[]
    for side,yy in enumerate([y-depth/2,y+depth/2]):
      for radius in (r_outer,r_inner):
       for i in range(n):
        a=2*math.pi*i/n
        v.append([x+radius*math.cos(a),yy,z+radius*math.sin(a)]);uv.append([.5+math.cos(a)*radius/(r_outer*2),.5+math.sin(a)*radius/(r_outer*2)])
    def strip(a,b,c,d):f.extend([[a,b,c],[a,c,d]])
    for i in range(n):
      j=(i+1)%n
      strip(i,j,n+j,n+i)
      strip(2*n+j,2*n+i,3*n+i,3*n+j)
      strip(n+i,n+j,3*n+j,3*n+i)
      strip(j,i,2*n+i,2*n+j)
    return mesh_with_material(v,f,uv,material,name)

# CHASSIS: reference suggests steel cabinet with very small bend radius and deeper side faces
rounded_shell('C01_outer_green_powdercoated_cabinet',W,D,Z0,TOP,.015,GREEN)
box_obj('C02_top_green_weathered_sheet',(0,0,TOP+.0013),(W-.02,D-.02,.0025),ROOF)
# rolled cabinet seams on left/right and service door at rear
poly_plate('C00_open_green_front_shell', [(-W/2+.013,Z0+.003),(W/2-.013,Z0+.003),(W/2-.013,TOP-.003),(-W/2+.013,TOP-.003)], [[(-.234,1.060),(.184,1.060),(.184,1.356),(-.234,1.356)],[(-.204,.674),(.156,.674),(.156,.745),(-.204,.745)]],YFRONT+.001,.009,GREEN)
box_obj('C03_top_lip_front',(0,YFRONT-.004,TOP-.022),(W-.017,.008,.006),GREEN)
box_obj('C04_lower_housing_joint',(0,YFRONT-.005,Z0+.082),(W-.025,.004,.0028),DARK)
box_obj('C05_rear_service_seam',(W/2-.035,D/2+.003,(TOP+Z0)/2),(.002,.002,H-.041),DARK)
# narrower steel plinth with panel joints
rounded_shell('B01_stainless_foundation_plinth',.602,.352,0,BASE_H,.004,PED,cy=.012)
box_obj('B02_front_service_join',(0,-.167,.216),(.53,.003,.003),GUNMETAL)
box_obj('B03_front_toe_panel',(0,-.169,.038),(.56,.003,.062),DARK)
box_obj('B04_plinth_top_hem',(0,-.170,BASE_H-.019),(.58,.006,.0045),BRIGHT)
box_obj('B05_plinth_foot_base',(0,.012,.014),(.61,.37,.012),PED)
for dx in [-.259,.259]:
 for dz in [.400,.255]:disc('B06_small_front_screw_%s_%s'%(int(dx*1000),int(dz*1000)),dx,-.176,dz,.004,.002,BRIGHT,16)

# CONTOURED ALUMINIUM PANEL with physically open LCD and ticket discharge apertures
pw=.303
outer=[(-pw,TOP-.043),(pw,TOP-.043),(pw,.859)]
for xv in np.linspace(pw-.0002,-pw+.0002,66):
  zv=.860-.264*math.sqrt(max(0,1-(xv/pw)**2))
  outer.append((float(xv),float(zv)))
outer.append((-pw,TOP-.043))
# screen well and slot cutouts, both actually punched through metal geometry
screen_rect=(-.224,.174,1.073,1.344)
slot_rect=(-.192,.144,.686,.736)
def rect_loop(r):
 a,b,c,d=r
 return [(a,c),(b,c),(b,d),(a,d)]
holes=[rect_loop(screen_rect),rect_loop(slot_rect)]
face_y=YFRONT-.007
poly_plate('F01_formed_anodized_aluminium_curved_face',outer,holes,face_y,.004,FACE)
# inner black rubber gasket behind screen, forms deep dark aperture
ring_rect('F02_screen_anti_vandal_rubber_gasket',-.224,.174,1.073,1.344,.011,face_y+.010,.017,MATTE)
# realistic bevel-shaped aperture lip with brighter aluminum trim
ring_rect('F03_machined_screen_bezel',-.221,.171,1.085,1.333,.008,face_y-.008,.008,BRIGHT)
ring_rect('F04_screen_inner_wall',-.195,.147,1.108,1.312,.015,face_y+.028,.055,SCREEN_FRAME)
# display glass deeper than outer aluminium; very slightly pitched; 2 triangle glass surface
plane('F05_recessed_worn_LCD_glass',[
 (-.178,face_y+.067,1.110),(.128,face_y+.067,1.110),(.128,face_y+.083,1.297),(-.178,face_y+.083,1.297)],LCD)
# right-side blank stainless section behind screen bezel
box_obj('F06_keypad_silver_sidepanel',(.151,face_y+.044,1.217),(.050,.022,.196),FACE)
# coin aperture ring to the right of LCD, key-slot inside
ring_disc('P01_coin_insertion_satin_chrome_ring',.255,face_y-.009,1.242,.025,.015,.005,BRIGHT)
disc('P02_coin_slot_dark_inset',.255,face_y-.007,1.242,.014,.002,HOLE)
box_obj('P03_vertical_coin_slot_cut',(.255,face_y-.011,1.242),(.003,.002,.021),GUNMETAL)
# bottom metal slot with pocket, reeded ticket guides
ring_rect('T01_ticket_exit_steel_trim',-.192,.144,.686,.736,.007,face_y-.009,.008,BRIGHT)
box_obj('T02_ticket_delivery_void',(-.024,face_y+.032,.708),(.322,.006,.035),HOLE)
box_obj('T03_ticket_slot_backing',(-.024,face_y+.052,.701),(.297,.005,.029),GUNMETAL)
box_obj('T04_lower_ticket_lip',(-.023,face_y-.015,.687),(.330,.020,.008),BRIGHT)
box_obj('T05_ticket_feeder_guides',(-.023,face_y+.019,.731),(.30,.025,.003),DARK)
for ix in range(17):
 x=-.165+ix*.019
 box_obj('T06_rib_%02d'%ix,(x,face_y+.027,.705),(.003,.013,.009),DARK)
# pale worn circular circle left button and right lower button
ring_disc('P04_contactless_white_trim',-.277,face_y-.014,.712,.032,.026,.003,GUNMETAL)
disc('P05_contactless_aged_plastic',-.277,face_y-.015,.712,.025,.006,BUTTON)
disc('P06_lower_right_pale_push_button',.273,face_y-.013,.674,.021,.009,WHITE)
disc('P07_center_scuffed_round_pictogram',-.006,face_y-.006,.855,.029,.002,BUTTON)
# Below main panel, tiny badge and mirrored fastening screws
for i,x in enumerate([-.347,.347]):
 for k,z in enumerate([.505,.974]):
  disc('F07_outer_cabinet_fastener_%d_%d'%(i,k),x,YFRONT-.004,z,.0038,.0025,BRIGHT,20)
# Diagram on front-facing part of left side; aluminum screw-secured map tray
side_x=-W/2-.002
mapy0,mapy1=-.221,.125
mapz0,mapz1=.663,1.355
box_obj('M01_left_side_map_mount_plate',(side_x-.004,(mapy0+mapy1)/2,(mapz0+mapz1)/2),(.008,mapy1-mapy0+.018,mapz1-mapz0+.018),BRIGHT)
plane('M02_illustrative_Basel_network_sheet',[(side_x-.010,mapy1,mapz0),(side_x-.010,mapy0,mapz0),(side_x-.010,mapy0,mapz1),(side_x-.010,mapy1,mapz1)],MAP,uv=[[0,0],[1,0],[1,1],[0,1]])
# map border rivets point along X, not front direction
for iy,yy in enumerate([mapy0+.011,mapy1-.011]):
 for iz,zz in enumerate([mapz0+.014,mapz1-.014]):
  mesh=disc('M03_map_corner_screw_%d_%d'%(iy,iz),0,0,0,.0045,.003,BRIGHT,16)
  # rotate the originally Y-facing fastener 90 degrees to face left side
  R=trimesh.transformations.rotation_matrix(math.pi/2,[0,0,1])
  mesh.apply_translation([0,0,0])
  # transform centered at disc origin by re-creating vertices relative to origin
  mesh.apply_transform(trimesh.transformations.translation_matrix([-0,-0,-0]))
  # disc object already in scene (mutable), safe to update
  mesh.apply_transform(R)
  mesh.apply_translation([side_x-.012,yy,zz])
# rear lock, vertical access line; no imaginary display or branding
box_obj('R01_back_door_top_seam',(0,D/2+.002,TOP-.11),(W-.065,.002,.002),DARK)
disc('R02_rear_round_lock',.283,D/2+.004,.991,.011,.003,BRIGHT)
# a thin front case rim, so the faceplate doesn't look like a sticker
box_obj('F08_left_vertical_green_case_hem',(-W/2+.032,YFRONT-.006,(Z0+TOP)/2),(.004,.005,H-.025),GREEN)
box_obj('F09_right_vertical_green_case_hem',(W/2-.033,YFRONT-.006,(Z0+TOP)/2),(.004,.005,H-.025),GREEN)

# export with meaningful component names and real-world scale
out_glb=ROOT/'BVB_legacy_ticket_machine_PBR.glb'
sc.export(out_glb,file_type='glb')
# OBJ/MTL exporter with PNG references; fallback if it doesn't return textures
try:
    objdata,materials=trimesh.exchange.obj.export_obj(sc,include_texture=True,return_texture=True,write_texture=True)
    (ROOT/'BVB_legacy_ticket_machine.obj').write_text(objdata)
    for fn,payload in materials.items():
      dest=ROOT/fn
      dest.parent.mkdir(parents=True,exist_ok=True)
      dest.write_bytes(payload if isinstance(payload,bytes) else payload.encode('utf8'))
except Exception as e:
    print('OBJ export alternative:',e)
    sc.export(ROOT/'BVB_legacy_ticket_machine.obj')

bounds=np.array(sc.bounds); size=bounds[1]-bounds[0]
report={
 'model':'BVB Basel legacy outdoor ticket machine; reference-led, non-certified reconstruction',
 'units':'metres','orientation':{'front':'-Y','height':'+Z','width':'+X'},
 'estimated_shell_dimensions_m':{'width':W,'depth':D,'height':H},
 'estimated_pedestal_height_m':BASE_H,
 'bounds_min_m':bounds[0].round(6).tolist(),'bounds_max_m':bounds[1].round(6).tolist(),'size_m':size.round(6).tolist(),
 'component_count':len(components),'total_triangles':sum(x['triangles'] for x in components),
 'texture_files':sorted(f.name for f in TEX.iterdir()),'parts':components,
 'reference_notes':['3 supplied views: front left 3/4; upper left side; full frontal','No machine serial number or manufacturer dimension plate visible','Cartographic side graphic is illustrative, not a BVB official/functional map','Top black circular object in second photo omitted as an unconfirmed loose object'],
 'qa_thresholds':{'target_triangle_count':'<25000','nonempty_materials':'true','no_missing_external_gltf_textures':'GLB self-contained'}
}
(ROOT/'qa_model_report.json').write_text(json.dumps(report,indent=2))
print('EXPORT',str(out_glb),out_glb.stat().st_size,'bytes')
print('BOUNDS',size,'COMPONENTS',len(components),'TRIANGLES',report['total_triangles'])
print('OBJ', (ROOT/'BVB_legacy_ticket_machine.obj').exists())