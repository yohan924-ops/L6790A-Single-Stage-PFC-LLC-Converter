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
    #  PQ 50/50DG - B65981Q core (distributed gap: G2 + G3 on the centre
    #  leg, delivered gapped only, A_L 100 / 250 / 400 nH stock, others on
    #  request), B65982E coil former.  October 2022 datasheet, received
    #  2026-09-22 from the user (the TDK CDN blocks this container).
    'PQ 50/50DG': dict(
        core='B65981Q', former='B65982E',
        le=113.0, Ae=332.0, Amin=314.0, Ve=37630.0, mass=190.0,
        AN=340.0, lN=100.5,
        AL_ungapped=None, material='N95',
        #  set totals: G2 and G3 are dimensions of ONE half (see ETD 49)
        AL_gaps={100: 2 * (1.67 + 0.85), 250: 2 * (0.62 + 0.23),
                 400: 2 * (0.31 + 0.18)}),
    #  ETD 49/25/16DG - B66367 core (distributed gap, gapped only: A_L 100
    #  / 250 nH stock), B66368 coil former, 20 pins.  October 2022,
    #  received 2026-09-22 from the user.
    'ETD 49/25/16DG': dict(
        core='B66367', former='B66368',
        le=114.0, Ae=211.0, Amin=209.0, Ve=24100.0, mass=124.0,
        AN=269.4, lN=86.0,
        AL_ungapped=None, material='N95',
        #  stock A_L -> total centre-leg gap of the SET [mm], datasheet
        #  page 2.  G2 and G3 are drawn on one half, and a set is two
        #  identical halves (single units, one ordering code, A_L "per
        #  set"), so the set carries 2 x (G2 + G3).  Taken as G2 + G3 it
        #  put 0.54 mm against 250 nH, where mu0 Ae / A_L alone asks for
        #  1.06 mm; the set total, 1.08 mm, matches it (round 63).
        AL_gaps={100: 2 * (1.06 + 0.48), 250: 2 * (0.39 + 0.15)}),
    #  ETD 54/28/19 - B66395 core (ungapped N87 4450 nH; gapped examples
    #  g 1.0 / 1.5 / 2.0 mm -> 393 / 287 / 229 nH, K1 393 K2 -0.779 for
    #  A_L(s) between 0.10 and 3.50 mm), B66396 coil former, 22 pins.
    #  October 2022, received 2026-09-22 from the user.  No N95 listed.
    'ETD 54/28/19': dict(
        core='B66395', former='B66396',
        le=127.0, Ae=280.0, Amin=280.0, Ve=35600.0, mass=180.0,
        AN=315.6, lN=96.0,
        AL_ungapped=4450.0, material='N87'),
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


