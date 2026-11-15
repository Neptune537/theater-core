"""
Original Harmonic Music Synthesizer for The Seven Daughters
Pure Python 3 standard library (math, wave, struct) - zero dependencies.
Generates authentic microtonal ambient beds tuned to the Daughters' harmonic scale
(Base: 432 Hz Solfeggio / Cosmic Tuning, 528 Hz DNA / Transformation, 639 Hz Connection).
"""

import math
import struct
import wave
import os

def generate_ambient_chord_track(
    output_wav_path: str,
    base_freq: float = 432.0,
    duration_sec: float = 30.0,
    sample_rate: int = 48000,
    sub_freq_ratio: float = 0.5, # 1 octave down
    fifth_ratio: float = 1.5,    # Perfect fifth
    major_third_ratio: float = 1.25, # Just major third
    octave_ratio: float = 2.0
):
    """
    Synthesizes a lush, warm analog-style ambient pad chord with slow LFO modulation,
    gentle binaural panning, and smooth envelope attack/decay.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
    total_samples = int(sample_rate * duration_sec)
    
    # Frequencies for the harmonic chord
    f_root = base_freq
    f_sub = base_freq * sub_freq_ratio
    f_third = base_freq * major_third_ratio
    f_fifth = base_freq * fifth_ratio
    f_octave = base_freq * octave_ratio
    
    # Detuning for analog warmth (chorus effect)
    detune = 0.75 # Hz
    
    fade_samples = int(sample_rate * 3.5) # 3.5s smooth fade-in and fade-out
    
    with wave.open(output_wav_path, "w") as wav_file:
        wav_file.setnchannels(2) # Stereo
        wav_file.setsampwidth(2) # 16-bit PCM
        wav_file.setframerate(sample_rate)
        
        frames = bytearray()
        
        for i in range(total_samples):
            t = i / sample_rate
            
            # Envelope (attack / sustain / release)
            if i < fade_samples:
                env = 0.5 * (1.0 - math.cos(math.pi * i / fade_samples))
            elif i > total_samples - fade_samples:
                env = 0.5 * (1.0 + math.cos(math.pi * (fade_samples - (total_samples - i)) / fade_samples))
            else:
                env = 1.0
                
            # Slow LFO filter sweep (0.15 Hz and 0.08 Hz)
            lfo1 = 0.7 + 0.3 * math.sin(2 * math.pi * 0.15 * t)
            lfo2 = 0.7 + 0.3 * math.cos(2 * math.pi * 0.08 * t)
            
            # Left & Right channel waveforms
            # Sub bass anchor
            sub = 0.28 * math.sin(2 * math.pi * f_sub * t)
            
            # Root & Detuned Root
            root_l = 0.22 * math.sin(2 * math.pi * (f_root - detune) * t) * lfo1
            root_r = 0.22 * math.sin(2 * math.pi * (f_root + detune) * t) * lfo2
            
            # Shimmering Major Third
            third_l = 0.16 * math.sin(2 * math.pi * f_third * t) * lfo2
            third_r = 0.16 * math.sin(2 * math.pi * (f_third + detune) * t) * lfo1
            
            # Resonant Fifth
            fifth_l = 0.18 * math.sin(2 * math.pi * (f_fifth - detune * 0.5) * t) * lfo1
            fifth_r = 0.18 * math.sin(2 * math.pi * (f_fifth + detune * 0.5) * t) * lfo2
            
            # Gentle High Octave Sparkle
            octave_l = 0.08 * math.sin(2 * math.pi * f_octave * t)
            octave_r = 0.08 * math.sin(2 * math.pi * (f_octave + detune) * t)
            
            # Composite mix
            mix_l = env * (sub + root_l + third_l + fifth_l + octave_l)
            mix_r = env * (sub + root_r + third_r + fifth_r + octave_r)
            
            # Soft limiting / saturation to avoid clipping
            mix_l = math.tanh(mix_l * 1.1) * 0.85
            mix_r = math.tanh(mix_r * 1.1) * 0.85
            
            # Convert to 16-bit signed PCM
            sample_l = int(mix_l * 32767.0)
            sample_r = int(mix_r * 32767.0)
            
            frames.extend(struct.pack("<hh", sample_l, sample_r))
            
        wav_file.writeframes(frames)
        
    print(f"[Harmonic Music Synth] Generated: {output_wav_path} ({duration_sec}s @ {base_freq}Hz)")
    return output_wav_path

if __name__ == "__main__":
    out_dir = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\original_music"
    
    # 1. Maia 432 Hz Dawn Horizon
    generate_ambient_chord_track(
        os.path.join(out_dir, "maia_432hz_ambient_bed.wav"),
        base_freq=432.0,
        duration_sec=30.0
    )
    
    # 2. Alcyone 528 Hz Transformation / Cyber Beat Bed
    generate_ambient_chord_track(
        os.path.join(out_dir, "alcyone_528hz_break_pad.wav"),
        base_freq=528.0,
        duration_sec=30.0
    )
