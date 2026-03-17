# Buildkit — Tasks

## Completed

- [x] Spike Test: demo_house.py (IFC generation)
- [x] Spike Test: Viewer v0.1 (drag-and-drop, 3D view)
- [x] Spike Test: Integration test (IFC renders in viewer)
- [x] Viewer v0.2: Spatial tree, property panel, highlighting
- [x] Viewer v0.2: Hover tooltip
- [x] Viewer v0.2: Dark/light theme toggle

---

## Task 4: Deploy Viewer to GitHub Pages

**Goal:** Live demo at https://thebrownproject.github.io/buildkit/ — anyone can visit, drag an IFC file, and view it.

**Steps:**
- Configure Vite for static build (`npm run build` in viewer/)
- Set up GitHub Actions workflow to build and deploy to gh-pages
- Include the demo_house.ifc as a downloadable sample on the page
- Test the deployed version works (WASM loading from CDN, worker, drag-and-drop)

**Key considerations:**
- Worker path changes in production (can't reference node_modules)
- Need to use CDN blob URL approach for the worker in production builds
- Base path may need to be `/buildkit/` for GitHub Pages subdirectory

**Status:** [ ] Pathfinder → [ ] Builder → [ ] Reviewer

---

## Task 5: ifc_query.py — CLI Model Inspector

**Goal:** Python CLI tool to inspect and summarise IFC models from the terminal.

**Output:** `cli-tools/ifc_query.py`

**Commands:**
```bash
python cli-tools/ifc_query.py --model examples/demo_house.ifc --summary
python cli-tools/ifc_query.py --model examples/demo_house.ifc --type IfcWall
python cli-tools/ifc_query.py --model examples/demo_house.ifc --element "Wall_North" --properties
python cli-tools/ifc_query.py --model examples/demo_house.ifc --storey "Ground Floor" --elements
```

**Output format:** JSON (for agent consumption) with optional `--pretty` flag for human reading.

**What it returns:**
- `--summary`: element counts by type, spatial hierarchy, materials, file schema
- `--type <IFC_CLASS>`: list all elements of that type with name, GUID, storey
- `--element <name_or_guid> --properties`: all properties, property sets, quantities for an element
- `--storey <name> --elements`: all elements contained in a storey

**Status:** [ ] Pathfinder → [ ] Builder → [ ] Reviewer

---

## Task 6: Visibility Toggles in Viewer

**Goal:** Hide/show elements by IFC type (walls, doors, windows, slabs, etc.) from the spatial tree panel.

**Implementation:**
- Use OBC.Classifier to group elements by entity type and by storey
- Use OBC.Hider to toggle visibility per group
- Add a "Classifications" panel section in the left panel with checkboxes per type
- Use BUIC.tables.classificationsTree() if available, or build custom toggle buttons

**Status:** [ ] Pathfinder → [ ] Builder → [ ] Reviewer

---

## Task 7: Phase 1.5 — ifc_place.py (First Creation CLI Tool)

**Goal:** CLI tool to create new IFC models and place wall elements. Proves the creation pipeline works.

**Output:** `cli-tools/ifc_create.py` + `cli-tools/ifc_place.py`

**ifc_create.py — Initialize a new model:**
```bash
python cli-tools/ifc_create.py \
  --output new_house.ifc \
  --project "My House" \
  --site "123 Main St" \
  --building "House" \
  --storeys "Ground Floor:0:2700"
```
Creates spatial hierarchy, sets millimetre units, writes minimal valid IFC4 file.
Returns JSON with GUIDs/names for all created entities.

**ifc_place.py wall — Place a wall:**
```bash
python cli-tools/ifc_place.py wall \
  --model new_house.ifc \
  --name "Wall_North" \
  --start 0,0 --end 10000,0 \
  --height 2700 --thickness 200 \
  --storey "Ground Floor"
```
Creates an IfcWall with geometry, assigns to storey, returns JSON with name + GUID.
Accepts millimetre values (converts to metres internally for IfcOpenShell).

**Key design decisions (from spec):**
- Names, not GUIDs — elements referenced by human-readable names
- Millimetres everywhere — matches Australian construction practice
- Functions first, CLI second — logic as importable Python functions, argparse as thin wrapper
- JSON output for agent consumption

**Status:** [ ] Pathfinder → [ ] Builder → [ ] Reviewer
