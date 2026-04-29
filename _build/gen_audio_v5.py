#!/usr/bin/env python3
"""V5: same script + same v4 layout, but each phrase is pre-cleaned
(silence-trimmed + fades) before adelay/mix to eliminate the audible
'scratch' between phrases. Also softened the sidechain compressor
so the drone duck no longer pumps audibly.

Pipeline per phrase:
  ElevenLabs MP3 → decode to WAV → silence-trim head/tail → 25ms
  fade-in + 50ms fade-out → use as adelay input

This guarantees:
- No click at the leading edge of a phrase (encoder DC offset / silence)
- No abrupt cutoff at the tail (clean fade to zero)
- Identical layout/timings to v4 so the JS schedule still matches"""

import os, json, subprocess, re, sys
import imageio_ffmpeg

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
    "v3_p3_few_who_do":    0.28,
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

def clean_phrase(src_mp3, out_wav):
    """Decode MP3 → WAV, trim leading/trailing silence (~-45dB), fade in 25ms / out 60ms."""
    # Step 1: decode + silence-remove (head and tail)
    tmp = out_wav + ".tmp.wav"
    ff([
        "-i", src_mp3,
        "-af",
        # Strip head silence
        "silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:detection=peak,"
        # Strip tail silence (uses areverse trick)
        "areverse,silenceremove=start_periods=1:start_duration=0.05:start_threshold=-45dB:detection=peak,areverse,"
        # Convert to consistent sample rate / channels
        "aformat=sample_rates=48000:channel_layouts=stereo",
        "-c:a", "pcm_s16le", tmp,
    ])
    d = duration(tmp)
    fade_out_start = max(0, d - 0.06)
    # Step 2: apply fades on the trimmed file
    ff([
        "-i", tmp,
        "-af",
        f"afade=t=in:st=0:d=0.025,afade=t=out:st={fade_out_start:.3f}:d=0.06",
        "-c:a", "pcm_s16le", out_wav,
    ])
    os.remove(tmp)
    return duration(out_wav)

def main():
    paths_in, durs_clean, paths_clean = {}, {}, {}
    print("[1] Pre-clean phrase MP3s → WAV (silence-trim + fades)…")
    for key, _ in PHRASES:
        src = f"{ASSETS}/{key}.mp3"
        if not os.path.exists(src):
            sys.exit(f"Missing phrase {src}; run gen_audio_v3.py first.")
        clean = f"{ASSETS}/{key}.clean.wav"
        d = clean_phrase(src, clean)
        paths_in[key]    = src
        paths_clean[key] = clean
        durs_clean[key]  = d
        print(f"    {key}: {duration(src):.2f}s → {d:.2f}s  (clean WAV)")

    starts = {}
    t = INTRO
    for key, _ in PHRASES:
        starts[key] = t
        t = t + durs_clean[key] + PAUSE_AFTER[key]
    TOTAL = round(t + OUTRO_TAIL, 2)

    print(f"\n[2] Layout (total {TOTAL}s):")
    for key, _ in PHRASES:
        print(f"    {key}: start={starts[key]:.2f}s end={starts[key]+durs_clean[key]:.2f}s gap_after={PAUSE_AFTER[key]:.2f}s")

    # VO track from cleaned WAVs
    print("\n[3] Assemble VO track (no MP3 boundary artifacts)…")
    vo_track = f"{ASSETS}/vo_track_v5.wav"
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
        # Gentler levelling — was acompressor 3:1, now 2:1 with slower release
        "acompressor=threshold=-20dB:ratio=2:attack=15:release=300,"
        "loudnorm=I=-18:LRA=11:TP=-2[out]"
    )
    ff([*inputs, "-filter_complex", ";".join(parts),
        "-map", "[out]", "-c:a", "pcm_s16le", vo_track])

    # Drone bed (unchanged from v4)
    print("[4] Drone bed…")
    drone = f"{ASSETS}/drone_v5.wav"
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
        "volume=0.42[out]",   # slightly quieter so duck pumps less
        "-map", "[out]", "-c:a", "pcm_s16le", drone,
    ])

    # Final mix with softer sidechain
    print("[5] Final mix (softer duck: ratio 4 not 8, longer release)…")
    final_audio = f"{ASSETS}/audio_v5.mp3"
    ff([
        "-i", vo_track, "-i", drone,
        "-filter_complex",
        # Softer compression on the drone when VO is present
        "[1:a][0:a]sidechaincompress=threshold=0.06:ratio=4:attack=30:release=600[duck];"
        "[0:a][duck]amix=inputs=2:duration=first:weights=1.0 0.85,"
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k", final_audio,
    ])

    # Caption schedule
    OB, OA = 0.15, 0.20
    schedule = []
    for i, (key, _) in enumerate(PHRASES):
        s = max(0, starts[key] - OB)
        e = starts[key] + durs_clean[key] + OA
        schedule.append({"idx": i, "start": round(s, 2), "end": round(e, 2)})
    title_start = starts["v3_p5_invitation"] + durs_clean["v3_p5_invitation"] - 0.5
    title_end   = TOTAL - 0.1

    print(f"\nFinal: {final_audio} ({duration(final_audio):.2f}s)")
    print("\n  // Paste into index.html JS:")
    print("  const SCHEDULE = [")
    for c in schedule:
        print(f"      {{ idx: {c['idx']}, start: {c['start']:>6.2f}, end: {c['end']:>6.2f} }},")
    print("  ];")

    with open(f"{ASSETS}/cues_v5.json", "w") as f:
        json.dump({
            "duration": TOTAL,
            "title_card": {"start": round(title_start, 2), "end": round(title_end, 2)},
            "phrases": schedule,
        }, f, indent=2)

if __name__ == "__main__":
    main()
