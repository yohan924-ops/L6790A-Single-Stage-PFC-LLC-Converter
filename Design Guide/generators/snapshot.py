# -*- coding: utf-8 -*-
"""Rewrite the design-values section of CLAUDE.md from the worksheet itself.

The problem this solves is small and specific. CLAUDE.md is what a new session
reads first, and its section 3 used to be numbers TYPED IN BY HAND. That block
went stale without anyone noticing - it claimed 80 mF / 8 capacitors / 4.40 %
ripple while the sheet had long since said 71.4 mF / 4.99 %. Nothing detects
that, because prose does not get recalculated.

So section 3 is no longer written by hand. This script reads the .sm, pulls the
values out of it, and rewrites the block between the two markers. guard.py then
refuses to end a turn while the block differs from what this would produce, so
the file a future session reads cannot disagree with the file it describes.

    python snapshot.py            rewrite the block, log what changed
    python snapshot.py --check    exit 1 if the block is stale, write nothing
    python snapshot.py --picks    list the yellow cells - what a HUMAN chose

When a value moves the diff is PRINTED, including which yellow cell a human
changed - nearly always the root of it. Record the decision as one line in
HISTORY.md section 8; this script deliberately does not write there itself.

Adding a value to the report: put it in LAYOUT below. A name the sheet does not
define is reported as missing rather than silently dropped.
"""
import io
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

import smresult

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SM = os.path.join(ROOT, 'Smath', 'L6790A_SingleStage_PF_LLC_Design_Guide.sm')
DOC = os.path.join(ROOT, 'CLAUDE.md')
PREV = os.path.join(HERE, '.snapshot_prev.json')

BEGIN = '<!-- BEGIN GENERATED  ...  snapshot.py 가 씁니다. 손으로 고치지 마십시오 -->'
END = '<!-- END GENERATED -->'

# Kept, and empty. These nine used to live here because they started with k
# and were not verdicts, so every "is it above 1" pass flagged them and every
# reader had to be told, name by name, to ignore them. They are named for
# what they are now - K. a coefficient, n. a turns ratio, r. a fraction - so
# the prefix does the excluding and this list has nothing to hold.
NOT_A_CHECK = {}

# A ratio whose real acceptance test is not "above 1". k.PM is phase margin over
# a 50 deg TARGET, but the sheet's own criterion is 45 deg, so 0.986 passes.
# Printing it as a failure sends the next session chasing a problem that is not
# there - which is the exact class of mistake this file exists to prevent.
SOFT = {'k.PM': ('Φ.act', 45.0, '°', '목표 50°, 합격선 45°'),
        # the fitted ZCD divider lands a hair under the target OVP1 by design:
        # only E24 ratios are available. What must hold is that it stays ABOVE
        # the regulated output, which V.OVP1_act > V.out checks directly.
        'k.OVP1': ('V.OVP1_act', 26.25, ' V', '목표 27.5 V, 하한은 V.out+5 %')}

# A verdict that really is below 1 and is MEANT to be. The budget it measures
# was provisional and the user decided to spend past it; without a line saying
# so, the next session reopens a closed decision and re-derives the whole
# argument. Keyed by verdict, and only printed when it is actually failing -
# if a later change brings it back over 1 the note disappears on its own.
# 아래 중 아직 결론이 안 난 것 - '오류가 아니다' 로 끝내면 닫힌 것처럼 읽힌다.
STILL_OPEN = {'k.PSR', 'k.Ae'}

