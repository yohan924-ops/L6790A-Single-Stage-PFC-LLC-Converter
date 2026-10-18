# -*- coding: utf-8 -*-
"""How the LG 26OP-LM83W flat transformer is built - drawn from its approval
sheet (KH Feelux, 2025-05-26):
  p.17  core EE6405: A 64, B 2.30, C 33.5, D 8.0, E 56, F 0.70, B-F 1.60;
        A_e 113.1 mm2, l_e 57.13, V_e 6461 (one pair)
  p.18  bobbin: slot 8.50, inner wall 14.50, 29.10, 35.10, 48.90, 54.90, 60.00;
        68.00 straight, 82.50 / 97.10 / 103.10 overall; 1.30 thick in the
        straight part, 4.10 at the ends
  p.5   outline: core region 66.9 mm long (measured with the drawing's own
        143.9 mm dimension), a joint line exactly in the middle in both views,
        one tape band centred on each half
  p.6   windings: NP1 5 T Litz 0.04 x 360, NS2 / NS3 1 T copper plate 0.5 x 4.5
  p.11  internal construction: NP1 next to the centre leg, a bobbin wall, the
        two secondary plates stacked outside it; TOP GAP (gap in the top core)
Not in the sheet, so not dimensioned here: the gap length, the Litz outside
diameter, the end shape of the secondary plates.
"""
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Ellipse, PathPatch, FancyArrowPatch
from matplotlib.path import Path
import numpy as np

plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
plt.rcParams['axes.unicode_minus'] = False

# ---------------------------------------------------------------- geometry (mm)
A, B, C, D, E, F = 64.0, 2.30, 33.5, 8.0, 56.0, 0.70
T = B - F                      # plate (yoke) 1.60
OL = (A - E) / 2               # outer leg 4.0
WIN = (E - D) / 2              # window width 24.0
CX = A / 2                     # centre line
GAP_DRAW = 0.18                # drawn only to show where it is - the length is not in the sheet
# bobbin (p.18), measured from the centre line
R_SLOT, R_IN, R_CH, R_WALL, R_RAIL, R_FR = 4.25, 7.25, 14.55, 17.55, 24.45, 27.45
STRAIGHT = 68.0                # y from -0.5 to 67.5
Y0S, Y1S = -0.5, 67.5
END = 17.55                    # (103.1 - 68) / 2
BOB_T, END_T = 1.30, 4.10
TAPE_W = 21.5                  # p.6 core fixing tape 0.025 x 21.5

COL_CORE_TOP, COL_CORE_FRONT, COL_CORE_SIDE = '#9aa3ad', '#6f7882', '#59616a'
COL_CORE2_TOP, COL_CORE2_FRONT, COL_CORE2_SIDE = '#b9b0a0', '#8f8676', '#757060'
COL_BOB_TOP, COL_BOB_FRONT, COL_BOB_SIDE = '#e9e4cf', '#cfc8ad', '#bdb593'
COL_CU_TOP, COL_CU_FRONT, COL_CU_SIDE = '#e8954a', '#c9732c', '#b06424'
COL_SEC_TOP, COL_SEC_FRONT, COL_SEC_SIDE = '#c46a2b', '#9c5020', '#86441a'
INK = '#1f2a36'
RED = '#c0392b'


