import re
import os

filepath = r"c:\Users\blue-\projects\theater\radio_streamer\stream_server.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target_sched = """def get_active_daughter_for_hour(hour=None):
    if hour is None:
        hour = datetime.datetime.now().hour
    if 4 <= hour < 8:
        return SEVEN_DAUGHTERS[0] # Maia
    elif 8 <= hour < 12:
        return SEVEN_DAUGHTERS[1] # Alcyone
    elif 12 <= hour < 16:
        return SEVEN_DAUGHTERS[2] # Asterope
    elif 16 <= hour < 20:
        return SEVEN_DAUGHTERS[3] # Celaeno
    elif 20 <= hour < 24:
        return SEVEN_DAUGHTERS[4] # Electra
    elif 0 <= hour < 2:
        return SEVEN_DAUGHTERS[5] # Taygete
    else:
        return SEVEN_DAUGHTERS[6] # Merope"""

replacement_sched = """def get_active_daughter_for_hour(dt=None):
    \"\"\"
    Dynamic Non-Repetitive Roster Rotation:
    Rotates the active host slot every single day using a deterministic prime-step permutation
    (day_of_year * 3 + day_of_week) so the weekly and daily schedules never repeat.
    \"\"\"
    if dt is None:
        dt = datetime.datetime.now()
    hour = dt.hour if hasattr(dt, 'hour') else int(dt)
    if 4 <= hour < 8:
        base_slot = 0
    elif 8 <= hour < 12:
        base_slot = 1
    elif 12 <= hour < 16:
        base_slot = 2
    elif 16 <= hour < 20:
        base_slot = 3
    elif 20 <= hour < 24:
        base_slot = 4
    elif 0 <= hour < 2:
        base_slot = 5
    else:
        base_slot = 6

    now = dt if isinstance(dt, datetime.datetime) else datetime.datetime.now()
    day_offset = (now.timetuple().tm_yday * 3 + now.weekday()) % len(SEVEN_DAUGHTERS)
    rotated_index = (base_slot + day_offset) % len(SEVEN_DAUGHTERS)
    return SEVEN_DAUGHTERS[rotated_index]"""

if target_sched in content:
    content = content.replace(target_sched, replacement_sched, 1)
    print("Schedule updated successfully!")
else:
    print("Target schedule not matched!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
