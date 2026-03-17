#!/usr/bin/env python3
"""ifc_query.py - CLI tool for inspecting IFC building models.

Returns structured JSON for all queries. Designed as both a CLI tool
and an importable module (functions first, argparse as thin wrapper).

Usage:
    python ifc_query.py --model <file.ifc> --summary
    python ifc_query.py --model <file.ifc> --type <element_type>
    python ifc_query.py --model <file.ifc> --element <name_or_guid> --properties
    python ifc_query.py --model <file.ifc> --storey <name> --elements
"""

import argparse
import json
import os
import re
import sys

import ifcopenshell
import ifcopenshell.util.element

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

TYPE_SHORTHAND = {
    "door": "IfcDoor",
    "window": "IfcWindow",
    "wall": "IfcWall",
    "slab": "IfcSlab",
    "floor": "IfcSlab",
    "roof": "IfcRoof",
    "column": "IfcColumn",
    "beam": "IfcBeam",
    "stair": "IfcStair",
    "railing": "IfcRailing",
    "space": "IfcSpace",
    "room": "IfcSpace",
    "covering": "IfcCovering",
    "opening": "IfcOpeningElement",
    "plate": "IfcPlate",
    "member": "IfcMember",
    "footing": "IfcFooting",
    "curtainwall": "IfcCurtainWall",
    "proxy": "IfcBuildingElementProxy",
    "furniture": "IfcFurnishingElement",
}

# Building element types scanned in --summary
BUILDING_ELEMENT_TYPES = [
    "IfcWall", "IfcDoor", "IfcWindow", "IfcSlab", "IfcRoof",
    "IfcColumn", "IfcBeam", "IfcStair", "IfcRailing", "IfcSpace",
    "IfcCovering", "IfcBuildingElementProxy", "IfcFurnishingElement",
    "IfcPlate", "IfcMember", "IfcCurtainWall", "IfcFooting",
    "IfcOpeningElement",
]

# Attributes to skip when serializing element info (not JSON-serializable)
SKIP_ATTRIBUTES = {"ObjectPlacement", "Representation", "OwnerHistory"}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def json_output(data, pretty=True):
    """Serialize data to JSON string."""
    indent = 2 if pretty else None
    return json.dumps(data, indent=indent, default=str, ensure_ascii=False)


def error_json(message, code="ERROR"):
    """Create a structured error dict."""
    return {"error": message, "code": code}


def print_error(message, code="ERROR"):
    """Print a JSON error to stderr and exit with non-zero code."""
    print(json_output(error_json(message, code)), file=sys.stderr)
    sys.exit(1)


def resolve_type(type_arg):
    """Resolve shorthand (e.g. 'wall') to IFC type name (e.g. 'IfcWall').

    Passes through unrecognised names as-is, so 'IfcWall' also works.
    """
    return TYPE_SHORTHAND.get(type_arg.lower(), type_arg)


def is_ifc_guid(s):
    """Check if a string matches the IFC GlobalId format (22-char base64-ish)."""
    return bool(re.match(r'^[0-9A-Za-z_$]{22}$', s))


def open_model(filepath):
    """Open an IFC file with error handling. Returns ifcopenshell file object."""
    if not os.path.isfile(filepath):
        print_error(f"File not found: {filepath}", "FILE_NOT_FOUND")

    try:
        return ifcopenshell.open(filepath)
    except RuntimeError as e:
        print_error(f"Failed to parse IFC file: {e}", "PARSE_ERROR")
    except Exception as e:
        print_error(f"Error opening IFC file: {type(e).__name__}: {e}", "IFC_ERROR")


def safe_by_type(model, ifc_type):
    """Query elements by type with error handling."""
    try:
        return model.by_type(ifc_type)
    except RuntimeError:
        print_error(
            f"'{ifc_type}' is not a valid IFC entity type in schema {model.schema}",
            "INVALID_TYPE",
        )


def get_storey(element):
    """Get the storey name for an element, or None."""
    container = ifcopenshell.util.element.get_container(element)
    return container.Name if container else None


def get_material_names(element):
    """Extract material names from an element as a list of strings.

    Handles all IFC material assignment patterns.
    """
    material = ifcopenshell.util.element.get_material(element, should_inherit=True)
    if material is None:
        return []

    if material.is_a("IfcMaterial"):
        return [material.Name]

    if material.is_a("IfcMaterialLayerSetUsage"):
        layers = material.ForLayerSet.MaterialLayers
        return [layer.Material.Name for layer in layers if layer.Material]

    if material.is_a("IfcMaterialLayerSet"):
        layers = material.MaterialLayers
        return [layer.Material.Name for layer in layers if layer.Material]

    if material.is_a("IfcMaterialConstituentSet"):
        constituents = material.MaterialConstituents or []
        return [c.Material.Name for c in constituents if c.Material]

    if material.is_a("IfcMaterialProfileSetUsage"):
        profiles = material.ForProfileSet.MaterialProfiles or []
        return [p.Material.Name for p in profiles if p.Material]

    if material.is_a("IfcMaterialProfileSet"):
        profiles = material.MaterialProfiles or []
        return [p.Material.Name for p in profiles if p.Material]

    if material.is_a("IfcMaterialList"):
        return [m.Name for m in material.Materials if m]

    name = getattr(material, "Name", None)
    return [name] if name else []


