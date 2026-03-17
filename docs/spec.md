# Builkkit — AI-Powered IFC Design Toolkit

**Talk to your building. Watch it build.**

An open-source toolkit that lets AI agents design, modify, and validate IFC building models through natural language. No Revit. No license fees. Just Python, IfcOpenShell, and a smart agent.

---

## 1. Vision

Builkkit is the open-source bridge between natural language and IFC building models. A user describes what they want — "3-bed house, single storey, 180sqm, north-facing living" — and an AI agent reasons about the brief, selects parametric building components, calls CLI tools to generate IFC geometry, and renders the result in a browser-based viewer. The user gives feedback — "move that door 500mm left" — and the agent modifies the model.

This is **Archie Copilot without Revit**. Where Archie Copilot proved that natural language can drive building element creation inside Revit (generating IronPython code against the Revit API), Builkkit does the same thing against an open, portable stack: IfcOpenShell for geometry, That Open Engine for viewing, Claude for reasoning.

### Why Now

- **LLM + tool use is validated.** MCP4IFC (2025) and Text2BIM (2024) proved that LLMs can orchestrate IFC generation through code. Zoo.dev's Zookeeper proved that conversational CAD agents work — they tried having AI generate geometry directly, it failed; they pivoted to "LLM writes code, engine executes." That's our architecture.
- **IfcOpenShell's API is mature.** The `ifcopenshell.api.geometry` module provides parametric creation functions for walls, slabs, doors, windows, columns, beams, and railings. IfcOpenHouse built an entire house with only 32 API calls.
- **Model capabilities are 6-12 months from ready.** Current models can handle simple buildings. By early 2027, better spatial reasoning, longer context, improved tool use, and multimodal input (sketch → IFC) will make complex designs feasible. Build the scaffolding now.
- **The market is locked behind licenses.** Autodesk Forma ($400/mo), TestFit ($250/mo), Finch ($50/mo) — all closed source, all output to proprietary formats. An open-source IFC-native alternative has clear value.

### Design Principles

1. **LLMs never do geometry.** IfcOpenShell computes all geometry. The AI reasons about intent, selects components, fills parameters, and calls tools.
2. **Dumb tools, smart agent.** CLI tools are simple Python scripts with explicit inputs and JSON outputs. All intelligence lives in the agent's reasoning.
3. **IFC is the source of truth.** Everything reads and writes IFC. No intermediate formats, no proprietary lock-in.
4. **Open by default.** MIT license. No cloud backend required. Runs locally.

---

## 2. Prior Art & Landscape

### Direct Comparables

| Project | Approach | Strengths | Limitations |
|---------|----------|-----------|-------------|
| **Archie Copilot** (ours) | Claude → IronPython → Revit API | Proven: built a house from 6 NL prompts. Self-correcting loop (3 retries). | Requires Revit 2025 ($$$), Windows-only, .NET/IronPython complexity |
| **MCP4IFC** (2025, MIT) | Claude → MCP → Blender/Bonsai → IfcOpenShell | 50-70 MCP tools, RAG for IfcOpenShell docs, visual feedback via screenshots | Requires Blender running (heavy), 40k token toolset, walls don't connect properly, weak self-correction |
| **Text2BIM** (2024, open source) | Multi-agent LLM → Vectorworks API | 4 specialised agents (planner, coder, checker, etc.), rule-based model validation | Locked to Vectorworks, not IFC-native |
| **Zoo.dev Zookeeper** | LLM → KCL code → Zoo geometry engine | Conversational CAD agent, visual inspection, 5-retry loop, file ingestion | Mechanical CAD focus (not architecture), proprietary engine, $0.50/min |

### Commercial Landscape

| Tool | What | Price | Limitation |
|------|------|-------|------------|
| **Autodesk Forma** (ex-Spacemaker) | AI massing + environmental analysis | ~$400/mo | City/site scale only, Revit ecosystem |
| **TestFit** | AI site planning for multifamily | $250+/mo | Closed source, parcel-level focus |
| **Finch 3D** | Unit layout optimisation | $50/mo | Building envelope only, Revit plugin |
| **Hypar** | Code-first generative design | Free tier | Closest philosophy but not open source, not IFC-native |
| **Snaptrude** | Text → LOD 300 model | Startup | Most advanced AI design tool, but proprietary |

