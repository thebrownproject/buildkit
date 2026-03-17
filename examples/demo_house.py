"""
demo_house.py — Generate a simple single-storey house as a valid IFC4 file.

Usage:
    python examples/demo_house.py

Output:
    examples/demo_house.ifc

House specs:
    - 10m x 8m footprint, 2700mm wall height, 200mm thick walls
    - 5 walls (4 perimeter + 1 internal partition at x=5)
    - 200mm concrete floor slab
    - 1 internal door (820x2040mm) in the partition wall
    - 2 windows (1200x1200mm, 900mm sill) in the north wall
    - Gable roof at 22.5 deg pitch, ridge running east-west

Unit rules (IfcOpenShell 0.8.x):
    - add_wall_representation, add_slab_representation, create_2pt_wall(is_si=True) -> SI METRES
    - add_door_representation, add_window_representation -> PROJECT UNITS (millimetres)
    - edit_object_placement(is_si=True) -> SI METRES
"""

import os
import math

import ifcopenshell
import ifcopenshell.api
import numpy as np


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def placement_matrix(origin, x_local=None, z_local=None):
    """Build a 4x4 placement matrix from origin + optional local axes."""
    x = np.array(x_local if x_local else [1, 0, 0], dtype=float)
    z = np.array(z_local if z_local else [0, 0, 1], dtype=float)
    y = np.cross(z, x)
    m = np.eye(4)
    m[0:3, 0] = x
    m[0:3, 1] = y
    m[0:3, 2] = z
    m[0:3, 3] = origin
    return m


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # ==================================================================
    # 1. Project Setup
    # ==================================================================
    model = ifcopenshell.api.run("project.create_file", version="IFC4")
    project = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcProject", name="Demo House"
    )
    ifcopenshell.api.run("unit.assign_unit", model)  # defaults to millimetres

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

    site = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcSite", name="Site"
    )
    building = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcBuilding", name="Building"
    )
    storey = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcBuildingStorey", name="Ground Floor",
    )

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
        products=[storey], relating_object=building,
    )

    # ==================================================================
    # 2. Walls  (create_2pt_wall with is_si=True — values in METRES)
    # ==================================================================
    # Thickness direction is perpendicular to p1->p2 rotated 90 deg CCW.

    # --- South wall: p1=(0,0)->p2=(10,0), thickness extends +Y -----------
    wall_south = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcWall", name="Wall_South"
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[wall_south], relating_structure=storey,
    )
    wall_south_rep = ifcopenshell.api.run(
        "geometry.create_2pt_wall", model,
        element=wall_south, context=body,
        p1=(0.0, 0.0), p2=(10.0, 0.0),
        elevation=0.0, height=2.7, thickness=0.2, is_si=True,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=wall_south, representation=wall_south_rep,
    )

    # --- East wall: p1=(10,0)->p2=(10,8), thickness extends -X -----------
    wall_east = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcWall", name="Wall_East"
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[wall_east], relating_structure=storey,
    )
    wall_east_rep = ifcopenshell.api.run(
        "geometry.create_2pt_wall", model,
        element=wall_east, context=body,
        p1=(10.0, 0.0), p2=(10.0, 8.0),
        elevation=0.0, height=2.7, thickness=0.2, is_si=True,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=wall_east, representation=wall_east_rep,
    )

    # --- North wall: p1=(10,8)->p2=(0,8), thickness extends -Y -----------
    wall_north = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcWall", name="Wall_North"
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[wall_north], relating_structure=storey,
    )
    wall_north_rep = ifcopenshell.api.run(
        "geometry.create_2pt_wall", model,
        element=wall_north, context=body,
        p1=(10.0, 8.0), p2=(0.0, 8.0),
        elevation=0.0, height=2.7, thickness=0.2, is_si=True,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=wall_north, representation=wall_north_rep,
    )

    # --- West wall: p1=(0,8)->p2=(0,0), thickness extends +X -------------
    wall_west = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcWall", name="Wall_West"
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[wall_west], relating_structure=storey,
    )
    wall_west_rep = ifcopenshell.api.run(
        "geometry.create_2pt_wall", model,
        element=wall_west, context=body,
        p1=(0.0, 8.0), p2=(0.0, 0.0),
        elevation=0.0, height=2.7, thickness=0.2, is_si=True,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=wall_west, representation=wall_west_rep,
    )

    # --- Internal partition at x=5 (north-south) -------------------------
    wall_internal = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcWall", name="Wall_Internal"
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[wall_internal], relating_structure=storey,
    )
    wall_internal_rep = ifcopenshell.api.run(
        "geometry.create_2pt_wall", model,
        element=wall_internal, context=body,
        p1=(5.0, 0.2), p2=(5.0, 7.8),
        elevation=0.0, height=2.7, thickness=0.2, is_si=True,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=wall_internal, representation=wall_internal_rep,
    )

    # ==================================================================
    # 3. Floor Slab  (SI METRES)
    # ==================================================================
    slab = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcSlab", name="Floor_Slab", predefined_type="FLOOR",
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[slab], relating_structure=storey,
    )
    slab_rep = ifcopenshell.api.run(
        "geometry.add_slab_representation", model,
        context=body, depth=0.2,
        polyline=[(0.0, 0.0), (10.0, 0.0), (10.0, 8.0), (0.0, 8.0)],
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=slab, representation=slab_rep,
    )
    # Place at z=-0.2 so top of slab aligns with z=0 (floor level)
    ifcopenshell.api.run(
        "geometry.edit_object_placement", model,
        product=slab, matrix=placement_matrix([0, 0, -0.2]), is_si=True,
    )

    # ==================================================================
    # 4. Door in Internal Wall  (820 x 2040 mm)
    # ==================================================================
    # Internal wall runs north (from y=0.2 to y=7.8) at x=5.
    # Wall local X direction is +Y global.
    # Place door opening ~3m along wall from south end.

    # a. Create opening element
    opening_door = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcOpeningElement", name="Opening_Door",
    )
    # Opening geometry slightly oversized (SI METRES)
    opening_door_rep = ifcopenshell.api.run(
        "geometry.add_wall_representation", model,
        context=body, length=0.92, height=2.14, thickness=0.4,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=opening_door, representation=opening_door_rep,
    )

    # b. Position opening (SI METRES)
    # Shift x by 0.1 to center in 0.2m thick wall
    matrix_open = placement_matrix(
        [5.1, 3.0, 0.0], x_local=[0, 1, 0], z_local=[0, 0, 1]
    )
    ifcopenshell.api.run(
        "geometry.edit_object_placement", model,
        product=opening_door, matrix=matrix_open, is_si=True,
    )

    # c. Cut the internal wall
    ifcopenshell.api.run(
        "feature.add_feature", model,
        feature=opening_door, element=wall_internal,
    )

    # d. Create door entity
    door = ifcopenshell.api.run(
        "root.create_entity", model, ifc_class="IfcDoor", name="Door_Internal"
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[door], relating_structure=storey,
    )

    # e. Door representation (PROJECT UNITS = millimetres!)
    door_rep = ifcopenshell.api.run(
        "geometry.add_door_representation", model,
        context=body,
        overall_height=2040.0,
        overall_width=820.0,
        operation_type="SINGLE_SWING_LEFT",
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=door, representation=door_rep,
    )

    # f. Fill opening, then place door
    ifcopenshell.api.run(
        "feature.add_filling", model,
        opening=opening_door, element=door,
    )
    matrix_door = placement_matrix(
        [5.0, 3.0, 0.0], x_local=[0, 1, 0], z_local=[0, 0, 1]
    )
    ifcopenshell.api.run(
        "geometry.edit_object_placement", model,
        product=door, matrix=matrix_door, is_si=True,
    )

    # ==================================================================
    # 5. Windows in North Wall  (2x 1200 x 1200 mm, 900 mm sill)
    # ==================================================================
    # North wall goes from p1=(10,8) to p2=(0,8).
    # Wall local X direction is -X global (west).

    windows = []

    for i, global_x in enumerate([7.0, 3.0], start=1):
        # a. Create opening
        opening_w = ifcopenshell.api.run(
            "root.create_entity", model,
            ifc_class="IfcOpeningElement", name=f"Opening_Window_{i}",
        )
        opening_w_rep = ifcopenshell.api.run(
            "geometry.add_wall_representation", model,
            context=body, length=1.3, height=1.3, thickness=0.4,
        )
        ifcopenshell.api.run(
            "geometry.assign_representation", model,
            product=opening_w, representation=opening_w_rep,
        )

        # b. Position opening (SI METRES) — sill at 0.9 m
        # Shift y by 0.1 to center in 0.2m thick wall (wall extends -Y from y=8)
        matrix_ow = placement_matrix(
            [global_x, 8.1, 0.9], x_local=[-1, 0, 0], z_local=[0, 0, 1]
        )
        ifcopenshell.api.run(
            "geometry.edit_object_placement", model,
            product=opening_w, matrix=matrix_ow, is_si=True,
        )

        # c. Cut the north wall
        ifcopenshell.api.run(
            "feature.add_feature", model,
            feature=opening_w, element=wall_north,
        )

        # d. Create window entity
        window = ifcopenshell.api.run(
            "root.create_entity", model,
            ifc_class="IfcWindow", name=f"Window_North_{i}",
        )
        ifcopenshell.api.run(
            "spatial.assign_container", model,
            products=[window], relating_structure=storey,
        )

        # e. Window representation (PROJECT UNITS = millimetres!)
        window_rep = ifcopenshell.api.run(
            "geometry.add_window_representation", model,
            context=body,
            overall_height=1200.0,
            overall_width=1200.0,
            partition_type="SINGLE_PANEL",
        )
        ifcopenshell.api.run(
            "geometry.assign_representation", model,
            product=window, representation=window_rep,
        )

        # f. Fill opening, then place window
        ifcopenshell.api.run(
            "feature.add_filling", model,
            opening=opening_w, element=window,
        )
        matrix_w = placement_matrix(
            [global_x, 8.0, 0.9], x_local=[-1, 0, 0], z_local=[0, 0, 1]
        )
        ifcopenshell.api.run(
            "geometry.edit_object_placement", model,
            product=window, matrix=matrix_w, is_si=True,
        )

        windows.append(window)

    # ==================================================================
    # 6. Gable Roof  (two IfcSlab elements, SI METRES)
    # ==================================================================
    # Ridge runs east-west at y=4, 22.5 deg pitch.
    # Each half spans 4m in plan from eave to ridge.

    pitch = math.radians(22.5)

    # --- South roof slab: eave at y=0, slopes up toward ridge at y=4 ---
    roof_s = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcSlab", name="Roof_South", predefined_type="ROOF",
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[roof_s], relating_structure=storey,
    )
    roof_s_rep = ifcopenshell.api.run(
        "geometry.add_wall_representation", model,
        context=body, length=10.0, height=4.0, thickness=0.2, x_angle=pitch,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=roof_s, representation=roof_s_rep,
    )
    m_south = np.eye(4)
    m_south[0:3, 0] = [-1, 0, 0]   # x_local: west (-X)
    m_south[0:3, 1] = [0, 0, 1]    # y_local: up
    m_south[0:3, 2] = [0, 1, 0]    # z_local: north (+Y)
    m_south[0:3, 3] = [10.0, 0.0, 2.7]
    ifcopenshell.api.run(
        "geometry.edit_object_placement", model,
        product=roof_s, matrix=m_south, is_si=True,
    )

    # --- North roof slab: eave at y=8, slopes up toward ridge at y=4 ---
    roof_n = ifcopenshell.api.run(
        "root.create_entity", model,
        ifc_class="IfcSlab", name="Roof_North", predefined_type="ROOF",
    )
    ifcopenshell.api.run(
        "spatial.assign_container", model,
        products=[roof_n], relating_structure=storey,
    )
    roof_n_rep = ifcopenshell.api.run(
        "geometry.add_wall_representation", model,
        context=body, length=10.0, height=4.0, thickness=0.2, x_angle=pitch,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation", model,
        product=roof_n, representation=roof_n_rep,
    )
    m_north = np.eye(4)
    m_north[0:3, 0] = [1, 0, 0]    # x_local: east (+X)
    m_north[0:3, 1] = [0, 0, 1]    # y_local: up
    m_north[0:3, 2] = [0, -1, 0]   # z_local: south (-Y)
    m_north[0:3, 3] = [0.0, 8.0, 2.7]
    ifcopenshell.api.run(
        "geometry.edit_object_placement", model,
        product=roof_n, matrix=m_north, is_si=True,
    )

    # ==================================================================
    # 7. Materials
    # ==================================================================
    concrete = ifcopenshell.api.run(
        "material.add_material", model, name="Concrete", category="concrete"
    )
    timber = ifcopenshell.api.run(
        "material.add_material", model, name="Timber Frame", category="wood"
    )
    steel = ifcopenshell.api.run(
        "material.add_material", model, name="Steel", category="steel"
    )

    # Walls — timber frame
    for w in [wall_south, wall_east, wall_north, wall_west, wall_internal]:
        ifcopenshell.api.run(
            "material.assign_material", model,
            products=[w], type="IfcMaterial", material=timber,
        )

    # Floor slab — concrete
    ifcopenshell.api.run(
        "material.assign_material", model,
        products=[slab], type="IfcMaterial", material=concrete,
    )

    # Door — timber
    ifcopenshell.api.run(
        "material.assign_material", model,
        products=[door], type="IfcMaterial", material=timber,
    )

    # Windows — assign individually (no material specified, skip if desired)
    # Leaving windows without explicit material for now.

    # Roof slabs — steel (metal roofing)
    ifcopenshell.api.run(
        "material.assign_material", model,
        products=[roof_s, roof_n], type="IfcMaterial", material=steel,
    )

    # ==================================================================
    # 8. Write IFC File
    # ==================================================================
    output_path = os.path.join(os.path.dirname(__file__), "demo_house.ifc")
    model.write(output_path)

    # ==================================================================
    # 9. Summary
    # ==================================================================
    print(f"Written: {output_path}")
    print()
    print("Demo House — IFC4 Summary")
    print("=" * 40)
    print(f"  Footprint:    10m x 8m")
    print(f"  Wall height:  2700mm (200mm thick)")
    print(f"  Walls:        5 (4 perimeter + 1 internal)")
    print(f"  Floor slab:   200mm concrete")
    print(f"  Door:         1 (820x2040mm, internal)")
    print(f"  Windows:      2 (1200x1200mm, north wall)")
    print(f"  Roof:         Gable, 22.5 deg pitch")
    print(f"  Materials:    Concrete, Timber Frame, Steel")
    print()
    print("Elements created:")
    walls_count = len(model.by_type("IfcWall"))
    slabs_count = len(model.by_type("IfcSlab"))
    doors_count = len(model.by_type("IfcDoor"))
    windows_count = len(model.by_type("IfcWindow"))
    openings_count = len(model.by_type("IfcOpeningElement"))
    print(f"  IfcWall:           {walls_count}")
    print(f"  IfcSlab:           {slabs_count} (1 floor + 2 roof)")
    print(f"  IfcDoor:           {doors_count}")
    print(f"  IfcWindow:         {windows_count}")
    print(f"  IfcOpeningElement: {openings_count}")


if __name__ == "__main__":
    main()
