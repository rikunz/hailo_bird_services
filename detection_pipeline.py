import setproctitle
from hailo_apps.hailo_app_python.core.common.installation_utils import detect_hailo_arch
from hailo_apps.hailo_app_python.core.common.core import get_default_parser, get_resource_path
from hailo_apps.hailo_app_python.core.common.defines import DETECTION_APP_TITLE, DETECTION_PIPELINE, RESOURCES_MODELS_DIR_NAME, RESOURCES_SO_DIR_NAME, DETECTION_POSTPROCESS_SO_FILENAME, DETECTION_POSTPROCESS_FUNCTION
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines import CROPPER_PIPELINE
from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_app import GStreamerApp, app_callback_class, dummy_callback

from helper.pipeline_helper import (
    SHM_SOURCE_PIPELINE,
    SIMPLE_INFERENCE_PIPELINE,
    CALLBACK_OVERLAY_SINK_PIPELINE,
)

# -----------------------------------------------------------------------------------------------
# User Gstreamer Application
# -----------------------------------------------------------------------------------------------

# This class inherits from the hailo_rpi_common.GStreamerApp class
class GStreamerDetectionApp(GStreamerApp):
    def __init__(self, app_callback, user_data, parser=None):
        if parser == None:
            parser = get_default_parser()
        parser.add_argument(
            "--labels-json",
            default=None,
            help="Path to costume labels JSON file",
        )

        # Call the parent class constructor
        super().__init__(parser, user_data)
        # Additional initialization code can be added here
        # Set Hailo parameters these parameters should be set based on the model used
        self.batch_size = 2
        self.network_width = 640
        self.network_height = 640
        self.network_format = "RGB"
        nms_score_threshold = 0.3
        nms_iou_threshold = 0.45


        # Determine the architecture if not specified
        if self.options_menu.arch is None:
            detected_arch = detect_hailo_arch()
            if detected_arch is None:
                raise ValueError("Could not auto-detect Hailo architecture. Please specify --arch manually.")
            self.arch = detected_arch
            print(f"Auto-detected Hailo architecture: {self.arch}")
        else:
            self.arch = self.options_menu.arch


        if self.options_menu.hef_path is not None:
            self.hef_path = self.options_menu.hef_path
        else:
            self.hef_path = get_resource_path(DETECTION_PIPELINE, RESOURCES_MODELS_DIR_NAME)


            # Set the post-processing shared object file
        self.post_process_so = get_resource_path(
            DETECTION_PIPELINE, RESOURCES_SO_DIR_NAME, DETECTION_POSTPROCESS_SO_FILENAME
        )

         
  
        self.post_function_name = DETECTION_POSTPROCESS_FUNCTION
        # User-defined label JSON file
        self.labels_json = self.options_menu.labels_json

        self.app_callback = app_callback

        self.thresholds_str = (
            f"nms-score-threshold={nms_score_threshold} "
            f"nms-iou-threshold={nms_iou_threshold} "
            f"output-format-type=HAILO_FORMAT_TYPE_FLOAT32"
        )

        # Set the process title
        setproctitle.setproctitle(DETECTION_APP_TITLE)

        self.create_pipeline()

    def get_pipeline_string(self):
        shm_source = SHM_SOURCE_PIPELINE()
        inference = SIMPLE_INFERENCE_PIPELINE(
            hef_path=self.hef_path,
            post_process_so=self.post_process_so,
            function_name="filter_letterbox"
        )
        crop_wrapper = CROPPER_PIPELINE(
            inner_pipeline=inference,
            so_path=self.cropper_process_so,
            function_name="create_crops",
            resize_method="inter-area",
            internal_offset=True,
            name="cropper1"
        )
        tracker = 'agg1. ! \n hailotracker name=hailo_tracker keep-tracked-frames=3 keep-new-frames=3 keep-lost-frames=3'
        callback_overlay = CALLBACK_OVERLAY_SINK_PIPELINE(
            shm_output_path="/tmp/infered.feed",
            use_fps_display=False
        )

        pipeline = f'{shm_source} ! {crop_wrapper} {tracker} ! {callback_overlay}'
        return pipeline
    
def main():
    # Create an instance of the user app callback class
    user_data = app_callback_class()
    app_callback = dummy_callback
    app = GStreamerDetectionApp(app_callback, user_data)
    # app.run()
    
if __name__ == "__main__":
    print("Starting Hailo Detection App...")
    main()