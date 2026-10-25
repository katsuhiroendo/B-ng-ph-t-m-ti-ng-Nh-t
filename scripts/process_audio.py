#!/usr/bin/env python3
"""Turn raw recordings from record.html into audio/<id>.mp3 and audio/manifest.json.

Usage:
    python3 scripts/process_audio.py kana-recordings.zip      # or a folder of files

For each recording: high-pass at 80 Hz, trim leading/trailing silence
(short clicks such as the record button are ignored),
match loudness (mean -20 dB, peak capped at -1 dBFS), 10 ms fades,
encode mono 44.1 kHz 64 kbps MP3. Existing mp3s are overwritten only for
ids present in the input, so partial re-recordings can be merged in.
"""
import array, json, math, re, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "audio"
LIST = json.loads((AUDIO / "list.json").read_text(encoding="utf-8"))
KNOWN = {i["id"] for i in LIST}
EXTS = {".webm", ".m4a", ".mp4", ".ogg", ".wav", ".mp3", ".aac"}

HPF = "highpass=f=80"

def speech_bounds(wav):
    """Return (start, end) seconds of the speech, ignoring clicks/blips shorter than 60 ms."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True)
    a = array.array("h", r.stdout)
    hop, win = 160, 400  # 10 ms hop, 25 ms window
    env = []
    for k in range(0, max(0, len(a) - win), hop):
        seg = a[k:k + win]
        rms = math.sqrt(sum(v * v for v in seg) / win) / 32768
        env.append(20 * math.log10(rms + 1e-9))
    if not env:
        return None
    thr = max(env) - 32
    segs, start = [], None
    for i, e in enumerate(env + [-999]):
        if e > thr and start is None: start = i
        if e <= thr and start is not None:
            segs.append([start, i]); start = None
    merged = []
    for sg in segs:  # join pieces closer than 120 ms (e.g. っ, word gaps)
        if merged and sg[0] - merged[-1][1] <= 12: merged[-1][1] = sg[1]
        else: merged.append(sg)
    keep = [m for m in merged if m[1] - m[0] >= 6]
    # drop an isolated short burst (<120 ms, >200 ms away from the voice) at either end
    while len(keep) > 1 and keep[0][1] - keep[0][0] < 12 and keep[1][0] - keep[0][1] > 20: keep.pop(0)
    while len(keep) > 1 and keep[-1][1] - keep[-1][0] < 12 and keep[-1][0] - keep[-2][1] > 20: keep.pop()
    if not keep:
        return None
    return max(0.0, keep[0][0] * 0.01 - 0.04), keep[-1][1] * 0.01 + 0.025 + 0.08

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def measure(path):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", r.stderr)
    peak = re.search(r"max_volume: (-?[\d.]+) dB", r.stderr)
    dur = re.search(r"time=(\d+):(\d+):([\d.]+)", r.stderr)
    secs = 0.0
    if dur:
        h, m, s = dur.groups(); secs = int(h) * 3600 + int(m) * 60 + float(s)
    return (float(mean.group(1)) if mean else None, float(peak.group(1)) if peak else None, secs)

def process(src, out, tmpdir):
    full = Path(tmpdir) / (out.stem + "_full.wav")
    trimmed = Path(tmpdir) / (out.stem + ".wav")
    r = run(["ffmpeg", "-y", "-hide_banner", "-i", str(src), "-ac", "1", "-ar", "44100", "-af", HPF, str(full)])
    if r.returncode != 0:
        return f"変換失敗: {r.stderr.strip().splitlines()[-1] if r.stderr else ''}"
    b = speech_bounds(full)
    if not b:
        return "無音または短すぎ（録音し直し）"
    run(["ffmpeg", "-y", "-hide_banner", "-i", str(full), "-af", f"atrim={b[0]:.3f}:{b[1]:.3f},asetpts=N/SR/TB", str(trimmed)])
    mean, peak, dur = measure(trimmed)
    if mean is None or dur < 0.12:
        return "無音または短すぎ（録音し直し）"
    gain = min(-20.0 - mean, -1.0 - peak)
    fade_out = max(0.0, dur - 0.01)
    af = f"volume={gain:.2f}dB,afade=t=in:d=0.01,afade=t=out:st={fade_out:.3f}:d=0.01,apad=pad_dur=0.04"
    r = run(["ffmpeg", "-y", "-hide_banner", "-i", str(trimmed), "-af", af,
             "-codec:a", "libmp3lame", "-b:a", "64k", "-ac", "1", "-ar", "44100", str(out)])
    if r.returncode != 0:
        return "mp3化失敗"
    warn = []
    if peak > -0.1: warn.append("音割れの可能性")
    if mean < -38: warn.append("録音レベルが低い")
    if dur > 3.5: warn.append(f"長すぎ {dur:.1f}秒")
    return "; ".join(warn) or None

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    AUDIO.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        if src.suffix == ".zip":
            folder = Path(tmp) / "in"
            with zipfile.ZipFile(src) as z: z.extractall(folder)
        else:
            folder = src
        files = [p for p in folder.rglob("*") if p.suffix.lower() in EXTS and not p.name.startswith(".")]
        done, problems, unknown = 0, [], []
        for f in sorted(files):
            if f.stem not in KNOWN:
                unknown.append(f.name); continue
            msg = process(f, AUDIO / f"{f.stem}.mp3", tmp)
            if msg and ("失敗" in msg or "録音し直し" in msg):
                problems.append(f"{f.stem}: {msg}")
                (AUDIO / f"{f.stem}.mp3").unlink(missing_ok=True)
                continue
            done += 1
            if msg: problems.append(f"{f.stem}: {msg}")
    have = sorted(p.stem for p in AUDIO.glob("*.mp3") if p.stem in KNOWN)
    (AUDIO / "manifest.json").write_text(json.dumps({"files": have}, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    missing = [f'{i["id"]}（{i["text"]}）' for i in LIST if i["id"] not in have]
    print(f"処理: {done} 件 / 公開中の録音: {len(have)} / {len(LIST)}")
    if problems: print("要確認:\n  " + "\n  ".join(problems))
    if unknown: print("対象外のファイル: " + ", ".join(unknown))
    if missing: print(f"未録音 {len(missing)} 件: " + "、".join(missing[:40]) + (" …" if len(missing) > 40 else ""))

if __name__ == "__main__":
    main()
