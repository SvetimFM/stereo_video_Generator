# 🎥 Stereoscoper: GoPro MAX to VR Video Converter

Convert your GoPro MAX 360° videos into VR-ready stereoscopic content for YouTube VR and Meta Quest headsets.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

## ✨ Features

- 🎮 User-friendly GUI interface
- 🚀 Hardware-accelerated processing (NVIDIA NVENC)
- 🎯 Optimized for YouTube VR and Meta Quest
- 🔄 Real-time processing progress tracking
- 🎛️ Adjustable IPD (Inter-Pupillary Distance)
- 📊 Detailed logging and error handling

## 🚀 Quick Start

1. **Prerequisites**
   ```bash
   # Install FFmpeg
   # Windows: Download from https://ffmpeg.org/download.html
   # Linux: sudo apt install ffmpeg
   # macOS: brew install ffmpeg

   # Install Python dependencies
   pip install -r requirements.txt
   ```

2. **Launch the GUI**
   ```bash
   python stereoscoper.py
   ```

3. **Or use CLI mode**
   ```bash
   python stereoscoper.py --input_path video.360 --output_path output.mp4 --ipd 64.0
   ```

## 🎯 Usage

### GUI Mode
1. Select your input .360 video file
2. Choose output location
3. Adjust IPD if needed (default: 64mm)
4. Click "Process Video"
5. Monitor progress with real-time stats

### CLI Mode

```bash
python stereoscoper.py --input_path <path_to_360_video> --output_path <output_path> --ipd <ipd_in_mm>
```


## 🔧 Technical Details

### Video Processing Pipeline
1. **Input Analysis**: Automatically detects front/back video streams
2. **Stereoscopic Conversion**: 
   - Combines front/back streams into 360° panorama
   - Creates left/right eye views with proper IPD separation
   - Applies correct VR projection and orientation
3. **Output Optimization**:
   - Hardware acceleration when available
   - High-quality encoding settings
   - YouTube VR metadata embedding

### Output Specifications
- Resolution: 4096x2048 per eye
- Format: Side-by-side stereoscopic
- Codec: H.264 (hardware) or x264 (software)
- Bitrate: Up to 150Mbps
- Metadata: YouTube VR and Quest-compatible

## 💡 Tips

- For best quality, use NVIDIA GPU with NVENC support
- Recommended IPD range: 58-72mm
- Processing time depends on:
  - Video length
  - Resolution
  - Hardware capabilities
  - Encoding settings

## 🔍 Troubleshooting

### Common Issues
1. **FFmpeg not found**
   - Ensure FFmpeg is installed and in system PATH
   - Or place ffmpeg.exe in script directory

2. **Hardware acceleration fails**
   - Falls back to software encoding automatically
   - Update GPU drivers
   - Check NVIDIA NVENC support

3. **High memory usage**
   - Normal for high-resolution processing
   - Close other applications
   - Consider reducing output resolution

## 🛠️ Development

### Project Structure

stereoscoper/
├── stereoscoper.py # Main application
├── requirements.txt # Python dependencies
└── README.md # Documentation


### Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - feel free to use in personal and commercial projects.

## 🙏 Acknowledgments

- FFmpeg team for the amazing video processing toolkit
- YouTube for VR video guidelines

## 📧 Support

- Create an issue for bugs/features
- Star the repo if you find it useful!