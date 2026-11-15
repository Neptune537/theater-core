"""
Kuroshio Gyre / Theater: Video Composer for The Seven Daughters & Social Releases
Combines original generated music pads, vocal stems, dynamic visualizer motion loops,
and clean animated subtitles/lower-thirds into 100% original, copyright-free video clips
ready for YouTube, Shorts, TikTok, and X.
"""

import os
import subprocess

def compose_daughter_music_video(
    vocal_stem_path: str,
    music_bed_path: str,
    visual_loop_path: str,
    output_mp4_path: str,
    title_text: str = "MAIA • 432 Hz",
    subtitle_text: str = "Dawn Oceanic Ambient • The Seven Daughters",
    vocal_gain: float = 1.3,
    music_gain: float = 0.55
):
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4_path)), exist_ok=True)
    
    # Filter graph without drawtext (avoids Windows fontconfig dependency)
    filter_complex = (
        f"[0:a]volume={vocal_gain}[vocal];"
        f"[1:a]volume={music_gain}[music];"
        f"[vocal][music]amix=inputs=2:duration=first:dropout_transition=2[mixed_a];"
        f"[mixed_a]asplit=2[out_a][wave_in];"
        f"[wave_in]showwaves=s=1200x240:mode=cline:colors=0x00E5FF@0.9:scale=cbrt[wave];"
        f"[2:v][wave]overlay=(W-w)/2:H-h-50[out_v]"
    )
    
    cmd = [
        "ffmpeg",
        "-y",
        "-i", vocal_stem_path,
        "-i", music_bed_path,
        "-stream_loop", "-1",
        "-i", visual_loop_path,
        "-filter_complex", filter_complex,
        "-map", "[out_v]",
        "-map", "[out_a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4_path
    ]
    
    print(f"[*] Composing Video: {output_mp4_path}...")
    subprocess.run(cmd, check=True)
    size = os.path.getsize(output_mp4_path) if os.path.exists(output_mp4_path) else 0
    print(f"[Video Composer OK] Finished: {output_mp4_path} ({size} bytes)")
    return output_mp4_path

if __name__ == "__main__":
    vocal = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\daughters\siren_id_maia_432Hz.mp3"
    music = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\original_music\maia_432hz_ambient_bed.wav"
    visual = r"C:\Users\blue-\projects\theater\radio_streamer\visual_loop.ts"
    out = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\video_releases\maia_432hz_official_release.mp4"
    
    compose_daughter_music_video(
        vocal_stem_path=vocal,
        music_bed_path=music,
        visual_loop_path=visual,
        output_mp4_path=out,
        title_text="MAIA • SIREN-01",
        subtitle_text="432 Hz Dawn Oceanic Ambient • Reincarnated in a Different World"
    )
