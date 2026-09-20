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
    fig, ax = plt.subplots(figsize=(11.6, 4.5))
    S.frame(ax, -0.4, 15.2, -1.5, 4.4)

    # half bridge
    S.wire(ax, [(0.5, 3.7), (2.2, 3.7)])
    S.label(ax, 0.35, 3.7, 'V$_{in}$', ha='right', weight='bold')
    S.wire(ax, [(0.5, -0.9), (2.2, -0.9)])
    S.gnd(ax, 0.9, -0.95)
    S.sw(ax, 2.2, 2.75, 'Q1')
    S.sw(ax, 2.2, 0.15, 'Q2')
    S.wire(ax, [(2.2, 3.7), (2.2, 3.01)])
    S.wire(ax, [(2.2, 2.49), (2.2, 0.41)])
    S.wire(ax, [(2.2, -0.11), (2.2, -0.9)])
    S.dot(ax, 2.2, 1.45)
    S.label(ax, 2.2, 3.95, 'half bridge', size=10.5, color=GREY)

    # the tank
    S.shade(ax, 2.85, 0.55, 7.35, 2.65, 'resonant tank', color=CYA)
    a, b = S.cap(ax, 3.55, 1.45, 'C$_r$', s=0.34, tdy=0.55)
    S.wire(ax, [(2.2, 1.45), a])
    c, d = S.ind(ax, 5.05, 1.45, 'L$_r$', s=0.95)
    S.wire(ax, [b, c])
    S.wire(ax, [d, (6.55, 1.45)])
    S.dot(ax, 6.55, 1.45)
    S.shunt(ax, 6.55, 1.45, -0.9, 'ind', 'L$_m$', frac=0.52)
    S.wire(ax, [(2.2, -0.9), (9.0, -0.9)])

    # transformer
    t = S.xfmr(ax, 8.05, 1.45, hp=1.9, hs=1.9, gap=0.34, ct=True,
               np_t=5, ns_t=2)
    S.wire(ax, [(6.55, 1.45), (6.55, 2.40), (t['p_top'][0], 2.40),
                t['p_top']])
    S.wire(ax, [t['p_bot'], (t['p_bot'][0], -0.9)])
    S.label(ax, 8.05, 3.30, 'n : 1', size=10.5, color=GREY)

    # secondary, centre tap
    XTAP = 9.05
    S.wire(ax, [t['s_top'], (9.6, t['s_top'][1])])
    di, do = S.diode(ax, 10.3, t['s_top'][1], s=0.30)
    S.wire(ax, [(9.6, t['s_top'][1]), di])
    S.wire(ax, [do, (11.6, t['s_top'][1])])
    #  The tap leaves on its own riser, so the lower end's wire has to cross
    #  it.  Run flat through the riser and the drawing shorts the lower half
    #  winding to the return - which is what it did before this hop.
    S.wire(ax, [t['s_bot'], (XTAP - 0.20, t['s_bot'][1])])
    S.hop(ax, XTAP, t['s_bot'][1])
    S.wire(ax, [(XTAP + 0.20, t['s_bot'][1]), (9.6, t['s_bot'][1])])
    di2, do2 = S.diode(ax, 10.3, t['s_bot'][1], s=0.30)
    S.wire(ax, [(9.6, t['s_bot'][1]), di2])
    S.wire(ax, [do2, (11.6, t['s_bot'][1])])
    S.wire(ax, [(11.6, t['s_top'][1]), (11.6, t['s_bot'][1])])
    S.dot(ax, 11.6, 1.45)
    S.wire(ax, [(11.6, 1.45), (14.3, 1.45)])
    S.label(ax, 10.3, t['s_top'][1] + 0.42, 'rectifier', size=10, color=GREY)

    # centre tap return
    S.wire(ax, [t['s_tap'], (XTAP, 1.45), (XTAP, -0.9), (14.3, -0.9)])

    ca, cb = S.cap(ax, 12.8, 0.28, None, horiz=False, s=0.34)
    S.wire(ax, [(12.8, 1.45), (12.8, 0.62)])
    S.wire(ax, [(12.8, -0.06), (12.8, -0.9)])
    S.dot(ax, 12.8, 1.45)
    S.label(ax, 13.1, 0.28, 'C$_{out}$', ha='left')
    S.res(ax, 14.3, 0.28, None, horiz=False, s=1.0)
    S.wire(ax, [(14.3, 1.45), (14.3, 0.78)])
    S.wire(ax, [(14.3, -0.22), (14.3, -0.9)])
    S.label(ax, 14.6, 0.28, 'load', ha='left')
    S.label(ax, 13.4, 2.0, 'V$_{out}$', weight='bold')

    S.note = None
    #  The callout used to start above the tank and reach down across it,
    #  so its text lay over the shading and over C_r, L_r and the tank's
    #  own name.  Below the half bridge there is clear air and a shorter
    #  leader.
    ax.annotate('the square wave the tank\nis driven with',
                xy=(2.32, 1.30), xytext=(2.95, -0.55), fontsize=10.5,
                color=MAG, ha='left', linespacing=1.4,
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.6,
                                connectionstyle='arc3,rad=0.18'))
    foot(fig, 'Three reactive elements and a square wave. The switches only '
              'set the frequency; the tank decides how much power flows and '
              'the transformer sets the voltage.')
    fig.tight_layout()
    save(fig, 'an_llc_stage')


