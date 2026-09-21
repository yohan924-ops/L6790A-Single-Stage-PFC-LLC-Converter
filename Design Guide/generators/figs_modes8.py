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

The first cut drew each switch as a labelled box and leaned on schem.py for
the rest.  It was not a schematic: no MOSFET symbol at all, an output
capacitor with plates three times the size of C_r's, a transformer whose
coils sat so close to L_m that the three read as one row of coils, and
callouts written straight over the wiring.  Everything a panel draws is
therefore defined here, to one proportion table, and every label has a
reserved place that no wire and no highlight runs through.

Each switch is a cluster of three symbols in parallel - the MOSFET, its
body diode, its C_oss - present in every panel and coloured by what it is
doing.  That is what gives intervals 4 and 8 somewhere to land.

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
import matplotlib.patheffects as pe
from matplotlib.patches import Rectangle, FancyArrowPatch, FancyBboxPatch

#  The symbols live in schemx.py so the rest of the note draws the same
#  MOSFET, the same windings and the same current highlight as these panels.
from schemx import (NAVY, YEL, MAG, CYA, GRN, PUR, GREY, LT, OFF_C, LW, BRK,
                    wire, dot, txt, vcap, hcap, coil_pts, hcoil_pts, coil,
                    hcoil, vdiode, resbox, hop, mosfet, path, register)

# ------------------------------------------------------------- the geometry
#  One proportion table.  Nothing below computes a coordinate twice, and the
#  current paths are built from these names, so moving anything moves the
#  highlights with it.
HI, LO = 7.70, 0.30                 # primary rails
XL, XR = 1.95, 5.80                 # the two leg wires
SH = (6.20, 1.70)                   # switch centres, high and low
DEVH = 1.80                         # drain node to source node
YT, YB = 4.75, 2.95                 # tank goes out on YT, comes back on YB
XCR, XLR, XLM, XTR = 8.70, 10.05, 11.30, 12.75
YMID = (YT + YB) / 2.0
VP, VN = YMID + 2.60, YMID - 2.60   # output rails, symmetric about the tank
#  Windings sit close to the core - a transformer symbol with a gap wider
#  than its own turns reads as two unrelated inductors.  The lead lines are
#  placed so the turns stop about one turn-radius short of the core bars.
XP = XTR - 0.34                     # primary lead line, turns face the core
XS = XTR + 0.34                     # secondary lead line, turns face it too
LEAD = 0.06                         # straight bit before the first turn
#  Turn counts are picked so every winding on the sheet has a turn radius
#  between 0.13 and 0.15 - fewer, bigger turns read at the size a panel is
#  actually printed, where eight primary turns came out as a fine ripple.
NP_T_N, NS_T_N = 6, 3               # turns drawn: primary, each half of N_s
#  Centre tap, the way this design actually rectifies: the tap is V_o+ and
#  the two winding ends are pulled to the return through one device each.
#  Order matters - with the near leg fed from the LOWER end and the far one
#  from the upper, the only crossing left in the whole secondary is the
#  tap's riser under the upper end's wire.
XQ1, XCT, XQ2 = 14.70, 15.80, 16.90
XCO, XLD = 18.25, 19.65
XEND = XLD

DX_D, DX_C = 0.80, 1.50             # body diode and C_oss, right of the leg
XGATE = 1.00                        # gate lead reaches this far left


