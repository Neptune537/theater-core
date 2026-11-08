import asyncio
import os
import sys
import json
import logging
import subprocess

logger = logging.getLogger("tts_engine")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Distinct character voice mappings with persona timbre and frequency characteristics
VOICE_MAP = {
    # --- TEAM 7 EXECUTIVE TRIAD ---
    "triton": {
        "edge_voice": "en-US-BrianNeural",
        "piper_voice": "en_US-lessac-medium",
        "gemini_voice": "Puck",
        "rate": "-3%",
        "pitch": "-4Hz",
    },
    "ursula": {
        "edge_voice": "en-US-SoniaNeural",
        "piper_voice": "en_US-amy-medium",
        "gemini_voice": "Kore",
        "rate": "+4%",
        "pitch": "+1Hz",
    },
    "sebastian": {
        "edge_voice": "en-US-GuyNeural",
        "piper_voice": "en_US-ryan-medium",
        "gemini_voice": "Fenrir",
        "rate": "+8%",
        "pitch": "+2Hz",
    },
    "antigravity": {
        "edge_voice": "en-US-EricNeural",
        "piper_voice": "en_US-lessac-medium",
        "gemini_voice": "Puck",
        "rate": "+2%",
        "pitch": "-1Hz",
    },

    # --- THE SEVEN DAUGHTERS (24/7 SIREN RADIO) ---
    "maia": {
        "edge_voice": "en-US-JennyNeural",
        "piper_voice": "en_US-amy-medium",
        "gemini_voice": "Aoede",
        "rate": "-2%",
        "pitch": "-1Hz",
        "frequency": "432 Hz",
    },
    "alcyone": {
        "edge_voice": "en-US-AriaNeural",
        "piper_voice": "en_US-libritts-high",
        "gemini_voice": "Leda",
        "rate": "+8%",
        "pitch": "+3Hz",
        "frequency": "528 Hz",
    },
    "asterope": {
        "edge_voice": "en-US-AvaNeural",
        "piper_voice": "en_US-amy-medium",
        "gemini_voice": "Kore",
        "rate": "+2%",
        "pitch": "+0Hz",
        "frequency": "639 Hz",
    },
    "celaeno": {
        "edge_voice": "en-US-MichelleNeural",
        "piper_voice": "en_US-amy-medium",
        "gemini_voice": "Aoede",
        "rate": "+5%",
        "pitch": "+2Hz",
        "frequency": "741 Hz",
    },
    "electra": {
        "edge_voice": "en-US-AnaNeural",
        "piper_voice": "en_US-libritts-high",
        "gemini_voice": "Leda",
        "rate": "+4%",
        "pitch": "+3Hz",
        "frequency": "852 Hz",
    },
    "taygete": {
        "edge_voice": "en-US-EmmaNeural",
        "piper_voice": "en_US-amy-medium",
        "gemini_voice": "Aoede",
        "rate": "-4%",
        "pitch": "-3Hz",
        "frequency": "963 Hz",
    },
    "merope": {
        "edge_voice": "en-US-JennyNeural",
        "piper_voice": "en_US-amy-medium",
        "gemini_voice": "Aoede",
        "rate": "-3%",
        "pitch": "-2Hz",
        "frequency": "396 Hz",
    },

    # --- NEWSROOM & WIRE CAST ---
    "kenji": {
        "edge_voice": "en-US-ChristopherNeural",
        "piper_voice": "en_US-lessac-medium",
        "gemini_voice": "Puck",
        "rate": "+0%",
        "pitch": "-2Hz",
    },
    "dex": {
        "edge_voice": "en-US-GuyNeural",
        "piper_voice": "en_US-ryan-medium",
        "gemini_voice": "Fenrir",
        "rate": "+18%",
        "pitch": "+3Hz",
    },
    "system": {
        "edge_voice": "en-US-AriaNeural",
        "piper_voice": "en_US-amy-medium",
        "gemini_voice": "Kore",
        "rate": "+5%",
        "pitch": "+0Hz",
    }
}

async def synthesize_with_edge(text: str, profile: dict, output_path: str) -> bool:
    """Primary Tier: Microsoft Edge-TTS."""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            text=text,
            voice=profile["edge_voice"],
            rate=profile["rate"],
            pitch=profile["pitch"],
        )
        await communicate.save(output_path)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            logger.info(f"[Edge-TTS OK] Generated {output_path} ({os.path.getsize(output_path)} bytes)")
            return True
    except Exception as e:
        logger.warning(f"[Edge-TTS Tripped / Failed]: {e}")
    return False