ACCEPTED = {
    'k.Ploss': '1차 정적 도통 소자(LVG2) 9.62 W 대 잠정 예산 3 W. 어느 기술로도 소자 '
               '1개로는 불가능하다(열간 25.3 mohm 필요, 600 V 최선이 17 mohm@25C). '
               '**2026-08-24 사용자가 현 구성으로 확정** — 방열판 여부는 시제품 열 '
               '실측에서 판정한다',
    'k.PSR': '2차 레그당 3.23 W 대 3 W. **9:1 로 오면서 미달로 넘어갔다** — 7.5:1 '
             '에서는 1.063 이었다. n.SR 을 3 으로 올리면 1.39 로 회복되고 그것 말고는 '
             '방법이 없다(`Power Components` D103 한 칸)',
    'k.Ae': '**코어가 아직 선정되지 않았다.** EE6405(113 mm²) 를 자리표시자로 둔 결과이며, '
            '필요 A.e 는 206 mm² 다. 2차를 2턴으로 하면(세트 9:1 유지, 유닛 6:2) 103 mm² '
            '가 되어 EE6405 가 들어간다. 가이드 부록 [151]',
    'k.lam': '**무부하** 최소 게인 조건이라 전부하 판정과 무관하다. 무부하 게인은 점근선 '
             '1/(1+λ.act) 아래로 내려가지 않으므로 요구 게인이 그보다 낮으면 아예 해가 '
             '없다 — 그때는 버스트 모드가 맡는다. 9:1 은 231 kHz 에서 해가 있고 7.5:1 · '
             '6:1 은 해가 없다. 가이드 부록 C.31',
    'k.auxr': '보조권선이 **ZCD 감지 전용**이라 적용되지 않는다 — VCC 는 외부 12 V 에서 '
              '온다. n.aux_max 는 "OVP2 에서 V.aux 가 VCC 정격 25 V 를 넘지 마라"는 뜻이고, 이 권선은 VCC 를 대지 않는다. 워크북과 값을 맞추려고 계산은 남겨 둔다',
    'k.VCC': 'k.auxr 과 같은 이유로 적용되지 않는다 — 보조권선은 ZCD 전용, VCC 는 외부 12 V',
}


def dw(t):
    """printed width - Korean glyphs occupy two columns"""
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in t)


def pad(t, n):
    return t + ' ' * max(0, n - dw(t))

# label, then the values on that line as (printed name, sheet variable, decimals)
LAYOUT = [
    ('탱크', [('Cr', 'C.r', 1), ('Lr', 'L.r', 1), ('Lm', 'L.m', 1),
              ('λ_act', 'λ.act', 3), ('fr', 'f.r', 1), ('fo', 'f.o', 1)]),
    ('', [('Q_pk', 'Q.pk', 3), ('R_ac', 'R.ac', 2, 'Ω'), ('n', 'n', 3),
          ('n_T', 'n.T_act', 3)]),
    ('주파수', [('f_sw HB코너', 'f.sw.a', 1), ('f_sw FB코너', 'f.sw.b', 1),
                ('T_ZC', 'T.ZC.a', 0), ('k_ZVS', 'k.ZVS', 3)]),
    ('전류', [('I_sec,pk', 'I.sec_pk', 1), ('I_Lr,pk', 'I.Lr_pk', 2),
              ('I_trafo,pk', 'I.trafo_pk', 2), ('I_Lm,pk', 'I.Lm_pk', 2)]),
    ('', [('I_pri,rms', 'I.pri_rms', 2), ('I_pri,라인', 'I.pri_lc', 2),
          ('I_diode', 'I.diode_lc', 2), ('I_Cout', 'I.Cout_rms', 2)]),
    ('출력', [('Cout 개당', 'C.single', 0), ('개수', 'n.C', 0),
              ('Cout 합계', 'C.out', 2), ('리플', 'ΔV.out', 3),
              ('리플', 'ΔV.out_pc', 2, '%')]),
    ('', [('홀드업', 't.hold_act', 2), ('k_hold', 'k.hold', 3),
          ('ESR 뱅크', 'ESR.out', 4), ('R&N', 'R.Nact', 1),
          ('개당 리플전류', 'I.Cout_each', 2), ('세라믹', 'C.ceramic', 0)]),
    ('자기', [('직렬 개수', 'N.x', 0), ('Np', 'N.p', 0), ('Ns', 'N.s', 0),
              ('A_L', 'A.L', 0), ('B_pk', 'B.pk', 0),
              ('A_e 필요', 'A.e_req_mm', 0), ('k_Ae', 'k.Ae', 3),
              ('개방시험 전류', 'I.sat_spec', 1)]),
    ('IC', [('R_CS', 'R.CS', 0), ('개당', 'R.CS_single', 0), ('병렬', 'N.RCS', 0),
            ('I_OCP1', 'I.OCP1', 1), ('k_OCP', 'k.OCP', 3)]),
    ('', [('R_T', 'R.T', 0), ('C_T', 'C.T', 0), ('f_Min', 'f.Min', 1),
          ('f_Max', 'f.Max', 1)]),
    ('', [('R_CFG', 'R.CFG_sel', 0), ('V_BO', 'V.BO_act', 2),
          ('R_BM', 'R.BM_sel', 0), ('C_in', 'C.in_sel', 0),
          ('n_aux/n_sec', 'n.aux', 2)]),
    ('루프', [('G_o', 'G.o', 1, 'rad/s'), ('EA_o', 'EA.o', 1, 'rad/s'),
              ('f_z', 'f.zi', 2),
              ('f_p', 'f.pi', 1), ('f_px', 'f.pxi', 0)]),
    ('', [('f_cross', 'f.cross', 2), ('Φ_M', 'Φ.act', 2, '°'),
          ('3차 고조파', 'D.3rd_act', 2, '%')]),
    ('보상망', [('R_I', 'R.I', 0), ('R_o', 'R.o', 0), ('R_P', 'R.P', 1),
                ('R_B', 'R.B', 1), ('V_Z', 'V.Z', 0)]),
    ('', [('C_Fo', 'C.Fo', 0), ('C_F', 'C.F', 0), ('R_F', 'R.F', 0),
          ('C_fx', 'C.fx', 2)]),
    ('1차', [('V_DS 최소', 'V.DS_pri', 1), ('P_in', 'P.in', 1)]),
]