# ---------------------------------------------------------------- oblique 3D
class Oblique:
    def __init__(self, ax, zs=3.0, k=0.55, ang=32.0):
        self.ax, self.zs, self.k = ax, zs, k
        self.c, self.s = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def p(self, x, y, z):
        return (x + self.k * y * self.c, self.zs * z + self.k * y * self.s)

    def poly(self, pts, fc, ec=INK, lw=0.6, z=1, alpha=1.0):
        self.ax.add_patch(Polygon([self.p(*q) for q in pts], closed=True, fc=fc,
                                  ec=ec, lw=lw, zorder=z, alpha=alpha))

    def box(self, x0, x1, y0, y1, z0, z1, cols, z=1, lw=0.6):
        top, front, side = cols
        self.poly([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], front, z=z, lw=lw)
        self.poly([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], side, z=z, lw=lw)
        self.poly([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top, z=z, lw=lw)

    def line(self, pts, **kw):
        q = [self.p(*a) for a in pts]
        self.ax.plot([a[0] for a in q], [a[1] for a in q], **kw)

    def text(self, x, y, z, s, **kw):
        u, v = self.p(x, y, z)
        self.ax.text(u, v, s, **kw)


def e_piece(o, y0, y1, zb, up=True, cols=None, gap=False, z=1):
    """One EE6405 half.  up=True: plate at the bottom, legs up (the lower core).
    up=False: legs down (the upper core), gap ground on its centre leg."""
    cols = cols or (COL_CORE_TOP, COL_CORE_FRONT, COL_CORE_SIDE)
    legs = [(0.0, OL), (CX - D / 2, CX + D / 2), (A - OL, A)]
    if up:
        o.box(0, A, y0, y1, zb, zb + T, cols, z=z)
        for x0, x1 in legs:
            o.box(x0, x1, y0, y1, zb + T, zb + B, cols, z=z)
    else:
        for i, (x0, x1) in enumerate(legs):
            zl0 = zb + (GAP_DRAW if (gap and i == 1) else 0.0)
            o.box(x0, x1, y0, y1, zl0, zb + F, cols, z=z)
        o.box(0, A, y0, y1, zb + F, zb + B, cols, z=z)


def stadium(r, y0, y1, n=40, half='both'):
    """Closed outline of a stadium of half-width r around the centre line,
    straight from y0 to y1, ends centred on (CX, y0) and (CX, y1)."""
    pts = []
    for t in np.linspace(0, math.pi, n):            # far end, right to left
        pts.append((CX + r * math.cos(t), y1 + r * math.sin(t)))
    for t in np.linspace(math.pi, 2 * math.pi, n):  # near end, left to right
        pts.append((CX + r * math.cos(t), y0 + r * math.sin(t)))
    return pts


def ring_top(o, r0, r1, y0, y1, z, fc, ec=INK, lw=0.6, zord=2, alpha=1.0):
    outer = [o.p(x, y, z) for x, y in stadium(r1, y0, y1)]
    inner = [o.p(x, y, z) for x, y in stadium(r0, y0, y1)][::-1]
    verts = outer + [outer[0]] + inner + [inner[0]]
    codes = ([Path.MOVETO] + [Path.LINETO] * (len(outer) - 1) + [Path.CLOSEPOLY] +
             [Path.MOVETO] + [Path.LINETO] * (len(inner) - 1) + [Path.CLOSEPOLY])
    o.ax.add_patch(PathPatch(Path(verts, codes), fc=fc, ec=ec, lw=lw, zorder=zord, alpha=alpha))


def u_band(o, r0, r1, yc, far, z, fc, ec=INK, lw=0.6, zord=2):
    """Half ring (the U turn) of radii r0..r1 at one end, on the plane z."""
    ts = np.linspace(0, math.pi, 40) if far else np.linspace(math.pi, 2 * math.pi, 40)
    outer = [(CX + r1 * math.cos(t), yc + r1 * math.sin(t)) for t in ts]
    inner = [(CX + r0 * math.cos(t), yc + r0 * math.sin(t)) for t in ts[::-1]]
    o.ax.add_patch(Polygon([o.p(x, y, z) for x, y in outer + inner], closed=True,
                           fc=fc, ec=ec, lw=lw, zorder=zord))


def coil_layer(o, zb, z=1, show_sec=True):
    """Bobbin (p.18) with the primary in its inner channel and the two secondary
    plates outside the wall (p.11), lying on the plane zb (bottom of the window)."""
    mid = zb + BOB_T / 2
    # far end block, with its U grooves
    eb0 = mid - END_T / 2
    o.box(CX - 30, CX + 30, Y1S, Y1S + END, eb0, eb0 + END_T,
          (COL_BOB_TOP, COL_BOB_FRONT, COL_BOB_SIDE), z=z)
    u_band(o, R_IN, R_CH, Y1S, True, eb0 + END_T, COL_CU_TOP, zord=z)
    u_band(o, R_CH, R_WALL, Y1S, True, eb0 + END_T, COL_BOB_FRONT, zord=z)
    # straight part: rails and channels, left to right
    strips = [(CX - R_FR, CX - R_RAIL), (CX - R_WALL, CX - R_CH), (CX - R_IN, CX - R_SLOT),
              (CX + R_SLOT, CX + R_IN), (CX + R_CH, CX + R_WALL), (CX + R_RAIL, CX + R_FR)]
    items = []
    for x0, x1 in strips:
        items.append((x0, 'rail', x1))
    items.append((CX - R_CH, 'pri', CX - R_IN))
    items.append((CX + R_IN, 'pri', CX + R_CH))
    if show_sec:
        sec_c = (R_WALL + R_RAIL) / 2
        items.append((CX - sec_c - 2.25, 'sec', CX - sec_c + 2.25))
        items.append((CX + sec_c - 2.25, 'sec', CX + sec_c + 2.25))
    for x0, kind, x1 in sorted(items):
        if kind == 'rail':
            o.box(x0, x1, Y0S, Y1S, zb, zb + BOB_T, (COL_BOB_TOP, COL_BOB_FRONT, COL_BOB_SIDE), z=z)
        elif kind == 'pri':
            o.box(x0, x1, Y0S, Y1S, zb + 0.05, zb + 1.2, (COL_CU_TOP, COL_CU_FRONT, COL_CU_SIDE), z=z, lw=0.5)
        else:
            o.box(x0, x1, Y0S, Y1S, zb + 0.1, zb + 0.6, (COL_SEC_TOP, COL_SEC_FRONT, COL_SEC_SIDE), z=z, lw=0.5)
            o.box(x0, x1, Y0S, Y1S, zb + 0.65, zb + 1.15, (COL_SEC_TOP, COL_SEC_FRONT, COL_SEC_SIDE), z=z, lw=0.5)
    # near end block on top of everything behind it
    o.box(CX - 30, CX + 30, Y0S - END, Y0S, eb0, eb0 + END_T,
          (COL_BOB_TOP, COL_BOB_FRONT, COL_BOB_SIDE), z=z)
    u_band(o, R_IN, R_CH, Y0S, False, eb0 + END_T, COL_CU_TOP, zord=z)
    u_band(o, R_CH, R_WALL, Y0S, False, eb0 + END_T, COL_BOB_FRONT, zord=z)


# ================================================================ figure
fig = plt.figure(figsize=(23.4, 16.5))       # A2 landscape in inches
gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 1.0], hspace=0.14, wspace=0.10,
                      left=0.03, right=0.985, top=0.885, bottom=0.10)
