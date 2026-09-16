# -*- coding: utf-8 -*-
"""Teaching figures for the training deck and the design guide.

The figures already in the deck came from a script that no longer exists, so
they could not be corrected - and two of them needed it: an annotation printed
on top of the legend, and the conclusion left in the title where a reader
looking at the picture never sees it.

Rules here, because the complaint was "I cannot tell what the graph is for":

  1. every figure states the QUESTION it answers, not a description of its axes;
  2. the answer is written ON the plot, in empty space, next to the thing it
     refers to - never over a curve or a legend;
  3. what must not be missed is DRAWN: an arrow, a shaded band, a marked point;
  4. numbers come from l6790.py with the real 25 V design, so a figure cannot
     drift away from the sheet.

Text is English, matching the deck. The three-region framing and the ZVS
mechanism follow the way ROHM TechWeb's LLC series presents them, which is the
clearest beginner path I have seen; the drawings are our own.

    python figs.py            regenerate all of them into ../figures/
    python figs.py f13        just one
"""
import os
import sys
from math import pi, sqrt, sin, cos

import matplotlib
import matplotlib.ticker
matplotlib.use('Agg')
import matplotlib.font_manager
import matplotlib.pyplot as plt                                      # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle            # noqa: E402
import numpy as np                                                   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from l6790 import design, sweep, M as gain_fn                        # noqa: E402

OUT = os.path.normpath(os.path.join(HERE, '..', 'figures'))

NAVY, YEL, MAG = '#03234B', '#FFD200', '#E6007E'
CYA, GRN, PUR = '#3CB4E6', '#49B170', '#8C0078'
GREY, LT = '#464650', '#E8E8E9'

# The four guide figures carry Korean labels and matplotlib's default font has
# no CJK glyphs - they come out as boxes with no error, only a warning. Put a
# Korean face first and keep a Latin one behind it for the deck figures.
_KR = next((n for n in ('Malgun Gothic', 'NanumBarunGothic', 'Gulim')
            if any(f.name == n for f in matplotlib.font_manager.fontManager.ttflist)),
           None)

plt.rcParams.update({
    'font.family': ([_KR] if _KR else []) + ['DejaVu Sans'],
    'axes.unicode_minus': False,
    'font.size': 11, 'axes.titlesize': 12.5, 'axes.labelsize': 12,
    'axes.edgecolor': GREY, 'axes.labelcolor': NAVY, 'text.color': NAVY,
    'xtick.color': GREY, 'ytick.color': GREY, 'axes.grid': True,
    'grid.color': LT, 'grid.linewidth': 0.8, 'figure.dpi': 170,
    'savefig.dpi': 170, 'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
    'legend.frameon': True, 'legend.edgecolor': LT, 'legend.framealpha': 0.96,
})

# The design point must come from the canonical sheet, not from constants
# typed here.  These were left on the 7.5:1 point after the sheet moved to
# 9:1, so every figure disagreed with the text beside it (f.o 90.4 vs
# 85.1 kHz, composite peak 18.32 vs 17.70 A).
def _sheet_point():
    # the same variant the application note is worked on - see an_pdf.AN_SM
    import snapshot
    import an_pdf
    v, _ = snapshot.read_sheet(an_pdf.AN_SM)
    return (v['n'][0], v['C.r'][0] * 1e-9, v['L.r'][0] * 1e-6,
            v['L.m'][0] * 1e-6)


_N, _CR, _LR, _LM = _sheet_point()
R = design(Vout=25., Pout=657.5, Vo_min=19., dv_out=0.05, Thold=12e-3,
           Nrect=1, fr_t=150e3, fsw_max_spec=225e3, fsw_min_spec=50e3,
           c_HB=800e-12, tD=220e-9, n_sel=_N,
           Cr_sel=_CR, Lr_sel=_LR, Lm_sel=_LM)
LAM, FR, FO, FN0 = R['lam_a'], R['fr'], R['fo'], R['fn0']
QPK, N, VOE, POUT = R['Qpk'], R['n'], R['Vo_eff'], R['Pout']


PLAIN = False          # note mode: no suptitle, and write into figures/an/


def ask(fig, q):
    # a numbered figure in a note gets its title from the caption below it,
    # not from a question printed on the artwork
    if PLAIN:
        return
    fig.suptitle(q, fontsize=13.5, fontweight='bold', color=NAVY, y=0.995)


def foot(fig, t):
    """remember it; save() places it once the layout has settled"""
    fig._foot = t


def note(ax, x, y, text, color=NAVY, size=10.5, ha='left', va='center',
         box=True, **kw):
    bb = dict(boxstyle='round,pad=0.35', fc='white', ec=color, lw=1.1,
              alpha=0.95) if box else None
    return ax.annotate(text, (x, y), color=color, fontsize=size, ha=ha, va=va,
                       bbox=bb, zorder=6, **kw)


def save(fig, name):
    t = getattr(fig, '_foot', None)
    if t:
        # below the lowest thing already drawn, whatever tight_layout decided
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        lo = min(a.get_tightbbox(r).y0 for a in fig.axes)
        y = lo / fig.bbox.height - 0.055
        fig.text(0.5, y, t, ha='center', va='top', fontsize=10.5, color=GREY,
                 wrap=True)
    d = os.path.join(OUT, 'an') if PLAIN else OUT
    if not os.path.isdir(d):
        os.makedirs(d)
    p = os.path.join(d, name + '.png')
    fig.savefig(p, bbox_inches='tight', pad_inches=0.14)
    plt.close(fig)
    print('  %-28s %6.1f KB' % (name + '.png', os.path.getsize(p) / 1024))


# ================================================================ LLC basics
def f02_two_resonances():
    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ask(fig, 'An LLC has TWO resonances — why the lower one is a floor')
    fn = np.linspace(0.45, 2.2, 1400)
    for q, c, w, lab in ((0.0001, PUR, 2.4, 'no load   Q → 0'),
                         (0.20, MAG, 1.7, 'Q = 0.2'),
                         (0.40, CYA, 1.7, 'Q = 0.4'),
                         (QPK, NAVY, 2.6, 'full load  Q = %.2f' % QPK),
                         (1.50, GRN, 1.7, 'Q = 1.5')):
        ax.plot(fn, [gain_fn(x, q, LAM) for x in fn], color=c, lw=w, label=lab)
    ax.axvline(FN0, color=PUR, ls='--', lw=1.7)
    ax.axvline(1.0, color=GREY, ls='--', lw=1.7)
    ax.set_xlim(0.45, 2.2)
    ax.set_ylim(0, 4.2)
    ax.set_xlabel('normalised frequency   f / f$_r$')
    ax.set_ylabel('gain   M = n·V$_o$ / V$_{in}$')
    ax.legend(loc='upper right', fontsize=9.5)
    note(ax, FN0 + 0.03, 3.55,
         'f$_o$ = %.1f kHz\nno-load gain goes to infinity here\n'
         '→ nothing can push the converter below it' % (FO / 1e3), color=PUR,
         size=10)
    note(ax, 1.04, 1.45,
         'f$_r$ = %.1f kHz\ngain = 1 at ANY load\n'
         '(L$_m$ is clamped by the output and drops out)' % (FR / 1e3),
         color=GREY, size=10)
    ax.axvspan(0.45, FN0, color=MAG, alpha=0.10)
    note(ax, 0.475, 0.42, 'capacitive AT NO LOAD\nhard switching — stay out',
         color=MAG, size=10)
    foot(fig, 'Between f$_o$ and f$_r$ the tank can boost, and that band is where '
              'an LLC lives. Follow one loaded curve down, though, and the gain '
              'stops rising at its own peak and falls again - the shaded edge is '
              'the no-load position of that peak, not the loaded one.')
    fig.tight_layout(rect=[0, 0.05, 1, 0.955])
    save(fig, 'f02_two_resonances')


