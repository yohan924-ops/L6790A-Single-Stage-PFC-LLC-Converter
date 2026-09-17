# -*- coding: utf-8 -*-
"""Build the application note PDF.

Layout follows the Infineon design-note convention the user pointed at: a
cover with a corner tag, a legal page, a dotted table of contents, then body
pages carrying a running head and a coloured document tag, numbered equations
set to the right margin, and captioned figures. The BRANDING is ours, not
Infineon's - this is an internal engineering document and must not read as
somebody else's publication.

Every number in the text comes out of VAL, which is built from l6790.py and
the SMath sheet. Nothing here is typed by hand, so the note cannot drift away
from the design the way a transcribed value would.

    python an_pdf.py            -> Design Guide/AN_L6790A_..._v1.1.pdf
    python an_pdf.py --figs     -> re-render the plain figures first
"""
import hashlib
import os
import subprocess
import sys
from math import pi, sqrt

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                                  # noqa: E402

from reportlab.lib import colors                                 # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_RIGHT  # noqa: E402
from reportlab.lib.pagesizes import A4                           # noqa: E402
from reportlab.lib.styles import ParagraphStyle                  # noqa: E402
from reportlab.lib.units import mm                               # noqa: E402
from reportlab.platypus import (BaseDocTemplate, Flowable, Frame,          # noqa: E402
                                Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents   # noqa: E402

import l6790                                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
GUIDE = os.path.normpath(os.path.join(HERE, '..'))
FIGS = os.path.join(GUIDE, 'figures', 'an')
EQD = os.path.join(HERE, '.eqcache')
OUT = os.path.join(GUIDE,
                   'AN_L6790A_SingleStage_PF_LLC_ApplicationNote_v1.1.pdf')

DOCID = ['Application Note AN-SS-L6790A-01', 'V1.1  September 2026']
TITLE = 'Single-Stage PF LLC Converter Design'
HEADSIZE = 14.5                 # 머리글 크기 - 한글 제목은 줄여야 상자를 안 문다
FIGWORD, TBLWORD = 'Figure', 'Table'
COVER = {
    'title': ['Single-Stage PF LLC', 'Converter Design'],
    'sub': 'with the STMicroelectronics L6790A',
    'boxhead': 'Worked design',
    'box': ['90 to 264 Vac,  47 to 63 Hz',
            '25 V / 26.3 A = 657.5 W'],
    'foot': [],
}

NAVY = colors.HexColor('#03234B')
BLUE = colors.HexColor('#0B4F8F')
GREY = colors.HexColor('#585862')
LT = colors.HexColor('#E4E6EA')
MAG = colors.HexColor('#B4005F')

PW, PH = A4
LM, RM = 62, 62
TM, BM = 108, 62
CW = PW - LM - RM


def _sheet_early(k):
    global _SHC
    try:
        _SHC
    except NameError:
        _SHC = _sheet()
    return _SHC[k]


# WHICH design point the note is worked on.  The canonical sheet is a
# different variant, so name the variant here rather than following it - the
# workbook and the vendor specification are kept per variant and the note is
# not allowed to drift between them.
AN_VARIANT = os.environ.get('AN_VARIANT', '7p5to1')
AN_SM = os.path.join(GUIDE, '..', 'Smath', 'variants',
                     'L6790A_%s.sm' % AN_VARIANT)


def _sheet():
    """the values the sheet owns - IC network, loop, verdicts"""
    import snapshot
    if not os.path.exists(AN_SM):
        raise SystemExit('변형 시트가 없다: %s   먼저 만들 것:  '
                         'set L6790_VARIANT=%s && python build_l6790_smath.py'
                         % (os.path.normpath(AN_SM), AN_VARIANT))
    v, _ = snapshot.read_sheet(AN_SM)
    return {k: a for k, (a, _u) in v.items()}



# ============================================================ design values
# The worked design must be the ONE the sheet holds. This used to sit on the
# 7.5:1 point while SH came from the 9:1 sheet, so the note printed n = 6.02
# next to n.T = 9 - two different transformers in the same table.
R = l6790.design(Vout=25., Pout=657.5, Vo_min=19., Thold=12e-3, dv_out=0.05,
                 fl_min=47., Nrect=1,
                 Cr_sel=_sheet_early('C.r') * 1e-9,
                 Lr_sel=_sheet_early('L.r') * 1e-6,
                 Lm_sel=_sheet_early('L.m') * 1e-6,
                 n_sel=_sheet_early('n'), c_HB=800e-12, tD=220e-9)
_, SA = l6790.sweep(R, R['Vin_min'], 1.0)          # HB corner, full load
_, SB = l6790.sweep(R, 332.34, 1.0)                # FB corner, full load


def _fsw_peaks():
    """peak f.sw at each plotted line condition, and which run above f.r

    Whether the converter lives above or below series resonance is not a
    separate choice - it falls out of the turns ratio, because a larger n
    demands more gain and more gain means further below f.r. Computed, not
    asserted.
    """
    fr = R['fr'] / 1e3
    out = []
    for nm, veq in (('minimum line', 2 * 90.0), ('tank minimum', R['Vin_min']),
                    ('110 Vac', 220.0), ('nominal', 225.0),
                    ('230 Vac', 230.0), ('maximum line', 264.0),
                    ('FB threshold', 332.34)):
        _q, S = l6790.sweep(R, veq, 1.0)
        pk = S['fsw_max'] / 1e3
        out.append((nm, veq, pk, pk > fr))
    return out


def _noload(R):
    """the no-load corner frequency in kHz, or None when there is no solution"""
    d = R['MFBmax'] * (1 + R['lam_a']) - 1
    if d <= 0:
        return None
    return (R['fr'] / 1e3) * (R['MFBmax'] * R['lam_a'] / d) ** 0.5


SH = _sheet()
V = dict(
    Vout=25.0, Iout=26.3, Pout=657.5, Vomin=19.0, Thold=12.0, dv=5.0,
    Vacmin=90.0, Vacmax=264.0, flmin=47.0, flmax=63.0, tD=220.0,
    Pin=R['Pin'], eta=R['eta_tot'] * 100, etaHB=98.0,
    # the four morphing corners, all from the two datasheet thresholds -
    # typed as constants these drift: 346.52 stood here against a true
    # 2*245/sqrt(2) = 346.48
    Veqlo=R['Vin_min'], Veqhi=2 * 235 / sqrt(2),
    Veqlo2=235 / sqrt(2), Veqhi2=2 * 245 / sqrt(2),
    n=R['n'], nT=SH['n.T'], Vrefl=R['n'] * R['Vo_eff'],
    Rac=R['Rac'], Qpk=R['Qpk'], lam=R['lam_a'], m=1 + 1 / R['lam_a'],
    Z0=SH['Z.0'], Z0s=SH['Z.0s'], QZVS=SH['Q.ZVS'],
    Crc=SH['C.r_calc'], Cr=SH['C.r'], Lrc=SH['L.r_calc'], Lr=SH['L.r'],
    Lmc=SH['L.m_calc'], Lm=SH['L.m'],
    fr=R['fr'] / 1e3, fo=R['fo'] / 1e3,
    fswA=SA['fsw_max'] / 1e3, fswB=SB['fsw_max'] / 1e3,
    Tzc=SA['Tzc_min'] * 1e9, kZVS=SH['k.ZVS'],
    Isec=SA['Isec_pk'], Itr=SA['Itr_pk'], ILm=SA['ILm_pk'],
    Icomp=SA['comp_pk'], Iprims=SH['I.pri_rms'], Iprilc=SA['Ipri_lc'],
    Idio=SH['I.diode_lc'], ICout=SH['I.Cout_rms'],
    Cout=SH['C.out'], Cout1=470.0, nC=SH['n.C'], dVo=SH['ΔV.out'],
    dVopc=SH['ΔV.out_pc'], thold=SH['t.hold_act'], RN=SH['R.Nact'],
    Icout1=SH['I.Cout_each'], Ccer=SH['C.ceramic'],
    Crip=SH['C.ripple'], Chold=SH['C.hold_req'],
    VDS=SH['V.DS_pri'], VDSs=SH['V.DS_sec_rec'],
    Rdreq=SH['R.dson_req_dev_p'], Rdp=45.0, Rdpk=1.8, Rds=3.7, Rdsk=1.9,
    nSR=2, npar=1,
    RT=SH['R.T'], CT=SH['C.T'], fMin=SH['f.Min'], fMax=SH['f.Max'],
    RCS=SH['R.CS'], RCS1=SH['R.CS_single'], RCFG=30.0, VBO=SH['V.BO_act'],
    RBM=SH['R.BM_sel'], RZH=SH['R.ZCD_H_sel'], RZL=SH['R.ZCD_L_sel'],
    OVP1=SH['V.OVP1_act'], OVP2=SH['V.OVP2_act'], Cin=SH['C.in_sel'],
    fcross=SH['f.cross'], PM=SH['Φ.act'], D3=SH['D.3rd_act'],
    Kv=SH['K.v'], EAo=SH['EA.o'], fMB=SH['f.MB'], Go=SH['G.o'],
    fz=SH['f.zero'], fp=SH['f.pole'], fpx=SH['f.pxi'], f180=SH['f.180'],
    GM=SH['GM'], dVFBBM=SH['ΔV.FBBM'], dRBM=SH['ΔR.BM'],
    CFo=82.0, CF=560.0, RF=47.0, Cfx=1.55, RP=1.3, RB=6.2,
    Np=int(SH['N.p']), Ns=int(SH['N.s']), nser=int(SH['N.x']),
    AL=SH['A.L'], Bpk=SH['B.pk'],
    Lmu=SH['L.mu'], LL1=SH['L.L1'], LL2=SH['L.L2'] / 1e3,
    Lopen=SH['L.open'], Lshort=SH['L.short'],
    Lopenx=SH['L.open'] / SH['N.x'], Lshortx=SH['L.r'] / SH['N.x'],
    Aereq=SH['A.e_req_mm'], kAe=SH['k.Ae'],
    Aemm=SH['k.Ae'] * SH['A.e_req_mm'],
    Isateq=SH['I.sat_eq'], Isatspec=SH['I.sat_spec'],
    Isecx=SH['I.diode_lc'] / SH['N.x'], Isecpkx=SH['I.sec_pk'] / SH['N.x'],
    MFBmax=R['MFBmax'], Minf=1 / (1 + R['lam_a']),
    # no-load corner: real only when the requirement is ABOVE the asymptote
    fnl=_noload(R), NpSet=int(round(SH['n.T_act'] * SH['N.s'])),
    # how much the open-circuit inductance may fall before f.o climbs past
    # f.Min:  f.o ~ 1/sqrt(L), so the limit is 1 - 1/k.floor^2
    Ldrop=100 * (1 - 1 / SH['k.floor'] ** 2),
    # the specified ceiling and the four lambda candidates it feeds: two of
    # them divide by 1 - (f.r/f.sw,max)^2, so the number typed as the maximum
    # switching frequency is what computes the tank
    frt=R['fr_t'] / 1e3, fswspec=R['fsw_max_spec'] / 1e3,
    lam1=SH['λ.1'], lam2=SH['λ.2'], lamTD=SH['λ.TD'], lam3=SH['λ.3'],
    fswmaxop=SH['f.sw_max_op'],
    frt2=100 * (R['fr_t'] / R['fsw_max_spec']) ** 2,
    fswPk=_fsw_peaks(),
    nAbove=sum(1 for _n, _v, _p, a in _fsw_peaks() if a),
    kfloor=SH['k.floor'], kceil=SH['k.ceil'], kOCP=SH['k.OCP'],
    khold=SH['k.hold'], kPloss=SH['k.Ploss'], kPSR=SH['k.PSR'],
    # the standing device in half-bridge morphing, and what it demands of the
    # heatsinking.  These were typed in as 9.62 W and 10.4 C/W, which is the
    # pair an earlier line-cycle rms produced - the sheet now says otherwise
    # and a typed number cannot follow it.
    Ploss=SH['P.mos_dc'], Rth=(125.0 - 25.0) / SH['P.mos_dc'],
    PSR=SH['P.SR_dev'],
)

# Hold-up is the one requirement both architectures must meet identically,
# so it is the fair way to price the move from a 400 V bus to a 25 V output.
# 320 V is the usual lower limit of an LLC working from a 400 V bus.
_VBUS, _VBUS_MIN = 400.0, 320.0
V['Ehold'] = V['Pout'] * V['Thold'] * 1e-3
V['Cbulk'] = 2 * V['Ehold'] / (_VBUS ** 2 - _VBUS_MIN ** 2) * 1e6      # uF
V['Cratio'] = (V['Chold'] * 1e-3) / (V['Cbulk'] * 1e-6)

# The switching-frequency part of the bank current, on its own. The 2fl
# envelope is the local mean 2*Iout*sin^2(theta); its mean square is
# 4*Iout^2*<sin^4> = 1.5*Iout^2, and the two components are orthogonal.
V['ICouthf'] = sqrt(SH['I.node_ms'] - 1.5 * V['Iout'] ** 2)
V['ICout2f'] = V['Iout'] / sqrt(2.0)

# Which condition sizes the bank. Hold-up starts at the trough of the 2fl
# ripple, so the usable window is (1 - dv/2)^2 - k^2, not 1 - k^2.
V['kv'] = V['Vomin'] / V['Vout']
V['ripLHS'] = (1 - V['dv'] / 200.0) ** 2 - V['kv'] ** 2
V['ripRHS'] = 4 * pi * V['flmin'] * (V['dv'] / 100.0) * V['Thold'] * 1e-3
V['ripK'] = V['Crip'] / V['Chold']      # which condition wins, and by how much
V['ripKs'] = V['ripLHS'] / V['ripRHS']  # the same call made by the screening rule
# what hold-up would be if it were allowed to start from Vout instead
V['tholdVo'] = (V['Cout'] * 1e-3 * (V['Vout'] ** 2 - V['Vomin'] ** 2)
                / (2 * V['Pout']) * 1e3)


def _zvs_closed_form():
    """the closed-form ZVS shortcut, so its error is measured and not quoted

    The shortcut is evaluated with the DESIGN lambda and the design Q_ZVS -
    not with lambda.act and the Q the converter actually runs at.  That is
    not a detail: read the same expression with lambda.act, which is what the
    symbol means everywhere else once the tank is chosen, and the phase comes
    out NEGATIVE - a capacitive answer - on every design point.  The two
    readings are reported side by side so the caller can say which is which.
    """
    from math import atan
    M_, Qz, Q1, fr = SH['M.HBmin'], SH['Q.ZVS'], SH['Q.ZVS1'], SH['f.r'] * 1e3
    e = 1 + (Qz / Q1) ** 5

    def one(lam):
        fn = 1 / sqrt(1 + (1 / lam) * (1 - M_ ** (-e)))
        num = (lam ** 2 + lam + (fn ** 2 - 1) * Qz ** 2) * fn ** 2 - lam ** 2
        return atan(num / (Qz * fn ** 3)) / (2 * pi * fn * fr) * 1e9

    return one(SH['λ']), one(SH['λ.act'])


V['TzcCF'], V['TzcCFact'] = _zvs_closed_form()
# signed error of the shortcut against the sweep at the SAME corner
V['TzcCFpc'] = 100 * (V['TzcCF'] / V['Tzc'] - 1)

# Two oscillator inputs the sheet does not echo as results, recovered from
# rows that it does, so that the design example can quote them without a
# typed constant.
V['Tidle'] = (1 / (2 * SH['f.Min'] * 1e3)
              - SH['C.T'] * 1e-12 * SH['R.T'] * 1e3) * 1e9          # ns
V['PinBM'] = SH['r.BM'] * V['Pin']                                  # W

# ================================================================== styles
# The typeface is a variable so a Korean document can reuse this layout.
FONT, FONTB, FONTI = 'Helvetica', 'Helvetica-Bold', 'Helvetica-Oblique'


def _winfonts():
    return os.path.join(os.environ.get('WINDIR', 'C:' + os.sep + 'Windows'),
                        'Fonts')


def _pkgfonts():
    """fonts that ship inside an installed package, if there is one

    A Linux box usually has no Malgun Gothic and often no Korean font at all.
    Rather than put a font binary in the repository, look for one that a
    package already carries.
    """
    out = []
    for mod in ('koreanize_matplotlib', 'matplotlib'):
        try:
            m = __import__(mod)
        except Exception:
            continue
        d = os.path.dirname(m.__file__)
        for sub in ('fonts', os.path.join('mpl-data', 'fonts', 'ttf')):
            p = os.path.join(d, sub)
            if os.path.isdir(p):
                out.append(p)
    return out


def _pick(cands):
    """first (regular, bold, italic) triple whose files all exist

    Each candidate is (dir, regular, bold, italic); italic may be None, in
    which case the regular face stands in for it.
    """
    for d, reg, bold, ital in cands:
        if d is None:
            continue
        pr = os.path.join(d, reg)
        pb = os.path.join(d, bold)
        pi_ = os.path.join(d, ital) if ital else pr
        if os.path.exists(pr) and os.path.exists(pb) and os.path.exists(pi_):
            return pr, pb, pi_
    return None


# Entities the prose uses that a substitute face may not carry, and what to
# put there instead. A missing glyph is not an error in reportlab - it draws
# nothing, so "5.17 us" silently becomes "5.17 s". NanumGothic, the usual
# Linux stand-in, has GREEK SMALL MU but not MICRO SIGN, and no MINUS SIGN.
_FALLBACK = {
    '&micro;': (0xB5, '&#956;'),        # MICRO SIGN   -> GREEK SMALL MU
    '&minus;': (0x2212, '-'),           # MINUS SIGN   -> hyphen
    '&asymp;': (0x2248, '~'),
    '&radic;': (0x221A, 'sqrt'),
    '&infin;': (0x221E, 'inf'),
    '&ge;': (0x2265, '&gt;='),
    '&le;': (0x2264, '&lt;='),
    '&times;': (0xD7, 'x'),
    '&sup2;': (0xB2, '^2'),
    '&plusmn;': (0xB1, '+/-'),
}
_ENTFIX = {}


def _entity_fixups(tag):
    """which of the entities above this face cannot draw"""
    from reportlab.pdfbase import pdfmetrics
    out = {}
    try:
        c2g = pdfmetrics.getFont(tag).face.charToGlyph
    except Exception:
        return out
    for ent, (cp, alt) in _FALLBACK.items():
        if cp not in c2g:
            out[ent] = alt
    return out


def _register(tag, triple):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pr, pb, pi_ = triple
    pdfmetrics.registerFont(TTFont(tag, pr))
    pdfmetrics.registerFont(TTFont(tag + '-B', pb))
    pdfmetrics.registerFont(TTFont(tag + '-I', pi_))
    pdfmetrics.registerFontFamily(tag, normal=tag, bold=tag + '-B',
                                  italic=tag + '-I', boldItalic=tag + '-B')
    _ENTFIX.clear()
    _ENTFIX.update(_entity_fixups(tag))
    if _ENTFIX:
        print('  이 서체에 없는 글자를 바꿔 넣는다: %s'
              % ' '.join(sorted(_ENTFIX)))


def use_unicode():
    """Register a Latin face that carries Greek and the maths signs.

    reportlab's built-in Helvetica is Latin-1, so every Greek letter and every
    maths sign in the prose was dropped silently - lambda, mu, ohm and eta came
    out blank and the square root came out as a stray glyph.

    Arial is the first choice because it is metric compatible with Helvetica,
    so the layout does not move.  Liberation Sans is a metric-compatible clone
    of Arial and is the usual Linux stand-in; DejaVu Sans is the last resort
    and does shift the line breaks slightly.
    """
    global FONT, FONTB, FONTI
    t = _pick([(_winfonts(), 'arial.ttf', 'arialbd.ttf', 'ariali.ttf'),
               ('/usr/share/fonts/truetype/liberation',
                'LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf',
                'LiberationSans-Italic.ttf'),
               ('/usr/share/fonts/truetype/dejavu', 'DejaVuSans.ttf',
                'DejaVuSans-Bold.ttf', 'DejaVuSans-Oblique.ttf')]
              + [(d, 'DejaVuSans.ttf', 'DejaVuSans-Bold.ttf',
                  'DejaVuSans-Oblique.ttf') for d in _pkgfonts()])
    if t is None:                                # keep building without Greek
        print('라틴 유니코드 폰트를 못 찾아 Helvetica 로 간다 '
              '(그리스 문자가 빠진다)')
        return
    _register('AN', t)
    bold = {k for k, v in S.items() if v.fontName == FONTB}
    ital = {k for k, v in S.items() if v.fontName == FONTI}
    FONT, FONTB, FONTI = 'AN', 'AN-B', 'AN-I'
    for k, v in S.items():
        v.fontName = FONTB if k in bold else (FONTI if k in ital else FONT)
    print('본문 서체: %s' % os.path.basename(t[0]))


def use_korean():
    """swap in a Korean face - reportlab's built-ins are Latin-1 only

    Malgun Gothic first, because that is what the documents were laid out on.
    Everything after it is a stand-in for a machine that does not have it; the
    metrics differ slightly, so line breaks can move, but nothing is dropped.
    """
    global FONT, FONTB, FONTI
    t = _pick([(_winfonts(), 'malgun.ttf', 'malgunbd.ttf', None),
               ('/usr/share/fonts/truetype/nanum', 'NanumGothic.ttf',
                'NanumGothicBold.ttf', None),
               ('/usr/share/fonts/opentype/noto', 'NotoSansCJK-Regular.ttc',
                'NotoSansCJK-Bold.ttc', None)]
              + [(d, 'NanumGothic.ttf', 'NanumGothicBold.ttf', None)
                 for d in _pkgfonts()]
              + [('/usr/share/fonts/truetype/wqy', 'wqy-zenhei.ttc',
                  'wqy-zenhei.ttc', None)])
    if t is None:
        raise SystemExit('한국어 폰트를 찾을 수 없다. Malgun Gothic 이 있는 '
                         'PC 에서 돌리거나  pip install koreanize-matplotlib '
                         '로 NanumGothic 을 받아 둘 것.')
    global LEAD_SCALE
    _register('KR', t)
    bold = {k for k, v in S.items() if v.fontName == FONTB}
    FONT, FONTB, FONTI = 'KR', 'KR-B', 'KR-I'
    # Hangul fills the full em box, so a leading set for Latin leaves a
    # subscript sitting on the line below it. Measured on the first build:
    # I_Lr and f_sw in running text collided at the Latin leading and clear
    # it at 1.16.
    LEAD_SCALE = 1.16
    for k, v in S.items():
        v.fontName = FONTB if k in bold else FONT
        v.leading = round(v.leading * LEAD_SCALE, 1)
    print('본문 서체: %s   행간 x%.2f'
          % (os.path.basename(t[0]), LEAD_SCALE))


# Styles built after use_korean() - bullets() makes one per call - have to get
# the same leading the S dict got, or a subscript in a bullet lands on the
# line below while the same subscript in a paragraph clears it.
LEAD_SCALE = 1.0


def st(name, **kw):
    kw.setdefault('fontName', FONT)
    kw.setdefault('fontSize', 9.3)
    kw.setdefault('leading', 12.2)
    kw['leading'] = round(kw['leading'] * LEAD_SCALE, 1)
    kw.setdefault('textColor', colors.black)
    return ParagraphStyle(name, **kw)


S = {
    'p': st('p', alignment=TA_JUSTIFY, spaceAfter=6),
    'h1': st('h1', fontName=FONTB, fontSize=13.5, leading=17,
             spaceBefore=16, spaceAfter=9, textColor=colors.black),
    'h2': st('h2', fontName=FONTB, fontSize=10.8, leading=14,
             spaceBefore=13, spaceAfter=6),
    # leading has to clear a subscript, or an I_Lr in a two-line caption
    # lands on the line below it
    'cap': st('cap', fontName=FONTB, fontSize=8.6, leading=12.6,
              alignment=TA_CENTER, spaceBefore=5, spaceAfter=11),
    'eqn': st('eqn', fontName=FONTB, fontSize=9, alignment=TA_RIGHT),
    'tc': st('tc', fontSize=8.4, leading=10.6),
    'th': st('th', fontName=FONTB, fontSize=8.4, leading=10.6,
             textColor=colors.white),
    'note': st('note', fontSize=8.8, leading=11.6, alignment=TA_JUSTIFY,
               textColor=NAVY),
    # tight enough that the contents fit two pages - a third page carrying
    # one entry is worse than a slightly denser list
    'toc0': st('toc0', fontName=FONTB, fontSize=9.3, leading=14.4),
    'toc1': st('toc1', fontSize=9.0, leading=12.8, leftIndent=22),
}


# ------------------------------------------------------------ text mangling
# reportlab renders the Greek entities, the arrows and the relations by itself
# - do not "help" it with <font face="Symbol">, which draws black boxes. The
# one entity it turns into nothing is &thinsp;.


def T(t):
    # A '%%' or a '%(' can only survive to here if a '% V' was forgotten - the
    # string would print the placeholder. Refuse rather than ship it.
    if '%%' in t or '%(' in t or '%s' in t or '%d' in t:
        raise SystemExit('포맷 안 된 문자열이 남아 있다: %s' % t[:110])
    t = t.replace('&thinsp;', '&#8202;')
    for ent, alt in _ENTFIX.items():          # empty unless a face lacks them
        t = t.replace(ent, alt)
    return t

# ============================================================== equations
def eqpng(tex, size=17.0):
    if not os.path.isdir(EQD):
        os.makedirs(EQD)
    key = hashlib.md5(('%s|%s' % (tex, size)).encode('utf-8')).hexdigest()[:14]
    p = os.path.join(EQD, key + '.png')
    if not os.path.exists(p):
        plt.rcParams['mathtext.fontset'] = 'stix'
        fig = plt.figure(figsize=(0.02, 0.02))
        fig.text(0, 0, '$%s$' % tex, fontsize=size)
        fig.savefig(p, dpi=340, transparent=True, bbox_inches='tight',
                    pad_inches=0.03)
        plt.close(fig)
    return p


_EQN = [0]


def eq(tex, size=17.0, number=True, key=None):
    """a centred equation with its number at the right margin

    key registers the number so that the worked example can say which
    equation a figure was substituted into, instead of the reader having
    to find it. The number is never typed by hand.
    """
    from PIL import Image as PIm
    p = eqpng(tex, size)
    iw, ih = PIm.open(p).size
    w = iw / 340.0 * 72
    h = ih / 340.0 * 72
    if w > CW - 60:                       # never let a long one run wide
        h *= (CW - 60) / w
        w = CW - 60
    lab = ''
    if number:
        _EQN[0] += 1
        lab = '(%d)' % _EQN[0]
        if key:
            REFS['eq'][key] = _EQN[0]
    t = Table([[Image(p, w, h), Paragraph(lab, S['eqn'])]],
              colWidths=[CW - 46, 46], rowHeights=[h + 10])
    t.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'CENTER'),
                           ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('LEFTPADDING', (0, 0), (-1, -1), 0),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                           ('TOPPADDING', (0, 0), (-1, -1), 2),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
    return t


