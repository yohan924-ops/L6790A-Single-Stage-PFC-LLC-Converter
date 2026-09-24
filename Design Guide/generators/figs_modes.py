# -*- coding: utf-8 -*-
"""Where the converter actually sits: above or below resonance.

The note stated that f_r divides boost from buck and then never said which
side the converter is on. In a single-stage converter the answer is not one
side - it walks across the boundary within a line cycle at high line, and
stays below it at low line. That is the picture this file draws.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from schem import NAVY, MAG, CYA, GRN, PUR, GREY, LT, YEL


def an_above_below(save, foot, R, sweep, FR):
    """f_sw(theta)/f_r for each equivalent input, with f_r marked"""
    fig, ax = plt.subplots(figsize=(9.35, 4.25))
    from l6790 import line_conditions
    COLS = [MAG, '#D97706', CYA, GRN, NAVY, PUR]
    CASES = [(veq, nm, c) for (nm, veq, _m), c in zip(line_conditions(R), COLS)]
    fr = R['fr']
    txt = []
    for vin, lab, col in CASES:
        rows, _ = sweep(R, vin, N=361)
        ok = [r for r in rows if r]
        t = np.array([np.degrees(r['th']) for r in ok])
        y = np.array([r['fsw'] for r in ok]) / fr
        # the sweep covers a quarter cycle; mirror it so the reader sees the
        # whole half cycle the converter actually walks through
        t = np.concatenate([t, 180.0 - t[::-1]])
        y = np.concatenate([y, y[::-1]])
        ax.plot(t, y, color=col, lw=2.2)
        frac = 100.0 * np.trapezoid((y > 1.0).astype(float), t) / 180.0
        txt.append((lab, frac, col))

    ax.axhline(1.0, color=GREY, lw=1.8, ls='--')
    ax.text(2, 1.03, 'f$_r$  \u2014  the boundary', color=GREY, fontsize=10.5,
            va='bottom')
    ax.axhspan(1.0, 2.6, color=CYA, alpha=0.10)
    ax.axhspan(0.0, 1.0, color=YEL, alpha=0.13)
    ax.text(4, 2.08, 'ABOVE resonance\ntank BUCKS  \u00b7  M < 1\n'
                     'secondary conducts the whole half period',
            color=NAVY, fontsize=10, ha='left', va='center',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=CYA, lw=1.2))
    ax.text(176, 0.40, 'BELOW resonance\ntank BOOSTS  \u00b7  M > 1\n'
                       'secondary stops early, then a dead interval',
            color=NAVY, fontsize=10, ha='right', va='center',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#B8860B',
                      lw=1.2))

    ax.grid(True, color='#C4C8CF', lw=0.7)
    ax.set_axisbelow(True)
    ax.set_xlim(0, 180)
    ax.set_ylim(0.0, 2.45)
    ax.set_xlabel('line phase  $\\theta$  [deg]')
    ax.set_ylabel('f$_{sw}$ / f$_r$')
    ax.set_xticks(range(0, 181, 30))
    #  The percentage used to sit in a block of its own on the left, which
    #  said the same four names as the legend and never said what it was a
    #  percentage OF (2026-09-22, user).  It belongs to the curve, so it
    #  goes in that curve's legend entry, under a title that names it once.
    hs = [Line2D([], [], color=c, lw=2.2) for _l, _f, c in txt]
    ax.legend(hs, ['%s  \u2014  %.0f %%' % (l, f) for l, f, _c in txt],
              loc='upper right', fontsize=9.4, ncol=1,
              title='input voltage and bridge, and the share of the\n'
                    'half cycle it spends above f$_r$',
              title_fontsize=9.4)
    foot(fig, 'At the lowest input voltage the converter never leaves the boosting region. '
              'At the high morphing edge it crosses into the bucking region '
              'around the line peak and comes back. A single-stage converter '
              'therefore has to be designed for BOTH sides.')
    fig.tight_layout()
    save(fig, 'an_above_below')


def an_zvs_zcs(save, foot):
    """which switch gets which soft-switching, and why

    Rebuilt after the question "is the tank current really that perfect a
    sine, and has the dead time been taken into account?"  It was a sine,
    and it had not.  Both panels now read the eight-interval model that the
    mode sheets use, so the three figures cannot disagree.  The gate
    waveforms are drawn as well: without them there is nothing in the
    picture that says WHEN the next device turns on, and "the node reaches
    zero before the next turn-on" is a claim about exactly that instant.
    """
    import figs as _F
    import figs_modes8 as _M
    from l6790 import sweep
    R = _F.R
    _, agg = sweep(R, R['Vin_min'], N=721)
    FSW_FR = 0.70                       # the ratio the mode sheets are drawn at
    T, e, ILR, ILM, IO, VA = _M.series(R['lam_a'], FSW_FR,
                                       agg['comp_pk'], agg['ILm_pk'])

    fig = plt.figure(figsize=(9.2, 6.0))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.15, 1.0],
                          height_ratios=[0.78, 0.80, 1.22],
                          hspace=0.20, wspace=0.22,
                          left=0.085, right=0.985, top=0.895, bottom=0.175)
    ag = fig.add_subplot(gs[0, 0])
    av = fig.add_subplot(gs[1, 0], sharex=ag)
    ai = fig.add_subplot(gs[2, 0], sharex=ag)
    ar = fig.add_subplot(gs[:, 1])

    # ================================================ primary: ZVS
    ag.set_title('PRIMARY  —  zero VOLTAGE switching',
                 fontsize=11.5, color=NAVY, pad=7)
    #  the two dead times, on all three rows, so the sync is not a matter
    #  of trusting the eye across panels
    for a in (ag, av, ai):
        for k in (2, 6):
            a.axvspan(e[k], e[k + 2], color=YEL, alpha=0.55, lw=0)
        a.set_xlim(0, 1)
        a.set_xticks([])
        for sp in ('top', 'right'):
            a.spines[sp].set_visible(False)

    def sq(a, b):
        return np.where((T >= a) & (T < b), 1.0, 0.0)
    ag.plot(T, 0.46 * sq(e[0], e[2]) + 0.54, color=NAVY, lw=2.2)
    ag.plot(T, 0.46 * sq(e[4], e[6]), color=PUR, lw=2.2)
    ag.text(-0.012, 0.77, 'S1, S4', ha='right', va='center', fontsize=10,
            color=NAVY, fontweight='bold')
    ag.text(-0.012, 0.23, 'S2, S3', ha='right', va='center', fontsize=10,
            color=PUR, fontweight='bold')
    ag.set_ylim(-0.22, 1.72)
    ag.set_yticks([])
    #  the band is 0.045 wide, so the two labels have to be stacked in y
    #  rather than placed side by side - they collided at the same height
    ag.text((e[2] + e[4]) / 2, 1.50, 'dead time', ha='center', va='bottom',
            fontsize=10, color='#8a6d00', fontweight='bold')
    ag.annotate('next turn-on', xy=(e[4], 0.46), xytext=(e[4] + 0.05, 0.98),
                fontsize=10, color=PUR, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=PUR, lw=1.4))

    av.plot(T, VA, color=NAVY, lw=2.3)
    av.set_ylim(-0.28, 1.62)
    av.set_yticks([0, 1])
    av.set_yticklabels(['0', 'V$_{in}$'])
    av.set_ylabel('node A', fontsize=10, color=NAVY)
    #  to the RIGHT of the transition: to its left is the V_in level line
    #  and the annotation sat straight on it
    #  Short lines on purpose: one long line ran out of this panel and into
    #  the one beside it, which is what the checker calls wrong-panel.
    av.annotate('v$_A$ is already 0 when\nS2, S3 turn on —\nthat is ZVS',
                xy=(e[4], 0.05), xytext=(e[4] + 0.055, 0.30), fontsize=10,
                color=GRN, ha='left', linespacing=1.35,
                arrowprops=dict(arrowstyle='-|>', color=GRN, lw=1.4))

    ai.plot(T, ILR, color=MAG, lw=2.4, label='i$_{Lr}$  tank')
    ai.plot(T, ILM, color=CYA, lw=2.2, ls='--', label='i$_{Lm}$  magnetising')
    ai.axhline(0, color=GREY, lw=0.9)
    ai.set_ylim(-1.62 * agg['comp_pk'], 1.72 * agg['comp_pk'])
    ai.set_yticks([0])
    ai.set_yticklabels(['0'])
    ai.set_xlabel('one switching period', fontsize=10, color=NAVY)
    ai.legend(loc='lower left', fontsize=10, ncol=2, framealpha=0.92)
    ai.annotate('the load component is already gone:\nwhat is left to swing the node is i$_{Lm}$',
                xy=(e[2], float(ILM[np.searchsorted(T, e[2])])),
                xytext=(0.035, 1.12 * agg['comp_pk']), fontsize=10,
                color=MAG, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.4))

    # ================================================ secondary: ZCS
    ar.set_title('SECONDARY  —  zero CURRENT switching (below f$_r$ only)',
                 fontsize=11.5, color=NAVY, pad=7)
    #  the same half period the left-hand panel shows, at the same f_sw/f_r
    h = T <= 0.5
    th, io = T[h] * 2.0, IO[h]                   # one half period, 0 to 1
    ar.plot(th, io, color=GRN, lw=2.4, label='rectifier current')
    ar.fill_between(th, 0, io, color=GRN, alpha=0.15)
    d = 2.0 * e[1]                               # = f_sw / f_r
    ar.axvspan(d, 1.0, color=LT, alpha=0.9, lw=0)
    ar.text((d + 1) / 2, 0.45 * io.max(), 'secondary\noff (step 2)',
            ha='center', fontsize=10, color=GREY)
    #  Labelled AT the zero crossing, not from across the panel: the long
    #  straight leader drawn before ran down the falling flank and read as
    #  part of the waveform.
    ar.plot([d], [0.0], 'o', color=GRN, ms=7, zorder=5)
    #  under the rising flank, where the panel is empty: written against the
    #  falling flank the middle line ran along the waveform itself
    ar.annotate('reaches zero on its own —\nno reverse recovery',
                xy=(d, 0.0), xytext=(0.045, 0.07 * io.max()),
                ha='left', va='bottom', fontsize=10, color=GRN,
                linespacing=1.35,
                arrowprops=dict(arrowstyle='-|>', color=GRN, lw=1.4))
    #  Above f_r the resonant half sine is LONGER than the half period, so
    #  the half period ends with the current still flowing and the switches
    #  cut it.  Drawn to the same peak, stretched by 1/d.
    t2 = np.linspace(0, 1.06, 640)
    st = 1.25
    hi = io.max() * np.sin(np.pi / st)
    above = np.where(t2 < 1.0, io.max() * np.sin(np.pi * t2 / st),
                     hi * np.clip(1.0 - (t2 - 1.0) / 0.03, 0.0, 1.0))
    ar.plot(t2, above, color=GREY, lw=1.4, ls=':',
            label='above f$_r$ : cut off while still flowing')
    ar.axvline(1.0, color=GREY, lw=0.9, ls='--')
    #  along the line, inside the axes: written under it the label fell off
    #  the bottom of the figure
    #  low and right, against the dashed line: at the top it disappeared
    #  behind the legend box, which is not a Text and so is invisible to
    #  the overlap check
    ar.text(0.995, 0.07 * io.max(), 'half period ends', ha='right',
            va='bottom', fontsize=10, color=GREY)
    ar.set_xlim(0, 1.06)
    ar.set_ylim(-0.14 * io.max(), 1.34 * io.max())
    ar.set_xlabel('one switching half period', fontsize=10, color=NAVY)
    ar.set_xticks([])
    ar.set_yticks([])
    for sp in ('top', 'right'):
        ar.spines[sp].set_visible(False)
    ar.legend(loc='upper left', fontsize=10, framealpha=0.94)

    foot(fig, 'Two different mechanisms on two different devices, drawn from '
              'the same eight-interval model as the mode figures, at '
              'f$_{sw}$/f$_r$ = %.2f and with the dead time wider than scale. '
              'ZVS on the primary needs inductive operation and is required '
              'everywhere. ZCS on the secondary happens only below '
              'resonance, and is lost the moment the converter crosses above '
              'it.' % FSW_FR)
    save(fig, 'an_zvs_zcs')