def f03_gain_walk():
    fig, axs = plt.subplots(1, 3, figsize=(13.2, 4.4))
    ask(fig, 'Reading a gain curve — more load (higher Q) flattens the peak')
    fn = np.linspace(0.5, 2.0, 1000)
    for ax, (q, cap) in zip(axs, [
            (0.15, '1  light load,  Q = 0.15\nthe hill is high — plenty of gain'),
            (0.45, '2  medium load,  Q = 0.45\nthe hill is lower'),
            (0.90, '3  full load,  Q = 0.90\nlower still — least gain available')]):
        for qq in (0.15, 0.45, 0.90):
            ax.plot(fn, [gain_fn(x, qq, LAM) for x in fn], color=LT, lw=1.4)
        g = np.array([gain_fn(x, q, LAM) for x in fn])
        ax.plot(fn, g, color=NAVY, lw=2.6)
        i = int(np.argmax(g))
        ax.plot(fn[i], g[i], 'o', color=MAG, ms=9, zorder=5)
        ax.annotate('peak gain %.2f' % g[i], (fn[i], g[i]),
                    xytext=(fn[i] + 0.30, g[i] + 0.30), color=MAG, fontsize=10,
                    arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.4))
        ax.axvline(FN0, color=PUR, ls='--', lw=1.3)
        ax.set_xlim(0.5, 2.0)
        ax.set_ylim(0, 3.2)
        ax.set_title(cap, fontsize=10.5, color=NAVY)
        ax.set_xlabel('f / f$_r$')
    axs[0].set_ylabel('gain  M')
    axs[0].text(0.53, 2.95, 'f$_o$', color=PUR, fontsize=11, fontweight='bold')
    foot(fig, 'The tank is the same in all three. Designing it means asking '
              '"does the gain I need still exist at the WORST load?"')
    fig.tight_layout(rect=[0, 0.055, 1, 0.925])
    save(fig, 'f03_gain_walk')


def f04_three_regions():
    fig = plt.figure(figsize=(10.6, 7.0))
    gs = fig.add_gridspec(2, 3, height_ratios=[2.0, 1.35], hspace=0.34,
                          wspace=0.16)
    ask(fig, 'Three operating regions - only the middle one is where you want to be')
    ax = fig.add_subplot(gs[0, :])
    fn = np.linspace(0.45, 2.2, 1400)
    for q in (0.20, 0.45, 1.50):
        ax.plot(fn, [gain_fn(x, q, LAM) for x in fn], color=LT, lw=1.3)
    ax.plot(fn, [gain_fn(x, QPK, LAM) for x in fn], color=NAVY, lw=2.8,
            zorder=4, label='full load  Q = %.2f' % QPK)
    ax.axvspan(0.45, FN0, color=MAG, alpha=0.16)
    ax.axvspan(FN0, 1.0, color=GRN, alpha=0.16)
    ax.axvspan(1.0, 2.2, color=CYA, alpha=0.14)
    ax.axvline(FN0, color=PUR, ls='--', lw=1.7)
    ax.axvline(1.0, color=GREY, ls='--', lw=1.7)
    ax.axhline(1.0, color=GREY, ls=':', lw=1.2)
    ax.set_xlim(0.45, 2.2)
    ax.set_ylim(0, 2.0)
    ax.set_xlabel('normalised frequency   f / f$_r$')
    ax.set_ylabel('gain   M')
    ax.legend(loc='upper right', fontsize=9.5)
    # short tags inside the bands, and the two resonances above the axis
    for x, t, c in (((0.45 + FN0) / 2, '(3)', MAG),
                    ((FN0 + 1.0) / 2, '(2)', GRN), (1.6, '(1)', CYA)):
        ax.text(x, 1.86, t, color=c, fontsize=15, fontweight='bold',
                ha='center', va='center')
    # the boundary belongs to the curve that is drawn, and this one is loaded
    _pk = max(np.linspace(FN0, 1.0, 900), key=lambda x: gain_fn(x, QPK, LAM))
    ax.plot([_pk], [gain_fn(_pk, QPK, LAM)], marker='*', ms=17, color=MAG,
            mec='white', mew=1.2, zorder=6)
    ax.annotate('peak gain AT THIS LOAD\nthe real capacitive edge is here,\n'
                'not at f$_o$ - it moves right as load rises',
                (_pk, gain_fn(_pk, QPK, LAM)), xytext=(1.22, 1.40),
                color=MAG, fontsize=9.6,
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=MAG,
                          lw=1.0, alpha=0.95),
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.4))
    ax.annotate('f$_o$ = %.1f kHz' % (FO / 1e3), (FN0, 0.22),
                xytext=(FN0 + 0.10, 0.42), color=PUR, fontsize=10.5,
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=PUR,
                          lw=1.0, alpha=0.95),
                arrowprops=dict(arrowstyle='-|>', color=PUR, lw=1.4))
    ax.annotate('f$_r$ = %.1f kHz' % (FR / 1e3), (1.0, 0.22),
                xytext=(1.12, 0.42), color=GREY, fontsize=10.5,
                bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=GREY,
                          lw=1.0, alpha=0.95),
                arrowprops=dict(arrowstyle='-|>', color=GREY, lw=1.4))

    cards = [
        (MAG, '(3)   below the GAIN PEAK',
         'CAPACITIVE. The body diode is\nhard reverse-recovered ->\n'
         'shoot-through current. Devices\ncan be DESTROYED. At no\n'
         'load the edge is f$_o$; under load higher.'),
        (GRN, '(2)   f$_o$ < f < f$_r$   gain > 1',
         'Inductive, ZVS, and the tank\ncan BOOST. The normal LLC\n'
         'region - where a single-stage\nconverter spends most of the\n'
         'line cycle.'),
        (CYA, '(1)   f > f$_r$   gain < 1',
         'Still inductive, still ZVS, but\nthe tank can no longer boost.\n'
         'Used at high line and light\nload.'),
    ]
    for i, (c, head, body) in enumerate(cards):
        a = fig.add_subplot(gs[1, i])
        a.axis('off')
        a.add_patch(Rectangle((0.02, 0.04), 0.96, 0.92, transform=a.transAxes,
                              fc='white', ec=c, lw=1.6, zorder=1))
        a.text(0.07, 0.86, head, transform=a.transAxes, color=c, fontsize=10.5,
               fontweight='bold', va='top', zorder=2)
        a.text(0.07, 0.68, body, transform=a.transAxes, color=NAVY,
               fontsize=9.6, va='top', linespacing=1.55, zorder=2)
    foot(fig, 'Frequency is the only control knob: raise it to cut the gain, '
              'lower it to raise the gain - but never below the gain peak. '
              'f$_o$ is that limit only at no load.   '
              '(region framing after ROHM TechWeb)')
    fig.tight_layout(rect=[0, 0.045, 1, 0.955])
    save(fig, 'f04_three_regions')

def f05_zvs_mechanism():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.8, 5.6), sharex=True,
                                 gridspec_kw=dict(height_ratios=[1.0, 1.0],
                                                  hspace=0.18))
    ask(fig, 'How ZVS actually happens — the magnetising current does the work')
    t = np.linspace(0, 1, 1200)
    dead = 0.055
    vsw = np.where(t < 0.5 - dead / 2, 1.0,
                   np.where(t < 0.5 + dead / 2,
                            1 - (t - (0.5 - dead / 2)) / dead, 0.0))
    a1.plot(t, vsw, color=NAVY, lw=2.6)
    a1.set_ylim(-0.30, 1.80)
    a1.set_yticks([0, 1])
    a1.set_yticklabels(['0', 'V$_{in}$'])
    a1.set_ylabel('bridge midpoint')
    a1.axvspan(0.5 - dead / 2, 0.5 + dead / 2, color=YEL, alpha=0.45)
    note(a1, 0.5, 1.50, 'DEAD TIME  t$_D$\nboth MOSFETs off', color='#8a6d00',
         ha='center', size=10)
    a1.annotate('', xy=(0.5 + dead / 2, 0.16), xytext=(0.5 - dead / 2, 0.94),
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=2.2))
    note(a1, 0.60, 0.52, 'C$_{oss}$ is discharged HERE,\n'
                         'before the next MOSFET turns on', color=MAG, size=10)

    ilm = 0.42 * (2 * np.where(t < 0.5, t / 0.5, (1 - t) / 0.5) - 1)
    ires = 0.95 * np.sin(2 * pi * t)
    a2.plot(t, ires, color=MAG, lw=2.6, label='resonant current  i$_{Lr}$')
    a2.plot(t, ilm, color=CYA, lw=2.4, ls='--',
            label='magnetising current  i$_{Lm}$')
    a2.axhline(0, color=GREY, lw=1.0)
    a2.axvspan(0.5 - dead / 2, 0.5 + dead / 2, color=YEL, alpha=0.45)
    a2.set_ylim(-2.05, 1.45)
    a2.set_xlim(0, 1)
    a2.set_xticks([])
    a2.set_ylabel('current')
    a2.set_xlabel('one switching period')
    a2.legend(loc='upper right', fontsize=9.5)
    a2.plot(0.5, float(np.interp(0.5, t, ilm)), 'o', color=CYA, ms=9, zorder=5)
    note(a2, 0.30, -1.50,
         'At the switching instant the resonant current has NOT\n'
         'reached zero — what is left is the magnetising current.\n'
         'That leftover current is what charges C$_{oss}$.', color=NAVY,
         size=10)
    foot(fig, 'Two conditions, both needed: current must still be flowing at '
              'turn-off (T$_{ZC}$ > t$_D$), AND the transition must finish '
              'inside the dead time (t$_D$ > T$_T$).')
    fig.tight_layout(rect=[0, 0.055, 1, 0.955])
    save(fig, 'f05_zvs_mechanism')


