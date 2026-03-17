"""
ifc_place.py -- Place elements in an existing IFC model.

Subcommands:
    wall    Place a wall element defined by two points.

Usage:
    python cli-tools/ifc_place.py wall \
      --model new_house.ifc \
      --name "Wall_North" \
      --start 0,0 --end 10000,0 \
      --height 2700 --thickness 200 \
      --storey "Ground Floor"

All dimensions are in millimetres. Output: JSON to stdout.
"""

import argparse
import json
import sys

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.representation


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------

def place_wall(model_path, name, start_mm, end_mm, height_mm, thickness_mm,
               storey_name) -> dict:
    """
    Place a wall element in an existing IFC model.

    Args:
        model_path: Path to the existing IFC file.
        name: Wall name.
        start_mm: Tuple (x, y) in millimetres for the wall start point.
        end_mm: Tuple (x, y) in millimetres for the wall end point.
        height_mm: Wall height in millimetres.
        thickness_mm: Wall thickness in millimetres.
        storey_name: Name of the storey to assign the wall to.

    Returns:
        Dict with wall details and GUID.
    """
    # 1. Open existing model
    model = ifcopenshell.open(model_path)

    # 2. Find storey by name
    storeys = model.by_type("IfcBuildingStorey")
    storey = None
    for s in storeys:
        if s.Name == storey_name:
            storey = s
            break

    if storey is None:
        available = [s.Name for s in storeys]
        raise ValueError(
            f"Storey '{storey_name}' not found. "
            f"Available storeys: {available}"
        )

    # 3. Find Body context
    body = ifcopenshell.util.representation.get_context(
        model, "Model", "Body", "MODEL_VIEW"
    )
    if body is None:
        raise ValueError(
            "Body representation context not found in the model. "
            "The model must have a Model/Body/MODEL_VIEW context. "
            "Create the model with ifc_create.py first."
        )

    # 4. Convert mm to metres
    p1 = (start_mm[0] / 1000.0, start_mm[1] / 1000.0)
    p2 = (end_mm[0] / 1000.0, end_mm[1] / 1000.0)
    height_m = height_mm / 1000.0
    thickness_m = thickness_mm / 1000.0

    # 5. Get storey elevation in metres
    elevation_m = (storey.Elevation or 0.0) / 1000.0

    # 6. Create wall entity
    wall = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcWall", name=name,
    )

    # 7. Assign to storey
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[wall], relating_structure=storey,
    )

    # 8. Create 2-point wall geometry (all values in metres, is_si=True)
    wall_rep = ifcopenshell.api.run(
        "geometry.create_2pt_wall", model,
        element=wall, context=body,
        p1=p1, p2=p2,
        elevation=elevation_m, height=height_m, thickness=thickness_m,
        is_si=True,
    )

    # 9. Assign representation (create_2pt_wall returns rep but doesn't assign it)
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=wall, representation=wall_rep,
    )

    # 10. Write model back
    model.write(model_path)

    # 11. Build result
    result = {
        "status": "ok",
        "file": model_path,
        "wall": {
            "name": name,
            "guid": wall.GlobalId,
            "storey": storey_name,
            "start_mm": list(start_mm),
            "end_mm": list(end_mm),
            "height_mm": height_mm,
            "thickness_mm": thickness_mm,
        },
    }
    return result


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def parse_point(value):
    """Parse 'x,y' string into (float, float) tuple in mm."""
    parts = value.split(",")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            f"Invalid point format '{value}'. Expected 'x,y' (e.g. '0,0' or '5000,3000')"
        )
    try:
        return (float(parts[0].strip()), float(parts[1].strip()))
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid coordinates in '{value}'. Expected numeric values."
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Place elements in an IFC model"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Wall subcommand
    wall_parser = subparsers.add_parser("wall", help="Place a wall element")
    wall_parser.add_argument("--model", required=True, help="Path to the IFC model file")
    wall_parser.add_argument("--name", required=True, help="Wall name")
    wall_parser.add_argument("--start", required=True, help="Start point x,y in mm")
    wall_parser.add_argument("--end", required=True, help="End point x,y in mm")
    wall_parser.add_argument("--height", required=True, type=float, help="Wall height in mm")
    wall_parser.add_argument("--thickness", required=True, type=float, help="Wall thickness in mm")
    wall_parser.add_argument("--storey", required=True, help="Storey name to assign wall to")

    args = parser.parse_args()

    if args.command == "wall":
        try:
            start_mm = parse_point(args.start)
            end_mm = parse_point(args.end)
        except argparse.ArgumentTypeError as e:
            print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
            sys.exit(1)

        try:
            result = place_wall(
                model_path=args.model,
                name=args.name,
                start_mm=start_mm,
                end_mm=end_mm,
                height_mm=args.height,
                thickness_mm=args.thickness,
                storey_name=args.storey,
            )
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
