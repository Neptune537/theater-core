import asyncio
import os
import sys
import json
import datetime
import glob
import logging
from episodic_story_engine import generate_four_act_narrative
from tts_engine import synthesize_speech
from duck_radio_bed import mix_voiceover_with_ducked_bed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("hourly_scheduler")

SECTORS = ["SEC-ALPHA", "SEC-BRAVO", "SEC-CHARLIE", "SEC-DELTA", "SEC-ECHO"]

def find_default_music_bed(base_dir: str) -> str:
    """Finds an available music bed or DJ mix from cache or audio_output."""
    search_paths = [
        os.path.join(base_dir, "audio_output", "dj_mix_cache", "*.mp3"),
        os.path.join(base_dir, "audio_output", "*.mp3"),
        os.path.join(base_dir, "..", "vinyl", "*.mp3")
    ]
    for pattern in search_paths:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return ""

async def stitch_act_stems_ffmpeg(stem_paths: list, output_speech_path: str):
    """Concatenates all 4 synthesized act stems into a unified voice track."""
    import subprocess
    concat_list_file = output_speech_path + ".txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in stem_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        output_speech_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    if os.path.exists(concat_list_file):
        os.remove(concat_list_file)

async def run_hourly_cycle(hour_index: int, music_bed_path: str = None):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sector = SECTORS[hour_index % len(SECTORS)]
    episode_day = hour_index + 1
    
    logger.info("=" * 60)
    logger.info(f"[{now}] TRIGGERING AUTOMATED 4-ACT HOURLY WHEEL (CYCLE #{episode_day} // {sector})")
    logger.info("=" * 60)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(base_dir, "audio_output", f"hour_{episode_day}")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Generate 4-Act Canonical Narrative
    logger.info("[1/4] Compiling 4-Act Story Payload...")
    narrative = generate_four_act_narrative(episode_day, sector)
    
    # 2. Synthesize Audio for each Act via Revolver Engine
    logger.info("[2/4] Synthesizing Voice Stems via Revolver TTS Engine...")
    act_stems = []
    for idx, act in enumerate(narrative["acts"]):
        stem_path = os.path.join(out_dir, f"{act['act_id']}_{act['narrator']}.mp3")
        logger.info(f"  -> Act {idx + 1} ({act['act_id']}) [{act['narrator'].upper()}]: {act['title']}")
        await synthesize_speech(act["script"], act["narrator"], stem_path)
        act["stem_path"] = stem_path
        act_stems.append(stem_path)

    # 3. Concatenate all 4 acts into unified episode speech track
    full_speech_mp3 = os.path.join(out_dir, f"episode_{episode_day:04d}_dialogue.mp3")
    logger.info("[3/4] Assembling full dialogue sequence...")
    await stitch_act_stems_ffmpeg(act_stems, full_speech_mp3)

    # 4. Mix and Duck under Music Bed
    if not music_bed_path or not os.path.exists(music_bed_path):
        music_bed_path = find_default_music_bed(base_dir)

    mastered_drop_mp3 = os.path.join(out_dir, f"episode_{episode_day:04d}_mastered_drop.mp3")
    if music_bed_path and os.path.exists(music_bed_path):
        logger.info(f"[4/4] Ducking background bed ({os.path.basename(music_bed_path)}) under voice dialog...")
        mix_voiceover_with_ducked_bed(
            speech_path=full_speech_mp3,
            music_bed_path=music_bed_path,
            output_path=mastered_drop_mp3,
            duck_gain_db=-14.0
        )
    else:
        logger.warning("[4/4] No music bed found; saving dialogue stem as broadcast drop.")
        mastered_drop_mp3 = full_speech_mp3

    # Save manifest for Theater UI, live radio server, and MCP
    narrative["audio_stems"] = {
        "dialogue_full": full_speech_mp3,
        "mastered_drop": mastered_drop_mp3,
        "acts": [act["stem_path"] for act in narrative["acts"]]
    }
    manifest_path = os.path.join(out_dir, "broadcast_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(narrative, f, indent=2)

    logger.info(f"[OK] 4-Act Mastered Broadcast Package Ready: {manifest_path}")
    logger.info(f"Live Ticker Lines: {narrative['ticker']}")
    return narrative

async def main():
    import sys
    interval_seconds = 3600
    if len(sys.argv) > 1:
        try:
            interval_seconds = int(sys.argv[1])
        except ValueError:
            pass

    logger.info("[*] 24/7 Theater Broadcast Scheduler ACTIVE")
    logger.info(f"[*] Broadcast Interval: {interval_seconds}s")
    
    cycle = 0
    while True:
        try:
            await run_hourly_cycle(cycle)
            cycle += 1
            logger.info(f"[STANDBY] Sleeping {interval_seconds}s until next hour's cycle (#{cycle + 1})...")
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"[!] Cycle error: {e}. Retrying in 30s...", exc_info=True)
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
