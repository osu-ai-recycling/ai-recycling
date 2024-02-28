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
plane.hide_render = True

modifier = plane.modifiers.new(name='Collision', type='COLLISION')
bpy.ops.object.modifier_apply(modifier='COLLISION')

# CAN
bpy.ops.import_scene.obj(filepath="/Users/jack/Code/Capstone/blender/natty_light_trim.obj")
obj = bpy.context.selected_objects[0]

# DECIMATE
modifier = obj.modifiers.new(name="Decimate", type='DECIMATE')
modifier.ratio = 0.02  # Adjust the decimation ratio as needed (0.5 means 50% reduction)
bpy.ops.object.modifier_apply(modifier="Decimate")

# SOLIDIFY
modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
modifier.thickness = 0.0005  # Adjust the thickness as needed
bpy.ops.object.modifier_apply(modifier="Solidify")

modifier = obj.modifiers.new(name="Softbody", type='SOFT_BODY')
bpy.ops.object.modifier_add(type='SOFT_BODY')
bpy.context.object.modifiers["Softbody"].settings.use_goal = False
bpy.context.object.modifiers["Softbody"].settings.use_edges = True
bpy.context.object.modifiers["Softbody"].settings.use_self_collision = True
bpy.context.object.modifiers["Softbody"].settings.mass = 0.02
bpy.context.object.modifiers["Softbody"].settings.use_stiff_quads = True
bpy.context.object.modifiers["Softbody"].settings.shear = 1
bpy.context.object.modifiers["Softbody"].settings.damping = 5
bpy.ops.object.modifier_apply(modifier="Softbody")

obj.rotation_euler.rotate_axis('X', math.radians(90))

# Set up lighting
bpy.ops.object.light_add(type='SUN', radius=1, location=(5, 5, 5))
sun = bpy.context.active_object

# Set up camera
bpy.ops.object.camera_add(location=(0, 0, 1))
camera = bpy.context.active_object
camera.rotation_euler = (0, 0, math.radians(90))  # Set rotation

start_frame = 1
end_frame = 40

frame_increment = 1

for frame in range(start_frame, end_frame + 1, frame_increment):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

# Set camera as active and select it
scene.camera = camera
camera.select_set(True)

# Set render settings
bpy.context.scene.render.image_settings.file_format = 'PNG'  # Set the output file format
bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # Set the color mode to include alpha channel
bpy.context.scene.render.film_transparent = True  # Enable transparent background
#scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = "//output4.png"  # Save image in blend file directory

# Render image
bpy.ops.render.render(write_still=True)

# Save the blend file
# bpy.ops.wm.save_mainfile(filepath="//output3.blend")