def read_sheet(path):
    """-> ({var: (value, unit)}, [(label, var, value, unit)] for the yellow cells)"""
    raw = io.open(path, encoding='utf-8').read()
    # base64 images make the parse enormous for no benefit
    raw = re.sub(r'<raw format="[^"]+" encoding="base64">.*?</raw>', '<raw/>', raw, flags=re.S)
    root = ET.fromstring(raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))

    vals, picks, last_label = {}, [], ''
    for r in root.iter('region'):
        t = r.find('text')
        if t is not None:
            paras = [(p.text or '') for p in t.iter('p')]
            if paras:
                last_label = ' '.join(paras).strip()
            continue
        m = r.find('math')
        if m is None:
            continue
        i = m.find('input')
        if i is None:
            continue
        e = list(i)
        if not (e and e[0].get('type') == 'operand'):
            continue
        name = e[0].text
        c = m.find('contract')
        unit = list(c)[0].text if c is not None and len(list(c)) else ''
        res = m.find('result')
        if res is not None and len(list(res)):
            # a <result> is RPN, not one token - smresult keeps the sign and
            # any exponent, which reading list(res)[0] silently threw away
            val = smresult.value(res)
            if val is not None:
                vals.setdefault(name, (val, unit))
        if r.get('bgColor') == '#ffff80':
            # a yellow cell is a bare assignment with no <contract>, so its unit
            # has to come from the unit token inside the expression itself
            u = [x.text for x in e if x.get('style') == 'unit']
            picks.append((last_label, name, literal(e), u[0] if u else ''))
    return vals, picks


def literal(elems):
    """the number a yellow assignment carries, when it is a plain literal

    The input is RPN, so a negative literal is stored as the digits followed by
    a unary minus - x.lo := -1 is <e>1</e><e args="1">-</e>. Picking the first
    numeric operand and stopping there reported x.lo as +1 and made a cell
    nobody had touched look like a user edit. Same mistake smresult.py fixes on
    the result side.
    """
    nums = [(i, x.text) for i, x in enumerate(elems)
            if x.get('type') == 'operand' and x.text
            and re.fullmatch(r'-?\d+(\.\d+)?', x.text)]
    if not nums:
        return ''
    i, txt = nums[0]
    nxt = elems[i + 1] if i + 1 < len(elems) else None
    if (nxt is not None and nxt.get('type') == 'operator'
            and nxt.text == '-' and nxt.get('args') == '1'):
        txt = txt[1:] if txt.startswith('-') else '-' + txt
    return txt


