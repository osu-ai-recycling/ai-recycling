# -*- coding: utf-8 -*-
"""
Created on Thu Jan 18 06:37:13 2024

@author: aadi
"""

""""client code with threading (read and send image on thread to server on socket) 
which also displays image on streamlit website"""

import socket
import threading
import cv2
import time

# Global variables to store the current frame and control thread execution
current_frame = None
hold_frame = None
frame_lock = threading.Lock()
stop_threads = False
total_duration = 0
frame_counter = 0

# Create a socket for TCP communication
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server at the specified host and port
host = "localhost"
port = 8008
sock.connect((host, port))
print(f"Connected to {host}:{port}")


def unflatten(input_string):
    # Split the input string into a list of values
    values = input_string.split(',')

    # Extract the first value
    first_value = values[0]

    # Create a list of groups of three values (excluding the first one)
    grouped_values = [values[i:i+3] for i in range(1, len(values), 3)]

    return grouped_values

def draw_centroids_on_frame(frame, centroids):
    for centroid in centroids:
        label, x, y = centroid
        # Convert x and y to integers
        x, y = int(float(x)), int(float(y))
        # Draw a circle at the centroid position
        cv2.circle(frame, (x, y), 20, (0, 255, 0), -1)
        # Optionally, put the label number near the centroid
        cv2.putText(frame, str(label), (x, y), cv2.FONT_HERSHEY_DUPLEX, 5, (255, 0, 0), 5,cv2.LINE_AA)


def read_frames(cap):
    # Thread function to continuously read frames from the video
    global current_frame, stop_threads, hold_frame
    while not stop_threads:
        ret, frame = cap.read()
        if not ret:
            stop_threads = True
            break
        with frame_lock:
            current_frame = frame
            
def send_and_receive_frames():
    # Thread function to send the current frame and receive a response
    global current_frame, stop_threads, frame_counter, total_duration, hold_frame
    while not stop_threads:
        with frame_lock:
            if current_frame is not None:
                start_time = time.time()
                # Encode the current frame as JPEG
                _, img_encoded = cv2.imencode(".jpg", current_frame)
                img_bytes = img_encoded.tobytes()
                img_len_bytes = len(img_bytes).to_bytes(4, 'little', signed=False)
                hold_frame = current_frame

                # Send the frame length followed by the frame itself
                sock.sendall(img_len_bytes)
                sock.sendall(img_bytes)
                current_frame = None  # Reset current frame after sending

        # Receive response from the server
        response_len_bytes = sock.recv(4)
        response_len = int.from_bytes(response_len_bytes, 'little')
        response = sock.recv(response_len)
        response_msg = response.decode()
        
        grouped_values = unflatten(response_msg)
        
        with frame_lock:
                if current_frame is not None and grouped_values:
                    draw_centroids_on_frame(hold_frame, grouped_values)
                    hold_frame_r = cv2.resize(hold_frame,(640,640))
                    cv2.imwrite('C:/Users/user/Spyder Project/YOLOv5/yolov5_farwest/latest_frame.jpg', hold_frame_r)  # Save the frame

                
        end_time = time.time()

        # Calculate and accumulate the duration
        duration = end_time - start_time
        total_duration += duration
        frame_counter += 1            
        
        # print(f"Received response for frame {frame_counter}: ", response_msg)
        print(f"Duration for this frame: {duration:.3f} seconds")
        print ("==================================")
        

def send_image(image_path):
    # Main function to handle video capture and threading
    global current_frame, stop_threads
    cap = cv2.VideoCapture(image_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # Read the first frame and set it as the current frame
    ret, frame = cap.read()
    if ret:
        current_frame = frame
    else:
        print("Error: Could not read the first frame.")
        cap.release()
        return

    # Create and start threads for reading frames and sending/receiving data
    thread_read = threading.Thread(target=read_frames, args=(cap,))
    thread_send_receive = threading.Thread(target=send_and_receive_frames)
    thread_read.start()
    thread_send_receive.start()

    # Wait for threads to complete
    thread_read.join()
    thread_send_receive.join()

    # Print the total duration after all frames are processed
    print("")
    print("")
    print("")
    print(f"Total duration for {frame_counter} frames: {total_duration:.3f} seconds")

    # Clean up
    stop_threads = True
    cap.release()

# Replace 'image_path' with the path to your video
image_path = "../far_west_test_video.mp4"
send_image(image_path)
# Close the socket
sock.close()