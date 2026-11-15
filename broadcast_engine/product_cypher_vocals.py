import asyncio
import os
import tts_engine

# High-energy, rhythmic Hip-Hop bars written specifically for Alcyone & Electra
# Flexing the platform products: Nautilus 3D Globe, Gaussian Splat Stores, 
# 432 Hz Siren Radio, Rapier3D Physics, and Coral Escrow
CYAN_CYPHER_VERSES = [
    {
        "character": "alcyone",
        "verse": (
            "Yo, check the coordinates, E-C-E-F on the line! "
            "Google Three-D Tiles streaming cities in real time! "
            "Forget a flat page, walk straight up in the store, "
            "Gaussian splat product floating off the showroom floor!"
        ),
        "file": "verse_01_alcyone.mp3"
    },
    {
        "character": "electra",
        "verse": (
            "Brembo carbon calipers, Rapier three-D speed, "
            "Zero point one micro-Cyan tipping what you need! "
            "Club Home Node encrypted in the vault, zero leaks, "
            "Siren frequency spinning seven daughters all week!"
        ),
        "file": "verse_02_electra.mp3"
    },
    {
        "character": "alcyone",
        "verse": (
            "Tide Ledger double-entry, zero variance locked, "
            "Hardware Proof of Health verified on the clock! "
            "From the hangar to the orbit, sixty hertz on the beat, "
            "Kuroshio Gyre, sovereign angels run the street!"
        ),
        "file": "verse_03_alcyone.mp3"
    }
]

async def generate_product_cypher():
    out_dir = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\cypher_vocals"
    os.makedirs(out_dir, exist_ok=True)
    print("==================================================================")
    print("[SEBASTIAN & DAUGHTERS] HIP-HOP PRODUCT CYPHER SYNTHESIS")
    print("==================================================================")
    
    generated = []
    for item in CYAN_CYPHER_VERSES:
        target = os.path.join(out_dir, item["file"])
        print(f"\n[Rap Delivery: {item['character'].upper()}] -> \"{item['verse'][:50]}...\"")
        path = await tts_engine.synthesize_speech(item["verse"], item["character"], target)
        generated.append(path)
        print(f" -> OK: {path}")
        
    print("\nAll Cypher vocal bars synthesized successfully!")
    return generated

if __name__ == "__main__":
    asyncio.run(generate_product_cypher())
