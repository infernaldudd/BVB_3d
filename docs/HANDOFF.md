# Handoff — BVB Basel Legacy Billetautomat (photoreal game asset)

**Project:** `infernaldudd/BVB_3d` (public, `main`)
**Source:** Three supplied photographic references (front, front-left, and rear/left-side/top) dated 2026-10-27.
**Deliverable:** Static 3D environment prop for Basel / GundeliTheftAuto / Helvetia, not an interactive ticket vending simulation.
**Status at handoff:** Reference-based textured 3D mesh built, critically rendered, revised, exported, and imported successfully. The repository includes a textured ~2 MB GLB and procedural Python builder. This handoff is intended to preserve detailed design and QA decisions.

## Reference observations to preserve

- Large vertical **green powder-coated painted steel** vending-machine cabinet, slightly bevelled edges and distinct depth; broad green sidewalls, green roof and back panel.
- **Pale aluminium U-shaped frontal fascia**, top squared and lower corners rounded; faded `Billette` / `Tickets` lettering above display near upper left.
- LCD screen is **dark glass inset into an actual deep recess** with several nested brushed-silver metal and black rubber frame layers, rather than a flat TV-sticker.
- Payment hardware near display's right side: chrome circular coin fitting; other circular pale tactile/contactless-looking components lower down. Do not pretend unspecified payment controls are verified.
- Lower front: long dark, recessed **ticket dispensing slot**, metallic rails/lips and cavity.
- Side transit network sheet under transparent/scuffed protective panel on **-X map-facing side**, surrounded by thin pale metal frame with mounting fasteners.
- Roof: paint chips/flaking, discoloured blue-green highlights, dirt and circular black top fitting.
- Base: brushed/dull metallic slab pedestal with upper/lower seam and scuffs, standing on pavement.
- Avoid random geometric gaps, missing holes, unrealistic planar black materials, or mirrored lettering.

## Geometry and coordinates

All dimensions **estimated from photos, not official BVB CAD/survey data**. Model unit metres, world +Z up, **-Y front**, **-X left/map side**. Nominal main cabinet 0.79 m width × 0.49 m depth × 1.075 m height, plinth 0.453 m high. Overall scene bounding box approx **0.8055 × 0.5275 × 1.53055 m**. The initial reference-led mesh has **76 distinct pieces / 3,868 triangles**, 14 material definitions and 21 embedded image assets. The full-res GLB is ~17.4 MB; repo-friendly embedded-PBR GLB is ~2 MB. A separately generated 384 px reduced-texture GLB was also validated at ~1.38 MB but should NOT replace a better-looking existing export without a visual texture comparison.

## Files and source-of-truth

- `assets/BVB_legacy_ticket_machine_PBR.glb` — game-ready optimized complete 3D model with embedded albedo/metallic-roughness/normal maps; preferred import.
- `source/build_bvb_ticket_machine.py` + `source/requirements.txt` — procedural reconstruction of geometry, generated textures and exports. Dependencies include Python, numpy, Pillow, shapely, trimesh.
- Full-fidelity working archive, generated during authoring: `BVB_Basel_Ticket_Machine_3D_PBR.zip` (45 MB), contains full-res GLB, OBJ+MTL, normal/albedo/metallic-roughness texture channels, 3 previews and QA report.
- Generated textures for green powdercoat, weathered green top, brushed aluminium face, pedestal brushed steel, machined dark metal, LCD glass, and illustrative map. Additional render reference files: `front.png`, `front_three_quarter.png`, `left_side.png`.
- Side transit map is **an original illustrative graphic, not an official route map or timetable**. Verify against official BVB map if exact location accuracy is needed.

## Existing harsh QA and completed fixes

1. Cabinet originally passed in front of LCD glass and blocked ticket slot: **rebuilt geometry with real openings**, giving separately modelled inset wall and actual dark cavity.
2. Side map was back-face invisible/mirrored in rendered preview: **fixed winding and UV orientation**.
3. Top weathered metal panel caused coplanar z-fighting/wedge: **separated layers and corrected overlapping geometry**.
4. `Billette Tickets` frontal text was upside down: **corrected UV vertical orientation**.
5. Neutral preview rendered metallic surfaces unphysically black: **used diffuse diagnostic lighting to judge shape**, retained correct metallic-roughness PBR setup in exported GLB.
6. Re-imported optimized GLB as a true scene successfully: **76 meshes, 3,868 triangles**, no missing parse errors.

## Critical unknowns and remaining work — do not claim perfection

- Need verified tape-measure/photogrammetry dimensions for exactly 1:1 scale.
- Fine lettering, actual label stickers, BVB historical hardware badges, official fare-network map design, coin slot dimensions and rear door hinge details are approximate.
- Reference photos are too low resolution to nail the subtle wear patterns on all faces. Increase texture fidelity only using references; avoid procedural noisiness.
- Need UE5.7 import/material inspection (PBR under realistic sun/sky and night exposure), normal-map handedness check, emissivity if display lit, real lighting evaluation, and material roughness variation at multiple distances.
- Need UE5 static mesh collision and LOD settings (possibly Nanite only if justified), pivot/ground anchoring, no floating geometry, optimized modular texture packing as game scale demands.
- If touching a model already accepted: **retain successful changes**, only make targeted revisions, and compare to reference at each iteration. Judge silhouette and proportions before details.

## Suggested next QA / acceptance gates

1. Compare front and side 3/4 perspective from same approximate camera field of view as the original photos. Prioritize front fascia shape and roof depth.
2. Inspect the screen, side sheet and ticket slot from a grazing light angle; no green bleed-through, interpenetrating surfaces or z-fighting.
3. Inspect ageing of aluminium and green paint in UE5.7's actual PBR renderer; avoid washed-out PBR and unnatural super-gloss.
4. Confirm high-resolution source and reduced version are **both** importable, with all texture channels and correct UV orientation; take close-up screenshots.
5. Provide machine-readable QA summary: scene bounds, mesh count, triangles, materials and map naming, visual issues fixed and known outstanding issues.

## Rebuild and import

```bash
python -m pip install -r source/requirements.txt
python source/build_bvb_ticket_machine.py
```

Expected regenerated outputs: `BVB_legacy_ticket_machine_PBR.glb`, OBJ/MTL, root textures, packed PBR maps, review images, `qa_model_report.json`. Use GLB for materials in Blender/UE; OBJ loses rich material fidelity. Verify engine orientation (+Z and -Y) and metres-to-centimetres import scale.

**Transparency:** No claim that every original object or official network-map label is present; photorealism is a direction and current output is a credible reference-based low-poly game prop, not a certified exact asset.