fig.suptitle('LG 26OP-LM83W (KH필룩스) 트랜스포머 하나의 구성 — 승인원 치수 그대로',
             fontsize=24, fontweight='bold', color=INK, x=0.03, y=0.985, ha='left')
fig.text(0.03, 0.948, '코어 EE6405 반쪽 4개 = 한 쌍(반쪽 2개)을 깊이 방향으로 2쌍 맞붙임.  '
         '권선 하나가 두 쌍의 센터 다리를 한꺼번에 감는다.  (LG 보드에는 이 트랜스포머가 3개, 1차 직렬)',
         fontsize=15, color=INK)

# ---------------------------------------------------------------- (1) one pair
ax = fig.add_subplot(gs[0, 0]); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('① 코어 한 세트 = 반쪽 2개 (EE6405 한 쌍)', fontsize=17, loc='left', color=INK, pad=12)
o = Oblique(ax, zs=3.0)
e_piece(o, 0, C, 0.0, up=True)
e_piece(o, 0, C, 12.0, up=False, gap=True)
for x in (0, A):
    o.line([(x, 0, B), (x, 0, 12.0)], color=RED, lw=1.0, ls=(0, (4, 3)), zorder=0)
def lab(o, ax, xyz, txt, uv, **kw):
    ax.annotate(txt, xy=o.p(*xyz), xytext=uv, fontsize=kw.pop('fontsize', 12), color=kw.pop('color', INK),
                va='center', arrowprops=dict(arrowstyle='->', lw=0.9, color=kw.pop('ac', INK)), **kw)
