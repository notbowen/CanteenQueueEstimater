# raspberry_pi.py
# In charge of taking a picture, counting
# and sending info to the server

# Libraries
import argparse
import math
import os
import sys
import requests

import torch
import cv2
import numpy as np

import threading
import time
import logging

print("Starting script...")

# Supress YOLOv5 Logging
logging.getLogger("yolov5").setLevel(logging.WARNING)

# Parse Arguments
parser = argparse.ArgumentParser(description='Client for Canteen Queue Counter')
parser.add_argument('--confidence_threshold', type=float, default=0.3, help='Minimum confidence for inference to be considered')
parser.add_argument('--debug', default=False, action="store_true", help='Turns on debug logging')
parser.add_argument('--image_debug', default=False, action="store_true", help='Turns on image debugging')
parser.add_argument('--url', type=str, default="http://localhost/", help='Url of flask server')
args = parser.parse_args()

# Variables
debug = args.debug
image_debug = args.image_debug

url = args.url  # TODO: Update this to default to webserver addr

auth_key = os.environ["QUEUE_AUTH_KEY"]
auth_token = os.environ["QUEUE_AUTH_TOKEN"]

W, H = 640, 640   # Width and height of cut image

interval = 30     # Seconds before running program again

cam = cv2.VideoCapture(0)  # Camera

try:
    model = torch.hub.load("ultralytics/yolov5", "custom", path="crowdhuman_yolov5m.pt")
    model.conf = args.confidence_threshold
except:
    print("[FATAL] Failed to load model!")
    print("[INFO]  Check if yolo_v5 crowdhuman is downloaded!")
    print("[INFO]  Link: https://drive.google.com/u/2/uc?id=1gglIwqxaH2iTvy6lZlXuAcMpd_U0GCUb&export=download&confirm=t")
    sys.exit(1)

# Canteen Queue Class
# Class for each single canteen stall
# Contains stall queue time (integer), Stall Name (string)
# Image and Image cut positions (list of 2 ints, arranged in top right, top left, bottom right, bottom left)
class Queue:
    def __init__(self, stallName : str, queueTime : int, imageCutPositions):
        self.stallName = stallName
        self.queueTime = queueTime
        self.image = None
        self.imageCutPositions = imageCutPositions

    # Function to cut image and flatten with 4 specified points (imageCutPositions)
    def cutImage(self):
        if image_debug:
            current_dir = os.path.dirname(__file__)
            img_path = os.path.join(current_dir, "../testing/queue_2.jpg")
            self.image = cv2.imread(img_path)
            return

        img = self.image

        # Define corresponding points in input image
        pts0 = np.float32(self.imageCutPositions)

        # Define corresponding points in output image
        pts1 = np.float32([[0,0],[W,0],[W,H],[0,H]])

        # Get perspective transform and apply it
        M = cv2.getPerspectiveTransform(pts0, pts1)
        image = cv2.warpPerspective(img, M, (W, H))

        self.image = image

    # Function to count num of people in CUT image, using YOLOv5 alogrithm
    def countPeople(self):
        results = model(self.image)
        person_count = list(results.xyxyn[0][:,-1].numpy()).count(1.0)
        return person_count

    # Function to get queue time based on number of ppl in mins
    def getQueueTime(self, people_count):
        secs = people_count * self.queueTime
        approx_mins = secs / 60

        if approx_mins < 1.0:
            return 0.9
        else:
            return "~" + str(math.ceil(approx_mins))


# Print in debug mode
def debug_print(msg):
    if debug:
        print(msg)


# Queue Handling Thread
def handle_queue(queue):
    """ Repeatedly take pictures of the queue, count the number of people and send to server """
    while True:
        debug_print("[DEBUG] Reading queue image...")

        # Take picture
        if not image_debug:
            ret, frame = cam.read()
            if not ret:  # Handle camera failing to take picture
                time.sleep(5)
                continue

            # Save picture
            queue.image = frame

        # Crop image
        queue.cutImage()

        # Get start time
        start_time = time.time()

        # Get number of people in image
        debug_print("[DEBUG] Counting people...")
        people_count = queue.countPeople()

        # Get queue time
        queue_time = queue.getQueueTime(people_count)

        # Send data to flask server
        authentication = {auth_key: auth_token}

        debug_print("[DEBUG] Sending data to server...")

        try:
            r = requests.post(url + f"/api/update_timing?stall_name={queue.stallName}&queue_time={queue_time}", headers=authentication)
            if r.status_code != 200:
                print("[ERROR] Received status code: " + str(r.status_code) + " from server!")
                print("[ERROR] Response: " + str(r.text))
        except Exception as e:
            print("[ERROR] Failed to send data to server!")
            print("Error Log: " + str(e))

        # Wait for interval
        if time.time() - start_time < interval:
            time.sleep(interval - (time.time() - start_time))


# Main Function
def main():
    # List of queues a Pi is supposed to handle
    # TODO: Add queues into this list
    # NOTE: This list is unique for every raspberry pi, depending on the stores it's in charge of
    queues = [Queue("Drinks", 120, [[0,0],[650, 0],[650,400],[0,500]])]

    # Loop through queues and start queue handling thread
    for queue in queues:
        debug_print("[DEBUG] Starting queue handling thread...")
        thread = threading.Thread(target=handle_queue, args=(queue,))
        thread.daemon = True
        thread.start()

    # Loop forever
    while True:
        time.sleep(60)


# Run Code
if __name__ == "__main__":
    main()
