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
        #  set totals: G2 and G3 are dimensions of ONE half, and a set
        #  is two identical halves, so it carries 2 x (G2 + G3)
        AL_gaps={100: 2 * (1.67 + 0.85), 250: 2 * (0.62 + 0.23),
                 400: 2 * (0.31 + 0.18)}),
    #  E 60/22/16 - Magnetics 0R46016EC (R material, the power ferrite
    #  with its loss minimum near 100 C), Magnetics "Ferrite Cores" 2022
    #  catalogue p. 30-31: l_e 110, A_e 248 (min 240), V_e 27200, 135 g
    #  a set, A_L 5733 nH ungapped in R; gapped to A_L on order (p. 18).
    #  No coil former is catalogued for it: the two-section former is
    #  CUSTOM, and A_N and l_N are computed from MECH below, not read.
    #  Chosen 2026-09-25 by a search over the Magnetics and TDK ranges
    #  for the one window that takes the section winding at the tank's
    #  leakage with both sections filling the depth (HISTORY.md).
    'E 60/22/16': dict(
        core='0R46016EC', former='custom two-section former',
        le=110.0, Ae=248.0, Amin=240.0, Ve=27200.0, mass=135.0,
        AN=None, lN=None,
        AL_ungapped=5733.0, material='Magnetics R', vendor='Magnetics'),
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
    #  E 60/22/16, Magnetics catalogue p. 31: A 59.99, B 22.3 (one half,
    #  so the set is 44.6 high), C 15.62 (depth), D 13.8 min (one half
    #  of the window height), E 44.0 min (between the outer legs), F
    #  15.62 +-0.38 (the centre leg, RECTANGULAR, F wide across the window
    #  and C deep).  Minima are used where the drawing gives them, so the
    #  radial room is a minimum: 22.0 - 18.6 / 2 = 12.70 mm.
    #  The former is custom (none catalogued).  Its dimensions are the
    #  SPECIFICATION this note gives the bobbin maker, not a reading:
    #  tube 18.6 wide = F max 16.0 + 0.3 clearance + 2 x 1.15 wall (the
    #  wall and clearance of TDK's catalogue coil formers); flanges at least
    #  FLANGE_MIN, made as thick as the winding leaves (winding()); pins as
    #  BOBBINS below.  'shape': 'E' tells the turn-length arithmetic that
    #  the leg is rectangular.
    'E 60/22/16': dict(
        core='0R46016EC', former='custom two-section former',
        shape='E', custom=True,
        W=60.0, H=44.6, d_centre=15.62, win_h=27.6, r_win_out=22.0,
        plan_w=60.0, plan_d=15.62,
        tube_od=18.6, bore=16.3, wind_w=27.6 - 2 * 1.35, flange_h=27.6,
        pitch_a=5.08, pitch_b=None, pins=20, rows=40.64),
}
FLANGE_MIN = 1.35   # mm, thinnest flange of a custom former - the flange of
                    # TDK's catalogue coil formers, taken as the moulding
                    # minimum; ASSUMED, the bobbin maker decides


def turn(name):
    """-> (mean turn l_N [mm], share of it inside the core) of a winding
    that fills the radial room of MECH[name].

    Round leg: the datasheet's l_N, and the two arcs of core depth over
    the circumference at mid-winding.  Rectangular leg (shape 'E'): the
    turn follows the tube - two straight sides of F, two of C - and turns
    the corners on a radius of the tube wall plus half the winding; the
    two C sides are the part inside the core."""
    M = MECH[name]
    room = M['r_win_out'] - M['tube_od'] / 2.0
    wall = (M['tube_od'] - M['d_centre']) / 2.0
    if M.get('shape') == 'E':
        ln = 2 * (M['d_centre'] + M['plan_d']) + 2 * pi * (wall + room / 2)
        return ln, min(1.0, 2 * M['plan_d'] / ln)
    r_mean = M['tube_od'] / 2.0 + room / 2.0
    return CORES[name]['lN'], min(1.0, 2 * M['plan_d'] / (2 * pi * r_mean))