# =============================================================== single stage
def f11_power_balance():
    fig, ax = plt.subplots(figsize=(9.6, 4.9))
    ask(fig, 'The mains delivers a pulsating power, the load wants a constant one')
    th = np.linspace(0, pi, 900)
    p_in = 2 * POUT * np.sin(th) ** 2
    ax.plot(np.degrees(th), p_in, color=MAG, lw=2.7,
            label='instantaneous input   2P·sin²θ')
    ax.axhline(POUT, color=NAVY, lw=2.4,
               label='what the load takes   P = %.0f W' % POUT)
    ax.fill_between(np.degrees(th), POUT, p_in, where=(p_in >= POUT),
                    color=GRN, alpha=0.30)
    ax.fill_between(np.degrees(th), POUT, p_in, where=(p_in < POUT),
                    color=MAG, alpha=0.20)
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 2 * POUT * 1.20)
    ax.set_xticks([0, 45, 90, 135, 180])
    ax.set_xlabel('line phase  θ  [deg]      (half cycle = %.1f ms at 47 Hz)'
                  % (1000 / (2 * 47)))
    ax.set_ylabel('power  [W]')
    ax.legend(loc='upper left', fontsize=9.5)
    for x in (45, 135):
        ax.axvline(x, color=GREY, ls=':', lw=1.3)
    note(ax, 90, 2 * POUT * 0.90, 'surplus → the bank CHARGES', color=GRN,
         ha='center', size=10)
    note(ax, 17, POUT * 0.40, 'deficit →\nthe bank FEEDS the load', color=MAG,
         ha='center', size=10)
    note(ax, 163, POUT * 0.40, 'deficit', color=MAG, ha='center', size=10)
    note(ax, 45, 2 * POUT * 1.10, 'θ = 45°: balance point\n= the ripple trough',
         color=NAVY, ha='center', size=9.8)
    foot(fig, 'The two shaded areas are equal — %.2f J. In a two-stage supply '
              'the 400 V bulk capacitor does this; here the OUTPUT bank does, '
              'and that is why the ripple condition alone asks for %d mF.'
              % (POUT / (2 * pi * 47), round(R['Cout_req'] * 1e3)))
    fig.tight_layout(rect=[0, 0.055, 1, 0.945])
    save(fig, 'f11_power_balance')


def f12_two_divergences():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.0, 5.0))
    ask(fig, 'Near the mains zero crossing the required gain goes to infinity - '
             'so how does it work?')
    deg = np.linspace(1.2, 90, 700)
    thr = np.radians(deg)
    Vac = R['Vin_min']
    Mreq = 2 * N * VOE / (sqrt(2) * Vac * np.sin(thr))
    Q = QPK * np.sin(thr) ** 2
    ceil = np.array([gain_fn(FN0 * 1.0002, q, LAM) if q > 1e-7 else 300
                     for q in Q])

    a1.fill_between(deg, Mreq, ceil, color=GRN, alpha=0.22)
    a1.plot(deg, Mreq, color=MAG, lw=2.8, label='what the grid DEMANDS')
    a1.plot(deg, ceil, color=PUR, lw=2.4, ls='--',
            label='what the tank can DELIVER')
    a1.set_yscale('log')
    a1.set_xlim(0, 90)
    a1.set_ylim(0.8, 300)
    a1.set_xticks([0, 15, 30, 45, 60, 75, 90])
    a1.set_xlabel('line phase  theta  [deg]')
    a1.set_ylabel('gain   (log scale)')
    a1.legend(loc='lower left', fontsize=9.5)
    a1.set_title('1   both blow up - but the ceiling stays ABOVE',
                 fontsize=11, color=NAVY)
    note(a1, 47, 40,
         'The green gap is the margin.\nIt never closes, because the load\n'
         'vanishes as sin^2(theta) and a vanishing\nload lifts the ceiling to '
         'infinity at f_o.', color=GRN, size=10)

    rows, _ = sweep(R, Vac, N=361)
    ok = [r for r in rows if r]
    a2.plot([np.degrees(r['th']) for r in ok], [r['fsw'] / 1e3 for r in ok],
            color=NAVY, lw=2.8)
    a2.axhline(FO / 1e3, color=PUR, ls='--', lw=2.0)
    a2.axhspan(FO / 1e3 - 8, FO / 1e3, color=MAG, alpha=0.12)
    a2.set_xlim(0, 90)
    a2.set_ylim(FO / 1e3 - 8, 138)
    a2.set_xticks([0, 15, 30, 45, 60, 75, 90])
    a2.set_xlabel('line phase  theta  [deg]')
    a2.set_ylabel('switching frequency  [kHz]')
    a2.set_title('2   so the frequency just walks down to f$_o$', fontsize=11,
                 color=NAVY)
    note(a2, 4, 130, 'theta = 90 deg, line peak\nmost power -> highest frequency',
         color=NAVY, size=10, ha='left')
    note(a2, 86, FO / 1e3 + 7,
         'f$_o$ = %.1f kHz\nthe frequency FLOOR' % (FO / 1e3), color=PUR,
         ha='right', size=10)
    a2.text(45, FO / 1e3 - 4.5, 'capacitive - never go here', color=MAG,
            fontsize=9.5, ha='center', va='center')
    foot(fig, 'Near theta = 0 the converter delivers almost no power - and it '
              'does not need to: the output capacitor bank is feeding the load '
              'there (previous figure).')
    fig.tight_layout(rect=[0, 0.055, 1, 0.925])
    save(fig, 'f12_two_divergences')

def f13_morphing():
    fig, (aW, aE) = plt.subplots(1, 2, figsize=(13.2, 5.2),
                                 gridspec_kw=dict(width_ratios=[1.0, 1.06],
                                                  wspace=0.20))
    ask(fig, 'Topology morphing - change the BRIDGE, and a 2.93:1 mains becomes 1.92:1')

    # ONE axes, ONE scale, so twice as tall LOOKS twice as tall
    t = np.linspace(0, 2, 1200)
    sq = np.where((t % 1) < 0.5, 1.0, -1.0)
    aW.plot(t, 0.5 * sq + 1.9, color=NAVY, lw=2.6)          # HB, offset up
    aW.plot(t, sq - 1.4, color=MAG, lw=2.6)                 # FB, offset down
    aW.axhline(1.4, color=GREY, lw=1.0, ls=':')
    aW.axhline(-1.4, color=GREY, lw=1.0, ls=':')
    aW.set_xlim(-0.06, 2.62)
    aW.set_ylim(-3.15, 3.15)
    aW.set_xticks([])
    aW.set_yticks([])
    aW.grid(False)
    aW.set_title('the same silicon, two different bridges', fontsize=11,
                 color=NAVY)
    aW.text(0, 2.72, 'HALF bridge - only leg 1 switches', color=NAVY,
            fontsize=10.5, fontweight='bold', va='bottom')
    aW.text(0, -2.72, 'FULL bridge - leg 2 switches 180 deg out of phase',
            color=MAG, fontsize=10.5, fontweight='bold', va='top')
    for y0, y1, c, lab in ((1.4, 2.4, NAVY, 'V$_{in}$'),
                           (-2.4, -0.4, MAG, '2 x V$_{in}$')):
        aW.annotate('', xy=(2.28, y1), xytext=(2.28, y0),
                    arrowprops=dict(arrowstyle='<|-|>', color=c, lw=2.0))
        aW.text(2.36, (y0 + y1) / 2, lab, color=c, fontsize=12,
                fontweight='bold', va='center')
    aW.text(1.0, 0.02, 'same vertical scale - the full bridge really is twice '
            'as tall', color=GREY, fontsize=9.5, ha='center', va='center')

    vac = np.linspace(85, 270, 900)
    eq = np.where(vac * sqrt(2) <= 235, 2 * vac, vac)
    aE.axhspan(173.24, 332.34, color=YEL, alpha=0.20)
    aE.plot(vac, eq, color=NAVY, lw=3.0)
    aE.plot([166.17, 166.17], [166.17, 332.34], color=GREY, ls=':', lw=1.6)
    aE.plot(166.17, 332.34, 'o', color=MAG, ms=10, zorder=5)
    aE.plot(173.24, 173.24, 'o', color=PUR, ms=10, zorder=5)
    aE.set_xlim(85, 272)
    aE.set_ylim(140, 392)
    aE.set_xlabel('mains voltage  [Vac]')
    aE.set_ylabel('what the TANK sees  [Vac equivalent]')
    aE.set_title('mains 2.93:1  ->  tank 1.92:1', fontsize=11, color=NAVY)
    note(aE, 92, 300, 'FULL bridge\nequivalent = 2 x mains', color=MAG, size=10)
    note(aE, 268, 196, 'HALF bridge\nequivalent = mains', color=NAVY, size=10,
         ha='right')
    note(aE, 150, 375, '332.3 V  MAXIMUM\nat only 166 Vac mains', color=MAG,
         size=9.8, ha='center')
    note(aE, 232, 152, '173.2 V  minimum', color=PUR, size=9.8, ha='center')
    aE.annotate('', xy=(167.5, 335), xytext=(163, 362),
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.5))
    foot(fig, 'Half bridge is entered at 245 V peak going up and full bridge '
              'returns at 235 V peak coming down - 10 V of hysteresis - and the '
              'change is made by holding LOUT2 statically high, no extra hardware. '
              'The worst corners are these EDGES, not the ends of the mains range.')
    fig.tight_layout(rect=[0, 0.055, 1, 0.935])
    save(fig, 'f13_morphing')

