# -*- coding: utf-8 -*-
"""Bobbin and core pictures after the vendor's images (as-built spec)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

S = os.path.dirname(os.path.abspath(__file__)) + '/'
NAVY = '#1f3a5f'; RED = '#b03030'; LT = '#eef3f8'

# ---------------- bobbin: 4 pins below (1-4), 8 pins above (12 ... 5)
fig, ax = plt.subplots(figsize=(4.2, 3.2), dpi=160); ax.set_aspect('equal'); ax.axis('off')
ax.add_patch(Rectangle((0, 1.2), 10, 3.6, fc='white', ec=NAVY, lw=1.6))
ax.add_patch(Rectangle((0.4, 1.9), 9.2, 2.2, fc=LT, ec=NAVY, lw=1.0))
ax.add_patch(Rectangle((-0.2, 4.8), 10.4, 0.5, fc='white', ec=NAVY, lw=1.6))
ax.add_patch(Rectangle((-0.2, 0.7), 10.4, 0.5, fc='white', ec=NAVY, lw=1.6))
for i in range(8):
    x = 0.55 + i * 1.27
    ax.add_patch(Rectangle((x, 5.3), 0.28, 0.9, fc=NAVY, ec=NAVY))
    ax.text(x + 0.14, 6.35, str(12 - i), ha='center', va='bottom', fontsize=7.5,
            color=RED, weight='bold')
for i in range(4):
    x = 1.2 + i * 2.5
    ax.add_patch(Rectangle((x, -0.2), 0.28, 0.9, fc=NAVY, ec=NAVY))
    ax.text(x + 0.14, -0.35, str(1 + i), ha='center', va='top', fontsize=7.5,
            color=RED, weight='bold')
ax.text(5, 3.0, 'winding section', ha='center', va='center', fontsize=8, color=NAVY)
ax.text(10.6, 5.75, 'pins 5-12', va='center', fontsize=8, color=NAVY)
ax.text(10.6, 0.25, 'pins 1-4', va='center', fontsize=8, color=NAVY)
ax.set_xlim(-0.6, 13); ax.set_ylim(-1.2, 7.2)
fig.savefig(S + 'bobbin.png', bbox_inches='tight', facecolor='white'); plt.close(fig)

# ---------------- core: front view (A, D, E, C) and side view (B, F), mm
A, B, C, D, E, F = 42.0, 7.85, 19.0, 36.0, 6.0, 4.85
leg = (A - D) / 2
fig, ax = plt.subplots(figsize=(5.6, 3.4), dpi=160); ax.set_aspect('equal'); ax.axis('off')
ax.add_patch(Rectangle((0, 0), C, A, fc='white', ec=NAVY, lw=1.6))
for y, h in ((0, leg), (A / 2 - E / 2, E), (A - leg, leg)):
    ax.add_patch(Rectangle((0, y), C, h, fc=LT, ec=NAVY, lw=1.0))


def dim(x1, y1, x2, y2, label, off=0, rot=0):
    ax.annotate('', (x1, y1), (x2, y2),
                arrowprops=dict(arrowstyle='<->', color=RED, lw=0.9, shrinkA=0, shrinkB=0))
    ax.text((x1 + x2) / 2 + (off if rot else 0), (y1 + y2) / 2 + (0 if rot else off), label,
            ha='center', va='center', fontsize=8.5, color=RED, rotation=rot,
            bbox=dict(fc='white', ec='none', pad=1))


dim(C + 6, 0, C + 6, A, 'A 42.00', off=1.8, rot=90)
dim(C + 3, leg, C + 3, A - leg, 'D 36.00', off=-1.8, rot=90)
dim(-2.5, A / 2 - E / 2, -2.5, A / 2 + E / 2, 'E 6.00', off=-3.4, rot=90)
dim(0, -3.5, C, -3.5, 'C 19.00', off=-2.4)
for y in (A / 2 - E / 2, A / 2 + E / 2):
    ax.plot([0, -3.5], [y, y], color=RED, lw=0.5)
for y in (leg, A - leg):
    ax.plot([C, C + 4], [y, y], color=RED, lw=0.5)
sx = C + 12
pl = B - F
ax.add_patch(Rectangle((sx, 0), pl, A, fc=LT, ec=NAVY, lw=1.4))
for y, h in ((0, leg), (A / 2 - E / 2, E), (A - leg, leg)):
    ax.add_patch(Rectangle((sx + pl, y), F, h, fc=LT, ec=NAVY, lw=1.4))
dim(sx, -3.5, sx + B, -3.5, 'B 7.85', off=-2.4)
dim(sx + pl, -8.0, sx + B, -8.0, 'F 4.85', off=-2.4)
for x, y0 in ((sx + pl, -9), (sx + B, -9), (sx, -4.5)):
    ax.plot([x, x], [0, y0], color=RED, lw=0.5)
ax.text(C / 2, A + 2.5, 'front view', ha='center', fontsize=8.5, color=NAVY)
ax.text(sx + B / 2, A + 2.5, 'side view', ha='center', fontsize=8.5, color=NAVY)
ax.set_xlim(-8, sx + B + 3); ax.set_ylim(-11, A + 5)
fig.savefig(S + 'core.png', bbox_inches='tight', facecolor='white'); plt.close(fig)
print('images ok')
