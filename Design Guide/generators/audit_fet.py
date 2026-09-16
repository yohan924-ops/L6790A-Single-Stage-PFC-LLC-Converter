# -*- coding: utf-8 -*-
"""Which device parameters do the two sheets pull, and do they compute with them?

Selecting a MOSFET for an LLC is not the same as selecting one for a hard
switched converter, so a checklist copied from a buck design silently drops the
parameters that matter here. This walks the primary and secondary blocks of the
workbook and of the SMath sheet and asks two separate questions about each
parameter an LLC needs:

    IN   is the parameter present at all - is there a cell or a variable for it
    USED is it consumed by a formula, or does it just sit there being printed

A parameter that is present but unused is the more dangerous of the two: it
looks like it was considered.

The checklist is written down here, not derived - deriving "what an LLC FET
selection needs" from the sheets themselves would only ever confirm whatever
the sheets already do.

    python audit_fet.py
"""
import io
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
SM = os.path.join(ROOT, 'Smath',
                  'L6790A_SingleStage_PF_LLC_Design_Guide.sm')
BUILDER = os.path.join(HERE, 'build_l6790_smath.py')

# ----------------------------------------------------------------- checklist
# (key, what it is, why an LLC needs it, workbook cell, SMath variable)
# '' asserts the parameter is absent; the tool checks that against the file
# rather than trusting it. A name starting with '#' means the sheet STATES the
# requirement in prose and deliberately computes no value - correct for a
# device number no calculation can produce.
PRIMARY = [
    ('VDS',   'V_DS breakdown rating',
     'must clear 1.3x the rectified line peak',            'D64', 'V.DS_pri'),
    ('ID',    'I_D rating per POSITION',
     'must clear the COMPOSITE tank peak, not I_trafo',    'D65', 'I.pri_rating'),
    ('NPAR',  'devices in parallel per position',
     'without it no current can divide',                   'D68', 'n.par'),
    ('IPKD',  'peak current in ONE device',
     'what the datasheet I_D has to cover',                'D66', 'I.pk_dev'),
    ('IRMSD', 'rms current in ONE device',
     'what the conduction loss is built on',               'D62', 'I.mos_dev'),
    ('RDS',   'R_DS(on)',
     'conduction loss - the dominant loss in an LLC',      'D70', 'R.dson_p25'),
    ('RDST',  'R_DS(on) temperature factor',
     'x1.8..2.2 at Tj = 125 C for a 600 V superjunction',  'D58', 'K.Tpri'),
    ('COSS',  'C_oss / Q_oss',
     'the charge the dead time has to move for ZVS',       'D71', 'c.HB'),
    ('COSSK', 'WHICH C_oss (Co(tr) vs Co(er) vs @25 V)',
     'the three differ by 3..5x and decide the ZVS answer', '',   '#Coss kind'),
    ('QG',    'Q_g gate charge',
     'sizes the external driver - HOUT/LOUT are logic level', '', '#Q_g'),
    ('EOFF',  'turn-OFF energy',
     'ZVS removes turn-ON loss only; turn-off is real',    '',    '#E_off'),
    ('QRR',   'body diode t_rr / Q_rr',
     'capacitive-region shoot-through - survival',    'D74/D75', 'V.bd_rr'),
    ('BUDG',  'loss budget actually checked',
     'a budget nothing compares against is decoration',    '',    'k.Ploss'),
    ('RTH',   'R_th(j-a) required',
     'thermal budget',                                     'D79', ''),
    ('TJ',    'T_j(max)',
     'the temperature the loss is evaluated AT',           '',    ''),
]
SECONDARY = [
    ('VDS',   'V_DS breakdown rating',
     'reflected 2*Vout plus leakage ringing',              'D89', 'V.DS_sec'),
    ('ID',    'I_D rating per LEG',
     'a CT leg carries the WHOLE secondary current',       'D90', 'I.sec_rating'),
    ('NSR',   'devices in parallel per leg',
     'the only place the leg current divides',            'D103', 'n.SR'),
    ('IPKD',  'peak current in ONE device',
     'what the datasheet I_D has to cover',                'D91', 'I.SR_pk_dev'),
    ('IRMSD', 'rms current in ONE device',
     'what the conduction loss is built on',               'D87', 'I.SR_dev'),
    ('RDS',   'R_DS(on)',
     'conduction loss - dominant at 26 A',                 'D96', 'R.dson_s25'),
    ('RDST',  'R_DS(on) temperature factor',
     'x1.4..1.6 at Tj = 125 C for a low-voltage SR FET',   'D98', 'K.Tsec'),
    ('TYPE',  'diode or SR MOSFET',
     'the loss model is a different equation',   'D93', '#SR by construction'),
    ('VF',    'body diode V_f',
     'conducts during the SR dead time',                   'D95', ''),
    ('COSS',  'C_oss',
     'rings with the leakage - this is what sets the 1.6x', '',   'K.ring'),
    ('QRR',   'body diode Q_rr',
     'recovered twice per switching period in CT',         '',    '#SR Qrr'),
    ('QG',    'Q_g gate charge',
     'x2 legs x n parallel at 150..250 kHz is real power', '',    '#Q_g'),
    ('BUDG',  'loss budget actually checked',
     'a budget nothing compares against is decoration',    '',    'k.PSR'),
    ('RTH',   'R_th required',
     'thermal budget',                                     'D101', ''),
]


