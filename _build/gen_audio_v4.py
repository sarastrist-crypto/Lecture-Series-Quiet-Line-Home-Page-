#!/usr/bin/env python3
"""V4: same script as v3, but pacing aggressively tightened.
Reuses the existing v3_*.mp3 phrase files (no new ElevenLabs calls)
and just rebuilds the assembly + drone + mix with shorter gaps.

Pause budget:
  v3: 0.45–0.70s pauses, 1.20s intro  → 31.15s total
  v4: 0.18–0.28s pauses, 0.50s intro  → ~26s total
"""

import os, json, subprocess, re, sys, imageio_ffmpeg

PROJECT = "/Users/tristianwalker/Personal Website /quiet-line-page"
ASSETS  = f"{PROJECT}/trailer-assets"
FFMPEG  = imageio_ffmpeg.get_ffmpeg_exe()

PHRASES = [
    ("v3_p0_interaction",   "In every interaction, there is a quiet line."),
    ("v3_p1_presence",      "It's the line between presence and process."),
    ("v3_p2_drifts",        "When the task overrules the human, character drifts."),
    ("v3_p3_few_who_do",    "Most never notice. The few who do — take action."),
    ("v3_p4_lecture",       "This lecture is for those who've drifted, numb to the success they could still claim."),
    ("v3_p5_invitation",    "It's my journey toward greatness. Join me. Explore the possibilities of you."),
    ("v3_p6_byline",        "A lecture by Tristian Walker."),
]

PAUSE_AFTER = {
    "v3_p0_interaction":   0.20,
    "v3_p1_presence":      0.22,
    "v3_p2_drifts":        0.25,
    "v3_p3_few_who_do":    0.28,   # rhetorical beat
    "v3_p4_lecture":       0.22,
    "v3_p5_invitation":    0.22,
    "v3_p6_byline":        0.0,
}
INTRO       = 0.50
OUTRO_TAIL  = 0.5

def ff(args):
    return subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True)

def duration(path):
    out = subprocess.check_output([FFMPEG, "-i", path, "-f", "null", "-"], stderr=subprocess.STDOUT).decode()
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", out)
    return int(m[1])*3600 + int(m[2])*60 + float(m[3]) if m else 0.0

def main():
    paths, durs = {}, {}
    for key, _ in PHRASES:
        p = f"{ASSETS}/{key}.mp3"
        if not os.path.exists(p):
            sys.exit(f"Missing phrase file {p} — run gen_audio_v3.py first.")
        paths[key] = p
        durs[key]  = duration(p)

    starts = {}
    t = INTRO
    for key, _ in PHRASES:
        starts[key] = t
        t = t + durs[key] + PAUSE_AFTER[key]
    TOTAL = round(t + OUTRO_TAIL, 2)

    print(f"Layout (total {TOTAL}s):")
    for key, _ in PHRASES:
        print(f"  {key}: start={starts[key]:.2f}s end={starts[key]+durs[key]:.2f}s dur={durs[key]:.2f}s gap_after={PAUSE_AFTER[key]:.2f}s")

    # VO track
    vo_track = f"{ASSETS}/vo_track_v4.wav"
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

    # Drone
    drone = f"{ASSETS}/drone_v4.wav"
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
        "volume=0.45[out]",
        "-map", "[out]", "-c:a", "pcm_s16le", drone,
    ])

    # Mix
    final_audio = f"{ASSETS}/audio_v4.mp3"
    ff([
        "-i", vo_track, "-i", drone,
        "-filter_complex",
        "[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];"
        "[0:a][duck]amix=inputs=2:duration=first:weights=1.0 0.85,"
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k", final_audio,
    ])

    # Caption schedule
    OB, OA = 0.15, 0.20
    schedule = []
    for i, (key, _) in enumerate(PHRASES):
        s = max(0, starts[key] - OB)
        e = starts[key] + durs[key] + OA
        schedule.append({"idx": i, "start": round(s, 2), "end": round(e, 2)})
    title_start = starts["v3_p5_invitation"] + durs["v3_p5_invitation"] - 0.5
    title_end   = TOTAL - 0.1

    print(f"\nFinal: {final_audio} ({duration(final_audio):.2f}s)")
    print("\n  // Paste into index.html JS:")
    print("  const SCHEDULE = [")
    for c in schedule:
        print(f"      {{ idx: {c['idx']}, start: {c['start']:>6.2f}, end: {c['end']:>6.2f} }},")
    print("  ];")
    print(f"  // Title-card overlay: {title_start:.2f} – {title_end:.2f}")

    with open(f"{ASSETS}/cues_v4.json", "w") as f:
        json.dump({
            "duration": TOTAL,
            "title_card": {"start": round(title_start, 2), "end": round(title_end, 2)},
            "phrases": schedule,
        }, f, indent=2)

if __name__ == "__main__":
    main()