def _skeleton(ax, states, parts=True):
    """Everything that is the same in every panel.

    `parts` draws each switch's body diode and C_oss beside it.  The mode
    panels need them, because intervals 3, 4, 7 and 8 are about nothing
    else.  A figure that is only saying what an LLC stage IS does not, and
    showing them there raises a question chapter 2 has not reached yet - so
    that figure reuses this drawing with parts off rather than keeping a
    second, half-bridge copy of the same converter.
    """
    ax.set_xlim(-0.75, XEND + 2.05)
    ax.set_ylim(-1.75, 10.30)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')
    for sp in ax.spines.values():
        sp.set_visible(False)

    # ---- primary rails and the two legs
    x_rail = (XR + DX_C if parts else XR) + 0.85
    wire(ax, [(0.25, HI), (x_rail, HI)])
    wire(ax, [(0.25, LO), (x_rail, LO)])
    dot(ax, 0.25, HI)
    dot(ax, 0.25, LO)
    txt(ax, 0.10, HI + 0.38, 'V$_{in}$', size=11.5, weight='bold', ha='left')
    txt(ax, 0.10, LO - 0.38, '0', size=11.5, ha='left')

    for x, hi_name, lo_name in ((XL, 'S1', 'S2'), (XR, 'S3', 'S4')):
        dh, _ = mosfet(ax, x, SH[0], hi_name, states[hi_name],
                       body=parts, coss=parts)
        _, sl = mosfet(ax, x, SH[1], lo_name, states[lo_name],
                       body=parts, coss=parts)
        wire(ax, [(x, HI), dh])
        wire(ax, [sl, (x, LO)])
        wire(ax, [(x, SH[0] - DEVH / 2), (x, SH[1] + DEVH / 2)])
        #  Each leg is a T on its rail.  Every other T in this drawing
        #  carries a junction dot, and figcheck found these four bare.
        dot(ax, x, HI)
        dot(ax, x, LO)
    dot(ax, XL, YT)
    dot(ax, XR, YB)

    # ---- the tank: out of the left junction, over the right leg, and back
    wire(ax, [(XL, YT), (XR - 0.20, YT)])
    hop(ax, XR, YT)
    wire(ax, [(XR + 0.20, YT), (XCR - 0.11, YT)])
    hcap(ax, XCR, YT, 0.30)
    txt(ax, XCR, YT + 0.66, 'C$_r$', size=11.5)
    wire(ax, [(XCR + 0.11, YT), (XLR - 0.45, YT)])
    hcoil(ax, XLR, YT, 0.90, 3)
    txt(ax, XLR, YT + 0.66, 'L$_r$', size=11.5)
    wire(ax, [(XLR + 0.45, YT), (XP, YT)])
    wire(ax, [(XR, YB), (XP, YB)])

    # L_m across the winding, bulging away from the transformer
    coil(ax, XLM, YB + 0.24, YT - 0.24, n=5, side=-1)
    wire(ax, [(XLM, YT), (XLM, YT - 0.24)])
    wire(ax, [(XLM, YB + 0.24), (XLM, YB)])
    dot(ax, XLM, YT)
    dot(ax, XLM, YB)
    txt(ax, XLM - 0.50, YMID, 'L$_m$', size=11.5, ha='right')

    # ---- the transformer, centre-tapped secondary
    for xx in (XTR - 0.13, XTR + 0.13):
        ax.plot([xx, xx], [YB - 0.38, YT + 0.38], color=GREY, lw=2.4, zorder=3)
    coil(ax, XP, YB + LEAD, YT - LEAD, n=NP_T_N, side=+1)
    wire(ax, [(XP, YB), (XP, YB + LEAD)])
    wire(ax, [(XP, YT - LEAD), (XP, YT)])
    # A dot beside a coil has to clear the widest loop AND stay nearer its
    # own coil than the next one; there is no such spot here.  Above the
    # terminal there is, and it is unambiguous.
    dot(ax, XP - 0.17, YT - 0.17, NAVY, 4.8)
    txt(ax, XP, YB - 0.70, 'N$_p$', size=11.5)

    coil(ax, XS, YMID + LEAD, YT - LEAD, n=NS_T_N, side=-1)
    coil(ax, XS, YB + LEAD, YMID - LEAD, n=NS_T_N, side=-1)
    wire(ax, [(XS, YB), (XS, YB + LEAD)])
    wire(ax, [(XS, YMID - LEAD), (XS, YMID + LEAD)])
    wire(ax, [(XS, YT - LEAD), (XS, YT)])
    # Both halves are drawn as separate windings, so both carry a polarity
    # dot.  They are one continuous winding in the same sense, so N_s2's
    # dot is at ITS start, which is the tap: the finish of N_s1.  That is
    # what makes the lower end conduct while the upper one blocks.  The
    # tap's own junction dot is on the lead line and sits clear of it.
    dot(ax, XS + 0.17, YT - 0.17, NAVY, 4.8)
    dot(ax, XS + 0.17, YMID - 0.20, NAVY, 4.8)
    dot(ax, XS, YMID)
    txt(ax, XS + 0.42, (YMID + YT) / 2.0, 'N$_{s1}$', size=11, ha='left')
    txt(ax, XS + 0.42, (YMID + YB) / 2.0, 'N$_{s2}$', size=11, ha='left')

    # ---- secondary: centre tap out to V_o+, one rectifier per winding end
    wire(ax, [(XS, YB), (XQ1, YB)])                       # lower end, near leg
    wire(ax, [(XS, YT), (XCT - 0.20, YT)])                # upper end, far leg
    hop(ax, XCT, YT)
    wire(ax, [(XCT + 0.20, YT), (XQ2, YT)])
    wire(ax, [(XS, YMID), (XCT, YMID), (XCT, VP)])        # the tap itself
    #  A dot means three or more wires meet.  There were three here that
    #  marked plain CORNERS - the tap riser turning onto the + rail, and
    #  each rectifier's top where one wire ends and the next begins - and
    #  a dot on a corner tells the reader nothing while looking exactly
    #  like the ones that do.  Only the true tee is marked.
    dot(ax, XQ2, VN)          # D2's return joins the - rail mid-run: a T
    # Set on one line it is wider than any gap left on this side, and
    # it landed on N_s2 twice and on the riser once. Two lines fit the
    # pocket between the winding labels and the riser.
    txt(ax, (XQ1 + XCT) / 2.0 - 0.10, YMID + 0.45, 'centre\ntap',
        size=9.6, color=GREY)
    wire(ax, [(XCT, VP), (XLD, VP)])
    wire(ax, [(XQ1, VN), (XLD, VN)])

    y_d = (VN + YB) / 2.0
    for x, ytop, nm, side in ((XQ1, YB, 'D1', -1), (XQ2, YT, 'D2', +1)):
        on = bool(states[nm])
        c = NAVY if on else OFF_C
        wire(ax, [(x, VN), (x, ytop)], c, 2.0 if on else 1.4)
        vdiode(ax, x, y_d, 0.28, up=True, color=c)
        txt(ax, x + side * 0.38, y_d, nm, size=11,
            ha='left' if side > 0 else 'right', color=NAVY if on else GREY)

    wire(ax, [(XCO, VN), (XCO, YMID - 0.12)])
    wire(ax, [(XCO, YMID + 0.12), (XCO, VP)])
    vcap(ax, XCO, YMID, 0.32)
    txt(ax, XCO + 0.48, YMID, 'C$_o$', size=11.5, ha='left')
    dot(ax, XCO, VP)
    dot(ax, XCO, VN)

    wire(ax, [(XLD, VN), (XLD, YMID - 0.58)])
    wire(ax, [(XLD, YMID + 0.58), (XLD, VP)])
    resbox(ax, XLD, YMID)
    txt(ax, XLD + 0.38, YMID, 'R$_o$', size=11.5, ha='left')
    xv = XLD + 1.30
    ax.add_patch(FancyArrowPatch((xv, VN), (xv, VP), arrowstyle='<|-|>',
                                 mutation_scale=12, color=GREY, lw=1.4,
                                 zorder=4, shrinkA=0, shrinkB=0))
    txt(ax, xv + 0.22, YMID, 'V$_o$', size=11.5, weight='bold', ha='left')
    txt(ax, XLD + 0.34, VP + 0.38, '+', size=13, weight='bold')
    txt(ax, XLD + 0.34, VN - 0.38, '−', size=14, weight='bold')


