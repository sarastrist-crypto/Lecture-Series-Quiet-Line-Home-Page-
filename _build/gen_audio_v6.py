#!/usr/bin/env python3
"""V6: same as v5, but the closing byline now says
'The Quiet Line, a lecture by Tristian Walker.'

Reuses v3 phrase files for everything except the byline (regenerated).
Same v5 cleaning pipeline (silence-trim + fades), same softened
sidechain duck. Bumps audio URL to ?v=6."""

import os, json, subprocess, urllib.request, re, sys, time
import imageio_ffmpeg

KEY_PATH = os.path.expanduser("~/.agents/secrets/wavespeed-key")
API_KEY  = open(KEY_PATH).read().strip()
PROJECT  = "/Users/tristianwalker/Personal Website /quiet-line-page"
ASSETS   = f"{PROJECT}/trailer-assets"
FFMPEG   = imageio_ffmpeg.get_ffmpeg_exe()
VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian

# v6_p6_byline is the only new file. The rest reuse v3 takes.
PHRASES = [
    ("v3_p0_interaction",   "In every interaction, there is a quiet line."),
    ("v3_p1_presence",      "It's the line between presence and process."),
    ("v3_p2_drifts",        "When the task overrules the human, character drifts."),
    ("v3_p3_few_who_do",    "Most never notice. The few who do — take action."),
    ("v3_p4_lecture",       "This lecture is for those who've drifted, numb to the success they could still claim."),
    ("v3_p5_invitation",    "It's my journey toward greatness. Join me. Explore the possibilities of you."),
    ("v6_p6_byline",        "The Quiet Line, a lecture by Tristian Walker."),
]

PAUSE_AFTER = {
    "v3_p0_interaction":   0.20,
    "v3_p1_presence":      0.22,
    "v3_p2_drifts":        0.25,
    "v3_p3_few_who_do":    0.28,
    "v3_p4_lecture":       0.22,
    "v3_p5_invitation":    0.30,   # slightly longer breath before the brand reveal
    "v6_p6_byline":        0.0,
}
INTRO       = 0.50
OUTRO_TAIL  = 0.5

