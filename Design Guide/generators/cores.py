# -*- coding: utf-8 -*-
"""Ferrite core candidates, as printed in the manufacturer's datasheet.

Nothing in this file is remembered or estimated.  Every number in CORES is
copied from the TDK Electronics datasheet named beside it, and everything
else here is arithmetic on those numbers and on the design.

The two candidates are the ones the design has to choose between: both
clear the flux requirement, and the choice is made on the winding window,
because a single-stage tank needs a leakage that only a physically
separated winding can give.

    PQ 32/30   core B65879B, coil former B65880E, October 2022
    PQ 40/40   core B65883A, coil former B65884E, October 2022

Window symbols follow the datasheets: A_N is the winding cross-section of
the coil former and l_N its mean turn length.
"""
from math import pi

MU0 = 4e-7 * pi

CORES = {
    'PQ 32/30': dict(
        core='B65879B', former='B65880E',
        le=67.80, Ae=153.8, Amin=127.5, Ve=10440.0, mass=57.4,
        AN=104.0, lN=62.0,
        AL_ungapped=6100.0, material='N95'),        # +30/-20 %
    'PQ 40/40': dict(
        core='B65883A', former='B65884E',
        le=93.0, Ae=189.0, Amin=174.0, Ve=17580.0, mass=90.0,
        AN=309.0, lN=87.0,
        AL_ungapped=5500.0, material='N95'),
}

#  Assumptions, stated here so that they are in one place and can be
#  changed in one place.  Neither is a constant of nature.
J_CU = 4.5          # A/mm^2, natural convection, transformer of this size
K_U = 0.30          # window utilisation with Litz, insulation and margins
B_MAX = 0.20        # T, the flux ceiling this note designs to


def flux(V, Ae_mm2):
    """Peak flux density [mT] on a core of this cross-section.

    B_pk = V_o,eff / (4 f_r N_s A_e) - the secondary volt-seconds, so it
    does not contain N_p.  f_r is carried in kHz.
    """
    return 1e3 * V['Vout'] / (4.0 * V['fr'] * 1e3 * V['Ns'] * Ae_mm2 * 1e-6)


def turns_needed(V, Ae_mm2, bmax=B_MAX):
    """The smallest secondary turn count that keeps B_pk under bmax."""
    return V['Vout'] / (4.0 * V['fr'] * 1e3 * bmax * Ae_mm2 * 1e-6)


def gap(V, Ae_mm2):
    """First-estimate centre-leg gap [mm] for the A_L the design needs.

    Assumes the gap carries the whole reluctance and ignores fringing, so
    the real gap always comes out larger.  It is here to show the order,
    not to be put on a drawing - the drawing carries A_L.
    """
    return 1e3 * MU0 * Ae_mm2 * 1e-6 / (V['AL'] * 1e-9)


def copper(V):
    """-> list of (name, turns, I_rms per unit [A], area per turn [mm^2]).

    Primaries in series, secondaries in parallel: every unit carries the
    WHOLE primary current and its share of the secondary current.
    """
    nx = V['nser']
    return [('primary', V['Np'], V['Iprilc'], V['Iprilc'] / J_CU),
            ('secondary, each half', V['Ns'], V['Idio'] / nx,
             V['Idio'] / nx / J_CU)]


def window(V):
    """-> bare copper area [mm^2] for one unit, counting both halves."""
    rows = copper(V)
    a = rows[0][1] * rows[0][3]              # primary
    a += 2 * rows[1][1] * rows[1][3]         # two secondary halves
    return a


# ===================================================================
#  Mechanical dimensions, so the cross-section can be drawn to scale
# ===================================================================
#  Everything in MECH is read off the datasheet dimensional drawings:
#
#      PQ 40/40 core        B65883A, October 2022, page 2
#      PQ 40/40 coil former B65884E, October 2022, page 3, section A-A
#
#  Values marked "scaled" carry no dimension label on the drawing.  They
#  were measured from the PDF's own vector geometry, not from a picture:
#  the drawing's line coordinates were read out, and the two labelled
#  dimensions on the same view (40.5 wide, 39.8 high) fix the scale to
#  2.1455 pt/mm with the two independent readings agreeing to 0.03 %.
#  The same measurement returns the centre leg as 14.94 mm against the
#  labelled 14.9, which is the check that the method is sound.
MECH = {
    'PQ 40/40': dict(
        core='B65883A', former='B65884E',
        #  core, section view - labelled
        W=40.5, H=39.8, d_centre=14.9, win_h=29.5,
        #  core, section view - scaled: inner face of the outer leg,
        #  measured from the centre line
        r_win_out=13.60,
        #  core, plan view - labelled
        plan_w=37.0, plan_d=28.0,
        #  coil former, section A-A - labelled
        tube_od=17.5, bore=15.5, wind_w=25.4, flange_h=29.0,
        #  coil former, plan and elevation - labelled
        former_w=38.1, former_d=40.0, flange_w=29.5, former_h=45.0,
        pitch_a=5.08, pitch_b=15.24, pins=12),
}

