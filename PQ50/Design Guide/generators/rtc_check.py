# -*- coding: utf-8 -*-
"""Is the workbook's f_sw(theta) grid search the same answer as the closed form?

RTC is the sheet where the workbook solves the central question of this
topology: at each line phase, what switching frequency delivers the gain the
boundary condition demands. It does it by laying out a grid of normalised
frequencies (83 columns, step 1/69), evaluating the gain curve across it, and
interpolating where that curve crosses the required gain. 10,008 formulas.

Reading those cells one by one is the wrong check - it would only prove the
grid is self-consistent. This compares its ANSWER against two solvers that
share no code with it:

  - Cardano       the closed form the SMath sheet uses (cubic in x = 1/fn^2,
                  physical root is always the k=1 branch)
  - bisection     l6790.py's solve_fn, scan-then-bisect

RTC computes 6 theta values at 3 input voltages = 18 points. CC reads 9 of
them (pi/4, pi/3, pi/2) and feeds them into the tank currents that size the
output bank and the semiconductors; Device Setting reads one more as f_sw,max.
All 18 are checked here, including the ones the grid reports as having no
inductive solution - the solvers must agree about that too.

Not covered, and not a defect in RTC: the workbook's Vin_max is 264 Vac, so
none of these points is the FB morphing corner (332.34 Vac equivalent), where
f_sw actually peaks. The worksheet sweeps that corner separately.
"""
import io
import os
import re
import sys
import zipfile
from math import pi, sqrt, sin, cos, acos

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# paths are relative to this script, so the toolchain moves with the folder
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
if os.environ.get('XL_OVERRIDE'):          # a variant instead of the canonical workbook
    XL = os.environ['XL_OVERRIDE']
sys.path.insert(0, HERE)
from l6790 import design, solve_fn                                    # noqa: E402

TOL = 0.5          # percent; one grid step is 1/69 of f_r, about 1.5 %
THETA = [(pi / 2, 'pi/2'), (5 * pi / 12, '5pi/12'), (pi / 3, 'pi/3'),
         (pi / 4, 'pi/4'), (pi / 6, 'pi/6'), (pi / 12, 'pi/12')]
# (row the fn solutions live on, row the required gains live on, label, RTC
# cell holding that band's input voltage). These are RTC'S OWN header cells -
# CC has a differently-numbered header block, and reading the wrong one silently
# feeds the turns ratio in as a voltage.
BANDS = [(60, 53, 'Vin.min', 'C7'),
         (74, 67, 'Vin.max', 'C9'),
         (88, 81, 'Vin.nom', 'C8')]

# 2026-08-23: the solutions moved to a closed form in RTC rows 220..234, one
# column per (band, theta) in the same order as BANDS x THETA. This maps each
# column back to the grid row it replaced.
CARDANO = {}
for _b, (_first, _m, _lbl, _v) in enumerate(BANDS):
    for _k in range(6):
        _i = _b * 6 + _k + 3                    # column C is 3
        _name = ''
        _n = _i
        while _n:
            _n, _r = divmod(_n - 1, 26)
            _name = chr(65 + _r) + _name
        CARDANO[_name] = _first + _k


def _xl_design_point():
    """설계점을 부거원서 Res. Tank Design 예 섬정 셀에서 읽블우.

    2026-09-08: C.r 과 L.r 도 F43 · F44 에서 읽는다.  그 둘만 100 nF / 11 uH 로
    남아 있어서 6:1(180 nF / 6.4 uH)에서 참조 f_r 이 151.75 kHz 로 굳었고,
    멀쩡한 워크북이 36건 불일치로 보고됐다.

    예전에는 n=6.0 / Lm=20u 가 이 파라㋐ 박혀 있었고, 설계가 9:1 조핐 뒤
    M_req 가 통째로 -19.5 % 어긋나 격자가 깨진 것처럼 보였다.  실제로 틀린 것은
    워크북이 아니라 이 참조값이었다.
    """
    import openpyxl
    wv = openpyxl.load_workbook(XL, read_only=True, data_only=True)
    ws = wv['Res. Tank Design']
    n = ws['F9'].value or ws['D9'].value
    cr = (ws['F43'].value or ws['D43'].value) * 1e-9
    lr = (ws['F44'].value or ws['D44'].value) * 1e-6
    lm = (ws['F45'].value or ws['D45'].value) * 1e-6
    wv.close()
    return float(n), float(cr), float(lr), float(lm)


