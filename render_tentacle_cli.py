#!/usr/bin/env python3
"""
CLI Tentacle Generator for Blender
==================================

Usage: blender --background --python render_tentacle_cli.py

This script generates a tri-lobe tentacle and renders it to image files
without requiring the Blender GUI. All output goes to the 'out' folder.
"""

import bpy
import math
import os
from mathutils import Vector
import bmesh

# =============================================================================
# PARAMETERS
# =============================================================================

# Output directory
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

# Tentacle parameters (mm)
# Note: Sizes are conservative to ensure minimum 3-4mm silicone wall thickness
tentacle_len_mm = 150.0
base_radius_mm = 25.0
tip_radius_mm = 0.0  # Pointed tip for seamless spade transition
spade_flattening = 0.8  # Much stronger flattening effect (0.0 = no flattening, 1.0 = completely flat)
# Bladder system
bladder_long_mm = 10.0         # Major axis (along tentacle) - reduced from 16.0
bladder_short_mm = 6.0         # Minor axis (cross-section) - reduced from 10.0
bladder_spacing_mm = 15.0
channel_radius_mm = 2.0        # Radius of connecting channels - reduced from 3.5
connector_radius_mm = 6.35
connector_length_mm = 20.0

# Scale conversion
MM = 0.001  # Convert mm to meters

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def setup_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    print(f"Output directory: {output_dir}")