# ===================================================================
#  Coil-former terminals: where each winding of one unit comes out
# ===================================================================
#  Geometry is the B65884E drawing (page 3, plan view FPK0430): twelve
#  terminals, six per side, each side in two groups of three, pitch 5.08
#  within a group, 15.24 between the inner pins of the two groups, and
#  the two rows 38.1 apart.  The drawing carries a "pin 1 marking" at the
#  bottom-left corner of the plan view and NO other pin number.
#
#  NUMBERING IS THEREFORE AN ASSUMPTION: 1 at the marking, 1-6 up the
#  marked side, 7-12 down the other, so that 12 is opposite 1.  That is
#  the usual coil-former convention, but the datasheet does not say so,
#  and the direction has to be confirmed against the vendor's bobbin
#  drawing before the specification goes out.  The ASSIGNMENT below does
#  not depend on it - which group carries which winding is fixed by the
#  drawing - only the printed numbers do.
#
#  Assignment, one unit (three identical units per set):
#      marked side   group 1-3   NP1  primary,   start 1, finish 3
#                    group 4-6   NAUX auxiliary, start 4, finish 6
#      other side    group 7-9   NS2  secondary, start 7, finish 9
#                    group 10-12 NS3  secondary, start 10, finish 12
#  The primary-referenced windings (NP1 and the ZCD auxiliary) share one
#  side and the two secondaries the other, so the isolation distance is
#  the whole bobbin width.  The centre tap is pins 9 and 10, adjacent
#  across the 15.24 gap, and is made ON THE PCB, not inside the part.
#  "start" is the end the polarity dot marks; NS2 and NS3 are wound in
#  the same sense, so joining NS2's finish to NS3's start makes the tap.
#  The middle pin of each group is left free: a Litz bundle and a foil
#  end each take one pin, and the spare keeps the two terminations of a
#  winding apart.
PIN_XY = {}
for _i, _y in enumerate((-17.78, -12.70, -7.62, 7.62, 12.70, 17.78)):
    PIN_XY[1 + _i] = (-19.05, _y)            # marked side, upwards
    PIN_XY[12 - _i] = (19.05, _y)            # other side, downwards
PINMAP = {                                  # winding -> (start, finish)
    'NP1': (1, 3), 'NAUX': (4, 6), 'NS2': (7, 9), 'NS3': (10, 12)}
PIN_SIDE = {'NP1': 'marked', 'NAUX': 'marked', 'NS2': 'other', 'NS3': 'other'}
CENTRE_TAP = (PINMAP['NS2'][1], PINMAP['NS3'][0])
PIN_NOTE = ('The datasheet marks pin 1 only; the numbers run counter-'
            'clockwise from it in the plan view, which is the usual '
            'convention. Confirm the direction against the bobbin drawing '
            'before the specification is released; the assignment does not '
            'depend on it, only the printed numbers do.')


def pins(w, dash='\u2013'):
    """'1 - 3' style terminal text for the spec and the tables."""
    a, b = PINMAP[w]
    return '%d %s %d' % (a, dash, b)


#  Three more assumptions, kept beside J_CU and K_U for the same reason.
K_LITZ = 0.55       # copper fill of a served Litz bundle, insulation included
T_FOIL = 0.20       # mm, copper foil thickness - the nearest standard gauge
                    # at or under twice the skin depth
T_FOIL_INS = 0.05   # mm, interlayer insulation on each foil turn
MARGIN = 2.0        # mm of margin tape at each flange
D_STRAND = 0.10     # mm, Litz strand diameter


