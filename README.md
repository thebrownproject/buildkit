# Buildkit

**Talk to your building. Watch it build.**

Open-source toolkit for creating, viewing, and querying IFC building models with AI. Describe what you want in natural language, an AI agent calls CLI tools to generate IFC geometry, and a browser viewer renders the result. No Revit. No license fees.

**[Live Demo](https://thebrownproject.github.io/buildkit/)** — drag any IFC file onto the viewer

---

## How it works

```
Claude (AI agent — reasons about intent, selects components, fills parameters)
    │
    ├── ifc_create.py      Create new IFC model with spatial hierarchy
    ├── ifc_place.py       Place elements (walls, doors, windows, slabs)
    ├── ifc_query.py       Inspect model — summary, properties, element lists
    │
    └── Viewer             Browser-based 3D viewer with spatial tree,
                           property panel, visibility toggles, theme toggle
```

The AI never does geometry. IfcOpenShell computes all geometry. The AI reasons, plans, and calls tools with parameters.

---

## Viewer

Browser-based IFC viewer built on That Open Engine (Three.js + WASM). Drag-and-drop any IFC file.

- 3D viewport with orbit, pan, zoom
- Spatial tree — IFC hierarchy with search
- Property inspector — click any element to see its data
- Visibility toggles — hide/show by element type
- Hover tooltip — element name + IFC type
- Dark/light theme toggle

## CLI Tools

All tools output JSON. All dimensions in millimetres.

```bash
# Create a new model
python cli-tools/ifc_create.py \
  --output house.ifc \
  --project "My House" \
  --storeys "Ground Floor:0:2700"

# Place a wall
python cli-tools/ifc_place.py wall \
  --model house.ifc \
  --name "Wall_North" \
  --start 0,0 --end 10000,0 \
  --height 2700 --thickness 200 \
  --storey "Ground Floor"

# Inspect the model
python cli-tools/ifc_query.py --model house.ifc --summary
python cli-tools/ifc_query.py --model house.ifc --type wall
python cli-tools/ifc_query.py --model house.ifc --element "Wall_North" --properties
```

## Tech Stack

**IFC Engine:** IfcOpenShell 0.8.x (Python, LGPL) <br>
**Viewer:** That Open Engine · web-ifc WASM · Three.js (MIT/MPL-2.0) <br>
**Agent:** Claude (via Claude Code or API) <br>
**Language:** Python (CLI tools), TypeScript (viewer)

## Setup

```bash
# CLI tools
pip install ifcopenshell numpy

# Viewer
cd viewer && npm install && npm run dev
```

## Project Structure

```
buildkit/
├── cli-tools/
│   ├── ifc_create.py          Create new IFC models
│   ├── ifc_place.py           Place elements (wall subcommand)
│   └── ifc_query.py           Query and inspect models
├── viewer/
│   ├── src/main.ts            Viewer application
│   └── public/demo_house.ifc  Sample model
├── examples/
│   └── demo_house.py          Generate a demo house from scratch
└── docs/
    ├── spec.md                Full specification
    ├── spike-test.md          Pipeline validation plan
    └── research/              Landscape research
```

## Prior Art

This project builds on learnings from:
- [Archie Copilot](https://github.com/thebrownproject/archie-copilot) — proved natural language → building elements works (built a house from 6 prompts in Revit)
- [BuildSpec](https://github.com/thebrownproject/buildspec) — NCC compliance assistant for Revit
- [BuildBrain](https://github.com/thebrownproject/buildbrain) — IFC + PDF extraction and cross-validation

## License

MIT