### Research

- **HouseDiffusion** (CVPR 2023) — Diffusion model generating vector floor plans from bubble diagrams. 67% improvement over House-GAN++.
- **ChatHouseDiffusion** (2024) — Extends HouseDiffusion with LLM natural language input.
- **Modular MCP Reference Architecture** (Jan 2026) — Proposes distributed AI agents across BIM workflow stages, each served by specialised MCP servers.

### Key Insight

The gap in the landscape is clear: **no open-source tool combines conversational AI + standalone IfcOpenShell (no Blender) + browser-based viewer + Australian market focus.** MCP4IFC is closest but requires Blender. Text2BIM requires Vectorworks. Archie Copilot requires Revit. Builkkit requires nothing but Python and a browser.

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                                                              │
│   ┌─────────────────┐    ┌────────────────────────────────┐  │
│   │   Chat Panel     │    │   IFC Viewer                   │  │
│   │   (natural lang) │    │   (That Open Engine / Three.js)│  │
│   │                  │◄──►│   - 3D model view              │  │
│   │   "Add a door    │    │   - Spatial tree panel         │  │
│   │    to the north  │    │   - Property inspector         │  │
│   │    wall"         │    │   - Element visibility toggles │  │
│   └────────┬─────────┘    └──────────────▲────────────────┘  │
│            │                             │                    │
│            │  prompt                     │  .ifc file         │
│            ▼                             │                    │
│   ┌────────────────────────────────────────────────────────┐  │
│   │              AI Agent (Claude)                          │  │
│   │                                                        │  │
│   │   1. Reasons about user intent                         │  │
│   │   2. Plans modifications (spatial logic, constraints)  │  │
│   │   3. Selects component templates + parameters          │  │
│   │   4. Calls CLI tools with explicit arguments           │  │
│   │   5. Validates output (reads back IFC, checks rules)   │  │
│   │   6. Self-corrects on error (up to 3 retries)         │  │
│   └────────┬───────────────────────────────────────────────┘  │
│            │  CLI calls                                       │
│            ▼                                                  │
│   ┌────────────────────────────────────────────────────────┐  │
│   │              CLI Tools (Python + IfcOpenShell)          │  │
│   │                                                        │  │
│   │   ifc_create.py    — create new IFC model from brief   │  │
│   │   ifc_place.py     — place element from template       │  │
│   │   ifc_modify.py    — modify existing element           │  │
│   │   ifc_query.py     — query model (elements, props)     │  │
│   │   ifc_validate.py  — validate against rules/IDS        │  │
│   │   ifc_export.py    — export to viewer format           │  │
│   └────────────────────────────────────────────────────────┘  │
│                                                              │
│   ┌────────────────────────────────────────────────────────┐  │
│   │              Component Library                          │  │
│   │                                                        │  │
│   │   templates/   — parametric element generators          │  │
│   │   types/       — pre-defined IfcTypeProducts            │  │
│   │   materials/   — material definitions                   │  │
│   │   profiles/    — structural cross-sections              │  │
│   └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Core Pattern: LLM Writes Parameters, Engine Computes Geometry

This is the same pattern proven by Zoo.dev, Archie Copilot, and MCP4IFC:

```
User: "Add a 900mm wide door to the north wall"
  ↓
Agent reasons:
  - North wall is Wall_N (GUID: 2x3abc...)
  - Wall is 200mm thick, 2700mm high
  - Door should be centred, 900x2100mm, single swing left
  - Need opening element + door + filling
  ↓
Agent calls:
  ifc_place.py --model house.ifc \
    --type door \
    --width 900 --height 2100 \
    --host-wall 2x3abc \
    --position 2500 \
    --operation SINGLE_SWING_LEFT
  ↓
CLI tool:
  1. Creates IfcOpeningElement (box: 900x2100x250)
  2. Cuts opening in wall via IfcRelVoidsElement
  3. Creates IfcDoor with parametric geometry (lining + panel)
  4. Fills opening via IfcRelFillsElement
  5. Returns JSON: {guid: "3y4def...", type: "IfcDoor", position: [2.5, 0, 0]}
  ↓
Agent:
  - Reads response, confirms success
  - Triggers viewer refresh
```

