import socket
import cv2
import numpy as np
import os
import sys
import tempfile
import time
import keyboard
import hashlib

video_path = "C:/Users/user/Downloads/try_small_test.mp4"


def id2(box):
    # Use hashlib to create a hash from the box coordinates
    hash_object = hashlib.md5(str(box).encode())
    return hash_object.hexdigest()[:4]

def start(video_path):

    # Add YOLOv5 folder to the sys.path
    # yolov5_path = "C:/Users/AI/Aditya_project/yolov5_aditya"
    yolov5_path = "C:/Users/user/Spyder Project/YOLOv5/yolov5_farwest"   # change back
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
    conf_thres = 0.5 # 0.35
    augment = True
    debug_save = False  # change to True if want to save image for debugging
    device = "CPU"
    fraction_hyp = 1/8
    centroid_y_low = 500,
    centroid_y_high = 750
    
    # Load the model
    model, stride, names, pt = load_model(weights=weights, device=device)
    
    video_path = video_path
    cap = cv2.VideoCapture(video_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter("C:/Users/user/Spyder Project/YOLOv5/yolov5_farwest" , cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    
    count_0 = 0
    count_1 = 0
    count_2 = 0
    count_3 = 0
    used = []
    
    
    while cap.isOpened():
        
        # Break the loop if 'q' key is pressed
        if keyboard.is_pressed('esc'):
                print("Script stopped.")
                sys.exit()
        ret, frame = cap.read()
           
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_img:
            temp_image_path = tmp_img.name
            cv2.imwrite(temp_image_path, frame)
            
        if ret:
            lst = run(
                        weights=weights,
                        source=temp_image_path,
                        iou_thres=iou_thres,
                        conf_thres=conf_thres,
                        augment=augment,
                        model=model,
                        stride=stride,
                        names=names,
                        pt=pt,
                        debug_save=debug_save,
                        fraction_hyp = fraction_hyp
                        )
        else:
            out.release()
            return frame
        
        
        for i in (lst):
            p1, p2 = (int(i[1][0]), int(i[1][1])), (int(i[1][2]), int(i[1][3]))
            # Calculate the centroid
            centroid_x = (i[1][0] + i[1][2]) // 2
            centroid_y = (i[1][1] + i[1][3]) // 2
            
            if (i[0]==0):
                cv2.circle(frame, (int(centroid_x), int(centroid_y)), 20, (0,255,0), -1)
            elif (i[0]==1):
                cv2.circle(frame, (int(centroid_x), int(centroid_y)), 20, (255,0,0), -1)
            elif (i[0]==2):
                cv2.circle(frame, (int(centroid_x), int(centroid_y)), 20, (255,225,0), -1)
            elif (i[0]==3):
                cv2.circle(frame, (int(centroid_x), int(centroid_y)), 20, (0,0,255), -1)
            
            if centroid_y > 475 and centroid_y < 525:
                if (id2([i[0],round(int(centroid_y),-1)])) not in used:
                    
                    if (i[0]==0):
                        count_0+=1
                    elif (i[0]==1):
                        count_1+=1
                    elif (i[0]==2):
                        count_2+=1
                    elif (i[0]==3):
                        count_3+=1
                    
                    used.append(id2([i[0],round(int(centroid_y),-1)]))

                    
        line_y = 500
        cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (255, 0, 0), 25)
        
        if len(used)==30:
            used.clear()
        
        print(count_0,count_1,count_2,count_3)
        out.write(frame)
        
        
        
        cv2.namedWindow('asd', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
        cv2.resizeWindow('asd', frame.shape[1], frame.shape[0])
        cv2.imshow('asd', frame)
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
        cv2.waitKey(1)  # 1 millisecond
        
                        
        os.remove(temp_image_path)
    
    
start(video_path)