def call_eleven(text, out_path):
    body = json.dumps({
        "text": text, "voice_id": VOICE_ID,
        "stability": 0.55, "similarity": 0.78,
        "use_speaker_boost": True, "enable_sync_mode": True,
    }).encode()
    req = urllib.request.Request(
        "https://api.wavespeed.ai/api/v3/elevenlabs/eleven-v3",
        data=body, method="POST",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
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

def clean_phrase(src_mp3, out_wav):
    tmp = out_wav + ".tmp.wav"
    ff(["-i", src_mp3, "-af",
        "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:detection=peak,"
        "areverse,silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:detection=peak,areverse,"
        "aformat=sample_rates=48000:channel_layouts=stereo",
        "-c:a", "pcm_s16le", tmp])
    d = duration(tmp)
    fade_out_start = max(0, d - 0.06)
    ff(["-i", tmp, "-af",
        f"afade=t=in:st=0:d=0.025,afade=t=out:st={fade_out_start:.3f}:d=0.06",
        "-c:a", "pcm_s16le", out_wav])
    os.remove(tmp)
    return duration(out_wav)

def main():
    # Generate the new byline (others already exist from v3)
    new_byline = f"{ASSETS}/v6_p6_byline.mp3"
    if not os.path.exists(new_byline):
        print(f"[1] Generating new byline: 'The Quiet Line, a lecture by Tristian Walker.'")
        call_eleven("The Quiet Line, a lecture by Tristian Walker.", new_byline)
        print(f"    saved → {new_byline}  ({duration(new_byline):.2f}s)")
    else:
        print(f"[1] Reusing existing byline ({duration(new_byline):.2f}s)")

    # Verify others
    for key, _ in PHRASES[:-1]:
        if not os.path.exists(f"{ASSETS}/{key}.mp3"):
            sys.exit(f"Missing phrase {key}; run gen_audio_v3.py first")

    # Clean all
    print("[2] Pre-clean phrases (silence-trim + fades)…")
    paths_clean, durs_clean = {}, {}
    for key, _ in PHRASES:
        src = f"{ASSETS}/{key}.mp3"
        clean = f"{ASSETS}/{key}.clean.wav"
        # Re-clean the byline (forces fresh) but reuse if WAV exists
        if key == "v6_p6_byline" or not os.path.exists(clean):
            d = clean_phrase(src, clean)
        else:
            d = duration(clean)
        paths_clean[key] = clean
        durs_clean[key]  = d
        print(f"    {key}: {d:.2f}s")

    starts = {}
    t = INTRO
    for key, _ in PHRASES:
        starts[key] = t
        t = t + durs_clean[key] + PAUSE_AFTER[key]
    TOTAL = round(t + OUTRO_TAIL, 2)

    print(f"\n[3] Layout (total {TOTAL}s):")
    for key, _ in PHRASES:
        print(f"    {key}: start={starts[key]:.2f}s end={starts[key]+durs_clean[key]:.2f}s")

    # Assemble
    print("\n[4] VO track…")
    vo_track = f"{ASSETS}/vo_track_v6.wav"
    inputs = ["-f", "lavfi", "-t", str(TOTAL), "-i",
              "anullsrc=channel_layout=stereo:sample_rate=48000"]
    for key, _ in PHRASES: inputs += ["-i", paths_clean[key]]
    parts, mix = [], ["[0:a]"]
    for i, (key, _) in enumerate(PHRASES, start=1):
        ms = int(starts[key] * 1000)
        parts.append(f"[{i}:a]adelay={ms}|{ms},aformat=channel_layouts=stereo,volume=1.05[s{i}]")
        mix.append(f"[s{i}]")
    parts.append(
        f"{''.join(mix)}amix=inputs={len(PHRASES)+1}:duration=first:dropout_transition=0,"
        "acompressor=threshold=-20dB:ratio=2:attack=15:release=300,"
        "loudnorm=I=-18:LRA=11:TP=-2[out]"
    )
    ff([*inputs, "-filter_complex", ";".join(parts),
        "-map", "[out]", "-c:a", "pcm_s16le", vo_track])

    print("[5] Drone bed…")
    drone = f"{ASSETS}/drone_v6.wav"
    ff([
        "-f", "lavfi", "-t", str(TOTAL), "-i", "sine=frequency=55:sample_rate=48000",
        "-f", "lavfi", "-t", str(TOTAL), "-i", "sine=frequency=55.4:sample_rate=48000",
        "-f", "lavfi", "-t", str(TOTAL), "-i", "sine=frequency=82.5:sample_rate=48000",
        "-filter_complex",
        "[0:a]volume=0.50[a1];[1:a]volume=0.42[a2];[2:a]volume=0.16[a3];"
        "[a1][a2][a3]amix=inputs=3:duration=first,"
        "tremolo=f=0.12:d=0.18,lowpass=f=180,"
        "aecho=0.7:0.85:600|1100|1700:0.35|0.25|0.15,"
        "aformat=channel_layouts=stereo,"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={TOTAL-1.5}:d=1.5,"
        "volume=0.42[out]",
        "-map", "[out]", "-c:a", "pcm_s16le", drone,
    ])

    print("[6] Final mix (gentle duck)…")
    final_audio = f"{ASSETS}/audio_v6.mp3"
    ff([
        "-i", vo_track, "-i", drone,
        "-filter_complex",
        "[1:a][0:a]sidechaincompress=threshold=0.06:ratio=4:attack=30:release=600[duck];"
        "[0:a][duck]amix=inputs=2:duration=first:weights=1.0 0.85,"
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k", final_audio,
    ])

    OB, OA = 0.15, 0.20
    schedule = []
    for i, (key, _) in enumerate(PHRASES):
        schedule.append({
            "idx": i,
            "start": round(max(0, starts[key] - OB), 2),
            "end":   round(starts[key] + durs_clean[key] + OA, 2),
        })

    print(f"\nFinal: {final_audio} ({duration(final_audio):.2f}s)")
    print("\n  // Paste into index.html JS:")
    print("  const SCHEDULE = [")
    for c in schedule:
        print(f"      {{ idx: {c['idx']}, start: {c['start']:>6.2f}, end: {c['end']:>6.2f} }},")
    print("  ];")

    with open(f"{ASSETS}/cues_v6.json", "w") as f:
        json.dump({"duration": TOTAL, "phrases": schedule}, f, indent=2)

if __name__ == "__main__":
    main()