---

## 4. Component Library

The library wraps IfcOpenShell's `ifcopenshell.api.geometry` functions into parameterised, JSON-callable templates. Based on IfcOpenHouse patterns — every element follows the same 5-step creation flow:

1. `create_entity` → make the IFC object
2. `add_*_representation` → create geometry
3. `assign_representation` → link geometry to object
4. `edit_object_placement` → position it (4x4 matrix)
5. `spatial.assign_container` → put it in the correct storey

### Tier 1: Core Elements (MVP)

| Component | Parameters | IfcOpenShell Function | Geometry Type |
|-----------|-----------|----------------------|---------------|
| **Wall** | start, end, height, thickness | `create_2pt_wall()` / `add_wall_representation()` | ExtrudedAreaSolid |
| **Slab / Floor** | outline polygon, thickness | `add_slab_representation()` | ExtrudedAreaSolid |
| **Door** | width, height, host_wall, position, operation_type | `add_door_representation()` + opening/filling | Parametric (lining + panel) |
| **Window** | width, height, sill_height, host_wall, position, partition_type | `add_window_representation()` + opening/filling | Parametric (lining + mullions) |
| **Column** | profile (rect/circle), dimensions, height | `add_profile_representation()` | ExtrudedAreaSolid |
| **Beam** | profile (I/rect), dimensions, length | `add_profile_representation()` | ExtrudedAreaSolid |
| **Roof** | outline, slope_angle, thickness | `add_slab_representation(x_angle=...)` | ExtrudedAreaSolid (angled) |
| **Opening** | width, height, host_element, position | `add_wall_representation()` + `add_feature()` | ExtrudedAreaSolid (void) |

### Tier 2: Extended Elements

| Component | Parameters | Method |
|-----------|-----------|--------|
| **Stair** | rise, run, num_treads, width | Custom profile via `add_profile_representation()` |
| **Railing** | path, height, diameter | `add_railing_representation()` |
| **Footing** | width, length, depth | `add_wall_representation()` (box) |
| **Space** | boundary polygon, height, name | `IfcSpace` with `add_slab_representation()` |
| **Curtain Wall** | grid pattern, panel dimensions | Mesh-based |

### Tier 3: Furniture & Fixtures (Future)

Mesh-based (`add_mesh_representation()`) from a library of common objects.

### Geometry Complexity Boundary

Builkkit uses only **SweptSolid + Clipping** (IfcExtrudedAreaSolid + IfcBooleanClippingResult). This covers 90%+ of residential/commercial geometry. We explicitly do NOT attempt:
- NURBS / B-spline surfaces (organic shapes)
- Advanced B-rep (complex curved facades)
- CSG boolean trees (complex assemblies)

If complex geometry is needed, the escape hatch is `add_mesh_representation()` with pre-computed vertices/faces.

### Type System

Following IFC best practices and IfcOpenHouse patterns:
- Define `IfcWallType`, `IfcDoorType`, `IfcWindowType` etc. with shared properties and mapped representations
- Instances reference types — geometry is defined once, reused via `MappedRepresentation`
- A type catalog provides standard Australian sizes:
  - Door: 820x2040, 870x2040, 920x2040 (AS 1428.1 accessible: 950x2040)
  - Window: 600x600, 900x900, 1200x1200, 1800x1200
  - Wall: 90mm timber frame, 200mm concrete, 270mm cavity brick

---

## 5. CLI Tools

All tools follow the BuildBrain pattern: **explicit paths, JSON output, no auto-discovery**.

### `ifc_create.py` — Create New IFC Model

```bash
python ifc_create.py \
  --output house.ifc \
  --schema IFC4 \
  --project "My House" \
  --site "123 Main St" \
  --building "House" \
  --storeys "Ground Floor:0:2700,First Floor:2700:2700"
```

Creates the spatial hierarchy (IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey) and writes a minimal valid IFC file. Returns JSON with GUIDs for all created entities.

### `ifc_place.py` — Place Element from Template

```bash
python ifc_place.py \
  --model house.ifc \
  --type wall \
  --start 0,0 --end 10000,0 \
  --height 2700 --thickness 200 \
  --storey "Ground Floor" \
  --material "Concrete"
```

