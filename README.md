# Builkkit

**Talk to your building. Watch it build.**

An open-source AI-powered IFC design toolkit. Describe a building in natural language, and an AI agent creates it as a valid IFC model — viewable in the browser, editable by conversation, no Revit required.

## What This Is

Builkkit combines three things:

1. **CLI tools** (Python + IfcOpenShell) — create, modify, query, and validate IFC building models
2. **Component library** — parametric templates for walls, slabs, doors, windows, columns, roofs
3. **IFC viewer** (That Open Engine + Three.js) — browser-based 3D viewer with spatial tree, property panel, and visibility toggles

An AI agent (Claude) orchestrates the tools: it reasons about your intent, selects components, fills parameters, calls tools, validates output, and self-corrects on errors.

## Why

Every existing tool for AI-powered building design is locked behind commercial software:

| Tool | Requires | Cost |
|------|----------|------|
| Archie Copilot | Revit 2025 | $$$ |
| MCP4IFC | Blender + Bonsai | Heavy dependency |
| Text2BIM | Vectorworks | $$$ |
| Autodesk Forma | Autodesk subscription | ~$400/mo |

Builkkit requires **Python and a browser**. That's it. MIT licensed. No cloud backend.

## Architecture

```
User (natural language)
  → AI Agent (Claude) reasons about intent
    → CLI tools (IfcOpenShell) generate IFC geometry
      → Viewer (That Open Engine) renders in browser
        → User gives feedback
          → Agent modifies → repeat
```

The AI never does geometry. IfcOpenShell computes all geometry. The AI reasons, plans, and calls tools with parameters.

## Status

Early development. See [docs/spec.md](docs/spec.md) for the full specification.

## Tech Stack

- **IFC Engine:** IfcOpenShell 0.8.x (Python, LGPL)
- **Viewer:** That Open Engine (web-ifc WASM + Three.js, MIT/MPL-2.0)
- **Agent:** Claude (via Claude Code or API)
- **Language:** Python (CLI), TypeScript (viewer)

## Prior Art

This project builds on learnings from:
- [Archie Copilot](https://github.com/thebrownproject/archie-copilot) — proved natural language → building elements works (built a house from 6 prompts in Revit)
- [BuildSpec](https://github.com/thebrownproject/buildspec) — NCC compliance assistant for Revit
- [BuildBrain](https://github.com/thebrownproject/buildbrain) — IFC + PDF extraction and cross-validation

## License

MIT
