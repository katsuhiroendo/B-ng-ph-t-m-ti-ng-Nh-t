#!/usr/bin/env python3
"""Turn raw recordings from record.html into audio/<id>.mp3 and audio/manifest.json.

Usage:
    python3 scripts/process_audio.py kana-recordings.zip      # or a folder of files

For each recording: high-pass at 80 Hz, trim leading/trailing silence,
match loudness (mean -20 dB, peak capped at -1 dBFS), 10 ms fades,
encode mono 44.1 kHz 64 kbps MP3. Existing mp3s are overwritten only for
ids present in the input, so partial re-recordings can be merged in.
"""
import json, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO = ROOT / "audio"
LIST = json.loads((AUDIO / "list.json").read_text(encoding="utf-8"))
KNOWN = {i["id"] for i in LIST}
EXTS = {".webm", ".m4a", ".mp4", ".ogg", ".wav", ".mp3", ".aac"}

TRIM = ("highpass=f=80,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06,"
        "areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.10,"
        "areverse")

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
    trimmed = Path(tmpdir) / (out.stem + ".wav")
    r = run(["ffmpeg", "-y", "-hide_banner", "-i", str(src), "-ac", "1", "-ar", "44100", "-af", TRIM, str(trimmed)])
    if r.returncode != 0:
        return f"変換失敗: {r.stderr.strip().splitlines()[-1] if r.stderr else ''}"
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
    if peak > -0.3: warn.append("音割れの可能性")
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
