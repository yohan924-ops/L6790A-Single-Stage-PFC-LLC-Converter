import re
# -*- coding: utf-8 -*-
"""벤더 사양서(Transformer_Spec_*.xlsx)의 숫자를 변형 시트에서 다시 계산해 대조한다.

build_trans_spec.py 의 VARIANTS 는 손으로 박은 상수 표다.  시트를 고치면
사양서는 조용히 낡는다 - 벤더에 나가는 문서라서 그게 가장 비싼 실수다.
이 스크립트는 상수 하나하나를 Smath/variants/*.sm 에서 역산해 비교한다.
"""
import io
import math
import os
import sys
import xml.etree.ElementTree as ET

import smresult

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
SMDIR = os.path.join(HERE, '..', '..', 'Smath', 'variants')


def sheet(path):
    """-> {변수명: (표시단위 값, 단위)}"""
    raw = open(path, encoding='utf-8').read()
    root = ET.fromstring(
        raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))
    out = {}
    for r in root.iter('region'):
        m = r.find('math')
        if m is None:
            continue
        i, res = m.find('input'), m.find('result')
        if i is None:
            continue
        e = list(i)
        if not (e and e[0].get('type') == 'operand'):
            continue
        c = m.find('contract')
        u = list(c)[0].text if c is not None else ''
        if res is not None:
            v = smresult.value(res)
        else:
            # 입력 셀은 <result> 가 없다 (규칙 D11).  `X := 숫자` 만 읽는다.
            v = None
            if (len(e) == 3 and e[1].get('type') == 'operand'
                    and e[2].text == ':'):
                try:
                    v = float(e[1].text)
                except (TypeError, ValueError):
                    v = None
        if v is not None:
            out.setdefault(e[0].text, (v, u))
    return out


def khz(s, k):
    """<result> 는 이미 표시 단위 값이다 (규칙 E24).  kHz 로 맞춘다."""
    v, u = s[k]
    return v * {'kHz': 1.0, 'Hz': 1e-3, 'MHz': 1e3}[u]


def derive(s):
    """사양서에 실리는 값을 시트 변수에서 만든다.  전부 '트랜스포머 1개당'."""
    g = lambda k: s[k][0]
    Nx = g('N.x')
    Np, Ns = g('N.p'), g('N.s')
    Lopen = g('L.r') + g('L.m')                     # 세트 (uH)
    Bpk = g('B.pk') / 1000.0                        # T, A.e_mm 기준
    Ae_now = g('A.e_mm')
    return dict(
        Np=int(round(Np)), Ns=int(round(Ns)), Nx=int(round(Nx)),
        # 보조 권선은 세트 전체로 n.aux*N.s 턴(시트 N.aux)이다.  코어가 여럿이면
        # 유닛마다 같은 수를 감고 필요한 만큼만 직렬로 쓴다 - 유닛당 턴수는
        # 올림이다(7.5:1 3코어: 2 T 가 필요하니 유닛마다 1 T, 둘만 직렬).
        Naux=int(math.ceil(g('n.aux') * Ns / Nx - 1e-9)),
        Naux_set=int(round(g('n.aux') * Ns)),
        Ivcc=g('I.VCC'),
        Lopen=Lopen / Nx,                           # uH/개
        Lshort=g('L.r') / Nx,                       # uH/개
        Ipri_rms=g('I.pri_lc'), Ipri_pk=g('I.Lr_pk'),      # 1차 직렬 -> 나누지 않는다
        Isec_rms=g('I.diode_lc') / Nx, Isec_pk=g('I.sec_pk') / Nx,
        Ae=Ae_now * Bpk / 0.20,                     # B <= 0.20 T 가 되는 A.e
        ILm_pk=g('I.Lm_pk'),
        # 개방 시험(다른 권선 OPEN)에서 동작 자속 B.pk 와 같은 자속을 만드는 DC 전류
        Ieq=g('I.sat_eq'), Isat_spec=g('I.sat_spec'),
        kOVsat=g('k.OVsat'),
        fmin=khz(s, 'f.Min'), fmax=khz(s, 'f.sw.b'),
        kfloor=g('k.floor'),
        nT=g('n.T_act'),
    )