def f14_fsw_theta():
    fig, ax = plt.subplots(figsize=(9.8, 5.1))
    ask(fig, 'Where does the switching frequency actually peak?')
    fam = [(R['Vin_min'], MAG, '173.2 Vac eq.  (HB morphing edge)'),
           (180.0, CYA, '180 Vac eq.  (90 Vac mains, FB)'),
           (225.0, GRN, '225 Vac eq.'),
           (264.0, NAVY, '264 Vac  (mains maximum, HB)'),
           (R['Vin_FBmax'], PUR, '332.3 Vac eq.  (FB morphing edge)')]
    top = 0.0
    for vac, c, lab in fam:
        rows, S = sweep(R, vac, N=361)
        ok = [r for r in rows if r]
        ax.plot([np.degrees(r['th']) for r in ok],
                [r['fsw'] / 1e3 for r in ok], color=c, lw=2.4, label=lab)
        top = max(top, S['fsw_max'] / 1e3)
    ax.axhline(FO / 1e3, color=GREY, ls=':', lw=1.6)
    ax.axhline(top, color=YEL, ls='--', lw=2.2)
    ax.set_xlim(0, 90)
    ax.set_ylim(FO / 1e3 - 9, top + 30)
    ax.set_xticks([0, 15, 30, 45, 60, 75, 90])
    ax.set_xlabel('line phase  θ  [deg]')
    ax.set_ylabel('switching frequency  [kHz]')
    ax.legend(loc='upper left', fontsize=9.2)
    note(ax, 88, top + 15, '%.1f kHz  ←  the real maximum' % top,
         color='#8a6d00', ha='right', size=10)
    note(ax, 88, FO / 1e3 - 3.8,
         'f$_o$ = %.1f kHz — every curve converges here at θ → 0' % (FO / 1e3),
         color=GREY, ha='right', size=10)
    foot(fig, 'The highest curve is NOT the maximum mains (264 V) — it is the '
              'FB morphing edge at 332 V equivalent. Miss morphing and you '
              'never plot that curve.')
    fig.tight_layout(rect=[0, 0.055, 1, 0.945])
    save(fig, 'f14_fsw_theta')


# ===================================================================== guide
# The four figures the design guide prints. Korean labels, because that is the
# guide's language; the deck figures above stay English.

def g_gain_regions():
    """게인 곡선 - f_o 가 왜 주파수 하한인가"""
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    fn = np.linspace(0.45, 2.0, 900)
    for q, c, lw in ((0.0, GREY, 1.4), (0.25, CYA, 1.8),
                     (QPK, NAVY, 2.6), (1.5, MAG, 1.8)):
        ax.plot(fn, [gain_fn(f, q, LAM) for f in fn], color=c, lw=lw,
                label=('무부하 Q=0' if q == 0 else
                       ('전부하 Q=%.3f' % q)
                       if abs(q - QPK) < 1e-9 else 'Q=%.2f' % q))
    ax.axvline(FN0, color=YEL, lw=2.4, zorder=1)
    ax.axvline(1.0, color=GREY, lw=1.0, ls=':')
    ax.axhline(R['MVmin'], color=GRN, lw=1.6, ls='--')
    ax.set_xlim(0.45, 2.0)
    ax.set_ylim(0, 3.2)
    ax.set_xlabel('정규화 주파수  $f_n=f_{sw}/f_r$')
    ax.set_ylabel('게인  $M$')
    note(ax, FN0 + 0.03, 2.85,
         '$f_o$ = %.1f kHz\n무부하 게인이 여기서 발산한다\n→ 주파수 하한'
         % (FO / 1e3), color=NAVY)
    note(ax, 1.55, R['MVmin'] + 0.12,
         '요구 게인 %.3f (저입력 코너)' % R['MVmin'], color=GRN, size=10)
    note(ax, 1.02, 0.35, '$f_r$ = %.1f kHz' % (FR / 1e3), color=GREY, size=10)
    ax.legend(loc='upper right', fontsize=10)
    ask(fig, '왜 $f_o$ 가 주파수 하한인가 — 무부하 게인이 거기서 발산하기 때문')
    foot(fig, '본 설계 탱크($\\lambda_{act}$ = %.2f)로 실제 계산한 게인 곡선. '
              '부하가 무거울수록 곡선이 낮고 평탄해진다.' % LAM)
    save(fig, 'gain_regions')


def g_fsw_theta():
    """라인 반주기에 걸친 f_sw - 이것이 곧 PFC"""
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    for vac, c, lab in ((R['Vin_min'], NAVY, 'HB 코너 173.2 Vac 등가'),
                        (225., CYA, '225 Vac'),
                        (R['Vin_FBmax'], MAG, 'FB 코너 332.3 Vac 등가')):
        rows, _ = sweep(R, vac, N=361)
        ok = [r for r in rows if r]
        ax.plot([r['th'] * 180 / pi for r in ok],
                [r['fsw'] / 1e3 for r in ok], color=c, lw=2.3, label=lab)
    ax.axhline(FO / 1e3, color=YEL, lw=2.0, ls='--')
    ax.axhline(FR / 1e3, color=GREY, lw=1.0, ls=':')
    ax.set_xlim(0, 90)
    ax.set_xlabel('라인 위상  $\\theta$  [deg]   (0 = 영교차, 90 = 라인 피크)')
    ax.set_ylabel('$f_{sw}$  [kHz]')
    note(ax, 4, FO / 1e3 + 9, '$f_o$ = %.1f kHz\n모든 곡선이 영교차에서\n여기로 수렴한다'
         % (FO / 1e3), color=NAVY, size=10)
    note(ax, 62, 232, '상한 %.1f kHz\n= FB 코너, 264 Vac 가 아니다'
         % (R['fr'] * 1.6448 / 1e3), color=MAG, size=10)
    ax.legend(loc='center right', fontsize=10)
    ask(fig, '$f_{sw}(\\theta)$ 변조가 곧 역률 보정이다')
    foot(fig, '주파수가 조절하는 것은 게인이 아니라 $Q$, 즉 전력이다. '
              '게인은 양쪽 포트가 전압원이라 경계조건으로 강제된다.')
    save(fig, 'fsw_theta')