def dg_gap(V, name=None):
    """Total gap [mm] for the design A_L on a distributed-gap core.

    Interpolates 1/A_L against the total gap between the two nearest
    stock values of the datasheet - the reluctance of the gap is what
    A_L sets, and it is linear in the gap length to first order.  Falls
    back to gap() when the core has no stock table.
    """
    name = name or CHOSEN
    R = CORES[name]
    tab = R.get('AL_gaps')
    if not tab:
        return gap(V, R['Ae'])
    al = V['AL']
    keys = sorted(tab)
    lo = max([k for k in keys if k <= al] or [keys[0]])
    hi = min([k for k in keys if k >= al] or [keys[-1]])
    if lo == hi:
        return tab[lo]
    f = (1.0 / al - 1.0 / lo) / (1.0 / hi - 1.0 / lo)
    return tab[lo] + (tab[hi] - tab[lo]) * f


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
    #  PQ 50/50DG, datasheet page 2 (core) and 3 (coil former), all
    #  labelled.  The outer legs' inner faces are the "31.5 min" of the
    #  plan view, so r_win_out is a minimum, not a scaled reading.  The
    #  window is SHALLOWER than PQ 40/40's: 15.75 - 11.6 = 4.15 mm.
    'PQ 50/50DG': dict(
        core='B65981Q', former='B65982E',
        W=50.0, H=44.0, d_centre=20.0, win_h=36.1,
        r_win_out=15.75,
        plan_w=44.0, plan_d=32.0,
        tube_od=23.2, bore=20.8, wind_w=30.4, flange_h=35.2,
        former_w=45.72, former_d=51.0, flange_w=34.4, former_h=51.0,
        pitch_a=7.62, pitch_b=12.7, pins=12),
    #  ETD 49/25/16DG, datasheet page 2 (core) and 3 (coil former).  The
    #  outer legs' inner faces are the labelled "36.1 +1.8" of the plan
    #  view; the window height is 2 x 17.7; the tube is "19.3 max", so
    #  the radial room is a minimum: 18.05 - 9.65 = 8.40 mm.
    'ETD 49/25/16DG': dict(
        core='B66367', former='B66368',
        W=48.5, H=49.8, d_centre=16.7, win_h=35.4,
        r_win_out=18.05,
        plan_w=48.5, plan_d=16.7,
        tube_od=19.3, bore=17.0, wind_w=32.7, flange_h=35.4,
        former_w=54.5, former_d=56.2, flange_w=35.9, former_h=40.9,
        pitch_a=5.08, pitch_b=None, pins=20, rows=40.64),
    #  ETD 54/28/19, datasheet page 2 and 4.  Legs' inner faces "40.1
    #  +2.2", window height 2 x 19.8, tube "22 max": 20.05 - 11.0 = 9.05.
    'ETD 54/28/19': dict(
        core='B66395', former='B66396',
        W=54.5, H=55.6, d_centre=19.3, win_h=39.6,
        r_win_out=20.05,
        plan_w=54.5, plan_d=19.3,
        tube_od=22.0, bore=19.8, wind_w=36.8, flange_h=39.4,
        former_w=61.6, former_d=61.4, flange_w=39.5, former_h=46.0,
        pitch_a=5.08, pitch_b=None, pins=22, rows=45.72),
}

# ===================================================================
#  The core this note builds on, and its coil-former terminals
# ===================================================================
#  CHOSEN names the core the design example is drawn and specified on.
#  Everything downstream - the section figure, the pin figure, the tables
#  of the note and the vendor specification - reads it from here.
#
#  2026-09-22: ONE transformer (the note's example is a single part), so
#  the PQ 40/40 of the three-unit build gave way to ETD 49/25/16DG: the
#  15-turn primary needs a window that is deep (7.1 mm radial for three
#  layers) or wide (19 mm axial for two), and every PQ is shallow.  The
#  comparison is winding() on each entry of CORES; HISTORY.md 2026-09-22.
CHOSEN = 'ETD 49/25/16DG'

#  Terminals, per coil former.  'xy' is pin number -> (x, y) in mm in the
#  datasheet's mounting-direction view; 'map' is winding -> (start pins,
#  finish pins), each a tuple because a heavy terminal may take two pins;
#  'plan' is the outline drawn under the pins.
#
#  PQ 40/40 (B65884E, page 3, plan view FPK0430): twelve terminals, six
#  per side in two groups of three, pitch 5.08 within a group, 15.24
#  between the inner pins of the groups, rows 38.1 apart, a "pin 1
#  marking" at the bottom-left corner and NO other pin number.
#
#  ETD 49/25/16DG (B66368, page 3, "hole arrangement, view in mounting
#  direction"): twenty terminals in two rows of ten, pitch 5.08 (9 x 5.08
#  = 45.72), rows 40.64 apart, square 0.8 mm pins.  The drawing carries
#  no pin numbers and no pin-1 marking at all.
#
#  NUMBERING IS THEREFORE AN ASSUMPTION on both: 1 at one end of one row,
#  counted along that row, then back along the other row so that the
#  last pin faces pin 1 (the usual coil-former convention; the PQ
#  50/50DG drawing, which does print its numbers, counts that way).  It
#  has to be confirmed against the vendor's bobbin drawing before the
#  specification goes out.  The ASSIGNMENT does not depend on it - which
#  row carries which winding is fixed - only the printed numbers do.
#
#  Assignment: the primary-referenced windings (NP1 and the ZCD auxiliary
#  NAUX) share one row and the two secondaries the other, so the
#  isolation distance is the whole bobbin.  The centre tap is made ON THE
#  PCB from the finish of NS2 and the start of NS3, which keeps the two
#  windings measurable one at a time; "start" is the end the polarity
#  dot marks, and NS2 and NS3 are wound in the same sense so that joining
#  NS2's finish to NS3's start makes the tap.  On the 20-pin former each
#  secondary terminal takes TWO pins: one winding carries the whole
#  secondary current (28 A rms) and a 0.8 mm pin is not rated for that -
#  the vendor confirms the pin rating or brings the foil out as a lug.
_ETD49_XY = {}
for _i in range(10):
    _x = -22.86 + 5.08 * _i
    _ETD49_XY[1 + _i] = (_x, -20.32)          # front row, left to right
    _ETD49_XY[20 - _i] = (_x, 20.32)          # back row, right to left
