from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import io
import re
import time
import requests
import datetime
import cv2

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

    
if __name__ == '__main__':
  labels = load_labels(args.labels)
  interpreter = Interpreter(args.model)
  interpreter.allocate_tensors()
  _, input_height, input_width, _ = interpreter.get_input_details()[0]['shape']
  
  fourcc = cv2.VideoWriter_fourcc(*'XVID')
  record_org = False
  record = False
  
  capture = cv2.VideoCapture(0)

  if (capture.isOpened() == False):
    print("NO CAMERA!")
  
  # Video frame settings.
  capture.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
  capture.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
  capture.set(cv2.CAP_PROP_FPS, 30)
  
  cnt=0

  while True:
    ret, frame = capture.read()

    cv2.imshow("res", frame)

    now = datetime.datetime.now().strftime("%d_%H-%M-%S")
    k = cv2.waitKey(1) & 0xff

    #Stop
    if k == ord('q') or k == 27:
      break
    #Capture (Original)
    elif k == ord('c'):
        print('Capture (Original)')
        cv2.imwrite("./" + now + ".png", frame)
    #Start Record (Original)
    elif k == ord('r'):
        print("Start Record (Original)")
        record_org = True
        video = cv2.VideoWriter("./" + now + ".avi", fourcc, 30.0, (frame.shape[1], frame.shape[0]))
    #Stop Record
    elif k == ord('s'):
        print("Stop Record")
        record_org = False
        
    if record_org == True:            
        video.write(frame)

  capture.release()
  cv2.destroyAllWindows()
