import os
import json
import asyncio
import datetime
import logging
from episodic_story_engine import generate_four_act_narrative
from colab_storyteller import generate_live_radio_banter
from tts_engine import synthesize_speech
from duck_radio_bed import mix_voiceover_with_ducked_bed
from hourly_scheduler import stitch_act_stems_ffmpeg, find_default_music_bed

logger = logging.getLogger("produce_package")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DAUGHTER_SCHEDULE = [
    ("Maia", "SEC-ALPHA", (4, 8)),
    ("Alcyone", "SEC-BRAVO", (8, 12)),
    ("Asterope", "SEC-CHARLIE", (12, 16)),
    ("Celaeno", "SEC-DELTA", (16, 20)),
    ("Electra", "SEC-ECHO", (20, 24)),
    ("Taygete", "SEC-CHARLIE", (0, 2)),
    ("Merope", "SEC-ALPHA", (2, 4)),
]

def get_active_daughter(hour: int):
    for name, sec, (s, e) in DAUGHTER_SCHEDULE:
        if s <= hour < e:
            return name, sec
    return "Maia", "SEC-ALPHA"

async def produce_broadcast_package(episode_day: int, output_dir: str = None, render_audio: bool = True):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if not output_dir:
        output_dir = os.path.join(base_dir, "audio_output", f"hour_{episode_day}")
    os.makedirs(output_dir, exist_ok=True)
    
    now = datetime.datetime.now()
    hour = now.hour
    daughter, default_sec = get_active_daughter(hour)
    
    logger.info(f"[*] Compiling Canonical Episode {episode_day} Package (Active Host: {daughter} @ {default_sec})")
    
    # 1. 4-Act Story Payload
    narrative = generate_four_act_narrative(episode_day, default_sec)
    
    # 2. Host Radio Banter
    try:
        banter = generate_live_radio_banter(daughter, default_sec, episode_day)
        narrative["daughter_banter"] = banter
    except Exception as e:
        logger.warning(f"Could not reach remote Colab banter tunnel ({e}); proceeding with standard 4 acts.")

    if render_audio:
        logger.info("[*] Synthesizing 4-Act Stems...")
        act_stems = []
        for act in narrative["acts"]:
            stem_path = os.path.join(output_dir, f"{act['act_id']}_{act['narrator']}.mp3")
            await synthesize_speech(act["script"], act["narrator"], stem_path)
            act["stem_path"] = stem_path
            act_stems.append(stem_path)

        # Assemble speech dialog
        full_speech_mp3 = os.path.join(output_dir, f"episode_{episode_day:04d}_dialogue.mp3")
        await stitch_act_stems_ffmpeg(act_stems, full_speech_mp3)

        # Duck background music bed
        music_bed = find_default_music_bed(base_dir)
        mastered_drop_mp3 = os.path.join(output_dir, f"episode_{episode_day:04d}_mastered_drop.mp3")
        if music_bed and os.path.exists(music_bed):
            logger.info(f"[*] Applying OpenMontage sidechain ducking over {os.path.basename(music_bed)}...")
            mix_voiceover_with_ducked_bed(full_speech_mp3, music_bed, mastered_drop_mp3, duck_gain_db=-14.0)
        else:
            mastered_drop_mp3 = full_speech_mp3

        narrative["audio_stems"] = {
            "dialogue_full": full_speech_mp3,
            "mastered_drop": mastered_drop_mp3,
            "acts": act_stems
        }

    manifest_path = os.path.join(output_dir, f"broadcast_manifest_EP{episode_day:04d}.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(narrative, f, indent=2)
        
    logger.info(f"[+] Broadcast package saved: {manifest_path}")
    return narrative

if __name__ == "__main__":
    asyncio.run(produce_broadcast_package(45, render_audio=False))