def fmt(v, dp):
    s = '%.*f' % (dp, v)
    return s.rstrip('0').rstrip('.') if '.' in s and dp > 0 else s


def build_block(vals):
    out, missing = [], []
    lines = []
    for head, items in LAYOUT:
        parts = []
        for item in items:
            shown, var, dp = item[0], item[1], item[2]
            override = item[3] if len(item) > 3 else None
            if var not in vals:
                missing.append(var)
                parts.append('%s ??' % shown)
                continue
            v, u = vals[var]
            parts.append(('%s %s %s' % (shown, fmt(v, dp), override or u)).strip())
        lines.append(pad(head, 9) + ' · '.join(parts))

    checks, ratios = [], []
    for k in sorted(vals):
        if not k.startswith('k.'):
            continue
        v = vals[k][0]
        if k in NOT_A_CHECK:
            ratios.append((k, v))
        elif k in SOFT:
            src, floor, unit, note = SOFT[k]
            actual = vals.get(src, (float('nan'), ''))[0]
            checks.append((k, v, actual >= floor,
                           '%s %s%s, %s' % (src, fmt(actual, 2), unit, note)))
        else:
            checks.append((k, v, v >= 1.0, ''))
    failed = [c for c in checks if not c[2]]

    out.append(BEGIN)
    out.append('')
    out.append('SMath 시트에서 **기계가 읽어 적은 값**이다. 사람이 고치지 말 것 —')
    out.append('`cd "Design Guide/generators" && python snapshot.py` 로 다시 만든다.')
    out.append('시트를 바꾸고 이 블록을 갱신하지 않으면 **Stop hook이 턴을 막는다.**')
    out.append('')
    out.append('```')
    out.extend(lines)
    out.append('```')
    out.append('')
    out.append('**판정 지표 — 전부 "> 1" 이어야 한다** (시트 §17):')
    out.append('')
    out.append('```')
    row, notes = [], []
    for k, v, ok, note in checks:
        row.append(pad('%s %.3f%s' % (k, v, '' if ok else '  <-- 미달'), 20))
        if note:
            notes.append('%s %.3f 은 %s -> 합격' % (k, v, note))
        elif not ok and k in ACCEPTED:
            tail = ('**계산 오류가 아니라 아직 안 닫은 설계 항목이다**'
                    if k in STILL_OPEN else '**오류가 아니다**')
            notes.append('%s %.3f 는 %s. %s' % (k, v, ACCEPTED[k], tail))
        if len(row) == 4:
            out.append(' '.join(row).rstrip())
            row = []
    if row:
        out.append(' '.join(row).rstrip())
    out.append('')
    out.append('통과 %d / %d%s' % (len(checks) - len(failed), len(checks),
                                   '' if not failed
                                   else '   미달: ' + ', '.join(c[0] for c in failed)
                                   + ('   ← 아래 설명 참조' if any(
                                       c[0] in ACCEPTED for c in failed) else '')))
    for n in notes:
        out.append(n)
    out.append('```')
    out.append('')
    out.append('> 아래는 **판정이 아니라 그냥 비율**이다. "1 미만"이라고 문제 삼지 말 것:')
    out.append('> ' + ' · '.join('`%s` %.3f (%s)' % (k, v, NOT_A_CHECK[k]) for k, v in ratios))
    if missing:
        out.append('')
        out.append('> **경고 — 시트에 없는 변수:** ' + ', '.join(sorted(set(missing)))
                   + '. `snapshot.py` 의 LAYOUT 을 고칠 것.')
    out.append('')
    out.append(END)
    return '\n'.join(out), checks, missing


