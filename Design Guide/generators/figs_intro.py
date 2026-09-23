# -*- coding: utf-8 -*-
"""The background circuit figures for the application note.

They answer four questions a reader who has not built an LLC will ask before
any equation means anything:

  an_llc_stage   what an LLC converter physically is
  an_fha_steps   how that circuit becomes L_r, L_m, C_r and one resistor
  an_pfc_idea    what power factor correction is, and what it costs
  an_architectures  two stages against one, and where the buffer sits

Drawn here rather than taken from another vendor's application note, because
this document is distributed.
"""
import matplotlib.pyplot as plt
import numpy as np

import schem as S
from schem import NAVY, MAG, CYA, GRN, PUR, GREY, LT, YEL


# ------------------------------------------------------------------ 1
def an_llc_stage(save, foot):
    """What an LLC stage physically is - the converter this note designs.

    This used to be a half bridge with its own hand-built centre tap, which
    was a second drawing of a converter the note already draws properly:
    the mode panels' full bridge with a centre-tapped secondary.  Two
    drawings of one circuit drift apart, and this one had, down to a ground
    symbol the panels do not use - the panels name the return rail 0, which
    is what it is.  So this figure is now that drawing, with the switches
    at rest and the group names written above it.
    """
    import figs_modes8 as F
    fig, ax = plt.subplots(figsize=(9.35, 4.60))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.10)
    rest = dict(S1='plain', S2='plain', S3='plain', S4='plain',
                D1=True, D2=True)
    F._skeleton(ax, rest, parts=False, lm_dy=0.42)

    #  Group names go ABOVE the rails, in the band the panels leave empty
    #  for their step number and title.  Nothing of the circuit is up there.
    yl = F.HI + 1.05
    #  The four bands must not touch, or their rules read as one long line
    #  underneath every name - which is what the first version drew.
    #  Each band ends short of the next one's start.  When the
    #  transformer grew (2026-09-21) its band ran into both neighbours and
    #  the three rules read as one, so the edges are now the midpoints of
    #  the gaps between the groups, less a fixed clearance.
    G = 0.18
    m_tank_tr = (F.XLM + F.XP) / 2.0
    m_tr_rect = (F.XS + F.XQ1) / 2.0
    for x0, x1, nm, col in ((F.XL - 1.35, F.XR + 0.80, 'full bridge', GREY),
                            (F.XCR - 0.95, m_tank_tr - G, 'resonant tank',
                             CYA),
                            (m_tank_tr + G, m_tr_rect - G, 'transformer',
                             GREY),
                            (m_tr_rect + G, F.XQ2 + 0.80, 'rectifier', GREY)):
        S.label(ax, (x0 + x1) / 2.0, yl, nm, size=11.5, color=col)
        #  zorder 1.8: a rule under a group name is not a wire, and figcheck
        #  reads zorder-2 lines as wiring
        ax.plot([x0, x1], [yl - 0.42] * 2, color=col, lw=1.2, alpha=0.55,
                zorder=1.8)
    S.label(ax, F.XTR, F.YB - 1.15, 'n : 1', size=10.5, color=GREY)

    #  The tank band, behind everything, over the three reactive elements
    S.shade(ax, F.XCR - 0.95, F.YB - 0.95, F.XLM + 0.75, F.YT + 1.05,
            None, color=CYA, alpha=0.09)

    #  Every quantity Figure 2 plots, marked where it is (2026-09-23, user:
    #  "which is v_d, what is i_S1?").  Each arrow is the positive direction
    #  of that trace in Figure 2 and takes that trace's colour: i_S1 drain to
    #  source; i_Lr out of A into the tank; i_Lm down through L_m; each
    #  rectifier current in its forward direction; v_d = v_A - v_B, the
    #  bridge output, +V_in while S1 and S4 are on.  The callout that used to
    #  sit in the pocket between the legs said the same thing as v_d in
    #  words, so v_d replaces it.
    from matplotlib.patches import FancyArrowPatch

    def cur(p0, p1, name, col, at, ha):
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle='-|>',
                                     mutation_scale=13, color=col, lw=1.8,
                                     zorder=6, shrinkA=0, shrinkB=0))
        F.txt(ax, at[0], at[1], name, size=11, color=col, ha=ha)

    #  Alongside the device, not on the short lead under it: there the
    #  arrow was all head.  The switch symbol is drawn left of its leg, so
    #  the right side is free.
    cur((F.XL + 0.30, F.SH[0] + 0.62), (F.XL + 0.30, F.SH[0] - 0.62),
        'i$_{S1}$', NAVY, (F.XL + 0.48, F.SH[0]), 'left')
    xi = (F.XR + 0.20 + F.XCR - 0.30) / 2.0 + 0.45
    cur((xi - 0.32, F.YT + 0.30), (xi + 0.32, F.YT + 0.30), 'i$_{Lr}$', MAG,
        (xi, F.YT + 0.66), 'center')
    cur((F.XLM - 0.64, F.YMID + 0.02), (F.XLM - 0.64, F.YB + 0.24),
        'i$_{Lm}$', CYA, (F.XLM - 0.80, F.YMID - 0.40), 'right')
    #  Beside each diode, on the side its name is not
    y_d = (F.VN + F.YB) / 2.0
    for x, nm, sd in ((F.XQ1, 'i$_{D1}$', +1), (F.XQ2, 'i$_{D2}$', -1)):
        cur((x + sd * 0.62, y_d - 0.45), (x + sd * 0.62, y_d + 0.45), nm,
            GRN, (x + sd * 0.80, y_d), 'left' if sd > 0 else 'right')

    xv = F.XR + 1.00
    ax.add_patch(FancyArrowPatch((xv, F.YB + 0.12), (xv, F.YT - 0.12),
                                 arrowstyle='<|-|>', mutation_scale=12,
                                 color=GREY, lw=1.4, zorder=4, shrinkA=0,
                                 shrinkB=0))
    F.txt(ax, xv - 0.28, F.YT - 0.30, '+', size=12, weight='bold')
    F.txt(ax, xv - 0.28, F.YB + 0.30, '−', size=13, weight='bold')
    F.txt(ax, xv + 0.22, F.YMID, 'v$_d$', size=11.5, weight='bold',
          ha='left')
    #  the two bridge mid-points v_d is taken between - the names the mode
    #  panels give them
    F.txt(ax, F.XL - 0.30, F.YT, 'A', size=11, color=PUR, weight='bold',
          ha='right')
    F.txt(ax, F.XR - 0.30, F.YB, 'B', size=11, color=PUR, weight='bold',
          ha='right')

    foot(fig, 'Three reactive elements and a square wave v_d = v_A - v_B. '
              'The switches only set the frequency; the tank decides how '
              'much power flows and the transformer sets the voltage.')
    save(fig, 'an_llc_stage')


