#!/usr/bin/env python3
"""V2: per-phrase Brian VO with controlled silence between, so the visual
caption schedule and the spoken audio land on the same moments.

Layout the trailer needs:
  0.0 – 3.0   silence (cold open)
  3.0 – ?     "In every interaction…"
   ?  – ?     "…there is a quiet line."
   ?  – ?     "It is the line between presence and process."
   ?  – ?     "When the task overrules the human, character drifts."
   ?  – ?     "Most never notice it. The few who do…"
  ?   – 42.5  silence (title-card visual beat)
  42.5– 44.5  "A lecture by Tristian Walker."
  44.5– 45.5  fade-out tail
"""
import os, json, subprocess, urllib.request, re, sys
import imageio_ffmpeg

KEY_PATH = os.path.expanduser("~/.agents/secrets/wavespeed-key")
API_KEY  = open(KEY_PATH).read().strip()
PROJECT  = "/Users/tristianwalker/Personal Website /quiet-line-page"
ASSETS   = f"{PROJECT}/trailer-assets"
os.makedirs(ASSETS, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian

PHRASES = [
    ("p0_interaction",   "In every interaction..."),
    ("p1_quiet_line",    "...there is a quiet line."),
    ("p2_presence",      "It is the line between presence and process."),
    ("p3_drifts",        "When the task overrules the human, character drifts."),
    ("p4_few_who_do",    "Most never notice it. The few who do..."),
    ("p5_byline",        "A lecture by Tristian Walker."),
]

def call_eleven(text, out_path):
    url = "https://api.wavespeed.ai/api/v3/elevenlabs/eleven-v3"
    body = json.dumps({
        "text": text,
        "voice_id": VOICE_ID,
        "stability": 0.55,
        "similarity": 0.78,
        "use_speaker_boost": True,
        "enable_sync_mode": True,
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from WaveSpeed: {e.read().decode('utf-8','replace')[:500]}")

    audio_url = None
    data = resp.get("data") or {}
    if isinstance(data, dict):
        outs = data.get("outputs") or data.get("output") or data.get("audio")
        if isinstance(outs, list) and outs: audio_url = outs[0]
        elif isinstance(outs, str):         audio_url = outs
    audio_url = audio_url or resp.get("url") or resp.get("output_url")
    if not audio_url and (data.get("id") or resp.get("id")):
        pid = data.get("id") or resp.get("id")
        poll_url = f"https://api.wavespeed.ai/api/v3/predictions/{pid}/result"
        import time
        for _ in range(60):
            with urllib.request.urlopen(urllib.request.Request(poll_url, headers={"Authorization": f"Bearer {API_KEY}"})) as r:
                pr = json.loads(r.read())
            pdata = pr.get("data") or {}
            status = pdata.get("status") or pr.get("status")
            if status == "completed":
                outs = pdata.get("outputs") or []
                if outs: audio_url = outs[0]
                break
            if status in ("failed","error"):
                sys.exit(f"Prediction {pid} failed: {pr}")
            time.sleep(2)
    if not audio_url:
        sys.exit(f"Couldn't extract audio URL from response: {json.dumps(resp)[:600]}")
    with urllib.request.urlopen(audio_url, timeout=120) as r, open(out_path, "wb") as f:
        f.write(r.read())
    return out_path

def ff(args):
    return subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True)

def duration(path):
    out = subprocess.check_output([FFMPEG, "-i", path, "-f", "null", "-"], stderr=subprocess.STDOUT).decode()
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", out)
    return int(m[1])*3600 + int(m[2])*60 + float(m[3]) if m else 0.0

def main():
    print("[1] Synthesize Brian segments…")
    paths = {}
    durs  = {}
    for key, text in PHRASES:
        out = f"{ASSETS}/{key}.mp3"
        if not os.path.exists(out):
            call_eleven(text, out)
        paths[key] = out
        durs[key]  = duration(out)
        print(f"    {key}: {durs[key]:.2f}s — {text}")

    # Layout. We want the 5 main phrases to land between 3.0s and ~33s,
    # leaving 33–42.5s for the title-card visual beat, and 42.5–44.5s for
    # the byline.
    PAUSE_AFTER = {
        "p0_interaction":   0.55,
        "p1_quiet_line":    0.75,
        "p2_presence":      0.65,
        "p3_drifts":        0.60,
        "p4_few_who_do":    None,   # filler computed to land title card at 33.5s
        "p5_byline":        0.0,
    }
    TITLE_CARD_AT = 33.5
    BYLINE_AT     = 42.5

    starts = {}
    t = 3.0
    for key, _ in PHRASES:
        if key == "p5_byline":
            starts[key] = BYLINE_AT
            continue
        starts[key] = t
        if PAUSE_AFTER[key] is None:
            # Pad until TITLE_CARD_AT
            t = max(t + durs[key], TITLE_CARD_AT)
        else:
            t = t + durs[key] + PAUSE_AFTER[key]
    print("[2] Layout:")
    for key, _ in PHRASES:
        print(f"    {key}: start={starts[key]:.2f}s dur={durs[key]:.2f}s end={starts[key]+durs[key]:.2f}s")

    TOTAL = max(BYLINE_AT + durs["p5_byline"] + 0.8, 45.0)
    TOTAL = round(TOTAL, 2)
    print(f"    total: {TOTAL:.2f}s")

    # Assemble VO track with adelay per segment
    print("[3] Assemble VO track…")
    vo_track = f"{ASSETS}/vo_track_v2.wav"
    inputs = ["-f", "lavfi", "-t", str(TOTAL), "-i",
              "anullsrc=channel_layout=stereo:sample_rate=48000"]
    for key, _ in PHRASES:
        inputs += ["-i", paths[key]]
    filter_parts = []
    mix_inputs = ["[0:a]"]
    for i, (key, _) in enumerate(PHRASES, start=1):
        ms = int(starts[key] * 1000)
        filter_parts.append(
            f"[{i}:a]adelay={ms}|{ms},aformat=channel_layouts=stereo,volume=1.05[s{i}]"
        )
        mix_inputs.append(f"[s{i}]")
    filter_parts.append(
        f"{''.join(mix_inputs)}amix=inputs={len(PHRASES)+1}:duration=first:dropout_transition=0,"
        "acompressor=threshold=-18dB:ratio=3:attack=10:release=200,"
        "loudnorm=I=-18:LRA=11:TP=-2[out]"
    )
    ff([*inputs, "-filter_complex", ";".join(filter_parts),
        "-map", "[out]", "-c:a", "pcm_s16le", vo_track])

    # Drone bed
    print("[4] Drone bed…")
    drone = f"{ASSETS}/drone_v2.wav"
    ff([
        "-f", "lavfi", "-t", str(TOTAL), "-i", "sine=frequency=55:sample_rate=48000",
        "-f", "lavfi", "-t", str(TOTAL), "-i", "sine=frequency=55.4:sample_rate=48000",
        "-f", "lavfi", "-t", str(TOTAL), "-i", "sine=frequency=82.5:sample_rate=48000",
        "-filter_complex",
        "[0:a]volume=0.55[a1];[1:a]volume=0.45[a2];[2:a]volume=0.18[a3];"
        "[a1][a2][a3]amix=inputs=3:duration=first,"
        "tremolo=f=0.12:d=0.18,lowpass=f=180,"
        "aecho=0.7:0.85:600|1100|1700:0.35|0.25|0.15,"
        "aformat=channel_layouts=stereo,"
        f"afade=t=in:st=0:d=2.5,afade=t=out:st={TOTAL-2.5}:d=2.5,"
        "volume=0.55[out]",
        "-map", "[out]", "-c:a", "pcm_s16le", drone,
    ])

    # Mix VO + drone with sidechain duck
    print("[5] Final mix…")
    final_audio = f"{ASSETS}/audio_v2.mp3"
    ff([
        "-i", vo_track, "-i", drone,
        "-filter_complex",
        "[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];"
        "[0:a][duck]amix=inputs=2:duration=first:weights=1.0 0.85,"
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k", final_audio,
    ])

    # Caption schedule for JS — slightly pre/post each phrase for natural feel
    OVERLAP_BEFORE = 0.25
    OVERLAP_AFTER  = 0.35
    schedule = []
    for i, (key, _) in enumerate(PHRASES):
        start = max(0, starts[key] - OVERLAP_BEFORE)
        end   = starts[key] + durs[key] + OVERLAP_AFTER
        schedule.append({"idx": i, "start": round(start, 2), "end": round(end, 2)})
    # Title-card cue between the end of "few who do" and the start of byline
    title_start = starts["p4_few_who_do"] + durs["p4_few_who_do"] + 0.4
    title_end   = starts["p5_byline"] - 0.2
    cues = {
        "duration": TOTAL,
        "title_card": {"start": round(title_start, 2), "end": round(title_end, 2)},
        "phrases": schedule,
    }
    with open(f"{ASSETS}/cues_v2.json", "w") as f:
        json.dump(cues, f, indent=2)

    print(f"\nDone.")
    print(f"  Audio: {final_audio} ({duration(final_audio):.2f}s)")
    print(f"  Cues:  {ASSETS}/cues_v2.json")
    print("  Schedule (for JS):")
    for c in schedule:
        print(f"    idx {c['idx']}: {c['start']:.2f} – {c['end']:.2f}")
    print(f"    title-card: {title_start:.2f} – {title_end:.2f}")

if __name__ == "__main__":
    main()
