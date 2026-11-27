# Cinematic 3D V6: look-development upgrade

V6 builds on the actual V5 package. It preserves the V3/V4/V5 source and adds a new stage entry point.

## What changed

- **Water shader:** layered wave fields, micro-normal variation, Fresnel edge response, depth-aware absorption, caustic detail and directional specular glints. This is a more dimensional real-time surface, not ray-traced refraction or fluid simulation.
- **Finishing pass:** a restrained highlight shoulder and protected midtone contrast, layered after the existing V4 grade and V5 temporal-stability fixes.
- **Review tooling:** a V6 still renderer plus a contact-sheet and exposure/sharpness screening report. Metrics are diagnostic signals only, never a substitute for human review.

## Offline validation

```bash
python validate_v6.py
```

This checks Python syntax and source guards. It does not compile GLSL or render frames.

## Render comparison

Install `requirements-v5.txt` and use a working EGL/OpenGL 3.3 runtime:

```bash
python render_v5_stills.py --stage v3 --times 5,20,45,180,380,630,900,1080 --outdir review/v3
python render_v5_stills.py --stage v4 --times 5,20,45,180,380,630,900,1080 --outdir review/v4
python render_v5_stills.py --stage v5 --times 5,20,45,180,380,630,900,1080 --outdir review/v5
python render_v6_stills.py --times 5,20,45,180,380,630,900,1080 --outdir review/v6
python review_v6.py review/v6/*.png --out review/v6-report
```

Use identical timestamps and dimensions. Then render 5-10 second moving tests around fast camera arcs and inspect at full resolution. Check water highlights, shadow crawl, texture shimmer, clipped windows, dark detail, focus pulls, camera continuity and audio sync.

## Known limitations

- The current engine still uses its existing scene geometry, camera choreography, shadow map, FX buffers and material atlas.
- V6 does not add true ray-traced refraction, real fluid simulation, new scanned PBR maps, glass thickness, geometry subdivision or a new animation system.
- No full film render or audio replacement is performed by these tools.
- Shader compilation and visual output must be tested on the target machine; source validation alone is not visual approval.
