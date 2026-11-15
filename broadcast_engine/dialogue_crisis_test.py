import asyncio
import os
import tts_engine

# High-stakes dual-speaker crisis dialogue between Studio Anchor Kenji Vance and Field Stringer Dexter Sloan
DIALOGUE_TURNS = [
    {
        "speaker": "kenji",
        "text": "This is Kenji Vance in the central studio. We have an unconfirmed alert from Sector Charlie near the fuel refinery. Automated telemetry is showing anomalous energy spikes on the perimeter radar.",
        "file": "dialogue_turn_01_kenji.mp3"
    },
    {
        "speaker": "dex",
        "text": "Kenji, can you hear me? Sloan on the wire! I am on the ridge overlooking Sector Charlie right now. It is not an anomaly, we have active combat drones deploying near the refinery gate! Power grid is fluctuating!",
        "file": "dialogue_turn_02_dex.mp3"
    },
    {
        "speaker": "kenji",
        "text": "Dex, keep your distance. The MCV construction yard is routing backup power from the fusion plant. What is your visual on the defense grid? Are the point defense cannons engaging?",
        "file": "dialogue_turn_03_kenji.mp3"
    },
    {
        "speaker": "dex",
        "text": "They just came online! Twin lasers tracking the airborne drones! But Kenji, look at the sky! The Karman storm ring is contracting fast! If the outer convoy doesn't get inside the shield boundary in four minutes, they are going to get caught in the vortex!",
        "file": "dialogue_turn_04_dex.mp3"
    },
    {
        "speaker": "kenji",
        "text": "Understood. We are broadcasting an emergency alert on all frequencies. All civilian craft and refinery rovers, execute tactical return immediately. Repeat, clear the perimeter. Dex, fall back to the safe zone now.",
        "file": "dialogue_turn_05_kenji.mp3"
    }
]

async def generate_dual_speaker_dialogue():
    out_dir = os.path.join("audio_output", "dialogue")
    os.makedirs(out_dir, exist_ok=True)
    print("==================================================================")
    print("[OPTION 2] DUAL-SPEAKER CRISIS DIALOGUE: KENJI VANCE & DEXTER SLOAN")
    print("==================================================================")
    
    total_bytes = 0
    manifest = []
    
    for idx, turn in enumerate(DIALOGUE_TURNS, 1):
        target_path = os.path.join(out_dir, turn["file"])
        print(f"\n[Turn {idx}] {turn['speaker'].upper()}: \"{turn['text'][:60]}...\"")
        path = await tts_engine.synthesize_speech(turn["text"], turn["speaker"], target_path)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        total_bytes += size
        manifest.append({
            "turn": idx,
            "speaker": turn["speaker"],
            "text": turn["text"],
            "path": path,
            "bytes": size
        })
        print(f" -> OK: {path} ({size} bytes)")
        
    print("\n------------------------------------------------------------------")
    print(f"DUAL-SPEAKER DIALOGUE COMPLETE: {len(manifest)} turns, {total_bytes} total bytes")
    print("------------------------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(generate_dual_speaker_dialogue())
