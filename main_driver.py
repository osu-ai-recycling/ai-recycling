# -*- coding: utf-8 -*-
"""
Created on Sat Dec  2 03:44:37 2023

@author: user
"""

import socket
import cv2
import numpy as np
import os
import sys
import tempfile
import time
import keyboard
import hashlib


# Add YOLOv5 folder to the sys.path
yolov5_path = "C:/Users/user/Spyder Project/YOLOv5/yolov5_farwest"   # change back
# yolov5_path ="/home/aditya/aditya-work/yolov5_farwest/"
sys.path.append(yolov5_path)

# Import the run function
from detect import run, load_model

### YOLO model
# weights = os.path.join(yolov5_path, 'yolov5x_bottle.pt')  # Replace with the path to your model weights

### YOLO model - japan_trial_2-tranfer_learned.pt
weights = os.path.join(yolov5_path, 'best.pt')
print('recycle.pt')

### YOLO - OpenVINO optmized model
# weights = os.path.join(yolov5_path, "yolov5x_bottle_back_openvino_model")

iou_thres =0.15 # 0.15
conf_thres = 0.8 # 0.35
augment = True
debug_save = True  # change to True if want to save image for debugging
device = "CPU"

# Load the model
model, stride, names, pt = load_model(weights=weights, device=device)

video_path = "C:/Users/user/Downloads/RemoteX-Aditya/Far West/far_west_test_video.mp4"
# video_path = "C:/Users/user/Downloads/try_small_test.mp4"
# video_path ="/home/aditya/aditya-work/far_west_dataset_v3/far_west_test_video.mp4"
 
run(
    weights=weights,
    source=video_path,
    iou_thres=iou_thres,
    conf_thres=conf_thres,
    augment=augment,
    model=model,
    stride=stride,
    names=names,
    pt=pt,
    debug_save=debug_save,
    )

sys.exit()
            
