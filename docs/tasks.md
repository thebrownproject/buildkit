# Spike Test — Tasks

## Task 1: IFC Generation Script (demo_house.py)

**Goal:** Python script that generates a simple house as a valid IFC4 file.

**Output:** `examples/demo_house.py` → generates `examples/demo_house.ifc`

**Elements to create:**
- IFC4 file with millimetre units
- Spatial hierarchy: IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey
- 4 perimeter walls (10m x 8m, 2700mm high, 200mm thick)
- 1 internal wall (dividing space at ~5m from west wall)
- 1 ground floor slab (10m x 8m, 200mm thick)
- 1 door in internal wall (820x2040mm, single swing left)
- 2 windows in north wall (1200x1200mm, 900mm sill height)
- 1 gable roof (2 angled slabs, 22.5° pitch)
- Basic materials (concrete, timber, steel)
- Named elements (Wall_North, Wall_South, etc.)

**Status:** [ ] Pathfinder → [ ] Builder → [ ] Reviewer

---

## Task 2: That Open Engine Viewer (v0.1)

**Goal:** Browser-based IFC viewer with drag-and-drop file loading.

**Output:** `viewer/` directory with working Vite + TypeScript project

**Features (v0.1 only):**
- 3D viewport with orbit/pan/zoom
- Drag-and-drop IFC file loading
- Grid floor
- Basic lighting/scene setup
- Loads and renders any valid IFC file

**No panels, no tree, no properties for v0.1.** Just: drop a file, see the model.

**Status:** [ ] Pathfinder → [ ] Builder → [ ] Reviewer

---

## Task 3: Integration Test

**Goal:** Verify the generated IFC file from Task 1 renders in the viewer from Task 2.

**Depends on:** Task 1 + Task 2 complete

**Test checklist:**
- [ ] File loads without errors
- [ ] Walls visible (4 perimeter + 1 internal)
- [ ] Wall corners (clean or acceptable overlap)
- [ ] Door opening visible in internal wall
- [ ] Door element visible inside opening
- [ ] Windows visible in north wall with openings
- [ ] Slab visible as floor
- [ ] Roof visible (two angled planes)

**Status:** [ ] After Task 1 + 2 complete
