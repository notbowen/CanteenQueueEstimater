import huskylib
from huskylib import HuskyLensLibrary
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=lambda x: int(x, 0), default=0x32, required=True)

args = parser.parse_args()

cam = HuskyLensLibrary("I2C","",address=args.port)
print(cam.knock())
