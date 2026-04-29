#!/usr/bin/env python3
"""V3: expanded script with the CTA (lecture-pitch + invitation), tighter
pacing — shorter inter-phrase silences, no big drone-only beat. Trailer
runtime now ~33–36s instead of 45s."""

import os, json, subprocess, urllib.request, re, sys, time
import imageio_ffmpeg

KEY_PATH = os.path.expanduser("~/.agents/secrets/wavespeed-key")
API_KEY  = open(KEY_PATH).read().strip()
PROJECT  = "/Users/tristianwalker/Personal Website /quiet-line-page"
ASSETS   = f"{PROJECT}/trailer-assets"
os.makedirs(ASSETS, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian

# Numbered prefix forces freshness (don't reuse v2 cached files)
PHRASES = [
    ("v3_p0_interaction",   "In every interaction, there is a quiet line."),
    ("v3_p1_presence",      "It's the line between presence and process."),
    ("v3_p2_drifts",        "When the task overrules the human, character drifts."),
    ("v3_p3_few_who_do",    "Most never notice. The few who do — take action."),
    ("v3_p4_lecture",       "This lecture is for those who've drifted, numb to the success they could still claim."),
    ("v3_p5_invitation",    "It's my journey toward greatness. Join me. Explore the possibilities of you."),
    ("v3_p6_byline",        "A lecture by Tristian Walker."),
]

def call_eleven(text, out_path):
    url = "https://api.wavespeed.ai/api/v3/elevenlabs/eleven-v3"
    body = json.dumps({
        "text": text, "voice_id": VOICE_ID,
        "stability": 0.55, "similarity": 0.78,
        "use_speaker_boost": True, "enable_sync_mode": True,
    }).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:500]}")
    audio_url = None
    data = resp.get("data") or {}
    if isinstance(data, dict):
        outs = data.get("outputs") or data.get("output") or data.get("audio")
        if isinstance(outs, list) and outs: audio_url = outs[0]
        elif isinstance(outs, str):         audio_url = outs
    audio_url = audio_url or resp.get("url") or resp.get("output_url")
    if not audio_url and (data.get("id") or resp.get("id")):
        pid = data.get("id") or resp.get("id")
        for _ in range(60):
            with urllib.request.urlopen(urllib.request.Request(
                f"https://api.wavespeed.ai/api/v3/predictions/{pid}/result",
                headers={"Authorization": f"Bearer {API_KEY}"})) as r:
                pr = json.loads(r.read())
            pdata = pr.get("data") or {}
            if (pdata.get("status") or pr.get("status")) == "completed":
                outs = pdata.get("outputs") or []
                if outs: audio_url = outs[0]
                break
            if (pdata.get("status") or pr.get("status")) in ("failed","error"):
                sys.exit(f"Prediction {pid} failed: {pr}")
            time.sleep(2)
    if not audio_url:
        sys.exit(f"No audio URL: {json.dumps(resp)[:600]}")
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
    paths, durs = {}, {}
    for key, text in PHRASES:
        out = f"{ASSETS}/{key}.mp3"
        if not os.path.exists(out):
            call_eleven(text, out)
        paths[key] = out
        durs[key]  = duration(out)
        print(f"    {key}: {durs[key]:.2f}s — {text}")

    # Tighter pacing — short silences between phrases (no big dead space)
    PAUSE_AFTER = {
        "v3_p0_interaction":   0.45,
        "v3_p1_presence":      0.55,
        "v3_p2_drifts":        0.55,
        "v3_p3_few_who_do":    0.7,    # beat after the rhetorical
        "v3_p4_lecture":       0.55,
        "v3_p5_invitation":    0.6,    # breath before the byline
        "v3_p6_byline":        0.0,
    }
    INTRO = 1.2  # short cold-open before first phrase
    starts = {}
    t = INTRO
    for key, _ in PHRASES:
        starts[key] = t
        t = t + durs[key] + PAUSE_AFTER[key]
    OUTRO_TAIL = 0.8
    TOTAL = round(t + OUTRO_TAIL, 2)
    print(f"\n[2] Layout (total {TOTAL}s):")
    for key, _ in PHRASES:
        print(f"    {key}: start={starts[key]:.2f}s end={starts[key]+durs[key]:.2f}s")

    # VO track
    print("\n[3] Assemble VO track…")
    vo_track = f"{ASSETS}/vo_track_v3.wav"
    inputs = ["-f", "lavfi", "-t", str(TOTAL), "-i",
              "anullsrc=channel_layout=stereo:sample_rate=48000"]
    for key, _ in PHRASES: inputs += ["-i", paths[key]]
    parts, mix = [], ["[0:a]"]
    for i, (key, _) in enumerate(PHRASES, start=1):
        ms = int(starts[key] * 1000)
        parts.append(f"[{i}:a]adelay={ms}|{ms},aformat=channel_layouts=stereo,volume=1.05[s{i}]")
        mix.append(f"[s{i}]")
    parts.append(
        f"{''.join(mix)}amix=inputs={len(PHRASES)+1}:duration=first:dropout_transition=0,"
        "acompressor=threshold=-18dB:ratio=3:attack=10:release=200,"
        "loudnorm=I=-18:LRA=11:TP=-2[out]"
    )
    ff([*inputs, "-filter_complex", ";".join(parts),
        "-map", "[out]", "-c:a", "pcm_s16le", vo_track])

    # Drone bed
    print("[4] Drone bed…")
    drone = f"{ASSETS}/drone_v3.wav"
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
        f"afade=t=in:st=0:d=2.0,afade=t=out:st={TOTAL-2.0}:d=2.0,"
        "volume=0.5[out]",
        "-map", "[out]", "-c:a", "pcm_s16le", drone,
    ])

    # Final mix with sidechain duck
    print("[5] Final mix…")
    final_audio = f"{ASSETS}/audio_v3.mp3"
    ff([
        "-i", vo_track, "-i", drone,
        "-filter_complex",
        "[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];"
        "[0:a][duck]amix=inputs=2:duration=first:weights=1.0 0.85,"
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k", final_audio,
    ])

    # Caption schedule for JS
    OB, OA = 0.20, 0.30
    schedule = []
    for i, (key, _) in enumerate(PHRASES):
        s = max(0, starts[key] - OB)
        e = starts[key] + durs[key] + OA
        schedule.append({"idx": i, "start": round(s, 2), "end": round(e, 2)})
    # Title card hold during the final phrase (byline)
    title_start = starts["v3_p5_invitation"] + durs["v3_p5_invitation"] - 0.5
    title_end   = TOTAL - 0.2

    print(f"\nDone.")
    print(f"  Audio: {final_audio} ({duration(final_audio):.2f}s)")
    print("\n  // Paste into index.html JS:")
    print("  const SCHEDULE = [")
    for c in schedule:
        print(f"      {{ idx: {c['idx']}, start: {c['start']:>6.2f}, end: {c['end']:>6.2f} }},")
    print("  ];")
    print(f"  // Title-card overlay: {title_start:.2f} – {title_end:.2f}")
    print(f"  // (overlaps with byline at idx {len(PHRASES)-1})")

    with open(f"{ASSETS}/cues_v3.json", "w") as f:
        json.dump({
            "duration": TOTAL,
            "title_card": {"start": round(title_start, 2), "end": round(title_end, 2)},
            "phrases": schedule,
        }, f, indent=2)

if __name__ == "__main__":
    main()
