import asyncio
import os
import sys
import tts_engine

# The Seven Daughters 24/7 Siren Frequency Station Identifiers (Canonical 432 Hz base)
DAUGHTERS_STATION_IDS = [
    {
        "id": "maia",
        "freq": "432 Hz",
        "shift": "04:00 - 08:00 (Dawn Oceanic Ambient / Horizon Chill)",
        "script": "You are listening to Maia on the Siren Frequency, broadcasting at four thirty-two hertz. The morning horizon is calm, the Kuroshio swells are gentle, and the oceanic dawn is yours. Stay centered."
    },
    {
        "id": "alcyone",
        "freq": "528 Hz",
        "shift": "08:00 - 12:00 (High-Speed Cyberpunk D&B / Breakbeats)",
        "script": "Alcyone here, five twenty-eight hertz locked in. Pulse rates up, tactical relays active, and breakbeats pushing past one-seventy BPM. Do not blink—Atlantis is moving at Mach speed."
    },
    {
        "id": "asterope",
        "freq": "639 Hz",
        "shift": "12:00 - 16:00 (Tactical Deep House & Frontline Reports)",
        "script": "This is Asterope at six thirty-nine hertz. Frontline radar clear across the five linked sectors. Keep your frequency tuned, your Coral channels funded, and the bassline deep."
    },
    {
        "id": "celaeno",
        "freq": "741 Hz",
        "shift": "16:00 - 20:00 (Glitch / Industrial Bass / Storm Chaser)",
        "script": "Celaeno on the wire, seven forty-one hertz. The Karman vortex ring is tightening on the outer perimeter. If you are caught outside the shield, listen to the sub-bass and run."
    },
    {
        "id": "electra",
        "freq": "852 Hz",
        "shift": "20:00 - 00:00 (Vocal Trance / Eurobeat / Club Atlantis)",
        "script": "Electra broadcasting live for Club Atlantis on eight fifty-two hertz! The strobe arrays are lit, the convoy is rolling in, and the night belongs to the reborn angels. Turn it loud!"
    },
    {
        "id": "taygete",
        "freq": "963 Hz",
        "shift": "00:00 - 02:00 (Darkwave / Minimal Techno / Abyssal Drone)",
        "script": "Taygete whispering through nine sixty-three hertz. Midnight over the deep trench. Only shadows and low-frequency resonance down here. Keep quiet, and listen to the abyss."
    },
    {
        "id": "merope",
        "freq": "396 Hz",
        "shift": "02:00 - 04:00 (Lo-Fi / Starlight Harbor Acoustic)",
        "script": "Merope with you at three ninety-six hertz. Harbor lights are fading, starlight across the water. Rest your thrusters, wanderer. Tomorrow we rebuild the guild."
    }
]

async def batch_generate_seven_daughters():
    out_dir = os.path.join("audio_output", "daughters")
    os.makedirs(out_dir, exist_ok=True)
    print("==================================================================")
    print("[OPTION 1] SYNTHESIZING ALL SEVEN DAUGHTERS SIREN STATION IDENTIFIERS")
    print("==================================================================")
    
    results = []
    for daughter in DAUGHTERS_STATION_IDS:
        target_path = os.path.join(out_dir, f"siren_id_{daughter['id']}_{daughter['freq'].replace(' ', '')}.mp3")
        print(f"\n[Daughter: {daughter['id'].upper()}] - {daughter['freq']} | Shift: {daughter['shift']}")
        path = await tts_engine.synthesize_speech(daughter["script"], daughter["id"], target_path)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        results.append((daughter['id'], daughter['freq'], size, path))
        print(f" -> OK: {path} ({size} bytes)")
    
    print("\n------------------------------------------------------------------")
    print("ALL 7 DAUGHTERS BROADCAST IDS GENERATED:")
    for d_id, freq, size, path in results:
        print(f" * {d_id.capitalize():<10} [{freq:<7}] : {size} bytes -> {path}")
    print("------------------------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(batch_generate_seven_daughters())