def close(a, b, tol):
    return abs(a - b) <= tol * max(1.0, abs(b))


def spec_from_xlsx(path):
    """벤더에 나가는 사양서를 그대로 읽는다 - 빌더의 상수가 아니라 결과물을 본다.

    셀 번지를 박아 두면 사양서 행이 한 줄만 밀려도 조용히 엉뚱한 칸을 읽는다
    (실제로 그렇게 깨졌다).  라벨로 행을 찾고 그 행에서 값을 집는다.
    """
    import openpyxl
    ws = openpyxl.load_workbook(path, data_only=True).active
    grid = {}
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.strip():
                grid[(c.row, c.column)] = c.value.strip()

    def find(label):
        """라벨이 든 행 번호 -> 그 행의 {열: 문자열}"""
        for (r, col), t in sorted(grid.items()):
            if t.startswith(label):
                return {cc: v for (rr, cc), v in grid.items() if rr == r}
        raise KeyError('사양서에 "%s" 행이 없다: %s' % (label, os.path.basename(path)))

    def num(row, col):
        return float(re.findall(r'[\d.]+', row[col])[0])

    wnd = lambda lab: find(lab)
    np_, ns_, na_ = wnd('NP1'), wnd('NS2'), wnd('NAUX')
    ins = find('Creepage')
    return dict(
        Np=int(num(np_, 5)), Ns=int(num(ns_, 5)), Naux=int(num(na_, 5)),
        creep=num(ins, 5), clear=num(find('Clearance'), 5),
        wire=find('NP1 wire')[5],
        Lopen=num(find('INDUCTANCE'), 5),
        Lshort=num(find('LEAKAGE INDUCTANCE'), 5),
        Isat=num(find('D.C OVERLAP'), 6),
        Ae=num(find('Core effective area'), 5),
        Ipri=np_[6], Isec=ns_[6],
        fsw=find('Switching frequency')[5],
    )


