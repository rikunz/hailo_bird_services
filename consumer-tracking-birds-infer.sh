#!/bin/bash
rm -f /tmp/infered*
source /home/thor/project/hailo_venv/bin/activate
python detection.py --hef-path yolov8s-new-best.hef --labels-json bird_labels.json
