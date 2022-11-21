import huskylib
from huskylib import HuskyLensLibrary
import argparse

parser=argparse.ArgumentParser(description="Test script to make sure that camera is connected")
parser.add_argument("--port",type=hex)

cam=HuskyLensLibrary("I2C","",address=0x32)
print(cam.knock())
