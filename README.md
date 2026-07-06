# Hogwarts — Procedural Blender Build

A full Hogwarts castle and its surrounding landscape — the crag, the lake, the
viaduct, the boathouse, the highlands and forest — built as a single Blender
scene, **entirely procedural and from scratch**: every mesh from primitives,
bmesh and geometry nodes, every material from shader nodes, no imported assets
and no external textures.

The whole scene was produced in **one autonomous run** by the **Fable 5** model
driving Blender through the [Blender MCP server](https://github.com/ahujasid/blender-mcp),
working only from the brief in [`Claude-Fable-5/SPEC.md`](Claude-Fable-5/SPEC.md).
Rendered in Cycles at 3840 × 2160, 1024 samples, denoised.

![Hero render](Claude-Fable-5/hero.png)

## Gallery

| | |
|---|---|
| [Aerial](Claude-Fable-5/angle_aerial.png) | [Boathouse](Claude-Fable-5/angle_boathouse.png) |
| [Viaduct](Claude-Fable-5/angle_viaduct.png) | [Detail — 01](Claude-Fable-5/detail_01.png) |
| [Detail — 02](Claude-Fable-5/detail_02.png) | [Detail — 03](Claude-Fable-5/detail_03.png) |

## What's in here

Everything lives under [`Claude-Fable-5/`](Claude-Fable-5/):

- **`hogwarts.blend`** — the final saved scene.
- **Renders** — `hero.png`, `angle_aerial.png`, `angle_boathouse.png`,
  `angle_viaduct.png`, and three close-up `detail_*.png` frames.
- **Build scripts** — the scene is generated in ordered passes:

  | Stage | Script |
  |-------|--------|
  | Terrain, crag, lake, mountains | `build_10_terrain.py` |
  | Castle assembly | `build_20_castle.py` |
  | Great Hall | `build_21_greathall.py` |
  | Central tower cluster | `build_22_towercluster.py` |
  | East keeps | `build_24_eastkeeps.py` |
  | Viaduct | `build_25_viaduct.py` |
  | Boathouse & cliff stair | `build_26_boathouse.py` |
  | Greenhouses | `build_27_greenhouses.py` |
  | Walls & terraces | `build_28_walls.py` |
  | Courtyard | `build_29_courtyard.py` |
  | Forest, moorland, scatter | `build_30_nature.py` |
  | Procedural materials | `build_40_materials.py` |
  | Lighting & atmosphere | `build_50_lights.py` |
  | Cameras | `build_60_cameras.py` |
  | Finalize | `build_70_finalize.py` |

  `hog_kit.py` and `hog_lib.py` hold the shared Gothic-detail kit and helper
  routines the stages draw on.

The Warner Bros. reference stills used as the visual brief are **not** included
here — they aren't ours to redistribute.

## Support

I make this kind of thing on the German YouTube brand **The Morpheus**. If you'd
like to support the work:

👉 **[patreon.com/c/themorpheus](https://www.patreon.com/c/themorpheus)**
