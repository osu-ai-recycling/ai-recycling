import bpy
import math
import time

# Clear existing objects and materials
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()
#bpy.data.materials.remove(bpy.data.materials.get("Material"), do_unlink=True)

# Create a new scene
scene = bpy.context.scene

# PLANE
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
plane = bpy.context.active_object

# CAN
bpy.ops.import_scene.obj(filepath="/Users/jack/Code/Capstone/blender/natty_light_trim.obj")
obj = bpy.context.selected_objects[0]

# DECIMATE
modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
modifier.ratio = 0.1  # Adjust the decimation ratio as needed (0.5 means 50% reduction)
bpy.ops.object.modifier_apply(modifier="Decimate")

# SOLIDIFY
modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
modifier.thickness = 0.0005  # Adjust the thickness as needed
bpy.ops.object.modifier_apply(modifier="Solidify")

#bpy.context.space_data.context = 'PHYSICS'
bpy.ops.object.modifier_add(type='SOFT_BODY')
bpy.context.object.modifiers["Softbody"].settings.use_goal = False
bpy.context.object.modifiers["Softbody"].settings.use_edges = True
bpy.context.object.modifiers["Softbody"].settings.use_self_collision = True
bpy.context.object.modifiers["Softbody"].settings.mass = 0.02
bpy.context.object.modifiers["Softbody"].settings.use_stiff_quads = True
bpy.context.object.modifiers["Softbody"].settings.shear = 1
bpy.context.object.modifiers["Softbody"].settings.damping = 5
bpy.ops.object.modifier_apply(modifier='SOFT_BODY')




# # Add soft body simulation to the cube
# bpy.ops.object.modifier_add(type='SOFT_BODY')
# soft_body_modifier = cube.modifiers['Soft Body']
# soft_body_settings = soft_body_modifier.settings

# # Adjust soft body settings
# soft_body_settings.goal = 1  # Goal value for soft body simulation (1 is rigid)
# soft_body_settings.vertex_mass = 0.1  # Mass of each vertex
# soft_body_settings.bend = 0.1  # Bend stiffness
# soft_body_settings.pull = 0.1  # Pull stiffness


# Add a UV sphere
# bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 2))
# sphere = bpy.context.active_object

# Add a material to the cube
# material = bpy.data.materials.new(name="CubeMaterial")
# material.diffuse_color = (1, 0, 0, 1)  # Set diffuse color to red
# cube.data.materials.append(material)

# Set up lighting
bpy.ops.object.light_add(type='SUN', radius=1, location=(5, 5, 5))
sun = bpy.context.active_object

# Set up camera
bpy.ops.object.camera_add(location=(0, 0, 1))
camera = bpy.context.active_object
camera.rotation_euler = (0, 0, math.radians(90))  # Set rotation

# Set camera as active and select it
scene.camera = camera
camera.select_set(True)


# Set render settings
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = "//output.png"  # Save image in blend file directory

# Render image
bpy.ops.render.render(write_still=True)

# Save the blend file
# bpy.ops.wm.save_mainfile(filepath="//output3.blend")
