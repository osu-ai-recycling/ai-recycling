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
from detect import run, load_model
import mlflow
import glob

# Paths and parameters for video processing
parser = argparse.ArgumentParser()
parser.add_argument("video_path", type=str, help="Path to the video to read.")
parser.add_argument('--hpc', dest='is_hpc', action='store_const',
                    const=True, default=False,
                    help='Run on HPC config')
args = parser.parse_args()

artifacts_folder = "./artifacts"
RUNID = os.environ["RUN_ID"]
BASE_URI = os.environ["MLFLOW_TRACKING_URI"]

mlflow.set_tracking_uri(BASE_URI)
download_artifacts = False

if download_artifacts:
    mlflow.artifacts.download_artifacts(run_id=RUNID, dst_path = artifacts_folder)

weights_path = glob.glob(f"{artifacts_folder}/best.pt")

if weights_path is None:
    print("Unable to find local weights file.")
    exit(1)

# YOLO model parameters
weights = weights_path  # Path to model weights file
use_openvino = True  # Whether to use OpenVINO for inference
iou_thres = 0.05  # Intersection Over Union threshold for determining detection accuracy
conf_thres = 0.65  # Confidence threshold for detecting objects
augment = False  # Whether to use image augmentation during detection
debug_save = False  # Whether to save debug images
device = "0" if args.is_hpc else "CPU"  # Specify the device to use for inference ('CPU' or 'GPU')
response_as_bbox = True
if use_openvino:
    print("Exporting model to OpenVINO format...")
    weights = os.path.join(yolov5_path, 'check.pt')  # Path to model weights file
    command = f"python {yolov5_path}/export.py --weights {weights} --batch 1 --device CPU --iou {iou_thres} --conf {conf_thres} --include openvino"
    os.system(command) # This is a blocking call
    weights = f'{yolov5_path}/check_openvino_model'

    os.remove(f'{yolov5_path}/check.onnx') # Artifact of the openvino conversion process

    print("")
    print("###")
    print("###")
    print("Model exported to OpenVINO format.")
    print("Beginning inference with OpenVINO...")
    print("###")
    print("###")
    print("")
else:
    weights = os.path.join(yolov5_path, 'check.pt')  # Path to model weights file

# Load the YOLO model with the specified parameters
model, stride, names, pt = load_model(weights=weights, device=device)

# Initialize variables for frame processing and detection counts
ct = defaultdict(int)  # Dictionary to count detected objects by category
ct = defaultdict(int)  # Dictionary to count detected objects by category
current_frame = None  # Variable to store the current frame for processing
frame_lock = threading.Lock()  # Lock for thread-safe operations on the current frame
stop_threads = False  # Flag to control the stopping of threads
frame_counter = 0  # Counter for processed frames
total_duration = 0
use_sv = True # Use supervision for counting unique objects
sv_cons_frames = 4 # Number of consecutive frames to consider an object as detected
os.environ['KMP_DUPLICATE_LIB_OK']='True'


def read_frames(cap):
    """
    Continuously read frames from the video capture device.
    """
    global current_frame, stop_threads
    while not stop_threads:
        if not args.is_hpc:
            if keyboard.is_pressed('esc'):  # Listen for ESC key to stop
                stop_threads = True
                break
        ret, frame = cap.read()
        if not ret:
            stop_threads = True
            break
        with frame_lock:
            current_frame = frame

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
        if not args.is_hpc:
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
    

if __name__ == "__main__":
    send_image(args.video_path)

