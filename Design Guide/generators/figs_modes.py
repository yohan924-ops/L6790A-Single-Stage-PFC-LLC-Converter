# -*- coding: utf-8 -*-
"""Where the converter actually sits: above or below resonance.

The note stated that f_r divides boost from buck and then never said which
side the converter is on. In a single-stage converter the answer is not one
side - it walks across the boundary within a line cycle at high line, and
stays below it at low line. That is the picture this file draws.
"""
import numpy as np
import matplotlib.pyplot as plt

from schem import NAVY, MAG, CYA, GRN, PUR, GREY, LT, YEL


def an_above_below(save, foot, R, sweep, FR):
    """f_sw(theta)/f_r for each equivalent input, with f_r marked"""
    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    CASES = [(R['Vin_min'], '173.2 Vac eq.  (HB morphing edge)', MAG),
             (225.0, '225 Vac eq.', CYA),
             (264.0, '264 Vac eq.  (mains maximum)', NAVY),
             (332.34, '332.3 Vac eq.  (FB morphing edge)', PUR)]
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
        ax.plot(t, y, color=col, lw=2.2, label=lab)
        frac = 100.0 * np.trapezoid((y > 1.0).astype(float), t) / 180.0
        txt.append((lab.split()[0], frac, col))

    ax.axhline(1.0, color=GREY, lw=1.8, ls='--')
    ax.text(2, 1.03, 'f$_r$  —  the boundary', color=GREY, fontsize=10.5,
            va='bottom')
    ax.axhspan(1.0, 2.6, color=CYA, alpha=0.10)
    ax.axhspan(0.0, 1.0, color=YEL, alpha=0.13)
    ax.text(176, 1.72, 'ABOVE resonance\ntank BUCKS  ·  M < 1\n'
                      'secondary conducts the whole half period',
            color=NAVY, fontsize=10, ha='right', va='center',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=CYA, lw=1.2))
    ax.text(176, 0.40, 'BELOW resonance\ntank BOOSTS  ·  M > 1\n'
                       'secondary stops early, then a dead interval',
            color=NAVY, fontsize=10, ha='right', va='center',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='#B8860B',
                      lw=1.2))

    y0 = 2.34
    for name, frac, col in txt:
        ax.text(3, y0, '%s Vac eq. : %.0f %% of the half cycle above f$_r$'
                % (name, frac), color=col, fontsize=10, fontweight='bold')
        y0 -= 0.135

    ax.set_xlim(0, 180)
    ax.set_ylim(0.0, 2.6)
    ax.set_xlabel('line phase  $\\theta$  [deg]')
    ax.set_ylabel('f$_{sw}$ / f$_r$')
    ax.set_xticks(range(0, 181, 30))
    ax.legend(loc='upper right', fontsize=9.2, ncol=1)
    foot(fig, 'At low line the converter never leaves the boosting region. '
              'At the high morphing edge it crosses into the bucking region '
              'around the line peak and comes back. A single-stage converter '
              'therefore has to be designed for BOTH sides.')
    fig.tight_layout()
    save(fig, 'an_above_below')


def an_zvs_zcs(save, foot):
    """which switch gets which soft-switching, and why"""
    fig, axs = plt.subplots(1, 2, figsize=(12.6, 4.3))
    t = np.linspace(0, 1, 600)

    # ---------------- primary: ZVS
    ax = axs[0]
    ax.set_title('PRIMARY  —  zero VOLTAGE switching',
                 fontsize=11.5, color=NAVY, pad=8)
    v = np.where(t < 0.46, 1.0, np.where(t < 0.54, 1 - (t - 0.46) / 0.08, 0.0))
    ax.plot(t, v, color=NAVY, lw=2.3, label='bridge midpoint')
    i = 0.75 * np.sin(2 * np.pi * (t - 0.06))
    ax.plot(t, i, color=MAG, lw=2.2, label='tank current')
    ax.axvspan(0.46, 0.54, color=YEL, alpha=0.55)
    ax.text(0.50, 1.32, 'dead time', ha='center', fontsize=10,
            color='#8a6d00', fontweight='bold')
    ax.annotate('current is still flowing when the gate turns off,\n'
                'so it pulls the node down for free',
                xy=(0.50, 0.5), xytext=(0.03, -1.05), fontsize=9.6,
                color=MAG, ha='left',
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.4))
    ax.text(0.62, 0.16, 'voltage reaches zero\nBEFORE the next turn-on',
            fontsize=9.6, color=NAVY,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=NAVY, lw=1.0))
    ax.set_ylim(-1.5, 1.6)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc='upper left', fontsize=9)

    # ---------------- secondary: ZCS
    ax = axs[1]
    ax.set_title('SECONDARY  —  zero CURRENT switching (below f$_r$ only)',
                 fontsize=11.5, color=NAVY, pad=8)
    d = 0.72
    s = np.where(t < d, np.sin(np.pi * t / d), 0.0)
    ax.plot(t, s, color=GRN, lw=2.4, label='rectifier current')
    ax.fill_between(t, 0, s, color=GRN, alpha=0.15)
    ax.axvspan(d, 1.0, color=LT, alpha=0.9)
    #  the interval after the current has reached zero is the secondary-off
    #  part of the same half cycle (step 2 in the mode figures), not the
    #  dead time - the note is careful about that word elsewhere
    ax.text((d + 1) / 2, 0.5, 'secondary\noff (step 2)', ha='center',
            fontsize=9.6, color=GREY)
    ax.annotate('current reaches zero on its own,\n'
                'so the rectifier turns off with no reverse recovery',
                xy=(d, 0.02), xytext=(0.04, 0.78), fontsize=9.6, color=GRN,
                arrowprops=dict(arrowstyle='-|>', color=GRN, lw=1.4))
    #  Above f_r the resonant half sine is LONGER than the half period, so
    #  the half period ends with the current still flowing and the switches
    #  cut it.  The first version drew a sine that reached zero exactly at
    #  the end - the opposite of its own label.
    t2 = np.linspace(0, 1.06, 640)
    hi = np.sin(np.pi / 1.25)
    above = np.where(t2 < 1.0, np.sin(np.pi * t2 / 1.25),
                     hi * np.clip(1.0 - (t2 - 1.0) / 0.03, 0.0, 1.0))
    ax.plot(t2, above, color=GREY, lw=1.4, ls=':',
            label='above f$_r$ : cut off while still flowing')
    ax.axvline(1.0, color=GREY, lw=0.9, ls='--')
    ax.text(1.0, -0.085, 'half period ends', ha='center', va='center',
            fontsize=8.8, color=GREY)
    ax.set_xlim(0, 1.06)
    ax.set_ylim(-0.15, 1.35)
    ax.set_xlabel('one switching half period')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(loc='upper right', fontsize=9)

    foot(fig, 'The two are different mechanisms on different devices. ZVS on '
              'the primary needs inductive operation and is required '
              'everywhere. ZCS on the secondary happens only below '
              'resonance, and is lost the moment the converter crosses above '
              'it.')
    fig.tight_layout()
    save(fig, 'an_zvs_zcs')
