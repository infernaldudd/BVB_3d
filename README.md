# BVB Basel – Legacy Ticket Machine 3D Asset

Reference-led reconstruction based on three supplied photographs of a green BVB outdoor ticket machine in Basel, Switzerland.

## Download the real 3D model

**[BVB_legacy_ticket_machine_PBR.glb](assets/BVB_legacy_ticket_machine_PBR.glb)** — optimized **2 MB GLB**, 76 mesh components and 3,868 triangles. Embedded PBR metallic-roughness, base-color and normal textures. The green steel case, U-shaped aluminium face, recessed LCD and ticket outlet are all geometry, not a 2D image.

The full-resolution 17 MB GLB, OBJ/MTL with individually generated texture files, preview renders, and the original photography are retained in the originating ChatGPT delivery ZIP rather than duplicated in this repository.

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

Five defects identified during render review and fixed before the GitHub export:

- Green cabinet originally occluded the LCD and ticket opening → actual opening geometry cut into front.
- Left transit map was mirrored/backface-invisible → corrected mesh winding/UVs.
- Roof had intersecting coplanar triangles → eliminated z-fighting.
- Aluminium faceplate text mapped upside down → corrected vertical UVs.
- Direct unlit-metal previews were misleading → reviewed in neutral diffuse lighting while keeping PBR maps in the export.

**Limits:** dimensions are estimated from photographs, not scanned or manufacturer verified. The side network map is newly generated and illustrative, *not* an official BVB timetable. This is a static game asset with no functional ticket sale logic.