# ================================================================ content
FIGSCALE = 1.0            # global figure size, tuned against the page gaps
_FIG = {}
# name -> the number it was given, filled on the first pass and read on the
# second. A reference that has no entry yet renders as "?" and the build
# refuses to keep it (see _check_refs).
REFS = {'fig': {}, 'tbl': {}, 'sec': {}, 'eq': {}}


# Every name asked for, so that one which never resolves fails the build
# instead of printing a question mark into the page. Pass one asks before
# anything is registered, so the test is what is still missing at the end.
_ASKED = {'fig': set(), 'tbl': set(), 'sec': set(), 'eq': set()}


def _ref(kind, key):
    _ASKED[kind].add(key)
    return str(REFS[kind].get(key, '?'))


def figref(name):
    return _ref('fig', name)


def tblref(name):
    return _ref('tbl', name)


def secref(title):
    return _ref('sec', title)


def eqref(key):
    return _ref('eq', key)


def check_refs():
    """names asked for that no pass ever registered"""
    dead = ['  %s  %s' % (k, n) for k in sorted(_ASKED)
            for n in sorted(_ASKED[k]) if n not in REFS[k]]
    if dead:
        raise SystemExit(u'풀리지 않는 상호참조 %d건:\n%s'
                         % (len(dead), '\n'.join(dead)))




