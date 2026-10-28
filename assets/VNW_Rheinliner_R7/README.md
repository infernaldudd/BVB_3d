# VNW Rheinliner R7 — Basel Flexity reference study (R6, WIP)

This directory is reserved for the **reference-informed, fictional VNW Rheinliner R7** tram asset. This is **not** an approved identical BVB Flexity model, nor a finished Unreal Engine 5.7 vehicle.

## Progress made

- Seven connected articulated sections and a roughly 42.86 m visual envelope.
- Corrected one-sided 8-entrance configuration: six double-leaf and two single-leaf doors (14 independently named leaves).
- Eight modeled axle assemblies over four bogies; mechanical curve-following is **not** yet tested.
- Rebuilt wheel-arch clearance and side skirting to reveal bogies.
- 82 passenger seat meshes in a 2+1 repeated layout (configuration is approximate, not manufacturer cabin CAD).
- Corrected open end-surface geometry; latest automated audit: **zero non-watertight mesh groups**, with the caution that intersections, cracks at moving joints and light leaks can still exist.
- Measured exported bounds approximately 42.86 × 2.3025 × 3.686 m. Compare to engineering reference 42.86 × 2.30 × 3.70 m.
- 40 actual-model render viewpoints: overall views, sides, roof, underneath, door sections, and interior.
- Four demonstration animation clips, a separate collision-proxy export and Low/Medium/High assets.

## Not finished / not validated

The cab front is still significantly too box-shaped compared with the real Basel Flexity; side styling, roof equipment, underside realism, articulation mechanics, doors (prototype slides instead of the Flexity-style outward-swing mechanism), PBR finish and driver controls remain approximate. Real-world reference images provided were not sufficient to validate all four orthographic directions, roof and underside. **No six successful full reference-revision loops have been completed.** The project should not be described as identical or photorealistic.

No Unreal Engine 5.7 in-game driving, player collision, door-state switching, curve-following or performance test has been completed. No manufacturer permission or guaranteed legal clearance exists; commercial game use should maintain an original vehicle identity and seek IP advice if a near-identical model is desired.

## Source and binary status on GitHub

**Successfully built, validated, and committed to this repository by GitHub Actions run [40772326376](https://github.com/infernaldudd/BVB_3d/actions/runs/40772326376).** Files now present at [assets/VNW_Rheinliner_R7/exports/](./exports/) include:

- `VNW_Rheinliner_R7_Complete.glb` (8.68 MB; complete current scene / prototype animation tracks)
- `VNW_Rheinliner_R7_High.glb`, `VNW_Rheinliner_R7_Medium.glb`, `VNW_Rheinliner_R7_Low.glb` (LOD variants)
- `VNW_Rheinliner_R7_Collisions.glb` (collision proxy)
- `textures/VNW_Oak_BaseColor_2K.png`, `VNW_Floor_BaseColor_2K.png`, `VNW_BrushedSteel_BaseColor_2K.png`
- `documentation/asset_manifest.json`, `documentation/build_validation.json`, `documentation/build_log.txt`

Reproducible generator: [source/VNW_Rheinliner_R7/generate_vnw_tram.py](../../source/VNW_Rheinliner_R7/generate_vnw_tram.py). Multi-view renderer: [render_40_inspection.py](../../source/VNW_Rheinliner_R7/render_40_inspection.py). Audit: [six_pass_audit.py](../../source/VNW_Rheinliner_R7/qa/six_pass_audit.py).

The **actual 40 rendered inspection images and contact sheets** are provided in the ChatGPT downloadable R6 review package, rather than committed as binaries to this GitHub repo. The model is not yet photorealistically identical to the real Flexity and was not validated in Unreal Engine; all QA failures below remain valid.

## Technical references

- Manufacturer Flexity Basel data: 7 modules, 8 doors (6 double + 2 single), nominal width 2,300 mm, nominal length 42.9 m.
- BVB engineering vehicle design guideline: `https://www.bvb.ch/wp-content/bvb/Dokumente/Infrastruktur/Projektierungsrichtlinie_Stand_Januar_2026.pdf`
- Source photographs have not been redistributed into this repo due to image copyrights.

**Status:** WIP / QA FAILED / NOT UE-VALIDATED / NOT COMMERCIALLY CLEARED FOR A NEAR-IDENTICAL REPLICA.
