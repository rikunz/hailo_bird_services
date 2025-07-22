from pathlib import Path
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
import os
import numpy as np
import cv2
import hailo
from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad, get_numpy_from_buffer
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import app_callback_class
from detection_pipeline import GStreamerDetectionApp
from threading import Timer, Event
import time
import signal
from influxdb_client import Point
from nodes.influxdb import client
from nodes.mqtt_control import MyMQTTClient
from setup_logger import logger
from influxdb_client.client.write_api import ASYNCHRONOUS
from dotenv import load_dotenv
import sys
import atexit

load_dotenv()

#InfluxDB Configuration
write_api = client.write_api(write_options=ASYNCHRONOUS)

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "my-super-secret-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "Smart Rice Guard")
INFLUX_BUCKET = "birds_counter"

target_classes = {'bird', 'drone'}

# MQTT Configuration
mqtt_client = MyMQTTClient()

# Global timer variable and shutdown event for proper cleanup
timer_thread = None
shutdown_event = Event()

def cleanup_resources():
    """Clean up all resources properly"""
    global timer_thread
    
    # Set shutdown event
    shutdown_event.set()
    
    # Stop the timer thread properly
    if timer_thread and timer_thread.is_alive():
        logger.info("Menghentikan timer thread...")
        timer_thread.cancel()
    
    # Close InfluxDB connections
    try:
        logger.info("Menutup InfluxDB Write API...")
        write_api.close()
        client.close()
    except Exception as e:
        logger.error(f"Error closing InfluxDB connections: {e}")
    
    # Close MQTT connection if available
    try:
        if hasattr(mqtt_client, 'disconnect'):
            mqtt_client.disconnect()
        elif hasattr(mqtt_client, 'close'):
            mqtt_client.close()
    except Exception as e:
        logger.error(f"Error closing MQTT connection: {e}")
    
    logger.info("Semua koneksi telah ditutup.")

# -----------------------------------------------------------------------------------------------
# User-defined class to be used in the callback function
# -----------------------------------------------------------------------------------------------
# Inheritance from the app_callback_class
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        # Counter untuk deteksi burung dalam satu menit
        self.bird_counter_minute = 0
        self.emitted_ids = set()

    def get_and_reset_count(self):
        """
        This function returns the count of bird detections in the last minute and resets the counter.
        """
        count = self.bird_counter_minute
        self.bird_counter_minute = 0
        self.emitted_ids.clear()
        return count
    
# Function to save and reset bird detection count every minute
def save_and_reset_task(user_data: user_app_callback_class):
    """
    This function saves the bird detection count to InfluxDB every minute and resets the count.
    It uses the user_data object to access the count and reset it.
    """
    global timer_thread
    
    # Check if shutdown was requested
    if shutdown_event.is_set():
        logger.info("Shutdown event detected, stopping timer task.")
        return
    
    # 1. Ambil jumlah deteksi dari class state
    count = user_data.get_and_reset_count()
    
    # 2. Hanya tulis ke InfluxDB jika ada deteksi
    if count > 0:
        logger.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Menyiapkan {count} deteksi burung untuk dikirim ke InfluxDB...")
        
        try:
            point = (
                Point("deteksi_lingkungan")
                .tag("lokasi_kamera", "sawah_utama")
                .field("bird_count", count)
            )
            
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        except Exception as e:
            logger.error(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Gagal mengirim data ke InfluxDB: {e}")
    else:
        logger.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Tidak ada deteksi burung dalam satu menit terakhir.")

    # Schedule next execution only if not shutting down
    if not shutdown_event.is_set():
        timer_thread = Timer(60.0, save_and_reset_task, [user_data])
        timer_thread.daemon = True  # Make it daemon thread for proper cleanup
        timer_thread.start()

# -----------------------------------------------------------------------------------------------
# User-defined callback function
# -----------------------------------------------------------------------------------------------

# This is the callback function that will be called when data is available from the pipeline
def app_callback(pad, info, user_data: user_app_callback_class):
    # Get the GstBuffer from the probe info
    buffer = info.get_buffer()
    # Check if the buffer is valid
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Get the caps from the pad
    format, width, height = get_caps_from_pad(pad)

    # If the user_data.use_frame is set to True, we can get the video frame from the buffer
    frame = None
    if user_data.use_frame and format is not None and width is not None and height is not None:
        # Get video frame
        frame = get_numpy_from_buffer(buffer, format, width, height)

    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)

    # Parse the detections
    for detection in detections:
        label = detection.get_label()
        bbox = detection.get_bbox()
        confidence = detection.get_confidence()
        if label == "bird":
            # Get track ID
            track_id = 0
            track = detection.get_objects_typed(hailo.HAILO_UNIQUE_ID)
            if len(track) == 1:
                track_id = track[0].get_id()
            # Increment the bird counter in user_data
            if track_id not in user_data.emitted_ids:
                user_data.bird_counter_minute += 1
                user_data.emitted_ids.add(track_id)
            logger.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Deteksi burung: ID {track_id}, BBOX {bbox}, Confidence {confidence:.2f}")
            mqtt_client.publish_play_sound()
            logger.info(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Mengirim perintah ke MQTT untuk memainkan suara burung.")

    return Gst.PadProbeReturn.OK

def signal_handler(signum, frame):
    """Handle SIGINT and SIGTERM signals"""
    print(f"\nMenerima signal {signum}, menghentikan aplikasi...")
    cleanup_resources()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function to run at exit
    atexit.register(cleanup_resources)
    
    user_data = user_app_callback_class()
    app = GStreamerDetectionApp(app_callback, user_data)

    # Mulai timer
    save_and_reset_task(user_data)
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nPipeline dihentikan oleh pengguna.")
    except Exception as e:
        logger.error(f"Error dalam aplikasi: {e}")
    finally:
        cleanup_resources()