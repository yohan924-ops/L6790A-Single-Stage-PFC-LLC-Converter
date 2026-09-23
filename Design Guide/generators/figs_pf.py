# -*- coding: utf-8 -*-
"""How a single-stage PFC LLC corrects the power factor, and how its gain
chart differs from an ordinary LLC's.

Three drawings, added because the note stated the control law as three
equations and never showed it (2026-09-22, user):

  an_pf_chain       one line half cycle, four panels: what unity power
                    factor asks for, the power that implies, what that
                    asks of the tank, and the f_sw(theta) that answers it
  an_gain_compare   the ordinary gain chart beside the single-stage one,
                    because the two look alike and are read differently
  an_gain_design    the same single-stage chart on the worked design's
                    own numbers, at the two corners that decide it

Nothing is typed in: the curves come from l6790, and the design figure
takes its operating points from the same sweep the tables are built from,
so a marker on the curve and a number in a table cannot disagree.
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

from schem import NAVY, MAG, CYA, GRN, PUR, GREY, LT, YEL
from l6790 import M, zvs_edge

HALO = [pe.withStroke(linewidth=3.4, foreground='white')]
PHASES = ((np.pi / 2, u'θ = 90°  (line peak)', MAG),
          (np.pi / 3, u'θ = 60°', CYA),
          (np.pi / 4, u'θ = 45°', PUR))


def _tidy(ax, xl, yl):
    ax.set_xlabel(xl, fontsize=10.5, color=NAVY)
    ax.set_ylabel(yl, fontsize=10.5, color=NAVY)
    ax.tick_params(labelsize=9.4, colors=GREY)
    ax.grid(True, color='#C4C8CF', lw=0.7)
    ax.set_axisbelow(True)
    for sp in ('top', 'right'):
        ax.spines[sp].set_visible(False)


def _cross(fn, g, level):
    """the INDUCTIVE crossing: the highest f_n at which the curve still
    reaches `level`.  None when the curve never gets there."""
    idx = np.where(g >= level)[0]
    return None if not len(idx) else float(fn[idx[-1]])


def _mz(lam, fn):
    """the capacitive/inductive boundary, traced as Q varies

    NOT the locus of the gain peaks: the boundary (arg Z_in = 0) lies a
    little to the right of each peak.  This docstring said "peaks =
    boundary" and the figure legend repeated it (fixed 2026-09-23).

    Parameterised by Q rather than by f_n: for each Q the boundary sits at
    zvs_edge(Q, lam), which is a closed form, so no peak has to be hunted
    for.  It exists only between f_n0 and resonance.
    """
    qs = np.linspace(0.02, 6.0, 900)
    x = np.array([zvs_edge(q, lam) for q in qs])
    y = np.array([M(zvs_edge(q, lam), q, lam) for q in qs])
    ok = (x >= fn[0]) & (x <= 1.0)
    return x[ok], y[ok]


# ------------------------------------------------ 1  the PFC, in one cycle
def an_pf_chain(save, foot, R, sweep):
    """The causal chain, over one line half cycle."""
    lam, qpk = R['lam_a'], R['Qpk']
    fig, axs = plt.subplots(4, 1, figsize=(9.35, 9.6), sharex=True)
    fig.subplots_adjust(left=0.115, right=0.975, top=0.972, bottom=0.062,
                        hspace=0.30)

    rows, _ = sweep(R, R['Vin_min'], 1.0, N=721)
    rows = [r for r in rows if r]
    th = np.array([r['th'] for r in rows])
    fsw = np.array([r['fsw'] for r in rows]) / R['fr']
    mir = lambda q: np.concatenate([q, q[::-1]])
    thd = np.degrees(np.concatenate([th, np.pi - th[::-1]]))
    d = np.linspace(0.0, 180.0, 901)
    sd = np.sin(np.radians(d))

    # ---- 1  voltage and current
    a = axs[0]
    a.set_title('1     what unity power factor asks for', fontsize=11.5,
                color=NAVY, loc='left')
    a.plot(d, sd, color=NAVY, lw=2.4)
    a.plot(d, sd, color=MAG, lw=2.4, ls=(0, (6, 3)))
    a.set_ylim(0, 1.24)
    a.text(90, 1.04, u'v$_{in}$(θ) after the bridge   —   and the '
           u'current drawn from it, i$_{in}$(θ)', ha='center',
           va='bottom', fontsize=10.2, color=NAVY, path_effects=HALO,
           zorder=9)
    a.annotate('same shape, no phase shift.\nThat is the whole of it.',
               xy=(38, float(np.interp(38, d, sd))), xytext=(52, 0.28),
               fontsize=10.0, color=MAG, ha='left',
               arrowprops=dict(arrowstyle='-|>', color=MAG, lw=1.3),
               path_effects=HALO, zorder=9)
    _tidy(a, '', 'normalised')

    # ---- 2  the power that implies
    a = axs[1]
    a.set_title('2     so the power taken from the mains must be this',
                fontsize=11.5, color=NAVY, loc='left')
    p = 2.0 * sd ** 2
    a.plot(d, p, color=NAVY, lw=2.4)
    a.axhline(1.0, color=MAG, lw=1.8, ls=(0, (5, 3)))
    a.fill_between(d, 1.0, p, where=(p > 1.0), color=CYA, alpha=0.22, lw=0)
    a.fill_between(d, p, 1.0, where=(p < 1.0), color=YEL, alpha=0.40, lw=0)
    a.set_ylim(0, 2.42)
    a.text(90, 2.06, u'p$_{in}$(θ) = 2 P$_{in}$ sin$^2$θ',
           ha='center', va='bottom', fontsize=10.2, color=NAVY,
           path_effects=HALO, zorder=9)
    #  the dashed line is the AVERAGE of p_in, i.e. P_in: labelled P_out
    #  it said the conversion was lossless (2026-09-23)
    a.text(45, 1.06, 'its average P$_{in}$: drawn by the load side at a steady rate',
           ha='center', va='bottom', fontsize=10.0, color=MAG,
           path_effects=HALO, zorder=9)
    a.text(90, 1.55, 'surplus:\nthe bank charges', ha='center', va='center',
           fontsize=9.8, color=NAVY, path_effects=HALO, zorder=9)
    #  named above the curve, where nothing is drawn (on the curve at
    #  150-180 deg it sat across the trace, 2026-09-23)
    a.annotate('deficit: the bank\nfeeds the load alone', xy=(160, 0.45),
               xytext=(178, 1.55), ha='right', va='center', fontsize=9.8,
               color='#8a6d00', path_effects=HALO, zorder=9,
               arrowprops=dict(arrowstyle='-|>', color='#8a6d00', lw=1.0,
                               shrinkB=3))
    _tidy(a, '', 'power / P$_{in}$')

    # ---- 3  what that asks of the tank
    a = axs[2]
    a.set_title('3     which asks the tank for two things at once',
                fontsize=11.5, color=NAVY, loc='left')
    a2 = a.twinx()
    a.set_zorder(a2.get_zorder() + 1)
    a.patch.set_visible(False)
    with np.errstate(divide='ignore'):
        mreq = np.where(sd > 1e-6, 1.0 / np.maximum(sd, 1e-6), np.nan)
    a.plot(d, mreq, color=MAG, lw=2.4)
    a2.plot(d, sd ** 2, color=CYA, lw=2.4)
    a.set_ylim(0, 5.2)
    a2.set_ylim(0, 1.24)
    a.tick_params(axis='y', colors=MAG)
    a2.tick_params(labelsize=9.4, colors=CYA)
    a.text(90, 1.45, u'required gain  M$_{req}$/M$_{pk}$ = 1/sinθ   '
           u'→ ∞', ha='center', va='bottom', fontsize=10.2,
           color=MAG, path_effects=HALO, zorder=9)
    a2.text(90, 0.92, u'loading  Q/Q$_{pk}$ = sin$^2$θ   → 0',
            ha='center', va='top', fontsize=10.2, color=CYA,
            path_effects=HALO, zorder=9)
    #  'both diverge' was wrong for the loading, which goes to zero
    a.text(60, 0.95, u'at the zero crossing: gain demand → ∞, load → 0;\n'
           'a tank with no load has unlimited gain at f$_o$',
           ha='left', va='top', fontsize=9.8, color=GREY,
           path_effects=HALO, zorder=9)
    _tidy(a, '', 'M$_{req}$ / M$_{pk}$')
    a2.set_ylabel('Q / Q$_{pk}$', fontsize=10.5, color=CYA)

    # ---- 4  the answer
    a = axs[3]
    a.set_title('4     and the only knob there is answers with this profile',
                fontsize=11.5, color=NAVY, loc='left')
    a.plot(thd, mir(fsw), color=NAVY, lw=2.6)
    a.axhline(1.0, color=GREY, lw=1.4, ls=(0, (5, 3)))
    a.axhline(R['fo'] / R['fr'], color=PUR, lw=1.4, ls=(0, (5, 3)))
    a.set_ylim(0.45, 1.20)
    a.text(90, 1.02, 'f$_r$', ha='center', va='bottom', fontsize=10.0,
           color=GREY, path_effects=HALO, zorder=9)
    a.text(4, R['fo'] / R['fr'] - 0.02, 'f$_o$  —  the floor of the '
           'whole design', ha='left', va='top', fontsize=10.0, color=PUR,
           path_effects=HALO, zorder=9)
    a.text(90, float(np.interp(90, thd, mir(fsw))) + 0.03,
           'f$_{sw}$(θ):  most power at the peak → highest '
           'frequency', ha='center', va='bottom', fontsize=10.2, color=NAVY,
           path_effects=HALO, zorder=9)
    _tidy(a, u'line phase  θ  [deg]', 'f$_{sw}$ / f$_r$')
    a.set_yticks([])                      # the profile, not this design's values
    a.set_xlim(0, 180)
    a.set_xticks(range(0, 181, 30))

    foot(fig, 'There is no current loop and no multiplier: panels 1 to 3 are '
              'forced by the two voltage sources, and panel 4 is what the '
              'controller has to do about it. The frequency profile IS the '
              'power factor correction.')
    save(fig, 'an_pf_chain')


# --------------------------------- 2  the two gain charts, side by side
def an_gain_compare(save, foot, R, sweep):
    """An ordinary LLC's gain chart, and this converter's."""
    from matplotlib.lines import Line2D
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.35, 4.75))
    fig.subplots_adjust(left=0.07, right=0.988, top=0.90, bottom=0.125,
                        wspace=0.19)
    fn = np.linspace(0.36, 2.0, 1600)

    # ---------------- ordinary
    lam1, QF = 0.20, 0.40            # m = L_p/L_r = 6, and a usual full load
    a1.set_title('an ordinary LLC, fed from a regulated dc bus',
                 fontsize=12, color=NAVY)
    hs = []
    for q, nm, col, w in ((0.001, 'no load', PUR, 1.8),
                          (0.15, 'Q = 0.15', CYA, 1.6),
                          (0.25, 'Q = 0.25', GRN, 1.6),
                          (QF, 'full load, Q = %.2f' % QF, NAVY, 2.6)):
        a1.plot(fn, [M(f, q, lam1) for f in fn], color=col, lw=w)
        hs.append((Line2D([], [], color=col, lw=w), nm))
    a1.axhline(1.0, color=GREY, lw=1.4, ls=(0, (2, 3)))
    a1.axhline(1.25, color=MAG, lw=2.0, ls=(0, (6, 3)))
    hs.append((Line2D([], [], color=MAG, lw=2.0, ls=(0, (6, 3))),
               'required at the minimum bus'))
    hs.append((Line2D([], [], color=GREY, lw=1.4, ls=(0, (2, 3))),
               'required at the nominal bus'))
    gfull = np.array([M(f, QF, lam1) for f in fn])
    xw = _cross(fn, gfull, 1.25)
    a1.plot([xw], [1.25], 'o', color=NAVY, ms=9, zorder=6)
    a1.annotate('ONE curve against ONE line,\nand the crossing is the only\n'
                'operating point the design is\nchecked at. It does not move.',
                xy=(xw, 1.25), xytext=(0.80, 2.28), fontsize=10.0,
                color=NAVY, ha='left', va='top',
                arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.3),
                path_effects=HALO, zorder=9)
    a1.text(0.40, 2.52, u'the family is LOAD\n\u03bb = %.2f  (m = %.0f)'
            % (lam1, 1 + 1 / lam1), ha='left', va='top', fontsize=10.6,
            color=NAVY, fontweight='bold', path_effects=HALO, zorder=9)
    a1.set_xlim(0.36, 2.0)
    a1.set_ylim(0, 2.6)
    _tidy(a1, 'f$_{sw}$ / f$_r$', 'gain  M')
    a1.legend([h for h, _n in hs], [n for _h, n in hs], loc='lower left',
              fontsize=9.4, frameon=False, ncol=1)

    # ---------------- single stage
    lam2, qpk = R['lam_a'], R['Qpk']
    a2.set_title('the single-stage converter of this note', fontsize=12,
                 color=NAVY)
    a2.plot(fn, [M(f, 1e-4, lam2) for f in fn], color=NAVY, lw=2.0)
    hs = [(Line2D([], [], color=NAVY, lw=2.0), 'M$_{OL}$: no load')]
    pts = []
    for ph, nm, col in PHASES:
        q = qpk * np.sin(ph) ** 2
        g = np.array([M(f, q, lam2) for f in fn])
        a2.plot(fn, g, color=col, lw=2.2)
        lev = 1.0 / np.sin(ph)                  # M_req / M_pk
        a2.axhline(lev, color=col, lw=1.5, ls=(0, (6, 3)))
        hs.append((Line2D([], [], color=col, lw=2.2), nm))
        x = _cross(fn, g, lev)
        if x:
            pts.append((x, lev))
            a2.plot([x], [lev], 'o', color=col, ms=8, zorder=6)
    mx, my = _mz(lam2, fn)
    a2.plot(mx, my, color=GRN, lw=1.8, ls=(0, (3, 2.4)))
    a2.axhline(1.0 / (1 + lam2), color=GREY, lw=1.6, ls=(0, (1, 2)))
    hs.append((Line2D([], [], color=GREY, lw=1.6, ls=(0, (6, 3))),
               u'M$_{req}$ of that \u03b8 (dashed, same colour)'))
    hs.append((Line2D([], [], color=GRN, lw=1.8, ls=(0, (3, 2.4))),
               'M$_Z$: the capacitive boundary'))
    hs.append((Line2D([], [], color=GREY, lw=1.6, ls=(0, (1, 2))),
               u'M$_{\\infty}$ = 1/(1+\u03bb): the no-load floor'))
    a2.set_xlim(0.36, 2.0)
    a2.set_ylim(0, 4.6)
    a2.text(0.40, 2.72, u'the family is LINE PHASE', ha='left', va='top',
            fontsize=10.6, color=NAVY, fontweight='bold',
            path_effects=HALO, zorder=9)
    if len(pts) > 1:
        a2.annotate('', xy=pts[-1], xytext=pts[0],
                    arrowprops=dict(arrowstyle='<|-|>', color=NAVY, lw=2.2,
                                    shrinkA=10, shrinkB=10,
                                    connectionstyle='arc3,rad=0.45'))
        a2.annotate('the operating point walks along\nhere and back, twice\n'
                    'every line cycle',
                    xy=(0.5 * (pts[0][0] + pts[-1][0]) + 0.02,
                        0.5 * (pts[0][1] + pts[-1][1]) - 0.12),
                    xytext=(1.05, 2.30), ha='left', va='top', fontsize=10.0,
                    color=NAVY,
                    arrowprops=dict(arrowstyle='-|>', color=NAVY, lw=1.2),
                    path_effects=HALO, zorder=9)
    _tidy(a2, 'f$_{sw}$ / f$_r$', 'gain  M   (drawn for M$_{pk}$ = 1)')
    a2.legend([h for h, _n in hs], [n for _h, n in hs], loc='upper right',
              fontsize=9.4, frameon=False, ncol=1)

    foot(fig, 'Same axes, same equation, read differently. On the left one '
              'curve is compared with one line. On the right every curve has '
              'its OWN line, in its own colour, and the converter visits all '
              'of them within one line half cycle.')
    save(fig, 'an_gain_compare')


# ------------------------------- 3  the same chart, on the design's numbers
def gain_points(R):
    """(V_eq, theta, Q, M_req, f_n, f_sw) at the marked crossings.

    The figure and the table in the text read this, so a marker on a
    curve and a row in a table cannot say different things.
    """
    lam, qpk, fr = R['lam_a'], R['Qpk'], R['fr']
    fn = np.linspace(0.40, 2.0, 4001)
    out = []
    from l6790 import line_conditions
    for _nm, vac, _mode in line_conditions(R):
        mpk = R['MVmin'] * R['Vin_min'] / vac      # M_pk scales as 1/V_eq
        for ph, _nm2, _col in PHASES:
            q = qpk * np.sin(ph) ** 2
            g = np.array([M(f, q, lam) for f in fn])
            lev = mpk / np.sin(ph)
            x = _cross(fn, g, lev)
            out.append((vac, ph, q, lev, x, None if x is None
                        else x * fr / 1e3))
    return out


def an_gain_design(save, foot, R, sweep):
    """The worked design's gain chart at all six line conditions.

    One panel per condition, in order of equivalent input.  The curves are
    the same in every panel - M(f_n, Q) does not depend on the input voltage -
    only the dashed required-gain lines move.  Six panels rather than six
    ladders on one chart, so that no curve can be compared with a line that
    is not its own (2026-09-22, user: the mains voltages a supply meets, not
    only the morphing edges).
    """
    from matplotlib.lines import Line2D
    from l6790 import line_conditions
    lam, qpk, fr = R['lam_a'], R['Qpk'], R['fr']
    fn = np.linspace(0.40, 2.0, 1600)
    conds = line_conditions(R)
    fig, axs = plt.subplots(2, 3, figsize=(11.6, 8.7), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.06, right=0.99, top=0.86, bottom=0.08,
                        wspace=0.08, hspace=0.24)
    curves = {ph: np.array([M(f, qpk * np.sin(ph) ** 2, lam) for f in fn])
              for ph, _n, _c in PHASES}
    nl = [M(f, 1e-4, lam) for f in fn]
    mx, my = _mz(lam, fn)
    minf = 1.0 / (1 + lam)
    for a, (nm, vac, mode) in zip(axs.flat, conds):
        mpk = R['MVmin'] * R['Vin_min'] / vac
        a.set_title(nm, fontsize=13.5, color=NAVY)
        a.plot(fn, nl, color=NAVY, lw=1.8)
        for ph, _n, col in PHASES:
            a.plot(fn, curves[ph], color=col, lw=2.0)
            lev = mpk / np.sin(ph)
            a.axhline(lev, color=col, lw=1.3, ls=(0, (6, 3)))
            x = _cross(fn, curves[ph], lev)
            if x:
                a.plot([x], [lev], 'o', color=col, ms=7, zorder=6)
        a.plot(mx, my, color=GRN, lw=1.6, ls=(0, (3, 2.4)))
        a.axhline(minf, color=GREY, lw=1.4, ls=(0, (1, 2)))
        #  the line-peak crossing, in words, in the empty upper part of the
        #  panel where nothing is drawn
        x90 = _cross(fn, curves[PHASES[0][0]], mpk)
        if x90:
            txt = (u'line peak:  f$_{sw}$ = %.0f kHz\n'
                   u'f$_{sw}$/f$_r$ = %.2f,  M$_{pk}$ = %.3f'
                   % (x90 * fr / 1e3, x90, mpk))
        else:
            txt = u'M$_{pk}$ = %.3f: no full-load solution' % mpk
        if mpk < minf:
            #  the no-load curve never gets this low: burst mode owns it
            txt += u'\nM$_{pk}$ < M$_{\\infty}$: no no-load solution'
        a.text(0.97, 0.96, txt, transform=a.transAxes, fontsize=12,
               color=NAVY, ha='right', va='top', path_effects=HALO,
               zorder=9)
        a.set_xlim(fn[0], 2.0)
        a.set_ylim(0, 4.6)
        _tidy(a, '', '')
    for a in axs[1]:
        a.set_xlabel('f$_{sw}$ / f$_r$   (f$_r$ = %.1f kHz)' % (fr / 1e3),
                     fontsize=12.5, color=NAVY)
    for a in axs[:, 0]:
        a.set_ylabel('gain  M', fontsize=12.5, color=NAVY)
    for a in axs.flat:
        a.tick_params(labelsize=11.8)
    hs = [(Line2D([], [], color=NAVY, lw=1.8), 'M$_{OL}$: no load')]
    for ph, nm, col in PHASES:
        hs.append((Line2D([], [], color=col, lw=2.0),
                   '%s,  Q = %.3f' % (nm, qpk * np.sin(ph) ** 2)))
    hs.append((Line2D([], [], color=GREY, lw=1.3, ls=(0, (6, 3))),
               u'M$_{req}$ = M$_{pk}$ / sin\u03b8, in the colour of its phase'))
    hs.append((Line2D([], [], color=GRN, lw=1.6, ls=(0, (3, 2.4))),
               'M$_Z$: capacitive boundary'))
    hs.append((Line2D([], [], color=GREY, lw=1.4, ls=(0, (1, 2))),
               u'M$_{\\infty}$ = %.3f' % minf))
    fig.legend([h for h, _n in hs], [n for _h, n in hs], loc='upper center',
               ncol=3, fontsize=12, frameon=False, bbox_to_anchor=(0.5, 0.99))
    foot(fig, 'The gain chart of this design at the six input voltages, '
              'low to high. The curves never change; only the required-gain '
              'lines move, up at low input and down at high input. Each '
              'curve is read against the dashed line of its own colour.')
    save(fig, 'an_gain_design')
