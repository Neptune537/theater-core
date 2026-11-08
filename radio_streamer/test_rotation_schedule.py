import sys
sys.path.append(r"c:\Users\blue-\projects\theater\radio_streamer")
import datetime
from stream_server import get_active_daughter_for_hour

base_dt = datetime.datetime(2026, 11, 7, 10, 0)
print("=== 10:00 AM Host Roster Across 7 Consecutive Days ===")
for day in range(7):
    d = base_dt + datetime.timedelta(days=day)
    host = get_active_daughter_for_hour(d)
    print(f"Day {day+1} ({d.strftime('%A %b %d')}): {host['name']} ({host['freq']} Hz) - {host['genre']}")