_XL_N, _XL_CR, _XL_LR, _XL_LM = _xl_design_point()


def require_readable(path):
    """Excel takes an exclusive lock while the workbook is open. Say so
    plainly rather than dying inside zipfile with a bare PermissionError."""
    try:
        open(path, 'rb').close()
    except PermissionError:
        print('워크북이 Excel 에서 열려 있어 읽을 수 없다. 닫고 다시 실행뵠 것:')
        print('  ' + path)
        raise SystemExit(2)


def sheets_of(z):
    wbx = z.read('xl/workbook.xml').decode('utf-8')
    rel = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          z.read('xl/_rels/workbook.xml.rels').decode('utf-8')))
    return {nm: 'xl/' + rel[r].lstrip('/') for nm, r in
            re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wbx)}


def cardano(Mreq, Q, lam):
    """The worksheet's section 8. Returns fn, or None where no real inductive
    root exists - the same 'burst region' answer the grid reports as NA()."""
    a2 = (Q ** 2 - 2 * lam * (1 + lam)) / lam ** 2
    a1 = ((1 + lam) ** 2 - 2 * Q ** 2 - 1 / Mreq ** 2) / lam ** 2
    a0 = Q ** 2 / lam ** 2
    p = a1 - a2 ** 2 / 3
    q = 2 * a2 ** 3 / 27 - a2 * a1 / 3 + a0
    if p >= 0:
        return None
    w = 2 * sqrt(-p / 3)
    z = 3 * q / (p * w)
    if not -1.0 <= z <= 1.0:
        return None
    x = w * cos(acos(z) / 3 - 2 * pi / 3) - a2 / 3
    if x <= 0:
        return None
    fn = 1 / sqrt(x)
    return fn if fn >= sqrt(lam / (1 + lam)) else None