_SHRUNK = {}          # the document is built three times; keep the last


class FigBlock(Flowable):
    """image + caption, able to give up a little height to avoid a break"""

    MINFIT = 0.74          # never shrink a figure past this much of itself

    def __init__(self, path, w, h, cap):
        Flowable.__init__(self)
        self.path, self.w0, self.h0, self.cap = path, w, h, cap
        self.w, self.h, self.ch, self.aw = w, h, 0, w
        self.spaceBefore = 4
        self.spaceAfter = 11

    def wrap(self, aw, ah):
        self.aw = aw
        self.ch = self.cap.wrap(aw, ah)[1]
        need = self.h0 + 5 + self.ch
        s = 1.0
        if ah < need <= ah / self.MINFIT:
            s = (ah - self.ch - 5) / self.h0
        self.w, self.h = self.w0 * s, self.h0 * s
        return aw, self.h + 5 + self.ch

    def draw(self):
        if self.w < self.w0 - 0.5:         # what it gave up, for the report
            _SHRUNK[os.path.basename(self.path)] = self.w / self.w0
        self.cap.drawOn(self.canv, 0, 0)
        self.canv.drawImage(self.path, (self.aw - self.w) / 2.0,
                            self.ch + 5, self.w, self.h, mask='auto')


def fig(name, caption, width=None, sec=None):
    """a centred figure with a numbered caption"""
    from PIL import Image as PIm
    p = os.path.join(FIGS, name + '.png')
    if not os.path.exists(p):
        raise SystemExit('그림이 없다: %s   (figs.py --plain %s)'
                         % (p, name.replace('f1', 'f1')))
    iw, ih = PIm.open(p).size
    # A figure block that will not fit in what is left of a page moves whole
    # to the next one and leaves the gap behind. Trimming every figure a
    # little lets more of them fit; FIGSCALE is the one knob for that.
    w = (width or CW) * FIGSCALE
    w = min(w, CW)
    h = w * ih / iw
    if h > 430:                            # keep one figure to a page at most
        w *= 430.0 / h
        h = 430
    n = _FIG.setdefault(name, len(_FIG) + 1)
    REFS['fig'][name] = n
    return FigBlock(p, w, h,
                    Paragraph(T('%s %d:  %s' % (FIGWORD, n, caption)), S['cap']))


