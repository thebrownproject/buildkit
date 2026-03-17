# Buildkit Spec — Consolidated Review

8 review agents evaluated the spec from different angles. This is the synthesis.

---

## CRITICAL: Rename the Project

**"Buildkit" is dead on arrival.** Docker BuildKit has 9,800+ GitHub stars and owns every search result. npm and PyPI `buildkit` are both taken. Both `.dev` and `.io` domains are unavailable.

**Suggested alternatives (all checked for conflicts):**
- **ifckit** — directly describes what it does
- **buildlens** — "lens into your building data"
- **sitelens** — construction "site" + data "lens"
- **setout** — Australian construction term for surveying/marking positions

Pick a new name before writing any code.

---

## CRITICAL: Rethink the Product Positioning

The builder review was the most important: **"This is a technology looking for a market, not a market problem looking for a solution."**

### The Wrong Demo
"Design me a 3-bed house" — any architect can sketch this in 15 minutes.

### The Right Demo
"Here's my site — 450sqm corner block in Blacktown, R3 Medium Density. Show me what I can fit."

The killer product is **rapid site feasibility**, not AI architecture:
- Pull planning controls for the LGA (FSR, height, setbacks)
- Show buildable envelope in 3D
- Compare options (dual-occ vs walk-up vs townhouses)
- Rough cost estimate ($X per sqm)
- Flag planning risks (overshadowing, solar access)

Developers spend $5-8k per manual feasibility study. Sites sell in days. LOD 200 is sufficient for feasibility. This is where the money is.

### IFC Reality Check
Australian residential builders don't use IFC. Everything is PDF. IFC should be the **internal format**, not the user-facing format. Accept PDF input (BuildBrain), generate IFC internally, output PDFs/visuals that builders can actually use.

---

## Spec Quality: Over-Engineered

> "An excellent research document masquerading as a build spec."

The spec is ~750 lines covering 4 phases for a project with 0 lines of code. Cut by 60%:
- Move Phase 4 (NCC compliance) to a separate document — different product, different customers
- Move Tier 2/3 component definitions out — don't define stairs before you can create a wall
- Move "future" viewer features out (BCF, measurement, clipping)
- Move prior art to `docs/research/` (already partially done)

---

## Phase-by-Phase Issues

### Phase 1 (Viewer + Query)
- **Split into two drops:** v0.1 = drag-and-drop + 3D view (2-3 days), v0.2 = panels (1-2 weeks)
- **Move `ifc_validate.py` to Phase 2** — you can't create models yet, so who are you validating?
- **Budget 2x for That Open Engine** — docs are patchy, WASM path issues
- **"Standalone IFC viewer" is not compelling** — there are dozens. It's foundation work.
- **Build `ifc_query.py` first** — fastest win, useful with BuildBrain immediately

### Phase 2 (Creation) — The Biggest Phase
- **Insert "Phase 1.5"** — one wall visible in the viewer validates the whole pipeline
- **Phase 2 is 2-4 months**, not a line item that looks equal to Phase 1's 2-4 weeks
- **IfcSpace is missing from Tier 1** — the agent reasons about rooms but can't represent them
- **Wall connectivity is the #1 hardest problem** — add `ifc_connect.py` for post-processing
- **Agent PLAN step has no tools** — pure LLM spatial reasoning will fail. Add a layout helper
- **No undo/rollback mechanism** — agent can corrupt the model on self-correction retries
- **Roof geometry is hand-waved** — no IfcOpenShell function exists. Support gable + shed only for v1

### Phase 3 (Agent + Viewer Integration)
- **Rename to "Web UI Integration"** — it's a frontend, not intelligence
- **"Chat panel" is hiding a separate web application** — needs its own architecture section
- **Adding chat breaks "no backend needed"** — Claude API needs a server proxy
- **Model auto-refresh needs WebSocket file watching** — requires a local server
- **Selection-as-context has zero technical detail** — unbuildable as specified

### Phase 4 (NCC Compliance)
- **Should be a separate project** — different product, different customers, different liability
- **Drop NatHERS and structural load path** — these are entire commercial products
- **IDS only checks data presence, not NCC rules** — spec contradicts itself on this
- **Most AU residential IFC models won't have the properties** needed for compliance
- **Position as helper, not authority** — "catch issues before your surveyor does"