def main():
    require_readable(XL)
    z = zipfile.ZipFile(XL)
    sh = sheets_of(z)
    rtc = z.read(sh['RTC']).decode('utf-8')
    cc = z.read(sh['CC']).decode('utf-8')

    def val(src, ref):
        m = re.search(r'<c r="%s"[^>]*(?:/>|>(.*?)</c>)' % ref, src, re.S)
        if not m or not m.group(1):
            return None
        v = re.search(r'<v>(.*?)</v>', m.group(1), re.S)
        try:
            return float(v.group(1))
        except (ValueError, TypeError, AttributeError):
            return None

    # the grid's answers, keyed by the row each BB cell scans
    grid = {}
    for m in re.finditer(r'<c r="BB\d+"[^>]*>(.*?)</c>', rtc, re.S):
        body = m.group(1)
        f = re.search(r'<f[^>]*>(.*?)</f>', body, re.S)
        if not f:
            continue
        # Three shapes, in the order they appeared:
        #   MAX(C60:CG60)      the plain grid scan
        #   MAX(C79:CH79)      the pi/12 rows, CH being the no-crossing fallback
        #   C232               the closed form installed 2026-08-23, which reads
        #                      straight out of the Cardano block below row 218
        g = re.search(r'MAX\(C(\d+):C[GH]\d+\)', f.group(1))
        if g:
            row = int(g.group(1))
        else:
            d = re.fullmatch(r'\$?([A-Z]{1,2})\$?(\d+)', f.group(1).strip())
            if not d or int(d.group(2)) <= 218:
                continue
            # map the Cardano column back to the grid row it replaced, so the
            # labels and band ordering below still line up
            row = CARDANO.get(d.group(1))
            if row is None:
                continue
        v = re.search(r'<v>(.*?)</v>', body, re.S)
        try:
            grid[row] = float(v.group(1))
        except (ValueError, TypeError, AttributeError):
            grid[row] = None                      # NA() - no inductive solution

    R = design(Vout=25., Pout=657.5, Vo_min=19., dv_out=0.05, Thold=12e-3,
               Nrect=1, fr_t=150e3, fsw_max_spec=225e3, fsw_min_spec=50e3,
               c_HB=800e-12, tD=220e-9, n_sel=_XL_N,
               Cr_sel=_XL_CR, Lr_sel=_XL_LR, Lm_sel=_XL_LM)
    n, Voe, lam = R['n'], R['Vo_eff'], R['lam_a']
    fr, fn0, Qpk = R['fr'], R['fn0'], R['Qpk']

    fr_xl = val(cc, 'C22')
    print('참조 구현  n %.4f · lambda %.4f · f_r %.4f kHz · Q_pk %.6f'
          % (n, lam, fr / 1e3, Qpk))
    print('워크북     f_r %.4f kHz  (CC C22)' % (fr_xl or float('nan')))
    print()
    print('%-15s %-8s %8s %7s %11s %11s %11s %8s %8s'
          % ('입력', 'theta', 'M_req', 'dM_req', '엑셀 격자', 'Cardano', '이분법',
             'dCard', 'dBisect'))
    print('-' * 100)

    bad = 0
    worst = 0.0
    checked = 0
    for base, mbase, blabel, vref in BANDS:
        Vac = val(rtc, vref)
        for k, (th, tl) in enumerate(THETA):
            if base + k not in grid:
                continue
            xl_fn = grid[base + k]
            checked += 1
            Mreq = 2 * n * Voe / (sqrt(2) * Vac * sin(th))
            Q = Qpk * sin(th) ** 2
            fc, fb = cardano(Mreq, Q, lam), solve_fn(Mreq, Q, lam, fn0)
            head = ('%-15s' % ('%s %.2f V' % (blabel, Vac))) if k == 0 else ' ' * 15
            # the workbook's own required gain, so an upstream error shows up
            # here rather than being blamed on the grid
            mxl = val(rtc, 'C%d' % (mbase + k))
            dm = (Mreq - mxl) / mxl * 100 if mxl else float('nan')
            if dm != dm or abs(dm) > TOL:
                bad += 1
            else:
                worst = max(worst, abs(dm))
            if xl_fn is None:
                ok = fc is None and fb is None
                if not ok:
                    bad += 1
                print('%s %-8s %8.4f %6.3f%% %11s %11s %11s   %s'
                      % (head, tl, Mreq, dm, 'NA(해없음)',
                         'NA' if fc is None else '%.4f' % (fc * fr / 1e3),
                         'NA' if fb is None else '%.4f' % (fb * fr / 1e3),
                         'ok' if ok else '** 불일치'))
                continue
            xl = xl_fn * fr / 1e3
            dc = (fc * fr / 1e3 - xl) / xl * 100 if fc else float('nan')
            db = (fb * fr / 1e3 - xl) / xl * 100 if fb else float('nan')
            for d in (dc, db):
                if d != d or abs(d) > TOL:
                    bad += 1
                else:
                    worst = max(worst, abs(d))
            print('%s %-8s %8.4f %6.3f%% %11.4f %11.4f %11.4f %7.3f%% %7.3f%%'
                  % (head, tl, Mreq, dm, xl,
                     fc * fr / 1e3 if fc else float('nan'),
                     fb * fr / 1e3 if fb else float('nan'), dc, db))
        print()

    step = fr / 1e3 / 69
    print('대조 %d점 · 최대 편차 %.4f %% · 허용 %.2f %%' % (checked, worst, TOL))
    print('격자 한 칸 = f_r/69 = %.3f kHz. 최쌀 편차를 주파수로 환산하면 약 %.3f kHz'
          % (step, worst / 100 * 160))
    print('VERDICT ' + ('OK' if bad == 0 else 'FAIL  불일치 %d' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
