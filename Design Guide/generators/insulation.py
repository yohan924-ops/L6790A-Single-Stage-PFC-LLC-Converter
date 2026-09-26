# -*- coding: utf-8 -*-
"""Safety insulation of the transformer - household AV equipment (a TV) sold
in the US, the EU, Japan, Korea and China.  2026-09-25, user request.

One construction has to pass everywhere, so every requirement is taken at
the strictest market:

  * the insulation grade from a Class II set: REINFORCED between everything
    mains-referenced (NP1, NAUX, the core) and the secondary (NS2, NS3).  A
    Class I set would need only basic; reinforced covers both.
  * the altitude from China: GB 4943.1-2022 "assumes a maximum altitude of
    5000 m unless otherwise specified", which multiplies every clearance by
    1.48.  The IEC text stops at 2000 m.
  * the working voltage at the top of the design range, 264 Vac, not the
    240 V a label would carry.

EVERY NUMBER HERE HAS A SOURCE in SOURCES and says which.  None of them is
read from the standard itself - the IEC and GB texts are not in this
repository - so they come from the manufacturers' seminars and from CB test
reports (the certifying bodies' own application of the tables).  Where two
sources could be read two ways, the stricter reading is taken.  What the
sources do NOT settle is listed in OPEN, and those go to the certifying body
and the transformer vendor, not into a guess.

    python insulation.py        the requirement table, the working-voltage
                                estimate and the geometry checks
"""
from math import pi, sin, sqrt, ceil

# ------------------------------------------------------------------ sources
SOURCES = {
    'PI': ('Power Integrations, "If Your Power Converter Is Not Safe, You May '
           'Have an Expensive Recall", PSMA IS293 (2020), slides 13-15',
           'https://psma.com/sites/default/files/uploads/node/6141/'
           'is293-if-your-power-converter-not-safe-you-may-have-expensive-'
           'recall.pdf'),
    'ATIS': ('M. Maytum, "IEC 62368-1 and Pluggable Mains Powered Equipment '
             'Surge Protection", ATIS PEG (2019), slides 13-16',
             'https://peg.atis.org/wp-content/uploads/2019/03/'
             'IEC62368-1_and_Pluggable_Mains_Powered_Equipment_Surge_'
             'Protection-MMaytum.pdf'),
    'TUV': ('TUV Rheinland CB test report 60431427 001, IEC 62368-1, Class II '
            'AV/ICT adapter 100-240 V, evaluated for 5000 m (Digi-Key)',
            'https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/'
            '2487/FWE050xBMWA050xB%20IEC62368%20Report%20(60431427%20001)'
            '%2020201222.pdf'),
    'UL': ('UL CB test report E135803-A6002-CB-1, IEC 62368-1, Advanced '
           'Energy GB130Q, evaluated for 5000 m',
           'https://www.advancedenergy.com/getmedia/cd966910-186e-4c1f-9e62-'
           'd3682b175225/gb130q_ite_cb_report.pdf'),
    'TI': ('Texas Instruments SLUP419, "Demystifying Clearance and Creepage '
           'Distance for High-Voltage End Equipment" (2024)',
           'https://www.ti.com/lit/pdf/slup419'),
    'GB': ('GB 4943.1-2022, English excerpt (ChineseStandard.net), foreword '
           'and clause 1',
           'https://www.chinesestandard.net/PDF-EN/'
           'GB4943.1-2022EN-P22P-H18474H-424252.pdf'),
    'TIW': ('Furukawa Electric, TEX-E safety approvals',
            'https://www.furukawaelectric.com/tex-e/en/safety/standard.html'),
}

