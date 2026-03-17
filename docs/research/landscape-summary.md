# Builkkit Research Summary

Research conducted 2026-03-17 across 11 parallel agents.

## Key Findings

### Comparable Projects

**MCP4IFC** (MIT, 2025) — LLM → MCP → Blender/Bonsai → IfcOpenShell
- 50-70 MCP tools, RAG for IfcOpenShell docs, visual feedback via screenshots
- Requires Blender running (heavy dependency)
- 40k token toolset (inefficient)
- Walls don't connect properly, weak self-correction
- GitHub: github.com/Show2Instruct/ifc-bonsai-mcp (26 stars)

**Text2BIM** (MIT, 2024) — Multi-agent LLM → Vectorworks
- 4 agents: Instruction Enhancer, Architect, Programmer, Reviewer
- 26 tool functions wrapping Vectorworks VectorScript APIs
- Solibri Model Checker for validation (BCF-based loop, up to 3 iterations)
- Architecture is platform-agnostic — only the 26 tools are Vectorworks-specific
- Could be adapted for IfcOpenShell by rewriting the tools
- GitHub: github.com/dcy0577/Text2BIM (85 stars)

**Zoo.dev Zookeeper** — Conversational CAD agent
- Tried having AI generate geometry directly → FAILED
- Pivoted to "LLM writes KCL code, engine executes"
- Plan-Act-Observe agentic loop with visual feedback (multi-angle snapshots)
- 5-retry limit, then asks for clarification
- $0.50/min for reasoning time
- Mechanical CAD focus, not architecture

### IfcOpenShell Creation Capabilities

- `ifcopenshell.api.geometry` provides parametric creation for: walls, slabs, doors, windows, columns, beams, railings
- `create_2pt_wall()` is the simplest wall creator (start, end, elevation, height, thickness)
- Door/window handling: create IfcOpeningElement → cut wall → create door/window → fill opening
- ShapeBuilder utility for arbitrary 2D profiles, extrusions, meshes
- IfcOpenHouse built a complete house with only 32 API calls in ~963 lines
- The creation pattern is highly repetitive and templatable
- Known limitation: no `add_roof_representation()` — roofs must be composed from slabs or meshes

### That Open Engine (Viewer)

- MIT license (components) + MPL-2.0 (web-ifc WASM parser)
- Three.js rendering, client-side WASM IFC parsing
- Built-in UI components: SpatialTree, ClassificationsTree, ElementProperties, Highlighter
- `npm create bim-app@latest` scaffolds a Vite + TypeScript project
- Static site deployment, no backend needed
- Fragments format for 10x faster loading than raw IFC
- ~12-15k npm downloads/week for web-ifc

### Australian NCC Compliance

- NCC is NOT machine-readable — no structured/computable version exists
- ABCB at "discussion paper" stage for digital transformation
- Residential NCC changes paused until mid-2029 (stable rule set)
- Competitors: UptoCode (PDF-based, not IFC), Archistar (planning, not deep NCC)
- Singapore CORENET took 20 years, Estonia 5+ years — huge gov't gap
- IDS (Information Delivery Specification) is the right standard for data quality gates
- IDS validates data exists; actual compliance logic must be separate
- Key automatable checks: fire separation, exit widths, room sizes, ceiling heights, insulation R-values
- Most AU residential IFC models have geometry but sparse properties

### AI Architecture Landscape

- Snaptrude (India, $14M Series A) — most advanced (LOD 300 from text)
- HouseDiffusion/ChatHouseDiffusion — diffusion models for floor plan generation
- Hypar — code-first generative design (closest philosophy, not open source)
- LLM + tool use is the validated approach (confirmed by Zoo.dev, MCP4IFC, Text2BIM)
- MCP protocol emerging as standard LLM-to-BIM interface

## Sources

All research agent transcripts preserved in temp files from this session.
Full paper references included in docs/spec.md.
