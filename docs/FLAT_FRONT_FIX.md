# BVB Ticket Machine — Flat-front geometry repair (V2)

**Original issue:** the render showed shimmering/green speckle and several stacked black and metal bars at the ticket-delivery slot, with protruding pieces rather than a flat physical panel.

**Corrective rebuild:**
- Replaced four overlapping metal bezel bars with **one continuous, flat rectangular ring** around the ticket outlet.
- Removed the protruding 20 mm lower ticket lip, the internal feeder-guide overlay and all **17 small rib meshes** that made the slot busy and glitch-prone.
- Replaced the multi-depth outlet with **one matte-black recessed panel**, placed 8 mm behind the aluminium faceplate, plus a single thin inner guide.
- Moved the bezel to **1.5 mm above the flat aluminium faceplate**; the front faceplate itself projects only about **3 mm** beyond the main steel cabinet.
- Flattened the screen bezel, control discs and stainless pedestal seams to reduce flicker/black shadow bands.
- Kept real openings for both LCD and ticket outlet. Checks confirm neither opening is blocked by front-cabinet polygons, and front-plate triangles do not overlap in 2D.

**Files**
- `BVB_legacy_ticket_machine_flat_fixed_game.glb`: self-contained optimized PBR model recommended for game import.
- `BVB_legacy_ticket_machine_PBR.glb`: full-texture PBR GLB, same updated geometry.
- `BVB_legacy_ticket_machine.obj`, `material.mtl`, and referenced PNGs: fallback interchange.
- `build_bvb_ticket_machine.py`: procedural regeneration source.
- `QA_FLAT_FIX.json`: measured geometry checks.

**Import**: units are metres, +Z up, -Y front. Set game collision separately; do not merge coplanar UI surfaces with other decorations. For Unreal Engine, confirm materials import in **metallic/roughness** mode and enable imported normals. No official manufacturer dimensions were available; model proportions are photographic estimates. The map illustration is not an official BVB schematic.

**Caveat:** geometric overlap and aperture checks passed; physically based shading still needs a final review in the target game's rendering setup. This is a static prop, not a functional ticket vending machine.