_PQ40_XY = {}
for _i, _y in enumerate((-17.78, -12.70, -7.62, 7.62, 12.70, 17.78)):
    _PQ40_XY[1 + _i] = (-19.05, _y)           # marked side, upwards
    _PQ40_XY[12 - _i] = (19.05, _y)           # other side, downwards
BOBBINS = {
    'ETD 49/25/16DG': dict(
        former='B66368', pins=20, pin='square 0.8 mm', xy=_ETD49_XY,
        map={'NP1': ((1, 2), (4, 5)), 'NAUX': ((8,), (10,)),
             'NS2': ((11, 12), (14, 15)), 'NS3': ((16, 17), (19, 20))},
        rows=('front row 1-10', 'back row 11-20'),
        #  outline of the mounting-direction view: 54.5 across the pins,
        #  56.2 along the coil axis; the coil sits between the flanges
        plan=dict(w=54.5, h=56.2, coil_w=35.9, coil_h=32.7, mark=None),
        pitch=5.08, rows_apart=40.64),
    'PQ 40/40': dict(
        former='B65884E', pins=12, pin='round 1.0 mm', xy=_PQ40_XY,
        map={'NP1': ((1,), (3,)), 'NAUX': ((4,), (6,)),
             'NS2': ((7,), (9,)), 'NS3': ((10,), (12,))},
        rows=('marked side 1-6', 'other side 7-12'),
        plan=dict(w=42.0, h=40.0, coil_w=None, coil_h=None,
                  mark=(-21.0, -20.0)),
        pitch=5.08, rows_apart=38.1),
}
BOBBIN = BOBBINS[CHOSEN]
PIN_XY = BOBBIN['xy']
PINMAP = BOBBIN['map']
CENTRE_TAP = PINMAP['NS2'][1] + PINMAP['NS3'][0]
PIN_NOTE = ('The datasheet prints no pin numbers; the numbering shown counts '
            'along one row from pin 1 and back along the other, the usual '
            'convention. Confirm it against the bobbin drawing before the '
            'specification is released; the assignment does not depend on '
            'it, only the printed numbers do.')
PIN_NOTE_KR = ('데이터시트에는 핀 번호가 없다. 여기 적은 번호는 핀 1 에서 한 '
               '열을 따라 세고 다른 열로 돌아오는 관례를 따랐다. 사양서를 내기 전에 '
               '보빈 도면으로 확인할 것. 번호 방향이 달라도 권선 배정은 그대로이고 '
               '표기 번호만 바뀐다.')


def _plus(t):
    return '+'.join(str(n) for n in t)


def pins(w, dash='\u2013'):
    """'1+2 - 4+5' style terminal text for the spec and the tables."""
    a, b = PINMAP[w]
    return '%s %s %s' % (_plus(a), dash, _plus(b))


def tap_text():
    """'14, 15, 16 and 17' - the pins joined on the board as the tap."""
    t = [str(n) for n in CENTRE_TAP]
    return ', '.join(t[:-1]) + ' and ' + t[-1]


