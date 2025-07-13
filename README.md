# 🐦 Hailo Bird Detection Services


A high-performance real-time bird detection system powered by Hailo AI accelerators, designed for agricultural monitoring and bird deterrent applications. The system provides accurate bird counting and tracking with seamless InfluxDB integration for data analytics and monitoring.

## 🌟 Features

- **Real-time Detection**: High-performance bird detection using Hailo AI accelerators
- **Object Tracking**: Advanced tracking capabilities to avoid duplicate counting
- **Time-series Analytics**: Automated data logging to InfluxDB for historical analysis
- **Configurable Pipeline**: Flexible GStreamer-based processing pipeline
- **Agricultural Focus**: Optimized for rice field and crop monitoring applications
- **Shared Memory Integration**: Efficient video stream processing via shared memory
- **Auto-detection**: Automatic Hailo architecture detection
- **Logging**: Comprehensive logging system for monitoring and debugging

## 🏗️ Architecture

```
Video Stream → Shared Memory → Hailo Inference → Object Tracking → Detection Callback → InfluxDB
```

### Core Components

- **Detection Pipeline**: GStreamer-based video processing pipeline
- **Hailo Inference**: AI-accelerated object detection using Hailo hardware
- **Object Tracking**: Multi-object tracking to prevent duplicate counting
- **Data Storage**: Time-series data storage in InfluxDB
- **Logging System**: Structured logging for monitoring and debugging

## 🛠️ Prerequisites

### Hardware Requirements
- Hailo AI accelerator (Hailo-8 or compatible)
- Camera or video input source
- Minimum 4GB RAM recommended

### Software Requirements
- Python 3.8 or higher
- GStreamer 1.0+
- Hailo software suite
- InfluxDB 2.0+

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/hailo-bird-detection.git
cd hailo-bird-detection
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Hailo Software Suite
Follow the official Hailo installation guide for your platform:
- [Hailo Installation Guide](https://hailo.ai/documentation/)

### 4. Set Up InfluxDB
```bash
# Install InfluxDB (Ubuntu/Debian)
wget https://dl.influxdata.com/influxdb/releases/influxdb2_2.7.1_amd64.deb
sudo dpkg -i influxdb2_2.7.1_amd64.deb
sudo systemctl start influxdb
```

## ⚙️ Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# InfluxDB Configuration
INFLUX_URL=http://localhost:8086
INFLUX_TOKEN=your-influxdb-token
INFLUX_ORG=Smart Rice Guard
INFLUX_BUCKET=birds_counter

# Camera Configuration (optional)
CAMERA_WIDTH=1920
CAMERA_HEIGHT=1080
CAMERA_FPS=30
```

### Model Configuration
The system automatically detects the Hailo architecture and loads the appropriate model. You can specify custom models using command-line arguments:

```bash
python detection.py --hef-path /path/to/your/model.hef --labels-json /path/to/labels.json
```

## 🚀 Usage

### Basic Usage
```bash
python detection.py
```

### Advanced Usage with Custom Parameters
```bash
python detection.py \
    --hef-path /path/to/custom/model.hef \
    --labels-json /path/to/custom/labels.json \
    --arch hailo8
```

### Pipeline Testing
```bash
# Test the detection pipeline without InfluxDB
python detection_pipeline.py
```

## 📊 Data Analytics

The system automatically logs detection data to InfluxDB every minute with the following schema:

```
Measurement: deteksi_lingkungan
Tags:
  - lokasi_kamera: sawah_utama
Fields:
  - bird_count: integer (number of birds detected)
  - timestamp: datetime
```

### Querying Data
```sql
-- Get bird count for the last 24 hours
from(bucket: "birds_counter")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "deteksi_lingkungan")
  |> filter(fn: (r) => r._field == "bird_count")
```

## 🔧 API Reference

### Main Classes

#### `GStreamerDetectionApp`
Main application class that handles the detection pipeline.

```python
app = GStreamerDetectionApp(app_callback, user_data)
app.run()
```

#### `user_app_callback_class`
Handles detection callbacks and counting logic.

```python
class user_app_callback_class(app_callback_class):
    def get_and_reset_count(self):
        """Returns and resets the bird count"""
        pass
```

### Pipeline Components

- **SHM_SOURCE_PIPELINE**: Shared memory video source
- **SIMPLE_INFERENCE_PIPELINE**: Hailo inference pipeline
- **CALLBACK_OVERLAY_SINK_PIPELINE**: Output processing and display

## 🐛 Troubleshooting

### Common Issues

1. **Hailo Architecture Not Detected**
   ```bash
   # Manually specify architecture
   python detection.py --arch hailo8
   ```

2. **InfluxDB Connection Failed**
   ```bash
   # Check InfluxDB status
   sudo systemctl status influxdb
   
   # Verify environment variables
   echo $INFLUX_URL
   echo $INFLUX_TOKEN
   ```

3. **GStreamer Pipeline Errors**
   ```bash
   # Check GStreamer installation
   gst-inspect-1.0 --version
   
   # Verify Hailo plugins
   gst-inspect-1.0 hailonet
   ```

### Debug Mode
Enable debug logging by modifying `setup_logger.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Optimization

### Recommended Settings
- **Batch Size**: 1-2 for real-time processing
- **Network Resolution**: 640x640 (default)
- **NMS Thresholds**: 
  - Score: 0.3
  - IoU: 0.45

### Memory Usage
- Monitor shared memory usage: `/tmp/feed.raw`
- Adjust queue buffer sizes based on available memory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hailo AI](https://hailo.ai/) for providing the AI acceleration platform
- [GStreamer](https://gstreamer.freedesktop.org/) for multimedia framework
- [InfluxDB](https://www.influxdata.com/) for time-series database

## 📞 Support

For questions and support:
- Create an issue in this repository
- Email: [your-email@example.com]
- Documentation: [Project Wiki](https://github.com/yourusername/hailo-bird-detection/wiki)

---

**Smart Rice Guard** - Protecting crops with AI-powered monitoring 🌾