# ------------------------------------------------------- what each one says
ALTITUDE_M = 5000
K_ALT = 1.48            # IEC 60664-1 Table A.2 at 5000 m               [PI]
V_TRANSIENT = 2500.0    # OVC II, mains 150..300 V, Table 12           [ATIS]
V_TEMP_OV = 2000.0      # temporary overvoltage, mains <= 250 V        [PI]
#  Clearance, reinforced, below 2000 m.
#   procedure 1, Table 10 at the temporary overvoltage 2000 V peak     [PI]
CL_TABLE10_R = 2.54
#   procedure 2, Table 14: reinforced insulation is taken at the next
#   withstand step, 4000 V [TUV table 5.4.2.3], and 4000 V reads 3.0 mm
#   [ATIS, basic column].  Both CB reports apply 4.5 mm at 5000 m, which is
#   3.0 x 1.48 rounded up [TUV, UL].
CL_TABLE14_R = 3.0
#  Creepage, BASIC, pollution degree 2, material group IIIa/IIIb, by rms
#  working voltage [PI]; reinforced is twice basic [TI].  The CB reports
#  apply exactly that: 5.0 mm at 250 V, 6.4 mm at 313 V [TUV].
CREEP_PD2_IIIB = [(250, 2.5), (320, 3.2), (400, 4.0), (500, 5.0),
                  (630, 6.3), (800, 8.0)]
DTI_REINFORCED = 0.4    # mm, solid insulation, reinforced             [TUV]
TAPE_LAYERS = 2         # thin sheet: each layer passes the reinforced test [TUV]
HIPOT_AC = 3000         # V rms, 60 s, reinforced type test (= 4242 V dc) [TUV]
HIPOT_DC = 4242
#  The TEX-E approvals: TUV Rheinland EN IEC 62368-1:2020+A11 and VDE
#  IEC 62368-1:2018 Annex J, 1000 V rms, 500 kHz, insulation Class B
#  (130 C).  The series is sold as reinforced-insulation wire; a Litz
#  version (TEX-ELZ) is on the same approvals.                        [TIW]
TIW_VRMS, TIW_FMAX, TIW_CLASS = 1000, 500e3, 'B (130 C)'

V_MAINS_DESIGN = 264.0  # Vac, top of the design range (l6790.design)


def round_up(x, step=0.1):
    """Distances are rounded UP to the next 0.1 mm [PI, slide 15]."""
    return ceil(x / step - 1e-9) * step


def creepage_basic(u_rms):
    """Table row at or above u_rms - no interpolation.  The standard allows
    it and one CB report uses it [UL]; the other does not [TUV].  Taking the
    row is the reading every certifier accepts."""
    for u, c in CREEP_PD2_IIIB:
        if u_rms <= u:
            return u, c
    raise ValueError('working voltage above the table: %g V' % u_rms)


# ------------------------------------------------- the working voltage
def working_voltage(R=None, vac=V_MAINS_DESIGN):
    """Primary winding to secondary, estimated from the design.

    Topology (Reference/Visio-LLC drawing.pdf): full bridge; NP1 runs from
    the leg-1 midpoint to C_r, and C_r to the leg-2 midpoint.  Below the
    morphing threshold both legs switch (FB); above it leg 2 holds its low
    side on and C_r carries half the bus as DC (HB).  The secondary is taken
    as earth and the mains neutral as earth, so the primary ground sits at
    0 in one half-cycle and at the line voltage in the other (bridge
    rectifier).  C_r's swing is the tank current peak over 2 pi f C_r per
    point of the line cycle (l6790.sweep).  Every point of the winding lies
    between its two terminals, and the rms of a straight mix of two
    waveforms is largest at one end, so the two ends are enough.

    An ESTIMATE: the standard asks for the measured value (the certifier
    measures it).  Returns (rms, peak) in volts, the larger terminal.
    """
    import bisect
    import l6790
    if R is None:
        import an_pdf
        R = an_pdf.R
    mode = 'HB' if sqrt(2) * vac > R['V_BIH'] else 'FB'
    veq = vac if mode == 'HB' else 2 * vac
    rows, _ = l6790.sweep(R, veq, 1.0)
    ok = [r for r in rows if r]
    ths = [r['th'] for r in ok]
    amp = [r['comp'] / (2 * pi * r['fsw'] * R['Cr']) for r in ok]

    def a_of(th):
        th = abs(th) % pi
        th = min(th, pi - th)
        i = min(max(bisect.bisect_left(ths, th), 0), len(ths) - 1)
        return amp[i]
    vpk = sqrt(2) * vac
    s = [0.0, 0.0]
    p = [0.0, 0.0]
    n = 0
    NL, NS = 360, 48
    for i in range(NL):
        th = 2 * pi * (i + 0.5) / NL
        vl = vpk * sin(th)
        vb, pg = abs(vl), min(0.0, vl)
        a = a_of(th)
        for k in range(NS):
            ph = 2 * pi * (k + 0.5) / NS
            s1 = vb if ph < pi else 0.0
            s2, dc = (vb - s1, 0.0) if mode == 'FB' else (0.0, vb / 2)
            v = (pg + s1, pg + s2 + dc + a * sin(ph - pi / 2))
            for j in (0, 1):
                s[j] += v[j] * v[j]
                p[j] = max(p[j], abs(v[j]))
            n += 1
    rms = [sqrt(x / n) for x in s]
    return max(rms), max(p), mode


