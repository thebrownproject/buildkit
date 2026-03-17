"""
ifc_create.py -- Create a new IFC4 file with spatial hierarchy and millimetre units.

Usage:
    python cli-tools/ifc_create.py \
      --output new_house.ifc \
      --project "My House" \
      --site "123 Main St" \
      --building "House" \
      --storeys "Ground Floor:0:2700"

    Multiple storeys (comma-separated):
      --storeys "Ground Floor:0:2700,First Floor:2700:2700"

Storey format: "Name:elevation_mm:height_mm"

Output: JSON to stdout with project structure and GUIDs.
"""

import argparse
import json
import sys

import ifcopenshell
import ifcopenshell.api
import numpy as np


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def placement_matrix(origin):
    """Build a 4x4 placement matrix from an origin point."""
    m = np.eye(4)
    m[0:3, 3] = origin
    return m


def parse_storey_defs(storeys_str):
    """Parse storey definitions from 'Name:elevation_mm:height_mm' comma-separated string."""
    defs = []
    for entry in storeys_str.split(","):
        parts = entry.strip().split(":")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid storey format '{entry.strip()}'. "
                f"Expected 'Name:elevation_mm:height_mm'"
            )
        name = parts[0].strip()
        elevation_mm = float(parts[1].strip())
        height_mm = float(parts[2].strip())
        defs.append({"name": name, "elevation_mm": elevation_mm, "height_mm": height_mm})
    return defs


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def create_ifc_model(output_path, project_name="Project", site_name="Site",
                     building_name="Building", storey_defs=None) -> dict:
    """
    Create a new IFC4 file with spatial hierarchy and millimetre units.

    Args:
        output_path: Path to write the IFC file.
        project_name: Name for the IfcProject.
        site_name: Name for the IfcSite.
        building_name: Name for the IfcBuilding.
        storey_defs: List of dicts with keys: name, elevation_mm, height_mm.
                     Defaults to [{"name": "Ground Floor", "elevation_mm": 0, "height_mm": 2700}].

    Returns:
        Dict with project structure details and GUIDs.
    """
    if storey_defs is None:
        storey_defs = [{"name": "Ground Floor", "elevation_mm": 0, "height_mm": 2700}]

    # 1. Create IFC4 file
    model = ifcopenshell.api.run("project.create_file", version="IFC4")

    # 2. Create project
    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject", name=project_name
    )

    # 3. Assign millimetre units
    ifcopenshell.api.run("unit.assign_unit", model)

    # 4. Create Model + Body representation contexts (required for element placement later)
    model3d = ifcopenshell.api.run(
        "context.add_context", model, context_type="Model"
    )
    body = ifcopenshell.api.run(
        "context.add_context", model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=model3d,
    )

    # 5. Create spatial structure
    site = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcSite", name=site_name
    )
    building = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuilding", name=building_name
    )

    # 6. Create storeys
    storeys = []
    for sdef in storey_defs:
        storey = ifcopenshell.api.run(
            "root.create_entity", model,
            ifc_class="IfcBuildingStorey", name=sdef["name"],
        )
        # Set elevation in project units (millimetres)
        storey.Elevation = float(sdef["elevation_mm"])

        # Set placement matrix with z in SI metres
        z_metres = sdef["elevation_mm"] / 1000.0
        ifcopenshell.api.run(
            "geometry.edit_object_placement", model,
            product=storey,
            matrix=placement_matrix([0.0, 0.0, z_metres]),
            is_si=True,
        )

        storeys.append({
            "entity": storey,
            "name": sdef["name"],
            "guid": storey.GlobalId,
            "elevation_mm": sdef["elevation_mm"],
            "height_mm": sdef["height_mm"],
        })

    # 7. Aggregate: Project -> Site -> Building -> Storeys
    ifcopenshell.api.run(
        "aggregate.assign_object", model,
        products=[site], relating_object=project,
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", model,
        products=[building], relating_object=site,
    )
    ifcopenshell.api.run(
        "aggregate.assign_object", model,
        products=[s["entity"] for s in storeys], relating_object=building,
    )

    # 8. Write file
    model.write(output_path)

    # 9. Build result
    result = {
        "status": "ok",
        "file": output_path,
        "project": {"name": project_name, "guid": project.GlobalId},
        "site": {"name": site_name, "guid": site.GlobalId},
        "building": {"name": building_name, "guid": building.GlobalId},
        "storeys": [
            {
                "name": s["name"],
                "guid": s["guid"],
                "elevation_mm": s["elevation_mm"],
                "height_mm": s["height_mm"],
            }
            for s in storeys
        ],
    }
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Create a new IFC4 file with spatial hierarchy and millimetre units."
    )
    parser.add_argument("--output", required=True, help="Output IFC file path")
    parser.add_argument("--project", default="Project", help="Project name")
    parser.add_argument("--site", default="Site", help="Site name")
    parser.add_argument("--building", default="Building", help="Building name")
    parser.add_argument(
        "--storeys", default="Ground Floor:0:2700",
        help='Storey definitions: "Name:elevation_mm:height_mm" comma-separated'
    )
    args = parser.parse_args()

    try:
        storey_defs = parse_storey_defs(args.storeys)
    except ValueError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    try:
        result = create_ifc_model(
            output_path=args.output,
            project_name=args.project,
            site_name=args.site,
            building_name=args.building,
            storey_defs=storey_defs,
        )
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