for _n, _M in MECH.items():
    if _M.get('custom'):
        CORES[_n]['lN'] = turn(_n)[0]
        CORES[_n]['AN'] = (_M['r_win_out'] - _M['tube_od'] / 2.0) * _M['wind_w']

# ===================================================================
#  The core this note builds on, and its coil-former terminals
# ===================================================================
#  CHOSEN names the core the design example is drawn and specified on.
#  Everything downstream - the section figure, the pin figure, the tables
#  of the note and the vendor specification - reads it from here.
#
#  E 60/22/16 (Magnetics), 2026-09-25.  The section winding the user asked
#  for (onsemi-style, no split primary, a partition, tape on every layer,
#  no empty space in the former) reaches the tank's L_short only in a
#  window that is DEEP and SHORT - leakage goes as the mean turn times the
#  section widths over the depth.  A search over the Magnetics and TDK
#  ranges (EER, ER, EC, E and the rest) found E 60/22/16 (14.2 mm deep,
#  27.6 mm high) the one that does it with both sections filling the depth.
#  HISTORY.md 2026-09-25.
CHOSEN = 'E 60/22/16'

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
#  E 60/22/16, custom former: twenty terminals in two rows of ten, pitch
#  5.08 (9 x 5.08 = 45.72), rows 40.64 apart, square 0.8 mm pins - this
#  note's specification to the bobbin maker.
#
#  NUMBERING IS THEREFORE AN ASSUMPTION on both: 1 at one end of one row,
#  counted along that row, then back along the other row so that the
#  last pin faces pin 1 (the usual coil-former convention; the PQ
#  50/50DG drawing, which does print its numbers, counts that way).  It
#  has to be confirmed against the vendor's bobbin drawing before the
#  specification goes out.  The ASSIGNMENT does not depend on it - which
#  row carries which winding is fixed - only the printed numbers do.
#
#  Assignment: the primary-referenced windings (NP1 and the VCC/ZCD auxiliary
#  NAUX) share one row and the two secondaries the other, so the
#  isolation distance is the whole bobbin.  The centre tap is made ON THE
#  PCB from the finish of NS2 and the start of NS3, which keeps the two
#  windings measurable one at a time; "start" is the end the polarity
#  dot marks, and NS2 and NS3 are wound in the same sense so that joining
#  NS2's finish to NS3's start makes the tap.  On the 20-pin former each
#  secondary terminal takes TWO pins, one per sub-winding (14 A rms a
#  pin) - the vendor confirms the pin rating.
_ROW20_XY = {}
for _i in range(10):
    _x = -22.86 + 5.08 * _i
    _ROW20_XY[1 + _i] = (_x, -20.32)          # front row, left to right
    _ROW20_XY[20 - _i] = (_x, 20.32)          # back row, right to left
_PQ40_XY = {}
for _i, _y in enumerate((-17.78, -12.70, -7.62, 7.62, 12.70, 17.78)):
    _PQ40_XY[1 + _i] = (-19.05, _y)           # marked side, upwards
    _PQ40_XY[12 - _i] = (19.05, _y)           # other side, downwards
