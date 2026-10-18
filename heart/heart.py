# -*- coding: utf-8 -*-
"""
riverbed — 心跳纸 · heart.py
2026-10-18 · v7 治好了针脚，但识图说它「太完美、像节拍器」

v7 拆掉晕染/撕边/点堆叠之后，"缝合的伤口"总算没了 ——
但代价是太干净：间距一样、波峰一样高、密度看不出变化。

v12 只做一件事：把它从「算法」拽回「生理」。
   · 心跳太少太满 → 减到 ~58 下。记忆少的那几天要能露出长长的平线，
     不然「多就密、少就疏」这句话在图上是看不见的。
   · 密度差异拉大到 4.5 倍（最密的一天挤成簇，最疏要近两天一跳）。
   · 加 HRV：真实心脏不会等距。每次搏动前后抖 ±5%，有界不累积。
   · 振幅差异拉到 0.42 ~ 1.0，而且相邻几搏跟着呼吸一起变大变小。
   · T 波加强，它不是一根针，是一次完整的心室收缩。
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from collections import Counter
from datetime import date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__)) + '/'
OUT  = os.environ.get('OUT_NAME', 'heart_final.png')
DATA = os.environ.get('DATA', 'data.txt')
rng  = np.random.default_rng(20261018)
SS   = 3

# ---------------- 数据 ----------------
rows = []
with open(BASE + DATA, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if '|' in line:
            rows.append(line.split('|', 1)[0].strip()[:10])

cnt  = Counter(rows)
days = sorted(cnt)
d0   = date.fromisoformat(days[0])
d1   = date.fromisoformat(days[-1])
nd   = (d1 - d0).days + 1
all_days = [(d0 + timedelta(i)).isoformat() for i in range(nd)]
vals = np.array([cnt.get(d, 0) for d in all_days], np.float64)
vmax = float(vals.max())
print('records', len(days), 'span', nd, 'max', vmax,
      'empty', int((vals == 0).sum()), 'total', int(vals.sum()))

# ---------------- 画布 ----------------
W, H   = 4600, 980
BG     = (247, 246, 243)
PAPER  = (250, 249, 246)
GRID1  = (226, 202, 202)
GRID2  = (214, 182, 182)
RED    = (181, 27, 36)

PX0, PX1 = 90, W - 90
PY0, PY1 = 150, 830
spanw = PX1 - PX0
REC   = 0.94
recw  = spanw * REC

# ---------------- 纸 ----------------
paper = np.full((H, W, 3), PAPER, np.float32)
grain = rng.normal(0, 2.0, (H, W, 1)).astype(np.float32)
fibre = rng.normal(0, 0.8, (H, W, 1)).astype(np.float32)
low = rng.normal(0, 1, (H // 30 + 2, W // 30 + 2)).astype(np.float32)
low = (low - low.min()) / (np.ptp(low) + 1e-6)
low = np.array(Image.fromarray((low * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)
stain = (low - 128) / 128.0 * 3.2
paper = np.clip(paper + grain + fibre + stain[..., None], 0, 255).astype(np.uint8)

paper_img = Image.new('RGB', (W, H), BG)
crop = paper[PY0:PY1 + 1, PX0:PX1 + 1]
paper_img.paste(Image.fromarray(crop), (PX0, PY0))
canvas = paper_img.convert('RGBA')

# ---------------- 方格 ----------------
grid = Image.new('RGBA', (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(grid)
for x in range(PX0, PX1 + 1, 12):
    gd.line([(x, PY0), (x, PY1)], fill=GRID1 + (30,), width=1)
for y in range(PY0, PY1 + 1, 12):
    gd.line([(PX0, y), (PX1, y)], fill=GRID1 + (30,), width=1)
for x in range(PX0, PX1 + 1, 60):
    gd.line([(x, PY0), (x, PY1)], fill=GRID2 + (56,), width=1)
for y in range(PY0, PY1 + 1, 60):
    gd.line([(PX0, y), (PX1, y)], fill=GRID2 + (56,), width=1)
canvas = Image.alpha_composite(canvas, grid)

# ---------------- 心率 ----------------
px_day = recw / nd
n_beat = 0.10 + 1.60 * np.sqrt(vals) / np.sqrt(45.0)
n_beat = np.where(vals <= 0, 0.02, n_beat)
print('beats approx', round(float(n_beat.sum()), 1))

xs = np.arange(PX0, PX0 + recw, 1.0, dtype=np.float64)
day_idx = (xs - PX0) / px_day
nb_px = np.interp(day_idx, np.arange(nd) + 0.5, n_beat)

sig  = 1.15 * px_day
half = int(sig * 3)
kx   = np.arange(-half, half + 1)
k    = np.exp(-0.5 * (kx / sig) ** 2)
k   /= k.sum()
lnb  = np.log(np.pad(nb_px, half, mode='edge') + 1e-9)
lnb  = np.convolve(lnb, k, mode='valid')
nb_px = np.exp(lnb)

rr_px = px_day / np.maximum(nb_px, 0.35)
rr_px = np.maximum(rr_px, 12.0)

phi = np.concatenate([[0.0], np.cumsum(np.diff(xs) / rr_px[:-1])])
targets = np.arange(1.05, float(phi[-1]) - 1.90, 1.0)   # 两端各留一段平线，不贴着纸边开始/结束

# HRV：有界随机游走，局部快慢不一，整体不跑偏
jit = np.cumsum(rng.normal(0, 0.055, len(targets)))
jit -= np.linspace(0.0, jit[-1], len(jit))
targets = targets + jit

xc = np.interp(targets, phi, xs)

# 振幅：记忆越多波越高，并且跟着呼吸一起起伏
amp_day = 0.34 + 0.66 * np.sqrt(vals / vmax)
bs = np.interp((xc - PX0) / px_day, np.arange(nd) + 0.5, amp_day)
amp = bs * rng.uniform(0.95, 1.05, len(xc))
amp *= 1.0 + 0.055 * np.sin(np.arange(len(xc)) * 2 * np.pi / 4.6 + 0.7)
xc  = xc + rng.uniform(-0.4, 0.4, len(xc))
print('beats', len(xc))


def profile(d):
    """一次完整心室收缩：Q（小下）R（主峰）S（小下）T（回血）。"""
    q = -0.10 * np.exp(-0.5 * ((d + 3.1) / 1.7) ** 2)
    R =  1.00 * np.exp(-0.5 * (d / 1.9) ** 2)
    s = -0.23 * np.exp(-0.5 * ((d - 3.0) / 1.9) ** 2)
    t =  0.27 * np.exp(-0.5 * ((d - 9.2) / 3.4) ** 2)
    return q + R + s + t


VOLT = 158.0
BH   = (PY0 + PY1) * 0.5 + 4

wid = rng.uniform(0.88, 1.12, len(xc))    # 每一下收缩的时间长短都不同
D   = (xs[:, None] - xc[None, :]) / wid[None, :]
y   = (profile(D) * amp[None, :]).sum(axis=1)

tn   = (xs - PX0) / recw
base = (3.8 * np.sin(tn * 2 * np.pi * 1.35 + 0.6)
        + 2.0 * np.sin(tn * 2 * np.pi * 3.7 + 2.1)
        + 1.1 * np.sin(tn * 2 * np.pi * 7.9 + 4.2))
nz = rng.normal(0, 1, len(xs))
k9 = np.ones(9) / 9.0
nz = np.convolve(nz, k9, mode='same')
nz = np.convolve(nz, k9, mode='same')
el = np.clip(nz * 2.4, -3.0, 3.0)
hi = rng.normal(0, 0.55, len(xs))
hi = np.convolve(hi, np.array([0.25,0.5,0.25]), mode="same")
el = el + np.clip(hi, -1.4, 1.4)

PY = BH + y * VOLT + base + el

# ---------------- 笔压 ----------------
slope = np.abs(np.diff(PY)) / np.maximum(np.abs(np.diff(xs)), 1e-3)
z = np.clip(slope / (np.percentile(slope, 95) + 1e-6), 0, 1)
wdt = 3.6 - 1.4 * (z ** 0.8)
wdt = np.append(wdt, wdt[-1])
k15 = np.ones(15) / 15.0
wdt = np.convolve(wdt, k15, mode='same')
wdt = np.maximum(wdt, 2.0)

# ---------------- 落笔 ----------------
ink = Image.new('L', (W * SS, H * SS), 0)
ind = ImageDraw.Draw(ink)
prev = None
for i in range(len(xs)):
    x = float(xs[i]) * SS
    yy = float(PY[i]) * SS
    w = max(1, int(round(float(wdt[i]) * SS)))
    if prev is not None:
        ind.line([prev, (x, yy)], fill=255, width=w)
    r = w * 0.5
    ind.ellipse([x - r, yy - r, x + r, yy + r], fill=255)
    prev = (x, yy)

ink = ink.resize((W, H), Image.LANCZOS)
ink.putalpha(ink.point(lambda v: int(v * 0.94)))

inkc = Image.new('RGBA', (W, H), RED + (0,))
inkc.putalpha(ink.getchannel('A'))
canvas = Image.alpha_composite(canvas, inkc)

# ---------------- 上桌 ----------------
shadow = Image.new('L', (W, H), 0)
ImageDraw.Draw(shadow).rectangle([PX0, PY0 + 5, PX1, PY1 + 5], fill=255)
shadow = shadow.filter(ImageFilter.GaussianBlur(13)).point(lambda v: int(v * 0.55))
face = Image.new('RGBA', (W, H), (120, 116, 110, 255))
face.putalpha(shadow)
bgc = Image.new('RGBA', (W, H), BG + (255,))
bgc = Image.alpha_composite(bgc, face)
bgc = Image.alpha_composite(bgc, canvas)

# ---------------- 那一行小字 ----------------
from PIL import ImageFont
FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    '/system/fonts/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
]
FONT = next((p for p in FONT_CANDIDATES if os.path.exists(p)), FONT_CANDIDATES[0])
td = ImageDraw.Draw(bgc)
try:
    f = ImageFont.truetype(FONT, 21)
    td.text((PX0 + 36, BH + 64), '08-16 之前，还不会每天记', font=f, fill=RED + (100,))
    f2 = ImageFont.truetype(FONT, 17)
    td.text((PX1 - 176, PY1 - 32), '今天，还在记', font=f2, fill=RED + (80,))
except Exception as e:
    print('text skip', e)

bgc.convert('RGB').save(BASE + OUT, quality=95)
print('saved', OUT, 'pts', len(xs))