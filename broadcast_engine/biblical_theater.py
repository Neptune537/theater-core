"""
Biblical Radio Theater & Canon Narratives Module
Curated historical biblical accounts structured into 4 Canonical Acts
for real-time audio theater narration by The Seven Daughters on Siren Radio.
"""

from typing import Dict, Any, List

BIBLICAL_CHRONICLES = [
    {
        "id": "CREATION_DAWN",
        "book": "Genesis 1-2",
        "title": "The First Morning: Voice Upon the Waters",
        "narrator": "Maia",
        "frequency": "432 Hz",
        "foley": "Deep ocean swells, rushing planetary wind, resonant dawn choral swell",
        "lines": [
            "In the beginning, darkness moved over the face of the deep, and the Spirit of God swept across the primal waters.",
            "Let there be light, spoken into the void, dividing the day from the night in holy order.",
            "The firmament lifted above the seas, establishing the celestial compass by which every sailor and wanderer charts their journey."
        ],
        "moral_reflection": "Order called out of chaos by voice alone."
    },
    {
        "id": "RED_SEA_CROSSING",
        "book": "Exodus 14",
        "title": "The Parting of the Abyssal Waters",
        "narrator": "Alcyone",
        "frequency": "528 Hz",
        "foley": "Rushing hurricane east wind, crashing pillar of fire, chariot wheels grinding stone",
        "lines": [
            "With the Egyptian vanguard pressing from behind, Moses stretched forth his rod over the churning sea.",
            "All that night, a great east wind divided the flood, and the children walked upon dry seabed with water walled like glass to their right and left.",
            "Fear not: stand firm, and witness the deliverance of the Lord, for the forces that pursue you today you shall never see again."
        ],
        "moral_reflection": "When the way forward seems barred by deep water, faith parts the sea."
    },
    {
        "id": "DAVID_GOLIATH",
        "book": "1 Samuel 17",
        "title": "The Valley of Elah: Five Smooth Stones",
        "narrator": "Asterope",
        "frequency": "639 Hz",
        "foley": "Bronze armor clanking, brook water trickling over stones, whirring leather sling, dull impact",
        "lines": [
            "In the valley of Elah, the Philistine champion shouted defiance across the ranks of Israel for forty days.",
            "David chose five smooth stones from the running brook, carrying no bronze spear or heavy mail, only the name of the Lord of Hosts.",
            "The sling hummed, the stone struck true, and the mighty giant fell face down upon the earth."
        ],
        "moral_reflection": "Not by armor or spear, but by conviction and righteousness is the battle won."
    },
    {
        "id": "ELIJAH_WHISPER",
        "book": "1 Kings 19",
        "title": "Mount Horeb: The Still Small Voice",
        "narrator": "Taygete",
        "frequency": "963 Hz",
        "foley": "Rending hurricane tearing rocks, earthquake tremor, roaring wildfire, sudden breathless silence",
        "lines": [
            "Behold, a great and strong wind tore the mountains and broke in pieces the rocks before the Lord, but the Lord was not in the wind.",
            "After the wind came an earthquake, but the Lord was not in the earthquake. And after the earthquake, a consuming fire, but the Lord was not in the fire.",
            "And after the fire came a gentle whisper, a still small voice, bringing peace to the solitary prophet."
        ],
        "moral_reflection": "True divine authority is found not in chaotic storms, but in quiet clarity."
    },
    {
        "id": "JONAH_DEEP",
        "book": "Jonah 1-2",
        "title": "Out of the Belly of Sheol: Prayer from the Abyss",
        "narrator": "Celaeno",
        "frequency": "741 Hz",
        "foley": "Heavy wooden timbers groaning, crashing maritime gale, muffled underwater resonance, heartbeat",
        "lines": [
            "The waters closed in over me to take my life; the deep surrounded me; weeds were wrapped about my head at the roots of the mountains.",
            "I went down to the land whose bars closed upon me forever, yet You brought up my life from the pit, O Lord my God.",
            "When my soul fainted within me, I remembered the Lord, and my prayer rose to Your holy temple."
        ],
        "moral_reflection": "Even from the deepest underwater trench, no soul is beyond redemption."
    },
    {
        "id": "CALMING_THE_STORM",
        "book": "Mark 4:35-41",
        "title": "Peace, Be Still: The Sea of Galilee",
        "narrator": "Electra",
        "frequency": "852 Hz",
        "foley": "Violent squall whipping canvas, waves swamping the hull, authoritative command, sudden glassy calm",
        "lines": [
            "A furious squall broke out, and the waves broke over the boat so that it was nearly swamped, while Jesus was in the stern sleeping on a cushion.",
            "The disciples awoke Him crying, 'Master, do You not care if we drown?'",
            "He arose, rebuked the wind and said to the sea, 'Peace! Be still!' And the wind ceased, and there was a dead calm."
        ],
        "moral_reflection": "In the fiercest tempest, the voice of peace commands the storm."
    },
    {
        "id": "PSALM_23_REST",
        "book": "Psalm 23",
        "title": "Beside Still Waters: The Shepherd's Refuge",
        "narrator": "Merope",
        "frequency": "396 Hz",
        "foley": "Gentle acoustic guitar arpeggio, night crickets, soft water rippling, distant flock bells",
        "lines": [
            "The Lord is my shepherd; I shall not want. He makes me lie down in green pastures; He leads me beside quiet waters.",
            "He restores my soul; He guides me in paths of righteousness for His name's sake.",
            "Yea, though I walk through the valley of the shadow of death, I will fear no evil, for You are with me; Your rod and Your staff, they comfort me."
        ],
        "moral_reflection": "Protection, restoration, and harbor rest for the weary traveler."
    }
]

def get_biblical_theater_feature(index: int) -> Dict[str, Any]:
    """Retrieve an authoritative biblical chronicle for radio theater narration."""
    return BIBLICAL_CHRONICLES[index % len(BIBLICAL_CHRONICLES)]
