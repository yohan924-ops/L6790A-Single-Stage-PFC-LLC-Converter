# -*- coding: utf-8 -*-
"""The eight operating intervals of one switching period, drawn our way.

The note had four circuit panels - two power delivery, two freewheeling -
and no picture at all of the dead time, which is the one interval ZVS
actually happens in.  That gap came from the source: the reference figures
those four panels were taken from have no dead-time panel either.

So this file draws the whole period from scratch.  The circuit is ours, the
topology is the one the rest of chapter 2 uses (full bridge on the primary,
bridge rectifier on the secondary), and the interval-by-interval treatment
follows the Toshiba application note's eight modes - which are for a HALF
bridge, so every path here had to be re-derived for the full bridge.

Two current colours, and they carry meaning:

    solid magenta   load current - power is crossing to the secondary
    dashed cyan     magnetising current only - nothing crosses

Mode map (first half; the second half is the mirror image):

    1  power delivery   S1,S4 on      D1,D4 conduct       i_Lr = i_Lm + i_o1
    2  freewheeling     S1,S4 STILL on, secondary off     i_Lr = i_Lm
    3  dead time (a)    all off, C_oss of the four swap the midpoints over
    4  dead time (b)    body diodes of S2,S3 clamp   <-- ZVS turn-on is here
"""
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

import matplotlib.patheffects as pe

import schem as S
from schem import NAVY, MAG, CYA, GRN, PUR, GREY, LT, YEL

OFFW = '#C9CBD1'          # a device that is off, or a wire carrying nothing


# ------------------------------------------------------------------ pieces
def hop(ax, x, y, r=0.17, vertical_wire=True, color=NAVY):
    """A wire crossing another without joining it.

    A bridge rectifier fed from a winding cannot be drawn without one
    crossing, and neither can a full bridge whose tank leaves to the right
    past the second leg.  Both are drawn, not fudged.
    """
    a = np.linspace(0, np.pi, 40)
    if vertical_wire:                       # the hopping wire is horizontal
        ax.plot(x + r * np.cos(a)[::-1], y + r * np.sin(a), color=color,
                lw=S.LW, zorder=4)
    else:
        ax.plot(x + r * np.sin(a), y + r * np.cos(a)[::-1], color=color,
                lw=S.LW, zorder=4)


def mosfet(ax, x, y, name, state, h=1.30, w=0.62):
    """A switch with its body diode always visible.

    state: 'on'   gated on and carrying
           'diode' gated off, body diode conducting  (this is the ZVS one)
           'coss'  gated off, only C_oss carrying
           'off'   gated off, nothing flowing

    -> (drain, source) terminal points, drain on top.
    """
    fc = {'on': YEL, 'diode': 'white', 'coss': 'white', 'off': 'white'}[state]
    ec = {'on': MAG, 'diode': GREY, 'coss': GREY, 'off': OFFW}[state]
    lw = 2.3 if state == 'on' else 1.4
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=fc, ec=ec, lw=lw,
                           zorder=3))
    ax.text(x, y, name, ha='center', va='center', fontsize=10.0,
            fontweight='bold', zorder=9,
            color=NAVY if state != 'off' else GREY,
            path_effects=[pe.withStroke(linewidth=3.2, foreground='white')])

    # the body diode, antiparallel, on the right flank
    xd = x + w / 2 + 0.34
    dcol = GRN if state == 'diode' else OFFW
    dlw = 2.4 if state == 'diode' else 1.2
    ax.plot([x + w / 2, xd, xd], [y + h / 2 - 0.10, y + h / 2 - 0.10,
                                  y + 0.16], color=dcol, lw=dlw, zorder=3)
    ax.plot([x + w / 2, xd, xd], [y - h / 2 + 0.10, y - h / 2 + 0.10,
                                  y - 0.16], color=dcol, lw=dlw, zorder=3)
    tri = [(xd - 0.15, y - 0.16), (xd + 0.15, y - 0.16), (xd, y + 0.16)]
    ax.fill(*zip(*tri), color=dcol, zorder=4)
    ax.plot([xd - 0.15, xd + 0.15], [y + 0.16] * 2, color=dcol, lw=2.0,
            zorder=4)
    return (x, y + h / 2), (x, y - h / 2)