```bash
python ifc_place.py \
  --model house.ifc \
  --type door \
  --width 900 --height 2100 \
  --host-wall <GUID> \
  --position 2500 \
  --operation SINGLE_SWING_LEFT
```

Places an element using the component library. Handles the full creation flow (entity → geometry → placement → containment → opening/filling for doors/windows). Returns JSON with the new element's GUID and properties.

### `ifc_modify.py` — Modify Existing Element

```bash
python ifc_modify.py \
  --model house.ifc \
  --element <GUID> \
  --move 500,0,0

python ifc_modify.py \
  --model house.ifc \
  --element <GUID> \
  --set-property FireRating=2HR

python ifc_modify.py \
  --model house.ifc \
  --element <GUID> \
  --delete
```

### `ifc_query.py` — Query Model

```bash
python ifc_query.py --model house.ifc --summary
python ifc_query.py --model house.ifc --type IfcWall
python ifc_query.py --model house.ifc --element <GUID> --properties
python ifc_query.py --model house.ifc --storey "Ground Floor" --elements
```

Returns structured JSON. This is Builkkit's equivalent of BuildBrain's `ifc_extract.py`.

### `ifc_validate.py` — Validate Model

```bash
python ifc_validate.py --model house.ifc --rules basic
python ifc_validate.py --model house.ifc --ids compliance.ids
```

Checks:
- Schema validity (well-formed IFC)
- Spatial hierarchy completeness
- Element containment (everything assigned to a storey)
- Opening/filling integrity (doors/windows properly voided)
- Basic dimensional sanity (wall height > 0, door fits in wall, etc.)
- Optional: IDS (Information Delivery Specification) compliance checking

### `ifc_export.py` — Export for Viewer

```bash
python ifc_export.py --model house.ifc --format fragments --output model.frag
```

Converts IFC to That Open Engine's Fragments format for fast browser loading. Optional — the viewer can also load raw IFC files directly.

---

## 6. IFC Viewer

### Technology: That Open Engine

**Why That Open Engine:**
- MIT license (components) + MPL-2.0 (web-ifc parser) — commercially permissive
- Three.js rendering — mature, smooth WebGL
- Client-side WASM IFC parsing — no server needed
- Built-in UI components (Web Components via Lit) — spatial tree, property panel, visibility toggles
- Active development, ~12-15k npm downloads/week for web-ifc

**Architecture:**
```
@thatopen/ui-obc          Pre-built BIM UI (Web Components)
@thatopen/components       BIM tools (Hider, Classifier, Clipper, etc.)
@thatopen/components-front Browser-only components
@thatopen/fragments        Optimised binary geometry format + worker-based viewer
web-ifc                    C++/WASM IFC parser
Three.js                   WebGL rendering
```

### Viewer Features (MVP)

1. **3D Model View** — orbit, pan, zoom. Orthographic/perspective toggle.
2. **Spatial Tree Panel** — IFC hierarchy (Site → Building → Storey → Elements). Click to select, checkbox to toggle visibility. Uses `RelationsTree` UI component + `Classifier` + `Hider`.
3. **Property Inspector** — Click an element, see its IFC properties (type, materials, dimensions, property sets). Uses `ElementProperties` UI component.
4. **Element Visibility Toggles** — Hide/show by element type (all walls, all doors), by storey, or individually.
5. **Drag-and-Drop IFC Loading** — Drop an .ifc file on the viewer to load it.

### Viewer Features (Future)

- **Agent Integration** — Chat panel alongside viewer. Select elements in viewer → context for agent. Agent modifies → viewer auto-refreshes.
- **Cross-Validation Overlay** — Highlight elements flagged by BuildBrain's cross-validation (mismatches between IFC and PDF data).
- **Measurement Tools** — Distance, area, angle measurement via `MeasurementUtils`.
- **Clipping Planes** — Section cuts through the model via `Clipper`.
- **BCF Issues** — Create/view BIM Collaboration Format issues.

### Setup

```bash
npm create bim-app@latest  # scaffolds Vite + TypeScript project
# OR
npm i @thatopen/components @thatopen/fragments web-ifc three
```

Static site deployment — HTML + JS + WASM. No backend needed.

---

## 7. Agent Workflow

