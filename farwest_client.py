# -*- coding: utf-8 -*-
"""
Created on Sat Dec 23 22:18:46 2023

@author: aadi
"""

"sends all frames of a video over socket keeping it in queue, results in delay. Only for some usecases and test purpose"

import socket
import time
import cv2
from datetime import datetime
import numpy as np

# Create a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to the server
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

    return first_value, grouped_values

def count_first_items(matrix,counts):

    for inner_list in matrix:
        if inner_list:
            first_item = inner_list[0]
            if int(first_item) in counts:
                counts[int(first_item)] += 1

    return counts

def send_image(video_path):
    
    global sock
    # Load the image
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        exit()
        
    count = 0
    abc = False
    start = time.time()
    ct = {0: 0, 1: 0, 2: 0, 3: 0}
    while True:
        # Read a frame from the video
        ret, img = cap.read()
    
        # Check if the video has ended
        if not ret:
            break

        # Encode the image as JPEG before sending
        _, img_encoded = cv2.imencode(".jpg", img)
    
        # Convert the encoded image to bytes
        img_bytes = img_encoded.tobytes()
        
        
        # Get the length of the image data
        img_len = len(img_bytes)
    
        # Convert the image length to bytes
        img_len_bytes = img_len.to_bytes(4, 'little',signed=False)
        

        while True:
            before = time.time()
            # Send the image length over the socket to the server
            sock.sendall(img_len_bytes)
            # print("Image length sent to the server")
            
            # # Wait for a short delay (optional)
            # time.sleep(1)
        
            # Send the image data over the socket to the server
            sock.sendall(img_bytes)
            # print("Image sent to the server")
        
            
            #time.sleep(20)
            # recive response length
            response_len_bytes = sock.recv(4)
            response_len = int.from_bytes(response_len_bytes, 'little')
            
            # recive response
            response = sock.recv(response_len)
            response_msg = response.decode()
            
            # print("Recieved response length: ", response_len)
            print("Recieved response: ", response_msg)
            after = time.time()
            
            duration = after - before
            print("  inference time + server time: ", duration * 1000, " ms")
            print ("==================================")
            count+=1
            # print("count :",count)
            
            if (count%136 == 0):
                msg_copy = response_msg
                a,unflattened_lst = unflatten(msg_copy)
                check = count_first_items(unflattened_lst,ct)
                
            break
        
        if abc:
            break
    
    end = time.time() 
    dur = end - start
    print("  overall time taken is ", dur * 1000, " ms", " and created ",count, " frames. ")
    print ("count",check)
    
# Replace 'video_path' with the path to your video
video_path = "../recycle_small_test.mp4" # change back

send_image(video_path)

# Close the socket
sock.close()
