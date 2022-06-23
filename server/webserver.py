# Flask Webserver to display Canteen Queue Times
# Updated via a POST request to /api/update_timing
# Displayed via GET request to /
# / should auto refresh once every minute

# Libraries
import flask
from flask import render_template, request

import os

# Flask init
app = flask.Flask(__name__)
app.config["DEBUG"] = True   # TODO: Change to False on production

# Variables

# Authentication key and token
auth_key = os.environ["QUEUE_AUTH_KEY"]
auth_token = os.environ["QUEUE_AUTH_TOKEN"]

# Stall names
stall_names = ["Drinks", "Snacks", "Malay 1", "Malay 2", "Western", "Chicken Rice", "Oriental Taste", "CLOSED"]

# Canteen queue times dict, passed to index.html
# Updated by POST request to /api/update_timing
timings = {}

# Init timings
for stall in stall_names:
    timings[stall] = "???"

# index.html
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", timings=timings)  # TODO: Write index.html

# API
# Update timings
@app.route("/api/update_timing", methods=["POST"])
def update_timing():
    # Check if auth key and token in request
    if auth_key not in request.headers:
        return "Invalid authentication key", 400

    if request.headers[auth_key] != auth_token:
        return "Invalid authentication token", 400

    # Check if canteen stall name and queue time in request
    if "stall_name" not in request.args:
        return "Missing stall name", 400
    
    if request.args["stall_name"] not in stall_names:
        return "Invalid stall name", 400

    if "queue_time" not in request.args:
        return "Missing queue time", 400

    # Update timings
    timings[request.args["stall_name"]] = request.args["queue_time"]

    return "Successfully updated timings", 200

# Get timings
@app.route("/api/get_timing", methods=["GET"])
def get_timing():
    # Check if stall name in request
    if "stall_name" not in request.args:
        return "Missing stall name", 400

    # Check if stall name is valid
    if request.args["stall_name"] not in stall_names:
        return "Invalid stall name", 400

    # Return queue time
    return timings[request.args["stall_name"]], 200

# Run server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)