def coss(ax, x, y, h, kind):
    """C_oss drawn on the left flank, only in the two C_oss panels.

    kind: 'charge' its V_ds is rising, 'discharge' falling, None not shown
    """
    if kind is None:
        return
    col = MAG if kind == 'charge' else CYA
    xc = x - 0.68
    ax.plot([x - 0.31, xc, xc], [y + h / 2 - 0.10, y + h / 2 - 0.10,
                                 y + 0.13], color=col, lw=1.7, zorder=3)
    ax.plot([x - 0.31, xc, xc], [y - h / 2 + 0.10, y - h / 2 + 0.10,
                                 y - 0.13], color=col, lw=1.7, zorder=3)
    for dy in (0.13, -0.13):
        ax.plot([xc - 0.19, xc + 0.19], [y + dy] * 2, color=col, lw=2.2,
                zorder=4)
    S.label(ax, xc - 0.26, y, 'C$_{oss}$', size=8.5, color=col,
             ha='right', z=5)
    ax.annotate('', xy=(xc, y + (0.52 if kind == 'charge' else -0.52)),
                xytext=(xc, y + (-0.10 if kind == 'charge' else 0.10)),
                arrowprops=dict(arrowstyle='-|>', color=col, lw=1.8),
                zorder=6)


HOPS = []                 # filled in below, once the geometry exists


def _arc(hx, hy, r, going_right):
    a = np.linspace(np.pi, 0, 24) if going_right else np.linspace(0, np.pi, 24)
    return [(hx + r * np.cos(t), hy + r * np.sin(t)) for t in a]


def _with_hops(pts, r=0.17):
    """Make the highlight climb the same hops the wire does.

    Drawn straight, the highlight runs through the crossing and the panel
    then claims a connection that is not there - which matters most in
    exactly the panels where both wires are live.
    """
    out = [pts[0]]
    for p0, p1 in zip(pts, pts[1:]):
        for hx, hy in HOPS:
            if abs(p0[1] - hy) < 1e-9 and abs(p1[1] - hy) < 1e-9 \
                    and min(p0[0], p1[0]) < hx - r \
                    and hx + r < max(p0[0], p1[0]):
                right = p1[0] > p0[0]
                out.append((hx - r if right else hx + r, hy))
                out += _arc(hx, hy, r, right)
                out.append((hx + r if right else hx - r, hy))
                break
        out.append(p1)
    return out


def path(ax, pts, load=True, heads=(), lw=3.6):
    """The conducting path, laid over the drawing.

    load=True  -> solid magenta, power is being delivered
    load=False -> dashed cyan, only the magnetising current circulates
    heads: indices into pts; an arrowhead is put on the segment ENDING there
    """
    col = MAG if load else CYA
    xs, ys = zip(*_with_hops(pts))
    ax.plot(xs, ys, color=col, lw=lw, alpha=0.50 if load else 0.72, zorder=7,
            solid_capstyle='round',
            ls='-' if load else (0, (4.0, 2.4)))
    for i in heads:
        p0, p1 = np.array(pts[i - 1], float), np.array(pts[i], float)
        m = p0 + 0.62 * (p1 - p0)
        d = p1 - p0
        n = np.hypot(*d)
        if n < 1e-9:
            continue
        ax.add_patch(FancyArrowPatch(m - d / n * 0.12, m + d / n * 0.12,
                                     arrowstyle='-|>', mutation_scale=17,
                                     color=col, lw=2.4, zorder=8,
                                     shrinkA=0, shrinkB=0))


# ------------------------------------------------------------- the circuit
#  One geometry table, used by all eight panels, so nothing can drift.
HI, LO = 7.05, 0.55                      # primary rails
XL, XR = 1.55, 3.95                      # the two legs
YT, YB = 4.30, 3.15                      # tank wire out, return wire back
SH = 5.62, 1.98                          # switch centres, high and low
XCR, XLR, XLM, XTR = 5.30, 6.45, 7.55, 9.05
VP, VN = 6.05, 1.50                      # output rails
XD1, XD2, XCO = 10.35, 11.75, 13.00