def free_pins():
    used = {n for a, b in PINMAP.values() for n in a + b}
    return [n for n in sorted(PIN_XY) if n not in used]


#  Three more assumptions, kept beside J_CU and K_U for the same reason.
K_LITZ = 0.55       # copper fill of a served Litz bundle, insulation included
T_FOIL = 0.20       # mm, copper foil thickness - the nearest standard gauge
                    # at or under twice the skin depth
T_FOIL_INS = 0.05   # mm, interlayer insulation on each foil turn
#  Margin tape, per flange (2026-09-25, insulation.py).  The core counts as
#  PRIMARY: the primary fills the window almost to the outer legs (about
#  1.3 mm of air on ETD 49), so the core cannot be held at a reinforced
#  distance from it.  The primary-to-core distance is then functional and
#  the primary flange needs only enough tape to keep the Litz off it.
#  The secondary flange is part of the reinforced secondary-to-core path.
#  What the reinforced primary-to-secondary insulation rests on is the
#  SEPARATION between the two sections - insulation.py checks it.
MARGIN_P = 1.0      # mm, primary flange
MARGIN_S = 2.0      # mm, secondary flange
MARGIN = MARGIN_S   # the Korean edition still reads this until it is ported
#  The auxiliary winding supplies VCC and must follow the OUTPUT, so it is
#  wound over the secondary - in triple-insulated wire, which carries the
#  reinforced insulation to the primary-referenced winding by itself.
TIW_OD = 0.6        # mm, outer diameter of the TIW, assumed - vendor datasheet
D_STRAND = 0.10     # mm, Litz strand diameter
W_FOIL_MAX = 12.0   # mm, widest single foil strip before it is split in parallel


def litz(area_mm2):
    """-> (bundle outer diameter [mm], strand count) for a bare copper area."""
    a_strand = pi * D_STRAND ** 2 / 4.0
    n = int(area_mm2 / a_strand + 0.9999)
    return (4.0 * area_mm2 / (pi * K_LITZ)) ** 0.5, n