def _tank_current(T, name):
    """composite tank current - T carries every visible string"""
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    rows, _ = sweep(R, R['Vin_min'], N=361)
    w = max((r for r in rows if r), key=lambda r: r['Ipk'])
    x = np.linspace(0, 1, 600)
    itr = w['Itr'] * np.sin(pi * x)
    ilm = w['ILm'] * (2 * x - 1)
    ax.plot(x, itr, color=CYA, lw=2.0, ls='--', label=T['refl'])
    ax.plot(x, ilm, color=GRN, lw=2.0, ls='--', label=T['mag'])
    ax.plot(x, itr + ilm, color=NAVY, lw=2.8, label=T['comp'])
    k = int(np.argmax(itr + ilm))
    ax.plot(x[k], (itr + ilm)[k], 'o', color=MAG, ms=9, zorder=6)
    ax.axhline(0, color=GREY, lw=0.9)
    ax.set_xlim(0, 1)
    # headroom for the legend, which otherwise covers the peaks
    _lo = min(float((itr + ilm).min()), float(itr.min()), float(ilm.min()))
    _hi = max(float((itr + ilm).max()), float(itr.max()), float(ilm.max()))
    ax.set_ylim(_lo * 1.12, _hi * 1.42)
    ax.set_xlabel(T['xlab'])
    ax.set_ylabel(T['ylab'])
    # this annotation used to sit above the axis limit and was clipped away -
    # park it in the empty lower right and point an arrow at the marker
    ax.annotate(T['pk'] % w['comp'],
                xy=(x[k], (itr + ilm)[k]), xytext=(0.46, -7.5),
                color=MAG, fontsize=10, ha='left', va='center', zorder=6,
                bbox=dict(boxstyle='round,pad=0.35', fc='white', ec=MAG,
                          lw=1.1, alpha=0.96),
                arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.4,
                                shrinkA=4, shrinkB=6))
    # the two component peaks used to sit in a box that covered the legend -
    # they belong in the footer, where there is room for them
    ax.legend(loc='upper left', fontsize=10)
    ask(fig, T['ask'])
    foot(fig, T['foot']
              % (w['Itr'], w['ILm'], w['comp'], 100 * (w['comp'] / w['Itr'] - 1)))
    save(fig, name)

_TANK_CURRENT_KO = {
    'refl':   '반사 부하 $i_{trafo}$',
    'mag':    '자화 $i_{Lm}$',
    'comp':   '합성 $i_{Lr}$  ← 이것을 본다',
    'xlab':   '스위칭 반주기 [정규화]',
    'ylab':   '전류 [A]',
    'pk':     '$I_{Lr,pk}$ = %.2f A\n두 성분의 피크를 더한 값이 아니다 —\n'
              '서로 다른 순간에 피크를 친다',
    'ask':    '$R_{CS}$ 와 1차 소자가 보는 것은 합성 탱크 전류다',
    'foot':   '반사 부하 %.2f A · 자화 %.2f A · 합성 %.2f A.  '
              '가이드 [79]·[115]와 ST 툴이 모두 반사 부하 전류를 쓰고 있었다 — '
              '정격이 %.0f %% 부족했다 (부록 C.14 · C.28).',
}

_TANK_CURRENT_EN = {
    'refl':   'reflected load  $i_{trafo}$',
    'mag':    'magnetising  $i_{Lm}$',
    'comp':   'composite  $i_{Lr}$  -- this is what the switch sees',
    'xlab':   'switching half period  [normalised]',
    'ylab':   'current  [A]',
    'pk':     '$I_{Lr,pk}$ = %.2f A\nNOT the sum of the two peaks -\n'
              'they occur at different instants',
    'ask':    'The composite tank current is what $R_{CS}$ and the primary devices see',
    'foot':   'Reflected load %.2f A, magnetising %.2f A, composite %.2f A.  '
              'Rating the primary switch on the reflected load current alone '
              'falls %.0f %% short of the composite peak.',
}


def g_tank_current():
    _tank_current(_TANK_CURRENT_KO, 'tank_current')


def an_tank_current():
    _tank_current(_TANK_CURRENT_EN, 'an_tank_current')


def _loop_bode(T, name):
    """open-loop gain and phase margin - T carries every visible string"""
    import snapshot as S
    v, _ = S.read_sheet(S.SM)
    g = lambda k: v[k][0]
    # EXACTLY the sheet's expression (16.6). The plant is two integrators, so
    # |T| = G.o*EA.oi/w^2 * A(w) and the phase margin IS the compensator's own
    # phase. Rebuilding T(s) by hand put the 0 dB crossing at 300 Hz.
    Go, EAoi = g('G.o'), g('EA.oi')
    wz, wp, wpx = g('\u03c9.z'), g('\u03c9.p'), g('\u03c9.px')
    f = np.logspace(0, 3.3, 900)
    w = 2 * pi * f
    A = np.sqrt(1 + (w / wz) ** 2) / (np.sqrt(1 + (w / wp) ** 2)
                                      * np.sqrt(1 + (w / wpx) ** 2))
    TdB = 20 * np.log10(Go * EAoi / w ** 2 * A)
    PM = np.degrees(np.arctan(w / wz) - np.arctan(w / wp)
                    - np.arctan(w / wpx))
    fc, pm, fl2 = g('f.cross'), g('\u03a6.act'), 2 * R['fl_min']

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.6, 5.9), sharex=True,
                                 gridspec_kw={'height_ratios': [1.2, 1]})
    a1.semilogx(f, TdB, color=NAVY, lw=2.5)
    a1.axhline(0, color=GREY, lw=1.0)
    a1.set_ylabel('$|T|$  [dB]')
    a2.semilogx(f, PM, color=MAG, lw=2.5)
    a2.axhline(45, color=GRN, lw=1.5, ls='--')
    a2.set_ylabel(T['ylab2'])
    a2.set_xlabel(T['xlab'])
    for a in (a1, a2):
        a.axvline(fc, color=YEL, lw=2.2, zorder=1)
        a.axvline(fl2, color=GREY, lw=1.1, ls=':')
        a.set_xlim(1, 2000)
    a1.set_ylim(-45, 55)
    a2.set_ylim(0, 95)
    note(a1, fc * 1.4, 40, T['fc'] % fc, color=NAVY, size=10.5)
    note(a2, fc * 1.4, 20, T['pm'] % pm,
         color=MAG, size=10.5)
    note(a1, fl2 * 1.3, -30,
         T['fl2'] % fl2,
         color=GREY, size=9.5)
    ask(fig, T['ask'] % fc)
    foot(fig, T['foot'])
    save(fig, name)