def _skeleton(ax, states, coss_map=None):
    """Everything that is the same in every panel."""
    S.frame(ax, 0.05, 15.2, -0.35, 9.15)

    # primary rails
    S.wire(ax, [(0.55, HI), (XR + 0.5, HI)])
    S.wire(ax, [(0.55, LO), (XR + 0.5, LO)])
    S.dot(ax, 0.55, HI)
    S.dot(ax, 0.55, LO)
    S.label(ax, 0.40, HI, 'V$_{in}$', ha='right', size=10.5, weight='bold')
    S.label(ax, 0.40, LO, '0', ha='right', size=10.5)

    # the two legs
    for x, hi_name, lo_name in ((XL, 'S1', 'S2'), (XR, 'S3', 'S4')):
        dh, sh = mosfet(ax, x, SH[0], hi_name, states[hi_name])
        dl, sl = mosfet(ax, x, SH[1], lo_name, states[lo_name])
        if coss_map:
            coss(ax, x, SH[0], 1.30, coss_map.get(hi_name))
            coss(ax, x, SH[1], 1.30, coss_map.get(lo_name))
        S.wire(ax, [(x, HI), dh])
        S.wire(ax, [sl, (x, LO)])
        S.wire(ax, [sh, dl])                       # through the junction
    S.dot(ax, XL, YT)
    S.dot(ax, XR, YB)

    # tank out of the left junction, over the right leg, and back
    S.wire(ax, [(XL, YT), (XR - 0.17, YT)])
    hop(ax, XR, YT)
    S.wire(ax, [(XR + 0.17, YT), (XCR - 0.30, YT)])
    S.cap(ax, XCR, YT, 'C$_r$', tdy=0.42)
    S.wire(ax, [(XCR + 0.30, YT), (XLR - 0.33, YT)])
    S.ind(ax, XLR, YT, 'L$_r$', tdy=0.40)
    S.wire(ax, [(XLR + 0.33, YT), (XTR - 0.30, YT)])
    S.shunt(ax, XLM, YT, YB, 'ind', 'L$_m$', frac=0.62, tdx=0.22)
    S.dot(ax, XLM, YT)
    S.dot(ax, XLM, YB)
    S.wire(ax, [(XR, YB), (XTR - 0.30, YB)])

    t = S.xfmr(ax, XTR, (YT + YB) / 2.0, hp=YT - YB, hs=YT - YB, gap=0.30)
    S.label(ax, XTR - 0.30, YB - 0.44, 'N$_p$', size=10)
    S.label(ax, XTR + 0.30, YB - 0.44, 'N$_s$', size=10)

    # secondary: bridge rectifier, output capacitor, load
    S.wire(ax, [(XD1, VP), (XCO, VP)])
    S.wire(ax, [(XD1, VN), (XCO, VN)])
    S.wire(ax, [t['s_top'], (XD1, YT)])
    S.wire(ax, [t['s_bot'], (XD1 - 0.17, YB)])
    hop(ax, XD1, YB)
    S.wire(ax, [(XD1 + 0.17, YB), (XD2, YB)])
    S.dot(ax, XD1, YT)
    S.dot(ax, XD2, YB)

    for x, ymid, up_name, dn_name in ((XD1, YT, 'D1', 'D2'),
                                      (XD2, YB, 'D3', 'D4')):
        a, b = S.diode(ax, x, (ymid + VP) / 2.0, up_name, horiz=False, s=0.26,
                       color=NAVY if states[up_name] else OFFW)
        S.wire(ax, [(x, ymid), a], color=NAVY if states[up_name] else OFFW)
        S.wire(ax, [b, (x, VP)], color=NAVY if states[up_name] else OFFW)
        c, d = S.diode(ax, x, (ymid + VN) / 2.0, dn_name, horiz=False, s=0.26,
                       color=NAVY if states[dn_name] else OFFW)
        S.wire(ax, [(x, VN), c], color=NAVY if states[dn_name] else OFFW)
        S.wire(ax, [d, (x, ymid)], color=NAVY if states[dn_name] else OFFW)

    S.shunt(ax, XCO, VP, VN, 'cap', 'C$_o$', frac=0.26, tdx=0.26)
    S.wire(ax, [(XCO, VP), (14.30, VP)])
    S.wire(ax, [(XCO, VN), (14.30, VN)])
    S.shunt(ax, 14.30, VP, VN, 'res', frac=0.30, tdx=0.24)
    S.label(ax, 14.62, (VP + VN) / 2.0, 'V$_o$', ha='left', size=10.5,
            weight='bold')
    return t


# ------------------------------------------------------------ the 8 modes
#  Every path below was derived from the full bridge, not translated from a
#  half bridge.  The direction is the same one all through a transition:
#  the tank current does not reverse because a switch opened.
P_HI, P_LO = (0.55, HI), (0.55, LO)
A, B = (XL, YT), (XR, YB)
NP_T, NP_B = (XTR - 0.30, YT), (XTR - 0.30, YB)
NS_T, NS_B = (XTR + 0.30, YT), (XTR + 0.30, YB)
LM_T, LM_B = (XLM, YT), (XLM, YB)