async def synthesize_with_gemini(text: str, profile: dict, output_path: str) -> bool:
    """Revolver Fallback Tier: Google Gemini Audio."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return False
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=text,
            config={
                "response_mime_type": "audio/mp3",
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": profile.get("gemini_voice", "Puck")
                        }
                    }
                }
            }
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                logger.info(f"[Gemini Audio OK] Fallback generated: {output_path}")
                return True
    except Exception as e:
        logger.warning(f"[Gemini Audio Fallback Failed]: {e}")
    return False

def chunk_text_by_sentences(text: str, max_chunk_chars: int = 3000) -> list[str]:
    """
    Splits long narrative scripts or live ticker bulletins into clean sentence chunks
    so downstream speech models do not timeout or exceed maximum single-request limits.
    """
    if len(text) <= max_chunk_chars:
        return [text]

    chunks = []
    current_chunk = []
    current_len = 0

    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        if current_len + len(sentence) + 1 > max_chunk_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_len = len(sentence)
        else:
            current_chunk.append(sentence)
            current_len += len(sentence) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

async def synthesize_with_openai_compatible(text: str, profile: dict, output_path: str) -> bool:
    """
    OpenAI-compatible speech endpoint (/v1/audio/speech).
    Supports local Kokoro ONNX, Groq Speech, or OpenRouter audio.
    """
    base_url = os.environ.get("OPENAI_TTS_BASE_URL", "http://127.0.0.1:8880/v1")
    api_key = os.environ.get("OPENAI_TTS_API_KEY", "not-needed-for-local")
    model = os.environ.get("OPENAI_TTS_MODEL", "kokoro")
    
    try:
        import urllib.request
        payload = json.dumps({
            "model": model,
            "input": text,
            "voice": profile.get("kokoro_voice", profile.get("edge_voice", "af_heart")),
            "response_format": "mp3",
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/audio/speech",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )

        loop = asyncio.get_running_loop()
        def _fetch():
            with urllib.request.urlopen(req, timeout=12) as response:
                return response.read()

        audio_bytes = await loop.run_in_executor(None, _fetch)
        if len(audio_bytes) > 200:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            logger.info(f"[Kokoro / OpenAI Audio OK] Generated: {output_path} ({len(audio_bytes)} bytes)")
            return True
    except Exception as e:
        logger.debug(f"[Kokoro / OpenAI Audio Unavailable]: {e}")
    return False
    """Tactical Fallback Tier: Local Offline Piper TTS (Blackout / WAN Resilient)."""
    try:
        # Check if piper executable is available in PATH
        cmd = ["piper", "--model", profile.get("piper_voice", "en_US-lessac-medium"), "--output_file", output_path]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(input=text)
        if proc.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            logger.info(f"[Piper Offline TTS OK] Local fallback generated: {output_path}")
            return True
    except Exception as e:
        logger.debug(f"[Piper TTS Unavailable]: {e}")
    return False

async def synthesize_speech(text: str, character: str, output_path: str):
    """
    Synthesize speech using the Free Model Revolver Engine:
    Chamber 1: Edge-TTS Neural (Zero-cost base)
    Chamber 2: OpenAI-compatible / Local Kokoro ONNX (/v1/audio/speech)
    Chamber 3: Google Gemini Audio Free Tier
    Chamber 4: Local Piper TTS (Hardened Mesh / Offline Survivability)
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    profile = VOICE_MAP.get(character.lower(), VOICE_MAP["system"])
    print(f"[*] Synthesizing [{character.upper()}] with voice {profile['edge_voice']} -> {output_path}")

    # Chunk text if necessary
    chunks = chunk_text_by_sentences(text, max_chunk_chars=3000)
    if len(chunks) > 1:
        logger.info(f"[Text Chunking Active] Processing {len(chunks)} sequential parts for long script...")

    # 1. Edge-TTS
    if await synthesize_with_edge(text, profile, output_path):
        return output_path

    # 2. Kokoro / Local OpenAI-Compatible Speech
    logger.info("[Revolver Revolving] Attempting Local Kokoro / OpenAI-compatible audio fallback...")
    if await synthesize_with_openai_compatible(text, profile, output_path):
        return output_path

    # 3. Gemini Audio Fallback
    logger.info("[Revolver Revolving] Attempting Gemini Free Tier Audio fallback...")
    if await synthesize_with_gemini(text, profile, output_path):
        return output_path

    # 4. Local Piper TTS Fallback
    logger.info("[Revolver Revolving] Attempting Local Offline Piper TTS fallback...")
    if await synthesize_with_piper(text, profile, output_path):
        return output_path

    raise RuntimeError(f"All TTS Revolver Chambers failed to synthesize voice for {character}")

async def main():
    if len(sys.argv) < 4:
        print("Usage: python tts_engine.py <character: kenji|dex|system> <text> <output_path>")
        sys.exit(1)

    char = sys.argv[1]
    text = sys.argv[2]
    out = sys.argv[3]
    await synthesize_speech(text, char, out)

if __name__ == "__main__":
    asyncio.run(main())