def _morph_levels(T, name):
    """where it is FB and where it is HB - T carries every visible string"""
    VBO = 30.0 * 4 / sqrt(2)            # R_CFG 30 kohm -> 120 Vpk
    BOH, BIH = 235 / sqrt(2), 245 / sqrt(2)
    LO, HI = 60., 285.
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.4, 6.8), sharex=True,
                                 gridspec_kw={'height_ratios': [1.0, 1.3]})

    # ---- upper: one lane per direction. The band is NOT filled here - the
    # whole point is that the two lanes differ inside it, and a fill hides that.
    for y, lab, flip in ((0.70, T['up'], BIH),
                         (0.26, T['down'], BOH)):
        a1.add_patch(Rectangle((LO, y - .105), VBO - LO, .21, fc=LT, ec='none'))
        a1.add_patch(Rectangle((VBO, y - .105), flip - VBO, .21,
                               fc=CYA, ec='none', alpha=.85))
        a1.add_patch(Rectangle((flip, y - .105), HI - flip, .21,
                               fc=NAVY, ec='none', alpha=.90))
        a1.text((VBO + flip) / 2, y, 'FULL BRIDGE', ha='center', va='center',
                color='white', fontsize=11.5, fontweight='bold')
        a1.text((flip + HI) / 2, y, 'HALF BRIDGE', ha='center', va='center',
                color='white', fontsize=11.5, fontweight='bold')
        a1.text((LO + VBO) / 2, y, T['stop'], ha='center', va='center',
                color=GREY, fontsize=10)
        a1.text(LO + 2, y + .155, lab, ha='left', va='bottom', color=NAVY,
                fontsize=11, fontweight='bold')
    a1.set_ylim(0, 1.0)
    a1.set_yticks([])
    # the band, as edges only, plus the sentence that makes it matter
    for xv in (BOH, BIH):
        a1.axvline(xv, color='#B08900', lw=1.6, ls='--', zorder=5)
    a1.annotate('', xy=(BIH, .875), xytext=(BOH, .875),
                arrowprops=dict(arrowstyle='<->', color='#B08900', lw=1.8))
    a1.text((BOH + BIH) / 2, .985, T['hyst'], ha='center', va='top',
            color='#8a6d00', fontsize=10.5, fontweight='bold')
    note(a1, HI - 4, .48,
         T['same'],
         color=MAG, size=10, ha='right', va='center')

    # ---- lower: what the TANK sees, and the 2:1 step at the transition
    v = np.linspace(VBO, BIH, 200)
    a2.plot(v, 2 * v, color=CYA, lw=3.2, label=T['legFB'])
    v2 = np.linspace(BOH, HI, 200)
    a2.plot(v2, v2, color=NAVY, lw=3.2, label=T['legHB'])
    a2.axhspan(BOH, 2 * BIH, color=GRN, alpha=.10, zorder=0)
    for xv in (BOH, BIH):
        a2.axvline(xv, color='#B08900', lw=1.6, ls='--', zorder=1)
        a2.annotate('', xy=(xv, 2 * xv), xytext=(xv, xv),
                    arrowprops=dict(arrowstyle='<|-|>', color=MAG, lw=2.0))
        for yy in (xv, 2 * xv):
            a2.plot(xv, yy, 'o', color=MAG, ms=7.5, zorder=6)
    a2.set_ylim(0, 400)
    a2.set_ylabel(T['ylab'])
    a2.set_xlabel(T['xlab'])
    a2.legend(loc='upper left', fontsize=10.5)
    note(a2, BIH + 8, 318,
         T['step'], color=MAG, size=10)
    note(a2, 70, 120, T['range'],
         color=GRN, size=10)

    for a in (a1, a2):
        a.set_xlim(LO, HI)
        a.axvline(VBO, color=GREY, lw=1.2, ls='--', zorder=1)
        a.set_axisbelow(True)
    # thresholds labelled ONCE, in the gap between the panels
    # 166.2 and 173.2 are seven volts apart - centring both captions on their
    # own line printed one on top of the other. One to each side of the band.
    # no number here - V_BO is set by R_CFG, which the power-stage chapter
    # has not chosen yet. The line's POSITION is this design's; the label is not.
    a1.text(VBO, -0.06, T['vbo'], ha='center', va='top',
            fontsize=9.5, color=GREY)
    a1.text(BOH - 3, -0.06, '235 $V_{pk}$\n166.2 V', ha='right', va='top',
            fontsize=9.5, color='#8a6d00')
    a1.text(BIH + 3, -0.06, '245 $V_{pk}$\n173.2 V', ha='left', va='top',
            fontsize=9.5, color='#8a6d00')
    for mv, lab in ((100, '100 V'), (120, '120 V'), (230, '230 V')):
        a1.plot(mv, 1.0, 'v', color=PUR, ms=9, clip_on=False)
        a1.text(mv, 1.02, lab, ha='center', va='bottom', color=PUR, fontsize=9)

    ask(fig, T['ask'])
    foot(fig, T['foot'])
    fig.tight_layout(rect=[0, 0.06, 1, 0.945])
    fig.subplots_adjust(hspace=0.42)
    save(fig, name)

# ======================================================= morphing, in detail
#
# The bridge itself, which the deck never drew. Everything here is geometry -
# no numbers are computed, so nothing can drift out of step with l6790.py.

_HI, _LO, _MID = 3.30, 0.0, 1.68        # rail and midpoint heights
_L1, _L2 = 1.15, 4.55                   # the two legs
_BW, _BH = 0.52, 0.62                   # switch box


_MORPH_KO = {
    'up':    '전압이 올라갈 때  →',
    'down':  '전압이 내려갈 때  ←',
    'stop':  '정지',
    'hyst':  '히스테리시스',
    'same':  '같은 전압인데 위 레인은 아직 FB, 아래 레인은 이미 HB —\n'
         '어느 쪽에서 왔는지가 모드를 정한다',
    'legFB': 'FB — 탱크는 라인의 2배를 본다',
    'legHB': 'HB — 탱크는 라인 그대로를 본다',
    'ylab':  '탱크가 보는 등가 입력 [Vac]',
    'xlab':  '상용전원 [Vrms]',
    'step':  '전환 순간 탱크 구동이 2배로 뛴다 —\n'
         '$f_{sw}$ 가 123 → 250 kHz 로 따라가야 한다',
    'range': '설계가 감당해야 하는 범위\n166.2 ~ 346.5 Vac  (2.08 : 1)',
    'vbo':   '$V_{BO}$\n($R_{CFG}$ 가 정함)',
    'ask':   'Morphing — 어디까지가 풀브리지이고 어디부터 하프브리지인가',
    'foot':  '경계 235 / 245 $V_{pk}$ 는 IC 고정 상수라 움직이지 않는다. '
              'morphing 을 켤지와 $V_{BO}$ 를 어디에 둘지는 $R_{CFG}$ 가 정한다 — '
              'CFG 핀 절 참조. 실사용 계통(보라 삼각형)은 밴드 밖에 있어 기동 때 모드가 '
              '정해지고 그대로 간다.',
}

_MORPH_EN = {
    'up':    'as the mains RISES  \u2192',
    'down':  'as the mains FALLS  \u2190',
    'stop':  'stopped',
    'hyst':  'hysteresis',
    'same':  'same mains voltage: the upper lane is still FB, the lower\n'
         'lane is already HB \u2014 the DIRECTION of travel decides',
    'legFB': 'FB \u2014 tank sees TWICE the mains',
    'legHB': 'HB \u2014 tank sees the mains as it is',
    'ylab':  'what the TANK sees  [Vac equivalent]',
    'xlab':  'mains  [Vrms]',
    'step':  'the drive jumps 2:1 at the transition \u2014\n'
         '$f_{sw}$ must follow it from 123 to 250 kHz',
    'range': 'the range the design must cover\n166.2 to 346.5 Vac  (2.08 : 1)',
    'vbo':   '$V_{BO}$\n(set by $R_{CFG}$)',
    'ask':   'Morphing \u2014 where it is a full bridge, and where it is a half bridge',
    'foot':  'The 235 / 245 $V_{pk}$ thresholds are FIXED IC constants. '
              '$R_{CFG}$ decides only whether morphing is enabled and where '
              '$V_{BO}$ sits. Real mains (purple markers) lies outside the '
              'band, so the mode is settled at start-up and stays.',
}

_LOOP_BODE_KO = {
    'ylab2':  '위상 여유  [deg]',
    'xlab':   '주파수 [Hz]',
    'fc':     '교차 %.1f Hz',
    'pm':     '$\\Phi_M$ = %.1f°\n합격선 45°',
    'fl2':    '$2f_l$ = %d Hz\n여기 이득이 3차 고조파를 정한다',
    'ask':    '루프는 $2f_l$ 리플을 따라가면 안 된다 — 그래서 %.0f Hz 에서 교차한다',
    'foot':   '선정 보상망의 개루프 이득. 교차를 더 올리면 루프가 출력 리플을 좇아 '
              '입력 전류에 3차 고조파가 실린다. 시트 16.6 과 같은 식.',
}

_LOOP_BODE_EN = {
    'ylab2':  'phase margin  [deg]',
    'xlab':   'frequency  [Hz]',
    'fc':     'crossover %.1f Hz',
    'pm':     '$\\Phi_M$ = %.1f°\nlimit 45°',
    'fl2':    '$2f_l$ = %d Hz\nthe gain here sets the 3rd harmonic',
    'ask':    'The loop must NOT follow the $2f_l$ ripple - hence a %.0f Hz crossover',
    'foot':   'Open-loop gain of the selected compensation network. Raising '
              'the crossover makes the loop chase the output ripple and puts '
              'third harmonic on the input current.',
}


def g_loop_bode():
    _loop_bode(_LOOP_BODE_KO, 'loop_bode')


def an_loop_bode():
    _loop_bode(_LOOP_BODE_EN, 'an_loop_bode')


def g_morphing_levels():
    _morph_levels(_MORPH_KO, 'morphing_levels')


def f18_morph_levels():
    _morph_levels(_MORPH_EN, 'f18_morph_levels')


def _sw(ax, x, y, label, state):
    """one switch: 'on' conducting, 'off' blocked, 'static' permanently on"""
    fc = {'on': YEL, 'static': GRN, 'off': 'white'}[state]
    ec = {'on': MAG, 'static': GRN, 'off': GREY}[state]
    lw = 2.4 if state != 'off' else 1.3
    ax.add_patch(plt.Rectangle((x - _BW / 2, y - _BH / 2), _BW, _BH,
                               fc=fc, ec=ec, lw=lw, zorder=3))
    ax.text(x, y, label, ha='center', va='center', fontsize=10.5,
            fontweight='bold', color=NAVY, zorder=4)