def bd(x, y, h=1.30, w=0.62):
    """The body-diode detour round one device, bottom terminal to top.

    In intervals 4 and 8 the channel is off and the current is in the diode,
    so the highlight has to go round the flank rather than through the box.
    """
    xd, ye = x + w / 2 + 0.34, h / 2 - 0.10
    return [(x, y - h / 2), (x, y - ye), (xd, y - ye), (xd, y + ye),
            (x, y + ye), (x, y + h / 2)]


# primary, first half: out of the left junction, back into the right one
PRI_FWD_XFMR = [P_HI, (XL, HI), A, NP_T, NP_B, B, (XR, LO), P_LO]
PRI_FWD_LM = [P_HI, (XL, HI), A, LM_T, LM_B, B, (XR, LO), P_LO]
PRI_FWD_DIODE = ([P_LO, (XL, LO)] + bd(XL, SH[1]) + [A, LM_T, LM_B, B]
                 + bd(XR, SH[0]) + [(XR, HI), P_HI])
# primary, second half: the mirror image
PRI_REV_XFMR = [P_HI, (XR, HI), B, NP_B, NP_T, A, (XL, LO), P_LO]
PRI_REV_LM = [P_HI, (XR, HI), B, LM_B, LM_T, A, (XL, LO), P_LO]
PRI_REV_DIODE = ([P_LO, (XR, LO)] + bd(XR, SH[1]) + [B, LM_B, LM_T, A]
                 + bd(XL, SH[0]) + [(XL, HI), P_HI])

# secondary: D1+D4 when current enters the primary dot, D2+D3 when it leaves
SEC_14 = [NS_T, (XD1, YT), (XD1, VP), (XCO, VP), (14.30, VP),
          (14.30, VN), (XCO, VN), (XD2, VN), (XD2, YB), NS_B]
SEC_23 = [NS_B, (XD2, YB), (XD2, VP), (XCO, VP), (14.30, VP),
          (14.30, VN), (XCO, VN), (XD1, VN), (XD1, YT), NS_T]

HOPS[:] = [(XR, YT), (XD1, YB)]

