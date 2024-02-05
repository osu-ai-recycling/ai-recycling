import cv2
import streamlit as st
from PIL import Image
import yolov5
import numpy as np
import time

# Load the image
image = Image.open('icon.png')

st.set_page_config(page_title="Cam stream Data - Demo", 
                   page_icon=image, 
                   initial_sidebar_state="expanded",
                   layout="wide")

# hide_streamlit_style = """
#             <style>
#             header {visibility: hidden;}
#             </style>
#             """
# st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.header("Webstream for Live Object Detection")
st.info("The Object Detection code is currently in development.", icon="ℹ️")
with st.container(border=True):
  st.caption("Currently work in progress for counting objects.")

@st.cache_resource
def load_model():
   model_load = yolov5.load('../check.pt')
   return model_load

model = load_model()

# cap=cv2.VideoCapture('Camera-url')
cap=cv2.VideoCapture(0)
placeholder = st.empty()


if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

while True:
    ret,frame=cap.read()
    if not ret:
        print("Error : Failed to capture frame")
        break
    # frame=cv2.resize(frame,(640,640))
    results = model(frame)
    
    frame=np.squeeze(results.render())
    placeholder.image(frame, channels="BGR", width = None)
    # time.sleep(0.7)

cap.release()