---

## Technical Issues

### Naming/Referencing
- **GUIDs are terrible for LLM agents** — they'll truncate, transpose, hallucinate
- **Solution:** Dual addressing — every element gets a human-readable name AND a GUID
- CLI tools accept either: `--host-wall "Wall_North_1"` or `--host-wall 2x3YT$0P...`
- Auto-generate predictable names: `Wall_1`, `Door_1`, or descriptive via `--name`

### Coordinate System
- **Spec uses millimeters (2700, 10000) but IfcOpenShell defaults to meters** — `create_2pt_wall(end=[10000,0])` creates a 10km wall
- **Fix:** Set model units to millimeters in `ifc_create.py` via `unit.assign_unit(length="MILLIMETRE")`
- Matches Australian construction practice (nobody says "2.7 metres")

### Wall Connectivity
- MCP4IFC's biggest problem. Buildkit's spec is silent on it.
- **Recommended approach:** Perimeter walls as connected polyline (`--outline` parameter), internal walls butt-joined
- Consider `ifc_place.py walls --outline 0,0 10000,0 10000,8000 0,8000` for perimeter

### Door/Window Placement Edge Cases
- Door at wall intersection (T-junction)
- Door near wall end (minimum stub validation needed)
- Multiple openings per wall (overlap check needed)
- `--position` is ambiguous — from which end of the wall?
- Add `_validate_opening_placement()` pre-check

### CLI Tool Design
- **Use subcommands:** `ifc_place.py wall ...` not `ifc_place.py --type wall ...`
- **Add `--name` parameter** for human-readable element names
- **Add `--type-name`** to reference the type catalog ("Door_820x2040")
- **Write logic as importable Python functions first**, CLI as thin wrapper (Phase 3 needs this)
- **File modification:** `--model` modifies in-place? Add backup mechanism.

### Roof Types
- V1: gable (two angled slabs) + shed (one slab)
- Hip roof (very common in Australia) should be early v2
- Dutch gable, gambrel, valley — defer indefinitely

---

## What a Credible Demo House Requires

Minimum viable demo (equivalent to IfcOpenHouse but parameterized):

| Template | Count | Notes |
|----------|-------|-------|
| Walls | 8-12 | 4 perimeter (clean corners) + 4-8 internal |
| Slab | 1 | Ground floor |
| Doors | 5-7 | 1 entry + internal |
| Windows | 6-8 | North-facing larger |
| Roof | 2 slabs | Gable |

**What makes it "credible" vs "toy":**
1. Clean wall corners (not overlapping boxes)
2. Doors properly voided (actual openings, not floating rectangles)
3. Windows at correct sill heights
4. Named elements (Wall_North_Ext, not Wall_1)
5. At least basic property sets and materials

**Critical path:** `ifc_create.py` → `wall.py` (with corner handling) → `slab.py` → `door.py` + `window.py` (opening chain) → `roof.py` (angled slabs)

---

## Recommended Action Plan

### Immediate (before any code)
1. **Rename the project** — pick from ifckit, buildlens, sitelens, or research more
2. **Decide the product:** Is this "AI architect" (current spec) or "rapid site feasibility" (builder review)? These are different products.
3. **Cut the spec to Phase 1 only** — write a focused 1-2 page build plan

### Phase 1 (2-4 weeks)
1. Build `ifc_query.py` (reuse BuildBrain patterns)
2. Build viewer v0.1: drag-and-drop + 3D view (deploy to GitHub Pages)
3. Write a proof-of-concept script: 4 walls + slab + door + roof with IfcOpenShell
4. Confirm PoC renders in viewer
5. Build viewer v0.2: spatial tree + property panel + visibility toggles

### Phase 1.5 (1 week)
1. Implement `ifc_create.py` (spatial hierarchy, millimeter units)
2. Implement `ifc_place.py wall` (single element type only)
3. Verify: CLI creates wall → loads in viewer

### Phase 2 (2-4 months)
1. Remaining element types one at a time
2. Wall connectivity (perimeter polyline approach)
3. Door/window opening chain
4. Roof (gable only)
5. Agent integration