def _bridge(ax, states, path, title, vlabel):
    """states: dict Q1..Q4 -> on|off|static.  path: list of (x, y) to trace."""
    ax.set_xlim(-0.55, 6.25)
    ax.set_ylim(-0.85, 4.35)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)

    # rails
    ax.plot([-0.25, 5.95], [_HI, _HI], color=NAVY, lw=2.0)
    ax.plot([-0.25, 5.95], [_LO, _LO], color=NAVY, lw=2.0)
    ax.text(-0.35, _HI, 'V$_{in}$', ha='right', va='center', fontsize=11,
            fontweight='bold', color=NAVY)
    ax.text(-0.35, _LO, 'GND', ha='right', va='center', fontsize=10,
            color=GREY)

    # legs
    for x, (qh, ql) in ((_L1, ('Q1', 'Q2')), (_L2, ('Q3', 'Q4'))):
        ax.plot([x, x], [_LO, _HI], color=GREY, lw=1.4, zorder=1)
        _sw(ax, x, 2.55, qh, states[qh])
        _sw(ax, x, 0.80, ql, states[ql])
        ax.plot(x, _MID, 'o', color=NAVY, ms=6, zorder=4)

    # the tank, drawn as a block between the two midpoints
    ax.plot([_L1, _L2], [_MID, _MID], color=GREY, lw=1.4, zorder=1)
    ax.add_patch(plt.Rectangle((2.30, _MID - 0.34), 1.30, 0.68, fc=LT,
                               ec=GREY, lw=1.3, zorder=7))
    ax.text(2.95, _MID, 'C$_r$  L$_r$  L$_m$', ha='center', va='center',
            fontsize=10, color=NAVY, zorder=8)

    # the conducting path, traced over the top of everything
    if path:
        xs, ys = zip(*path)
        ax.plot(xs, ys, color=MAG, lw=3.4, alpha=0.55, zorder=5,
                solid_capstyle='round')
        i = len(path) // 2
        ax.annotate('', xy=path[i], xytext=path[i - 1],
                    arrowprops=dict(arrowstyle='-|>', color=MAG, lw=2.6),
                    zorder=6)

    # what the tank sees, as an arrow between the midpoints
    ax.annotate('', xy=(_L2 - _BW, 0.62), xytext=(_L1 + _BW, 0.62),
                arrowprops=dict(arrowstyle='<|-|>', color=PUR, lw=1.8))
    ax.text((_L1 + _L2) / 2, 0.44, vlabel, ha='center', va='top',
            fontsize=11.5, fontweight='bold', color=PUR)
    ax.set_title(title, fontsize=11.5, color=NAVY, pad=8)


def f15_bridge_fb():
    """FULL bridge - both legs switch, 180 deg apart"""
    fig = plt.figure(figsize=(13.2, 5.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.02], wspace=0.13)
    ask(fig, 'FULL bridge - both legs switch, and the tank sees the WHOLE input')

    aA, aB, aW = (fig.add_subplot(gs[0]), fig.add_subplot(gs[1]),
                  fig.add_subplot(gs[2]))

    _bridge(aA, dict(Q1='on', Q2='off', Q3='off', Q4='on'),
            [(_L1, _HI), (_L1, _MID), (_L2, _MID), (_L2, _LO)],
            'first half period:  Q1 + Q4', 'v$_{tank}$ = + V$_{in}$')
    _bridge(aB, dict(Q1='off', Q2='on', Q3='on', Q4='off'),
            [(_L2, _HI), (_L2, _MID), (_L1, _MID), (_L1, _LO)],
            'second half period:  Q2 + Q3', 'v$_{tank}$ = - V$_{in}$')

    t = np.linspace(0, 2, 1200)
    sq = np.where((t % 1) < 0.5, 1.0, -1.0)
    aW.plot(t, sq, color=MAG, lw=2.8)
    aW.axhline(0, color=GREY, lw=1.0, ls=':')
    aW.set_xlim(-0.05, 2.05)
    aW.set_ylim(-1.75, 1.75)
    aW.set_xticks([])
    aW.set_yticks([-1, 0, 1])
    aW.set_yticklabels(['-V$_{in}$', '0', '+V$_{in}$'])
    aW.set_title('v$_{tank}$  \u2014  swing 2 \u00d7 V$_{in}$', fontsize=11.5,
                 color=NAVY, pad=8)
    aW.text(0.5, -0.085, 'fundamental  (4/\u03c0)\u00b7V$_{in}$',
            transform=aW.transAxes, ha='center', va='top',
            fontsize=10, color=GREY)

    foot(fig, 'Diagonal pairs conduct together, so the tank is driven from '
              '+V$_{in}$ to -V$_{in}$ every cycle. Every one of the four '
              'devices switches, and each carries the tank current for half '
              'the period.')
    fig.tight_layout(rect=[0, 0.075, 1, 0.935])
    save(fig, 'f15_bridge_fb')


def f16_bridge_hb():
    """HALF bridge - leg 2 stops, Q4 stands on, Cr blocks the DC"""
    fig = plt.figure(figsize=(13.2, 5.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.02], wspace=0.13)
    ask(fig, 'HALF bridge - leg 2 STOPS, and the tank sees half as much')

    aA, aB, aW = (fig.add_subplot(gs[0]), fig.add_subplot(gs[1]),
                  fig.add_subplot(gs[2]))

    _bridge(aA, dict(Q1='on', Q2='off', Q3='off', Q4='static'),
            [(_L1, _HI), (_L1, _MID), (_L2, _MID), (_L2, _LO)],
            'first half period:  Q1  (Q4 standing)', 'v$_{tank}$ = + V$_{in}$')
    _bridge(aB, dict(Q1='off', Q2='on', Q3='off', Q4='static'),
            [(_L1, _LO), (_L1, _MID), (_L2, _MID), (_L2, _LO)],
            'second half period:  Q2  (Q4 standing)', 'v$_{tank}$ = 0')

    t = np.linspace(0, 2, 1201)[:-1]
    sq = np.where((t % 1) < 0.5, 1.0, 0.0)
    aW.plot(t, sq, color=NAVY, lw=2.8, label='at the bridge')
    aW.plot(t, sq - 0.5, color=MAG, lw=2.8, ls='--',
            label='after C$_r$ blocks the DC')
    aW.axhline(0.5, color=GREY, lw=1.0, ls=':')
    aW.axhline(0, color=GREY, lw=1.0, ls=':')
    aW.set_xlim(0, 2)
    aW.set_ylim(-1.05, 1.45)
    aW.set_xticks([])
    aW.set_yticks([-0.5, 0, 0.5, 1])
    aW.set_yticklabels(['-V$_{in}$/2', '0', '+V$_{in}$/2', 'V$_{in}$'])
    aW.legend(loc='upper right', fontsize=9)
    aW.set_title('v$_{tank}$  \u2014  swing 1 \u00d7 V$_{in}$', fontsize=11.5,
                 color=NAVY, pad=8)
    aW.text(0.5, -0.085, 'fundamental  (2/\u03c0)\u00b7V$_{in}$  '
            '\u2014  exactly half',
            transform=aW.transAxes, ha='center', va='top',
            fontsize=10, color=GREY)

    foot(fig, 'Q3 never turns on and Q4 never turns off, so the leg-2 midpoint '
              'IS ground. The bridge output now swings 0 to V$_{in}$; C$_r$ '
              'blocks the V$_{in}$/2 of DC, leaving the tank a '
              '\u00b1V$_{in}$/2 square wave. No extra hardware - the green '
              'device is simply held on.')
    fig.tight_layout(rect=[0, 0.075, 1, 0.935])
    save(fig, 'f16_bridge_hb')


