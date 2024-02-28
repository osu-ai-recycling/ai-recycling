import cv2
import cv2.aruco as aruco

def count_aruco_codes(image_path):
    # Load the image
    image = cv2.imread(image_path)
    
    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Define the ArUco dictionary
    aruco_dict = aruco.Dictionary_get(aruco.DICT_6X6_250)
    
    # Initialize the ArUco detector parameters
    parameters = aruco.DetectorParameters_create()
    
    # Detect ArUco markers in the image
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    # Count the number of detected markers
    num_markers = len(ids) if ids is not None else 0
    
    return num_markers

# Example usage:
image_path = 'preprocess.png'
num_aruco_codes = count_aruco_codes(image_path)
print("Number of ArUco codes detected:", num_aruco_codes)