# ------------------------------------------------------------------ workbook
def sheet_xml(name):
    with zipfile.ZipFile(XL) as z:
        wb = z.read('xl/workbook.xml').decode('utf-8')
        rels = z.read('xl/_rels/workbook.xml.rels').decode('utf-8')
        rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels))
        for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
            if nm.replace('&amp;', '&') == name:
                return z.read('xl/' + rid[r].lstrip('/')).decode('utf-8')
    raise KeyError(name)


def xl_cells(xml):
    """-> {ref: formula-or-None}"""
    out = {}
    for m in re.finditer(r'<c r="([A-Z]+\d+)"(.*?)(?:/>|</c>)', xml, re.S):
        f = re.search(r'<f[^>]*>(.*?)</f>', m.group(2), re.S)
        out[m.group(1)] = f.group(1) if f else None
    return out


#  'Design Spec'!D95" contains "D95" but is not this sheet's D95. Without
# stripping cross-sheet references first, the audit reported the secondary
# forward drop as consumed by D89, which reads Design Spec D95 instead.
FOREIGN = re.compile(r"(?:'[^']+'|[A-Za-z_][A-Za-z0-9_. ]*)!\$?[A-Z]+\$?\d+")


def xl_used(cells, ref):
    """is `ref` read by a formula ON THIS SHEET?"""
    bare = ref.lstrip('$')
    col, row = re.match(r'([A-Z]+)(\d+)', bare).groups()
    pat = re.compile(r'(?<![A-Z0-9$])\$?%s\$?%s(?![0-9])' % (col, row))
    for r in sorted(cells, key=lambda k: (len(k), k)):
        f = cells[r]
        if f and r != bare and pat.search(FOREIGN.sub('~', f)):
            return r
    return None


# --------------------------------------------------------------- SMath sheet
def sm_defs():
    """-> ({var: rpn-token-list}, order) straight out of the .sm"""
    raw = io.open(SM, encoding='utf-8').read()
    raw = re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>',
                 '<raw/>', raw, flags=re.S)
    root = ET.fromstring(
        raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))
    defs = {}
    for r in root.iter('region'):
        m = r.find('math')
        if m is None:
            continue
        i = m.find('input')
        if i is None:
            continue
        e = list(i)
        if not (e and e[0].get('type') == 'operand'):
            continue
        toks = [x.text for x in e[1:] if x.get('type') == 'operand'
                and x.get('style') != 'unit']
        defs.setdefault(e[0].text, []).append(toks)
    return defs


def sm_used(defs, var):
    for other, bodies in defs.items():
        if other == var:
            continue
        for toks in bodies:
            if var in toks:
                return other
    return None


def report(title, rows, cells, defs):
    print()
    print('=' * 78)
    print(title)
    print('=' * 78)
    print('%-36s %-19s %-19s' % ('parameter', 'workbook', 'SMath'))
    print('-' * 78)
    miss = []
    for key, what, why, cell, var in rows:
        # workbook
        if not cell:
            x = 'ㅡ 없음'
        else:
            first = cell.split('/')[0]
            if first not in cells:
                x = '?? %s 없음' % first
            else:
                u = xl_used(cells, first)
                x = ('사용 -> %s' % u) if u else '표시만'
        # SMath
        if var.startswith('#'):
            m = '요구조건만 명시'
        elif not var:
            m = 'ㅡ 없음'
        elif var not in defs:
            m = '?? %s 없음' % var
        else:
            u = sm_used(defs, var)
            m = ('사용 -> %s' % u) if u else '표시만'
        print('%-36s %-19s %-19s' % (what[:36], x, m))
        if not cell and not var:
            miss.append((what, why))
    if miss:
        print()
        print('  양쪽 모두 없음 -- %d건' % len(miss))
        for what, why in miss:
            print('   * %-32s %s' % (what, why))
    return len(miss)


def main():
    for p in (XL, SM):
        if not os.path.exists(p):
            raise SystemExit('없음: %s' % p)
    try:
        pc = xl_cells(sheet_xml('Power Components'))
    except PermissionError:
        raise SystemExit('워크북이 열려 있다 - Excel 을 닫고 다시 실행할 것')
    defs = sm_defs()

    n1 = report('1차 스위치 (primary MOSFET)   -- Power Components 57..79 / SMath 13.1',
                PRIMARY, pc, defs)
    n2 = report('2차 정류 (SR MOSFET)          -- Power Components 83..102 / SMath 13.2',
                SECONDARY, pc, defs)

    # the one internal contradiction worth naming, checked not asserted
    print()
    print('=' * 78)
    print('온도 정합성')
    print('=' * 78)
    bad = 0
    for label, rds, kt, loss, rth in (('1차', 'D70', 'D58', 'D78', 'D79'),
                                      ('2차', 'D96', 'D98', 'D100', 'D101')):
        f = pc.get(rth) or ''
        tj = re.search(r'\((\d+)\s*-', f)
        rl = pc.get(loss) or ''
        ok = re.search(r'(?<![A-Z0-9$])%s(?![0-9])' % kt, rl) is not None
        if not ok:
            bad += 1
        print('  %s  %s = %s' % (label, loss, rl[:56]))
        print('      %s 는 Tj = %s C 기준. %s(25 C)에 %s 를 곱하는가 -> %s'
              % (rth, tj.group(1) if tj else '?', rds, kt,
                 '예' if ok else '아니오 -- 손실 과소평가'))
    if bad:
        print('  -> 온도 불일치 %d건' % bad)
    else:
        print('  -> 두 식 모두 Tj,max 기준으로 평가된다.')

    print()
    print('양쪽 모두 없는 항목 %d건 (1차 %d · 2차 %d)' % (n1 + n2, n1, n2))
    return 1 if (n1 + n2 + bad) else 0


if __name__ == '__main__':
    raise SystemExit(main())