# ------------------------------------------------------------------ 2
def an_fha_steps(save, foot):
    """As built, referred, first harmonic: the three steps to M(f_n, Q).

    The panels are laid out BEFORE anything is drawn.  Symbol size reads
    the axes' position on the figure, and a tight_layout afterwards moved
    the panels under symbols sized for where they used to be.
    """
    fig, axs = plt.subplots(1, 3, figsize=(9.35, 2.60))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.04,
                        wspace=0.06)
    XS_, YS_, YR = 0.55, 1.1, -0.9              # source; the return rail
    YMID = (YS_ + YR) / 2.0                     # the source stands on this

    def drive(ax, kind):
        """The source, standing IN the left branch of the loop.

        It used to be wired out of its right side and down out of its
        bottom, which put the symbol itself on the top-left corner of the
        loop and left the reader looking for the corner (2026-09-22,
        user).  A two-terminal source belongs in a branch: terminals up
        and down, the loop square around it.

        -> the node on the top rail it feeds
        """
        f, r = (S.sqsrc, 0.38) if kind == 'sq' else (S.acsrc, 0.36)
        f(ax, XS_, YMID, None, r=r)
        S.wire(ax, [(XS_, YMID + r), (XS_, YS_)])
        S.wire(ax, [(XS_, YMID - r), (XS_, YR)])
        return (XS_, YS_)

    def series(ax, right, x_c, x_l, x_n):
        """source -> C_r -> L_r -> the node at x_n, dotted"""
        a, b = S.cap(ax, x_c, YS_, 'C$_r$', tdy=0.42)
        S.wire(ax, [right, a])
        c, d = S.ind(ax, x_l, YS_, 'L$_r$', s=0.8, tdy=0.36)
        S.wire(ax, [b, c])
        S.wire(ax, [d, (x_n, YS_)])
        S.dot(ax, x_n, YS_)
        #  L_m's name goes to the LEFT of its coil.  On the right it is in
        #  the channel between this coil and the transformer's primary
        #  lead, which is the narrowest part of the panel.
        S.shunt(ax, x_n, YS_, YR, 'ind', None, frac=0.4)
        S.label(ax, x_n - 0.30, (YS_ + YR) / 2.0, 'L$_m$', size=10,
                ha='right')
        S.dot(ax, x_n, YR)                       # L_m's foot is a T on the rail

    # ---- (a) as built
    ax = axs[0]
    S.frame(ax, -0.3, 7.6, -1.3, 3.5, '1   as built')
    top = drive(ax, 'sq')
    #  Everything to the left is packed closer than in panels 2 and 3,
    #  because the transformer needs the width: with the bigger turns its
    #  lead lines stand 0.9 either side of the core, and at the old
    #  positions the primary lead landed exactly on L_m's branch and the
    #  load block on the secondary.
    XN = 3.05
    series(ax, top, 1.55, 2.35, XN)
    #  The primary spans the SAME two rails as L_m, so its terminals land
    #  on them and both leads are straight.  Centred on the node line it
    #  needed a step up to reach the top rail and a step down to reach the
    #  bottom one, and that step was the only bend in the figure.
    t = S.xfmr(ax, 4.75, YMID, hp=YS_ - YR, hs=YS_ - YR, gap=0.30)
    S.wire(ax, [(XN, YS_), t['p_top']])
    S.wire(ax, [t['p_bot'], (XS_, YR)])
    #  the block fills what is left to the frame edge, from the lead line
    xb0, xb1 = t['s_top'][0] + 0.45, 7.45
    bl, _ = S.box(ax, (xb0 + xb1) / 2.0, YMID, xb1 - xb0, 2.3,
                  'rectifier\n+ load', size=9.5)
    S.wire(ax, [t['s_top'], (bl[0], t['s_top'][1])])
    S.wire(ax, [t['s_bot'], (bl[0], t['s_bot'][1])])

    # ---- (b) referred
    ax = axs[1]
    S.frame(ax, -0.3, 7.6, -1.3, 3.5, '2   secondary referred to the primary')
    top = drive(ax, 'sq')
    series(ax, top, 1.95, 3.1, 4.2)
    #  The rectifier stays: only the transformer goes.  A resistor n^2 R_L
    #  here, still driven by the square wave, said the rectifier and the
    #  stiff output were a resistor at every harmonic - they look like one
    #  only at the fundamental, which is step 3 (2026-09-23).
    xb0, xb1 = 5.25, 7.45
    bl, _ = S.box(ax, (xb0 + xb1) / 2.0, YMID, xb1 - xb0, 2.3,
                  'rectifier\n+ n$^2$R$_L$', size=9.5)
    S.wire(ax, [(4.2, YS_), (bl[0], YS_)])
    S.wire(ax, [(bl[0], YR), (XS_, YR)])
    ax.annotate('the ideal transformer disappears;\n'
                'the load is scaled by n$^2$',
                xy=(xb0 + 0.55, YMID + 1.15), xytext=(1.6, 2.75), fontsize=10,
                color=GREY, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.3))

    # ---- (c) FHA
    ax = axs[2]
    S.frame(ax, -0.3, 7.6, -1.3, 3.5, '3   first harmonic only')
    top = drive(ax, 'ac')
    series(ax, top, 1.95, 3.1, 4.2)
    XR_ = 5.9
    S.wire(ax, [(4.2, YS_), (XR_, YS_)])
    S.shunt(ax, XR_, YS_, YR, 'res', 'R$_{ac}$')
    S.wire(ax, [(XR_, YR), (XS_, YR)])
    #  The band is the whole network, return rail included - drawn to the
    #  node line only, it cut L_m and R_ac in half.
    S.shade(ax, 1.45, -1.18, 7.05, 1.95, None, color=CYA)
    ax.annotate('one ac network.\nM and Q are read off it',
                xy=(3.6, 1.95), xytext=(1.6, 2.75), fontsize=10,
                color=CYA, ha='left', fontweight='bold',
                arrowprops=dict(arrowstyle='-|>', color=CYA, lw=1.3))

    foot(fig, 'The rectifier and load become one resistor R_ac, and the '
              'square wave becomes its fundamental. Everything in this note '
              'that is written as M(f_n, Q) is read from the right-hand '
              'circuit.')
    save(fig, 'an_fha_steps')