def f17_morph_gates():
    """the four gate signals, both modes, on one time base"""
    fig, (aF, aH) = plt.subplots(1, 2, figsize=(13.2, 4.9), sharey=True,
                                 gridspec_kw=dict(wspace=0.10))
    ask(fig, 'One pin decides it: LOUT2 switches, or LOUT2 just stays high')

    t = np.linspace(0, 2, 2000)
    a = ((t % 1) < 0.47).astype(float)          # leg 1 high side
    b = (((t + 0.5) % 1) < 0.47).astype(float)  # 180 deg out of phase
    rows = ('HOUT1', 'LOUT1', 'HOUT2', 'LOUT2')

    for ax, sig, ttl in (
            (aF, (a, b, b, a), 'FULL bridge   (mains peak below 235 V)'),
            (aH, (a, b, 0 * t, 1 + 0 * t), 'HALF bridge   (above 245 V)')):
        for i, (nm, s) in enumerate(zip(rows, sig)):
            y = 3 - i
            static = np.ptp(s) == 0
            c = GRN if static and s.max() > 0.5 else (GREY if static else NAVY)
            ax.plot(t, y + 0.62 * s, color=c, lw=2.4)
            ax.text(-0.06, y + 0.31, nm, ha='right', va='center', fontsize=10.5,
                    fontweight='bold', color=c)
            if static:
                ax.text(1.0, y + 0.62 * s.max() + 0.24,
                        'held HIGH  \u2014  Q4 conducts all the time'
                        if s.max() > 0.5 else 'held LOW  \u2014  Q3 never turns on',
                        ha='center', va='center', fontsize=10, color=c,
                        bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=c,
                                  lw=1.1, alpha=0.95))
        ax.set_xlim(-0.55, 2.05)
        ax.set_ylim(-0.35, 4.0)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.set_title(ttl, fontsize=11.5, color=NAVY, pad=8)

    foot(fig, 'The dead time between the two signals of a leg is what ZVS '
              'lives in. Morphing changes nothing else: same pins, same tank, '
              'same control law \u2014 leg 2 simply stops switching, and the '
              'transition is hysteretic so it cannot chatter.')
    fig.tight_layout(rect=[0, 0.085, 1, 0.935])
    save(fig, 'f17_morph_gates')
def f19_cout_criterion():
    """why 75 mF, and why it is the ripple condition that asks for it"""
    fig, (aL, aR) = plt.subplots(1, 2, figsize=(12.6, 5.2),
                                 gridspec_kw=dict(width_ratios=[1.25, 1.0],
                                                  wspace=0.28))
    ask(fig, 'Sizing the output bank - and what the architecture really trades')

    # ---- left: both conditions fall as 1/Vout^2, so Vout cannot separate them
    P, FL, DV, TH, K = 657.5, 47.0, 0.05, 0.012, 19.0 / 25.0
    v = np.linspace(15, 75, 400)
    Cr = P / (2 * pi * FL * DV * v ** 2) * 1e3          # mF
    # hold-up starts at the ripple trough, so the usable window is smaller
    Ch = 2 * P * TH / (v ** 2 * ((1 - DV / 2) ** 2 - K ** 2)) * 1e3   # mF
    CRIP = P / (2 * pi * FL * DV * 25.0 ** 2) * 1e3
    CHLD = 2 * P * TH / (25.0 ** 2 * ((1 - DV / 2) ** 2 - K ** 2)) * 1e3
    LHS, RHS = (1 - DV / 2) ** 2 - K ** 2, 4 * pi * FL * DV * TH
    aL.loglog(v, Cr, color=MAG, lw=3.0, label='ripple:  $\\Delta$v = 5 % pk-pk')
    aL.loglog(v, Ch, color=NAVY, lw=3.0,
              label='hold-up:  12 ms down to 76 % of $V_{out}$')
    aL.axvline(25, color=GREY, lw=1.3, ls='--')
    aL.plot([25, 25], [CRIP, CHLD], 'o', color=PUR, ms=9, zorder=5)
    aL.set_xlim(15, 75)
    aL.set_ylim(8, 260)
    aL.set_xlabel('output voltage  [V]')
    aL.set_ylabel('capacitance required  [mF]')
    aL.set_xticks([15, 20, 25, 30, 40, 50, 60, 75])
    aL.set_yticks([10, 20, 50, 100, 200])
    aL.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    aL.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    aL.legend(loc='upper right', fontsize=10)
    note(aL, 26, 105, '25 V:  %.1f mF ripple\n           %.1f mF hold-up'
         % (CRIP, CHLD), color=PUR, size=10)
    aL.set_title('both conditions go as 1 / $V_{out}^2$ - PARALLEL on log-log',
                 fontsize=11, color=NAVY)
    aL.text(0.5, 0.04,
            'the output voltage cannot decide between them.\n'
            r'ripple wins when   $(1-\Delta v/2)^2 - '
            r'(V_{o,min}/V_{out})^2  >  4\pi f_l \Delta v T_{hold}$'
            '\n'
            'here  %.3f > %.3f,  by %.2fx' % (LHS, RHS, LHS / RHS),
            transform=aL.transAxes, ha='center', va='bottom', fontsize=9.4,
            color=GREY, linespacing=1.5,
            bbox=dict(boxstyle='round,pad=0.32', fc='white', ec=LT, lw=1.0))

    # ---- right: the hold-up energy is the same. Only the voltage changed.
    # USABLE energy, 1/2 C (V^2 - Vmin^2) - not 1/2 C V^2. The bank never
    # gives back the charge below Vmin, so total stored energy compares
    # nothing.
    def _use(c, v, vmin):
        return 0.5 * c * (v ** 2 - vmin ** 2)
    bars = ((274e-6, 400., 320., 'two stage\n274 µF, 400 to 320 V',
             '1 capacitor', 'one bulk\nelectrolytic', NAVY),
            (CHLD * 1e-3, 25., 19.,
             'single stage\n%.1f mF, 25 to 19 V' % CHLD,
             '%d capacitors' % -(-CHLD // 0.47), 'hold-up\nminimum', PUR),
            (75.2e-3, 25., 19., 'as built\n75.2 mF, 25 to 19 V',
             '160 capacitors', 'ripple\ndecided this', MAG))
    en = [_use(c, v, vm) for c, v, vm, _, _, _, _ in bars]
    aR.bar(range(3), en, width=0.56,
           color=[b[6] for b in bars])
    for x, (e, b) in enumerate(zip(en, bars)):
        aR.text(x, e + 0.35, '%.1f J' % e, ha='center', va='bottom',
                fontsize=12.5, fontweight='bold', color=NAVY)
        aR.text(x, e / 2, b[4] + '\n\n' + b[5], ha='center', va='center',
                fontsize=9.4, color='white', fontweight='bold')
    aR.set_xticks(range(3))
    aR.set_xticklabels([b[3] for b in bars], fontsize=9.4)
    aR.set_ylim(0, 13)
    aR.set_ylabel('energy the hold-up can actually use  [J]')
    aR.set_title('the hold-up energy does not go away', fontsize=11,
                 color=NAVY)
    aR.grid(axis='x')

    foot(fig, 'Removing the boost stage removes the 400 V bus, not the energy '
              'it held. The first two bars are the SAME 7.9 J - 12 ms at full '
              'power - and the capacitance between them differs by '
              '(400$^2$-320$^2$)/((25-0.6)$^2$-19$^2$) = 245x. That single line is '
              'the cost of the architecture. The bank actually built is '
              'larger again because RIPPLE, not hold-up, set its size.')
    fig.tight_layout(rect=[0, 0.10, 1, 0.935])
    save(fig, 'f19_cout_criterion')

import figs_intro                                                    # noqa: E402

FIGS = {'f02': f02_two_resonances, 'f03': f03_gain_walk,
        'f04': f04_three_regions, 'f05': f05_zvs_mechanism,
        'f11': f11_power_balance, 'f12': f12_two_divergences,
        'f13': f13_morphing, 'f14': f14_fsw_theta,
        'f15': f15_bridge_fb, 'f16': f16_bridge_hb,
        'f17': f17_morph_gates, 'f18': f18_morph_levels,
        'f19': f19_cout_criterion,
        'an_tank_current': an_tank_current,
        'an_loop_bode': an_loop_bode,
        'gain_regions': g_gain_regions,
        'fsw_theta': g_fsw_theta,
        'tank_current': g_tank_current,
        'loop_bode': g_loop_bode,
        'morphing_levels': g_morphing_levels}
# the background circuit drawings live in their own module
FIGS.update({k: (lambda f=f: f(save, foot))
             for k, f in figs_intro.FIGS.items()})

import figs_modes                                                    # noqa: E402
FIGS['an_above_below'] = lambda: figs_modes.an_above_below(
    save, foot, R, sweep, FR)
FIGS['an_zvs_zcs'] = lambda: figs_modes.an_zvs_zcs(save, foot)

if __name__ == '__main__':
    argv = sys.argv[1:]
    if '--plain' in argv:
        argv.remove('--plain')
        PLAIN = True
    want = argv or sorted(FIGS)
    print('figures -> %s' % OUT)
    for k in want:
        if k not in FIGS:
            raise SystemExit('unknown figure %s  (have: %s)'
                             % (k, ' '.join(sorted(FIGS))))
        FIGS[k]()