# ------------------------------------------------------------ current paths
#  Every path below was derived from the full bridge, not translated from a
#  half bridge.  The direction is the same one all through a transition:
#  the tank current does not reverse because a switch opened.
P_HI, P_LO = (0.25, HI), (0.25, LO)
A, B = (XL, YT), (XR, YB)
NP_T, NP_B = (XP, YT), (XP, YB)
NS_T, NS_B, NS_C = (XS, YT), (XS, YB), (XS, YMID)
LM_T, LM_B = (XLM, YT), (XLM, YB)
HOPS = [(XR, YT), (XCT, YT)]
#  Every winding the current can run through, as (x, ylo, yhi, turns, side)
#  for the vertical ones and (x, y, span, turns) for L_r.  A segment that
#  covers one of these is replaced by the winding's own polyline.
VCOILS = [(XLM, YB + 0.24, YT - 0.24, 5, -1),
          (XP, YB + LEAD, YT - LEAD, NP_T_N, +1),
          (XS, YMID + LEAD, YT - LEAD, NS_T_N, -1),
          (XS, YB + LEAD, YMID - LEAD, NS_T_N, -1)]
HCOILS = [(XLR, YT, 0.90, 3)]
register(HOPS, VCOILS, HCOILS)


def bd(x, y, h=DEVH):
    """The body-diode detour round one device, source node to drain node."""
    return [(x, y - h / 2), (x + DX_D, y - h / 2), (x + DX_D, y + h / 2),
            (x, y + h / 2)]


