import sys
sys.path.append("/Users/jack/Code/Capstone/blender/venv/lib/python3.9/site-packages/cv2")

import bpy
import cv2
import numpy as np
import math

def boundary_edges(corners):
    # Initialize variables to store max and min coordinates
    max_x = float('-inf')
    min_x = float('inf')
    max_y = float('-inf')
    min_y = float('inf')

    # Loop through each array of corners
    for corner_array in corners:
        # Flatten the array to get a list of corner points
        corner_points = corner_array[0]  # Extract the inner array
        for corner in corner_points:
            x, y = corner
            # Update max and min coordinates
            max_x = max(max_x, x)
            min_x = min(min_x, x)
            max_y = max(max_y, y)
            min_y = min(min_y, y)
    print("MIN MAX", max_x, min_x, max_y, min_y)
    
    return max_x, min_x, max_y, min_y


def is_inside_boundary(point, max_x, min_x, max_y, min_y):
    """
    Check if a point is inside the boundary defined by a list of boundary points.
    
    Args:
    - point (Vector): The point to check.
    - boundary_points (list): List of boundary points defining the boundary polygon.
    
    Returns:
    - bool: True if the point is inside the boundary, False otherwise.
    """
    # Implementation of point-in-polygon algorithm
    # You can replace this with a suitable algorithm based on your requirements
    
#    print("point: ", point)
#    print("boundary points: ", boundary_points)
#    
#    # Simple implementation: check if the point is within the bounding box of the boundary polygon
#    min_x = min(p[0] for p in boundary_points)
#    max_x = max(p.x for p in boundary_points)
#    min_y = min(p.y for p in boundary_points)
#    max_y = max(p.y for p in boundary_points)
    
    return min_x <= point.x <= max_x and min_y <= point.y <= max_y


def cv_trim_preprocess():

    print("cv_trim_preprocess() called")
    
    # Clear existing objects and materials
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    scene = bpy.context.scene

    # CAN
    bpy.ops.import_scene.obj(filepath="/Users/jack/Code/Capstone/blender/Scaniverse_2024_02_27_154257.obj")
    scan = bpy.context.selected_objects[0]


    # Set up the top-down view
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.context.scene.objects[0]  # Select the object you want to render
    bpy.context.active_object.select_set(True)
#    bpy.ops.view3d.view_axis(type='TOP', align_active=True)

    # Set camera to orthographic
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 2.1), rotation=(0, 0, 0))
    bpy.context.scene.camera = bpy.context.object
#    bpy.data.cameras[bpy.context.camera.name].type = 'ORTHO'

    # Render the image
    scene.render.filepath = "//preprocess.png"  # Save image in blend file directory
    
    
    
    
    
    camera = bpy.context.scene.camera

    # Check if the active object is a camera
    if camera and camera.type == 'CAMERA':
        # Extract camera properties
        sensor_width = camera.data.sensor_width
        sensor_height = camera.data.sensor_height
        focal_length = camera.data.lens
        sensor_fit = camera.data.sensor_fit
        aspect_ratio = bpy.context.scene.render.resolution_y / bpy.context.scene.render.resolution_x
        
        # Calculate the image width and height
        if sensor_fit == 'HORIZONTAL':
            image_width = 2 * math.tan(math.radians(camera.data.angle_x / 2)) * camera.data.clip_end
            image_height = image_width / aspect_ratio
        elif sensor_fit == 'VERTICAL':
            image_height = 2 * math.tan(math.radians(camera.data.angle_y / 2)) * camera.data.clip_end
            image_width = image_height * aspect_ratio
        else:  # AUTO
            if sensor_width > sensor_height:
                image_width = 2 * math.tan(math.radians(camera.data.angle_x / 2)) * camera.data.clip_end
                image_height = image_width / aspect_ratio
            else:
                image_height = 2 * math.tan(math.radians(camera.data.angle_y / 2)) * camera.data.clip_end
                image_width = image_height * aspect_ratio
        
        print("Image width (Blender units):", image_width)
        print("Image height (Blender units):", image_height)
    else:
        print("No active camera found.")




    
    bpy.context.scene.render.image_settings.file_format = 'PNG'  # Set the output file format
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'  # Set the color mode to include alpha channel
    bpy.context.scene.render.film_transparent = True  # Enable transparent background

    bpy.ops.render.render(write_still=True)

    # Delete the camera after rendering if you don't need it
    # bpy.data.objects.remove(bpy.context.object, do_unlink=True)


    image_path = "/Users/jack/Code/Capstone/blender/preprocess.png"
    image = cv2.imread(image_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Define the Aruco dictionary and parameters
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
    parameters =  cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)

    # Detect Aruco markers in the image
