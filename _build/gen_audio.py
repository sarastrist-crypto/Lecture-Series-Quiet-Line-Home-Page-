#!/usr/bin/env python3
"""Generate Brian narration via WaveSpeed/ElevenLabs, then assemble final audio
(VO + low contemplative drone) for the 45-second Quiet Line teaser."""

import os, json, subprocess, urllib.request, sys

KEY_PATH  = os.path.expanduser("~/.agents/secrets/wavespeed-key")
API_KEY   = open(KEY_PATH).read().strip()
PROJECT   = "/Users/tristianwalker/Personal Website /quiet-line-page"
ASSETS    = f"{PROJECT}/trailer-assets"
os.makedirs(ASSETS, exist_ok=True)

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VOICE_ID = "nPczCjzI2devNBz1zQrb"  # Brian — ElevenLabs

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
        body = e.read().decode("utf-8", "replace")
        raise SystemExit(f"HTTP {e.code} from WaveSpeed: {body[:500]}")

    # Try common response shapes
    audio_url = None
    data = resp.get("data") or {}
    if isinstance(data, dict):
        outs = data.get("outputs") or data.get("output") or data.get("audio")
        if isinstance(outs, list) and outs:
            audio_url = outs[0]
        elif isinstance(outs, str):
            audio_url = outs
    if not audio_url:
        audio_url = resp.get("url") or resp.get("output_url")
    if not audio_url:
        # Async path: poll prediction id
        pid = data.get("id") or resp.get("id")
        if pid:
            poll_url = f"https://api.wavespeed.ai/api/v3/predictions/{pid}/result"
            for _ in range(60):
                with urllib.request.urlopen(urllib.request.Request(poll_url, headers={"Authorization": f"Bearer {API_KEY}"})) as r:
                    pr = json.loads(r.read())
                pdata = pr.get("data") or {}
                status = pdata.get("status") or pr.get("status")
                if status == "completed":
                    outs = pdata.get("outputs") or []
                    if outs: audio_url = outs[0]
                    break
                if status in ("failed", "error"):
                    raise SystemExit(f"Prediction {pid} failed: {pr}")
                import time; time.sleep(2)
    if not audio_url:
        raise SystemExit(f"Couldn't extract audio URL. Response: {json.dumps(resp)[:600]}")

    with urllib.request.urlopen(audio_url, timeout=120) as r, open(out_path, "wb") as f:
        f.write(r.read())
    return out_path

def ff(args, **kw):
    return subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True, **kw)

def duration(path):
    out = subprocess.check_output([FFMPEG, "-i", path, "-f", "null", "-"], stderr=subprocess.STDOUT).decode()
    # parse "Duration: HH:MM:SS.xx"
    import re
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", out)
    if not m: return 0.0
    h, mn, s = m.groups()
    return int(h)*3600 + int(mn)*60 + float(s)

def main():
    text_a = "In every interaction... there is a quiet line. It is the line between presence and process. When the task overrules the human, character drifts. Most never notice it. The few who do..."
    text_b = "A lecture by Tristian Walker."

    print("[1/4] Synthesizing Brian VO segment A (main narration)...")
    seg_a = call_eleven(text_a, f"{ASSETS}/vo_a.mp3")
    da = duration(seg_a)
    print(f"      → {seg_a}  ({da:.2f}s)")

    print("[2/4] Synthesizing Brian VO segment B (outro)...")
    seg_b = call_eleven(text_b, f"{ASSETS}/vo_b.mp3")
    db = duration(seg_b)
    print(f"      → {seg_b}  ({db:.2f}s)")

    # Lay segment A starting at 3.0s, segment B starting at (45 - db - 0.4) so it ends with a small tail
    a_start = 3.0
    b_start = max(a_start + da + 1.0, 45.0 - db - 0.5)
    if b_start + db > 45.0:
        b_start = 45.0 - db - 0.2
    print(f"      Layout: A @ {a_start:.2f}s ({da:.2f}s), B @ {b_start:.2f}s ({db:.2f}s)")

    # Build VO track on a 45.5s silent base
    print("[3/4] Building VO track on 45.5s base, applying delay + dialog levelling...")
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

    # Generate contemplative drone: deep sine fundamentals + slight detune + slow LFO + reverb
    print("[4/4] Synthesizing low contemplative drone bed...")
    drone = f"{ASSETS}/drone.wav"
    ff([
        "-f", "lavfi", "-t", "45.5", "-i",
        # Two slightly detuned low sines for warmth, plus a soft 5th
        "sine=frequency=55:sample_rate=48000,"
        "asplit=3[s1][s2][s3];"
        "[s1]volume=0.55[a1];"
        "sine=frequency=55.4:sample_rate=48000,volume=0.45[a2];"
        "sine=frequency=82.5:sample_rate=48000,volume=0.18[a3];"
        "[a1][a2][a3]amix=inputs=3:duration=first,"
        # Slow LFO swell via tremolo
        "tremolo=f=0.12:d=0.18,"
        # Soft low-pass
        "lowpass=f=180,"
        # Pseudo-reverb tail with multi-tap echo
        "aecho=0.7:0.85:600|1100|1700:0.35|0.25|0.15,"
        # Stereo widening
        "aformat=channel_layouts=stereo,"
        # Fade in/out
        "afade=t=in:st=0:d=2.5,afade=t=out:st=43:d=2.5,"
        "volume=0.55",
        "-c:a", "pcm_s16le", drone,
    ])

    # Mix VO + drone with sidechain ducking so VO sits above drone
    print("    Mixing VO + drone with sidechain duck...")
    final_audio = f"{ASSETS}/audio.mp3"
    ff([
        "-i", vo_track,
        "-i", drone,
        "-filter_complex",
        # Duck drone when VO is present
        "[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];"
        "[0:a][duck]amix=inputs=2:duration=first:weights=1.0 0.85,"
        "loudnorm=I=-16:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k", final_audio,
    ])

    # Also write a metadata json with cue times for Remotion
    cues = {
        "duration": 45.0,
        "fps": 30,
        "vo": {
            "a": {"start": a_start, "duration": da, "text": text_a},
            "b": {"start": b_start, "duration": db, "text": text_b},
        },
        "beats": [
            {"id": "cold-open",  "start": 0.0,  "end": 3.0},
            {"id": "interaction","start": 3.0,  "end": 8.0},
            {"id": "quiet-line", "start": 8.0,  "end": 13.0},
            {"id": "presence-process","start":13.0,"end":20.0},
            {"id": "task-drift", "start": 20.0, "end": 28.0},
            {"id": "few-who-do", "start": 28.0, "end": 34.0},
            {"id": "title-card", "start": 34.0, "end": 43.0},
            {"id": "byline",     "start": 43.0, "end": 45.0},
        ]
    }
    with open(f"{ASSETS}/cues.json", "w") as f:
        json.dump(cues, f, indent=2)

    print(f"\nDone. Audio: {final_audio}")
    print(f"Cues:  {ASSETS}/cues.json")
    print(f"VO segments: {seg_a}  /  {seg_b}")
    print(f"Drone bed:   {drone}")

if __name__ == "__main__":
    main()