### Pattern: Plan → Act → Observe → Refine

Borrowed from Zoo.dev's Zookeeper and adapted for IFC:

```
1. PLAN    — Agent analyses brief, proposes spatial layout
2. ACT     — Agent calls CLI tools to create/modify elements
3. OBSERVE — Agent queries the model to verify (ifc_query.py)
4. REFINE  — Agent checks for errors, adjusts if needed (up to 3 retries)
5. PRESENT — Agent summarises what was built, viewer renders result
```

### Example: "Design me a 3-bed house"

```
Agent PLAN:
  "I'll create a single-storey, 3-bedroom house. Approximate layout:
  - Living/kitchen/dining: 45sqm (north-facing for light)
  - Master bedroom: 16sqm (with ensuite)
  - Bedroom 2: 12sqm
  - Bedroom 3: 10sqm
  - Bathroom: 6sqm
  - Laundry: 4sqm
  - Entry/hallway: 8sqm
  Total: ~180sqm footprint, 12m x 15m envelope"

Agent ACT:
  1. ifc_create.py --output house.ifc --storeys "Ground Floor:0:2700"
  2. ifc_place.py --type wall [12 perimeter + internal walls]
  3. ifc_place.py --type slab [floor slab, 12000x15000]
  4. ifc_place.py --type door [6 internal doors + 1 entry]
  5. ifc_place.py --type window [8 windows, north-facing larger]
  6. ifc_place.py --type roof [gable roof, 22.5° pitch]

Agent OBSERVE:
  ifc_query.py --model house.ifc --summary
  → 12 walls, 7 doors, 8 windows, 1 slab, 1 roof. All contained in Ground Floor.

Agent PRESENT:
  "I've created a 12m x 15m single-storey house with:
  - North-facing living area (45sqm) with 3 large windows
  - Master bedroom with ensuite (16sqm, east-facing)
  - Two bedrooms (12sqm, 10sqm) on the south side
  - Central hallway connecting all rooms
  - Gable roof at 22.5° pitch

  The model is ready to view. What would you like to change?"
```

### Self-Correction

When a CLI tool returns an error:
1. Agent reads the error message
2. Reasons about the cause (e.g., "door wider than wall — reduce door width or find a wider wall")
3. Calls the tool again with corrected parameters
4. Up to 3 retries, then asks the user for clarification

This mirrors Archie Copilot's proven self-correction loop and Zoo.dev's 5-retry pattern.

---

## 8. Phased Roadmap

### Phase 1: Foundation (Viewer + Query)

**Goal:** Working IFC viewer + basic CLI tools for querying existing models.

- [ ] That Open Engine viewer with: 3D view, spatial tree, property panel, visibility toggles, drag-and-drop loading
- [ ] `ifc_query.py` — read and summarise IFC models
- [ ] `ifc_validate.py` — basic schema and structure validation
- [ ] Project scaffolding: repo, docs, CI, example IFC files
- [ ] README with live demo (GitHub Pages static site)

**This phase alone is a useful open-source project** — a standalone, no-install IFC viewer.

### Phase 2: Creation (Component Library + Place/Modify)

**Goal:** AI agent can create and modify simple buildings.

- [ ] Component library: walls, slabs, doors, windows, columns, roofs
- [ ] `ifc_create.py` — initialise new IFC models
- [ ] `ifc_place.py` — place elements from templates
- [ ] `ifc_modify.py` — modify/move/delete elements
- [ ] Type catalog with Australian standard sizes
- [ ] Agent workflow integration (Claude Code skills or MCP server)

### Phase 3: Intelligence (Agent + Viewer Integration)

**Goal:** Conversational design loop — chat + viewer side by side.

- [ ] Chat panel integrated with viewer (web UI)
- [ ] Selection-as-context: click element in viewer → agent receives context
- [ ] Agent modifies model → viewer auto-refreshes
- [ ] Multi-turn design iteration with full conversation history
- [ ] Visual feedback: agent can "see" the model (screenshot/render)

### Phase 4: Validation & Compliance (Australian Market)

**Goal:** AI-assisted compliance checking against Australian building codes.