_TBL = [0]


def tbl(caption, rows, widths=None, align=None, key=None):
    _TBL[0] += 1
    REFS['tbl'][key or caption] = _TBL[0]
    head = [Paragraph(T(c), S['th']) for c in rows[0]]
    body = [[Paragraph(T(str(c)), S['tc']) for c in r]
            for r in rows[1:]]
    widths = widths or [CW / len(rows[0])] * len(rows[0])
    t = Table([head] + body, colWidths=widths, repeatRows=1)
    style = [('BACKGROUND', (0, 0), (-1, 0), NAVY),
             ('LINEBELOW', (0, 0), (-1, -1), 0.4, LT),
             ('LINEBELOW', (0, 0), (-1, 0), 0.7, NAVY),
             ('VALIGN', (0, 0), (-1, -1), 'TOP'),
             ('TOPPADDING', (0, 0), (-1, -1), 3.5),
             ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
             ('LEFTPADDING', (0, 0), (-1, -1), 5),
             ('RIGHTPADDING', (0, 0), (-1, -1), 5)]
    for i in range(2, len(rows), 2):
        style.append(('BACKGROUND', (0, i), (-1, i),
                      colors.HexColor('#F4F6F8')))
    if align:
        for col, a in align.items():
            style.append(('ALIGN', (col, 0), (col, -1), a))
    t.setStyle(TableStyle(style))
    return KeepTogether([t, Paragraph(T('%s %d:  %s' % (TBLWORD, _TBL[0], caption)),
                                      S['cap'])])


