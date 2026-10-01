# -*- coding: utf-8 -*-
"""Ferrite cores, as printed in the manufacturer's catalogue.

Nothing in CORES or MECH is remembered or estimated: every number is
copied from the TDK document named beside it, or measured from that
document's own vector drawing where no dimension is printed (said so per
value), and everything else here is arithmetic on those numbers and on
the design.  One core is carried:

    PQ 50/50     core B65981A and coil former B65982E, TDK October 2022 -
                 the single transformer of this note's design example
                 (CHOSEN)

Window symbols follow the datasheets: A_N is the winding cross-section of
the coil former and l_N its mean turn length.
"""
from math import pi

MU0 = 4e-7 * pi

CORES = {
    #  PQ 50/50 - TDK B65981A core, 10/2022 data sheet p. 2: l_e 113, A_e 332,
    #  A_min 314, V_e 37630, 190 g a set; ungapped A_L 6700 nH (N97) and
    #  P_V < 3.50 W a set at 100 mT, 100 kHz, 100 C (N97).  No A_L-gap
    #  relation is printed (gapped cores on request).  Coil former B65982E,
    #  p. 3: one section, A_N 340 mm2, l_N 100.5 mm, 12 pins.  Chosen
    #  2026-09-30: the single 15 : 2 transformer of the design.
    'PQ 50/50': dict(
        core='B65981A', former='B65982E',
        le=113.0, Ae=332.0, Amin=314.0, Ve=37630.0, mass=190.0,
        AN=340.0, lN=100.5,
        AL_ungapped=6700.0, material='TDK N97', vendor='TDK',
        P_core_max=(3.50, 100.0, 100.0, 100.0)),   # W at kHz, mT, C
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
#  Everything in MECH is read off the datasheet dimensional drawings.
#  Values marked "scaled" carry no dimension label on the drawing.  They
#  were measured from the PDF's own vector geometry, not from a picture:
#  the drawing's line coordinates were read out and a labelled dimension
#  on the same view fixed the scale.
MECH = {
    #  PQ 50/50, TDK B65981A core (10/2022, p. 2): 50 +-0.7 wide over the
    #  outer legs, 50 +0.2/-0.3 high as a set, window 36.1 +-0.3 high,
    #  centre leg diameter 20 +-0.35, depth 32 +-0.5, 44 +-0.7 the diameter
    #  of the arc that forms the inner face of each outer leg (the window's
    #  outer wall), 31.5 min between the tips of the two legs.  Read from
    #  the PDF's vectors (scale from the 20 mm leg): the section's window
    #  runs out to 22.0 mm from the centre line (the line at 16.0 mm inside
    #  it is the tip of the leg seen behind the section plane, drawn over
    #  the window), and the back plate between the legs and the post is a
    #  bow tie, not a rectangle - its edge runs from (4.80, 11.21) to
    #  (16.02, 15.18) mm, the leg's arc reaches |y| = 14.94 mm, and from
    #  its inner end a short step runs to the post at `neck` (3.50, 9.33).
    #  The 04/13 databook drawing (data/TDK_B65981A_core.pdf, FPK0457-U)
    #  gives the same outline within 0.1 mm: (16.14, 15.30) - (5.17, 11.30),
    #  a fillet, then (3.52, 9.41).
    #  Coil former B65982E (p. 3): tube 23.2 +-0.2 over a 20.8 +-0.2 bore,
    #  30.4 +-0.3 between the flanges at the tube, 35.2 +-0.3 over them,
    #  12 pins of 1.2 mm in two rows 45.72 +-0.3 apart, 7.62 +-0.2 between
    #  neighbours of a group of three and 12.7 +-0.2 between the groups,
    #  pins 1, 6, 7 and 12 numbered on the drawing and pin 1 marked.  Its
    #  flanges taper and are round towards the legs; their rim is not
    #  dimensioned - scaled, 21.3 to 21.6 mm from the axis (two scales from
    #  the same view disagree by 1.5 %).  The winding width grows to about
    #  31.7 mm at the rim (scaled).  The catalogue former has one section;
    #  the partition is this note's addition (PARTITION).
    'PQ 50/50': dict(
        core='B65981A', former='B65982E', partition=True, shape='PQ',
        W=50.0, H=50.0, d_centre=20.0, win_h=36.1, r_win_out=22.0,
        r_win_min=21.65, plan_w=50.0, plan_d=32.0, plan_d_max=32.5,
        wing=((4.80, 11.21), (16.02, 15.18)), neck=(3.50, 9.33),
        leg_y=14.94,
        r_rim=(21.3, 21.6),
        tube_od=23.2, tube_max=23.4, bore=20.8, wind_w=30.4,
        flange_h=35.2, pitch_a=7.62, pitch_b=12.70, pins=12, rows=45.72),
}
YOKE_SHARE = 0.5    # how much of the 'yoke' zone of a turn (under the back
                    # plate, no outer leg beside it) counts as in the core -
                    # between 0 and 1 by construction, 0.5 ASSUMED; leakage
                    # is given at 0 and 1 as well


def zones(name, rho):
    """-> (leg, yoke, open) lengths [mm] of a turn at radius rho [mm].

    'leg': an outer leg beside it (the arc reaches |y| = leg_y), 'yoke':
    under the back plate but with no outer leg, 'open': outside the core.
    PQ cores only; the plate outline is MECH['wing']."""
    import numpy as np
    M = MECH[name]
    (x0, y0), (x1, y1) = M['wing']
    th = (np.arange(4000) + 0.5) * (pi / 2) / 4000
    x, y = rho * np.cos(th), rho * np.sin(th)
    edge = y0 + (y1 - y0) / (x1 - x0) * (x - x0)
    under = np.where(x >= x1, y <= M['plan_d'] / 2.0, y <= edge)
    leg = np.sin(th) <= M['leg_y'] / M['r_win_out']
    dl = rho * (pi / 2) / 4000 * 4
    return (float(dl * np.sum(leg & under)), float(dl * np.sum(~leg & under)),
            float(dl * np.sum(~under)))


def zone_pct(name, rho):
    """-> zones() as whole per cents that add up to 100 (largest remainder),
    so a figure and the text that quote them agree and sum."""
    z = zones(name, rho)
    t = sum(z)
    raw = [100.0 * v / t for v in z]
    out = [int(v) for v in raw]
    for i in sorted(range(3), key=lambda i: raw[i] - out[i],
                    reverse=True)[:100 - sum(out)]:
        out[i] += 1
    return tuple(out)


def turn(name, rho=None):
    """-> (mean turn l_N [mm], share of it inside the core).

    Round leg: the datasheet's l_N.  The share: on a PQ core, the zones()
    split at the mean radius of the winding (rho, or the middle of the
    radial room), the 'yoke' zone counted at YOKE_SHARE; otherwise the two
    arcs of core depth over the circumference at mid-winding."""
    M = MECH[name]
    room = M['r_win_out'] - M['tube_od'] / 2.0
    r_mean = rho if rho is not None else M['tube_od'] / 2.0 + room / 2.0
    if M.get('shape') == 'PQ':
        l, yk, o = zones(name, r_mean)
        return CORES[name]['lN'], (l + YOKE_SHARE * yk) / (l + yk + o)
    return CORES[name]['lN'], min(1.0, 2 * M['plan_d'] / (2 * pi * r_mean))


# ===================================================================
#  The core this note builds on, and its coil-former terminals
# ===================================================================
#  CHOSEN names the core the design example is drawn and specified on.
#  Everything downstream - the section figure, the pin figure, the tables
#  of the note and the vendor specification - reads it from here.
#
#  PQ 50/50 (TDK B65981A + catalogue former B65982E, 12 pins), chosen
#  2026-09-30.  User: a catalogue coil former with its data, no parallel
#  bundles and no turning over, wire sized by the current in round sizes,
#  nothing left empty, a partition of ordinary thickness, no external
#  inductor.  Of the data-backed formers only this one takes a 15 : 2
#  section winding that way; its leakage IS the tank's L_r.
#  HISTORY.md 2026-09-30.
CHOSEN = 'PQ 50/50'

#  Terminals, per coil former.  'xy' is pin number -> (x, y) in mm in the
#  datasheet's numbered view (for B65982E the bottom view, below); 'map' is winding -> (start pins, finish pins);
#  'plan' is the outline drawn under the pins.  One conductor to a pin.
#
#  PQ 50/50 (B65982E, databook 04/13 p. 287, drawing FPK0433-H): twelve
#  pins, six per row in two groups of three, 7.62 within a group, 12.7
#  between the groups, rows 45.72 apart.  The numbered view is the BOTTOM
#  view, from the pin side: it is the one that shows the pin ends, placed
#  above the front view (first-angle projection); the view below the front
#  view, from the winding side, shows no pins (bobbin_outline.py).  In it
#  the drawing prints 1, 6, 7 and 12 and marks pin 1 with the chamfered
#  corner (bottom left): 1 to 6 up the left row, 7 to 12 down the right.
#  The numbers between are counted.  So these x, y are AS SEEN FROM BELOW;
#  from the component side of the board x changes sign.
#
#  Assignment: the primary-referenced windings (NP1 and the VCC/ZCD
#  auxiliary NAUX) share one row and the two secondaries the other, so the
#  isolation distance is the whole bobbin.  "Start" is the end the polarity
#  dot marks, and NS2 and NS3 are wound in the same sense so that NS2's
#  finish and NS3's start make the centre tap - joined on the board, each
#  on its own pin.  Every winding is one conductor, one pin an end.
_PQ50_XY = {}
for _i, _y in enumerate((-21.59, -13.97, -6.35, 6.35, 13.97, 21.59)):
    _PQ50_XY[1 + _i] = (-22.86, _y)           # pin-1 row, upwards
    _PQ50_XY[12 - _i] = (22.86, _y)           # other row, downwards
BOBBINS = {
    'PQ 50/50': dict(
        former='B65982E', pins=12, pin='round 1.2 mm', xy=_PQ50_XY,
        map={'NP1': ((1,), (3,)), 'NAUX': ((4,), (6,)),
             'NS2': ((7,), (9,)), 'NS3': ((10,), (12,))},
        rows=('pin-1 row 1-6', 'other row 7-12'),
        #  former 51.6 x 51 (labelled); the coil drawn schematically
        #  inside the pin rows (34.4 between the pin blocks, labelled)
        plan=dict(w=51.6, h=51.0, coil_w=29.0, coil_h=43.0,
                  mark=(-25.0, -24.0)),
        pitch=7.62, pitch_b=12.70, rows_apart=45.72),
}
BOBBIN = BOBBINS[CHOSEN]
PIN_XY = BOBBIN['xy']
PINMAP = BOBBIN['map']
CENTRE_TAP = tuple(sorted(set(PINMAP['NS2'][1] + PINMAP['NS3'][0])))
PIN_NOTE = ('Pin numbers as the data sheet gives them in its view from '
            'below, the pin side: pin 1 at the chamfered corner, 1 to 6 in '
            'one row and 7 to 12 in the other, 6 facing 7 and 1 facing 12. '
            'The data sheet prints 1, 6, 7 and 12; the pins between are '
            'counted. Seen from the component side of the board, left and '
            'right are exchanged.')
PIN_NOTE_KR = ('핀 번호는 데이터시트의 밑면도(핀 쪽에서 본 그림) 그대로다: 모따기한 '
               '모서리가 핀 1, 한 줄에 1–6, 다른 줄에 7–12, 6 과 7 · 1 과 12 가 '
               '마주 본다. 데이터시트는 1, 6, 7, 12 만 적고 그 사이는 센 것이다. '
               'PCB 부품면에서 보면 좌우가 바뀐다.')


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
#  The WINDING is a section winding: the catalogue former gets one
#  partition, and each winding is laid in plain layers - one conductor a
#  turn, turns side by side, one winding to a layer, nothing turned over,
#  a wrap of tape over every layer:
#
#      flange | NP1, 3 layers of 5 T | PARTITION | NS2 2 T | NS3 2 T | NAUX | flange
#                                                  (layers, from the tube out)
#
#  The wire sizes are the user's round figures (2026-09-30), checked
#  against the current, and the build is checked against the radial room;
#  along the layer the pitch k_ax spreads the two sections over the width
#  the partition leaves, so nothing in the former is empty.
TIW_LITZ_ADD = 0.2  # mm, triple insulation over the Litz bundle, on the
                    # diameter - assumed, the wire vendor's datasheet decides
D_PRI = 2.9         # mm, NP1 over its triple insulation (round figure,
                    # user 2026-09-30)
D_SEC = 4.0         # mm, NS2 / NS3 Litz bundle (round figure, same)
PRI_LAYERS = 3      # NP1, 15 T as 5 + 5 + 5
PRI_PAR = 1         # one conductor a turn
SEC_PAR = 1         # one conductor a turn
SEC_PER = 2         # secondary turns side by side in a layer
SEC_LAYERS = 2      # one winding a layer: NS2, then NS3
SEC_ORDER = ('NS2', 'NS3')
                    # layer by layer from the tube
K_WIND = 1.10       # winding pitch over bundle diameter, layer to layer:
                    # a real winding is not packed tight (user, 2026-09-25:
                    # "leave for the small gaps").  ASSUMED; the first
                    # sample's measured build replaces it.
T_TAPE = 0.05       # mm, one wrap of layer tape over every winding layer
                    # and over NAUX - ASSUMED thickness; functional only,
                    # the reinforced insulation is in the wire
MARGIN_F = 0.0      # mm, margin tape at each flange - none (user,
                    # 2026-09-26: nothing left empty; the insulation is in
                    # the wire)
PARTITION = 3.0     # mm, the partition added to the one-section catalogue
                    # former (user, 2026-09-30: an ordinary thickness);
                    # ASSUMED mouldable - the bobbin maker decides


def winding(V, name=None, g=None, k=None, order=None):
    """The section winding laid out along the former, in millimetres.

        flange | NP1 | partition | NS2 layer, NS3 layer, NAUX | flange

    Axial positions run from the inside of the primary flange (y = 0) to
    the other flange (y = wind_w); radial heights from the top of the tube.
    The wire is D_PRI / D_SEC; layers are stacked at pitch k (K_WIND if
    None; k = 1.0: packed tight) with a wrap of tape each, and along the
    layer the pitch k_ax spreads the two sections over the width the
    partition g (PARTITION if None) leaves.  Nothing is rounded for
    appearance: if it does not fit, 'fits' is False and the reason is in
    'why'.

    The secondary: layer q carries SEC_PER turns of winding order[q], side
    by side.  'smap' names the winding at each place, 'bmap' which of its
    turns sits there, 'turn_of' is kept for the drawing.
    """
    name = name or CHOSEN
    k = K_WIND if k is None else k
    order = SEC_ORDER if order is None else order
    M = MECH[name]
    rows = copper(V)
    Np, Ns = V['Np'], V['Ns']
    r_free = M['r_win_out'] - M['tube_od'] / 2.0
    why = []
    if SEC_LAYERS * SEC_PER != 2 * Ns or sorted(order) != ['NS2', 'NS3']:
        why.append('secondary order %s is not one winding a layer' % (order,))
    dp, ds = D_PRI, D_SEC
    d_bare = dp - TIW_LITZ_ADD
    area_p = pi * K_LITZ * d_bare ** 2 / 4.0          # copper, one bundle
    nstr = int(area_p / (pi * D_STRAND ** 2 / 4.0) + 0.9999)
    area_s = pi * K_LITZ * ds ** 2 / 4.0
    nstr_s = int(area_s / (pi * D_STRAND ** 2 / 4.0) + 0.9999)
    j_p = rows[0][2] / (PRI_PAR * area_p)
    j_s = rows[1][2] / (SEC_PAR * area_s)
    n_aux = int(V.get('Naux', 0))
    per = -(-Np // PRI_LAYERS)
    rA = [min(per, Np - q * per) for q in range(PRI_LAYERS)]
    hA = PRI_LAYERS * (dp * k + T_TAPE)
    hS = SEC_LAYERS * (ds * k + T_TAPE)
    hS_aux = hS + ((TIW_OD * k + T_TAPE) if n_aux else 0.0)
    flange = (M['flange_h'] - M['wind_w']) / 2.0
    wind_w = M['wind_w']
    g = PARTITION if g is None else g
    k_ax = (wind_w - 2 * MARGIN_F - g) / (per * PRI_PAR * dp + SEC_PER * ds)
    if k_ax < 1.0:
        why.append('axial: the sections are wider than the room')
    wA = per * PRI_PAR * dp * k_ax
    wS = SEC_PER * ds * k_ax
    need = 2 * MARGIN_F + wA + g + wS
    spare = wind_w - need
    yA0 = MARGIN_F
    yA1 = yA0 + wA
    yS0 = yA1 + g
    yS1 = yS0 + wS
    #  the radial room at the tolerance limits that make it smallest: the
    #  leg arc at its least, the tube at its most
    room_min = M.get('r_win_min', M['r_win_out']) - M.get('tube_max',
                                                           M['tube_od']) / 2.0
    build = max(hA, hS_aux)
    if build > room_min + 1e-9:
        why.append('%.2f mm deep, %.2f of room at the tolerance limits'
                   % (build, room_min))
    if n_aux * TIW_OD * k > wS:
        why.append('NAUX wider than the secondary')
    smap = [[order[q]] * SEC_PER for q in range(SEC_LAYERS)]
    bmap = [list(range(1, SEC_PER + 1)) for _ in range(SEC_LAYERS)]
    turn_of = [1] * SEC_LAYERS
    return dict(
        name=name, M=M, Np=Np, Ns=Ns,
        ap=rows[0][3], asec=rows[1][3], d_litz=d_bare, d_pri=dp,
        n_strand=nstr, area_p=area_p, j_p=j_p,
        tiw_add=TIW_LITZ_ADD, d_sec=ds, n_strand_s=nstr_s, sec_par=SEC_PAR,
        sec_per=SEC_PER, area_s=area_s, j_s=j_s, order=tuple(order),
        sec_layers=SEC_LAYERS, smap=smap, bmap=bmap, turn_of=turn_of,
        layers_A=PRI_LAYERS, per_A=per, rows_A=rA, w_A=wA, h_A=hA,
        w_S=wS, h_S=hS, h_S_aux=hS_aux, n_aux=n_aux, tiw_od=TIW_OD,
        t_tape=T_TAPE, k=k, k_ax=k_ax, k_wind=K_WIND, sep=g,
        pri_par=PRI_PAR,
        spare=spare, margin=MARGIN_F, flange=flange, wind_w=wind_w,
        unused=spare, build=build, room_min=room_min,
        clear_min=room_min - build, clear_nom=r_free - build,
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
        '  radial room %.2f mm nominal (window %.2f - tube %.2f / 2), %.2f at '
        'the tolerance limits; window height %.1f'
        % (w['r_free'], M['r_win_out'], M['tube_od'], w['room_min'],
           M['win_h']),
        '  layer pitch K_WIND %.2f x the bundle, %.3f along the layer; '
        'partition %.2f mm' % (w['k_wind'], w['k_ax'], w['sep']),
        '  NP1 %d T, TIW-Litz %d x %.2f mm, bundle %.2f + %.2f = %.2f mm, '
        'J %.2f A/mm2' % (w['Np'], w['n_strand'], D_STRAND, w['d_litz'],
                          w['tiw_add'], w['d_pri'], w['j_p']),
        '      %d layers %s -> %5.2f mm axial, %.2f mm deep'
        % (w['layers_A'], w['rows_A'], w['w_A'], w['h_A']),
        '  NS2, NS3 %d T each, Litz %d x %.2f mm, d %.2f mm, J %.2f A/mm2'
        % (w['Ns'], w['n_strand_s'], D_STRAND, w['d_sec'], w['j_s']),
        '      %d layers %s of %d T -> %5.2f mm axial, %.2f mm deep, %.2f '
        'with NAUX' % (w['sec_layers'], list(w['order']), w['sec_per'],
                       w['w_S'], w['h_S'], w['h_S_aux']),
        '  clearance to the leg arc %.2f mm nominal, %.2f at the limits'
        % (w['clear_nom'], w['clear_min']),
        '  winding width %.2f mm, flanges %.2f mm, spare %.2f mm'
        % (w['wind_w'], w['flange'], w['spare']),
        '  VERDICT %s' % ('fits' if w['fits'] else
                          '** DOES NOT FIT: ' + '; '.join(w['why'])),
    ]
    return '\n'.join(out)
