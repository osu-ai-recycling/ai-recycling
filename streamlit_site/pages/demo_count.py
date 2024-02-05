# -*- coding: utf-8 -*-
"""
Created on Thu Feb  1 01:06:41 2024

@author: user
"""

import streamlit as st
from PIL import Image
import time
import os
import cv2

def load_latest_frame(frame_path):
    try:
        return cv2.imread(frame_path)
    except Exception as e:
        return None

frame_path = 'C:/Users/user/Spyder Project/YOLOv5/yolov5_farwest/latest_frame.jpg'

st.title('Real-time Frame Display')

# Display a placeholder that will be updated with the latest frame
frame_placeholder = st.empty()

while True:
    if os.path.exists(frame_path):
        frame = load_latest_frame(frame_path)
        if frame is not None:
            frame_resized = cv2.resize(frame,(640,640))
            frame_placeholder.image(frame_resized, caption='Latest Frame', use_column_width=True)
    time.sleep(0.1)  # Check for a new frame every 100ms