ON, OFF = 'on', 'off'
MODES = [
    dict(n=1, t='POWER DELIVERY', sub='S1, S4 on  ·  D1, D4 conduct',
         sw=dict(S1=ON, S2=OFF, S3=OFF, S4=ON), d=(1, 0, 0, 1),
         pri=PRI_FWD_XFMR, load=True, lm=True, sec=SEC_14,
         say='The tank rings at f$_r$. L$_m$ is clamped by the output, so '
             'i$_{Lm}$ ramps straight and the difference i$_{Lr}$ - i$_{Lm}$ '
             'is the half sine that crosses to the secondary.'),
    dict(n=2, t='FREEWHEELING', sub='S1, S4 STILL on  ·  secondary off',
         sw=dict(S1=ON, S2=OFF, S3=OFF, S4=ON), d=(0, 0, 0, 0),
         pri=PRI_FWD_LM, load=False, lm=False, sec=None,
         say='i$_{Lr}$ has fallen to i$_{Lm}$, so nothing is left for the '
             'secondary and every rectifier is off. L$_m$ is free again and '
             'the tank rings at f$_o$. Same two switches, no power.'),
    dict(n=3, t='DEAD TIME (a)', sub='all four off  ·  C$_{oss}$ swaps '
                                     'the midpoints over',
         sw=dict(S1='coss', S2='coss', S3='coss', S4='coss'), d=(0, 0, 0, 0),
         pri=PRI_FWD_LM, load=False, lm=False, sec=None,
         coss=dict(S1='charge', S4='charge', S2='discharge', S3='discharge'),
         swing=(':  V$_{in}$ $\\rightarrow$ 0', ':  0 $\\rightarrow$ V$_{in}$'),
         say='The same magnetising current keeps flowing and has nowhere to '
             'go but the device capacitances. Node A falls from V$_{in}$ to '
             '0 and node B rises from 0 to V$_{in}$.'),
    dict(n=4, t='DEAD TIME (b)  —  ZVS', sub='body diodes of S2 and S3 '
                                                 'clamp',
         sw=dict(S1=OFF, S2='diode', S3='diode', S4=OFF), d=(0, 0, 0, 0),
         pri=PRI_FWD_DIODE, load=False, lm=False, sec=None,
         heads=(8, 10, 18),
         zvs='S2 and S3 now stand at V$_{ds}$ = 0.\nGATE THEM ON HERE.',
         say='Once the swing finishes the current cannot stop, so it takes '
             'the body diodes of the pair that is about to turn on. Their '
             'V$_{ds}$ is zero: turn on now and the turn-on loss is zero.'),
    dict(n=5, t='POWER DELIVERY', sub='S2, S3 on  ·  D2, D3 conduct',
         sw=dict(S1=OFF, S2=ON, S3=ON, S4=OFF), d=(0, 1, 1, 0),
         pri=PRI_REV_XFMR, load=True, lm=True, sec=SEC_23,
         say='The mirror image of interval 1. For the first moments after '
             'turn-on the old current is still running the other way through '
             'the two channels; power delivery starts when i$_{Lr}$ '
             'reverses.'),
    dict(n=6, t='FREEWHEELING', sub='S2, S3 STILL on  ·  secondary off',
         sw=dict(S1=OFF, S2=ON, S3=ON, S4=OFF), d=(0, 0, 0, 0),
         pri=PRI_REV_LM, load=False, lm=False, sec=None,
         say='The mirror image of interval 2, and the one that is easy to '
             'miss because it sits at the right-hand edge of a waveform '
             'plot. Both halves have one.'),
    dict(n=7, t='DEAD TIME (a)', sub='all four off  ·  C$_{oss}$ swaps '
                                     'the midpoints back',
         sw=dict(S1='coss', S2='coss', S3='coss', S4='coss'), d=(0, 0, 0, 0),
         pri=PRI_REV_LM, load=False, lm=False, sec=None,
         coss=dict(S2='charge', S3='charge', S1='discharge', S4='discharge'),
         swing=(':  0 $\\rightarrow$ V$_{in}$', ':  V$_{in}$ $\\rightarrow$ 0'),
         say='The mirror image of interval 3. Node B falls and node A rises, '
             'and the charge is moved by the magnetising current again.'),
    dict(n=8, t='DEAD TIME (b)  —  ZVS', sub='body diodes of S1 and S4 '
                                                 'clamp',
         sw=dict(S1='diode', S2=OFF, S3=OFF, S4='diode'), d=(0, 0, 0, 0),
         pri=PRI_REV_DIODE, load=False, lm=False, sec=None,
         heads=(8, 10, 18),
         zvs='S1 and S4 now stand at V$_{ds}$ = 0.\nGATE THEM ON HERE.',
         say='The mirror image of interval 4, and the period closes. ZVS '
             'happens twice per period, in intervals 4 and 8 - and in none '
             'of the other six.'),
]


def panel(ax, m):
    st = dict(m['sw'])
    for k, v in zip(('D1', 'D2', 'D3', 'D4'), m['d']):
        st[k] = bool(v)
    _skeleton(ax, st, m.get('coss'))

    path(ax, m['pri'], load=m['load'], heads=m.get('heads', (2, 4, 6)))
    if m['lm']:                       # the magnetising branch, split off
        path(ax, [LM_T, LM_B] if m['pri'] is PRI_FWD_XFMR else [LM_B, LM_T],
             load=False, heads=(1,), lw=3.0)
    if m['sec']:
        path(ax, m['sec'], load=True, heads=(2, 5, 8))

    sa, sb = m.get('swing', ('', ''))
    S.label(ax, XL + 0.20, YT + 0.36, 'A' + sa, size=10.5, weight='bold',
            color=PUR, ha='left')
    S.label(ax, XR + 0.20, YB - 0.40, 'B' + sb, size=10.5, weight='bold',
            color=PUR, ha='left')
    if m.get('coss'):
        ax.text(7.7, 0.55, 'Every channel is off. The current is in the four '
                'C$_{oss}$,\nand what it is doing is moving the two '
                'midpoints across.', ha='center', va='center', fontsize=11,
                color=GREY, zorder=9,
                bbox=dict(boxstyle='round,pad=0.45', fc='white', ec=OFFW,
                          lw=1.6))
    if m.get('zvs'):
        ax.text(7.7, 0.55, m['zvs'], ha='center', va='center', fontsize=11,
                color=GRN, fontweight='bold', zorder=9,
                bbox=dict(boxstyle='round,pad=0.45', fc='white', ec=GRN,
                          lw=1.8))
    ax.text(0.05, 8.72, '%d' % m['n'], ha='left', va='center', fontsize=20,
            color=MAG, fontweight='bold')
    ax.text(0.85, 8.78, m['t'], ha='left', va='center', fontsize=14.5,
            color=NAVY, fontweight='bold')
    ax.text(0.87, 8.10, m['sub'], ha='left', va='center', fontsize=11,
            color=GREY)


