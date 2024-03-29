# raspberry_pi.py
# In charge of taking a picture, counting
# and sending info to the server

# Libraries
import argparse
import sys

import torch
import cv2
import numpy as np
import picamera
import math

import threading
import time
import logging
import os

import socket

print("Starting script...")

# Supress YOLOv5 Logging
logging.getLogger("utils.general").setLevel(logging.WARNING)  # yolov5 logger

# Parse Arguments
parser = argparse.ArgumentParser(description='Client for Canteen Queue Counter')
parser.add_argument('--confidence_threshold', type=float, default=0.3, help='Minimum confidence for inference to be considered')
parser.add_argument('--debug', default=False, action="store_true", help='Turns on debug logging')
parser.add_argument('--image_debug', default=False, action="store_true", help='Turns on image debugging')
parser.add_argument('--ip', type=str, default="127.0.0.1", help='IP Address of Socket Server')
parser.add_argument('--port', type=int, default=6942, help='Port of Socket Server')
args = parser.parse_args()

# Variables
debug = args.debug
image_debug = args.image_debug

server_ip = args.ip
server_port = args.port

# Read credentials
cred_path = os.path.join(os.path.dirname(__file__), "../misc/credentials.txt")
credentials = {}

with open(cred_path, "r") as f:
    for line in f:
       (key, val) = line.split("=")
       credentials[key] = val
    f.close()

try:
    password = credentials["password"].strip("\n")
except KeyError:
    print("[FATAL] Password not found in credentials.txt")
    sys.exit(1)

W, H = 640, 640   # Width and height of cut image

interval = 30     # Seconds before running program again

try:
    model = torch.hub.load("ultralytics/yolov5", "custom", path="crowdhuman_yolov5m.pt")
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
            with picamera.PiCamera() as camera:
                camera.resolution = (320, 240)
                camera.framerate = 24
                time.sleep(2)
                image = np.empty((240 * 320 * 3,), dtype=np.uint8)
                camera.capture(image, 'bgr')
                image = image.reshape((240, 320, 3))

                # ret, frame = cam.read()
                # if not ret:  # Handle camera failing to take picture
                #     time.sleep(5)
                #     continue

                # Save picture
                queue.image = image

        # Crop image
        queue.cutImage()

        # Get start time
        start_time = time.time()

        # Get number of people in image
        debug_print("[DEBUG] Counting people...")
        people_count = queue.countPeople()

        # Connect to server and send data
        # Connect to server
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            debug_print("[DEBUG] Socket Created!")
        except socket.error as error:
            print("[FATAL] Error while creating Socket!")
            print("Error Log: " + str(error))
            print("Recovering...")
            time.sleep(10)
            continue

        try:
            sock.connect((server_ip, server_port))
            debug_print(f"[DEBUG] Connected to {server_ip}:{server_port}")
        except socket.error as error:
            print("[FATAL] Error while connecting to server!")
            print("Error Log: " + str(error))
            print("Recovering...")
            time.sleep(10)
            continue

        queue_time = queue.getQueueTime(people_count)

        # Send data
        data = password + "|" + queue.stallName + "|" + str(queue_time)
        debug_print("[DEBUG] Sending data: " + data)
        sock.send(data.encode())

        # Wait for server to send back ACK and close socket
        sock.recv(1024)
        sock.close()
        debug_print(f"[DEBUG] ACK Received, waiting for {interval} seconds...")

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