# ------------------------------------------------------- the requirements
def requirements(R=None):
    u_rms, u_pk, mode = working_voltage(R)
    u_design = max(V_MAINS_DESIGN, u_rms)
    row, basic = creepage_basic(u_design)
    cl_2000 = max(CL_TABLE10_R, CL_TABLE14_R)
    return dict(
        u_rms=u_rms, u_pk=u_pk, mode=mode, u_design=u_design, row=row,
        creep_basic=basic, creep=2 * basic,
        cl_2000=cl_2000, clearance=round_up(cl_2000 * K_ALT),
        dti=DTI_REINFORCED, layers=TAPE_LAYERS,
        hipot_ac=HIPOT_AC, hipot_dc=HIPOT_DC)


REQ = None


def req():
    """The requirements, computed once (the sweep takes a moment)."""
    global REQ
    if REQ is None:
        REQ = requirements()
    return REQ


def separation_min():
    """What the separation between a primary and a secondary SECTION would
    have to be if the distance carried the reinforced insulation (creepage
    along the tube, clearance across the gap).  The winding of this note no
    longer uses that route - the triple-insulated primary carries it - but
    the number is what a side-by-side winding in plain wire must respect,
    and the note quotes it (Section 6.17).  cores.winding_v64() reads it."""
    r = req()
    return max(r['creep'], r['clearance'])


# ------------------------------------------------------- what carries what
def checks(V=None, name=None):
    """Every path between the primary circuit and the secondary circuit of
    the winding cores.winding() lays out, and what carries its reinforced
    insulation.  Returns rows of (path, carried by, requirement, status)
    and the winding; status is 'ok' where the drawing or the design shows
    it, 'open' where only the bobbin drawing, the wire vendor or the
    certifier can."""
    import cores
    if V is None:
        import an_pdf
        V = an_pdf.V
    r = req()
    w = cores.winding(V, name)
    B = cores.BOBBINS.get(w['name'])
    tiw = ('triple-insulated wire, rated %d V rms against a working voltage '
           'of %.0f V rms' % (TIW_VRMS, r['u_rms']))
    rows = [
        ('NP1 to NS2, NS3 and the core', 'the triple insulation of the '
         'NP1 Litz, one wire from pin to pin', 'reinforced: ' + tiw,
         'ok' if TIW_VRMS >= r['u_rms'] else 'FAIL'),
        ('NAUX to NS2, NS3 and the core', 'the triple insulation of NAUX, '
         'from pin to pin', 'reinforced: ' + tiw,
         'ok' if TIW_VRMS >= r['u_rms'] else 'FAIL'),
        ('the face where the two sections touch', 'the triple insulation '
         'of NP1 (nothing else is between them)', 'reinforced: ' + tiw,
         'ok' if TIW_VRMS >= r['u_rms'] else 'FAIL'),
        ('NS2, NS3 to the core', 'the same side of the barrier: the core is '
         'secondary here', 'functional', 'ok'),
    ]
    if B and B.get('rows_apart'):
        pin = 0.8 if 'square 0.8' in B.get('pin', '') else 1.0
        gap_pins = B['rows_apart'] - pin
        rows.append(('primary pin row to secondary pin row, across the '
                     'coil former', '%.1f mm between the rows (%.2f apart, '
                     'less one pin)' % (gap_pins, B['rows_apart']),
                     'creepage %.1f mm, clearance %.1f mm'
                     % (r['creep'], r['clearance']),
                     'ok' if gap_pins >= separation_min() else 'FAIL'))
    rows.append(('primary pins and the stripped TIW ends to the core yoke '
                 'and to secondary leads', 'the coil former and the lead '
                 'dress, not this drawing',
                 'creepage %.1f mm, clearance %.1f mm, or sleeving qualified '
                 'as reinforced' % (r['creep'], r['clearance']), 'open'))
    fsu = None
    try:
        import an_pdf
        fsu = an_pdf.SH['f.SU'] * 1e3
    except Exception:
        fsu = None
    rows.append(('the TIW approval against the frequencies it sees',
                 'approved to %d kHz' % (TIW_FMAX / 1e3),
                 'every switching frequency, start-up included (%s)'
                 % ('%.0f kHz' % (fsu / 1e3) if fsu else 'f_SU'),
                 'open' if fsu and fsu > TIW_FMAX else 'ok'))
    return rows, w


