# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 09:15:16 2024

@author: user

This script is designed for object detection in video streams using the YOLOv5 model. It captures video frames, and processes them to detect objects. 
The script uses multi-threading to improve performance by simultaneously reading frames andperforming object detection. 
Additionally, it listens for a keyboard interrupt (ESC key) to gracefully terminate the process.
"""

import cv2  # For handling video capture and image operations
import threading  # For running tasks in parallel
import os  # For file path operations
import sys  # For adding the YOLOv5 directory to the system path
import tempfile  # For creating temporary files for image processing
import keyboard  # For detecting ESC key press to terminate the script
import pandas as pd  # For creating and updating Excel files
from collections import defaultdict  # For creating a dictionary with default values
import supervision as sv  # For counting unique objects in detection results
import numpy as np  # For array operations
from datetime import datetime  # For timestamping detection events
import time

# Add YOLOv5 directory to the system path to import custom functions
yolov5_path = "../yolov5_farwest"  # Adjust the path as necessary
sys.path.append(yolov5_path)

# Import custom detection functions from the YOLOv5 implementation
from detect import run, load_model

# YOLO model parameters
weights = os.path.join(yolov5_path, 'check.pt')  # Path to model weights file
iou_thres = 0.05  # Intersection Over Union threshold for determining detection accuracy
conf_thres = 0.65  # Confidence threshold for detecting objects
augment = False  # Whether to use image augmentation during detection
debug_save = False  # Whether to save debug images
device = "CPU"  # Specify the device to use for inference ('CPU' or 'GPU')

# Load the YOLO model with the specified parameters
model, stride, names, pt = load_model(weights=weights, device=device)

# Initialize variables for frame processing and detection counts
ct = defaultdict(int)  # Dictionary to count detected objects by category
current_frame = None  # Variable to store the current frame for processing
frame_lock = threading.Lock()  # Lock for thread-safe operations on the current frame
stop_threads = False  # Flag to control the stopping of threads
frame_counter = 0  # Counter for processed frames
total_duration = 0
use_sv = True # Use supervision for counting unique objects
sv_cons_frames = 4 # Number of consecutive frames to consider an object as detected
# KMP_DUPLICATE_LIB_OK=TRUE
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# def unflatten(input_string):
#     """
#     Reformat a flat input string from detection output into a structured format.
#     """
#     values = input_string.split(',')
#     first_value = values[0]
#     grouped_values = [values[i:i+3] for i in range(1, len(values), 3)]
#     return first_value, grouped_values

# def count_first_items(matrix, counts):
#     """
#     Count occurrences of the first item in each inner list of a 2D list (matrix).
#     """
#     for inner_list in matrix:
#         if inner_list:
#             first_item = inner_list[0]
#             if int(first_item) in counts:
#                 counts[int(first_item)] += 1
#     return counts

def read_frames(cap):
    """
    Continuously read frames from the video capture device.
    """
    global current_frame, stop_threads
    while not stop_threads:
        if keyboard.is_pressed('esc'):  # Listen for ESC key to stop
            stop_threads = True
            break
        ret, frame = cap.read()
        if not ret:
            stop_threads = True
            break
        with frame_lock:
            current_frame = frame

def detect_and_display():
    """
    Perform object detection on captured frames and display the results.
    """
    global current_frame, stop_threads, frame_counter, ct, total_duration
    tracker = sv.ByteTrack()            # Bytetrack takes a number of optional arguments, TODO tuning
    seen_ids = []
    consecutive_frames = defaultdict(int)

    while not stop_threads:
        start_time = time.time()
        if keyboard.is_pressed('esc'):  # Listen for ESC key to stop
            stop_threads = True
            break

        local_frame = None
        with frame_lock:
            if current_frame is not None:
                local_frame = current_frame.copy()
                current_frame = None

        if local_frame is not None:
            # Run detection on the temporary image file
            output = run(weights=weights, source=local_frame, iou_thres=iou_thres,
                         conf_thres=conf_thres, augment=augment, model=model, stride=stride,
                         names=names, pt=pt, debug_save=debug_save)

            if not use_sv:
                # Every 10 frames
                if frame_counter % 14 == 0:
                    for detection in output:
                        ct[detection[2]] += 1
            else:
                # Turn the first element in each tuple in output list into a np array
                xyxy = np.array([np.array([int(d[0][0]), int(d[0][1]), int(d[0][2]), int(d[0][3])]) for d in output])
                # Second element is the confidence score
                confs = np.array([d[1] for d in output])
                # Third element is the category id
                labels = np.array([d[2] for d in output])

                # Feed this to supervision
                detections = sv.Detections(xyxy, confidence=confs, class_id=labels)
                detections = tracker.update_with_detections(detections)

                try:
                    for class_id, tracker_id in zip(detections.class_id, detections.tracker_id):
                        if tracker_id not in seen_ids:
                            consecutive_frames[tracker_id] += 1
                            if consecutive_frames[tracker_id] >= sv_cons_frames:
                                seen_ids.append(tracker_id)
                                seen_ids = seen_ids[-30:]
                                ct[class_id] += 1
                        # Delete IDs that are not tracked consistently
                        if tracker_id not in detections.tracker_id:
                            consecutive_frames.pop(tracker_id, None)
                except TypeError as e:
                    # Sometimes the detections are empty, and zip doesn't like that
                    print(e)
                    pass


                
            end_time = time.time()

            # Calculate and accumulate the duration
            duration = end_time - start_time
            total_duration += duration
            frame_counter += 1            
            
            # print(f"Received response for frame {frame_counter}: ", response_msg)
            print(f"Duration for this frame: {duration:.3f} seconds")
            # print ("==================================")



def send_image(video_path):
    """
    Main function to start the video capture and processing threads.
    """
    global stop_threads, ct
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    # Start the frame reading and detection threads
    thread_read = threading.Thread(target=read_frames, args=(cap,))
    thread_detect = threading.Thread(target=detect_and_display)
    thread_read.start()
    thread_detect.start()

    # Wait for both threads to finish
    thread_read.join()
    thread_detect.join()
    
    # Print the total duration after all frames are processed
    print("")
    print("")
    print("")
    print(f"Total duration for {frame_counter} frames: {total_duration:.3f} seconds")
    # Print the detection counts
    # Format: {category_id: count}
    count = pd.DataFrame(ct.items(), columns=['Category', 'Count'])
    print ("count",dict(ct))
    for class_id, count in dict(ct).items():
        print(f'{model.names[class_id]}: {count}')
    stop_threads = True
    cap.release()
    
# Paths and parameters for video processing
video_path = "../recycle_small_test_slow.mp4"
send_image(video_path)
