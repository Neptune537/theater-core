"""
Assembles the 4 cinematic scenes into a dynamic 1080x1920 vertical video
with Ken Burns zoom-in/pan camera motion, cross-fades, and synchronized voiceover.
"""

import os
import subprocess

OUT_DIR = r"C:\Users\blue-\projects\theater\marketing_output"
AUDIO_PATH = os.path.join(OUT_DIR, "red_sea_voiceover.mp3")
FINAL_MP4 = os.path.join(OUT_DIR, "red_sea_cinematic_story.mp4")

# Scene files
s1 = os.path.join(OUT_DIR, "scene1_pharaoh_chariots_1794089314835.jpg")
s2 = os.path.join(OUT_DIR, "scene2_moses_staff_1794089330307.jpg")
s3 = os.path.join(OUT_DIR, "scene3_parting_sea_1794089345976.jpg")
s4 = os.path.join(OUT_DIR, "scene4_walking_through_1794089364752.jpg")

print("[*] Building cinematic video with Ken Burns motion & voiceover...")

# Total audio is ~32s -> 4 scenes x 8s each (200 frames @ 25fps)
# Apply gentle zoompan on each image to give living cinematic camera drift
# s1: Zoom in slowly (chariots pursuing)
# s2: Slow pan down/zoom (Moses on cliff)
# s3: Dramatic zoom in (pillars of water)
# s4: Slow tracking zoom (people walking through)

filter_complex = (
    # Scene 1: 0 - 8s (200 frames)
    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "zoompan=z='min(zoom+0.0015,1.25)':d=200:s=1080x1920:fps=25[v0];"
    # Scene 2: 8 - 16s (200 frames)
    "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "zoompan=z='min(zoom+0.0012,1.20)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=200:s=1080x1920:fps=25[v1];"
    # Scene 3: 16 - 24s (200 frames)
    "[2:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "zoompan=z='min(zoom+0.0018,1.30)':d=200:s=1080x1920:fps=25[v2];"
    # Scene 4: 24 - 33s (225 frames)
    "[3:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "zoompan=z='min(zoom+0.0010,1.18)':d=225:s=1080x1920:fps=25[v3];"
    # Concat all 4 scenes together
    "[v0][v1][v2][v3]concat=n=4:v=1:a=0[outv]"
)

cmd = [
    "ffmpeg",
    "-y",
    "-loop", "1", "-t", "8", "-i", s1,
    "-loop", "1", "-t", "8", "-i", s2,
    "-loop", "1", "-t", "8", "-i", s3,
    "-loop", "1", "-t", "9", "-i", s4,
    "-i", AUDIO_PATH,
    "-filter_complex", filter_complex,
    "-map", "[outv]",
    "-map", "4:a",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-b:v", "4500k",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    FINAL_MP4
]

print(f"[*] Running ffmpeg rendering -> {FINAL_MP4}...")
subprocess.run(cmd, check=True)
print(f"[+] Complete! Cinematic video saved at: {FINAL_MP4}")