OPEN = [
    'The working voltage is an estimate (secondary and neutral taken as '
    'earth, C_r swing from the sweep); the certifier measures it.  The '
    'creepage row taken covers up to %d V rms.',
    'Primary pins and the stripped ends of the TIW against the core yoke '
    '(the core is secondary here) and against secondary leads: set by the '
    'coil former and the lead dress, not by this drawing.  Reinforced '
    'distances, or sleeving qualified as reinforced insulation.',
    'Triple-insulated LITZ for NP1, one bundle: the approval quoted is for '
    'the series; the size, its outer diameter (0.2 mm over the bare bundle '
    'assumed) and its approval come from the wire vendor.',
    'Material group IIIb is assumed for the bobbin and the board; a bobbin '
    'with a higher CTI allows less creepage, not more.',
    'The electric strength test voltage is the value the TUV report applies '
    'to the same case under IEC 62368-1:2014; confirm it under the edition '
    'the certificate will cite, and the routine (production) test voltage.',
    'Clearance above 30 kHz (the tables for high-frequency working voltage) '
    'is not in these sources; the UL report applied the ordinary values at '
    '133 kHz and 588 V peak.',
    'The TIW approval quoted is for 500 kHz; the start-up frequency f.SU is '
    'above that for the first milliseconds of safe start.  Ask the wire '
    'vendor.  The approval is Class B: the winding hot spot stays under '
    '130 C, which the thermal measurement has to show.',
    'L_short is an estimate (leakage.py, a 2-D field solution) at an '
    'assumed winding pitch; the first samples measure it.',
    'The coil former of E 60/22/16 is custom: its tube, flanges, pins and '
    'material are this note\'s specification to the bobbin maker, and the '
    'distances around the pins are checked on its drawing.',
]


def report():
    r = req()
    lines = ['REQUIREMENTS (reinforced, PD2, OVC II, material group IIIb, '
             '%d m)' % ALTITUDE_M,
             '  working voltage estimate  %.0f V rms, %.0f V peak (%s, %g Vac)'
             % (r['u_rms'], r['u_pk'], r['mode'], V_MAINS_DESIGN),
             '  creepage   2 x %.1f = %.1f mm   (row %d V covers max(%g V '
             'mains, estimate))' % (r['creep_basic'], r['creep'], r['row'],
                                    V_MAINS_DESIGN),
             '  clearance  %.2f x %.2f = %.2f -> %.1f mm' %
             (r['cl_2000'], K_ALT, r['cl_2000'] * K_ALT, r['clearance']),
             '  solid      DTI >= %.1f mm, or >= %d tape layers each passing '
             'the reinforced test' % (r['dti'], r['layers']),
             '  hipot      %d V ac 60 s (%d V dc), NP1+NAUX to NS2+NS3+core'
             % (r['hipot_ac'], r['hipot_dc']),
             '  a plain-wire side-by-side winding would need a separation of %.2f mm (not used: the primary is TIW)' % separation_min(), '']
    rows, w = checks()
    lines.append('WHAT CARRIES EACH PATH on %s' % w['name'])
    for path, by, need, st in rows:
        lines.append('  %-5s %s\n        by   %s\n        need %s'
                     % (st, path, by, need))
    return '\n'.join(lines)


if __name__ == '__main__':
    print(report())
