import huskylib
from huskylib import HuskyLensLibrary
import argparse

parser=argparse.ArgumentParser(description="Test script to make sure that camera is connected")
parser.add_argument("--port",type=hex)
args = parser.parse_args()

cam=HuskyLensLibrary("I2C","",address=args.port)
print(cam.knock())
