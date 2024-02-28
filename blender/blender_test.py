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

# Add a cube
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
cube = bpy.context.active_object

# Add a UV sphere
# bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0))
# sphere = bpy.context.active_object

# Add a material to the cube
material = bpy.data.materials.new(name="CubeMaterial")
material.diffuse_color = (1, 0, 0, 1)  # Set diffuse color to red
cube.data.materials.append(material)

# Set up lighting
bpy.ops.object.light_add(type='SUN', radius=1, location=(5, 5, 5))
sun = bpy.context.active_object

# Set up camera
bpy.ops.object.camera_add(location=(0, 0, 8))
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
bpy.ops.wm.save_mainfile(filepath="//output.blend")
