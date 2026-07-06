# Hogwarts — Full Environment Build

Build **Hogwarts castle and its complete surrounding landscape** as a single
Blender scene, working through the Blender MCP tools.

Four reference images sit in this folder, next to this file — study all of
them before you model anything:

- `Hogwarts.jpg` — the Warner Bros. studio miniature, warm-lit, the densest
  view of the architecture.
- `Hogwarts2.jpg` — a moonlit cinematic view across the water, the strongest
  mood and atmosphere reference.
- `Hogwarts3.jpg` — a film-style composite showing the lake, the crag, and
  the boathouse stairs, the strongest composition reference.
- `Hogwarts4.jpg` — a daylight build on its rock, useful for silhouette and
  roof-material reference.

They define the target: not any one of them literally, but the castle they
all share — **synthesize the most beautiful version of it**.

This is a fully autonomous build. There will be no further messages, no
answers to questions, and no feedback until you are done — every decision is
yours. You have unlimited time and unlimited tool calls, and you may spawn
subagents or workflows however you see fit. The work is finished only when
you, acting as your own harshest art director, can look at the final renders
and honestly say that no change you know how to make would improve them. Do
not stop at "good". The bar is a frame that could ship as the hero concept
render of a AAA production.

## Hard constraints

- **This folder is your entire workspace.** Read the references from it and
  save every deliverable into it. Do not read from or write to anything
  outside this folder — no other directories, no downloads, no external
  resources. Blender itself and its documentation are the only exceptions.
- **Everything procedural, from scratch.** No imported assets, no
  asset-browser libraries, no external image textures (the reference JPGs
  are for your eyes only — never load them into the scene), no third-party
  add-ons. Every mesh is built from primitives, bmesh, or geometry nodes;
  every material from procedural shader nodes.
- **Render engine: Cycles.** Final renders at **3840 × 2160**, 100 % scale,
  **1024 samples**, denoising enabled. Everything else — color management,
  world, lights, camera — is your artistic call.
- You start from Blender's factory startup file; remove the default
  cube/light/camera as you see fit.

## The castle

A composite Gothic castle crowning a sheer rock promontory above a great
dark lake, silhouette instantly recognizable against the references.
Required elements:

- **The Great Hall** — a long Gothic hall with tall lancet windows set in
  bays, stepped buttresses between them, a steep gabled slate roof, and four
  slender corner turrets with conical caps and finials.
- **The central tower cluster** — the tallest structure, a main spire
  layered with attendant turrets, dominating the skyline.
- **A clock tower** with a readable clock face.
- **The grand viaduct** — a many-arched stone bridge on tall piers, striding
  across the gorge or lake inlet to the castle gates, lanterns along its
  parapet.
- **The boathouse** at the waterline, with a long switchback stair climbing
  the cliff face to the castle above.
- **Greenhouses** — glass-and-frame structures on a lower terrace.
- **Defensive walls, courtyards and terraces** stepping down the crag, so
  the castle grows out of the rock rather than sitting on it.
- **Hundreds of windows** — arched, mullioned, varied in size. Inhabited
  ones glow warm from within; the glow must vary in intensity and must not
  be uniform, so the castle reads as alive at a distance.
- **Full Gothic vocabulary** wherever the camera can see: pointed arches,
  window tracery, buttresses and flying buttresses, crenellated parapets,
  machicolations, string courses, corbels, pinnacles, spire finials.
- **No two towers identical.** Vary height, girth, roof shape, and detail.
  The massing is asymmetric yet balanced — study the references for how the
  vertical cluster on one side plays against the long horizontal of the
  Great Hall on the other.

Valued additions if you judge they strengthen the image (build them well or
not at all): a covered wooden bridge across a ravine, an owlery on an
outcrop, the Quidditch pitch with spectator towers and golden hoops in the
middle distance, a gamekeeper's hut with a smoking chimney at the forest
edge, a standing-stone circle, a small jetty, a distant railway viaduct.

## The surroundings

The castle is half the picture; the landscape carries the other half.

- **The crag** — stratified, near-vertical rock beneath the walls, plunging
  to the water; believable geology, not a smooth mound.
- **The lake** — dark, deep, wrapping the promontory. Physically plausible
  water: subtle wave displacement, sharp reflections of the lit windows and
  sky, near-shore transparency over rock.
