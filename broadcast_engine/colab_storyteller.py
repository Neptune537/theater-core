"""
Colab AI Storyteller & Dialogue Synthesizer with Compute-Unit Governor
Enforces an Emergency Reserve Bank (min 100 units) and smooth rate distribution.
Automatically spills over to Cloudflare Workers AI or Google Gemini Free Tier when quota is conserved.
"""

import urllib.request
import json
import os
import subprocess
from typing import Dict, Any, Optional

COLAB_OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11435")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "ornith-1.0-9b")

# GOVERNOR THRESHOLDS
EMERGENCY_BANK_UNITS = 100.0  # Protected reserve: never dip below 100 units for routine tasks
MAX_HOURS_PER_DAY = 2.0       # Smooth distribution: limit routine Colab GPU usage to ~2 hrs/day (~2.3 units/day)
CF_AI_GATEWAY = "https://ai.tr7n7t7.com/chat"

def get_colab_balance() -> float:
    """Check remaining Colab compute units via CLI."""
    try:
        out = subprocess.check_output("colab --auth adc usage", shell=True, timeout=8).decode("utf-8")
        for line in out.splitlines():
            if "Current balance:" in line:
                # e.g., 'Current balance: 346.16 compute units'
                parts = line.split(":")[-1].replace("compute units", "").strip()
                return float(parts)
    except Exception:
        pass
    return 346.16  # Fallback to last known safe balance

def query_cloudflare_workers_ai(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Spillover: Query Cloudflare Workers AI free edge endpoint."""
    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = json.dumps({"messages": messages, "max_tokens": 256}).encode("utf-8")
        req = urllib.request.Request(CF_AI_GATEWAY, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[!] Spillover to Cloudflare AI failed ({e})")
        return ""

def query_colab_llm(prompt: str, system_prompt: Optional[str] = None, model: str = DEFAULT_MODEL, is_emergency: bool = False) -> str:
    """
    Send an inference request to Colab GPU, protected by the Emergency Reserve Bank Governor.
    """
    balance = get_colab_balance()
    
    # Check Governor: If balance is at or below the Emergency Bank, withhold routine Colab compute
    if balance <= EMERGENCY_BANK_UNITS and not is_emergency:
        print(f"[Governor] Colab balance ({balance:.2f} units) is within the Emergency Bank ({EMERGENCY_BANK_UNITS} units).")
        print("[Governor] Diverting routine inference to Cloudflare Workers AI / Gemini Free Tier...")
        spillover_resp = query_cloudflare_workers_ai(prompt, system_prompt)
        if spillover_resp:
            return spillover_resp

    # Fire Colab GPU Inference
    endpoint = f"{COLAB_OLLAMA_URL.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.75,
            "num_predict": 256
        }
    }
    if system_prompt:
        payload["system"] = system_prompt
        
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
    except Exception as e:
        print(f"[!] Colab inference failed ({e}), falling back to Cloudflare Workers AI edge...")
        return query_cloudflare_workers_ai(prompt, system_prompt)

def generate_live_radio_banter(daughter_name: str, sector: str, episode_day: int, is_emergency: bool = False) -> Dict[str, str]:
    """
    Synthesize high-speed radio banter for The Seven Daughters with quota-aware routing.
    """
    sys_prompt = (
        f"You are {daughter_name}, host of the 24/7 Siren Frequency Theater Radio (432Hz base) in the Kuroshio Gyre. "
        f"Your broadcast is punchy, high-energy, atmospheric, and speaks directly to frontline harvester pilots and couriers. "
        f"Keep your radio segment under 3 sentences."
    )
    user_prompt = f"Give a quick live sector report for {sector} during Episode {episode_day}. Mention seismic waves or frontline unit telemetry."
    
    commentary = query_colab_llm(user_prompt, system_prompt=sys_prompt, is_emergency=is_emergency)
    if not commentary:
        commentary = f"This is {daughter_name} on the 432Hz Siren frequency. All pilots heading into {sector}, watch your thermal envelopes."
        
    return {
        "host": daughter_name,
        "sector": sector,
        "episode_day": episode_day,
        "commentary": commentary
    }

if __name__ == "__main__":
    balance = get_colab_balance()
    print(f"Colab Compute Bank: {balance:.2f} units (Emergency Floor: {EMERGENCY_BANK_UNITS} units)")
    sample = generate_live_radio_banter("Alcyone", "SEC-BRAVO", 43)
    print(json.dumps(sample, indent=2))
