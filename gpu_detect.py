
import os
import argparse
import cv2
import numpy as np
import sys
from tensorflow.lite.python.interpreter import Interpreter
from toolbox import threat_presence, clear_dict, time_diff, reset_json_file, gen_vid_writer, output_mode, modify_json_field
import toolbox
import time
import threading
from main import main
import psutil



def object_detection(object_dict):

# Variables required to be intialized before program executes. 
    
    mode = output_mode()  
    MODEL_NAME = 'models/10oct'
    GRAPH_NAME = 'test.tflite'
    LABELMAP_NAME = 'label_map.txt'
    min_conf_threshold = 0.5
    resolution = '600x600'

    resW, resH = resolution.split('x')
    imW, imH = int(resW), int(resH)

    # Get path to current working directory
    CWD_PATH = os.getcwd()

    # Path to .tflite file, which contains the model that is used for object detection
    PATH_TO_CKPT = os.path.join(CWD_PATH, MODEL_NAME, GRAPH_NAME)

    # Path to label map file
    PATH_TO_LABELS = os.path.join(CWD_PATH, MODEL_NAME, LABELMAP_NAME)

    # Load the label map
    with open(PATH_TO_LABELS, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    # Load the Tensorflow Lite model and get details
    interpreter = Interpreter(model_path=PATH_TO_CKPT)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    floating_model = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    # Initialize webcam feed
    video = cv2.VideoCapture(0)
    ret = video.set(3, imW)
    ret = video.set(4, imH)
    object_dict = {
        "bat": 0,
        "handgun": 0,
        "knife": 0,
        "person": 0
    }
    while(True):
        try:
        # Acquire frame and resize to expected shape [1xHxWx3]
            ret, frame = video.read()

            frame_resized = cv2.resize(frame, (width, height))
            input_data = np.expand_dims(frame_resized, axis=0)

            curr_time_for_vid = str(time.ctime())
            cv2.putText(frame, curr_time_for_vid, (imW - 600, imH - 130),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
            # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
            if floating_model:
                input_data = (np.float32(input_data) - input_mean) / input_std

            # Perform the actual detection by running the model with the image as input
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            

            # Retrieve detection results
            # Bounding box coordinates of detected objects
            boxes = interpreter.get_tensor(output_details[0]['index'])[0]
            classes = interpreter.get_tensor(output_details[1]['index'])[
                0]  # Class index of detected objects
            scores = interpreter.get_tensor(output_details[2]['index'])[
                0]  # Confidence of detected objects
            # num = interpreter.get_tensor(output_details[3]['index'])[0]  # Total number of detected objects (inaccurate and not needed)

            # Loop over all detections and draw detection box if confidence is above minimum threshold
            for i in range(len(scores)):
                if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):

                    # Get bounding box coordinates and draw box
                    # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
                    ymin = int(max(1, (boxes[i][0] * imH)))
                    xmin = int(max(1, (boxes[i][1] * imW)))
                    ymax = int(min(imH, (boxes[i][2] * imH)))
                    xmax = int(min(imW, (boxes[i][3] * imW)))

                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (10, 255, 0), 2)

                    # Draw label
                    # Look up object name from "labels" array using class index
                    object_name = labels[int(classes[i])]

                    label = '%s: %d%%' % (object_name, int(
                        scores[i] * 100))  # Example: 'person: 72%'
                    labelSize, baseLine = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)  # Get font size
                    # Make sure not to draw label too close to top of window
                    label_ymin = max(ymin, labelSize[1] + 10)
                    # Make sure not to draw label too close to right of window
                    label_xmin = min(xmin, int(imH) - labelSize[0] - 10)

                    cv2.rectangle(frame, (label_xmin, label_ymin - labelSize[1] - 10), (label_xmin + labelSize[0],label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)  # Draw white box to put label text in
                    cv2.putText(frame, label, (label_xmin, label_ymin - 7),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)  # Draw label text

                    # This object dictionary will be sent to validate presence of a threat depending on certain conditions.
                    object_dict[object_name] += 1
                    # Display the dictionary of items detected.
                    cv2.putText(frame, (str(object_dict)), (0, 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            cv2.imwrite('frame.jpg',frame)
            yield frame,object_dict
            object_dict = clear_dict(object_dict)
        video.release()
            
    

def main():
    frame,object_dict = None,None
    start_time = time.ctime()
    out,out_threat = gen_vid_writer(video) 
        
    try:
        with tf.device('/device:GPU:0'): # Change GPU device params to actual value
            
            frame,object_dict = object_detection()
        if frame or object_dict != None:
            
            # If the next hour has come, then mode will be redetermined in outputmode(). params for mode are set in config.json 
            mode = output_mode()
            # Reset all dictionary values of threat dict so there is no overlap.
            
            # Object dict of all detected objects sent for validation. Threat is a boolean.         
            threat, threat_dict_send = threat_presence(object_dict, mode)
            # Send all data to the main function in main.py to decide course of action. 
            t1 = threading.Thread(target=main, args=(threat, threat_dict_send, frame))
            t1.start()
            if threat_dict_send != None:
                threat_dict_send = clear_dict(threat_dict_send)
            
            td_h = toolbox.td_h(start_time) # td_h == time diff in hours - i.e. td_h of 2.59 pm and 3 pm = 1 

            if td_h > 0:
                # If the next hour has come new video writer is generated, to write video for the next hour. this is for
                # uploading purposes. This ensures clips are segregated by hour.
                out,out_threat = gen_vid_writer(video)
                # Start time is updated so the function can determine when the next hour comes and condition's cycle resets.
                start_time = time.ctime()
                # Starts a thread to execute function to upload video of the previous hour to s3 bucket. 
                
                t3 = threading.Thread(target=upload_to_s3,args='saved_videos/')
                t3.start()

                
            # General footage video writer
            out.write(frame)
            if threat == True:
                # Threat specific video writer.
                out_threat.write(frame)


            except RuntimeError as e:
                print(e)
                break
            except KeyboardInterrupt:
                    # Reset all notification logs to avoid discrepancies when system restarts. 
                    reset_json_file('json/notification_log.json',"last_notified","notification_count")
                    modify_json_field('json/config.json',"current_mode","0")
                    break
                            

main()


    