def get_element_summary(element):
    """Extract a compact summary dict for an element: name, guid, type, storey."""
    return {
        "name": getattr(element, "Name", None),
        "guid": element.GlobalId,
        "type": element.is_a(),
        "storey": get_storey(element),
    }


def get_element_detail(element):
    """Extract full detail dict for an element: attributes, psets, qtos, materials, storey."""
    # Attributes (skip non-serializable ones)
    info = element.get_info()
    attributes = {k: v for k, v in info.items() if k not in SKIP_ATTRIBUTES}

    # Property sets — strip internal "id" key from each pset
    psets = ifcopenshell.util.element.get_psets(element, psets_only=True)
    cleaned_psets = {}
    for pset_name, props in psets.items():
        cleaned_psets[pset_name] = {k: v for k, v in props.items() if k != "id"}

    # Quantity sets — strip internal "id" key
    qtos = ifcopenshell.util.element.get_psets(element, qtos_only=True)
    cleaned_qtos = {}
    for qto_name, props in qtos.items():
        cleaned_qtos[qto_name] = {k: v for k, v in props.items() if k != "id"}

    # Materials
    materials = get_material_names(element)

    # Storey
    storey = get_storey(element)

    return {
        "attributes": attributes,
        "property_sets": cleaned_psets,
        "quantity_sets": cleaned_qtos,
        "materials": materials,
        "storey": storey,
    }


# ---------------------------------------------------------------------------
# SPATIAL HIERARCHY
# ---------------------------------------------------------------------------

def build_spatial_hierarchy(model):
    """Build a nested tree of the spatial structure: Project > Site > Building > Storey.

    Returns a dict with nested children lists.
    """
    def node(entity):
        """Create a tree node for a spatial element."""
        result = {
            "name": getattr(entity, "Name", None),
            "type": entity.is_a(),
            "guid": entity.GlobalId,
        }

        children = []

        # Check for IfcRelAggregates (spatial decomposition)
        if hasattr(entity, "IsDecomposedBy"):
            for rel in entity.IsDecomposedBy:
                for child in rel.RelatedObjects:
                    children.append(node(child))

        if children:
            result["children"] = children

        return result

    # Start from IfcProject
    projects = model.by_type("IfcProject")
    if not projects:
        return {"error": "No IfcProject found in model"}

    return node(projects[0])


# ---------------------------------------------------------------------------
# COMMAND FUNCTIONS
# ---------------------------------------------------------------------------

def cmd_summary(model, filepath):
    """Generate a model summary: schema, element counts, spatial hierarchy, materials.

    Args:
        model: ifcopenshell file object
        filepath: path to the IFC file (for metadata)

    Returns:
        dict with schema, element_counts, spatial_hierarchy, materials, total_elements
    """
    # Schema version
    schema = model.schema

    # Element counts (only types that actually exist in the model)
    element_counts = {}
    total = 0
    for ifc_type in BUILDING_ELEMENT_TYPES:
        try:
            elements = model.by_type(ifc_type)
            count = len(elements)
            if count > 0:
                element_counts[ifc_type] = count
                total += count
        except RuntimeError:
            pass

    # Spatial hierarchy
    spatial_hierarchy = build_spatial_hierarchy(model)

    # Materials — collect unique names across all elements
    material_names = set()
    for mat in model.by_type("IfcMaterial"):
        if mat.Name:
            material_names.add(mat.Name)

    return {
        "file": os.path.basename(filepath),
        "schema": schema,
        "element_counts": element_counts,
        "total_elements": total,
        "spatial_hierarchy": spatial_hierarchy,
        "materials": sorted(material_names),
    }


def cmd_type(model, type_arg):
    """List all elements of a given type.

    Args:
        model: ifcopenshell file object
        type_arg: element type name or shorthand (e.g. 'wall' or 'IfcWall')

    Returns:
        dict with type, count, and elements list
    """
    ifc_type = resolve_type(type_arg)
    elements = safe_by_type(model, ifc_type)

    result = {
        "type": ifc_type,
        "count": len(elements),
        "elements": [get_element_summary(el) for el in elements],
    }

    return result


