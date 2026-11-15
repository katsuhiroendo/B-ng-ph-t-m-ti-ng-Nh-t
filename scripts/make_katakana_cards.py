#!/usr/bin/env python3
"""Make katakana versions of the cross-section cards (illus/x -> illus/xk).

The kana in the cards is set in Noto Sans CJK JP Regular. For each card the
script finds the hiragana, fits the font size and position that reproduce it,
whites it out, and draws the katakana at the same size and baseline.
The drawing and the IPA label are left untouched.

Usage: python3 scripts/make_katakana_cards.py [--font /path/NotoSansCJK-Regular.ttc]
"""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, DST = os.path.join(ROOT, "illus", "x"), os.path.join(ROOT, "illus", "xk")
KANA = {"a": "あ", "i": "い", "u": "う", "e": "え", "o": "お", "ka": "か", "ki": "き", "ku": "く", "ke": "け", "ko": "こ", "ga": "が", "gi": "ぎ", "gu": "ぐ", "ge": "げ", "go": "ご", "ga_nasal": "が", "gi_nasal": "ぎ", "gu_nasal": "ぐ", "ge_nasal": "げ", "go_nasal": "ご", "sa": "さ", "shi": "し", "su": "す", "se": "せ", "so": "そ", "za": "ざ", "ji": "じ", "zu": "ず", "ze": "ぜ", "zo": "ぞ", "ta": "た", "chi": "ち", "tsu": "つ", "te": "て", "to": "と", "da": "だ", "di": "ぢ", "du": "づ", "de": "で", "do": "ど", "na": "な", "ni": "に", "nu": "ぬ", "ne": "ね", "no": "の", "ha": "は", "hi": "ひ", "fu": "ふ", "he": "へ", "ho": "ほ", "pa": "ぱ", "pi": "ぴ", "pu": "ぷ", "pe": "ぺ", "po": "ぽ", "ba": "ば", "bi": "び", "bu": "ぶ", "be": "べ", "bo": "ぼ", "ma": "ま", "mi": "み", "mu": "む", "me": "め", "mo": "も", "ya": "や", "yu": "ゆ", "yo": "よ", "ra": "ら", "ri": "り", "ru": "る", "re": "れ", "ro": "ろ", "wa": "わ", "wo": "を", "n": "ん"}
FONT = sys.argv[sys.argv.index("--font") + 1] if "--font" in sys.argv else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
kata = lambda t: "".join(chr(ord(c) + 0x60) if 0x3041 <= ord(c) <= 0x3096 else c for c in t)

def kana_box(img):
    """Bounding box of the kana: dark pixels in the left half above the last row cluster (the IPA label)."""
    a = np.array(img.convert("L")) < 128
    left = a[:, : int(a.shape[1] * 0.52)]
    rows = np.where(left.any(1))[0]
    gap = int(a.shape[0] * 0.03)
    starts = [rows[0]] + [rows[i + 1] for i in range(len(rows) - 1) if rows[i + 1] - rows[i] > gap]
    ipa_top = starts[-1]
    kr = rows[rows < ipa_top - gap // 2]
    top, bottom = kr[0], kr[-1]
    cols = np.where(left[top:bottom + 1].any(0))[0]
    return cols[0], top, cols[-1], bottom

_ink_cache = {}
def ink_box(ch, size):
    """Real ink bounds of a glyph drawn at origin (0, 0). (PIL's getbbox reports the full advance width for CJK.)"""
    key = (ch, size)
    if key not in _ink_cache:
        f = ImageFont.truetype(FONT, size)
        c = Image.new("L", (size * 2, size * 2), 255)
        ImageDraw.Draw(c).text((size // 2, size // 2), ch, font=f, fill=0)
        a = np.array(c) < 128
        ys, xs = np.where(a)
        _ink_cache[key] = (xs.min() - size // 2, ys.min() - size // 2, xs.max() - size // 2, ys.max() - size // 2)
    return _ink_cache[key]

def size_for(ch, box):
    """Font size whose ink height best matches the box height."""
    h = box[3] - box[1]
    lo, hi = 60, 700
    while hi - lo > 1:
        mid = (lo + hi) // 2
        ib = ink_box(ch, mid)
        lo, hi = (mid, hi) if ib[3] - ib[1] < h else (lo, mid)
    return min((lo, hi), key=lambda s: abs((lambda ib: ib[3] - ib[1])(ink_box(ch, s)) - h))

def place(ch, box, size):
    """Draw origin that puts the ink of glyph ch (at this size) exactly on box."""
    ib = ink_box(ch, size)
    return ImageFont.truetype(FONT, size), (box[0] - ib[0], box[1] - ib[1])

def main():
    os.makedirs(DST, exist_ok=True)
    cards = []
    for path in sorted(glob.glob(os.path.join(SRC, "*.webp"))):
        name = os.path.basename(path)
        hira = KANA.get(name.rsplit("_", 1)[0])
        if not hira:
            print("skip (unknown kana):", name); continue
        img = Image.open(path).convert("RGB")
        cards.append((name, hira, img, kana_box(img)))
    # all cards are typeset at one size: take the median of the per-card estimates
    sizes = [size_for(h, b) for _, h, _, b in cards]
    size = int(np.median(sizes))
    off = [ (n, s) for (n, *_), s in zip(cards, sizes) if abs(s - size) > size * 0.06 ]
    for name, hira, img, box in cards:
        f, origin = place(hira, box, size)
        out = img.copy()
        d = ImageDraw.Draw(out)
        pad = int(img.width * 0.012)
        d.rectangle([box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad // 2], fill="white")
        d.text(origin, kata(hira), font=f, fill="black")
        out.save(os.path.join(DST, name), "WEBP", quality=85, method=6)
    print(f"{len(cards)} cards -> {DST}; font size {size} (per-card estimates {min(sizes)}-{max(sizes)})")
    if off: print("estimates more than 6% off the common size:", off)

if __name__ == "__main__":
    main()