def build_picks(picks):
    """the yellow cells - the answer to 'what did somebody choose, and when'"""
    lines = ['', '### 3.0 사람이 고른 값 (노란 셀 %d개 중 수치 입력)' % len(picks), '',
             '계산이 만든 값이 아니라 **누군가 정한 값**이다. 다른 PC에서 사양이 바뀌었다면',
             '거의 항상 이 목록 중 하나가 바뀐 것이다.', '', '```']
    for label, var, v, unit in picks:
        if not v:
            continue
        lab = re.sub(r'^[-\s]*', '', label)[:52]
        lines.append('%-54s %-14s %s %s' % (lab, var, v, unit))
    lines += ['```', '']
    return '\n'.join(lines)


def current_block(doc):
    m = re.search(re.escape(BEGIN) + r'.*?' + re.escape(END), doc, re.S)
    return m.group(0) if m else None


def main():
    check_only = '--check' in sys.argv
    vals, picks = read_sheet(SM)
    if '--picks' in sys.argv:
        print(build_picks(picks))
        return 0
    block, checks, missing = build_block(vals)
    doc = io.open(DOC, encoding='utf-8').read()
    cur = current_block(doc)

    if check_only:
        if cur is None:
            print('CLAUDE.md has no generated block - run snapshot.py once')
            return 1
        if cur.strip() != block.strip():
            print('CLAUDE.md section 3 is stale - run snapshot.py')
            return 1
        print('CLAUDE.md section 3 is current')
        return 0

    if cur is None:
        print('no marker block in CLAUDE.md; nothing written.')
        print('Put these two lines around the section 3 code block first:')
        print('  ' + BEGIN)
        print('  ' + END)
        return 1

    doc = doc.replace(cur, block, 1)
    io.open(DOC, 'w', encoding='utf-8').write(doc)

    # what moved since last time - so a session picking up elsewhere can see it
    snap = {k: round(v[0], 6) for k, v in vals.items()}
    picked = {p[1]: (p[2], p[3]) for p in picks if p[2]}
    try:
        prev = json.load(io.open(PREV, encoding='utf-8'))
        before = prev.get('vals')
        before_picks = prev.get('picks', {})
    except Exception:                                        # noqa: BLE001
        before, before_picks = None, {}
    io.open(PREV, 'w', encoding='utf-8').write(
        json.dumps({'vals': snap, 'picks': picked}, ensure_ascii=False, indent=0))

    print('CLAUDE.md section 3 rewritten from the worksheet.')
    print('  values %d · yellow picks %d · checks %d%s'
          % (len(vals), len([p for p in picks if p[2]]), len(checks),
             '' if not missing else ' · MISSING ' + ','.join(sorted(set(missing)))))
    if before is None:
        print('  (no previous snapshot to compare against)')
        return 0
    moved = [(k, before[k], snap[k]) for k in sorted(snap)
             if k in before and before[k] != snap[k]]
    added = [k for k in sorted(snap) if k not in before]
    gone = [k for k in sorted(before) if k not in snap]
    pick_moves = [(k, before_picks[k][0], picked[k][0], picked[k][1])
                  for k in sorted(picked)
                  if k in before_picks and before_picks[k][0] != picked[k][0]]
    if not (moved or added or gone):
        print('  nothing changed since the last snapshot')
        return 0
    if pick_moves:
        print('  a HUMAN changed:')
        for name, a, b, u in pick_moves:
            print('    %-16s %s -> %s %s' % (name, a, b, u))
    print('  changed since the last snapshot:')
    for k, a, b in moved[:40]:
        print('    %-16s %-14g -> %-14g' % (k, a, b))
    if len(moved) > 40:
        print('    ... and %d more' % (len(moved) - 40))
    if added:
        print('    new: ' + ', '.join(added[:20]))
    if gone:
        print('    gone: ' + ', '.join(gone[:20]))
    return 0


if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.exit(main())