- [ ] NCC/BCA rule encoding as IDS specifications
- [ ] `ifc_validate.py` extended with NCC checks:
  - Fire safety (FRL, compartmentation, egress distances)
  - Accessibility (AS 1428.1 — door widths, ramp gradients, toilet dimensions)
  - Energy efficiency (NatHERS alignment, glazing ratios)
  - Structural basics (load path validation)
- [ ] BuildBrain integration — cross-validate IFC model against PDF specifications
- [ ] Compliance report generation

**Australian context:** No automated NCC/BCA compliance checking tool exists in the market. The ABCB is actively pursuing digitisation. Singapore's CORENET proved the concept. This is a significant market gap and a strong differentiator.

---

## 9. Tech Stack

| Layer | Technology | License | Purpose |
|-------|-----------|---------|---------|
| **IFC Engine** | IfcOpenShell 0.8.x | LGPL | Read, write, create IFC files |
| **Viewer** | That Open Engine (web-ifc + components) | MPL-2.0 / MIT | Browser-based 3D IFC rendering |
| **3D Rendering** | Three.js | MIT | WebGL rendering |
| **Viewer UI** | @thatopen/ui (Lit Web Components) | MIT | Tree panels, property panels, toolbars |
| **Agent** | Claude (via Claude Code or API) | — | Natural language reasoning + tool orchestration |
| **Data** | pandas, JSON | MIT | Structured data handling |
| **Validation** | buildingSMART IDS, python-mvdxml | MIT/LGPL | IFC compliance checking |
| **Language** | Python 3.10+ (CLI), TypeScript (viewer) | — | — |

### Dependencies

**Python (CLI tools):**
```
ifcopenshell>=0.8.0
numpy
mathutils          # for ShapeBuilder (optional, for complex geometry)
pandas             # for tabular output
```

**JavaScript (viewer):**
```
@thatopen/components
@thatopen/components-front
@thatopen/fragments
@thatopen/ui
@thatopen/ui-obc
web-ifc
three
```

---

## 10. Project Structure

```
builkkit/
├── docs/
│   ├── spec.md                    # This document
│   ├── research/                  # Research notes from agents
│   └── architecture.md            # Detailed architecture decisions
├── cli-tools/
│   ├── ifc_create.py              # Create new IFC model
│   ├── ifc_place.py               # Place element from template
│   ├── ifc_modify.py              # Modify existing element
│   ├── ifc_query.py               # Query model
│   ├── ifc_validate.py            # Validate model
│   └── ifc_export.py              # Export for viewer
├── components/
│   ├── templates/
│   │   ├── wall.py                # create_wall(start, end, height, thickness)
│   │   ├── slab.py                # create_slab(outline, thickness)
│   │   ├── door.py                # create_door(width, height, host_wall, ...)
│   │   ├── window.py              # create_window(width, height, host_wall, ...)
│   │   ├── column.py              # create_column(profile, height)
│   │   ├── beam.py                # create_beam(profile, length)
│   │   ├── roof.py                # create_roof(outline, slope)
│   │   └── opening.py             # create_opening(host, width, height, position)
│   ├── types/
│   │   ├── catalog.py             # Pre-defined IfcTypeProducts (AU standard sizes)
│   │   ├── profiles.py            # Standard structural profiles
│   │   └── materials.py           # Material layer sets
│   ├── spatial/
│   │   ├── project.py             # Project + site + building + storey creation
│   │   └── placement.py           # Coordinate system and placement utilities
│   └── properties/
│       ├── psets.py                # Standard property sets (Pset_WallCommon, etc.)
│       └── quantities.py          # Base quantities (Qto_WallBaseQuantities, etc.)
├── viewer/
│   ├── index.html                 # Static viewer page
│   ├── src/
│   │   ├── main.ts                # Viewer initialisation
│   │   ├── tree.ts                # Spatial tree panel
│   │   ├── properties.ts          # Property inspector
│   │   └── controls.ts            # Visibility toggles, tools
│   ├── package.json
│   └── vite.config.ts
├── examples/
│   ├── simple-house.ifc           # Generated example
│   └── simple-house.json          # Config that generated it
├── requirements.txt               # Python deps
├── CLAUDE.md                      # Agent instructions
└── README.md
```

---

## 11. Relationship to BuildBrain

Builkkit and BuildBrain are complementary:

```
BuildBrain (read/analyse)  ←→  Builkkit (create/modify)
         ↕                            ↕
    IFC + PDF files              IFC Viewer
         ↕                            ↕
    Extraction + QTO          Design + Validation
```

- **BuildBrain** reads existing IFC models and PDFs, extracts data, cross-validates, generates reports.
- **Builkkit** creates new IFC models from scratch, modifies existing models, validates against codes.
- **Shared viewer** — both projects can use the same That Open Engine viewer for visualisation.
- **Cross-validation loop** — BuildBrain extracts data from a PDF specification; Builkkit generates an IFC model; BuildBrain validates that the model matches the spec.

Future integration: a single web UI with chat, viewer, and both toolkits available to the agent. The agent decides whether to read (BuildBrain) or write (Builkkit) based on the user's intent.

---

## 12. Open Questions

1. **Claude Code plugin vs MCP server?** Builkkit could be a Claude Code plugin (like BuildBrain) with skills and CLI tools, OR an MCP server that any LLM client can connect to. MCP is more portable. Claude Code plugin is more proven (we've done it). Could support both.

2. **Viewer as separate project or integrated?** The viewer is useful standalone (pure IFC viewer, no AI). Could be its own repo/project, embedded into Builkkit for the design workflow. Leaning toward separate repo, shared via npm package.

3. **How to handle multi-storey?** Single-storey is straightforward. Multi-storey introduces: slab-to-slab alignment, stair placement, vertical element continuity (columns through floors). Needs careful spatial hierarchy management.

4. **Floor plan generation strategy?** Three options:
   - Agent reasons about spatial layout purely through text (current approach)
   - Integrate a floor plan generation model (HouseDiffusion) and convert output to IFC
   - Template-based: pre-defined layout patterns the agent configures

5. **How far to push compliance?** NCC compliance checking is a massive differentiator but also a massive scope. Start with basic dimensional checks, expand to fire safety and accessibility over time.

---

## 13. References

### Core Technologies
- [IfcOpenShell Documentation](https://docs.ifcopenshell.org/)
- [IfcOpenShell Geometry Creation](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html)
- [IfcOpenShell API Reference](https://docs.ifcopenshell.org/autoapi/ifcopenshell/api/geometry/index.html)
- [That Open Engine Docs](https://docs.thatopen.com/)
- [That Open Engine GitHub](https://github.com/ThatOpen)
- [web-ifc npm](https://www.npmjs.com/package/web-ifc)

### Comparable Projects
- [Archie Copilot](https://github.com/thebrownproject/archie-copilot) — AI Revit add-in (our prior work)
- [BuildSpec](https://github.com/thebrownproject/buildspec) — NCC compliance in Revit (our prior work)
- [MCP4IFC](https://github.com/Show2Instruct/ifc-bonsai-mcp) — LLM + MCP + Blender/Bonsai
- [Text2BIM](https://github.com/dcy0577/Text2BIM) — Multi-agent LLM → Vectorworks
- [Zoo.dev / Zookeeper](https://zoo.dev/) — Conversational CAD agent
- [IfcOpenHouse](https://github.com/cvillagrasa/IfcOpenHouse) — Reference IFC house generation

### Research
- [MCP4IFC Paper](https://arxiv.org/abs/2511.05533) — IFC-Based Building Design Using LLMs
- [Text2BIM Paper](https://arxiv.org/abs/2408.08054) — Multi-Agent Framework for BIM Generation
- [Modular MCP Architecture for BIM](https://arxiv.org/html/2601.00809v1)
- [HouseDiffusion](https://arxiv.org/abs/2211.13287) — Floor Plan Generation via Diffusion
- [ChatHouseDiffusion](https://arxiv.org/html/2410.11908v1) — LLM + Diffusion Floor Plans
- [AI for Floor Planning Survey (2025)](https://generativeaiandhci.github.io/papers/2025/genaichi2025_6.pdf)

### Standards
- [buildingSMART IDS](https://technical.buildingsmart.org/projects/information-delivery-specification-ids/)
- [IFC4 Documentation](https://ifc43-docs.standards.buildingsmart.org/)
- [NCC 2025](https://ncc.abcb.gov.au/)
- [AS ISO 19650 (Australian BIM Standard)](https://www.standards.org.au/)