def note(text):
    t = Table([[Paragraph(T(text), S['note'])]], colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1),
                            colors.HexColor('#F2F6FA')),
                           ('LINEBEFORE', (0, 0), (0, -1), 2.4, NAVY),
                           ('LEFTPADDING', (0, 0), (-1, -1), 9),
                           ('RIGHTPADDING', (0, 0), (-1, -1), 9),
                           ('TOPPADDING', (0, 0), (-1, -1), 7),
                           ('BOTTOMPADDING', (0, 0), (-1, -1), 7)]))
    return KeepTogether([Spacer(1, 3), t, Spacer(1, 9)])


class H1(Paragraph):
    pass


class H2(Paragraph):
    pass


_SEC = [0, 0]


def h1(text):
    _SEC[0] += 1
    _SEC[1] = 0
    p = H1(T('%d&nbsp;&nbsp;&nbsp;&nbsp;%s' % (_SEC[0], text)), S['h1'])
    p._toc = (0, T('%d  %s' % (_SEC[0], text)))
    REFS['sec'][text] = '%d' % _SEC[0]
    return p


def h2(text):
    _SEC[1] += 1
    lab = '%d.%d' % (_SEC[0], _SEC[1])
    p = H2(T('%s&nbsp;&nbsp;&nbsp;%s' % (lab, text)), S['h2'])
    p._toc = (1, T('%s  %s' % (lab, text)))
    REFS['sec'][text] = lab
    return p