#  Each end of NS2 and NS3 takes two pins: a winding is two sub-windings
#  of four Litz bundles in parallel (winding()), and each sub-winding ends
#  on its own pin.  NP1 is two TIW-Litz bundles in parallel, one to each
#  pin of a pair.
BOBBINS = {
    'E 60/22/16': dict(
        former='custom two-section', pins=20, pin='square 0.8 mm',
        xy=_ROW20_XY,
        map={'NP1': ((1, 2), (4, 5)), 'NAUX': ((8,), (10,)),
             'NS2': ((11, 12), (14, 15)), 'NS3': ((16, 17), (19, 20))},
        rows=('front row 1-10', 'back row 11-20'),
        plan=dict(w=64.0, h=50.0, coil_w=44.0, coil_h=27.6, mark=None),
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
PIN_NOTE = ('The former is custom, so its pins are this note\'s '
            'specification: the numbering counts along one row from pin 1 '
            'and back along the other, the usual convention. Agree it with '
            'the bobbin maker\'s drawing before the specification is '
            'released; the assignment does not depend on it, only the '
            'printed numbers do.')
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
#  Margin tape, per flange, of the WITHDRAWN side-by-side layout
#  (winding_v64, kept for the unported Korean edition).  There the core
#  counted as PRIMARY: the primary fills the window almost to the outer legs (about
#  1.3 mm of air), so the core cannot be held at a reinforced
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


def winding_v64(V, name=None):
    """WITHDRAWN 2026-09-25 - the side-by-side foil layout of rounds 63-65.

    Kept only because the Korean edition (an_kr_body.py), which has not
    been ported since, still reads its keys; delete it with that port.
    leakage.py showed it leaks about 27 uH against the 11 uH asked, and
    that its radial field crosses the foil.  The text below is its own.

    The winding laid out along the bobbin, in millimetres.

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


#  The construction since 2026-09-25 (user: integrated leakage, Litz
#  secondary).  leakage.py found that no side-by-side layout on these cores
#  leaks as little as 11 uH once the separation also has to be the
#  reinforced insulation (6.4 mm): about 28 uH with a Litz secondary.  So
#  the insulation moves into the WIRE: NP1 is triple-insulated Litz, NAUX is
#  TIW, and the core is on the secondary's side.
#
#  The WINDING is a plain section winding on a TWO-SECTION coil former, the
#  way the onsemi / Fairchild LLC reference transformers are wound (user,
#  2026-09-25: "do not split the primary; wind it like onsemi", then "with
#  a partition"):
#
#      flange | NP1, one section | PARTITION | NS2 + NS3 | tape | flange
#
#  No catalogue former has two sections; the former is custom, and its
#  partition G_NOM is set by the leakage (leakage.py).  A split primary
#  (part of NP1 on each side of the secondary) was the other way and was
#  withdrawn at the user's request.
TIW_LITZ_ADD = 0.2  # mm, triple insulation over the Litz bundle, on the
                    # diameter - assumed, the wire vendor's datasheet decides
#  The layout (2026-09-25, E 60/22/16).  Both sections are as deep as the
#  radial room; the wire is sized to FILL it, so the diameters come out of
#  the room and the layer counts, and the current density is the result
#  (checked against J_CU).  The user asked for thin bundles that can be
#  wound by hand (the 3 x 498-strand secondary of the first E 60 layout
#  was judged unwindable): the primary is two TIW-Litz bundles in parallel
#  (bifilar), the secondary turn is eight thin bundles - two sub-windings of
#  four, stacked, each sub-winding one layer per turn.
PRI_PAR = 2         # TIW-Litz bundles per primary turn, wound bifilar
PRI_LAYERS = 6      # 30 bundle positions -> 5 a layer (2.5 turns)
SEC_PAR = 8         # Litz bundles per secondary turn
SEC_SUB = 2         # ... as this many sub-windings of SEC_PAR / SEC_SUB,
                    # paralleled at the pins (each on its own pin)
SEC_LAYERS = 8      # one sub-winding turn per layer: 2 windings x 2 T x 2
SEC_ORDER = ('NS2', 'NS2', 'NS3', 'NS3', 'NS2', 'NS2', 'NS3', 'NS3')
                    # layer by layer from the tube: NS2a, NS3a, NS2b, NS3b,
                    # two turns each - every sub-winding in two adjacent
                    # layers, NS2 and NS3 each once near the tube
K_WIND = 1.10       # winding pitch over bundle diameter, along the layer and
                    # layer to layer: a real winding is not packed tight
                    # (user, 2026-09-25: "leave for the small gaps").
                    # ASSUMED; the first sample's measured build replaces it.
                    # The wire is sized so that the winding at K_WIND fills
                    # the room; a tighter one leaves the difference to the
                    # margin tape and a finishing wrap.
G_NOM = 1.1         # mm, the partition - set so that L_short = L_r at K_WIND
                    # by leakage.py (the trimming knob after the first sample)
T_TAPE = 0.05       # mm, one wrap of layer tape over every winding layer
                    # and over NAUX, as the onsemi reference winding shows
                    # (user, 2026-09-25) - ASSUMED thickness; functional
                    # only, the reinforced insulation is in the wire
MARGIN_F = 1.0      # mm, margin tape at each flange - mechanical only now
                    # (keeps the Litz off the flange); no insulation role


def winding(V, name=None, g=None, k=None, order=None):
    """The section winding laid out along the former, in millimetres.

        flange | margin | NP1 | PARTITION | NS2/NS3 + NAUX | margin | flange

    Axial positions run from the primary margin's outer edge (y = 0) - the
    inside of the primary flange - to the other flange (y = wind_w); radial
    heights from the top of the tube.  The bundles are sized so that the
    two sections, wound at pitch K_WIND, both fill the radial room; k
    builds the same wire at another pitch (k = 1.0: packed tight) to see
    what the looseness does.  On a custom former the flanges take what the
    winding leaves of the window height ('flange'); on a catalogue former
    what is left is margin tape ('spare').  Nothing is rounded for
    appearance: if it does not fit, 'fits' is False and the reason is in
    'why'.
    """
    name = name or CHOSEN
    g = G_NOM if g is None else g
    k = K_WIND if k is None else k
    order = SEC_ORDER if order is None else order
    M = MECH[name]
    rows = copper(V)
    Np, Ns = V['Np'], V['Ns']
    r_free = M['r_win_out'] - M['tube_od'] / 2.0
    why = []
    #  wire from the room: PRI_LAYERS layers of pitch dp K_WIND + tape
    dp = (r_free / PRI_LAYERS - T_TAPE) / K_WIND
    d_bare = dp - TIW_LITZ_ADD
    area_p = pi * K_LITZ * d_bare ** 2 / 4.0          # copper, one bundle
    nstr = int(area_p / (pi * D_STRAND ** 2 / 4.0) + 0.9999)
    n_aux = int(V.get('Naux', 0))
    h_aux = (TIW_OD * K_WIND + T_TAPE) if n_aux else 0.0
    ds = ((r_free - h_aux) / SEC_LAYERS - T_TAPE) / K_WIND
    area_s = pi * K_LITZ * ds ** 2 / 4.0
    nstr_s = int(area_s / (pi * D_STRAND ** 2 / 4.0) + 0.9999)
    j_p = rows[0][2] / (PRI_PAR * area_p)
    j_s = rows[1][2] / (SEC_PAR * area_s)
    #  the build at pitch k
    pos = Np * PRI_PAR
    per = -(-pos // PRI_LAYERS)
    rA = [min(per, pos - q * per) for q in range(PRI_LAYERS)]
    wA, hA = per * dp * k, PRI_LAYERS * (dp * k + T_TAPE)
    per_s = 2 * Ns * SEC_PAR // SEC_LAYERS
    wS = per_s * ds * k
    hS = SEC_LAYERS * (ds * k + T_TAPE)
    hS_aux = hS + ((TIW_OD * k + T_TAPE) if n_aux else 0.0)
    need = 2 * MARGIN_F + wA + g + wS
    if M.get('custom'):
        flange = (M['win_h'] - (2 * MARGIN_F + wA + g + wS)
                  if k == K_WIND else None)
        #  the former is made for the K_WIND build; a tighter one leaves
        #  its difference in the margin tape of the secondary side
        if flange is None:
            w0 = winding(V, name, g, order=order)
            flange, wind_w = w0['flange'], w0['wind_w']
        else:
            flange /= 2.0
            wind_w = M['win_h'] - 2 * flange
        if flange < FLANGE_MIN:
            why.append('flanges %.2f mm, under %.2f' % (flange, FLANGE_MIN))
    else:
        flange = (M['flange_h'] - M['wind_w']) / 2.0
        wind_w = M['wind_w']
    spare = wind_w - need
    yA0 = MARGIN_F
    yA1 = yA0 + wA
    yS0 = yA1 + g
    yS1 = yS0 + wS
    if spare < -1e-9:
        why.append('axial: %.2f mm short' % -spare)
    if hA > r_free + 1e-9:
        why.append('primary %.2f mm deep, room %.2f' % (hA, r_free))
    if hS_aux > r_free + 1e-9:
        why.append('secondary + NAUX %.2f mm deep, room %.2f' % (hS_aux, r_free))
    if n_aux * TIW_OD > wS:
        why.append('NAUX wider than the secondary')
    #  bundle map of the secondary group, layer by layer from the tube; the
    #  sub-winding letter of each layer beside it
    smap = [[order[q]] * per_s for q in range(SEC_LAYERS)]
    seen = {}
    sub = []
    for q in range(SEC_LAYERS):
        who = order[q]
        n = seen.get(who, 0)
        seen[who] = n + 1
        sub.append('%s%s' % (who, 'ab'[n // Ns]))
    return dict(
        name=name, M=M, Np=Np, Ns=Ns, nA=Np, nB=0,
        ap=rows[0][3], asec=rows[1][3], d_litz=d_bare, d_pri=dp,
        n_strand=nstr, pri_par=PRI_PAR, area_p=area_p, j_p=j_p,
        tiw_add=TIW_LITZ_ADD, d_sec=ds, n_strand_s=nstr_s, sec_par=SEC_PAR,
        sec_sub=SEC_SUB, area_s=area_s, j_s=j_s,
        sec_layers=SEC_LAYERS, per_layer_s=per_s, smap=smap, sub=sub,
        layers_A=PRI_LAYERS, per_A=per, rows_A=rA, w_A=wA, h_A=hA,
        layers_B=0, per_B=0, rows_B=[], w_B=0.0, h_B=0.0,
        w_S=wS, h_S=hS, h_S_aux=hS_aux, n_aux=n_aux, tiw_od=TIW_OD,
        t_tape=T_TAPE, k=k, k_wind=K_WIND,
        gap=g, n_gaps=1, room=wind_w - 2 * MARGIN_F - wA - wS,
        spare=spare, margin=MARGIN_F, flange=flange, wind_w=wind_w,
        yA=(yA0, yA1), yS=(yS0, yS1), yB=(yS1, yS1),
        r_tube=M['tube_od'] / 2.0, r_free=r_free,
        fits=not why, why=why)


def report(V, name=None):
    """Print the fit arithmetic.  Run this before believing the drawing."""
    name = name or CHOSEN
    w = winding(V, name)
    M = w['M']
    out = [
        '%s   core %s   coil former %s' % (name, M['core'], M['former']),
        '  radial room %.2f mm  (window %.2f - tube %.2f / 2), window '
        'height %.1f' % (w['r_free'], M['r_win_out'], M['tube_od'],
                         M['win_h']),
        '  winding pitch K_WIND %.2f x the bundle, margin tape %.2f mm, '
        'partition %.2f mm' % (w['k_wind'], MARGIN_F, w['gap']),
        '  NP1 %d T, %d TIW-Litz bundles in parallel, %d x %.2f mm, bundle '
        '%.2f + %.2f = %.2f mm, J %.2f A/mm2'
        % (w['Np'], w['pri_par'], w['n_strand'], D_STRAND, w['d_litz'],
           w['tiw_add'], w['d_pri'], w['j_p']),
        '      %d layers %s -> %5.2f mm axial, %.2f mm deep'
        % (w['layers_A'], w['rows_A'], w['w_A'], w['h_A']),
        '  NS2, NS3 %d T each, %d Litz bundles per turn (%d sub-windings), '
        '%d x %.2f mm, d %.2f mm, J %.2f A/mm2'
        % (w['Ns'], w['sec_par'], w['sec_sub'], w['n_strand_s'], D_STRAND,
           w['d_sec'], w['j_s']),
        '      %d layers %s -> %5.2f mm axial, %.2f mm deep, %.2f with NAUX'
        % (w['sec_layers'], w['sub'], w['w_S'], w['h_S'], w['h_S_aux']),
        '  winding width %.2f mm, flanges %.2f mm, spare %.2f mm'
        % (w['wind_w'], w['flange'], w['spare']),
        '  VERDICT %s' % ('fits' if w['fits'] else
                          '** DOES NOT FIT: ' + '; '.join(w['why'])),
    ]
    return '\n'.join(out)