lab(o, ax, (A, C * 0.5, 12.0 + B * 0.6), '위쪽 반쪽 (센터 다리에 갭 · 승인원 "TOP GAP")', (A + 26, 52))
lab(o, ax, (CX + 2, 0, 12.0 + GAP_DRAW / 2), '갭 위치 (길이는 승인원에 없음)', (A + 26, 44))
lab(o, ax, (A, C * 0.5, B * 0.6), '아래쪽 반쪽 (갭 없음)', (A + 26, 14))
# dimensions
o.line([(0, -7, 0), (A, -7, 0)], color=INK, lw=0.8)
o.text(A / 2, -7, -2.2, 'A = 64.0 (폭)', fontsize=11.5, ha='center', va='top', color=INK)
o.line([(A + 2.0, 0, 0), (A + 2.0, C, 0)], color=INK, lw=0.8)
o.text(A + 3.0, C * 0.5, 0, 'C = 33.5 (깊이)', fontsize=11.5, color=INK, va='top', rotation=0)
o.text(CX, 0, B + 0.5, 'D 8.0', fontsize=10.5, ha='center', va='bottom', color=INK)
o.text(OL + WIN / 2, 0, T + 0.15, '창 24.0', fontsize=10.5, ha='center', va='bottom', color='white')
o.text(A - OL / 2, 0, B + 0.5, '4.0', fontsize=10.5, ha='center', va='bottom', color=INK)
ax.set_xlim(-6, A + 95); ax.set_ylim(-14, 62)
ax.text(0.0, -0.01, '한 반쪽: 판 1.6 + 다리 0.7 = 2.3 mm.  두 반쪽을 맞대면 두께 4.6 mm, 창 높이 1.4 mm.\n'
        '한 쌍의 A_e 113.1 mm² · l_e 57.13 mm · V_e 6461 mm³ (승인원 17쪽).  두께 방향은 3배로 그렸다.',
        transform=ax.transAxes, fontsize=12, color=INK, va='top')

# ---------------------------------------------------------------- (2) LG: two pairs
ax = fig.add_subplot(gs[0, 1:]); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('② LG 26OP-LM83W: ①의 한 쌍을 깊이 방향으로 2쌍 → 반쪽 4개 + 보빈 하나 + 권선 한 벌 (분해도)',
             fontsize=17, loc='left', color=INK, pad=12)
o = Oblique(ax, zs=3.0, k=0.62, ang=28.0)
SEP = 4.0                                   # pulled apart only to show the joint
Z_COIL, Z_TOP = 13.0, 26.0
pairs = [(C + SEP, 2 * C + SEP, (COL_CORE2_TOP, COL_CORE2_FRONT, COL_CORE2_SIDE)),
         (0.0, C, (COL_CORE_TOP, COL_CORE_FRONT, COL_CORE_SIDE))]
for y0, y1, cols in pairs:                   # bottom halves, far one first
    e_piece(o, y0, y1, 0.0, up=True, cols=cols, z=1)
coil_layer(o, Z_COIL, z=2)
for y0, y1, cols in pairs:                   # top halves
    e_piece(o, y0, y1, Z_TOP, up=False, cols=cols, gap=True, z=3)
# assembly guides
for x, y in ((0, 0), (A, 0), (A, 2 * C + SEP)):
    o.line([(x, y, B), (x, y, Z_TOP)], color=RED, lw=0.9, ls=(0, (4, 3)), zorder=0)
# labels: pair 1 on the left, pair 2 on the right, the rest in the right margin
UL, UR = -46, 120
lab(o, ax, (0, C * 0.5, T * 0.5), '쌍 1 아래 반쪽', (UL, o.p(0, C * 0.5, T * 0.5)[1]), fontsize=13)
lab(o, ax, (0, C * 0.5, Z_TOP + B * 0.6), '쌍 1 위 반쪽', (UL, o.p(0, C * 0.5, Z_TOP + B * 0.6)[1]), fontsize=13)
lab(o, ax, (A, C + SEP + C * 0.75, T * 0.5), '쌍 2 아래 반쪽', (UR, o.p(A, C + SEP + C * 0.75, T * 0.5)[1] - 2), fontsize=13)
lab(o, ax, (A, C + SEP + C * 0.75, Z_TOP + B * 0.6), '쌍 2 위 반쪽', (UR, o.p(A, C + SEP + C * 0.75, Z_TOP + B * 0.6)[1] + 3), fontsize=13)
lab(o, ax, (A, C + SEP / 2, B * 0.5), '여기서 두 쌍이 맞붙는다 (이음선)\n승인원 5쪽 외형도의 가운데 선.  그림은 4 mm 벌려 그림',
    (UR, o.p(A, C + SEP / 2, B * 0.5)[1] - 9), color=RED, ac=RED)
lab(o, ax, (CX, 20, Z_COIL + BOB_T * 0.5), '보빈(18쪽) 가운데 홈\n8.5 × 68 mm 에\n두 쌍의 센터 다리\n8 × 33.5 두 개(= 8 × 67)가\n이어서 들어간다',
    (-82, o.p(CX, 20, Z_COIL)[1] + 4), fontsize=12, ha='left')
