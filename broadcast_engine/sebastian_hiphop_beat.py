"""
Sebastian's 808 Hip-Hop Beat Synthesizer (Baton DSP Core)
Generates authentic booming 808 sub-bass kicks, crisp layered claps/snares,
ticking trap hi-hat rolls, and dark chord stabs tuned to 432 Hz / 88 BPM.
Pure Python 3 standard library (math, wave, struct) - zero dependencies.
"""

import math
import struct
import wave
import os
import random

SAMPLE_RATE = 48000

def generate_808_hiphop_beat(
    output_wav_path: str,
    duration_sec: float = 38.0,
    bpm: float = 88.0,
    root_pitch_hz: float = 54.0 # Sub C1/A0 range (tuned to 432 harmonic)
):
    os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
    total_samples = int(SAMPLE_RATE * duration_sec)
    
    beat_sec = 60.0 / bpm
    sixteenth_sec = beat_sec / 4.0
    
    # Pre-render drum voice samples
    # 1. 808 Kick: Pitch sweep from 140Hz down to root_pitch_hz with exponential decay
    kick_len = int(SAMPLE_RATE * 0.75)
    kick_samples = []
    for i in range(kick_len):
        t = i / SAMPLE_RATE
        freq = root_pitch_hz + (130.0 * math.exp(-22.0 * t))
        env = math.exp(-3.2 * t)
        sample = math.sin(2 * math.pi * freq * t) * env
        # Slight tube drive / saturation
        sample = math.tanh(sample * 1.4) * 0.95
        kick_samples.append(sample)
        
    # 2. Snare / Clap: Noise burst + pitched body
    snare_len = int(SAMPLE_RATE * 0.25)
    snare_samples = []
    random.seed(42)
    for i in range(snare_len):
        t = i / SAMPLE_RATE
        noise = (random.random() * 2.0 - 1.0) * math.exp(-18.0 * t)
        tone = math.sin(2 * math.pi * 210.0 * t) * math.exp(-25.0 * t)
        sample = (noise * 0.7 + tone * 0.3) * 0.8
        snare_samples.append(sample)
        
    # 3. Hi-Hat: Metallic noise click
    hat_len = int(SAMPLE_RATE * 0.05)
    hat_samples = []
    for i in range(hat_len):
        t = i / SAMPLE_RATE
        noise = (random.random() * 2.0 - 1.0) * math.exp(-60.0 * t) * 0.45
        hat_samples.append(noise)
        
    # Grid sequence layout
    # 4 beats per bar, 16 sixteenths per bar
    # Kick on: 1, 3.5, 4.25
    # Snare on: 2, 4
    # Hats on: continuous 8ths with 16th rolls
    
    buffer_l = [0.0] * total_samples
    buffer_r = [0.0] * total_samples
    
    current_time = 0.0
    step = 0
    
    while current_time < duration_sec:
        sixteenth_index = step % 16
        sample_idx = int(current_time * SAMPLE_RATE)
        
        # --- DRUMS TRIGGER ---
        # Kick trigger
        if sixteenth_index in [0, 6, 10]:
            for ki, val in enumerate(kick_samples):
                if sample_idx + ki < total_samples:
                    buffer_l[sample_idx + ki] += val * 0.85
                    buffer_r[sample_idx + ki] += val * 0.85
                    
        # Snare trigger (on 2 and 4 = steps 4 and 12)
        if sixteenth_index in [4, 12]:
            for si, val in enumerate(snare_samples):
                if sample_idx + si < total_samples:
                    buffer_l[sample_idx + si] += val * 0.75
                    buffer_r[sample_idx + si] += val * 0.75
                    
        # Hi-Hat trigger (straight 8ths + occasional 16th roll)
        if sixteenth_index % 2 == 0 or sixteenth_index in [14, 15]:
            pan = 0.6 if sixteenth_index % 4 == 0 else 0.4
            for hi, val in enumerate(hat_samples):
                if sample_idx + hi < total_samples:
                    buffer_l[sample_idx + hi] += val * pan
                    buffer_r[sample_idx + hi] += val * (1.0 - pan)
                    
        current_time += sixteenth_sec
        step += 1
        
    # --- MELODIC CHORD STABS (Minor 9th tuned to 432 Hz) ---
    chord_freqs = [216.0, 256.0, 324.0, 384.0] # 432 Hz octave-halved minor chord
    for bar in range(int(duration_sec / (beat_sec * 4)) + 1):
        bar_sample = int(bar * beat_sec * 4 * SAMPLE_RATE)
        stab_len = int(SAMPLE_RATE * 1.8)
        for i in range(stab_len):
            idx = bar_sample + i
            if idx >= total_samples:
                break
            t = i / SAMPLE_RATE
            env = math.exp(-2.2 * t)
            stab = sum(math.sin(2 * math.pi * f * t) for f in chord_freqs) * 0.08 * env
            lfo = 0.5 + 0.3 * math.sin(2 * math.pi * 3.0 * t) # Tremolo
            buffer_l[idx] += stab * lfo
            buffer_r[idx] += stab * (1.0 - lfo)
            
    # Write output WAV
    with wave.open(output_wav_path, "w") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        
        frames = bytearray()
        for i in range(total_samples):
            # Soft master limiting
            l = math.tanh(buffer_l[i]) * 0.88
            r = math.tanh(buffer_r[i]) * 0.88
            
            sl = int(l * 32767.0)
            sr = int(r * 32767.0)
            frames.extend(struct.pack("<hh", sl, sr))
            
        wav_file.writeframes(frames)
        
    print(f"[Sebastian 808 Hip-Hop Beat] Generated: {output_wav_path} ({duration_sec}s @ {bpm} BPM)")
    return output_wav_path

if __name__ == "__main__":
    out_file = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\original_music\sebastian_808_hiphop_beat.wav"
    generate_808_hiphop_beat(out_file, duration_sec=36.0, bpm=88.0)
