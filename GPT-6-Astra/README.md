# Hogwarts — The Black Lake at blue hour

Open `hogwarts.blend` in Blender 5.1 or later. The scene uses meters and opens with `Cam_Hero` active.

All geometry and shading were created procedurally in the connected Blender instance. The four supplied JPGs were studied visually and were never used as scene textures. No external assets, libraries, or downloads are required.

| Render | Camera |
| --- | --- |
| hero.png | Cam_Hero |
| angle_aerial.png | Cam_Aerial |
| angle_boathouse.png | Cam_Boathouse |
| angle_viaduct.png | Cam_Viaduct |
| detail_01.png | Cam_Detail_01 — layered spires and individual slate tiles |
| detail_02.png | Cam_Detail_02 — boathouse, slipways and moorings |
| detail_03.png | Cam_Detail_03 — Great Hall stonework and stained glass |

Delivery settings: Cycles, 3840 × 2160 at 100%, 1024 samples, adaptive sampling disabled, denoising enabled, 16-bit RGB PNG. The saved scene is configured for an OptiX GPU.

Collections organize the castle, carved architectural details, terrain, forest, viaduct, boathouse, greenhouses, lights, atmosphere, and cameras. Repeated conifers use shared meshes. Timeline markers label the shots without overriding the active render camera.

`process/` contains the incremental construction sources and render reviews. They document the build passes and revisions. `render_all.py` can be executed inside the open Blender scene to render the seven cameras again.
