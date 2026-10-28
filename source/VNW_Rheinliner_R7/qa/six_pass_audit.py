from pathlib import Path
import json, numpy as np, trimesh, re
R=Path(__file__).resolve().parents[1]
s=trimesh.load(R/'exports/VNW_Rheinliner_R7_Complete.glb',force='scene')
names=set(s.graph.nodes); nodes_mesh=list(s.graph.nodes_geometry)
meshcount=len(nodes_mesh); triangles=sum(len(s.geometry[s.graph.get(n)[1]].faces) for n in nodes_mesh)
door_nodes=sorted(n for n in names if re.fullmatch(r'DOOR_S\d{2}_D\d_[LR]_[AB]',n) is not None)
section_nodes=[n for n in names if n.startswith('SECTION_') and n.count('_')==1]
artic_nodes=[n for n in names if n.startswith('ARTICULATION_') and n.count('_')==1]
axles=[n for n in names if n.startswith('AXLE_') and n.count('_')==2]
# meshes that inherently contain open surfaces: vehicle glazing, cab window loft, bellows.
nonwatertight=[]; degenerate=0
for node in nodes_mesh:
    m=s.geometry[s.graph.get(node)[1]]
    if not m.is_watertight:nonwatertight.append(node)
    degenerate+=int(np.count_nonzero(m.area_faces<=1e-11))
views=json.loads((R/'qa/view_manifest.json').read_text())
pass_checks=[
 ('1 Engineering and body layout',{'sections':len(section_nodes),'articulations':len(artic_nodes),'axle_nodes':len(axles),'door_leaves':len(door_nodes),'door_openings':8,'side_doors':'right only'},len(section_nodes)==7 and len(artic_nodes)==6 and len(axles)==8 and len(door_nodes)==14),
 ('2 Dimensions and clearances',{'actual_extents_m':[round(float(v),4) for v in s.extents],'reference_target_m':[42.86,2.30,3.70],'y_excess_m':round(float(s.extents[1]-2.3),4)},bool(abs(s.extents[1]-2.3)<.005)),
 ('3 40 camera perspective coverage',{'views_captured':len(views),'render_images_exist':sum((R/v['file']).exists() for v in views)},len(views)==40 and all((R/v['file']).exists() for v in views)),
 ('4 Surface/gap topology',{'mesh_groups':meshcount,'open_surface_meshes':len(nonwatertight),'first_open_surfaces':nonwatertight[:12],'zero_area_triangles':degenerate},len(nonwatertight)==0 and degenerate==0),
 ('5 Motion and collision readiness',{'animation_clips':'demonstrations only','collision':'separate static proxies; UE test not run','section_curve_kinematics':'not tested'},False),
 ('6 Reference and commercialization',{'silhouette':'not identical; front too squared and side composition differs','roof_top_reference':'no photo-backed top geometry validation','rear_reference':'insufficient photos','ip_status':'not cleared for identical commercial replica'},False),
]
result={'status':'FAIL — work in progress; not photoreal / not identical / not UE validated', 'six_distinct_qa_stages_not_six_completed_model_revisions':True,'triangle_count':triangles,'checks':[]}
for title,details,pass_check in pass_checks:
 result['checks'].append({'stage':title,'result':'PASS' if pass_check else 'FAIL','details':details})
(R/'qa'/'six_pass_audit.json').write_text(json.dumps(result,indent=2))
with (R/'qa'/'six_pass_audit.md').open('w') as o:
 o.write('# Six-stage geometry and visual audit — R3\n\n**STATUS: FAILED — remaining visual, geometry and gameplay issues; not approved for commercial shipping.**\n\n')
 o.write('The six checks are separate QA stages on the latest revised model, **not** six completed revision-and-rerender loops. Forty actual-mesh renders are stored in `qa/40_views`.\n\n')
 for x in result['checks']:
  o.write(f'## {x["stage"]}: {x["result"]}\n\n')
  for k,v in x['details'].items():o.write(f'- {k}: {v}\n')
  o.write('\n')
 o.write('### Critical remaining corrections\n\n- Replace rectangular end caps with properly lofted welded nose, rounded corners and exact manufacturer-style window/lamps.\n- Reduce side trim overhang to 2.300 m when clearances permit.\n- Seal open cab windshield and various one-sided surfaces; run game collision and light-leak tests.\n- Check door mechanisms (outward-swing vs model sliding), bogie skirts, articulation watertightness and pantograph geometry against appropriate licensed references.\n- Correct roof and underside using authentic high-angle references.\n- Confirm seat count and layout against precise vehicle subtype; early supplier brochure listed 81/82, updated BVB project document lists 76.\n- No automatic claims of legal clearance, visual identity, driving or UE5.7 runtime validation.\n')
print(json.dumps(result,indent=2)[:6500])