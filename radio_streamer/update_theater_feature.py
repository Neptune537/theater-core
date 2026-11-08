import re

filepath = r"c:\Users\blue-\projects\theater\radio_streamer\stream_server.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target_block = """    if is_breaking:
        seb_line = f"Order! Attention all stations across the Cyan Network and Club Atlantis! Sebastian here! Emergency interruption on {daughter['freq']} Hertz! {daughter['name']}, take the emergency line now!"
        d_line = f"Breaking report from the wires: {news_text}! Urgent alert on titan chaos: {chaos_text}! Frontline frequency holding at {daughter['freq']} Hertz!"
    else:
        seb_line = f"This is Sebastian, Conductor of the Cyan Network broadcast. Order in the studio, please! It is time for our scheduled Siren update on {daughter['freq']} Hertz. Taking the broadcast desk now is {daughter['name']} hosting {daughter['genre']}."
        if daughter["name"] == "Maia":
            d_line = f"Good dawn from Maia at 432 Hertz oceanic horizon. Surface conditions in {weather_info['area']} are holding at {weather_info['temp']} with {weather_info['condition']}. Wire report: {news_text}."
        elif daughter["name"] == "Alcyone":
            d_line = f"Alcyone locked in at 528 Hertz breakbeats! Cyberpunk wire is burning: {rumor_text}! The frontline sensors confirm sub-oceanic activity!"
        elif daughter["name"] == "Asterope":
            d_line = f"Asterope on tactical desk at 639 Hertz. Developing wire: {news_text}. Secondary dispatch: {headlines[1] if len(headlines)>1 else news_text}. All frontline relays remain live."
        elif daughter["name"] == "Celaeno":
            d_line = f"Celaeno storm chaser frequency at 741 Hertz! In {weather_info['area']}, we are tracking {weather_info['condition']}, temperatures at {weather_info['temp']}, humidity {weather_info['humidity']}, and winds gusting {weather_info['wind']}."
        elif daughter["name"] == "Electra":
            d_line = f"Electra at 852 Hertz trance stage! Critical update: {chaos_text}! Club Atlantis dancefloor and defensive shield telemetry are fully synchronized!"
        elif daughter["name"] == "Taygete":
            d_line = f"Taygete here at 963 Hertz darkwave drone. Abyssal trenches registering deep frequency vibrations. Maintain defensive vigilance."
        else: # Merope
            d_line = f"Merope with 396 Hertz lo-fi harbor vibes. Relaxing into the starlight acoustic harbor as night settles over the citadel. Enjoy the music rotation!"

    full_script = f"{seb_line} ... {d_line} ... Sebastian concluding: And now, back to our synchronized vinyl turntables!\""""

replacement_block = """    # Daily Dynamic Feature Selection: Rotate between Canonical Biblical Theater & Station Wire
    now_dt = datetime.datetime.now()
    # Deterministic daily narrative seed: different chronicle every day and hour
    feature_index = (now_dt.timetuple().tm_yday * 7 + now_dt.hour + (daughter_idx or 0)) % 7
    biblical_feature = get_biblical_theater_feature(feature_index) if get_biblical_theater_feature else None

    # Alternate between Biblical Radio Drama Feature and Live Wire Report
    is_theater_feature = (not is_breaking) and (biblical_feature is not None) and (now_dt.minute < 30 or daughter_idx % 2 == 1)

    if is_breaking:
        seb_line = f"Order! Attention all stations across the Cyan Network and Club Atlantis! Sebastian here! Emergency interruption on {daughter['freq']} Hertz! {daughter['name']}, take the emergency line now!"
        d_line = f"Breaking report from the wires: {news_text}! Urgent alert on titan chaos: {chaos_text}! Frontline frequency holding at {daughter['freq']} Hertz!"
        full_script = f"{seb_line} ... {d_line} ... Sebastian concluding: And now, back to our synchronized vinyl turntables!"
    elif is_theater_feature and biblical_feature:
        seb_line = f"This is Sebastian, Conductor of the Cyan Network broadcast. Order in the studio, listeners! We present today's Radio Theater feature: {biblical_feature['title']}, taken from {biblical_feature['book']}. Narrated in live spatial acoustic foley by {daughter['name']} at {daughter['freq']} Hertz."
        scripture_body = " ... ".join(biblical_feature["lines"])
        d_line = f"From {biblical_feature['book']}: {scripture_body} ... Moral reflection: {biblical_feature['moral_reflection']}"
        full_script = f"{seb_line} ... {d_line} ... Sebastian concluding: That concludes today's Radio Theater performance. And now, returning to our 24/7 vinyl rotation!"
    else:
        seb_line = f"This is Sebastian, Conductor of the Cyan Network broadcast. Order in the studio, please! It is time for our scheduled Siren update on {daughter['freq']} Hertz. Taking the broadcast desk now is {daughter['name']} hosting {daughter['genre']}."
        if daughter["name"] == "Maia":
            d_line = f"Good dawn from Maia at 432 Hertz oceanic horizon. Surface conditions in {weather_info['area']} are holding at {weather_info['temp']} with {weather_info['condition']}. Wire report: {news_text}."
        elif daughter["name"] == "Alcyone":
            d_line = f"Alcyone locked in at 528 Hertz breakbeats! Cyberpunk wire is burning: {rumor_text}! The frontline sensors confirm sub-oceanic activity!"
        elif daughter["name"] == "Asterope":
            d_line = f"Asterope on tactical desk at 639 Hertz. Developing wire: {news_text}. Secondary dispatch: {headlines[1] if len(headlines)>1 else news_text}. All frontline relays remain live."
        elif daughter["name"] == "Celaeno":
            d_line = f"Celaeno storm chaser frequency at 741 Hertz! In {weather_info['area']}, we are tracking {weather_info['condition']}, temperatures at {weather_info['temp']}, humidity {weather_info['humidity']}, and winds gusting {weather_info['wind']}."
        elif daughter["name"] == "Electra":
            d_line = f"Electra at 852 Hertz trance stage! Critical update: {chaos_text}! Club Atlantis dancefloor and defensive shield telemetry are fully synchronized!"
        elif daughter["name"] == "Taygete":
            d_line = f"Taygete here at 963 Hertz darkwave drone. Abyssal trenches registering deep frequency vibrations. Maintain defensive vigilance."
        else: # Merope
            d_line = f"Merope with 396 Hertz lo-fi harbor vibes. Relaxing into the starlight acoustic harbor as night settles over the citadel. Enjoy the music rotation!"
        full_script = f"{seb_line} ... {d_line} ... Sebastian concluding: And now, back to our synchronized vinyl turntables!\""""

if target_block in content:
    content = content.replace(target_block, replacement_block, 1)
    print("Biblical Radio Theater integration replaced successfully!")
else:
    print("Target block not matched!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