lab(o, ax, (CX - (R_IN + R_CH) / 2, Y1S - 6, Z_COIL + 1.2), '1차 NP1 5T 리츠: 보빈 안쪽 홈,\n코어 밖 보빈 끝에서 U자로 돈다',
    (UR, o.p(A, Y1S, Z_COIL)[1] + 14), color='#a3501a', ac='#a3501a')
lab(o, ax, (CX + (R_WALL + R_RAIL) / 2, Y1S * 0.45, Z_COIL + 1.15), '2차 NS2 · NS3 동판 1T씩(0.5 × 4.5):\n칸막이 바깥에 두 장을 위아래로 겹침\n(끝 모양 · 핀 연결은 승인원에 없음)',
    (UR, o.p(A, Y1S * 0.45, Z_COIL)[1] - 1), color='#7a3a12', ac='#7a3a12')
ax.text(0.0, 0.0, '두께 방향 3배.  보빈 끝 블록의 홈 깊이는 단순화.', transform=ax.transAxes, fontsize=11.5, color=INK)
ax.set_xlim(UL - 6, UR + 62); ax.set_ylim(-8, 128)

# ---------------------------------------------------------------- (3) top view
ax = fig.add_subplot(gs[1, 0]); ax.set_aspect('equal'); ax.axis('off')
ax.set_title('③ 위에서 본 모습 (축척 그대로, mm)', fontsize=17, loc='left', color=INK, pad=10)
# bobbin
ax.add_patch(Rectangle((CX - 30, Y0S - END), 60, END, fc=COL_BOB_TOP, ec=INK, lw=0.8))
ax.add_patch(Rectangle((CX - 30, Y1S), 60, END, fc=COL_BOB_TOP, ec=INK, lw=0.8))
ax.add_patch(Rectangle((CX - R_FR, Y0S), 2 * R_FR, STRAIGHT, fc=COL_BOB_TOP, ec=INK, lw=0.8))
for yc, far in ((Y1S, True), (Y0S, False)):
    for r0, r1, fc in ((R_IN, R_CH, COL_CU_TOP), (R_CH, R_WALL, COL_BOB_FRONT)):
        ts = np.linspace(0, math.pi, 60) if far else np.linspace(math.pi, 2 * math.pi, 60)
        pts = ([(CX + r1 * math.cos(t), yc + r1 * math.sin(t)) for t in ts] +
               [(CX + r0 * math.cos(t), yc + r0 * math.sin(t)) for t in ts[::-1]])
        ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=INK, lw=0.6))
# cores (two pairs) and tapes
for y0, cols in ((0.0, COL_CORE_TOP), (C, COL_CORE2_TOP)):
    ax.add_patch(Rectangle((0, y0), A, C, fc=cols, ec=INK, lw=1.0, alpha=0.93, zorder=3))
    yc = y0 + C / 2
    ax.add_patch(Rectangle((-0.6, yc - TAPE_W / 2), A + 1.2, TAPE_W, fc='white', ec='#888888',
                           lw=0.6, alpha=0.45, zorder=4, hatch='////'))
ax.plot([-3, A + 3], [C, C], color=RED, lw=1.8, zorder=5)
ax.text(A + 4, C, '이음선', color=RED, fontsize=12, va='center')
# hidden lines: centre leg and window edges
for x in (OL, CX - D / 2, CX + D / 2, A - OL):
    ax.plot([x, x], [0, 2 * C], color=INK, lw=0.8, ls=(0, (5, 4)), zorder=5)
ax.text(CX, 2 * C - 3, '센터 다리\n8 × 67', fontsize=10.5, ha='center', va='top', color=INK, zorder=6)
ax.text(OL + WIN / 2, 2 * C - 3, '창', fontsize=11, ha='center', va='top', color=INK, zorder=6)
ax.text(A - OL - WIN / 2, 2 * C - 3, '창', fontsize=11, ha='center', va='top', color=INK, zorder=6)
ax.text(A / 2, C / 2, '쌍 1', fontsize=16, ha='center', va='center', color=INK, zorder=6, fontweight='bold')
ax.text(A / 2, C + C / 2, '쌍 2', fontsize=16, ha='center', va='center', color=INK, zorder=6, fontweight='bold')


