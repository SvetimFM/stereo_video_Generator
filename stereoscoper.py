import cv2
import numpy as np
from pathlib import Path
import subprocess
import json
import sys
import os
import argparse
from shutil import which
import logging
import time
import tkinter as tk
from tkinter import filedialog, ttk
from threading import Thread


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stereo_processor.log')
    ]
)

class StereoscoperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("360° Video Processor for Quest Pro")
        self.root.geometry("600x400")
        self.processor = QuestProProcessor()
        
        # Create main frame with padding
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Input file selection
        ttk.Label(main_frame, text="Input Video:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.input_path, width=50).grid(row=0, column=1, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        
        # Output file selection
        ttk.Label(main_frame, text="Output Location:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_path = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.output_path, width=50).grid(row=1, column=1, pady=5)
        ttk.Button(main_frame, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)
        
        # IPD selection
        ttk.Label(main_frame, text="IPD (mm):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.ipd = tk.StringVar(value="64.0")
        ttk.Entry(main_frame, textvariable=self.ipd, width=10).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame, 
            length=400, 
            mode='determinate',
            maximum=100
        )
        self.progress.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Add detailed progress labels
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=4, column=0, columnspan=3, pady=5)
        
        self.frames_label = ttk.Label(self.progress_frame, text="Frames: 0/0")
        self.frames_label.grid(row=0, column=0, padx=5)
        
        self.fps_label = ttk.Label(self.progress_frame, text="FPS: 0")
        self.fps_label.grid(row=0, column=1, padx=5)
        
        self.eta_label = ttk.Label(self.progress_frame, text="ETA: --:--:--")
        self.eta_label.grid(row=0, column=2, padx=5)
        
        # Status label
        self.status = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status).grid(row=4, column=0, columnspan=3, pady=5)
        
        # Process button
        self.process_btn = ttk.Button(main_frame, text="Process Video", command=self.process_video)
        self.process_btn.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Log display
        self.log_text = tk.Text(main_frame, height=10, width=70)
        self.log_text.grid(row=6, column=0, columnspan=3, pady=5)
        
        # Add text handler for logging
        self.log_handler = TextHandler(self.log_text)
        logging.getLogger().addHandler(self.log_handler)

    def browse_input(self):
        filename = filedialog.askopenfilename(filetypes=[
            ("360 Video files", "*.360 *.mp4 *.mov *.avi"),
            ("360 files", "*.360"),
            ("Video files", "*.mp4 *.mov *.avi"),
            ("All files", "*.*")
        ])
        if filename:
            self.input_path.set(filename)

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4")]
        )
        if filename:
            self.output_path.set(filename)

    def process_video(self):
        if not self.input_path.get() or not self.output_path.get():
            self.status.set("Please select input and output files")
            return
            
        try:
            ipd = float(self.ipd.get())
        except ValueError:
            self.status.set("Invalid IPD value")
            return
            
        self.process_btn.state(['disabled'])
        self.progress.start()
        self.status.set("Processing...")
        
        # Run processing in separate thread
        Thread(target=self.run_processing, daemon=True).start()


    def update_progress(self, progress, frame_count, total_frames, fps, eta):
        """Update all progress indicators"""
        def _update():
            self.progress['value'] = progress
            self.frames_label['text'] = f"Frames: {frame_count}/{total_frames}"
            self.fps_label['text'] = f"FPS: {fps:.1f}"
            
            # Convert eta to HH:MM:SS
            eta_str = time.strftime('%H:%M:%S', time.gmtime(eta))
            self.eta_label['text'] = f"ETA: {eta_str}"
            
            # Update status text
            self.status.set(f"Processing: {progress:.1f}%")
            
        self.root.after(0, _update)

    def run_processing(self):
        try:
            self.processor.process_360_video(
                self.input_path.get(),
                self.output_path.get(),
                ipd_mm=float(self.ipd.get()),
                progress_callback=self.update_progress  # Pass the callback
            )
            self.root.after(0, self.processing_complete)
        except Exception as error:
            self.root.after(0, lambda: self.processing_error(str(error)))

    def processing_complete(self):
        self.progress.stop()
        self.process_btn.state(['!disabled'])
        self.status.set("Processing complete!")

    def processing_error(self, error_msg):
        self.progress.stop()
        self.process_btn.state(['!disabled'])
        self.status.set(f"Error: {error_msg}")

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record) + '\n'
        self.text_widget.after(0, self.append_text, msg)

    def append_text(self, msg):
        self.text_widget.insert(tk.END, msg)
        self.text_widget.see(tk.END)