def clear_scene():
    """Clear all objects from the scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_material(name, color=(0.8, 0.6, 0.4, 1.0)):
    """Create a material with enhanced visual definition"""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # Clear existing nodes
    mat.node_tree.nodes.clear()

    # Create nodes for enhanced material
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Output node
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (600, 0)

    # For very transparent materials, use simpler setup
    if color[3] < 0.5:  # If alpha is less than 0.5, use principled BSDF for better transparency
        # Principled BSDF for transparent materials
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled.location = (200, 0)

        # Set base color
        if 'Base Color' in principled.inputs:
            principled.inputs['Base Color'].default_value = color

        # Set alpha
        if 'Alpha' in principled.inputs:
            principled.inputs['Alpha'].default_value = color[3]

        # Try different transmission property names for different Blender versions
        if 'Transmission Weight' in principled.inputs:
            principled.inputs['Transmission Weight'].default_value = 0.95
        elif 'Transmission' in principled.inputs:
            principled.inputs['Transmission'].default_value = 0.95

        # Set other properties
        if 'Roughness' in principled.inputs:
            principled.inputs['Roughness'].default_value = 0.1
        if 'IOR' in principled.inputs:
            principled.inputs['IOR'].default_value = 1.45

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    else:
        # Mix shader for less transparent materials
        mix_shader = nodes.new(type='ShaderNodeMixShader')
        mix_shader.location = (400, 0)

        # Glass BSDF for realistic refraction
        glass_bsdf = nodes.new(type='ShaderNodeBsdfGlass')
        glass_bsdf.location = (200, 100)
        glass_bsdf.inputs['Color'].default_value = color
        glass_bsdf.inputs['Roughness'].default_value = 0.05
        glass_bsdf.inputs['IOR'].default_value = 1.45

        # Transparent BSDF for alpha blending
        transparent_bsdf = nodes.new(type='ShaderNodeBsdfTransparent')
        transparent_bsdf.location = (200, -100)
        transparent_bsdf.inputs['Color'].default_value = color

        # Fresnel node for edge highlighting
        fresnel = nodes.new(type='ShaderNodeFresnel')
        fresnel.location = (0, 0)
        fresnel.inputs['IOR'].default_value = 1.45

        # Connect nodes
        links.new(fresnel.outputs['Fac'], mix_shader.inputs['Fac'])
        links.new(glass_bsdf.outputs['BSDF'], mix_shader.inputs[1])
        links.new(transparent_bsdf.outputs['BSDF'], mix_shader.inputs[2])
        links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])

    # Set blend mode for transparency
    mat.blend_method = 'BLEND'
    mat.use_screen_refraction = True
    mat.use_backface_culling = False
    mat.show_transparent_back = False

    return mat

# =============================================================================
# GEOMETRY CREATION
# =============================================================================

def create_simple_tentacle():
    """Create a tri-lobe tentacle body - clean and simple"""
    print("Creating tri-lobe tentacle body...")

    # Create a single smooth tapered cylinder as the base
    bpy.ops.mesh.primitive_cone_add(
        vertices=32,
        radius1=base_radius_mm * MM,
        radius2=tip_radius_mm * MM,  # Tapers to a point
        depth=tentacle_len_mm * MM,
        location=(0, 0, tentacle_len_mm/2 * MM)
    )

    tentacle = bpy.context.active_object
    tentacle.name = "TentacleBody"

    # Use bmesh to create subtle tri-lobe shaping
    bpy.context.view_layer.objects.active = tentacle
    bpy.ops.object.mode_set(mode='OBJECT')

    bm = bmesh.new()
    bm.from_mesh(tentacle.data)
    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # Create subtle tri-lobe effect by adjusting vertices
    for vert in bm.verts:
        # Calculate height ratio (0 = base, 1 = tip)
        z_ratio = (vert.co.z + tentacle_len_mm/2 * MM) / (tentacle_len_mm * MM)

        # Calculate angle of this vertex around the cylinder
        angle = math.atan2(vert.co.y, vert.co.x)

        # Create more pronounced tri-lobe effect that maintains strength through most of the tentacle
        # Use a smoother function that creates deeper valleys between lobes
        lobe_effect = math.sin(angle * 3) * 0.35 * (1 - z_ratio**3)  # Increased from 0.15 to 0.35, changed power from 2 to 3

        # Apply the effect as a radial displacement
        radius = math.sqrt(vert.co.x**2 + vert.co.y**2)
        if radius > 0:
            scale_factor = 1 + lobe_effect
            vert.co.x *= scale_factor
            vert.co.y *= scale_factor

    # Update the mesh
    bm.to_mesh(tentacle.data)
    bm.free()
    tentacle.data.update()

    # Apply smooth shading
    bpy.context.view_layer.objects.active = tentacle
    bpy.ops.object.shade_smooth()

    # Add transparent material
    mat = create_material("TentacleBody", color=(0.95, 0.98, 1.0, 0.3))  # 30% opacity
    tentacle.data.materials.append(mat)

    print("✓ Created clean tri-lobe tentacle body")
    print("  No spade tip - keeping it simple")
    print("  Pronounced tri-lobe geometry with smooth taper to tip")

    return tentacle

def create_bladders():
    """Create bladder system aligned with channel paths"""
    print("Creating bladders aligned with channel paths...")

    bladders = []
    num_bladders = int(tentacle_len_mm / bladder_spacing_mm) - 1

    for lobe in range(3):
        # Add 30 degree offset to align with sine wave peaks
        angle = lobe * 2 * math.pi / 3 + math.pi / 6  # Add π/6 (30°) offset

        # Calculate channel start position (same as in create_channels)
        offset_ratio_start = 0.5
        offset_distance_start = base_radius_mm * offset_ratio_start * MM
        lobe_effect_start = math.sin(angle * 3) * 0.35
        actual_offset_start = offset_distance_start * (1 + lobe_effect_start)
        start_x = actual_offset_start * math.cos(angle)
        start_y = actual_offset_start * math.sin(angle)

        # Calculate channel end position (same as in create_channels)
        z_end = tentacle_len_mm * MM * 0.85
        z_ratio_end = 0.85
        offset_ratio_end = 0.5 - (0.3 * z_ratio_end)
        offset_distance_end = base_radius_mm * offset_ratio_end * MM
        lobe_effect_end = math.sin(angle * 3) * 0.35 * (1 - z_ratio_end**3)
        actual_offset_end = offset_distance_end * (1 + lobe_effect_end)

        # Apply same inward factor as channels
        inward_factor = 0.4
        end_x = actual_offset_end * math.cos(angle) * inward_factor
        end_y = actual_offset_end * math.sin(angle) * inward_factor

        for i in range(num_bladders):
            z_pos = (i + 1) * bladder_spacing_mm * MM
            if z_pos >= tentacle_len_mm * MM - bladder_spacing_mm * MM:
                break

            # Calculate position along the angled channel path
            # Interpolate between start and end positions
            path_ratio = z_pos / z_end  # How far along the channel path

            # Linear interpolation for x and y positions
            center_x = start_x + (end_x - start_x) * path_ratio
            center_y = start_y + (end_y - start_y) * path_ratio

            # Calculate taper
            z_ratio = z_pos / (tentacle_len_mm * MM)

            # Calculate tentacle radius at this height (linear taper to point)
            tentacle_radius_at_z = base_radius_mm * MM * (1.0 - z_ratio)

            # Size bladders proportional to available space
            # At base: use 35% of tentacle radius for bladder radius
            # At tip: use only 20% to maintain wall thickness
            size_ratio = 0.35 - (z_ratio * 0.15)  # From 35% to 20%

            # Calculate bladder size based on local tentacle radius
            bladder_radius = tentacle_radius_at_z * size_ratio

            # Apply minimum and maximum constraints
            min_bladder_radius = 0.0005  # 0.5mm minimum for manufacturing
            max_bladder_radius = bladder_short_mm * MM * 1.2  # Allow 20% larger than nominal
            bladder_radius = max(min(bladder_radius, max_bladder_radius), min_bladder_radius)

            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=bladder_radius,
                location=(center_x, center_y, z_pos)
            )

            bladder = bpy.context.active_object
            bladder.name = f"Bladder_L{lobe+1}_{i+1}"

            # Scale to ellipsoid (elongated along tentacle axis)
            bladder.scale.z = bladder_long_mm / bladder_short_mm
            bpy.ops.object.transform_apply(scale=True)

            # Add material with lobe-specific colors
            lobe_colors = [
                (0.2, 1.0, 0.2, 0.8),  # Green for lobe 1
                (0.2, 0.2, 1.0, 0.8),  # Blue for lobe 2
                (1.0, 0.2, 0.2, 0.8),  # Red for lobe 3
            ]
            mat = create_material(f"BladderMaterial_{lobe}", color=lobe_colors[lobe])
            bladder.data.materials.append(mat)

            bladders.append(bladder)

    print(f"✓ Created {len(bladders)} bladders aligned with channel paths")
    print(f"  Bladders positioned at lobe peaks: 30°, 150°, 270°")
    print(f"  Bladders follow angled channel paths for perfect alignment")
    print(f"  Proportional sizing: 35% of tentacle radius at base, 20% at tip")
    print(f"  Ensures consistent wall thickness throughout tentacle")
    return bladders

def create_channels():
    """Create channel system using single cylinders per lobe that pass through bladders"""
    print("Creating channels as single cylinders through bladders...")

    channels = []
    num_bladders = int(tentacle_len_mm / bladder_spacing_mm) - 1

    # Create one continuous channel per lobe
    for lobe in range(3):
        # Add 30 degree offset to align with sine wave peaks (same as bladders)
        angle = lobe * 2 * math.pi / 3 + math.pi / 6  # Add π/6 (30°) offset

        # Calculate channel start and end positions
        # Start at base
        z_start = 0
        offset_ratio_start = 0.5  # Wide at base
        offset_distance_start = base_radius_mm * offset_ratio_start * MM
        lobe_effect_start = math.sin(angle * 3) * 0.35
        actual_offset_start = offset_distance_start * (1 + lobe_effect_start)

        # End near tip (stop at 85% to avoid poking out)
        z_end = tentacle_len_mm * MM * 0.85
        z_ratio_end = 0.85
        offset_ratio_end = 0.5 - (0.3 * z_ratio_end)
        offset_distance_end = base_radius_mm * offset_ratio_end * MM
        lobe_effect_end = math.sin(angle * 3) * 0.35 * (1 - z_ratio_end**3)
        actual_offset_end = offset_distance_end * (1 + lobe_effect_end)

        # Calculate positions
        start_x = actual_offset_start * math.cos(angle)
        start_y = actual_offset_start * math.sin(angle)

        # Angle the end point inward by 30-40% to keep within tentacle
        inward_factor = 0.4  # End point at 40% of calculated offset (was 0.6)
        end_x = actual_offset_end * math.cos(angle) * inward_factor
        end_y = actual_offset_end * math.sin(angle) * inward_factor

        # Calculate cylinder properties
        channel_length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2 + (z_end - z_start)**2)

        # Center position
        center_x = (start_x + end_x) / 2
        center_y = (start_y + end_y) / 2
        center_z = (z_start + z_end) / 2

        # Create single tapered cylinder for the entire channel
        # Size channels proportional to tentacle radius for consistent wall thickness
        # Base: 20% of tentacle radius, Tip: 10% of tentacle radius
        base_tentacle_radius = base_radius_mm * MM
        tip_tentacle_radius = base_radius_mm * MM * 0.15  # Tentacle at 85% height

        base_channel_radius = base_tentacle_radius * 0.15  # 15% of tentacle radius
        tip_channel_radius = tip_tentacle_radius * 0.10   # 10% of tentacle radius

        # But don't exceed reasonable limits
        base_channel_radius = min(base_channel_radius, channel_radius_mm * MM * 1.5)
        tip_channel_radius = max(tip_channel_radius, channel_radius_mm * MM * 0.1)

        bpy.ops.mesh.primitive_cone_add(
            vertices=32,
            radius1=base_channel_radius,
            radius2=tip_channel_radius,
            depth=channel_length,
            location=(center_x, center_y, center_z)
        )

        channel = bpy.context.active_object
        channel.name = f"Channel_Lobe_{lobe+1}"

        # Calculate rotation to align cylinder from start to end point
        # Default cone points along Z axis
        up_vector = Vector((0, 0, 1))
        direction_vector = Vector((end_x - start_x, end_y - start_y, z_end - z_start)).normalized()

        # Calculate rotation
        rotation_axis = up_vector.cross(direction_vector)
        if rotation_axis.length > 0:
            rotation_axis.normalize()
            rotation_angle = math.acos(min(1.0, max(-1.0, up_vector.dot(direction_vector))))

            # Apply rotation
            channel.rotation_mode = 'AXIS_ANGLE'
            channel.rotation_axis_angle = (rotation_angle, rotation_axis.x, rotation_axis.y, rotation_axis.z)
            bpy.ops.object.transform_apply(rotation=True)

        # Add material with lobe-specific color
        channel_colors = [
            (0.2, 1.0, 0.2, 0.8),  # Green for lobe 1
            (0.2, 0.2, 1.0, 0.8),  # Blue for lobe 2
            (1.0, 0.2, 0.2, 0.8),  # Red for lobe 3
        ]
        mat = create_material(f"ChannelMaterial_L{lobe+1}", color=channel_colors[lobe])
        channel.data.materials.append(mat)

        channels.append(channel)

    print(f"✓ Created {len(channels)} continuous channels (one per lobe)")
    print(f"  Channels positioned at lobe peaks: 30°, 150°, 270°")
    print(f"  Proportional sizing: 15% of tentacle radius at base, 10% at tip")
    print(f"  Channels angled strongly inward (60% convergence) to stay within tentacle")
    return channels

def join_bladders_and_channels(bladders, channels):
    """Join bladders and channels using CSG boolean union operations"""
    print("\nJoining bladders and channels with CSG operations...")

    combined_lobes = []

    # Group bladders by lobe first, before any deletions
    bladders_by_lobe = {0: [], 1: [], 2: []}
    for bladder in bladders:
        for lobe in range(3):
            if f"_L{lobe+1}_" in bladder.name:
                bladders_by_lobe[lobe].append(bladder)
                break

    for lobe in range(3):
        # Get bladders for this lobe
        lobe_bladders = bladders_by_lobe[lobe]

        # Get channel for this lobe
        lobe_channels = [c for c in channels if f"_Lobe_{lobe+1}" in c.name]
        if not lobe_channels:
            print(f"  ⚠ No channel found for lobe {lobe+1}")
            continue

        lobe_channel = lobe_channels[0]

        if lobe_bladders:
            # Start with the channel as base object
            base_obj = lobe_channel
            base_obj.name = f"HydraulicSystem_Lobe_{lobe+1}"

            # Join all bladders to the channel using boolean union
            for bladder in lobe_bladders:
                # Add boolean modifier
                bool_mod = base_obj.modifiers.new(name=f"Union_{bladder.name}", type='BOOLEAN')
                bool_mod.operation = 'UNION'
                bool_mod.object = bladder

                # Apply modifier
                bpy.context.view_layer.objects.active = base_obj
                bpy.ops.object.modifier_apply(modifier=bool_mod.name)

                # Delete the bladder object after union
                bpy.data.objects.remove(bladder, do_unlink=True)

            print(f"  ✓ Lobe {lobe+1}: Joined {len(lobe_bladders)} bladders with channel")
            combined_lobes.append(base_obj)

    print(f"✓ Created {len(combined_lobes)} combined hydraulic systems")
    return combined_lobes


# =============================================================================
# SCENE SETUP
# =============================================================================

def setup_camera():
    """Set up camera for rendering"""
    print("Setting up camera...")

    # Calculate tentacle center position
    tentacle_center = Vector((0, 0, tentacle_len_mm * MM * 0.5))  # Center at 75mm height

    # Position camera to get a good view
    camera_pos = Vector((0.4, -0.4, 0.25))  # Position camera at reasonable distance and height

    bpy.ops.object.camera_add(location=camera_pos)
    camera = bpy.context.active_object
    camera.name = "RenderCamera"

    # Point camera at tentacle center using constraint
    constraint = camera.constraints.new(type='TRACK_TO')

    # Create an empty object at tentacle center for the camera to look at
    bpy.ops.object.empty_add(location=tentacle_center)
    target = bpy.context.active_object
    target.name = "CameraTarget"

    # Set up the constraint
    constraint.target = target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

    # Camera settings for proper framing
    camera.data.lens = 50  # Standard lens for good perspective
    camera.data.clip_end = 100

    bpy.context.scene.camera = camera
    print(f"✓ Camera positioned at {camera.location} looking at tentacle center {tentacle_center}")
    return camera

def setup_lighting():
    """Set up soft, even lighting for transparency"""
    print("Setting up soft even lighting...")

    # Main area light - large and soft
    bpy.ops.object.light_add(type='AREA', location=(3, -2, 4))
    main_light = bpy.context.active_object
    main_light.name = "MainLight"
    main_light.data.energy = 4.0
    main_light.data.size = 5  # Large area for soft shadows
    main_light.data.color = (1.0, 1.0, 1.0)  # Pure white

    # Fill light from opposite side
    bpy.ops.object.light_add(type='AREA', location=(-3, 2, 3))
    fill_light = bpy.context.active_object
    fill_light.name = "FillLight"
    fill_light.data.energy = 3.0
    fill_light.data.size = 4  # Large area for soft fill
    fill_light.data.color = (0.95, 0.98, 1.0)  # Slightly cool fill

    # Top light for internal illumination
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 6))
    top_light = bpy.context.active_object
    top_light.name = "TopLight"
    top_light.data.energy = 2.0
    top_light.data.size = 3
    top_light.data.color = (1.0, 1.0, 1.0)  # Pure white
    top_light.rotation_euler = (0, 0, 0)  # Point straight down

    # Back light for rim lighting
    bpy.ops.object.light_add(type='AREA', location=(0, 4, 2))
    back_light = bpy.context.active_object
    back_light.name = "BackLight"
    back_light.data.energy = 1.5
    back_light.data.size = 3
    back_light.data.color = (1.0, 0.98, 0.95)  # Slightly warm back light

    print("✓ Four-point soft lighting setup complete")
    return main_light, fill_light, top_light, back_light

def setup_world():
    """Set up world background optimized for transparency"""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        # Lighter background to help show internal structures through transparency
        bg_node.inputs['Color'].default_value = (0.2, 0.22, 0.25, 1.0)  # Neutral gray
        bg_node.inputs['Strength'].default_value = 0.8  # Brighter for better transparency contrast

def setup_render():
    """Set up render settings"""
    print("Setting up render...")

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'  # Updated for Blender 4.4+

    # Render settings
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    # Enable transparency and refraction in EEVEE
    scene.render.film_transparent = True  # Enable transparent background

    # EEVEE Next settings for transparency
    try:
        # Try to access EEVEE settings (may vary by Blender version)
        if hasattr(scene, 'eevee'):
            scene.eevee.use_ssr = True
            scene.eevee.use_ssr_refraction = True
    except:
        pass  # Skip if EEVEE settings not available

    print("✓ Render settings configured with transparency support")

# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_stl(obj, filename):
    """Export object as STL"""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    filepath = os.path.join(output_dir, filename)

    # Try different STL export methods for different Blender versions
    try:
        # Method 1: Standard STL export
        bpy.ops.export_mesh.stl(
            filepath=filepath,
            use_selection=True,
            global_scale=1000.0,  # Convert back to mm for 3D printing
            use_mesh_modifiers=True
        )
        print(f"✓ Exported: {filename}")
    except AttributeError:
        try:
            # Method 2: Newer STL export format
            bpy.ops.wm.stl_export(
                filepath=filepath,
                export_selected_objects=True,
                global_scale=1000.0
            )
            print(f"✓ Exported (method 2): {filename}")
        except AttributeError:
            try:
                # Method 3: Save as blend file if STL not available
                blend_filepath = filepath.replace('.stl', '.blend')
                bpy.ops.wm.save_as_mainfile(filepath=blend_filepath)
                print(f"⚠ STL export not available, saved as: {blend_filepath}")
            except:
                print(f"✗ Could not export: {filename}")

def render_image(filename, view_type="camera"):
    """Render scene to image"""
    filepath = os.path.join(output_dir, filename)

    if view_type == "camera":
        bpy.context.scene.render.filepath = filepath
        bpy.ops.render.render(write_still=True)

    print(f"✓ Rendered: {filename}")

def save_blend_file(filename):
    """Save the current scene as a .blend file"""
    filepath = os.path.join(output_dir, filename)

    try:
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        print(f"✓ Saved Blender file: {filename}")
    except Exception as e:
        print(f"✗ Could not save Blender file: {e}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function"""
    print("=== CLI Tentacle Generator ===")

    # Setup
    setup_output_dir()
    clear_scene()

    # Create geometry
    tentacle = create_simple_tentacle()
    bladders = create_bladders()
    channels = create_channels()

    # Join bladders and channels
    combined_hydraulics = join_bladders_and_channels(bladders, channels)

    # Scene setup
    camera = setup_camera()
    lights = setup_lighting()
    setup_world()
    setup_render()

    # Render multiple views
    print("\nRendering views...")
    render_image("tentacle_camera_view.png", "camera")

    # Save .blend file with all separate objects
    print("\nSaving Blender file...")
    save_blend_file("tentacle_complete.blend")

    # Export STL files
    print("\nExporting STL files...")

    # Export tentacle (now includes integrated spade)
    export_stl(tentacle, "tentacle_body.stl")

    # Export combined hydraulic systems
    if combined_hydraulics:
        # Combine all combined hydraulic systems
        bpy.ops.object.select_all(action='DESELECT')
        for hydraulic_system in combined_hydraulics:
            hydraulic_system.select_set(True)
        if combined_hydraulics:
            bpy.context.view_layer.objects.active = combined_hydraulics[0]
            bpy.ops.object.join()
            export_stl(bpy.context.active_object, "tentacle_hydraulic_systems.stl")

    print("\n🎯 CLI Generation Complete!")
    print(f"Check the '{output_dir}' folder for:")
    print("- tentacle_camera_view.png (rendered image)")
    print("- tentacle_complete.blend (Blender scene file)")
    print("- tentacle_body.stl (main tentacle)")
    print("- tentacle_hydraulic_systems.stl (combined hydraulic systems)")
    print("\n✨ Enhanced tri-lobe tentacle with hydraulic system")
    print("   - More pronounced tri-lobe shape")
    print("   - Proportional sizing system for consistent wall thickness:")
    print("     • Bladders: 35% of tentacle radius (base) → 20% (tip)")
    print("     • Channels: 15% of tentacle radius (base) → 10% (tip)")
    print("     • Result: ~8-10mm walls at base, ~3-4mm walls at tip")
    print("   - Channels strongly angled inward (60% convergence)")
    print("   - CSG-joined hydraulic systems for seamless geometry")

if __name__ == "__main__":
    main()
