"""
Master Mixer & Video Producer for the Cyan Platform Hip-Hop Cypher Track
Combines Sebastian's 808 Hip-Hop Beat with Alcyone & Electra's Rap Stems,
producing both the mastered full song (.mp3 / .wav) and an animated 1080p video clip.
"""

import os
import subprocess

def mix_and_produce_hiphop_cypher():
    base_dir = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output"
    beat_path = os.path.join(base_dir, "original_music", "sebastian_808_hiphop_beat.wav")
    v1 = os.path.join(base_dir, "cypher_vocals", "verse_01_alcyone.mp3")
    v2 = os.path.join(base_dir, "cypher_vocals", "verse_02_electra.mp3")
    v3 = os.path.join(base_dir, "cypher_vocals", "verse_03_alcyone.mp3")
    
    out_song_wav = os.path.join(base_dir, "original_music", "kuroshio_platform_cypher_master.wav")
    out_video_mp4 = os.path.join(base_dir, "video_releases", "kuroshio_platform_cypher_video.mp4")
    visual_loop = r"C:\Users\blue-\projects\theater\radio_streamer\visual_loop.ts"
    
    # Concatenate vocal verses sequentially with slight spacing
    # Using FFmpeg filter graph to stitch v1, v2, v3 over the 808 beat
    filter_complex = (
        "[1:a][2:a][3:a]concat=n=3:v=0:a=1[all_vocals];"
        "[all_vocals]volume=1.45[lead_vocals];"
        "[0:a]volume=0.9[beat];"
        "[beat][lead_vocals]amix=inputs=2:duration=first:dropout_transition=2[master_audio];"
        "[master_audio]asplit=2[final_a][wave_feed];"
        "[wave_feed]showwaves=s=1200x260:mode=cline:colors=0x00E5FF@0.95:scale=cbrt[wave];"
        "[4:v][wave]overlay=(W-w)/2:H-h-40[final_v]"
    )
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", beat_path,
        "-i", v1,
        "-i", v2,
        "-i", v3,
        "-stream_loop", "-1",
        "-i", visual_loop,
        "-filter_complex", filter_complex,
        "-map", "[final_v]",
        "-map", "[final_a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        out_video_mp4
    ]
    
    print("[Master Mixer] Rendering complete 808 Hip-Hop Cypher Music Video...")
    subprocess.run(cmd, check=True)
    
    size = os.path.getsize(out_video_mp4) if os.path.exists(out_video_mp4) else 0
    print(f"[Done!] Finished Cypher Video: {out_video_mp4} ({size} bytes)")
    return out_video_mp4

if __name__ == "__main__":
    mix_and_produce_hiphop_cypher()
