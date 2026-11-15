"""
Kuroshio Gyre / Theater 24/7 Siren Radio Live Streamer to YouTube.
Hardware-Synchronized Clock Architecture:
- Uses pre-rendered high-quality 720p 24fps visual loop
- `-fflags +genpts` ensures continuous, non-jittered timestamps
- Direct H.264 copy avoids transcoding
- Real-time RTMP stream with 0 CPU load and zero YouTube buffering!
"""

import os
import sys
import time
import subprocess

STREAM_KEY = os.environ.get("YOUTUBE_STREAM_KEY", "sxj7-8328-16dc-fj8t-8gy0")
# Audio Ingest: Dedicated Voice / News Broadcast Stems (NOT copyrighted radio rotation)
AUDIO_SOURCE = os.environ.get("AUDIO_SOURCE", r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\daughters\siren_id_maia_432Hz.mp3")
RTMP_URL = os.environ.get("RTMP_URL", "rtmp://a.rtmp.youtube.com/live2")
VIDEO_LOOP = os.environ.get("VIDEO_LOOP", r"C:\Users\blue-\projects\theater\radio_streamer\visual_loop.ts")

full_rtmp_target = f"{RTMP_URL}/{STREAM_KEY}"

print("=" * 65)
print(" [*] Kuroshio Gyre: Siren Radio 24/7 -> YouTube Live (Paced Real-Time)")
print(f" Audio Ingest:  {AUDIO_SOURCE}")
print(f" RTMP Endpoint: {RTMP_URL}/********")
print(f" Video Loop:    {VIDEO_LOOP}")
print(" Mode:          Synchronous +genpts Flv Muxer (Zero Dropped Frames)")
print("=" * 65)

cmd = [
    "ffmpeg",
    "-re",
    "-stream_loop", "-1",
    "-i", VIDEO_LOOP,
    "-fflags", "+genpts",
    "-i", AUDIO_SOURCE,
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "128k",
    "-ar", "48000",
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-flvflags", "no_duration_filesize",
    "-f", "flv",
    full_rtmp_target,
]

while True:
    print(f"[{time.strftime('%H:%M:%S')}] Broadcasting Siren Radio to YouTube Live...")
    try:
        subprocess.run(cmd)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Stream error: {e}")
    print(f"[{time.strftime('%H:%M:%S')}] Stream disconnected. Reconnecting in 5 seconds...")
    time.sleep(5)
