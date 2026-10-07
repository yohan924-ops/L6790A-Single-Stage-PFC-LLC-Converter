# -*- coding: utf-8 -*-
"""Bobbin and core pictures after the vendor's images (as-built spec)."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

S = os.path.dirname(os.path.abspath(__file__)) + '/'
NAVY = '#1f3a5f'; RED = '#b03030'; LT = '#eef3f8'

# ---------------- bobbin, side view after the vendor's picture: an 8-pin terminal
# block on top (12 ... 5), two flanges with the tube between, a 4-pin block with
# mounting feet below (1 ... 4). Proportions follow the picture, not a drawing.
from matplotlib.patches import Arc
fig, ax = plt.subplots(figsize=(4.0, 4.6), dpi=160); ax.set_aspect('equal'); ax.axis('off')
def rect(x, y, w, h, lw=1.2, fc='white', ec=NAVY):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw))
# --- upper terminal block (x 0 .. 10)
rect(0, 7.4, 10.0, 2.9, lw=1.4)
for i in range(8):                                   # 8 pin stubs on top
    x = 0.35 + i * 1.3
    rect(x, 10.3, 0.22, 0.7, lw=1.0)
    ax.plot([x - 0.35, x + 0.57], [10.3, 10.3], color=NAVY, lw=1.4)
    ax.text(x + 0.11, 11.15, str(12 - i), ha='center', va='bottom', fontsize=7.5, color=RED, weight='bold')
for i in (0, 1, 2, 5, 6, 7):                         # 6 slots in the block face
    x = 0.95 + i * 1.3
    rect(x, 8.6, 0.3, 1.4, lw=0.9, fc='#8a99ab')
rect(4.55, 8.45, 0.9, 0.5, lw=1.0)                   # centre boss
ax.add_patch(Rectangle((4.4, 7.4), 1.2, 1.05, fc='white', ec=NAVY, lw=1.0))
ax.add_patch(Arc((5.0, 7.75), 0.9, 0.5, theta1=180, theta2=360, color=NAVY, lw=1.0))
# neck between block and flange, with two arches
rect(0.7, 6.6, 8.6, 0.8, lw=1.0)
for cx in (3.4, 6.6):
    ax.add_patch(Arc((cx, 6.6), 1.8, 1.4, theta1=0, theta2=180, color=NAVY, lw=1.0))
# --- flanges and the tube
rect(-0.15, 6.0, 10.3, 0.6, lw=1.4)                  # upper flange
rect(0.0, 3.0, 10.0, 3.0, lw=1.4)                    # tube (winding section)
rect(-0.15, 2.4, 10.3, 0.6, lw=1.4)                  # lower flange
# --- lower neck with arches, then the terminal block with feet
rect(0.7, 1.6, 8.6, 0.8, lw=1.0)
for cx in (3.4, 6.6):
    ax.add_patch(Arc((cx, 2.4), 1.8, 1.4, theta1=180, theta2=360, color=NAVY, lw=1.0))
rect(0.0, -1.3, 10.0, 2.9, lw=1.4)                   # lower block
rect(0.4, -1.0, 9.2, 2.3, lw=0.8)                    # inner frame
for x in (1.6, 7.4):                                 # two square feet openings
    rect(x, -0.8, 1.0, 1.3, lw=1.0, fc='#8a99ab')
rect(4.3, 0.2, 1.4, 1.1, lw=1.0)                     # centre latch
rect(4.5, -0.9, 1.0, 1.1, lw=0.9)
rect(2.9, -0.9, 1.4, 0.6, lw=0.8); rect(5.7, -0.9, 1.4, 0.6, lw=0.8)
for x in (-0.35, 10.05):                             # side tabs
    rect(x, -1.0, 0.3, 0.7, lw=1.0)
for i in range(4):                                   # 4 pin stubs below
    x = 1.1 + i * 2.6
    rect(x, -2.0, 0.22, 0.7, lw=1.0)
    ax.text(x + 0.11, -2.2, str(1 + i), ha='center', va='top', fontsize=7.5, color=RED, weight='bold')
ax.text(10.9, 10.65, 'pins 5-12', va='center', fontsize=8, color=NAVY)
ax.text(10.9, -1.65, 'pins 1-4', va='center', fontsize=8, color=NAVY)
ax.set_xlim(-0.8, 13.6); ax.set_ylim(-3.1, 12.1)
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