class QuestProProcessor:
    def __init__(self):
        self.output_width = 5760
        self.output_height = 2880
        self.target_bitrate = "150M"
        self.fps = 60
        
        logging.info("Initializing QuestProProcessor...")
        
        # Check for FFmpeg installation
        self.ffmpeg_path = self._get_ffmpeg_path()
        if not self.ffmpeg_path:
            raise RuntimeError(
                "FFmpeg not found! Please install FFmpeg and add it to your PATH, or place ffmpeg.exe in the same directory as this script."
            )
        logging.info(f"Using FFmpeg from: {self.ffmpeg_path}")

    def _get_ffmpeg_path(self):
        """Find FFmpeg executable with detailed logging"""
        logging.info("Searching for FFmpeg...")
        
        # First check if ffmpeg is in PATH
        ffmpeg_path = which('ffmpeg')
        if ffmpeg_path:
            logging.info(f"Found FFmpeg in PATH: {ffmpeg_path}")
            return ffmpeg_path
            
        # Check in script directory
        script_dir = Path(__file__).parent.absolute()
        ffmpeg_exe = script_dir / 'ffmpeg.exe'
        if ffmpeg_exe.exists():
            logging.info(f"Found FFmpeg in script directory: {ffmpeg_exe}")
            return str(ffmpeg_exe)
            
        # Check common Windows install locations
        common_locations = [
            Path(os.environ.get('PROGRAMFILES', '')) / 'ffmpeg' / 'bin' / 'ffmpeg.exe',
            Path(os.environ.get('PROGRAMFILES(X86)', '')) / 'ffmpeg' / 'bin' / 'ffmpeg.exe',
            Path.home() / 'ffmpeg' / 'bin' / 'ffmpeg.exe',
            Path('C:/ffmpeg/bin/ffmpeg.exe'),
        ]
        
        for location in common_locations:
            logging.info(f"Checking location: {location}")
            if location.exists():
                logging.info(f"Found FFmpeg at: {location}")
                return str(location)
                
        logging.error("FFmpeg not found in any expected location!")
        return None

    def process_360_video(self, input_path, output_path, ipd_mm=64):
        """Process 360 video with detailed logging"""
        start_time = time.time()
        logging.info(f"Starting video processing at: {time.strftime('%H:%M:%S')}")
        
        try:
            # Convert paths to Path objects and resolve them
            input_path = Path(input_path).resolve()
            output_path = Path(output_path).resolve()
            
            logging.info(f"Input path: {input_path}")
            logging.info(f"Output path: {output_path}")
            
            # Verify input file exists
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            logging.info(f"Input file size: {input_path.stat().st_size / (1024*1024*1024):.2f} GB")
            
            # Create output directory structure
            output_path.parent.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {output_path.parent}")
            
            # Process video in a single pass
            self._process_video(str(input_path), str(output_path), ipd_mm/10.0)
            
            # Add metadata
            self.add_quest_metadata(output_path, ipd_mm)
            logging.info("Added metadata")
            
            end_time = time.time()
            duration = end_time - start_time
            logging.info(f"Processing completed in {duration/60:.2f} minutes")
            
        except Exception as e:
            logging.error(f"Error during processing: {str(e)}", exc_info=True)
            raise

    def _process_video(self, input_path, output_path, ipd_cm):
        """Process video in a single pass with hardware acceleration when available"""
        logging.info(f"Processing video: {input_path} -> {output_path}")
        
        # First, probe the input file to check stream information
        probe_cmd = [
            str(self.ffmpeg_path),
            '-i', input_path
        ]
        try:
            probe_result = subprocess.run(probe_cmd, 
                                        capture_output=True, 
                                        text=True)
            logging.info(f"File probe result: {probe_result.stderr}")
            
            # Find the video streams
            streams = probe_result.stderr.split('\n')
            video_streams = []
            for line in streams:
                if 'Stream #' in line and 'Video: hevc' in line:
                    # Extract stream identifier like "0:0" or "0:5"
                    stream_id = line.split('Stream #')[1].split('[')[0].strip()
                    video_streams.append(stream_id)
            
            if len(video_streams) < 2:
                raise RuntimeError("Could not find both front and back video streams")
                
            # Get stream indices
            front_stream = video_streams[0]
            back_stream = video_streams[1]
            logging.info(f"Using front stream: {front_stream}, back stream: {back_stream}")
            
        except subprocess.CalledProcessError as e:
            logging.warning(f"File probe failed: {e.stderr}")
            # Fall back to default stream indices
            front_stream = "0:0"
            back_stream = "0:5"

        configs = [
            # Config 1: CUDA hardware acceleration with NVENC
            {
                'input': [],
                'filters': [
                    f'[{front_stream}]format=yuvj420p[front]',
                    f'[{back_stream}]format=yuvj420p[back]',
                    '[front][back]hstack[full360]',
                    # Left eye (note the additional parameters for proper orientation)
                    f'[full360]v360=input=e:output=e:d_fov=180:yaw=-{ipd_cm}:h_flip=1[left]',
                    # Right eye
                    f'[full360]v360=input=e:output=e:d_fov=180:yaw={ipd_cm}:h_flip=1[right]',
                    # Scale each eye view
                    f'[left]scale=2048:2048,format=yuv420p[left_scaled]',
                    f'[right]scale=2048:2048,format=yuv420p[right_scaled]',
                    # Stack left and right views side by side
                    '[left_scaled][right_scaled]hstack[out]'
                ],
                'output': [
                    '-c:v', 'h264_nvenc',
                    '-preset', 'p7',
                    '-tune', 'hq',
                    '-b:v', '100M',
                    '-maxrate', '150M',
                    '-bufsize', '200M'
                ]
            },
            # Config 2: Similar changes for software encoding
            {
                'input': [],
                'filters': [
                    f'[{front_stream}]format=yuvj420p[front]',
                    f'[{back_stream}]format=yuvj420p[back]',
                    '[front][back]hstack[full360]',
                    f'[full360]v360=input=e:output=e:d_fov=180:yaw=-{ipd_cm}:h_flip=1[left]',
                    f'[full360]v360=input=e:output=e:d_fov=180:yaw={ipd_cm}:h_flip=1[right]',
                    f'[left]scale=2880:2880,format=yuv420p[left_scaled]',
                    f'[right]scale=2880:2880,format=yuv420p[right_scaled]',
                    '[left_scaled][right_scaled]hstack[out]'
                ],
                'output': [
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-crf', '23',
                    '-pix_fmt', 'yuv420p'
                ]
            }
        ]

        success = False
        for config in configs:
            try:
                filters = ';'.join(config.get('filters', []))
                cmd = [
                    str(self.ffmpeg_path),
                    '-i', input_path,
                    '-filter_complex', filters,
                    '-map', '[out]',
                    *config['output'],
                    '-pix_fmt', 'yuv420p',
                    '-color_range', '1',
                    '-colorspace', 'bt709',
                    '-color_primaries', 'bt709',
                    '-color_trc', 'bt709',
                    # Changed metadata to indicate side-by-side format
                    '-metadata:s:v:0', 'stereo_mode=left-right',
                    '-metadata:s:v:0', 'projection_type=equirectangular',
                    '-movflags', '+faststart',
                    '-y',
                    output_path
                ]
                
                logging.info(f"Processing with command: {' '.join(cmd)}")
                result = subprocess.run(cmd, 
                                    capture_output=True, 
                                    text=True,
                                    check=True)
                logging.info("Video processing successful!")
                success = True
                break
            except subprocess.CalledProcessError as e:
                logging.warning(f"Configuration failed: {e.stderr}")
                continue

        if not success:
            raise RuntimeError("All processing configurations failed")

    def add_quest_metadata(self, video_path, ipd_mm):
        """Add Quest-specific VR metadata"""
        metadata = {
            "Format": "360_TB",
            "Stereoscopic": "true",
            "ProjectionType": "equirectangular",
            "Layout": "top-bottom",
            "QuestOptimized": "true",
            "InitialFov": 97,
            "IPD": ipd_mm
        }
        
        json_path = str(Path(video_path).with_suffix('.json'))
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        logging.info(f"Added metadata to {json_path}")

def main():
    # Check if running with command line arguments
    if len(sys.argv) > 1:
        # Use existing command line processing
        parser = argparse.ArgumentParser(description='Process 360 video for Quest Pro')
        parser.add_argument('--input_path', required=True, help='Path to input video file')
        parser.add_argument('--output_path', required=True, help='Path to output video file or directory')
        parser.add_argument('--ipd', type=float, default=64.0, help='IPD in millimeters (default: 64.0)')
        
        args = parser.parse_args()
        
        processor = QuestProProcessor()
        processor.process_360_video(args.input_path, args.output_path, ipd_mm=args.ipd)
    else:
        # Launch GUI
        root = tk.Tk()
        app = StereoscoperGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()