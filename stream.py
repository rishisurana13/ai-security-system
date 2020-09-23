#!/usr/bin/env python
from flask import Flask, render_template, Response
import cv2
import socket
import io
import numpy as np


import os
app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming"""
    return render_template('index.html')

def gen():
    """Video streaming generator function."""
    frame = open('frame.jpg', 'rb').read() 
    i = 0

    while True:
        if i % 400 == 0:
            frame = open('frame.jpg', 'rb').read()   
        i += 1
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
       

@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)


        
    
        
    