def cs(x, y, h=DEVH):
    """The C_oss detour round one device, source node to drain node.

    The dead time is the one interval in which NO channel conducts, so the
    current cannot be drawn down the leg the way intervals 1, 2, 5 and 6
    draw it.  It goes through the device capacitance - that is the whole
    mechanism, and a displacement current is a current: it passes between
    the plates.  Drawn down the leg instead, as it was, the picture shows
    current in a channel that the panel's own caption says is off.

    Same shape as bd(), one column further out.
    """
    return [(x, y - h / 2), (x + DX_C, y - h / 2), (x + DX_C, y + h / 2),
            (x, y + h / 2)]


# primary, first half: out of the left junction, back into the right one
PRI_FWD_XFMR = [P_HI, (XL, HI), A, NP_T, NP_B, B, (XR, LO), P_LO]
PRI_FWD_LM = [P_HI, (XL, HI), A, LM_T, LM_B, B, (XR, LO), P_LO]
PRI_FWD_DIODE = ([P_LO, (XL, LO)] + bd(XL, SH[1]) + [A, LM_T, LM_B, B]
                 + bd(XR, SH[0]) + [(XR, HI), P_HI])
#  Dead time, first half.  The tank current does not change direction when
#  the gates drop, so it still leaves node A and returns to node B - but it
#  now has to reach the rails through the capacitances, and it SPLITS:
#    upper   V_in rail -> C_oss(S1) -> A -> tank -> B -> C_oss(S3) -> V_in
#    lower   0 rail    -> C_oss(S2) -> A -> tank -> B -> C_oss(S4) -> 0
#  Both halves are drawn, because leaving one out would say the midpoint is
#  carried by one capacitor when it is carried by four.  Each capacitor's
#  own colour still says which way its V_ds is going.
COSS_FWD_HI = ([P_HI, (XL, HI)] + cs(XL, SH[0])[::-1] + [A, LM_T, LM_B, B]
               + cs(XR, SH[0]) + [(XR, HI), P_HI])
COSS_FWD_LO = ([P_LO, (XL, LO)] + cs(XL, SH[1]) + [A, LM_T, LM_B, B]
               + cs(XR, SH[1])[::-1] + [(XR, LO), P_LO])
COSS_HEADS = ((4, 0.50), (7, 0.34), (12, 0.50))

# primary, second half: the mirror image
PRI_REV_XFMR = [P_HI, (XR, HI), B, NP_B, NP_T, A, (XL, LO), P_LO]
PRI_REV_LM = [P_HI, (XR, HI), B, LM_B, LM_T, A, (XL, LO), P_LO]
PRI_REV_DIODE = ([P_LO, (XR, LO)] + bd(XR, SH[1]) + [B, LM_B, LM_T, A]
                 + bd(XL, SH[0]) + [(XL, HI), P_HI])