def winding(V, name=None):
    """The winding laid out along the bobbin, in millimetres.

    Side by side, not interleaved: a single-stage tank needs
    L_short/L_open = lambda/(1+lambda), and only a deliberate gap between
    primary and secondary gives leakage of that order.  The gap is
    therefore not slack - it is the resonant inductor, and this function
    reports what is left for it after the copper and the margins.  It is
    ALSO the reinforced insulation between primary and secondary (creepage
    along the tube and clearance across it), so it may not come out below
    insulation.separation_min(), whatever the leakage would like.

    Returns a dict the drawing can render directly.  Nothing is rounded
    for appearance: if the copper does not fit, 'gap' comes out negative
    and 'fits' is False.
    """
    name = name or CHOSEN
    M = MECH[name]
    rows = copper(V)
    ap, asec = rows[0][3], rows[1][3]
    dp, nstr = litz(ap)
    wf = asec / T_FOIL                       # foil width for one turn
    usable = M['wind_w'] - MARGIN_P - MARGIN_S
    r_tube = M['tube_od'] / 2.0
    r_free = M['r_win_out'] - r_tube         # radial room at the narrow section
    #  A foil wider than W_FOIL_MAX is split into parallel strips: one
    #  secondary winding of a single-core build wants 6 mm2, which as one
    #  0.20 mm foil would be 31 mm wide - wider than any bobbin here.
    n_foil = max(1, -(-int(wf / W_FOIL_MAX + 0.999999) // 1))
    n_foil = max(1, int(-(-wf // W_FOIL_MAX)))
    wf = wf / n_foil
    #  fewest primary layers that leave room for the foil and the
    #  separation the reinforced insulation needs (insulation.py) AND stay
    #  inside the radial room; if none does, the deepest that fits radially
    #  is reported so the shortfall is visible
    from insulation import separation_min        # lazy: it imports cores
    SEPARATION_MIN = separation_min()
    lay, chosen = 1, None
    while lay <= V['Np']:
        per = -(-V['Np'] // lay)             # ceil
        if lay * dp > r_free:
            break
        if per * dp + wf + SEPARATION_MIN <= usable:
            chosen = lay
            break
        lay += 1
    lay = chosen if chosen else max(1, int(r_free // dp))
    per = -(-V['Np'] // lay)
    rows_p = [min(per, V['Np'] - i * per) for i in range(lay)]
    wp = per * dp
    gap_ax = usable - wp - wf
    build_p = lay * dp
    build_s = 2 * V['Ns'] * n_foil * (T_FOIL + T_FOIL_INS)
    #  NAUX, one layer of TIW over the secondary foil (V['Naux'] turns)
    n_aux = int(V.get('Naux', 0))
    aux_fits = n_aux * TIW_OD <= wf
    build_s += TIW_OD if n_aux else 0.0
    return dict(
        name=name, M=M, Np=V['Np'], Ns=V['Ns'],
        ap=ap, asec=asec, d_litz=dp, n_strand=nstr,
        t_foil=T_FOIL, w_foil=wf, n_foil=n_foil, margin_p=MARGIN_P,
        margin_s=MARGIN_S, n_aux=n_aux, tiw_od=TIW_OD, usable=usable,
        layers=lay, per_layer=per, rows_p=rows_p, w_pri=wp, gap=gap_ax,
        build_p=build_p, build_s=build_s, r_tube=r_tube, r_free=r_free,
        sep_min=SEPARATION_MIN,
        fits=(gap_ax >= SEPARATION_MIN and build_p <= r_free
              and build_s <= r_free and aux_fits))


def report(V, name=None):
    """Print the fit arithmetic.  Run this before believing the drawing."""
    name = name or CHOSEN
    w = winding(V, name)
    M = w['M']
    out = [
        '%s   core %s   coil former %s' % (name, M['core'], M['former']),
        '  bobbin winding width      %6.2f mm   (datasheet)' % M['wind_w'],
        '  margin tape, both flanges %6.2f mm   (primary %.1f, secondary %.1f)'
        % (MARGIN_P + MARGIN_S, MARGIN_P, MARGIN_S),
        '  usable axial              %6.2f mm' % w['usable'],
        '  primary  %d turns of %.2f mm2 -> Litz %d x %.2f mm, bundle '
        'd = %.2f mm' % (w['Np'], w['ap'], w['n_strand'], D_STRAND,
                         w['d_litz']),
        '           %d layer(s) %s -> %6.2f mm axial, %.2f mm build'
        % (w['layers'], w['rows_p'], w['w_pri'], w['build_p']),
        '  secondary %d + %d turns of %.2f mm2 -> foil %.2f x %.2f mm%s'
        % (w['Ns'], w['Ns'], w['asec'], w['t_foil'], w['w_foil'],
           '' if w['n_foil'] == 1 else ' x %d in parallel' % w['n_foil']),
        '           %d turns -> %6.2f mm axial, %.2f mm build%s'
        % (2 * w['Ns'], w['w_foil'], w['build_s'],
           ' (with %d T of TIW NAUX on top)' % w['n_aux'] if w['n_aux'] else ''),
        '  LEFT FOR THE SEPARATION    %5.2f mm   %s (insulation needs %.2f)'
        % (w['gap'], 'ok' if w['gap'] >= w['sep_min'] else '** TOO NARROW',
           w['sep_min']),
        '  radial room at the narrow section %.2f mm  '
        '(window %.2f - bobbin r %.2f)' % (w['r_free'], M['r_win_out'],
                                           w['r_tube']),
        '  primary build %.2f mm %s   secondary build %.2f mm %s'
        % (w['build_p'], 'ok' if w['build_p'] <= w['r_free'] else '** TOO DEEP',
           w['build_s'], 'ok' if w['build_s'] <= w['r_free'] else '** TOO DEEP'),
        '  VERDICT %s' % ('fits' if w['fits'] else '** DOES NOT FIT'),
    ]
    return '\n'.join(out)
