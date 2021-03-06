# python3
#
# Copyright 2019 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Example using TF Lite to detect objects with the Raspberry USB webcam."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import io
import re
import time
import requests
import datetime

import numpy as np
import cv2

from tflite_runtime.interpreter import Interpreter

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--model', type=str, default='./models/detect.tflite', help='File path of .tflite file.', required=False)
parser.add_argument('--labels', default='./models/coco_labels.txt', type=str, help='File path of labels file.', required=False)
parser.add_argument('--threshold', default=0.55, type=float, help='Score threshold for detected objects.', required=False) 
args = parser.parse_args()

CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

def load_labels(path):
  """Loads the labels file. Supports files with or without index numbers."""
  with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    labels = {}
    for row_number, content in enumerate(lines):
      pair = re.split(r'[:\s]+', content.strip(), maxsplit=1)
      if len(pair) == 2 and pair[0].strip().isdigit():
        labels[int(pair[0])] = pair[1].strip()
      else:
        labels[row_number] = pair[0].strip()
  return labels


def set_input_tensor(interpreter, image):
  """Sets the input tensor."""
  tensor_index = interpreter.get_input_details()[0]['index']
  input_tensor = interpreter.tensor(tensor_index)()[0]
  input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
  """Returns the output tensor at the given index."""
  output_details = interpreter.get_output_details()[index]
  tensor = np.squeeze(interpreter.get_tensor(output_details['index']))
  return tensor


def detect_objects(interpreter, image, threshold):
  """Returns a list of detection results, each a dictionary of object info."""
  set_input_tensor(interpreter, image)
  interpreter.invoke()

  # Get all output details
  boxes = get_output_tensor(interpreter, 0)
  classes = get_output_tensor(interpreter, 1)
  scores = get_output_tensor(interpreter, 2)
  count = int(get_output_tensor(interpreter, 3))

  results = []
  for i in range(count):
    if scores[i] >= threshold:
      result = {
          'bounding_box': boxes[i],
          'class_id': classes[i],
          'score': scores[i]
      }
      results.append(result)
  return results


def annotate_objects(frame, results, labels):
  """Draws the bounding box and label for each object in the results."""
  for obj in results:
    # Convert the bounding box figures from relative coordinates
    # to absolute coordinates based on the original resolution
    ymin, xmin, ymax, xmax = obj['bounding_box']
    xmin = int(xmin * CAMERA_WIDTH)
    xmax = int(xmax * CAMERA_WIDTH)
    ymin = int(ymin * CAMERA_HEIGHT)
    ymax = int(ymax * CAMERA_HEIGHT)

    # Overlay the box, label, and score on the camera preview
    print('--------------------------------')
    print('  id:    ', labels[obj['class_id']])
    print('  score: ', obj['score'])
    print('  bbox:  ', [xmin, ymin, xmax, ymax])
    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 3)
    cv2.putText(frame, '%s  %.2f' % (labels[obj['class_id']], obj['score']), (xmin, ymin), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
    


def main():
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
    ret, image = capture.read()
    frame =  cv2.resize(image, (0, 0), fx=1, fy=1)
    frame_re = cv2.resize(frame, dsize=(input_width, input_height))
    starttime = time.time()
    results = detect_objects(interpreter, frame_re, args.threshold)
      
    annotate_objects(frame, results, labels)
    elapsed_ms = (time.time() - starttime)
    
    if elapsed_ms != 0:
        fps = 1 / (elapsed_ms)
        str = 'FPS: %0.1f' % fps
        cv2.putText(frame, str, (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)    

    cv2.imshow("res", frame)

    now = datetime.datetime.now().strftime("%d_%H-%M-%S")
    k = cv2.waitKey(1) & 0xff

    #Stop
    if k == ord('q') or k == 27:
      break
    #Capture (Original)
    elif k == ord('c'):
        print('Capture (Original)')
        cv2.imwrite("./" + now + ".png", image)
    #Capture (Detection)
    elif k == ord('C'):
        print('Capture (Detection)')
        cv2.imwrite("./" + now + ".png", frame)
    #Start Record (Original)
    elif k == ord('r'):
        print("Start Record (Original)")
        record_org = True
        video = cv2.VideoWriter("./" + now + ".avi", fourcc, 20.0, (image.shape[1], image.shape[0]))
    #Start Record (Detection)
    elif k == ord('R'):
        print("Start Record (Detection)")
        record = True
        video = cv2.VideoWriter("./" + now + ".avi", fourcc, 20.0, (frame.shape[1], frame.shape[0]))
    #Stop Record
    elif k == ord('s'):
        print("Stop Record")
        record_org = False
        record = False
        
    if record_org == True:            
        video.write(image)
    if record == True:            
        video.write(frame)

  capture.release()
  cv2.destroyAllWindows()

if __name__ == '__main__':
  main()
