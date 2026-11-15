#!/usr/bin/env python3
"""Make katakana versions of the front (mouth-shape) cards: illus/<v>.webp -> illus/k/<v>.webp.

The kana on these cards is a heavy rounded gothic; the closest available font is
M PLUS Rounded 1c ExtraBold (800). Get it as TTF, e.g.:
    npm pack @fontsource/m-plus-rounded-1c@5.1.0  (woff2 -> ttf with fontTools)
The script erases the hiragana up to the lips, then draws the katakana in the
card's own blue, centred where the hiragana was and shrunk only if it would
touch the lips or the IPA label.

Usage: python3 scripts/make_katakana_front_cards.py path/to/m-plus-rounded-1c-800.ttf
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
def blue_mask(img):
    a=np.array(img).astype(int);return (a[:,:,2]>70)&(a[:,:,0]<70)&(a[:,:,1]<100)&(a[:,:,2]-a[:,:,0]>40)
def kana_box(img):
    m=blue_mask(img);H,W=m.shape
    reg=m[int(H*.05):int(H*.95),int(W*.02):lips_left(img)-3]
    rows=np.where(reg.any(1))[0];gap=int(H*.03)
    starts=[rows[0]]+[rows[i+1] for i in range(len(rows)-1) if rows[i+1]-rows[i]>gap]
    kr=rows[rows<starts[-1]-gap//2];t,b=kr[0],kr[-1]
    cols=np.where(reg[t:b+1].any(0))[0]
    return cols[0]+int(W*.02),t+int(H*.05),cols[-1]+int(W*.02),b+int(H*.05)
def ink(font,ch,size):
    f=ImageFont.truetype(font,size);c=Image.new("L",(size*2,size*2),255);ImageDraw.Draw(c).text((size//2,size//2),ch,font=f,fill=0)
    a=np.array(c)<128;ys,xs=np.where(a);return f,(xs.min()-size//2,ys.min()-size//2,xs.max()-size//2,ys.max()-size//2)

def lips_left(img):
    a=np.array(img).astype(int);H,W=a.shape[:2]
    m=(a[:,:,0]>170)&(a[:,:,1]<160)&(a[:,:,2]<160)&(a[:,:,0]-a[:,:,1]>40)
    xs=np.where(m[int(H*.15):int(H*.85)].any(0))[0];return xs.min()
def ipa_top(img):
    m=blue_mask(img);H,W=m.shape;reg=m[int(H*.05):int(H*.95),int(W*.02):lips_left(img)-3]
    rows=np.where(reg.any(1))[0];gap=int(H*.03)
    return [rows[0]]+[rows[i+1] for i in range(len(rows)-1) if rows[i+1]-rows[i]>gap]
def make2(font,v,hira,kata):
    img=Image.open(R+v+".webp").convert("RGB");l,t,r,b=kana_box(img);H,W=img.size[1],img.size[0]
    bm=blue_mask(img);color=tuple(int(x) for x in np.median(np.array(img)[bm],axis=0))
    bg=tuple(int(x) for x in np.median(np.array(img)[t:b, max(0,l-30):l-10].reshape(-1,3),axis=0))
    starts=ipa_top(img);itop=starts[-1]+int(H*.05)
    area=(int(W*.025), t-10, lips_left(img)-int(W*.012), itop-int(H*.025))   # where the katakana may go
    size=min(range(100,600,2),key=lambda s:abs((lambda ib:ib[3]-ib[1])(ink(font,hira,s)[1])-(b-t)))
    f,ib=ink(font,kata,size)
    kw,kh=ib[2]-ib[0],ib[3]-ib[1];aw,ah=area[2]-area[0],area[3]-area[1]
    if kw>aw or kh>ah:                          # shrink only when it does not fit
        size=int(size*min(aw/kw,ah/kh));f,ib=ink(font,kata,size);kw,kh=ib[2]-ib[0],ib[3]-ib[1]
    cx,cy=(l+r)/2,(t+b)/2                       # same centre as the hiragana, kept inside the area
    x0=min(max(cx-kw/2,area[0]),area[2]-kw);y0=min(max(cy-kh/2,area[1]),area[3]-kh)
    out=img.copy();d=ImageDraw.Draw(out)
    d.rectangle([l-12,t-12,lips_left(img)-3,b+12],fill=bg)   # clear everything up to the lips
    d.text((x0-ib[0],y0-ib[1]),kata,font=f,fill=color)
    return out,size

R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "illus") + os.sep

if __name__ == "__main__":
    font = sys.argv[1]
    os.makedirs(R + "k", exist_ok=True)
    for v, h, k in zip("aiueon", "あいうえおん", "アイウエオン"):
        out, size = make2(font, v, h, k)
        out.save(R + "k/" + v + ".webp", "WEBP", quality=88, method=6)
        print(v, k, "size", size)
