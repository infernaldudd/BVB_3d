# VNW Rheinliner R7 — R6 QA / comparison findings

Date: 2026-10-28. The **actual GLB geometry** was inspected using 40 diagnostic camera positions, with two contact sheets and a full camera manifest included in the ChatGPT downloadable package. This file is a QA summary, **not** proof that an identical Basel Flexity model has been completed or uploaded to GitHub.

| Stage | Result | Main observations |
|---|---|---|
| 1. Section and door count | PASS | 7 sections, 6 articulations, 4 bogies/8 axles, 8 right-side doorways (6 double, 2 single) with 14 uniquely named leaves |
| 2. Overall dimensions | PASS within small tolerance | Mesh bounds about 42.860 × 2.3025 × 3.686 m; nominal target 42.860 × 2.300 × 3.700 m |
| 3. Camera inspection coverage | PASS | 40 distinct model viewpoints, including nose, rear, roof, underside, both sides, inter-car joints, cabin |
| 4. Structural mesh topology | PASS, limited | 298 mesh groups inspected; no non-watertight mesh groups or zero-area triangles reported; **does not prove lack of moving-joint gaps or intersecting parts** |
| 5. Unreal Engine 5.7 gameplay, collision & animations | FAIL / NOT TESTED | Animation clips are demonstrations; rail-following/door mechanics, riding movement base and collision not tested |
| 6. Visual identity, hidden mechanics & commercialization | FAIL | Front too square; wrong detailed window/body treatment, rough roof and pantograph; no high-angle real reference; no guaranteed IP rights |

## Revisions completed

R2–R6 revisions focused on correct one-sided door layout, distinct central door pivots, additional 2+1 seat rows (82 total in prototype), opening bogie wheel bays, less intrusive roof HVAC housings, replacing teal by a greener color, installing shaped nose trim, sealing open front skin surfaces, reducing width overhang, and adjusting bounds.

### Severe remaining discrepancies

- **Cab front:** rounded windshield and lower nose are not nearly identical to the real train; existing geometry remains visibly rectangular.
- **Doors:** real vehicle uses electrically operated outward-swing doors while prototype uses sliding leaves.
- **Mechanical:** articulation, wheel/bogie steering, motor and pantograph shapes are simplified, not independently validated.
- **Seats:** repeated approximate 82 seat shells, not a verified BVB variant's 76/81/82 seat blueprint.
- **Rendering:** no complete physically calibrated PBR material stack (only generated 2K base-color images and numeric roughness/metalness).
- **Quality process:** six audit *categories* were checked, **not six successful complete reference-to-model optimization loops**.
- **Legal:** original fictional VNW styling should remain; an identical Flexity offered in a commercial game may require separate permissions.

## Current user-provided photo coverage

Actual photograph directions: two exterior three-quarter views and two interior views. No original orthographic front, roof-top or rear imagery was supplied. Model-only 40-angle renders must never be mislabeled as real vehicle photos.

This report explicitly keeps the project WIP until failures are addressed.
