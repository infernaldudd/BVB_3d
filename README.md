# BVB Basel – Legacy Ticket Machine 3D Asset

Reference-led reconstruction based on three supplied photographs of a green BVB outdoor ticket machine in Basel, Switzerland.

## Download the real 3D model

**[BVB_legacy_ticket_machine_PBR.glb](assets/BVB_legacy_ticket_machine_PBR.glb)** — **flat-front V2**, optimized **2.88 MB GLB**, **51 mesh components** and **3,598 triangles**. Embedded PBR metallic-roughness, base-color and normal textures. The green steel case, U-shaped aluminium face, recessed LCD and ticket outlet are all geometry, not a 2D image.

The full-resolution 17 MB GLB, OBJ/MTL and individual texture maps are included in the ChatGPT **Flat Fix V2** ZIP rather than duplicated in the GitHub repository. For the exact repair and checks, read [FLAT_FRONT_FIX.md](docs/FLAT_FRONT_FIX.md) and [QA_FLAT_FIX.json](qa/QA_FLAT_FIX.json).

## Rebuild high-resolution asset + texture maps

Run from `source/` on Linux or WSL (DejaVu font paths are Linux-style):

```bash
python -m pip install -r source/requirements.txt
python source/build_bvb_ticket_machine.py
```

This creates a full-resolution GLB, OBJ + MTL, regenerated texture files, and a quantitative QA report under `source/`.

## Import into Unreal Engine or Blender

The model is in **metres**, with +Z up, -Y forward/front and -X the side-map face. Estimated total envelope is about 0.81 × 0.53 × 1.53 m (including small hardware projections), with main painted shell ≈0.79 × 0.49 × 1.075 m on a ≈0.453 m plinth.

Import the **GLB** to preserve PBR maps. Generate game-specific LODs and collision separately.

## Visual critique and fixes

Initial visual defects corrected in V1:

- Green cabinet originally occluded the LCD and ticket opening → actual opening geometry cut into front.
- Left transit map was mirrored/backface-invisible → corrected mesh winding/UVs.
- Roof had intersecting coplanar triangles → eliminated z-fighting.
- Aluminium faceplate text mapped upside down → corrected vertical UVs.
- Direct unlit-metal previews were misleading → reviewed in neutral diffuse lighting while keeping PBR maps in the export.

**Limits:** dimensions are estimated from photographs, not scanned or manufacturer verified. The side network map is newly generated and illustrative, *not* an official BVB timetable. This is a static game asset with no functional ticket sale logic.
## Complete handoff and additional exports

- **[Technical handoff / next-steps and critical QA](docs/HANDOFF.md)** — reference observations, proportions, materials, corrections, remaining limitations and acceptance gates.
- **[QA model report](qa/qa_model_report.json)** — recorded dimensions, mesh counts, triangle counts, part names and material associations.
- **[Full OBJ interchange export](assets/obj/BVB_legacy_ticket_machine.obj)** with [MTL](assets/obj/material.mtl) and the 7 diffuse images in [assets/obj/](assets/obj/). For richer PBR materials, prefer GLB.
- **[Compact GLB variant](assets/BVB_legacy_ticket_machine_compact_PBR.glb)** — 1.38 MB, 384 px max embedded textures; same geometry (76 meshes, 3,868 triangles). Lower texture resolution only, not a geometric LOD.

The original full-resolution authored ZIP stays available in the originating ChatGPT conversation; the generator can regenerate all full-size textures and exports locally.

## Flat-front V2 — Oct 28, 2026

- Replaced intersecting ticket-trim prisms with one unified planar bezel.
- Eliminated 17 overlapping feeder ribs and a 20 mm front-projecting metal lip.
- Recessed the dark ticket cavity by 8 mm; bezel now projects 1.5 mm from the face.
- Flattened the screen bezel, buttons and pedestal seams.
- Re-imported and checked the optimized GLB: 51 named meshes, 3,598 triangles; no front-cabinet or fascia triangles obstruct the LCD or ticket slot. See [quantitative QA](qa/QA_FLAT_FIX.json).

**Verification limits:** numeric aperture and overlap checks pass, but inspect reflections and depth artifacts in Unreal Engine or Blender under your chosen materials and lighting setup.