def dim_v(ax, x, y0, y1, txt, side='right'):
    ax.annotate('', xy=(x, y0), xytext=(x, y1), arrowprops=dict(arrowstyle='<->', lw=0.9, color=INK))
    ax.text(x + (1.2 if side == 'right' else -1.2), (y0 + y1) / 2, txt, fontsize=11, va='center',
            ha='left' if side == 'right' else 'right', color=INK, rotation=90)


def dim_h(ax, y, x0, x1, txt, below=True):
    ax.annotate('', xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle='<->', lw=0.9, color=INK))
    ax.text((x0 + x1) / 2, y + (-1.4 if below else 1.4), txt, fontsize=11, ha='center',
            va='top' if below else 'bottom', color=INK)


dim_v(ax, A + 9, 0, C, '33.5')
dim_v(ax, A + 9, C, 2 * C, '33.5')
dim_v(ax, A + 16, 0, 2 * C, '67 = 2 × 33.5')
dim_v(ax, -4, Y0S, Y1S, '보빈 직선부 68', side='left')
dim_v(ax, -10, Y0S - END, Y1S + END, '보빈 103.1', side='left')
dim_h(ax, Y0S - END - 3, 0, A, '코어 폭 64')
ax.text(A / 2, Y1S + END + 2, '보빈 끝(핀 쪽)', fontsize=11, ha='center', va='bottom', color=INK)
ax.text(A / 2, Y0S - END - 8.5, '빗금 띠 = 코어 고정 테이프(21.5 폭), 쌍마다 하나.  점선 = 코어에 가려진 센터 다리 · 창.\n'
        '주황 = 1차 권선이 코어 밖으로 나와 U자로 도는 부분.', fontsize=11, ha='center', va='top', color=INK)
ax.set_xlim(-22, A + 26); ax.set_ylim(Y0S - END - 16, Y1S + END + 6)

# ---------------------------------------------------------------- (4) cross-section A-A
ax = fig.add_subplot(gs[1, 1]); ax.axis('off')
ax.set_title('④ 단면 A–A: 한 쌍을 폭 방향으로 자른 면 (두께 방향 6배)', fontsize=17, loc='left', color=INK, pad=10)
ZS = 6.0
def R(x0, x1, z0, z1, **kw):
    ax.add_patch(Rectangle((x0, z0 * ZS), x1 - x0, (z1 - z0) * ZS, **kw))
core_kw = dict(fc=COL_CORE_FRONT, ec=INK, lw=0.8)
R(0, A, 0, T, **core_kw)
for x0, x1 in ((0, OL), (CX - D / 2, CX + D / 2), (A - OL, A)):
    R(x0, x1, T, B, **core_kw)
for i, (x0, x1) in enumerate(((0, OL), (CX - D / 2, CX + D / 2), (A - OL, A))):
    R(x0, x1, B + (GAP_DRAW if i == 1 else 0), B + F, **core_kw)
R(0, A, B + F, 2 * B, **core_kw)
# bobbin rails (1.3 thick) inside the 1.4 window
zb = T + 0.05
for x0, x1 in ((CX - R_FR, CX - R_RAIL), (CX - R_WALL, CX - R_CH), (CX - R_IN, CX - R_SLOT),
               (CX + R_SLOT, CX + R_IN), (CX + R_CH, CX + R_WALL), (CX + R_RAIL, CX + R_FR)):
    R(x0, x1, zb, zb + BOB_T, fc=COL_BOB_FRONT, ec=INK, lw=0.6)
# primary: 5 turns, one layer in the 7.3 mm channel
for side in (-1, 1):
    a, b = (CX + side * R_IN, CX + side * R_CH)
    lo, hi = min(a, b), max(a, b)
    for k in range(5):
        xc = lo + (k + 0.5) * (hi - lo) / 5
        ax.add_patch(Ellipse((xc, (T + B + F) / 2 * ZS), 1.25, 1.25 * ZS, fc=COL_CU_TOP, ec=INK, lw=0.6))
    # secondaries: two plates 0.5 x 4.5, stacked
    sc = CX + side * (R_WALL + R_RAIL) / 2
    R(sc - 2.25, sc + 2.25, T + 0.12, T + 0.62, fc=COL_SEC_TOP, ec=INK, lw=0.6)
    R(sc - 2.25, sc + 2.25, T + 0.72, T + 1.22, fc=COL_SEC_TOP, ec=INK, lw=0.6)
