import os
import subprocess
import json
import logging
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("duck_radio_bed")

def probe_duration(file_path: str) -> float:
    """Returns the duration of an audio file in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())

def mix_voiceover_with_ducked_bed(
    speech_path: str,
    music_bed_path: str,
    output_path: str,
    duck_gain_db: float = -14.0,
    attack_ms: int = 200,
    release_ms: int = 800,
    lufs_target: float = -14.0,
    pad_tail_seconds: float = 2.0
) -> str:
    """
    Applies OpenMontage sidechain compression filtergraph to duck the background music
    whenever voice speech is present, then normalizes according to EBU R128 (-14 LUFS).
    
    Inputs:
      - speech_path: Path to vocal track (e.g. Kenji Vance, Dexter Sloan, or Siren Daughter)
      - music_bed_path: Path to music track / vinyl bed
      - output_path: Resulting mixed and mastered mp3/wav
      - duck_gain_db: Attenuation in dB for background music during speech (e.g. -14dB)
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    speech_duration = probe_duration(speech_path)
    total_target_duration = speech_duration + pad_tail_seconds

    # FFmpeg sidechain filtergraph inspired by OpenMontage audio_mixer.py:
    # 1. Loop or trim the music bed to match the voice length + tail
    # 2. Resample and format both inputs to 48kHz stereo
    # 3. Apply sidechaincompress filter where voice is the sidechain trigger
    # 4. Mix voice + ducked music
    # 5. Apply loudnorm for broadcast clarity
    
    # Linear gain multiplier from dB: 10^(duck_gain_db / 20)
    # sidechaincompress syntax:
    # sidechaincompress=threshold=0.03:ratio=8:attack=200:release=800
    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09[bed_loop];"
        f"[bed_loop]atrim=0:{total_target_duration},aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[bed];"
        f"[0:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo[voice];"
        f"[bed][voice]sidechaincompress=threshold=0.04:ratio=10:attack={attack_ms}:release={release_ms}:knee=2.8[ducked_bed];"
        f"[ducked_bed][voice]amix=inputs=2:duration=first:dropout_transition=2[mixed];"
        f"[mixed]loudnorm=I={lufs_target}:TP=-1.5:LRA=11[mastered]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", speech_path,
        "-i", music_bed_path,
        "-filter_complex", filter_complex,
        "-map", "[mastered]",
        "-ac", "2",
        "-ar", "48000",
        "-b:a", "192k",
        output_path
    ]

    logger.info(f"Ducking music bed ({music_bed_path}) under voice ({speech_path}) -> {output_path}")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    logger.info(f"[OK] Mastered broadcast clip written: {output_path} ({os.path.getsize(output_path)} bytes)")
    return output_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python duck_radio_bed.py <speech.mp3> <music_bed.mp3> <output.mp3>")
    else:
        mix_voiceover_with_ducked_bed(sys.argv[1], sys.argv[2], sys.argv[3])