def find_element(model, identifier):
    """Find a single element by name or GUID.

    Args:
        model: ifcopenshell file object
        identifier: element Name or GlobalId

    Returns:
        ifcopenshell element, or calls print_error (exits) if not found
    """
    element = None

    if is_ifc_guid(identifier):
        # Look up by GUID
        element = model.by_guid(identifier) if identifier else None
    else:
        # Look up by Name — search all elements
        for el in model:
            if getattr(el, "Name", None) == identifier:
                element = el
                break

    if element is None:
        print_error(
            f"Element not found: '{identifier}'",
            "NOT_FOUND",
        )

    return element


def cmd_element_summary(model, identifier):
    """Get compact summary for a single element found by name or GUID.

    Args:
        model: ifcopenshell file object
        identifier: element Name or GlobalId

    Returns:
        dict with name, guid, type, storey
    """
    element = find_element(model, identifier)
    return get_element_summary(element)


def cmd_element_detail(model, identifier):
    """Get full details for a single element found by name or GUID.

    Args:
        model: ifcopenshell file object
        identifier: element Name or GlobalId

    Returns:
        dict with full element detail (attributes, psets, qtos, materials, storey)
    """
    element = find_element(model, identifier)
    return get_element_detail(element)


def find_storey(model, storey_name):
    """Find a storey by name.

    Args:
        model: ifcopenshell file object
        storey_name: name of the IfcBuildingStorey

    Returns:
        ifcopenshell element, or calls print_error (exits) if not found
    """
    storeys = model.by_type("IfcBuildingStorey")
    for s in storeys:
        if s.Name == storey_name:
            return s

    available = [s.Name for s in storeys]
    print_error(
        f"Storey not found: '{storey_name}'. Available storeys: {available}",
        "NOT_FOUND",
    )


def cmd_storey_info(model, storey_name):
    """Show storey summary: name, guid, elevation, and element count.

    Args:
        model: ifcopenshell file object
        storey_name: name of the IfcBuildingStorey

    Returns:
        dict with storey name, guid, elevation, element_count
    """
    target = find_storey(model, storey_name)
    contained = ifcopenshell.util.element.get_decomposition(target)
    count = sum(1 for el in contained if el != target)

    return {
        "storey": storey_name,
        "guid": target.GlobalId,
        "elevation": getattr(target, "Elevation", None),
        "element_count": count,
    }


def cmd_storey_elements(model, storey_name):
    """List all elements contained in a given storey.

    Args:
        model: ifcopenshell file object
        storey_name: name of the IfcBuildingStorey

    Returns:
        dict with storey name, count, and elements list
    """
    target = find_storey(model, storey_name)
    contained = ifcopenshell.util.element.get_decomposition(target)

    # Filter to building elements only (skip the storey itself if returned)
    elements = []
    for el in contained:
        if el == target:
            continue
        elements.append(get_element_summary(el))

    return {
        "storey": storey_name,
        "guid": target.GlobalId,
        "count": len(elements),
        "elements": elements,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    """Build the argparse parser."""
    parser = argparse.ArgumentParser(
        description="Inspect IFC building models. All output is JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --model house.ifc --summary
  %(prog)s --model house.ifc --type wall
  %(prog)s --model house.ifc --element "Wall_North" --properties
  %(prog)s --model house.ifc --storey "Ground Floor" --elements
""",
    )

    parser.add_argument(
        "--model", required=True,
        help="Path to the IFC file",
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Show model summary: schema, element counts, spatial hierarchy, materials",
    )
    parser.add_argument(
        "--type",
        help="List elements of this type (e.g. 'wall', 'IfcDoor')",
    )
    parser.add_argument(
        "--element",
        help="Look up a single element by Name or GlobalId",
    )
    parser.add_argument(
        "--properties", action="store_true",
        help="Show full properties for --element (attributes, psets, qtos, materials)",
    )
    parser.add_argument(
        "--storey",
        help="Filter by storey name",
    )
    parser.add_argument(
        "--elements", action="store_true",
        help="List elements in --storey",
    )
    parser.add_argument(
        "--compact", action="store_true",
        help="Compact JSON output (no indentation). Default is pretty-printed.",
    )

    return parser


def main():
    """Entry point for CLI usage."""
    parser = build_parser()
    args = parser.parse_args()

    pretty = not args.compact

    # Open model
    model = open_model(args.model)

    # Dispatch to the right command
    if args.summary:
        result = cmd_summary(model, args.model)

    elif args.type:
        result = cmd_type(model, args.type)

    elif args.element and args.properties:
        result = cmd_element_detail(model, args.element)

    elif args.element:
        result = cmd_element_summary(model, args.element)

    elif args.storey and args.elements:
        result = cmd_storey_elements(model, args.storey)

    elif args.storey:
        result = cmd_storey_info(model, args.storey)

    else:
        parser.print_help()
        sys.exit(0)

    # Output
    print(json_output(result, pretty=pretty))


if __name__ == "__main__":
    main()