# ------------------------------------------------------------------ 3
def an_pfc_idea(save, foot):
    fig, axs = plt.subplots(1, 2, figsize=(12.4, 4.1))
    t = np.linspace(0, 2, 800)
    v = np.sin(np.pi * t)

    ax = axs[0]
    ax.set_title('without correction:  a capacitor-input rectifier',
                 fontsize=11.5, color=NAVY, pad=8)
    ax.plot(t, v, color=NAVY, lw=2.0, label='line voltage')
    vr = np.abs(v)
    pk = 0.86
    i = np.where(vr > pk, (vr - pk) ** 1.4, 0.0)
    i = i / i.max() * 0.95 * np.sign(np.sin(np.pi * t))
    ax.plot(t, i, color=MAG, lw=2.2, label='line current')
    ax.fill_between(t, 0, i, color=MAG, alpha=0.16)
    ax.axhline(0, color=GREY, lw=0.9)
    ax.set_ylim(-1.35, 1.55)
    ax.set_xlim(0, 2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc='upper right', fontsize=9.5)
    ax.annotate('current only flows at the crest,\n'
                'in narrow high spikes',
                xy=(0.5, 0.85), xytext=(0.06, -1.18), fontsize=10.5,
                color=MAG, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.5))
    ax.text(1.5, -1.18, 'PF $\\approx$ 0.6', fontsize=12, color=MAG,
            fontweight='bold', ha='center')

    ax = axs[1]
    ax.set_title('with correction:  current shaped to the voltage',
                 fontsize=11.5, color=NAVY, pad=8)
    ax.plot(t, v, color=NAVY, lw=2.0, label='line voltage')
    ax.plot(t, 0.82 * v, color=GRN, lw=2.2, label='line current')
    ax.fill_between(t, 0, 0.82 * v, color=GRN, alpha=0.16)
    ax.axhline(0, color=GREY, lw=0.9)
    ax.set_ylim(-1.35, 1.55)
    ax.set_xlim(0, 2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc='upper right', fontsize=9.5)
    ax.annotate('same shape, same phase',
                xy=(0.5, 0.82), xytext=(0.06, -1.18), fontsize=10.5,
                color=GRN, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=GRN, lw=1.5))
    ax.text(1.5, -1.18, 'PF > 0.95', fontsize=12, color=GRN,
            fontweight='bold', ha='center')

    foot(fig, 'Power factor correction makes the converter look resistive to '
              'the mains. The price is that the input power then pulses at '
              'twice the line frequency, and something has to absorb that.')
    fig.tight_layout()
    save(fig, 'an_pfc_idea')


