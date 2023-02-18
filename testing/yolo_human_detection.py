import torch
import cv2
import numpy as np

"""
Image Coords:
TOP LEFT:     404, 414
TOP RIGHT:    1461, 256
BOTTOM RIGHT: 1416, 792
BOTTOM LEFT:  441, 791
"""

model = torch.hub.load("ultralytics/yolov5", "yolov5m", pretrained=True)

# image = "D:\\python\\CanteenQueueEstimater\\testing\\front_queue.jpg"

W, H = 600, 200

img = cv2.imread("C:\\Users\\hbw30\\Downloads\\python.jpg")
pts0 = np.float32([[404, 414],[1461, 256],[1416, 792],[441, 791]])

# Define corresponding points in output image
pts1 = np.float32([[0,0],[W,0],[W,H],[0,H]])

# Get perspective transform and apply it
M = cv2.getPerspectiveTransform(pts0,pts1)
image = cv2.warpPerspective(img,M,(W,H))

results = model(image)

# results.print()
# print(results.xyxyn[0][:,-1].numpy())

results.show()

person_count = list(results.xyxyn[0][:,-1].numpy()).count(0.0)  # Get number of persons
print("Person Count:", person_count)