# ------------------------------------------------------- the waveform strip
#  Built piecewise from what each interval IS, not sketched by hand:
#    power delivery  L_m is clamped, so i_Lm is a straight ramp and the
#                    difference i_Lr - i_Lm is a half sine of length T_r/2
#    freewheeling    i_Lr = i_Lm and the tank rings at f_o
#    dead time       the same current, near enough constant
#  The amplitudes are the design's own I_Lr,pk and I_Lm,pk.
def _timeline(fsw_over_fr, td_draw):
    """-> the eight interval edges, as fractions of one switching period."""
    t1 = 0.5 * fsw_over_fr                       # power delivery = T_r / 2
    t3 = td_draw * 0.40                          # C_oss swing
    t4 = td_draw - t3                            # body-diode clamp
    t2 = 0.5 - t1 - td_draw                      # freewheeling
    e = [0.0, t1, t1 + t2, t1 + t2 + t3, 0.5]
    return e + [x + 0.5 for x in e[1:]]


def _halfwave(t, lam, fsw_over_fr, e, ilm_pk, io_pk):
    """i_Lm and i_Lr over the first half period, t in [0, 0.5].

    The freewheeling arc RISES; it does not decay.  Written the other way
    round first, and the reference waveform says otherwise: once the
    secondary stops conducting the tank is (L_r + L_m) with C_r and it is
    still on the rising side of that much slower ring, so the current goes
    on climbing and peaks at the end of the half period.  The kink at the
    join is real - the effective inductance jumps from L_r to L_r + L_m the
    moment the rectifiers stop clamping L_m.
    """
    t1, t2e = e[1], e[4]
    fo_fsw = np.sqrt(lam / (1.0 + lam)) / fsw_over_fr
    ph = 2 * np.pi * (t2e - t1) * fo_fsw           # how far along the f_o ring
    join = ilm_pk * np.cos(ph)                     # i_Lm where the ramp ends
    ilm = np.where(t <= t1,
                   -ilm_pk + (ilm_pk + join) * t / t1,
                   ilm_pk * np.cos(2 * np.pi * np.clip(t2e - t, 0, None)
                                   * fo_fsw))
    io = np.where(t <= t1, io_pk * np.sin(np.pi * np.clip(t, 0, t1) / t1), 0.0)
    return ilm, ilm + io, io


def _solve_io(lam, fsw_over_fr, e, ilm_pk, ilr_pk):
    """The load component whose sum with i_Lm peaks at the design I_Lr,pk."""
    t = np.linspace(0.0, e[1], 2000)
    lo, hi = 0.0, 4.0 * ilr_pk
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        pk = _halfwave(t, lam, fsw_over_fr, e, ilm_pk, mid)[1].max()
        lo, hi = (mid, hi) if pk < ilr_pk else (lo, mid)
    return 0.5 * (lo + hi)


BANDS = [('1', 'power delivery', MAG), ('2', 'freewheeling', CYA),
         ('3', '', GREY), ('4', '', GRN),
         ('5', 'power delivery', MAG), ('6', 'freewheeling', CYA),
         ('7', '', GREY), ('8', '', GRN)]


def _step(T, e, lo, hi):
    """node A: V_in through 1-2, down in 3, 0 through 4-6, up in 7, V_in in 8.

    Writing this as one np.where chain lost the last interval - the node came
    back down at the end of 7 because nothing held it.  Explicit segments.
    """
    v = np.zeros_like(T)
    v[(T >= e[0]) & (T < e[2])] = 1.0
    m = (T >= e[2]) & (T <= e[3])
    v[m] = 1.0 - (T[m] - e[2]) / (e[3] - e[2])
    m = (T >= e[6]) & (T <= e[7])
    v[m] = (T[m] - e[6]) / (e[7] - e[6])
    v[T > e[7]] = 1.0
    return lo + (hi - lo) * v