# ------------------------------------------------------------------ 4
def an_architectures(save, foot):
    fig, axs = plt.subplots(2, 1, figsize=(12.2, 5.6))

    def chain(ax, items, y=0.0):
        x = 0.6
        prev = None
        for w, t, fc, ec in items:
            S.box(ax, x + w / 2, y, w, 1.0, t, fc=fc, ec=ec, size=10)
            if prev is not None:
                S.wire(ax, [(prev, y), (x, y)], lw=1.6)
            prev = x + w
            x += w + 0.55
        return x

    ax = axs[0]
    #  17.2: the upper chain runs to 16.9, and at 15.4 its last box was
    #  clipped off with only its label left to say it had been there
    S.frame(ax, -0.2, 17.2, -1.9, 1.5, 'two stages, the usual arrangement')
    chain(ax, [(1.5, 'mains', 'white', GREY),
               (1.6, 'bridge', LT, GREY),
               (2.3, 'boost PFC', LT, GREY),
               (2.5, '400 V bulk\ncapacitor', YEL, MAG),
               (1.9, 'LLC', LT, GREY),
               (1.9, 'C$_{out}$\nsmall', LT, GREY),
               (1.3, 'load', 'white', GREY)])
    ax.annotate('the buffer sits here, at 400 V',
                xy=(8.05, -0.52), xytext=(6.2, -1.55), fontsize=10.5,
                color=MAG, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.5))

    ax = axs[1]
    S.frame(ax, -0.2, 17.2, -1.9, 1.5, 'one stage')
    chain(ax, [(1.5, 'mains', 'white', GREY),
               (1.6, 'bridge', LT, GREY),
               (2.5, 'PF LLC', CYA, NAVY),
               (3.0, 'C$_{out}$\nvery large', YEL, MAG),
               (1.3, 'load', 'white', GREY)])
    ax.annotate('the same energy, now at the output voltage',
                xy=(7.25, -0.52), xytext=(5.0, -1.55), fontsize=10.5,
                color=MAG, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.5))
    ax.annotate('this stage now does both jobs',
                xy=(5.05, 0.52), xytext=(4.0, 1.15), fontsize=10.5,
                color=NAVY, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.5))

    foot(fig, 'Removing the boost stage does not remove the energy it was '
              'buffering. C = 2E/V^2, so moving the same joules from 400 V '
              'to a low output multiplies the capacitance by the square of '
              'the voltage ratio.')
    fig.tight_layout()
    save(fig, 'an_architectures')


FIGS = {'an_llc_stage': an_llc_stage, 'an_fha_steps': an_fha_steps,
        'an_pfc_idea': an_pfc_idea, 'an_architectures': an_architectures}