COSS_REV_HI = ([P_HI, (XR, HI)] + cs(XR, SH[0])[::-1] + [B, LM_B, LM_T, A]
               + cs(XL, SH[0]) + [(XL, HI), P_HI])
COSS_REV_LO = ([P_LO, (XR, LO)] + cs(XR, SH[1]) + [B, LM_B, LM_T, A]
               + cs(XL, SH[1])[::-1] + [(XL, LO), P_LO])

#  Secondary, centre tapped.  Current always LEAVES the tap into the load
#  and comes back through one rectifier into one winding end; which end is
#  set by the dot.  Current entering the primary dot leaves the secondary
#  dot, which is the tap for the lower half - so the LOWER end conducts in
#  the first half and the upper end in the second.
SEC_LO = [NS_C, (XCT, YMID), (XCT, VP), (XLD, VP), (XLD, VN), (XQ1, VN),
          (XQ1, YB), NS_B, NS_C]
SEC_HI = [NS_C, (XCT, YMID), (XCT, VP), (XLD, VP), (XLD, VN), (XQ2, VN),
          (XQ2, YT), NS_T, NS_C]


ON, OFF = 'on', 'off'
MODES = [
    dict(n=1, t='POWER DELIVERY', sub='S1, S4 on  ·  D1 conducts  ·  lower half of N$_s$',
         sw=dict(S1=ON, S2=OFF, S3=OFF, S4=ON), d=(1, 0),
         pri=PRI_FWD_XFMR, load=True, lm=True, sec=SEC_LO,
         note=('L$_m$ is clamped, so i$_{Lm}$ is a straight ramp and i$_{Lr}$ - i$_{Lm}$ is the half sine that crosses.\nWhat is traced is the load component; i$_{Lm}$ flows in L$_m$ too, but it reverses inside this interval.'),
         say='The tank rings at f$_r$. L$_m$ is clamped by the output, so '
             'i$_{Lm}$ ramps straight and the difference i$_{Lr}$ - i$_{Lm}$ '
             'is the half sine that crosses to the secondary.'),
    dict(n=2, t='FREEWHEELING', sub='S1, S4 STILL on  ·  secondary off',
         sw=dict(S1=ON, S2=OFF, S3=OFF, S4=ON), d=(0, 0),
         pri=PRI_FWD_LM, load=False, lm=False, sec=None,
         note='i$_{Lr}$ has fallen to i$_{Lm}$. Every rectifier is off, L$_m$ is free again, and the tank rings at f$_o$.',
         say='i$_{Lr}$ has fallen to i$_{Lm}$, so nothing is left for the '
             'secondary and every rectifier is off. L$_m$ is free again and '
             'the tank rings at f$_o$. Same two switches, no power.'),
    dict(n=3, t='DEAD TIME (a)', sub='all four off  ·  C$_{oss}$ swaps '
                                     'the midpoints over',
         sw=dict(S1='charge', S4='charge', S2='discharge', S3='discharge'),
         d=(0, 0), pri=COSS_FWD_HI, pri_b=COSS_FWD_LO, heads=COSS_HEADS,
         load=False, lm=False, sec=None, coss=True,
         swing=(':  V$_{in}$ $\\rightarrow$ 0', ':  0 $\\rightarrow$ V$_{in}$'),
         note=('All four channels off: the current goes THROUGH the four C$_{oss}$, in two loops, one round each rail.\nThat is what carries the midpoints across.  Magenta: C$_{oss}$ charging, V$_{ds}$ rising;  cyan: discharging.'),
         say='The same magnetising current keeps flowing and has nowhere to '
             'go but the device capacitances. Node A falls from V$_{in}$ to '
             '0 and node B rises from 0 to V$_{in}$.'),
    dict(n=4, t='DEAD TIME (b)  —  ZVS', sub='body diodes of S2 and S3 '
                                                 'clamp',
         sw=dict(S1=OFF, S2='diode', S3='diode', S4=OFF), d=(0, 0),
         pri=PRI_FWD_DIODE, load=False, lm=False, sec=None,
         heads=((6, 0.62), (7, 0.45), (14, 0.55)),
         zvs='S2 and S3 now stand at V$_{ds}$ = 0.\nGATE THEM ON HERE.',
         note='V$_{ds}$ = 0 on S2 and S3 now, because their own body diodes are clamping them. Gate them on HERE.',
         say='Once the swing finishes the current cannot stop, so it takes '
             'the body diodes of the pair that is about to turn on. Their '
             'V$_{ds}$ is zero: turn on now and the turn-on loss is zero.'),
    dict(n=5, t='POWER DELIVERY', sub='S2, S3 on  ·  D2 conducts  ·  upper half of N$_s$',
         sw=dict(S1=OFF, S2=ON, S3=ON, S4=OFF), d=(0, 1),
         pri=PRI_REV_XFMR, load=True, lm=True, sec=SEC_HI,
         note=('The mirror of 1. Just after turn-on the old current still runs back through the two channels.\nAgain only the load component is traced - i$_{Lm}$ reverses inside this interval as well.'),
         say='The mirror image of interval 1. For the first moments after '
             'turn-on the old current is still running the other way through '
             'the two channels; power delivery starts when i$_{Lr}$ '
             'reverses.'),
    dict(n=6, t='FREEWHEELING', sub='S2, S3 STILL on  ·  secondary off',
         sw=dict(S1=OFF, S2=ON, S3=ON, S4=OFF), d=(0, 0),
         pri=PRI_REV_LM, load=False, lm=False, sec=None,
         note='The mirror of 2, and the easy one to miss:  it ends at the right-hand edge of a waveform plot.',
         say='The mirror image of interval 2, and the one that is easy to '
             'miss because it sits at the right-hand edge of a waveform '
             'plot. Both halves have one.'),
    dict(n=7, t='DEAD TIME (a)', sub='all four off  ·  C$_{oss}$ swaps '
                                     'the midpoints back',
         sw=dict(S2='charge', S3='charge', S1='discharge', S4='discharge'),
         d=(0, 0), pri=COSS_REV_HI, pri_b=COSS_REV_LO, heads=COSS_HEADS,
         load=False, lm=False, sec=None, coss=True,
         swing=(':  0 $\\rightarrow$ V$_{in}$', ':  V$_{in}$ $\\rightarrow$ 0'),
         note=('The mirror of 3. Node B falls, node A rises, and the same magnetising current moves the charge -\nthrough the capacitances again, never a channel.  Same colours:  magenta charging, cyan discharging.'),
         say='The mirror image of interval 3. Node B falls and node A rises, '
             'and the charge is moved by the magnetising current again.'),
    dict(n=8, t='DEAD TIME (b)  —  ZVS', sub='body diodes of S1 and S4 '
                                                 'clamp',
         sw=dict(S1='diode', S2=OFF, S3=OFF, S4='diode'), d=(0, 0),
         pri=PRI_REV_DIODE, load=False, lm=False, sec=None,
         heads=((7, 0.45), (9, 0.45), (14, 0.55)),
         zvs='S1 and S4 now stand at V$_{ds}$ = 0.\nGATE THEM ON HERE.',
         note='The same for S1 and S4, and the period closes. ZVS is in 4 and 8 - and in none of the other six.',
         say='The mirror image of interval 4, and the period closes. ZVS '
             'happens twice per period, in intervals 4 and 8 - and in none '
             'of the other six.'),
]