ax.annotate('1차 NP1 5T 리츠 (한 줄)', xy=(CX - (R_IN + R_CH) / 2, (B + 0.3) * ZS), xytext=(CX - 6, 2 * B * ZS + 6),
            fontsize=11, color='#a3501a', ha='center', arrowprops=dict(arrowstyle='->', lw=0.8, color='#a3501a'))
ax.annotate('2차 NS2 · NS3 동판 2장 (겹침)', xy=(CX - (R_WALL + R_RAIL) / 2, (T + 1.0) * ZS), xytext=(2, 2 * B * ZS + 11),
            fontsize=11, color='#7a3a12', ha='left', arrowprops=dict(arrowstyle='->', lw=0.8, color='#7a3a12'))
ax.annotate('갭', xy=(CX, (B + GAP_DRAW / 2) * ZS), xytext=(CX + 9, 2 * B * ZS + 6), fontsize=11, color=INK,
            arrowprops=dict(arrowstyle='->', lw=0.8, color=INK))
ax.annotate('보빈 칸막이', xy=(CX - (R_WALL + R_CH) / 2, T * ZS + 1), xytext=(CX - 22, -3.0), fontsize=10.5, color=INK,
            ha='center', va='top', arrowprops=dict(arrowstyle='->', lw=0.8, color=INK))
# dims
def hd(y, x0, x1, txt):
    ax.annotate('', xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle='<->', lw=0.8, color=INK))
    ax.text((x0 + x1) / 2, y - 0.5, txt, fontsize=10.5, ha='center', va='top', color=INK)
hd(-6.5, 0, A, '64.0')
hd(-11.5, OL, CX - D / 2, '창 24.0')
hd(-11.5, CX - D / 2, CX + D / 2, '8.0')
ax.annotate('', xy=(A + 2.5, 0), xytext=(A + 2.5, 2 * B * ZS), arrowprops=dict(arrowstyle='<->', lw=0.8, color=INK))
ax.text(A + 3.4, B * ZS, '4.6', fontsize=10.5, va='center', color=INK)
ax.annotate('', xy=(-2.5, T * ZS), xytext=(-2.5, (B + F) * ZS), arrowprops=dict(arrowstyle='<->', lw=0.8, color=INK))
ax.text(-3.2, B * ZS, '창 1.4', fontsize=10.5, va='center', ha='right', color=INK)
ax.text(-3.2, T * ZS / 2, '판 1.6', fontsize=10.5, va='center', ha='right', color=INK)
ax.text(0, -16.5, '창 폭 24 mm 를 바깥쪽부터: 보빈 레일 · 2차 동판 · 칸막이 · 1차 리츠 · 안쪽 벽 순(승인원 11쪽 · 18쪽).\n'
        '높이 1.4 mm 라 1차는 한 줄, 2차는 0.5 mm 판 두 장이 한계.  갭 길이 · 리츠 외경은 승인원에 없어 크기 없이 위치만 표시.',
        fontsize=11, va='top', color=INK)
ax.set_xlim(-14, A + 9); ax.set_ylim(-25, 2 * B * ZS + 16); ax.set_aspect('equal')

# ---------------------------------------------------------------- (5) long section B-B
ax = fig.add_subplot(gs[1, 2]); ax.axis('off')
ax.set_title('⑤ 단면 B–B: 센터 다리를 길이 방향으로 자른 면 (두께 방향 6배)', fontsize=17, loc='left', color=INK, pad=10)
def L(y0, y1, z0, z1, **kw):
    ax.add_patch(Rectangle((y0, z0 * ZS), y1 - y0, (z1 - z0) * ZS, **kw))
for y0, col in ((0.0, COL_CORE_FRONT), (C, COL_CORE2_FRONT)):
    kw = dict(fc=col, ec=INK, lw=0.8)
    L(y0, y0 + C, 0, B, **kw)                 # lower half, cut through its centre leg
    L(y0, y0 + C, B + GAP_DRAW, 2 * B, **kw)  # upper half, gap at its centre leg
ax.plot([C, C], [-1.2, 2 * B * ZS + 1.2], color=RED, lw=1.8)
ax.text(C, 2 * B * ZS + 1.8, '이음선', color=RED, fontsize=12, ha='center', va='bottom')
ax.text(C / 2, B / 2 * ZS, '쌍 1', fontsize=15, ha='center', va='center', color='white', fontweight='bold')
ax.text(C + C / 2, B / 2 * ZS, '쌍 2', fontsize=15, ha='center', va='center', color='white', fontweight='bold')
ax.annotate('갭(위 반쪽 센터 다리, 길이 미기재)', xy=(C * 0.25, (B + GAP_DRAW / 2) * ZS), xytext=(C * 0.05, 2 * B * ZS + 5.5),
            fontsize=10.5, color=INK, arrowprops=dict(arrowstyle='->', lw=0.8, color=INK))
