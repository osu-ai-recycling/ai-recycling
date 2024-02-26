# -*- coding: utf-8 -*-
"""
Created on Wed Dec 27 20:34:10 2023

@author: aadi
"""
"socket listener to farwest_client.py, runs model on recieved image"

import socket
import cv2
import numpy as np
import os
import sys
import tempfile
import time
import keyboard


# Add YOLOv5 folder to the sys.path
yolov5_path = "../yolov5_farwest"   # change back
# yolov5_path ="/home/aditya/aditya-work/yolov5_farwest/"
sys.path.append(yolov5_path)

# Import the run function
from detect import run, load_model

### YOLO model
weights = os.path.join(yolov5_path, 'check.pt')
print('check.pt')


iou_thres =0.05 # 0.05
conf_thres = 0.65 # 0.65
augment = True
debug_save = False  # change to True if want to save image for debugging
device = "CPU"
response_as_bbox = False

# Load the model
model, stride, names, pt = load_model(weights=weights, device=device)

# Create a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific address and port
host = "localhost"
port = 8008
sock.bind((host, port))

count = 0
total_time = 0
ct = {0: 0, 1: 0, 2: 0, 3: 0}

def count_first_items(matrix, counts):
    # Count occurrences of the first item in each sublist of a matrix
    for inner_list in matrix:
        if inner_list:
            first_item = inner_list[0]
            if int(first_item) in counts:
                counts[int(first_item)] += 1
    return counts

def unflatten(input_string):
    # Split the input string into a list of values
    values = input_string.split(',')

    # Extract the first value
    first_value = values[0]

    # Create a list of groups of three values (excluding the first one)
    grouped_values = [values[i:i+3] for i in range(1, len(values), 3)]

    return first_value, grouped_values

# Listen for incoming connections
sock.listen(1)
print(f"Listening on {host}:{port}")


while True:
    # Wait for a connection
    conn, addr = sock.accept()
    print(f"Connection established from {addr}")

    try:
        while True:
            # Receive the image length
            print("Waiting for image length")
            img_len_bytes = conn.recv(4)
            if not img_len_bytes:
                # print("Didn't recieve image length.")
                break

            # Convert the image length bytes to an integer
            # print("  image len in int: ", img_len_bytes, " len: ", len(img_len_bytes))
            img_len = int.from_bytes(img_len_bytes, "little", signed=False)
            # print("  Image data length : ",img_len)

            before = time.time()
            # Receive the image data
            image_data = b""

            # image_data = conn.recv(img_len)
            to_read_len = img_len
            data_len = 0
            while True:
                count += 1
                data = conn.recv(to_read_len)
                # print(len(data)," ", end="")
                data_len = len(data)

                image_data += data
                to_read_len -= data_len
                if to_read_len == 0:
                    break

            # print("  recieved image data",len(image_data))
            img_len = len(image_data)

            after = time.time()
            duration = after - before
            # print("  transmission time : ",duration * 1000,"ms")

            # If no more data is received, the connection is closed
            if not image_data:
                print("Connection closed by client.")
                break

            # Convert the image data to a NumPy array
            nparr = np.frombuffer(image_data, dtype=np.uint8)

            # Decode the NumPy array to an OpenCV image
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            # print("  Image size: ", img.shape)

            # Call the run function
            before = time.time()
            output = run(
                weights=weights,
                source=img,
                iou_thres=iou_thres,
                conf_thres=conf_thres,
                augment=augment,
                model=model,
                stride=stride,
                names=names,
                pt=pt,
                debug_save=debug_save,
                response_as_bbox = response_as_bbox,
            )
            
            if not response_as_bbox:
                # Every 10 frames
                if (count%9 ==0):
                    a,unflattened_lst = unflatten(output)
                    check = count_first_items(unflattened_lst, ct)
                    
                count+=1
                
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
                
            after = time.time()
            duration = after - before
            print("  inference time: ", duration * 1000, " ms")
            
            # encoding response
            response = output.encode()
            # print ("*** Detected : ", output[0], " objects")
            # print(response)
            
            if len(output) > 0:
                print ("*** Detected : ", output[:2], " objects")
            else:
                print ("*** No object detected")
                output = "0"
                
            # encoding rsponse lenghth
            response_len = len(response).to_bytes(4, "little", signed=False)

            # print('  Sending Response Length')
            conn.send(response_len)
            
            # print('Sending Response')
            conn.send(response)
            print ("==================================")
            # sys.exit(1)
    except Exception as e:
        print ("Exception: ", e)
        sys.exit(1)
        #pass
    
    print("")
    print("")
    print("")
    print("count:",check)
    conn.close()
    sys.exit(1)