#  Reserved places for text.  A callout gets one of these and nothing else
#  is ever drawn in them, which is the only way a panel stays readable when
#  eight of them share one geometry.
NODE_A = (XL + 0.30, YT + 0.42)                  # above the tank wire
NODE_B = (XR + DX_C + 0.55, YB - 0.52)           # below the return wire


def panel(ax, m):
    st = dict(m['sw'])
    for k, v in zip(('D1', 'D2'), m['d']):
        st[k] = bool(v)
    _skeleton(ax, st)

    hd = m.get('heads', ((2, 0.90), (3, 0.45), (6, 0.90)))
    path(ax, m['pri'], load=m['load'], heads=hd)
    if m.get('pri_b'):
        #  the dead time has two loops, one round each rail
        path(ax, m['pri_b'], load=m['load'], heads=hd)
    if m['sec']:
        #  The last head sits early on the run back to the winding: at
        #  0.45 it landed on the 'centre tap' label in the second half.
        path(ax, m['sec'], load=True,
             heads=((2, 0.62), (4, 0.75), (7, 0.15)))

    sa, sb = m.get('swing', ('', ''))
    txt(ax, NODE_A[0], NODE_A[1], 'A' + sa, size=11, weight='bold', color=PUR,
        ha='left', halo=True)
    txt(ax, NODE_B[0], NODE_B[1], 'B' + sb, size=11, weight='bold', color=PUR,
        ha='left', halo=True)

    zvs = bool(m.get('zvs'))
    ax.text(-0.55, -1.02, m['note'], ha='left', va='center',
            fontsize=10.6, linespacing=1.45,
            color=GRN if zvs else GREY, fontweight='bold' if zvs else 'normal')

    ax.text(-0.55, 9.55, '%d' % m['n'], ha='left', va='center', fontsize=21,
            color=MAG, fontweight='bold')
    ax.text(0.30, 9.60, m['t'], ha='left', va='center', fontsize=15,
            color=NAVY, fontweight='bold')
    ax.text(0.32, 8.82, m['sub'], ha='left', va='center', fontsize=11.5,
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
    for lo, hi, col, nm in ((0.0, 0.5, MAG, 'D1'),
                            (0.5, 1.0, PUR, 'D2')):
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
LEGEND = [('load current', MAG, 'solid'),
          ('magnetising current only', CYA, 'dash'),
          ('gated on', YEL, 'fill'),
          ('body diode conducting = the ZVS window', GRN, 'outline'),
          ('C$_{oss}$ charging, V$_{ds}$ rising', MAG, 'cap'),
          ('C$_{oss}$ discharging', CYA, 'cap')]
LEG_X = (0.030, 0.144, 0.310, 0.397, 0.608, 0.726)


def _legend(fig, y=0.010):
    for x, (what, col, kind) in zip(LEG_X, LEGEND):
        if kind in ('solid', 'dash'):
            fig.add_artist(plt.Line2D(
                [x, x + 0.026], [y + 0.010] * 2, transform=fig.transFigure,
                color=col, lw=3.2, clip_on=False,
                ls='-' if kind == 'solid' else (0, (4, 2.4))))
            dx = 0.032
        elif kind == 'cap':
            for dy in (0.004, 0.016):
                fig.add_artist(plt.Line2D(
                    [x, x + 0.016], [y + dy] * 2, transform=fig.transFigure,
                    color=col, lw=2.4, clip_on=False))
            dx = 0.022
        else:
            fig.patches.append(plt.Rectangle(
                (x, y + 0.003), 0.015, 0.013, transform=fig.transFigure,
                fc=col if kind == 'fill' else 'white', ec=col, lw=2.0,
                zorder=5, clip_on=False))
            dx = 0.021
        fig.text(x + dx, y + 0.010, what, fontsize=9.6, color=GREY,
                 va='center')


def sheet_fig(nums):
    """Four panels, two by two, with the colour key underneath - the figure
    itself, so figcheck can read it the way it reads every other drawing."""
    fig, axs = plt.subplots(2, 2, figsize=(17.6, 10.4))
    #  Laid out first: symbol scale reads the axes' position, and adjusted
    #  afterwards the panels recorded a scale for a layout they never had.
    #  (The panels themselves draw at explicit sizes, so nothing moves.)
    fig.subplots_adjust(left=0.004, right=0.996, top=0.995, bottom=0.042,
                        wspace=0.02, hspace=0.02)
    for ax, n in zip(axs.ravel(), nums):
        panel(ax, MODES[n - 1])
    _legend(fig)
    return fig


def sheet(nums, out, dpi=150):
    fig = sheet_fig(nums)
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