def waveforms(axes, lam, fsw_over_fr, ilr_pk, ilm_pk, td_draw=0.045):
    e = _timeline(fsw_over_fr, td_draw)
    io_pk = _solve_io(lam, fsw_over_fr, e, ilm_pk, ilr_pk)
    t = np.linspace(0.0, 0.5, 4000)
    ilm, ilr, io = _halfwave(t, lam, fsw_over_fr, e, ilm_pk, io_pk)
    T = np.concatenate([t, t + 0.5])
    ILM = np.concatenate([ilm, -ilm])
    ILR = np.concatenate([ilr, -ilr])
    IO = np.concatenate([io, io])                # rectified, so always up

    ag, av, ai, ar = axes
    for k, (num, name, col) in enumerate(BANDS):
        x0, x1 = e[k], e[k + 1]
        for ax in axes:
            ax.axvspan(x0, x1, color=col, alpha=0.09 if k % 2 == 0 else 0.16,
                       lw=0)
        ag.text((x0 + x1) / 2.0, 2.28, num, ha='center', va='center',
                fontsize=12, fontweight='bold', color='white', zorder=6,
                bbox=dict(boxstyle='circle,pad=0.26', fc=col, ec='none'))
        if name:
            ag.text((x0 + x1) / 2.0, 1.66, name, ha='center', va='center',
                    fontsize=10.5, color=col, fontweight='bold')
    for a, b in ((3, 4), (7, 8)):
        xm = (e[a - 1] + e[b]) / 2.0
        ag.annotate('', xy=(e[a - 1], 1.60), xytext=(e[b], 1.60),
                    arrowprops=dict(arrowstyle='-', color=GREY, lw=1.3))
        if a == 3:          # saying it twice just runs off the right edge
            ag.text(xm, 1.16, 'dead time\n(b) is the ZVS window',
                    ha='center', va='center', fontsize=8.8, color=GREY,
                    linespacing=1.3)

    # gates
    def sq(on0, on1):
        return np.where((T >= on0) & (T < on1), 1.0, 0.0)
    ag.plot(T, 0.50 * sq(e[0], e[2]) + 0.22, color=NAVY, lw=2.2)
    ag.plot(T, 0.50 * sq(e[4], e[6]) - 0.58, color=PUR, lw=2.2)
    ag.text(-0.010, 0.47, 'S1, S4', ha='right', va='center', fontsize=10.5,
            color=NAVY, fontweight='bold')
    ag.text(-0.010, -0.33, 'S2, S3', ha='right', va='center', fontsize=10.5,
            color=PUR, fontweight='bold')
    ag.set_ylim(-0.95, 2.72)

    # the two bridge midpoints - this is where ZVS is visible on a scope
    va = _step(T, e, 0.0, 1.0)
    av.plot(T, va, color=NAVY, lw=2.3, label='node A')
    av.plot(T, 1.0 - va, color=PUR, lw=2.3, ls='--', label='node B')
    av.set_yticks([0, 1])
    av.set_yticklabels(['0', 'V$_{in}$'])
    av.set_ylim(-0.32, 1.70)
    av.legend(loc='upper left', fontsize=9, ncol=2, framealpha=0.92)
    av.annotate('S2, S3 reach V$_{ds}$ = 0', xy=(e[3], 0.04),
                xytext=(e[3] + 0.035, 0.62), fontsize=9.5, color=GRN,
                arrowprops=dict(arrowstyle='-|>', color=GRN, lw=1.5))
    av.annotate('S1, S4 reach V$_{ds}$ = 0', xy=(e[7] - 0.002, 0.96),
                xytext=(e[7] - 0.10, 1.46), fontsize=9.5, color=GRN,
                ha='right',
                arrowprops=dict(arrowstyle='-|>', color=GRN, lw=1.5))

    # tank and magnetising current
    ai.axhline(0, color=GREY, lw=0.9)
    ai.plot(T, ILR, color=MAG, lw=2.5, label='i$_{Lr}$  tank')
    ai.plot(T, ILM, color=CYA, lw=2.3, ls='--', label='i$_{Lm}$  magnetising')
    ai.set_ylabel('tank current  [A]')
    ai.legend(loc='upper right', fontsize=9, ncol=2, framealpha=0.92)
    ai.set_ylim(-1.30 * ilr_pk, 1.78 * ilr_pk)
    ai.annotate('one current from here on:\ni$_{Lr}$ = i$_{Lm}$, nothing left '
                'for the secondary', xy=(e[1], ilm_pk * 1.02),
                xytext=(e[1] - 0.30, 1.30 * ilr_pk), fontsize=9.5,
                color=NAVY, ha='left', linespacing=1.25,
                arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.5))

    # what the rectifiers carry
    ar.axhline(0, color=GREY, lw=0.9)
    for lo, hi, col, nm in ((0.0, 0.5, MAG, 'D1 + D4'),
                            (0.5, 1.0, PUR, 'D2 + D3')):
        m = (T >= lo) & (T <= hi)
        ar.fill_between(T[m], 0, IO[m], color=col, alpha=0.22, lw=0)
        ar.plot(T[m], IO[m], color=col, lw=2.3)
        ar.text(lo + e[1] / 2.0, io_pk * 1.13, nm, ha='center', fontsize=10.5,
                color=col, fontweight='bold')
    ar.set_ylim(-0.10 * io_pk, 1.52 * io_pk)
    ar.set_ylabel('rectifier  [A]')
    ar.set_xlabel('one switching period')

    for ax in axes:
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        for sp in ('top', 'right', 'bottom'):
            ax.spines[sp].set_visible(False)
    ag.set_yticks([])
    ag.spines['left'].set_visible(False)
    return e, io_pk


