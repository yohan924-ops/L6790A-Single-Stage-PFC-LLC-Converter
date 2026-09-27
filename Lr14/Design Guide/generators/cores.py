# -*- coding: utf-8 -*-
"""Ferrite cores, as printed in the manufacturer's catalogue.

Nothing in CORES or MECH is remembered or estimated: every number is
copied from the TDK document named beside it, and everything else here is
arithmetic on those numbers and on the design.  Three cores are carried:

    ETD 54/28/19 core B66395 and coil former B66396W, TDK October 2022 -
                 the single transformer of this note's design example
                 (CHOSEN, Lr14 copy 2026-09-27)

    E 60/22/16   PC47EE60-Z, TDK "Ferrite Core for Switching Power
                 Supplies" (20231117), p. 22 and p. 31 - the example's
                 core until 2026-09-27; its former was custom
    PQ 40/40     core B65883A, coil former B65884E, October 2022 - one unit
                 of the three-unit build of the SMath sheet

Window symbols follow the datasheets: A_N is the winding cross-section of
the coil former and l_N its mean turn length.
"""
from math import pi

MU0 = 4e-7 * pi

CORES = {
    'PQ 40/40': dict(
        core='B65883A', former='B65884E',
        le=93.0, Ae=189.0, Amin=174.0, Ve=17580.0, mass=90.0,
        AN=309.0, lN=87.0,
        AL_ungapped=5500.0, material='N95'),
    #  E 60/22/16 - TDK PC47EE60-Z (JIS FEE60A), PC47 material, catalogue
    #  p. 31: C1 0.446 /mm, l_e 110, A_e 247, A_cp min 231, V_e 27100,
    #  A_cw 407 mm2, 135 g a set, A_L 5670 nH +-25 % ungapped; core loss
    #  11.35 W max at 100 kHz, 200 mT, 100 C.  Gapped stock is 250 and
    #  500 nH (p. 22); any other A_L is ground to order.  The centre-pole gap
    #  curve of p. 31 is A_L = 373.02 lg^-0.7405 (lg in mm), drawn from about
    #  0.13 mm to about 2 mm.  No coil former is catalogued: the former is
    #  CUSTOM, and A_N and l_N are computed from MECH below, not read.
    'E 60/22/16': dict(
        core='PC47EE60-Z', former='custom coil former',
        le=110.0, Ae=247.0, Amin=231.0, Ve=27100.0, mass=135.0,
        AN=None, lN=None, Acw=407.0,
        AL_ungapped=5670.0, material='TDK PC47', vendor='TDK',
        P_core_max=(11.35, 100.0, 200.0, 100.0),   # W at kHz, mT, C
        AL_curve=(373.02, -0.7405, 0.13, 2.0)),    # a, b, lg from, lg to
    #  ETD 54/28/19 - TDK B66395 core, 10/2022 data sheet p. 2-3: l_e 127,
    #  A_e 280, A_min 280, V_e 35600, 180 g a set; ungapped A_L 4600 nH
    #  (N97) and P_V < 2.60 W a set at 100 mT, 100 kHz, 100 C (N97).  The
    #  gap relation of p. 3 is A_L = K1 s^K2 with K1 393, K2 -0.779 (N87,
    #  25 C), valid 0.10 to 3.50 mm.  Coil former B66396W, p. 4: one
    #  section, A_N 315.6 mm2, l_N 96 mm, 22 pins.
    'ETD 54/28/19': dict(
        core='B66395', former='B66396W',
        le=127.0, Ae=280.0, Amin=280.0, Ve=35600.0, mass=180.0,
        AN=315.6, lN=96.0,
        AL_ungapped=4600.0, material='TDK N97', vendor='TDK',
        P_core_max=(2.60, 100.0, 100.0, 100.0),   # W at kHz, mT, C
        AL_curve=(393.0, -0.779, 0.10, 3.50),
        #  gapped stock, p. 2: (gap mm, A_L nH approx.), N27 and N87 only
        stock=((0.20, 1377.0), (0.50, 670.0), (1.00, 393.0), (1.50, 287.0),
               (2.00, 229.0)), stock_mat='N27 and N87'),
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


def gap_len(V, name=None):
    """-> (centre-leg gap [mm] for the design A_L, True if the catalogue
    curve covers it).

    From the catalogue's A_L-against-gap curve where it has one (a fit of
    the vendor's measurement, fringing included); gap() otherwise.  Past
    the drawn end of the curve the fit is extrapolated, and the flag says
    so - the vendor grinds to A_L, not to this length.
    """
    name = name or CHOSEN
    R = CORES[name]
    cv = R.get('AL_curve')
    if not cv:
        return gap(V, R['Ae']), False
    a, b, lo, hi = cv
    lg = (V['AL'] / a) ** (1.0 / b)
    return lg, lo <= lg <= hi


def dg_gap(V, name=None):
    """The gap length alone - the Korean edition reads this name."""
    return gap_len(V, name)[0]


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
    #  E 60/22/16, TDK PC47EE60-Z, catalogue p. 31 (the set drawn with
    #  its dimensions): A 60.0 +1.1/-0.8 wide, 44.6 +-0.6 high as a set
    #  (22.3 +-0.3 a half), C 15.6 +-0.4 deep, centre leg D 15.6 +-0.4 wide
    #  and C deep (RECTANGULAR), E 43.8 min between the outer legs, F
    #  14.05 +-0.25 the half-window height, outer legs H 7.7.  The limits
    #  that make the window smallest are used: 2 x 13.8 = 27.6 high,
    #  21.9 from the centre line to an outer leg.
    #  The former is custom (none catalogued).  Its dimensions are the
    #  SPECIFICATION this note gives the bobbin maker, not a reading:
    #  tube 18.6 wide = D max 16.0 + 2 x (0.15 clearance + 1.15 wall), the
    #  wall and clearance of TDK's catalogue coil formers; flanges at least
    #  FLANGE_MIN, made as thick as the winding leaves (winding()); pins as
    #  BOBBINS below.  The radial room is then 21.9 - 9.3 = 12.60 mm, a
    #  minimum.  'shape': 'E' tells the turn-length arithmetic that the leg
    #  is rectangular.
    'E 60/22/16': dict(
        core='PC47EE60-Z', former='custom coil former',
        shape='E', custom=True,
        W=60.0, H=44.6, d_centre=15.6, win_h=27.6, r_win_out=21.9,
        plan_w=60.0, plan_d=15.6,
        tube_od=18.6, bore=16.3, wind_w=27.6 - 2 * 1.35, flange_h=27.6,
        pitch_a=5.08, pitch_b=None, pins=24, rows=40.64),
    #  ETD 54/28/19, TDK B66395 core (10/2022, p. 2): 54.5 +-1.3 wide, 27.8
    #  -0.4 a half (55.6 as a set), window 19.8 +0.8 a half, centre leg
    #  diameter 19.3 -0.8 and core depth 19.3 -0.8, 40.1 +2.2 between the
    #  outer legs.  The limits that make the window smallest: 2 x 19.8 =
    #  39.6 high, 20.05 from the centre line to an outer leg.
    #  Coil former B66396W (p. 4): tube 22 max over a 19.8 min bore,
    #  flanges 39.5 -0.4 across (19.55 radius at the least), 36.8 min
    #  between the flanges, 39.4 max over them, 22 pins of 1 mm in two rows
    #  of 11 at 5.08, rows 45.72 apart.  A_N = 36.8 x (39.1 - 22)/2 = 315
    #  against the catalogue's 315.6, l_N = pi (22 + 8.55) = 96.0 against
    #  96 - the reading is sound.  The catalogue former has one section;
    #  the 2.0 mm partition is this note's addition (PARTITION).
    'ETD 54/28/19': dict(
        core='B66395', former='B66396W', partition=True,
        W=54.5, H=55.6, d_centre=19.3, win_h=39.6, r_win_out=20.05,
        r_room=19.55, plan_w=54.5, plan_d=19.3,
        tube_od=22.0, bore=19.8, wind_w=36.8, flange_h=39.4,
        pitch_a=5.08, pitch_b=None, pins=22, rows=45.72),
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
#  ETD 54/28/19 (TDK B66395 + catalogue former B66396W), Lr14 copy
#  2026-09-27.  User: a catalogue coil former with its pins on the data
#  sheet, a 2.0 mm partition, and nothing left empty.  The section winding
#  (primary in one section, the secondaries in the other, tape on every
#  layer, both sections filling the radial room) is then fixed by the
#  former: its leakage IS the tank's L_r, and the tank follows from it
#  (L_r 23.4 uH, lambda 0.55, C_r 200 nF).  Of the eleven TDK cores with a
#  pinned catalogue former checked that day, six fill with a 2.0 mm
#  partition; ETD 54/28/19 was taken for the pins and the loss.
#  HISTORY.md 2026-09-27.
CHOSEN = 'ETD 54/28/19'

#  ETD 54/28/19 (B66396W, page 4): twenty-two pins of 1 mm in two rows,
#  pitch 5.08, rows 45.72 apart; each row has twelve places, one of them
#  the 3.4 mm fixing hole (at opposite ends of the two rows), and a "Pin 1
#  marking" - no other number.
#
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
#  E 60/22/16, custom former: twenty-four terminals in two rows of twelve,
#  pitch 5.08 (11 x 5.08 = 55.88, inside the 60 mm core), rows 40.64 apart,
#  square 0.8 mm pins - this note's specification to the bobbin maker.
#
#  NUMBERING IS THEREFORE AN ASSUMPTION on both: 1 at one end of one row,
#  counted along that row, then back along the other row so that the
#  last pin faces pin 1 (the usual coil-former convention).  It
#  has to be confirmed against the vendor's bobbin drawing before the
#  specification goes out.  The ASSIGNMENT does not depend on it - which
#  row carries which winding is fixed - only the printed numbers do.
#
#  Assignment: the primary-referenced windings (NP1 and the VCC/ZCD auxiliary
#  NAUX) share one row and the two secondaries the other, so the
#  isolation distance is the whole bobbin.  "Start" is the end the polarity
#  dot marks, and NS2 and NS3 are wound in the same sense so that NS2's
#  finish and NS3's start make the centre tap.  At most TWO bundles are
#  soldered to one pin (user, 2026-09-26).  A secondary turn is five Litz
#  bundles (winding()): an end is three pins (2 + 2 + 1), and the two
#  secondaries would need twelve pins in a row of eleven.  So NS2's finish
#  and NS3's start share the five tap pins (ten bundles, two a pin): the tap
#  is made at the pins, and each half is still measured on its own - NS2
#  from its start pins to the tap pins, NS3 from the tap pins to its
#  finish.  NP1 is three TIW-Litz bundles a turn: two pins an end (2 + 1).
#  NAUX is one TIW, one pin an end.
_ROW24_XY = {}
for _i in range(12):
    _x = -27.94 + 5.08 * _i
    _ROW24_XY[1 + _i] = (_x, -20.32)          # front row, left to right
    _ROW24_XY[24 - _i] = (_x, 20.32)          # back row, right to left
_PQ40_XY = {}
for _i, _y in enumerate((-17.78, -12.70, -7.62, 7.62, 12.70, 17.78)):
    _PQ40_XY[1 + _i] = (-19.05, _y)           # marked side, upwards
    _PQ40_XY[12 - _i] = (19.05, _y)           # other side, downwards
_ETD54_XY = {}
for _i in range(11):
    _ETD54_XY[1 + _i] = (-27.94 + 5.08 * (_i + 1), -22.86)   # hole at the left
    _ETD54_XY[22 - _i] = (-27.94 + 5.08 * _i, 22.86)        # hole at the right
BOBBINS = {
    'ETD 54/28/19': dict(
        former='B66396W', pins=22, pin='round 1.0 mm',
        xy=_ETD54_XY,
        map={'NP1': ((1, 2), (4, 5)), 'NAUX': ((8,), (10,)),
             'NS2': ((12, 13, 14), (15, 16, 17, 18, 19)),
             'NS3': ((15, 16, 17, 18, 19), (20, 21, 22))},
        rows=('primary row 1-11', 'secondary row 12-22'),
        #  outline drawn round the two pin rows (not dimensioned); coil =
        #  flange 39.5 across, 39.4 over the flanges
        plan=dict(w=61.6, h=60.0, coil_w=39.5, coil_h=39.4, mark=None),
        pitch=5.08, rows_apart=45.72),
    'E 60/22/16': dict(
        former='custom', pins=24, pin='square 0.8 mm',
        xy=_ROW24_XY,
        map={'NP1': ((1,), (3,)), 'NAUX': ((10,), (12,)),
             'NS2': ((13, 14, 15), (16, 17, 18)),
             'NS3': ((19, 20, 21), (22, 23, 24))},
        rows=('front row 1-12', 'back row 13-24'),
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
CENTRE_TAP = tuple(sorted(set(PINMAP['NS2'][1] + PINMAP['NS3'][0])))
PIN_NOTE_ETD = ('The data sheet marks pin 1 and gives no other number; the '
                'numbering here counts along one row from pin 1 and back along '
                'the other, the usual convention. Agree it with the bobbin '
                'maker\'s drawing before the specification is released; the '
                'assignment does not depend on it, only the printed numbers '
                'do.')
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
if not MECH[CHOSEN].get('custom'):          # a catalogue former: pin 1 is marked
    PIN_NOTE = PIN_NOTE_ETD


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


#  The construction.  The leakage is integrated (no separate resonant
#  inductor), and no side-by-side layout leaks as little as L_r once the
#  space between the windings also has to be the reinforced insulation.  So
#  the insulation is in the WIRE: NP1 is triple-insulated Litz, NAUX is TIW,
#  and the core is on the secondary's side (insulation.py).
#
#  The WINDING is a section winding on a two-section (split) coil former, the
#  construction of the LLC references (onsemi AN-4151, TDK SRX/SRV, Infineon,
#  the LGE production part), with a wrap of tape over every layer:
#
#      flange | margin | NP1 | PARTITION | NS2 + NS3, NAUX over them | margin | flange
#
#  Lr14 copy: the flanges are the thinnest the former allows (FLANGE_MIN) and
#  the partition takes the whole width the winding leaves, so nothing in the
#  former is empty; with L.r = 14 uH that lands on the tank's L_short
#  (leakage.py).
#
#  Both sections are as deep as the radial room and the wire is sized to
#  FILL it, so the bundle diameters come out of the room and the layer
#  counts, and the current density is the result (checked against J_CU).
#  NP1 is one TIW-Litz bundle; a secondary turn is SEC_PAR Litz bundles
#  side by side in one layer - the bundles of a turn are never split by
#  tape - and one turn fills a layer.
TIW_LITZ_ADD = 0.2  # mm, triple insulation over the Litz bundle, on the
                    # diameter - assumed, the wire vendor's datasheet decides
PRI_LAYERS = 4      # NP1, 15 T as 4 + 4 + 4 + 3, the last layer spread
PRI_PAR = 3         # TIW-Litz bundles side by side in a primary turn
SEC_PAR = 5         # Litz bundles side by side in a secondary turn
SEC_LAYERS = 4      # one secondary turn a layer: 2 windings x 2 T
SEC_ORDER = ('NS2', 'NS3', 'NS2', 'NS3')
                    # layer by layer from the tube; see winding()
K_WIND = 1.10       # winding pitch over bundle diameter, along the layer and
                    # layer to layer: a real winding is not packed tight
                    # (user, 2026-09-25: "leave for the small gaps").
                    # ASSUMED; the first sample's measured build replaces it.
                    # The wire is sized so that the winding at K_WIND fills
                    # the radial room.  Along the layer the pitch is spread
                    # a little further ('k_ax') so that the two sections and
                    # the partition fill the winding width exactly.
T_TAPE = 0.05       # mm, one wrap of layer tape over every winding layer
                    # and over NAUX - ASSUMED thickness; functional only,
                    # the reinforced insulation is in the wire
MARGIN_F = 0.0      # mm, margin tape at each flange - none (user,
                    # 2026-09-26: nothing left empty; the insulation is in
                    # the wire)
PARTITION = 2.0     # mm, the partition added to a one-section catalogue
                    # former (user, 2026-09-27); ASSUMED mouldable - the
                    # bobbin maker decides


def winding(V, name=None, g=None, k=None, order=None):
    """The section winding laid out along the former, in millimetres.

        flange | margin | NP1 | NS2/NS3 + NAUX | margin | flange

    Axial positions run from the inside of the primary flange (y = 0) to
    the other flange (y = wind_w); radial heights from the top of the tube.
    The bundles are sized so that the two sections, wound at pitch K_WIND,
    both fill the radial room; k builds the same wire at another pitch
    (k = 1.0: packed tight) to see what the looseness does.  On the custom
    former the flanges are FLANGE_MIN and the PARTITION takes what the
    K_WIND winding leaves of the window height ('sep'); g sets another
    partition (a thinner one leaves 'spare', the trimming direction).  On a
    catalogue former what is left is margin ('spare').
    Nothing is rounded for appearance: if it does not fit, 'fits' is False
    and the reason is in 'why'.

    The secondary: layer q carries one turn of winding order[q], its
    SEC_PAR bundles side by side.  'smap' names the winding of each bundle
    place, 'bmap' which of its bundles sits there - the second turn of a
    winding lays them in the reverse order (the group is turned over on the
    way up), which leakage.sharing() weighs.
    """
    name = name or CHOSEN
    k = K_WIND if k is None else k
    order = SEC_ORDER if order is None else order
    M = MECH[name]
    rows = copper(V)
    Np, Ns = V['Np'], V['Ns']
    r_free = M.get('r_room', M['r_win_out']) - M['tube_od'] / 2.0
    why = []
    if 2 * Ns != SEC_LAYERS or sorted(order) != ['NS2'] * Ns + ['NS3'] * Ns:
        why.append('secondary order %s is not one turn a layer' % (order,))
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
    per = -(-Np // PRI_LAYERS)
    rA = [min(per, Np - q * per) for q in range(PRI_LAYERS)]
    hA = PRI_LAYERS * (dp * k + T_TAPE)
    hS = SEC_LAYERS * (ds * k + T_TAPE)
    hS_aux = hS + ((TIW_OD * k + T_TAPE) if n_aux else 0.0)
    if M.get('custom'):
        #  the former: thinnest flanges, the partition the rest of the K_WIND
        #  build; a tighter winding or a thinner partition leaves 'spare'
        flange = FLANGE_MIN
        wind_w = M['win_h'] - 2 * flange
        wA0 = per * PRI_PAR * dp * K_WIND
        wS0 = SEC_PAR * ds * K_WIND
        g_nom = wind_w - 2 * MARGIN_F - wA0 - wS0
        g = g_nom if g is None else g
        if g_nom < 0:
            why.append('no room for a partition: %.2f mm' % g_nom)
        k_ax = k
    else:
        #  catalogue former; a partition of PARTITION is added to it, and the
        #  pitch along the layer spreads the two sections over what is left
        flange = (M['flange_h'] - M['wind_w']) / 2.0
        wind_w = M['wind_w']
        g_nom = PARTITION if M.get('partition') else 0.0
        g = g_nom if g is None else g
        k_fill = (wind_w - 2 * MARGIN_F - g_nom) / (per * PRI_PAR * dp
                                                    + SEC_PAR * ds)
        if k_fill < K_WIND - 1e-9:
            why.append('axial: the sections at pitch %.2f are wider than the '
                       'room' % K_WIND)
        k_ax = max(k_fill, K_WIND) * k / K_WIND
    wA = per * PRI_PAR * dp * k_ax
    wS = SEC_PAR * ds * k_ax
    need = 2 * MARGIN_F + wA + g + wS
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
    if n_aux * TIW_OD * k > wS:
        why.append('NAUX wider than the secondary')
    smap = [[order[q]] * SEC_PAR for q in range(SEC_LAYERS)]
    bmap, turn_of, seen = [], [], {}
    for q in range(SEC_LAYERS):
        n = seen.get(order[q], 0)
        seen[order[q]] = n + 1
        turn_of.append(n + 1)
        b = list(range(1, SEC_PAR + 1))
        bmap.append(b[::-1] if n % 2 else b)
    return dict(
        name=name, M=M, Np=Np, Ns=Ns,
        ap=rows[0][3], asec=rows[1][3], d_litz=d_bare, d_pri=dp,
        n_strand=nstr, area_p=area_p, j_p=j_p,
        tiw_add=TIW_LITZ_ADD, d_sec=ds, n_strand_s=nstr_s, sec_par=SEC_PAR,
        area_s=area_s, j_s=j_s, order=tuple(order),
        sec_layers=SEC_LAYERS, smap=smap, bmap=bmap, turn_of=turn_of,
        layers_A=PRI_LAYERS, per_A=per, rows_A=rA, w_A=wA, h_A=hA,
        w_S=wS, h_S=hS, h_S_aux=hS_aux, n_aux=n_aux, tiw_od=TIW_OD,
        t_tape=T_TAPE, k=k, k_ax=k_ax, k_wind=K_WIND, sep=g,
        pri_par=PRI_PAR,
        spare=spare, margin=MARGIN_F, flange=flange, wind_w=wind_w,
        unused=spare,
        yA=(yA0, yA1), yS=(yS0, yS1),
        r_tube=M['tube_od'] / 2.0, r_free=r_free,
        fits=not why, why=why)


def report(V, name=None):
    """Print the fit arithmetic.  Run this before believing the drawing."""
    name = name or CHOSEN
    w = winding(V, name)
    M = w['M']
    out = [
        '%s   core %s   coil former %s' % (name, M['core'], M['former']),
        '  radial room %.2f mm  (flange or window %.2f - tube %.2f / 2), '
        'window height %.1f' % (w['r_free'], M.get('r_room', M['r_win_out']),
                                M['tube_od'], M['win_h']),
        '  winding pitch K_WIND %.2f x the bundle layer to layer, %.3f '
        'along the layer; margin tape %.2f mm, partition %.2f mm'
        % (w['k_wind'], w['k_ax'], MARGIN_F, w['sep']),
        '  NP1 %d T, %d TIW-Litz bundles a turn, %d x %.2f mm each, bundle '
        '%.2f + %.2f = %.2f mm, J %.2f A/mm2'
        % (w['Np'], w['pri_par'], w['n_strand'], D_STRAND, w['d_litz'],
           w['tiw_add'], w['d_pri'], w['j_p']),
        '      %d layers %s -> %5.2f mm axial, %.2f mm deep'
        % (w['layers_A'], w['rows_A'], w['w_A'], w['h_A']),
        '  NS2, NS3 %d T each, %d Litz bundles side by side a turn, '
        '%d x %.2f mm, d %.2f mm, J %.2f A/mm2'
        % (w['Ns'], w['sec_par'], w['n_strand_s'], D_STRAND,
           w['d_sec'], w['j_s']),
        '      %d layers %s -> %5.2f mm axial, %.2f mm deep, %.2f with NAUX'
        % (w['sec_layers'], list(w['order']), w['w_S'], w['h_S'],
           w['h_S_aux']),
        '  winding width %.2f mm, flanges %.2f mm, spare %.2f mm'
        % (w['wind_w'], w['flange'], w['spare']),
        '  VERDICT %s' % ('fits' if w['fits'] else
                          '** DOES NOT FIT: ' + '; '.join(w['why'])),
    ]
    return '\n'.join(out)