- **Highlands backdrop** — layered mountain ridges receding with aerial
  perspective, silhouettes softening with distance.
- **The forest** — dense conifer forest with natural distribution (scatter
  with size, rotation and density variation; thicker in valleys, thinning
  at altitude and at the castle grounds' edge). Trees must hold up at the
  distance the cameras see them.
- **Moorland and paths** — rolling ground with exposed rock, and worn paths
  winding believably from the landscape up to the castle gates.

## Atmosphere and light

Choose **one** strong mood — moonlit night, deep dusk, or dramatic dawn —
and commit everything to it:

- Procedural sky matched to the mood (moon and stars if night; volumetric
  or believable clouds either way).
- **Low mist over the lake** and pooling in valleys — volumetrics that give
  the image depth without swallowing detail.
- **Warm–cool contrast**: window glow and lantern light warm against a cool
  ambient key. Lanterns along the viaduct, the boathouse stair, and the
  courtyards.
- Clear depth layering: foreground interest, midground castle, background
  ridges — each plane separated by light and atmosphere.

## Materials (all procedural)

- **Weathered stone** — per-region color variation as if quarried in
  batches, dirt streaking under sills and ledges, moss creeping into
  crevices on lower and wetter surfaces, edge wear on corners; bump/normal
  detail that survives a close-up.
- **Roofs** — blue-grey slate with tile-scale variation and weathering;
  verdigris copper accents on select turret caps.
- **Glass** — window panes with visible mullion structure; emissive warmth
  from inhabited rooms.
- **Water, rock, vegetation** — each with enough shader depth that no
  surface reads as flat default material anywhere a camera looks.

## Craft requirements

- **Real-world scale.** Model in meters; a door is ~2 m. Get proportions
  from the references, not from guesswork.
- **Clean scene organization**: collections (e.g. Castle / Terrain / Nature
  / Lights / FX / Cameras), meaningful object names, no orphan data.
- **Sound geometry**: correct normals, no z-fighting, no shading artifacts,
  polygon density spent where cameras actually look.
- **No placeholders anywhere.** Nothing default-grey, nothing floating,
  nothing unfinished visible from any delivered camera.

## Workflow you are expected to follow

Work in passes, and render-check after every pass — do not fly blind:

1. **Block-out** — mass the castle, crag, lake, mountains. Render. Compare
   the silhouette against all four references from the hero camera. Fix the
   massing until the silhouette alone says "Hogwarts".
2. **Architecture** — build out towers, halls, bridges, windows, Gothic
   detail. Render and inspect from multiple angles at each step.
3. **Landscape** — terrain sculpting, forest scatter, water, paths.
4. **Materials** — full procedural shading pass, checked in close-up.
5. **Light and atmosphere** — mood, volumetrics, window glow, final
   composition tuning per camera.
6. **Polish loop** — render, critique yourself brutally (silhouette,
   readability, scale cues, material realism, lighting depth, composition),
   fix the weakest thing, repeat. Leave the loop only when a full pass
   finds nothing left that you know how to improve.

Set up **at least four cameras** and keep them all working:

- `Cam_Hero` — low across the lake toward the castle (in the spirit of
  `Hogwarts3.jpg`), the money shot.
- `Cam_Aerial` — elevated three-quarter view showing the whole composition.
- `Cam_Boathouse` — close, water level, boathouse and stair with the castle
  towering above.
- `Cam_Viaduct` — from the viaduct or a courtyard, architecture filling the
  frame.

## Deliverables

Into **this folder** (the one containing this file), all renders Cycles
3840 × 2160 @ 1024 samples, denoised:

- `hogwarts.blend` — the final saved scene
- `hero.png` — from `Cam_Hero`
- `angle_aerial.png`, `angle_boathouse.png`, `angle_viaduct.png`
- `detail_01.png`, `detail_02.png`, `detail_03.png` — three close-ups of
  your choice that prove the material and geometry detail (e.g. a turret
  cap, the boathouse, a stretch of wall with windows at dusk-glow).

Save the `.blend` regularly during the run, not only at the end.

Take as long as it takes. Build the most beautiful Hogwarts you are capable
of.