def litz(area_mm2):
    """-> (bundle outer diameter [mm], strand count) for a bare copper area."""
    a_strand = pi * D_STRAND ** 2 / 4.0
    n = int(area_mm2 / a_strand + 0.9999)
    return (4.0 * area_mm2 / (pi * K_LITZ)) ** 0.5, n


def winding(V, name='PQ 40/40'):
    """The winding laid out along the bobbin, in millimetres.

    Side by side, not interleaved: a single-stage tank needs
    L_short/L_open = lambda/(1+lambda), and only a deliberate gap between
    primary and secondary gives leakage of that order.  The gap is
    therefore not slack - it is the resonant inductor, and this function
    reports what is left for it after the copper and the margins.

    Returns a dict the drawing can render directly.  Nothing is rounded
    for appearance: if the copper does not fit, 'gap' comes out negative
    and 'fits' is False.
    """
    M = MECH[name]
    rows = copper(V)
    ap, asec = rows[0][3], rows[1][3]
    dp, nstr = litz(ap)
    wf = asec / T_FOIL                       # foil width for one turn
    usable = M['wind_w'] - 2 * MARGIN
    #  fewest primary layers that leave room for the foil and a gap
    lay = 1
    while lay <= V['Np']:
        per = -(-V['Np'] // lay)             # ceil
        if per * dp + wf < usable:
            break
        lay += 1
    per = -(-V['Np'] // lay)
    rows_p = [min(per, V['Np'] - i * per) for i in range(lay)]
    wp = per * dp
    gap_ax = usable - wp - wf
    build_p = lay * dp
    build_s = 2 * V['Ns'] * (T_FOIL + T_FOIL_INS)
    r_tube = M['tube_od'] / 2.0
    r_free = M['r_win_out'] - r_tube         # radial room at the narrow section
    return dict(
        name=name, M=M, Np=V['Np'], Ns=V['Ns'],
        ap=ap, asec=asec, d_litz=dp, n_strand=nstr,
        t_foil=T_FOIL, w_foil=wf, margin=MARGIN, usable=usable,
        layers=lay, per_layer=per, rows_p=rows_p, w_pri=wp, gap=gap_ax,
        build_p=build_p, build_s=build_s, r_tube=r_tube, r_free=r_free,
        fits=(gap_ax > 0 and build_p <= r_free and build_s <= r_free))


def report(V, name='PQ 40/40'):
    """Print the fit arithmetic.  Run this before believing the drawing."""
    w = winding(V, name)
    M = w['M']
    out = [
        '%s   core %s   coil former %s' % (name, M['core'], M['former']),
        '  bobbin winding width      %6.2f mm   (datasheet)' % M['wind_w'],
        '  margin tape, both flanges %6.2f mm   (assumed %.1f each)'
        % (2 * MARGIN, MARGIN),
        '  usable axial              %6.2f mm' % w['usable'],
        '  primary  %d turns of %.2f mm2 -> Litz %d x %.2f mm, bundle '
        'd = %.2f mm' % (w['Np'], w['ap'], w['n_strand'], D_STRAND,
                         w['d_litz']),
        '           %d layer(s) %s -> %6.2f mm axial, %.2f mm build'
        % (w['layers'], w['rows_p'], w['w_pri'], w['build_p']),
        '  secondary %d + %d turns of %.2f mm2 -> foil %.2f x %.2f mm'
        % (w['Ns'], w['Ns'], w['asec'], w['t_foil'], w['w_foil']),
        '           %d turns -> %6.2f mm axial, %.2f mm build'
        % (2 * w['Ns'], w['w_foil'], w['build_s']),
        '  LEFT FOR THE SEPARATION    %5.2f mm   %s'
        % (w['gap'], 'ok' if w['gap'] > 0 else '** DOES NOT FIT'),
        '  radial room at the narrow section %.2f mm  '
        '(window %.2f - bobbin r %.2f)' % (w['r_free'], M['r_win_out'],
                                           w['r_tube']),
        '  primary build %.2f mm %s   secondary build %.2f mm %s'
        % (w['build_p'], 'ok' if w['build_p'] <= w['r_free'] else '** TOO DEEP',
           w['build_s'], 'ok' if w['build_s'] <= w['r_free'] else '** TOO DEEP'),
        '  VERDICT %s' % ('fits' if w['fits'] else '** DOES NOT FIT'),
    ]
    return '\n'.join(out)