# ------------------------------------------------------------- the sheets
LEGEND = [('load current  -  power crosses to the secondary', MAG, '-'),
          ('magnetising current only  -  nothing crosses', CYA, (0, (4, 2.4))),
          ('gated on', YEL, None),
          ('body diode conducting  -  V$_{ds}$ = 0, the ZVS window', GRN,
           None)]
LEG_X = (0.030, 0.310, 0.560, 0.650)


def _legend(fig, y=0.012):
    for x, (what, col, ls) in zip(LEG_X, LEGEND):
        if ls is None:
            fig.patches.append(plt.Rectangle(
                (x, y + 0.003), 0.015, 0.013, transform=fig.transFigure,
                fc=col if col is YEL else 'white', ec=col, lw=2.0,
                zorder=5, clip_on=False))
            dx = 0.021
        else:
            fig.add_artist(plt.Line2D([x, x + 0.026], [y + 0.010] * 2,
                                      transform=fig.transFigure, color=col,
                                      lw=3.2, ls=ls, clip_on=False))
            dx = 0.032
        fig.text(x + dx, y + 0.010, what, fontsize=9.6, color=GREY,
                 va='center')


def sheet(nums, out, dpi=150):
    """Four panels, two by two, with the colour key underneath."""
    fig, axs = plt.subplots(2, 2, figsize=(17.2, 9.6))
    for ax, n in zip(axs.ravel(), nums):
        panel(ax, MODES[n - 1])
    fig.subplots_adjust(left=0.004, right=0.996, top=0.99, bottom=0.045,
                        wspace=0.03, hspace=0.05)
    _legend(fig)
    fig.savefig(out, dpi=dpi, facecolor='white')
    plt.close(fig)
    return out


def build(out_dir, dpi=150):
    """The three sheets. Numbers come from the design, never from typing.

    lambda and the two current peaks are this design's own, taken at the
    low-line corner where l6790 puts them.  f_sw / f_r is drawn at 0.70 and
    the dead time wider than scale, both for legibility, and the caption has
    to say so.
    """
    import figs                                   # the design point
    from l6790 import sweep
    R = figs.R
    _, agg = sweep(R, R['Vin_min'], N=721)

    fig, axes = plt.subplots(4, 1, figsize=(13.2, 8.8), sharex=True,
                             gridspec_kw=dict(height_ratios=[1.25, 1.0,
                                                             1.4, 0.9]))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.985, bottom=0.075,
                        hspace=0.18)
    waveforms(axes, R['lam_a'], 0.70, agg['comp_pk'], agg['ILm_pk'])
    w = os.path.join(out_dir, 'an_modes_wave.png')
    fig.savefig(w, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    return [w,
            sheet([1, 2, 3, 4], os.path.join(out_dir, 'an_modes_1234.png'),
                  dpi),
            sheet([5, 6, 7, 8], os.path.join(out_dir, 'an_modes_5678.png'),
                  dpi)]


if __name__ == '__main__':
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else '.'
    for f in build(d):
        print('  %-24s %6.1f KB' % (os.path.basename(f),
                                    os.path.getsize(f) / 1024))