def main():
    import re as _re
    global INS
    import insulation                   # 절연 요구치의 유일한 출처
    INS = insulation.req()
    bad = 0
    for var in ('7p5to1', '7p5to1_x1', '8to1', '6to1'):
        smp = os.path.join(SMDIR, 'L6790A_%s.sm' % var)
        xlp = os.path.join(HERE, '..', '..', 'Calculation Excel Sheet',
                           'variants', 'Transformer_Spec_%s.xlsx' % var)
        # 없는 파일 판정은 이 변형에만 걸어야 한다.  누적 bad 를 보고 continue
        # 하면 앞 변형이 하나라도 어긋난 순간 뒤 변형을 통째로 건너뛴다 -
        # 실제로 (지금은 지운) 9to1 하나 때문에 나머지 셋이 검사되지 않고 있었다.
        missing = [q for q in (smp, xlp) if not os.path.exists(q)]
        for q in missing:
            print('%-8s  없음: %s' % (var, os.path.normpath(q)))
        bad += len(missing)
        if missing:
            continue
        d, spec = derive(sheet(smp)), spec_from_xlsx(xlp)
        print('=' * 78)
        print('%s   (세트 권선비 %.4g,  유닛 %d : %d)'
              % (var, d['nT'], d['Np'], d['Ns']))
        print('=' * 78)
        for name, have, want, tol in [
                ('Np  1차 턴수',        spec['Np'],     d['Np'],     0.0),
                ('Ns  2차 턴수',        spec['Ns'],     d['Ns'],     0.0),
                ('Naux 보조 턴수/유닛',  spec['Naux'],   d['Naux'],   0.0),
                ('연면거리 mm',          spec['creep'],  INS['creep'], 0.0),
                ('공간거리 mm',          spec['clear'],  INS['clearance'], 0.0),
                ('L.open  uH/개',       spec['Lopen'],  d['Lopen'],  0.005),
                ('L.short uH/개',       spec['Lshort'], d['Lshort'], 0.005),
                ('A.e  mm2 (B<=0.2T)',  spec['Ae'],     d['Ae'],     0.01)]:
            ok = close(float(have), float(want), tol)
            bad += 0 if ok else 1
            print('  %-20s 사양서 %-12s 시트 %-12.4g %s'
                  % (name, have, want, 'same' if ok else '** DIFF'))
        num = lambda t: [float(x) for x in _re.findall(r'[\d.]+', t)]
        for name, txt, wants, tol in [
                ('I.pri  rms/pk A', spec['Ipri'], [d['Ipri_rms'], d['Ipri_pk']], 0.01),
                ('I.sec  rms/pk A', spec['Isec'], [d['Isec_rms'], d['Isec_pk']], 0.01),
                ('f.sw   min/max kHz', spec['fsw'], [d['fmin'], d['fmax']], 0.01)]:
            have = num(txt)
            ok = len(have) == len(wants) and all(
                close(h, w, tol) for h, w in zip(have, wants))
            bad += 0 if ok else 1
            print('  %-20s 사양서 %-12s 시트 %-12s %s'
                  % (name, '/'.join('%g' % h for h in have),
                     '/'.join('%.4g' % w for w in wants), 'same' if ok else '** DIFF'))
        # 개방 시험은 2차 기자력 상쇄가 없어 같은 전류로도 자속이 훨씬 크다.
        # 1차 피크 전류와 비교하면 안 된다 - 동작 자속의 등가 DC 전류가 기준이다.
        ok = spec['Isat'] >= d['Ieq']
        bad += 0 if ok else 1
        print('  %-20s 사양서 %-12g 자속등가 %-12.4g %s  (여유 %.0f %%)'
              % ('I.sat  개방시험 A', spec['Isat'], d['Ieq'],
                 'same' if ok else '** 동작보다 헐거움',
                 100 * (spec['Isat'] / d['Ieq'] - 1)))
        #  개방 시험에서는 2차가 없으므로 1차 전류 전체가 자화 전류다.  따라서
        #  동작 자속을 재현하는 DC 전류는 자화전류 피크와 같아야 한다 - 그것이
        #  아니면 분모에 틀린 인덕턴스가 들어간 것이다.  L.open 을 쓰면 정확히
        #  L.mu/L.open 배만큼 작게 나오고, 2026-09-21 까지 실제로 그랬다.
        ok = close(d['Ieq'], d['ILm_pk'], 0.002)
        bad += 0 if ok else 1
        print('  %-20s %-12.4g 자화피크 %-12.4g %s'
              % ('I.sat_eq = I.Lm_pk?', d['Ieq'], d['ILm_pk'],
                 'same' if ok else '** 분모 인덕턴스가 틀렸다'))
        #  시험 전류가 탱크 피크보다 낮은 것은 정상이고 요구사항이 아니다 -
        #  개방시험은 전류 시험이 아니라 자속 시험이다.  판정해야 하는 것은
        #  "OVP2 에서의 자화전류를 덮는가" 이고, 그것이 이 설계의 근거다.
        #  the reinforced insulation is carried by the primary wire since
        #  2026-09-25 (insulation.checks): the spec must ask for it
        ok = 'TIW' in spec['wire']
        bad += 0 if ok else 1
        print('  %-20s 사양서 %-12s %s' % ('NP1 선재', spec['wire'],
                                        'same' if ok else '** TIW 요구 없음'))
        want = d['ILm_pk'] * d['kOVsat']
        ok = spec['Isat'] >= want - 0.5
        bad += 0 if ok else 1
        print('  %-20s 사양서 %-12g OVP2자화 %-12.4g %s  (OVP2 는 V.out 의 %.3f 배)'
              % ('I.sat vs OVP2', spec['Isat'], want,
                 'same' if ok else '** OVP2 자속을 못 덮는다', d['kOVsat']))
    print()
    print('불일치 %d 건' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
