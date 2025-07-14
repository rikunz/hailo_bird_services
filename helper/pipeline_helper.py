from hailo_apps.hailo_app_python.core.gstreamer.gstreamer_helper_pipelines  import(
    QUEUE
)

def SHM_SOURCE_PIPELINE(socket_path='/tmp/feed.raw', width=1920, height=1080, framerate='30/1', name='shm_source'):
    return (
        f'shmsrc socket-path={socket_path} do-timestamp=true is-live=true ! '
        f'video/x-raw, format=NV12, width={width}, height={height}, framerate={framerate} ! '
        f'videoconvert ! '
        f'video/x-raw, format=RGB, width={width}, height={height}, framerate={framerate} '
    )

def SIMPLE_INFERENCE_PIPELINE(hef_path, post_process_so=None, function_name=None, name='inference'):
    pipeline = (
        f'{QUEUE(name=f"{name}_preprocess_q", max_size_buffers=30)} ! '
        f'videoscale qos=false n-threads=2 ! '
        f'video/x-raw, pixel-aspect-ratio=1/1 ! '
        f'{QUEUE(name=f"{name}_convert_q", max_size_buffers=30)} ! '
        f'hailonet hef-path={hef_path} batch-size=1 ! '
        f'{QUEUE(name=f"{name}_post_q", max_size_buffers=30)} ! '
        f'hailofilter so-path={post_process_so} function-name={function_name} qos=false ! '
        f'{QUEUE(name=f"{name}_out_q", max_size_buffers=30)}'
    )
    return pipeline

def CALLBACK_OVERLAY_SINK_PIPELINE(
    shm_output_path="/tmp/infered.feed",
    name="display"
):
    return (
        f'queue name=queue_user_callback leaky=no max-size-buffers=30 max-size-bytes=0 max-size-time=0 ! '
        f'identity name=identity_callback signal-handoffs=true ! '
        f'{QUEUE(name=f"{name}_overlay_q", max_size_buffers=30)} ! '
        f'hailooverlay qos=false line-thickness=4 font-thickness=4 ! '
        f'{QUEUE(name=f"{name}_vc_q", max_size_buffers=30)} ! '
        f'videoconvert n-threads=2 qos=false ! '
        f'shmsink socket-path={shm_output_path} sync=false wait-for-connection=false'
    )

def VIDEO_SHMSINK_PIPELINE(socket_path="/tmp/infered.feed", width=1920, height=1080, framerate='30/1'):
    """
    Creates a GStreamer pipeline string portion for shared memory video transfer using the shm plugins.
    Shmsink creates a shared memory segment and socket.
    Args:
        socket_path (str): socket path.
        width (int): Width of the video frame.
        height (int): Height of the video frame.
    Returns:
        str: GStreamer pipeline string fragment.
    """
    return (f"videoconvert ! video/x-raw,format=RGB,width={width},height={height},framerate={framerate} ! shmsink socket-path={socket_path}")

def TCP_VIDEO_STREAM_PIPELINE(
    host="0.0.0.0",
    port=9111,
):
    """
    Creates a GStreamer pipeline string portion for TCP video streaming.
    Args:
        host (str): Host address for the TCP server.
        port (int): Port number for the TCP server.
    Returns:
        str: GStreamer pipeline string fragment.
    """
    return (
        f'videoconvert ! jpegenc ! multipartmux ! tcpserversink host={host} port={port}'
    )