def p(text):
    return Paragraph(T(text), S['p'])


def bullets(items):
    out = []
    for it in items:
        out.append(Paragraph(T('&bull;&nbsp;&nbsp;' + it),
                             st('b', alignment=TA_JUSTIFY, leftIndent=12,
                                firstLineIndent=-12, spaceAfter=4)))
    return out


# =================================================================== canvas
def body_page(c, doc):
    c.saveState()
    c.setFillColor(colors.black)
    c.setFont(FONT, HEADSIZE)
    c.drawString(LM, PH - 56, TITLE)
    c.setStrokeColor(LT)
    c.setLineWidth(0.7)
    c.line(LM, PH - 90, PW - RM, PH - 90)
    # The document identity used to sit in a navy block at the top right,
    # where it competed with the section title on every page.  It belongs in
    # the footer: needed for reference, not for reading.
    c.line(LM, 52, PW - RM, 52)
    c.setFont(FONT, 7.4)
    c.setFillColor(GREY)
    c.drawString(LM, 40, '%s    %s' % (DOCID[0], DOCID[1]))
    c.setFont(FONT, 8.6)
    c.drawRightString(PW - RM, 40, str(doc.page))
    c.restoreState()


def cover_page(c, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, PH - 96, 250, 96, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont(FONT, 9.6)
    c.drawString(24, PH - 40, DOCID[0])
    c.drawString(24, PH - 56, DOCID[1])

    # A slim accent band sitting on the rule. It was 300 pt tall when it
    # framed a circuit drawing; with the drawing gone that read as a
    # missing image rather than as white space.
    c.setFillColor(colors.HexColor('#DCE6F1'))
    c.rect(0, PH - 420, PW, 56, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.rect(0, PH - 424, PW, 4, stroke=0, fill=1)

    c.setFillColor(colors.black)
    c.setFont(FONT, 25)
    for i, line in enumerate(COVER['title']):
        c.drawString(LM, PH - 490 - i * 34, line)
    c.setFont(FONT, 14)
    c.setFillColor(BLUE)
    c.drawString(LM, PH - 556, COVER['sub'])

    h = 44 + 15 * len(COVER['box'])
    c.setFillColor(colors.HexColor('#CBD8E6'))
    c.roundRect(LM, 96, CW, h, 6, stroke=0, fill=1)
    c.setFillColor(colors.black)
    c.setFont(FONTB, 9.4)
    c.drawString(LM + 18, 96 + h - 22, COVER['boxhead'])
    c.setFont(FONT, 9.2)
    for i, line in enumerate(COVER['box']):
        c.drawString(LM + 18, 96 + h - 44 - i * 15, line)
    c.restoreState()


class Doc(BaseDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, '_toc'):
            lvl, txt = flowable._toc
            self.notify('TOCEntry', (lvl, txt, self.page))


# ==================================================================== front
def legal():
    s = [Paragraph('Before you start', S['h1'])]
    for t in (
        'The L6790A behaviour described here comes from a <b>draft</b> '
        'datasheet dated 30&nbsp;April&nbsp;2026. That draft has items marked '
        'TBD and at least one place where it contradicts itself. Check every '
        'controller constant against the released datasheet before the design '
        'goes to production.',
        'The worked design has not been built. Only the numbers marked as '
        'measured are measured; the rest are calculated.',
        'Some of the LLC theory figures are taken from the application notes '
        'in the reference list. Each one names its source in the caption.',
    ):
        s.append(Paragraph(T(t), S['p']))
        s.append(Spacer(1, 3))

    s.append(Spacer(1, 12))
    s.append(Paragraph('Revision history', S['h2']))
    s.append(Table(
        [[Paragraph(c, S['th']) for c in ('Version', 'Date', 'Change')],
         [Paragraph('V1.0', S['tc']), Paragraph('August 2026', S['tc']),
          Paragraph('First issue. Worked design: %.0f V / %.1f A, %.1f W.'
                    % (V['Vout'], V['Iout'], V['Pout']), S['tc'])],
         [Paragraph('V1.1', S['tc']), Paragraph('September 2026', S['tc']),
          Paragraph('Background section on LLC and power factor correction '
                    'added, with circuit figures. Transformer design, the '
                    'closed form for f<sub>sw</sub>(&theta;), the '
                    'compensator design method, the gain-margin check and '
                    'the input capacitor added. Worked design moved to the '
                    'N<sub>p</sub>:N<sub>s</sub> = %d:%d transformer.'
                    % (V['NpSet'], V['Ns']), S['tc'])]],
        colWidths=[70, 90, CW - 160],
        style=TableStyle([('BACKGROUND', (0, 0), (-1, 0), NAVY),
                          ('LINEBELOW', (0, 0), (-1, -1), 0.4, LT),
                          ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                          ('TOPPADDING', (0, 0), (-1, -1), 4),
                          ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                          ('LEFTPADDING', (0, 0), (-1, -1), 5)])))

    s.append(Spacer(1, 18))
    s.append(Paragraph('Conventions', S['h2']))
    s.extend(bullets([
        'Frequencies are switching frequencies unless written '
        'f<sub>l</sub>, which is the line frequency.',
        '<b>f<sub>n</sub></b> = f<sub>sw</sub>/f<sub>r</sub> is the '
        'switching frequency normalised to the series resonance. Gain curves '
        'are always drawn against it, so that one curve serves every tank. '
        'Figures reproduced from other documents may write f<sub>s</sub> for '
        'f<sub>sw</sub>; that is the same quantity.',
        '<b>M</b> is the voltage gain of the resonant network: the output '
        'voltage referred to the primary, divided by the fundamental of the '
        'square wave driving it. <b>M = 1 at the series resonance</b>, '
        'whatever the load.',
        '<b>Z<sub>0</sub></b> = &radic;(L<sub>r</sub>/C<sub>r</sub>) is the '
        'characteristic impedance of the tank, and <b>Q = '
        'Z<sub>0</sub>/R<sub>ac</sub></b> is its quality factor &mdash; how '
        'heavily the tank is loaded. Q = 0 is no load; larger Q is more '
        'power and a flatter, lower gain curve.',
        '<b>V<sub>o,eff</sub></b> = V<sub>out</sub> + '
        'N<sub>rect</sub>V<sub>f</sub> is the output voltage the primary '
        'actually sees, with the rectifier drop added. '
        '<b>N<sub>rect</sub></b> is the number of rectifier drops in the '
        'conduction path: 1 for a centre tap, 2 for a full bridge.',
        '<b>n</b> is the equivalent-model turns ratio used in the gain '
        'equation; <b>n<sub>T</sub></b> is the physical turns ratio of a '
        'transformer whose leakage is integrated into L<sub>r</sub>.',
        '&lambda;&nbsp;=&nbsp;L<sub>r</sub>/L<sub>m</sub>, and '
        'm&nbsp;=&nbsp;1&nbsp;+&nbsp;1/&lambda; is the ratio of total primary '
        'to resonant inductance used in older literature.',
        '&theta; is the line phase angle, zero at the mains zero crossing.',
        '&ldquo;Equivalent input&rdquo; is what the resonant tank sees after '
        'topology morphing, which is not the mains voltage.',
    ]))
    return s


def toc(title='Table of contents'):
    t = TableOfContents()
    t.levelStyles = [S['toc0'], S['toc1']]
    t.dotsMinLevel = 0
    return [Paragraph(title, S['h1']), Spacer(1, 8), t]


# ==================================================================== build
# ReportLab fits a paragraph by leading, so the descenders of a last line
# that lands on the frame edge fall outside it - 3.2 pt, measured. The frame
# keeps that much in hand.
DESC = 5


def build(story, out=None, toc_title='Table of contents'):
    """page furniture + the story. A second document reuses everything here."""
    doc = Doc(out or OUT, pagesize=A4, title=TITLE,
              author='Single-stage PF LLC programme',
              subject=DOCID[0], leftMargin=LM, rightMargin=RM,
              topMargin=TM, bottomMargin=BM)
    doc.addPageTemplates([
        PageTemplate(id='cover', frames=[Frame(0, 0, PW, PH, id='c')],
                     onPage=cover_page),
        PageTemplate(id='body',
                     frames=[Frame(LM, BM, CW, PH - TM - BM, id='b',
                                   leftPadding=0, rightPadding=0,
                                   topPadding=0, bottomPadding=DESC)],
                     onPage=body_page)])
    doc.multiBuild(story)
    p = out or OUT
    print('%s   %.1f KB' % (os.path.basename(p), os.path.getsize(p) / 1024.0))
    check_refs()
    print('  equations %d · figures %d · tables %d'
          % (_EQN[0], len(_FIG), _TBL[0]))
    if _SHRUNK:
        print('  figures trimmed to fit the page: %d of %d'
              % (len(_SHRUNK), len(_FIG)))
        for nm, r in sorted(_SHRUNK.items(), key=lambda t: t[1]):
            print('    %-28s %.0f %%' % (nm[:-4], r * 100))


def _pass1():
    _FIG.clear()
    _TBL[0] = 0
    _EQN[0] = 0
    _SEC[0] = _SEC[1] = 0


def _pass2():
    """keep REFS, reset the counters so the real pass numbers from one"""
    _FIG.clear()
    _TBL[0] = 0
    _EQN[0] = 0
    _SEC[0] = _SEC[1] = 0


def main():
    use_unicode()          # Greek and maths signs in the prose
    if '--figs' in sys.argv:
        subprocess.check_call(
            [sys.executable, os.path.join(HERE, 'figs.py'), '--plain',
             'f02', 'f04', 'f05', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16',
             'f17', 'f18', 'f19', 'an_tank_current', 'an_loop_bode'])
    import an_body
    # First pass: throw the story away and keep only the numbering, so that
    # figref/tblref/secref resolve on the second.  A typed "Figure 1" cannot
    # survive adding a figure; a name can.
    _pass1()
    an_body.build(sys.modules[__name__])
    _pass2()
    s = [NextPageTemplate('body'), PageBreak()]
    s += legal()
    s.append(PageBreak())
    s += toc()
    s.append(PageBreak())
    s += an_body.build(sys.modules[__name__])
    build(s)


if __name__ == '__main__':
    main()
