# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 09:15:16 2024

@author: user

This script is designed for object detection in video streams using the YOLOv5 model. 
It captures video frames, and processes them to detect objects. 
The script uses multi-threading to improve performance by simultaneously reading frames andperforming object detection. 
Additionally, it listens for a keyboard interrupt (ESC key) to gracefully terminate the process.
Uses supervision module to track objects and perform counting
"""

import cv2  # For handling video capture and image operations
import threading  # For running tasks in parallel
import os  # For file path operations
import sys  # For adding the YOLOv5 directory to the system path
import tempfile  # For creating temporary files for image processing
import tempfile  # For creating temporary files for image processing
import keyboard  # For detecting ESC key press to terminate the script
import pandas as pd  # For creating and updating Excel files
from collections import defaultdict  # For creating a dictionary with default values
import supervision as sv  # For counting unique objects in detection results
import numpy as np  # For array operations
from datetime import datetime  # For timestamping detection events
from math import sqrt
import argparse
import time
import supervision as sv  # For counting unique objects in detection results


# Paths and parameters for video processing
parser = argparse.ArgumentParser()
parser.add_argument('--hpc', dest='is_hpc', action='store_const',
                    const=True, default=False,
                    help='Run on HPC config')
args = parser.parse_args()

# Add YOLOv5 directory to the system path to import custom functions
yolov5_path = "../yolov5_farwest"  # Adjust the path as necessary
sys.path.append(yolov5_path)

# Import custom detection functions from the YOLOv5 implementation
from detect import run, load_model

# YOLO model parameters
#weights = os.path.join(yolov5_path, 'check.pt')  # Path to model weights file
weights = 'check_openvino_model'
iou_thres = 0.05  # Intersection Over Union threshold for determining detection accuracy
conf_thres = 0.65  # Confidence threshold for detecting objects
augment = False  # Whether to use image augmentation during detection
debug_save = False  # Whether to save debug images
device = "0" if args.is_hpc else "CPU"  # Specify the device to use for inference ('CPU' or 'GPU')
response_as_bbox = True

# Load the YOLO model with the specified parameters
model, stride, names, pt = load_model(weights=weights, device=device)

# Initialize variables for frame processing and detection counts
ct = defaultdict(int)  # Dictionary to count detected objects by category
ct = defaultdict(int)  # Dictionary to count detected objects by category
frame_counter = 0  # Counter for processed frames
total_duration = 0
use_sv = True # Use supervision for counting unique objects
sv_cons_frames = 4 # Number of consecutive frames to consider an object as detected
# KMP_DUPLICATE_LIB_OK=TRUE
os.environ['KMP_DUPLICATE_LIB_OK']='True'
count_read = 0

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

def intersect (b1: list, b2: list) -> bool:
    """
    Takes two bounding boxes and determines if there's an intersection

    @param b1: the first bounding box (format: [xmin, ymin, xmax, ymax])
    @param b2: the second bounding box (format: [xmin, ymin, xmax, ymax])
    """

    x_overlap = (b1[0] <= b2[0] <= b1[2]) or (b1[0] <= b2[2] <= b1[2])
    y_overlap = (b1[1] <= b2[1] <= b1[3]) or (b1[1] <= b2[3] <= b1[3])

    return x_overlap and y_overlap

def centroid(box: list) -> tuple[int, int]:
    """
    Takes a bounding box as input and returns its centroid as a tuple.

    @param box: the bounding box (format: [xmin, ymin, xmax, ymax])
    """
    
    xmin, ymin, xmax, ymax = box[0], box[1], box[2], box[3]

    return ((xmin+xmax)/2, (ymin+ymax)/2)

def get_occluded (boxes: list, confidences: list) -> list:
    """
    Detects occlusions and returns a list of indices for which objects should be ignored.

    @param boxes: a list of bounding boxes (format is [xmin, ymin, xmax, ymax])
    @param confidences: a list of confidences so the ith confidence corresponds to the ith box
    """
    
    indices_to_remove = []

    for i, box_a in enumerate(boxes):
        for j, box_b in enumerate(boxes):
            # ignore boxes we don't need to calculate
            # if j is less than or equal to i, they've already been compared
            if j <= i:
                continue

            if intersect(box_a, box_b):
                centroid_a = centroid(box_a)
                centroid_b = centroid(box_b)

                # get diagonal of each box
                diagonal_a = sqrt((box_a[2] - box_a[0])**2 + (box_a[3] - box_a[1])**2)
                diagonal_b = sqrt((box_b[2] - box_b[0])**2 + (box_b[3] - box_b[1])**2)

                # calculate area of each box
                area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[0])
                area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[0])

                # calculate area difference ratio
                size_diff_ratio = abs(area_a - area_b) / max(area_a, area_b)

                # size threshold, for example, 0.5 means the size difference should not exceed 50%
                size_threshold = 0.5

                # sum of diagonal of each box, and take 1/8 of the sum, use it as the distance threshold
                dist_threshold = (diagonal_a + diagonal_b)/8

                # if the euclidean distance between the centroids is greater than the threshold, ignore
                # if the size difference ratio is smaller than the threshold, ignore
                centroid_distance = sqrt((centroid_b[0] - centroid_b[0])**2 + (centroid_a[1] - centroid_b[1])**2)
                if (centroid_distance > dist_threshold) and (size_diff_ratio < size_threshold):
                    continue
                
                # ignore the item with lower confidence
                if confidences[i] > confidences[j]:
                    indices_to_remove.append(j)
                else:
                    indices_to_remove.append(i)
    
    return indices_to_remove

def pickup_order(output: list) -> list:
    """
    Takes output from modified run() and returns it in the optimal order
    to pick it up in.

    @param output: tuple (box: list, conf: float, cls: int)
                   for the bounding box, confidence, and class
    """

    # extract boxes and confidences
    boxes = list(map(lambda obj: obj[0], output))
    confs = list(map(lambda obj: obj[1], output))

    # figure out which boxes to ignore and remove them from the list
    occluded_indices = get_occluded(boxes, confs)
    boxes = [box for i, box in enumerate(boxes) if i not in occluded_indices]

    # return sorted by ymin
    return sorted(boxes, key = lambda b: b[1], reverse=False)

def detect_and_display(cap):
    """
    Perform object detection on captured frames and display the results.
    """
    global frame_counter, total_duration
    tracker = sv.ByteTrack()            # Bytetrack takes a number of optional arguments, TODO tuning
    box_annotator = sv.BoxAnnotator()
    label_annotator = sv.LabelAnnotator(text_scale=2, text_thickness=3)
    seen_ids = []
    consecutive_frames = defaultdict(int)
    
    while True:
        start_time = time.time()
        if not args.is_hpc:
            if keyboard.is_pressed('esc'):  # Listen for ESC key to stop
                return False
    
        ret, local_frame = cap.read()
        if not ret:
            return False
        
        # Run detection on the temporary image file
        output = run(weights=weights, source=local_frame, iou_thres=iou_thres,
                        conf_thres=conf_thres, augment=augment, model=model, stride=stride,
                        names=names, pt=pt, debug_save=debug_save)
                
        # cv2.imshow('Object Detection', local_frame)
        # cv2.waitKey(1) 
        
        if not response_as_bbox:
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

            try:
                # Feed this to supervision
                detections = sv.Detections(xyxy, confidence=confs, class_id=labels)
                detections = tracker.update_with_detections(detections)

                anno_labels = [
                    f'{tracker_id}: {model.names[class_id]}'
                    for class_id, tracker_id
                    in zip(detections.class_id, detections.tracker_id)
                ]

                local_frame = box_annotator.annotate(local_frame, detections)
                local_frame = label_annotator.annotate(local_frame, detections=detections, labels=anno_labels)

                for _, (class_id, count) in enumerate(ct.items()):
                    # print(f'{model.names[class_id]}: {count}')
                    cv2.putText(img=local_frame, text=f'{model.names[class_id]}: {count}', org=(200, (class_id+1)*150), fontFace=2, fontScale=3, color=(255,255,0), thickness=3)

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
                count = pd.DataFrame(ct.items(), columns=['Category', 'Count'])
            
            except (TypeError, ValueError) as e:
                # Sometimes the detections are empty, and zip doesn't like that
                print(e)
                pass


        resized_frame = cv2.resize(np.squeeze(local_frame), (1920, 1080))
        cv2.imshow('Object Detection', resized_frame)
        cv2.waitKey(5) 
        end_time = time.time()

        # Calculate and accumulate the duration
        duration = end_time - start_time
        total_duration += duration
        frame_counter += 1            
        
        # print(f"Received response for frame {frame_counter}: ", response_msg)
        # print(f"Duration for this frame: {duration:.3f} seconds")
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

    detect_and_display(cap)
    
    # Print the total duration after all frames are processed
    print("")
    print("")
    print("")
    print(f"Total duration for {frame_counter} frames: {total_duration:.3f} seconds")
    # Print the detection counts
    # Format: {category_id: count}
    count = pd.DataFrame(ct.items(), columns=['Category', 'Count'])
    print ("Final Count")
    for class_id, count in dict(ct).items():
        print(f'{model.names[class_id]}: {count}')
    #stop_threads = True
    cap.release()
    
send_image('udp://@127.0.0.1:1234?overrun_nonfatal=1&fifo_size=50000000') # Recovers from buffer overrun
# 'udp://@127.0.0.1:1234'
# rtsp://192.168.0.101:8090/stream
