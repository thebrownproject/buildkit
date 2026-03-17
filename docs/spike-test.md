# Spike Test — Can We Build and View an IFC House?

**Goal:** Prove the core pipeline works in one afternoon.

Create a simple house with IfcOpenShell (Python), scaffold a browser viewer with That Open Engine, load the house, confirm it renders.

If this works, the project has legs. If it's painful, we know exactly where the problems are.

---

## What We're Building

A single-storey box house with:
- 4 perimeter walls (10m x 8m, 2700mm high, 200mm thick)
- 1 ground floor slab
- 1 internal wall (dividing the space)
- 1 door in the internal wall (820x2040mm)
- 2 windows in the north wall
- 1 gable roof (2 angled slabs)

This is IfcOpenHouse-level complexity, parameterised.

---

## Part 1: IFC Generation Script

**File:** `examples/demo_house.py`

**What it does:**
1. Creates IFC4 file with millimetre units
2. Sets up spatial hierarchy: IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey
3. Creates 4 perimeter walls using `create_2pt_wall()` or `add_wall_representation()`
4. Creates 1 internal wall
5. Creates 1 ground slab using `add_slab_representation()`
6. Creates door: IfcOpeningElement → void in wall → IfcDoor → fill opening
7. Creates 2 windows: same opening/filling pattern
8. Creates gable roof: 2 IfcSlab elements with `x_angle` for slope
9. Assigns basic materials (concrete slab, timber frame walls, steel roof)
10. Writes `examples/demo_house.ifc`

**Dependencies:** `pip install ifcopenshell numpy`

**Success criteria:** The output `.ifc` file opens in any IFC viewer (BIM Vision, FreeCAD, or our own viewer).

### Key Technical Questions This Answers

- Does `create_2pt_wall()` produce clean geometry?
- Do walls overlap at corners, or do we need clipping?
- Does the opening/void/filling chain work for doors and windows?
- Does the angled slab approach work for a gable roof?
- Are millimetre units handled correctly?
- How many lines of code does it actually take?

---

## Part 2: Viewer Scaffold

**Directory:** `viewer/`

**Setup:**
```bash
npm create bim-app@latest    # scaffolds Vite + TypeScript
# OR manual:
npm init -y
npm i @thatopen/components @thatopen/components-front @thatopen/fragments @thatopen/ui @thatopen/ui-obc web-ifc three vite typescript
```

**MVP viewer features (v0.1):**
1. 3D viewport with orbit/pan/zoom
2. Drag-and-drop IFC file loading (or file picker button)
3. Grid floor
4. Basic lighting

**That's it for v0.1.** No panels, no tree, no properties. Just: drop a file, see the model.

**v0.2 (if v0.1 works):**
- Spatial tree panel (left side) — `BUIC.tables.spatialTree()`
- Property inspector (right side) — `BUIC.tables.itemsData()`
- Element highlighting on click — `OBCF.Highlighter`
- Visibility toggles by element type — `OBC.Classifier` + `OBC.Hider`

### Key Technical Questions This Answers

- Does `npm create bim-app@latest` produce a working starter?
- Does web-ifc WASM load correctly in Vite?
- Does our generated `.ifc` file parse and render?
- How does the spatial tree look for our model?
- Do the walls, door, windows, roof show up correctly?
- Any visual artifacts at wall corners?

---

## Part 3: The Moment of Truth

1. Run `python examples/demo_house.py` → generates `examples/demo_house.ifc`
2. Run `cd viewer && npm run dev` → opens browser
3. Drag `demo_house.ifc` onto the viewer
4. **Does it render?**

### What We're Looking For

| Check | Pass | Fail |
|-------|------|------|
| File loads without errors | Model appears in viewport | WASM crash, parse error, blank screen |
| Walls visible | 4 perimeter + 1 internal wall | Missing walls, inverted normals, floating geometry |
| Wall corners | Clean or acceptable overlap | Huge gaps, walls not meeting |
| Door opening | Visible hole in internal wall | No opening, or opening in wrong place |
| Door element | Door visible inside opening | Door missing, floating in space |
| Windows | Visible in north wall with openings | Missing, wrong wall, no openings |
| Slab | Flat floor under everything | Missing, floating, wrong size |
| Roof | Two angled planes meeting at ridge | Missing, flat, wrong angle, gap at ridge |
| Spatial tree | Shows hierarchy (Site > Building > Storey > elements) | Flat list, missing elements |
| Click element | Properties appear | No properties, wrong element selected |

---

## Timeline

| Task | Estimate |
|------|----------|
| `demo_house.py` — basic walls + slab | 2-3 hours |
| `demo_house.py` — door + windows + roof | 2-3 hours |
| Viewer v0.1 — scaffold + drag-and-drop loading | 2-3 hours |
| Integration test — load generated IFC in viewer | 30 min |
| Viewer v0.2 — panels (if v0.1 works) | 1-2 days |

**Total: 1-2 days** for the spike. Half a day if things go smoothly.

---

## What Happens After

**If it works:** We have a working pipeline. Next steps:
- Parameterise `demo_house.py` (accept room count, dimensions, orientation)
- Extract wall/slab/door/window creation into `components/` library
- Build `ifc_query.py` for model inspection
- Deploy viewer to GitHub Pages as a live demo
- Start on `ifc_place.py` CLI tool

**If walls don't connect:** Investigate perimeter polyline approach or `IfcBooleanClippingResult` clipping. This is the known hard problem.

**If the viewer chokes:** Check WASM path config, Three.js version compatibility, or try loading a known-good IFC file (BuildingSMART sample files) to isolate whether the problem is our IFC or the viewer.

**If door/window openings fail:** Check `IfcRelVoidsElement` relationship chain, opening placement coordinates relative to wall. The IfcOpenHouse code is the reference implementation.

---

## Dependencies

**Python:**
```bash
pip install ifcopenshell numpy
# Optional: pip install mathutils (for ShapeBuilder, complex geometry)
```

**Node:**
```bash
npm create bim-app@latest
# OR see manual install above
```

**No other infrastructure needed.** No database, no cloud, no Docker. Python + Node + browser.