#    corners, ids, rejected = cv2.aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    corners, ids, rejected = detector.detectMarkers(gray)
    print("CORNERS: ", corners)

    # Assuming you have four Aruco codes
    if len(corners) == 4:
        # Compute the boundary defined by the Aruco codes
#        boundary_points = np.concatenate(corners)
        max_x, min_x, max_y, min_y = boundary_edges(corners)

        # Get the active object (assuming it's the mesh you want to edit)
        obj = scan

        # Assuming the object is a mesh
        if obj.type == 'MESH':
            # Get the mesh data
            mesh = obj.data
            
            # Assuming the object has vertices
            if mesh.vertices:
                # Create a list to store vertices to delete
                vertices_to_delete = []

                
                # Switch to edit mode
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                
                bpy.ops.mesh.select_all(action='DESELECT')

                # Loop through vertices
                for vertex in mesh.vertices:
                    # Check if the vertex is outside the boundary defined by Aruco codes
                    # You can implement a suitable condition here based on the boundary points
#                    print("TEST: ", is_inside_boundary(vertex.co, max_x, min_x, max_y, min_y))
                    if not is_inside_boundary(vertex.co, max_x, min_x, max_y, min_y):
#                        vertices_to_delete.append(vertex.index)
                        vertex.select = True
                        
                    if is_inside_boundary(vertex.co, max_x, min_x, max_y, min_y):
#                        vertices_to_delete.append(vertex.index)
                        print("INSIDE")
                
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.delete(type='VERT')
                        
#                bpy.ops.object.mode_set(mode='OBJECT')
#                vertex_group = bpy.context.active_object.vertex_groups.new(name='_PAST_BOUNDARY_')
#                vertex_group.add(vertices_to_delete, 1.0, 'ADD')
#                
#                bpy.ops.object.mode_set(mode='EDIT')
#                # Select vertices to delete
#                bpy.ops.mesh.select_all(action='DESELECT')
#                bpy.ops.object.vertex_group_set_active(group_index=0)
#                bpy.ops.object.vertex_group_select()
#                bpy.ops.mesh.delete(type='VERT')

#                # Return to object mode
#                bpy.ops.object.mode_set(mode='OBJECT')

#                # Loop through vertices
#                for vertex in mesh.vertices:
#                    # Check if the vertex is outside the boundary defined by Aruco codes
#                    # You can implement a suitable condition here based on the boundary points
#                    if not is_inside_boundary(vertex.co, max_x, min_x, max_y, min_y):
#                        vertices_to_delete.append(vertex)

#                # Delete the vertices
#                bpy.context.view_layer.objects.active = obj
##        bpy.ops.object.mode_set(mode='EDIT')
#                bpy.ops.object.mode_set(mode='EDIT')
#                bpy.ops.mesh.select_all(action='DESELECT')
##                bpy.ops.object.mode_set(mode='OBJECT')

#                for vertex in vertices_to_delete:
#                    vertex.select = True
#                
##                bpy.ops.mesh.select_all(action='DESELECT')
##                bpy.ops.object.vertex_group_set_active()
##                bpy.ops.object.vertex_group_select()
#                bpy.ops.mesh.delete(type='VERT')

##                bpy.ops.object.mode_set(mode='EDIT')
##                bpy.ops.mesh.delete(type='VERT')

#                # Return to object mode
#                bpy.ops.object.mode_set(mode='OBJECT')
                
                print("Done!")

            else:
                print("Mesh has no vertices.")

        else:
            print("Active object is not a mesh.")

    else:
        print("Four Aruco codes not detected in the image.")

cv_trim_preprocess()