# bobbin end blocks with the primary's U turn crossing the centre line
mid = (T + B + F) / 2
for ys, sgn in ((Y0S, -1), (Y1S, 1)):
    y_a, y_b = sorted((ys, ys + sgn * END))
    L(y_a, y_b, mid - END_T / 2, mid + END_T / 2, fc=COL_BOB_FRONT, ec=INK, lw=0.7)
    u0, u1 = sorted((ys + sgn * R_IN, ys + sgn * R_CH))
    L(u0, u1, T + 0.05, T + 1.25, fc=COL_CU_TOP, ec=INK, lw=0.6)
ax.text(Y0S - (R_IN + R_CH) / 2, mid * ZS + END_T / 2 * ZS + 1.5, '1차 권선\n(U자 끝)', fontsize=10.5,
        ha='center', va='bottom', color='#a3501a')
ax.text(Y1S + (R_IN + R_CH) / 2, mid * ZS + END_T / 2 * ZS + 1.5, '1차 권선\n(U자 끝)', fontsize=10.5,
        ha='center', va='bottom', color='#a3501a')
ax.text(Y0S - END / 2, mid * ZS - END_T / 2 * ZS - 1.2, '보빈 끝', fontsize=10.5, ha='center', va='top', color=INK)
ax.text(Y1S + END / 2, mid * ZS - END_T / 2 * ZS - 1.2, '보빈 끝', fontsize=10.5, ha='center', va='top', color=INK)
def hd2(z, y0, y1, txt):
    ax.annotate('', xy=(y0, z), xytext=(y1, z), arrowprops=dict(arrowstyle='<->', lw=0.8, color=INK))
    ax.text((y0 + y1) / 2, z - 0.6, txt, fontsize=10.5, ha='center', va='top', color=INK)
hd2(-6.0, 0, C, '33.5')
hd2(-6.0, C, 2 * C, '33.5')
hd2(-11.5, 0, 2 * C, '센터 다리 67 (= 33.5 × 2)')
ax.text(Y0S - END, -16.5, '권선은 두 쌍의 센터 다리 전체(67 mm)를 한 바퀴로 감싸고, 코어 밖 보빈 끝에서 돌아 나간다.\n'
        '그래서 자속이 지나는 단면도 두 쌍 합계: A_e 113.1 × 2 = 226 mm² (높이는 한 쌍과 같은 4.6 mm).',
        fontsize=11, va='top', color=INK)
ax.set_xlim(Y0S - END - 3, Y1S + END + 3); ax.set_ylim(-25, 2 * B * ZS + 16); ax.set_aspect('equal')

# ---------------------------------------------------------------- footer
fig.text(0.03, 0.035,
         '근거(승인원, KH필룩스 2025-05-26): 17쪽 코어 치수 A 64 · B 2.30 · C 33.5 · D 8.0 · E 56 · F 0.70 · B-F 1.60 / '
         '18쪽 보빈 중앙 홈 8.50 · 직선부 68.00 · 82.50 · 97.10 · 103.10 · 14.50 · 29.10 · 35.10 · 48.90 · 54.90 · 60.00 / '
         '5쪽 외형도: 도면의 143.9 mm 치수를 자로 재면 코어 영역 66.9 mm, 윗면 · 밑면 모두 정확히 가운데에 이음선, 테이프 띠가 각 쌍 중심에 하나씩 / '
         '6쪽 권선표 / 11쪽 내부 구조(8절).\n'
         '사양서 어디에도 코어 수량은 숫자로 적혀 있지 않다(19쪽 QC 공정도는 다른 모델 24OP-LM77G 의 표).  '
         '갭 길이 · 리츠 외경 · 2차 동판의 끝 모양은 승인원에 없어 치수 없이 그렸다.',
         fontsize=11.5, color='#45505c', va='bottom', wrap=True)

import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'docs',
                   'LG_26OP-LM83W_core_construction')
fig.savefig(out + '.png', dpi=120)
fig.savefig(out + '.pdf')
print('saved', os.path.normpath(out))
