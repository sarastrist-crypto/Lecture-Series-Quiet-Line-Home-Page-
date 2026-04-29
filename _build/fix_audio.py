#!/usr/bin/env python3
"""Re-run only drone + mix steps using already-generated vo_a.mp3 / vo_b.mp3."""
import os, json, subprocess, re, imageio_ffmpeg

FFMPEG  = imageio_ffmpeg.get_ffmpeg_exe()
PROJECT = "/Users/tristianwalker/Personal Website /quiet-line-page"
ASSETS  = f"{PROJECT}/trailer-assets"

def ff(args):
    return subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True)

def duration(path):
    out = subprocess.check_output([FFMPEG, "-i", path, "-f", "null", "-"], stderr=subprocess.STDOUT).decode()
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", out)
    if not m: return 0.0
    h, mn, s = m.groups()
    return int(h)*3600 + int(mn)*60 + float(s)

seg_a = f"{ASSETS}/vo_a.mp3"
seg_b = f"{ASSETS}/vo_b.mp3"
da = duration(seg_a)
db = duration(seg_b)

a_start = 3.0
b_start = 45.0 - db - 0.4  # outro tucked at the end with ~0.4s tail
print(f"VO layout: A @ {a_start:.2f}s ({da:.2f}s), B @ {b_start:.2f}s ({db:.2f}s)")

# 1) VO track on a 45.5s silent base, with delays + dialog levelling
print("[1/3] VO track...")
vo_track = f"{ASSETS}/vo_track.wav"
ff([
    "-f", "lavfi", "-t", "45.5", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
    "-i", seg_a,
    "-i", seg_b,
    "-filter_complex",
    f"[1:a]adelay={int(a_start*1000)}|{int(a_start*1000)},aformat=channel_layouts=stereo,volume=1.05[a];"
    f"[2:a]adelay={int(b_start*1000)}|{int(b_start*1000)},aformat=channel_layouts=stereo,volume=1.0[b];"
    f"[0:a][a][b]amix=inputs=3:duration=first:dropout_transition=0,"
    f"acompressor=threshold=-18dB:ratio=3:attack=10:release=200,"
    f"loudnorm=I=-18:LRA=11:TP=-2[out]",
    "-map", "[out]", "-c:a", "pcm_s16le", vo_track,
])

# 2) Contemplative drone — multiple lavfi sine inputs mixed via filter_complex
print("[2/3] Drone bed...")
drone = f"{ASSETS}/drone.wav"
ff([
    "-f", "lavfi", "-t", "45.5", "-i", "sine=frequency=55:sample_rate=48000",
    "-f", "lavfi", "-t", "45.5", "-i", "sine=frequency=55.4:sample_rate=48000",
    "-f", "lavfi", "-t", "45.5", "-i", "sine=frequency=82.5:sample_rate=48000",
    "-filter_complex",
    "[0:a]volume=0.55[a1];"
    "[1:a]volume=0.45[a2];"
    "[2:a]volume=0.18[a3];"
    "[a1][a2][a3]amix=inputs=3:duration=first,"
    "tremolo=f=0.12:d=0.18,"
    "lowpass=f=180,"
    "aecho=0.7:0.85:600|1100|1700:0.35|0.25|0.15,"
    "aformat=channel_layouts=stereo,"
    "afade=t=in:st=0:d=2.5,"
    "afade=t=out:st=43:d=2.5,"
    "volume=0.55[out]",
    "-map", "[out]", "-c:a", "pcm_s16le", drone,
])

# 3) Final mix with sidechain duck
print("[3/3] Final mix...")
final_audio = f"{ASSETS}/audio.mp3"
ff([
    "-i", vo_track,
    "-i", drone,
    "-filter_complex",
    "[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];"
    "[0:a][duck]amix=inputs=2:duration=first:weights=1.0 0.85,"
    "loudnorm=I=-16:LRA=11:TP=-1.5",
    "-c:a", "libmp3lame", "-b:a", "192k", final_audio,
])

cues = {
    "duration": 45.0, "fps": 30,
    "vo": {
        "a": {"start": a_start, "duration": da},
        "b": {"start": b_start, "duration": db},
    },
    "beats": [
        {"id":"cold-open",  "start":0.0,  "end":3.0},
        {"id":"interaction","start":3.0,  "end":8.0},
        {"id":"quiet-line", "start":8.0,  "end":13.0},
        {"id":"presence-process","start":13.0,"end":20.0},
        {"id":"task-drift", "start":20.0, "end":28.0},
        {"id":"few-who-do", "start":28.0, "end":34.0},
        {"id":"title-card", "start":34.0, "end":43.0},
        {"id":"byline",     "start":43.0, "end":45.0},
    ],
}
with open(f"{ASSETS}/cues.json", "w") as f:
    json.dump(cues, f, indent=2)

print(f"\nDone. Audio: {final_audio} ({duration(final_audio):.2f}s)")