# ------------------------------------------------------------------ 2
def an_fha_steps(save, foot):
    fig, axs = plt.subplots(1, 3, figsize=(14.4, 4.0))

    # ---- (a) as built
    ax = axs[0]
    S.frame(ax, -0.3, 7.6, -1.3, 3.5,
            '1   as built')
    S.sqsrc(ax, 0.55, 1.1, 'square\nwave')
    S.wire(ax, [(0.91, 1.1), (1.3, 1.1)])
    a, b = S.cap(ax, 1.6, 1.1, 'C$_r$', s=0.28, tdy=0.48)
    c, d = S.ind(ax, 2.6, 1.1, 'L$_r$', s=0.8)
    S.wire(ax, [b, c])
    S.wire(ax, [d, (3.5, 1.1)])
    S.dot(ax, 3.5, 1.1)
    S.shunt(ax, 3.5, 1.1, -0.9, 'ind', 'L$_m$', frac=0.5)
    S.wire(ax, [(3.5, -0.9), (0.55, -0.9), (0.55, 0.74)])
    S.wire(ax, [(3.5, 1.1), (3.5, 2.2), (4.4, 2.2)])
    t = S.xfmr(ax, 4.75, 1.1, hp=1.6, hs=1.6, gap=0.30)
    S.wire(ax, [(4.4, 2.2), t['p_top']])
    S.wire(ax, [t['p_bot'], (t['p_bot'][0], -0.9)])
    S.wire(ax, [t['s_top'], (5.9, t['s_top'][1])])
    S.wire(ax, [t['s_bot'], (5.9, t['s_bot'][1])])
    S.wire(ax, [(5.9, t['s_top'][1]), (5.9, t['s_bot'][1])])
    S.box(ax, 6.6, 1.1, 1.3, 1.7, 'rectifier\n+ load', size=9.5)

    # ---- (b) referred
    ax = axs[1]
    S.frame(ax, -0.3, 7.6, -1.3, 3.5,
            '2   secondary referred to the primary')
    S.sqsrc(ax, 0.55, 1.1, 'square\nwave')
    S.wire(ax, [(0.91, 1.1), (1.3, 1.1)])
    a, b = S.cap(ax, 1.6, 1.1, 'C$_r$', s=0.28, tdy=0.48)
    c, d = S.ind(ax, 2.8, 1.1, 'L$_r$', s=0.8)
    S.wire(ax, [b, c])
    S.wire(ax, [d, (4.0, 1.1)])
    S.dot(ax, 4.0, 1.1)
    S.shunt(ax, 4.0, 1.1, -0.9, 'ind', 'L$_m$', frac=0.5)
    S.wire(ax, [(4.0, 1.1), (5.6, 1.1)])
    S.dot(ax, 5.6, 1.1)
    S.shunt(ax, 5.6, 1.1, -0.9, 'res', 'n$^2$R$_{load}$', frac=0.5,
            tdx=0.36)
    S.wire(ax, [(5.6, -0.9), (0.55, -0.9), (0.55, 0.74)])
    S.note = None
    ax.annotate('the ideal transformer disappears;\n'
                'the load is scaled by n$^2$',
                xy=(5.6, 1.75), xytext=(2.2, 2.75), fontsize=10,
                color=GREY, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.3))

    # ---- (c) FHA
    ax = axs[2]
    S.frame(ax, -0.3, 7.6, -1.3, 3.5,
            '3   first harmonic only')
    S.acsrc(ax, 0.55, 1.1, 'fundamental\nof the drive')
    S.wire(ax, [(0.91, 1.1), (1.3, 1.1)])
    a, b = S.cap(ax, 1.6, 1.1, 'C$_r$', s=0.28, tdy=0.48)
    c, d = S.ind(ax, 2.8, 1.1, 'L$_r$', s=0.8)
    S.wire(ax, [b, c])
    S.wire(ax, [d, (4.0, 1.1)])
    S.dot(ax, 4.0, 1.1)
    S.shunt(ax, 4.0, 1.1, -0.9, 'ind', 'L$_m$', frac=0.5)
    S.wire(ax, [(4.0, 1.1), (5.6, 1.1)])
    S.dot(ax, 5.6, 1.1)
    S.shunt(ax, 5.6, 1.1, -0.9, 'res', 'R$_{ac}$', frac=0.5)
    S.wire(ax, [(5.6, -0.9), (0.55, -0.9), (0.55, 0.74)])
    S.shade(ax, 1.32, 0.05, 6.45, 2.05, None, color=CYA)
    ax.annotate('one ac network.\nM and Q are read off it',
                xy=(3.6, 2.05), xytext=(1.5, 2.78), fontsize=10,
                color=CYA, ha='left', fontweight='bold',
                arrowprops=dict(arrowstyle='-|>', color=CYA, lw=1.3))

    foot(fig, 'The rectifier and load become one resistor R_ac, and the '
              'square wave becomes its fundamental. Everything in this note '
              'that is written as M(f_n, Q) is read from the right-hand '
              'circuit.')
    fig.tight_layout()
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
    S.frame(ax, -0.2, 15.4, -1.9, 1.5, 'two stages, the usual arrangement')
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
    S.frame(ax, -0.2, 15.4, -1.9, 1.5, 'one stage')
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
