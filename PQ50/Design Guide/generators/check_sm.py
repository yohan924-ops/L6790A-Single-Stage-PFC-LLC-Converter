# -*- coding: utf-8 -*-
"""Geometry and content checks for a generated .sm worksheet.

A worksheet that opens but has regions on top of each other, or running off the
right edge of the paper, is worse than one that does not open at all - the
damage is silent.  Run this after every build.

    python check_sm.py ../../Smath/L6790A_SingleStage_PF_LLC_Design_Guide.sm
"""
import re
import sys
import xml.etree.ElementTree as ET

# paper size is read from the worksheet itself - the user may switch A4 <-> A3
# what the design sheet is allowed to call: the scalar set that both known-good
# worksheets use, plus the names a plot matrix needs.  'for' and 'line' were in
# here for the section 16.6 loop block; that block is gone, because a matrix
# filled inside for() does not draw in a ZedGraph pane.  They stay allowed - a
# variant sheet may still use them - but nothing emits them today.
ALLOWED = {'sqrt', 'abs', 'ln', 'exp', 'atan', 'cos', 'sin',
           'el', 'line', 'for', 'range',
           'eval', 'augment', 'vectorize', 'sys'}
# regions inside a collapsed <area> still carry absolute coordinates, so they
# are checked for overlap exactly like the visible ones.


def main(path, extra=()):
    raw = open(path, encoding='utf-8').read()
    bad = 0
    m = re.search(r'<paper id="(\d+)" orientation="(\w+)" width="(\d+)" height="(\d+)"', raw)
    PAGE_W, PAGE_H = (int(m.group(3)), int(m.group(4))) if m else (1169, 827)
    m2 = re.search(r'<margins left="(\d+)"', raw)
    MARGIN = int(m2.group(1)) if m2 else 19
    print('  paper          %s %s  %d x %d px, margin %d'
          % ({'8': 'A3', '9': 'A4', '63': 'A3+ (custom)'}.get(m.group(1), 'paper id ' + m.group(1)) if m else '?',
             m.group(2) if m else '?', PAGE_W, PAGE_H, MARGIN))

    try:
        root = ET.fromstring(
            raw.replace(' xmlns="http://smath.info/schemas/worksheet/1.0"', ''))
    except ET.ParseError as e:
        print('  XML            ** NOT WELL FORMED:', e)
        return 1
    print('  XML            well formed')

    regs = []
    for r in root.iter('region'):
        if r.get('left') is None or r.get('top') is None:
            continue
        x, y = int(r.get('left')), int(r.get('top'))
        w, h = int(r.get('width') or 0), int(r.get('height') or 0)
        kind = ('plot' if r.find('plot') is not None else
                'zedgraph' if r.find('zedgraph') is not None else
                'picture' if r.find('picture') is not None else
                'text' if r.find('text') is not None else 'math')
        regs.append((x, y, w, h, kind))
    regs.sort(key=lambda r: (r[1], r[0]))
    print(f'  regions        {len(regs)}')

    over = 0
    for i in range(len(regs)):
        xi, yi, wi, hi, ki = regs[i]
        for j in range(i + 1, len(regs)):
            xj, yj, wj, hj, kj = regs[j]
            if yj >= yi + hi:
                break
            if xi < xj + wj and xj < xi + wi and yi < yj + hj and yj < yi + hi:
                over += 1
                if over <= 6:
                    print(f'    overlap {ki}@({xi},{yi},{wi}x{hi}) '
                          f'vs {kj}@({xj},{yj},{wj}x{hj})')
    print(f'  overlaps       {over}')
    bad += over

    # --- does anything cross a page break?
    # SMath shades the part of a region that has spilled onto the next sheet.
    # That grey band is the only warning the user gets that something will
    # print cut in half, and it is invisible to every other check here: the
    # region is inside the paper, inside the margins, and overlaps nothing.
    # A region taller than a whole page is not counted - it has to cross.
    # Two corrections, both measured against the printed PDF. A COLLAPSED
    # AREA takes no room - SMath draws one grey line and pulls what follows
    # up - so the break does not fall at a multiple of anything in absolute
    # y. And a page holds PAGE_CONTENT, not the paper height: the margins
    # and the footer come out of it first.
    # read from the builder, so the two cannot drift apart. PAGE_CONTENT
    # and PAGE_ORIGIN were measured on L6790A_ruler.sm - see smsheet.
    from smsheet import Sheet as _S
    PAGE_CONTENT, PAGE_ORIGIN = _S.PAGE_CONTENT, _S.PAGE_ORIGIN
    SAFE_TOP, SAFE_BOT = _S.SAFE_TOP, _S.SAFE_BOT
    folds = []

    def _walk(node):
        for ch in node:
            if ch.tag != 'region':
                continue
            a = ch.find('area')
            if a is not None and a.get('collapsed') == 'true':
                # exactly what the builder counts as hidden: the area's own
                # top to its terminator, not the extent of its children
                term = [int(x.get('top')) for x in ch.iter('region')
                        if x.find('area') is not None
                        and x.find('area').get('terminator') == 'true']
                if term and ch.get('top'):
                    folds.append((int(ch.get('top')), max(term)))
            _walk(ch)

    _walk(root.find('regions') if root.find('regions') is not None else root)
    folds.sort()
    # MERGE overlapping spans. One collapsed block contains another here,
    # and counting the inner one separately subtracts the same 814 px of
    # paper twice - which put every page break below it three quarters of a
    # page early. Merging is right whether or not the builder ever nests
    # again, so this does not depend on the builder behaving.
    _mg = []
    for _a, _b in folds:
        if _mg and _a <= _mg[-1][1]:
            _mg[-1][1] = max(_mg[-1][1], _b)
        else:
            _mg.append([_a, _b])
    folds = [(_a, _b) for _a, _b in _mg]

    def _vy(y):
        out = y
        for a, b in folds:
            if b <= y:
                out -= (b - a)
            elif a < y:
                out -= (y - a)
        return out

    inside = set()
    for a, b in folds:
        for x, y, w, h, k in regs:
            if a <= y < b:
                inside.add((x, y, w, h, k))
    straddle = []
    for r in regs:
        x, y, w, h, k = r
        if h <= 0 or h > PAGE_CONTENT or r in inside:
            continue
        _p = (_vy(y) - PAGE_ORIGIN) % PAGE_CONTENT
        if _p + h > PAGE_CONTENT:
            straddle.append(r)
    for r in straddle[:6]:
        print('    crosses a page break: %s@(%d,%d,%dx%d) - visible y %d, '
              'page %d ends at %d'
              % (r[4], r[0], r[1], r[2], r[3], _vy(r[1]),
                 _vy(r[1]) // PAGE_CONTENT + 1,
                 (_vy(r[1]) // PAGE_CONTENT + 1) * PAGE_CONTENT))
    print(f'  page straddles {len(straddle)}   (page holds {PAGE_CONTENT} px, '
          f'{len(folds)} folds hide {sum(b - a for a, b in folds)} px)')
    bad += len(straddle)

    # "0 straddles" is not the same as "safe". Every region height here is
    # an ESTIMATE of what SMath will draw, so a region that finishes four
    # pixels above the break is one bad estimate away from crossing - and
    # when it crosses, SMath moves it to the next page and leaves its label
    # behind, which is how a row gets separated from its own value. Report
    # the tightest clearance so the margin is a number somebody can watch,
    # not something to be measured again by hand after the next surprise.
    room = []
    for x, y, w, h, k in regs:
        if h <= 0 or h > PAGE_CONTENT or (x, y, w, h, k) in inside:
            continue
        room.append((PAGE_CONTENT
                     - ((_vy(y) - PAGE_ORIGIN) % PAGE_CONTENT + h), k))
    if room:
        room.sort()
        print('  seam clearance  tightest %d px (%s), bands %d top / %d bottom'
              % (room[0][0], room[0][1], SAFE_TOP, SAFE_BOT))
        if room[0][0] < min(SAFE_TOP, SAFE_BOT):
            print('    ** something finishes inside the bottom band')
            bad += 1

    off = [r for r in regs if r[0] + r[2] > PAGE_W - MARGIN]
    for r in off[:6]:
        print(f'    past the right margin: {r[4]}@({r[0]},{r[1]},{r[2]}x{r[3]}) '
              f'ends at {r[0] + r[2]} > {PAGE_W - MARGIN}')
    print(f'  right overflow {len(off)}')
    bad += len(off)

    # --- would SMath re-wrap any <p>?  That is what actually caused the
    # overlaps: a paragraph wider than its region grows an extra rendered line
    # that the declared height does not account for.  0.58 px/char per font
    # pixel is the value measured on the rendered PDF (0.58); 0.60 here so the
    # check trips before the real thing does.
    # This check only means anything on a FRESHLY GENERATED file. Once SMath
    # saves the worksheet it shrinks every text region to its content, so the
    # declared width equals the rendered width and the test would flag
    # everything. <revision> is 1 straight out of the builder and 2+ after
    # SMath has written the file.
    rev = re.search(r'<revision>(\d+)</revision>', raw)
    smath_saved = bool(rev) and int(rev.group(1)) > 1
    rewrap = 0
    for r in root.iter('region'):
        if smath_saved:
            break
        t = r.find('text')
        if t is None or r.get('width') is None:
            continue
        w = int(r.get('width'))
        fs = float(r.get('fontSize') or 10)
        for para in t.iter('p'):
            txt = ''.join(para.itertext())
            need = -(-int(len(txt) * 0.60 * fs) // max(1, w - 8))
            if need > 1:
                rewrap += 1
                if rewrap <= 6:
                    print(f'    would re-wrap into {need} lines '
                          f'(w={w}, size={fs:.0f}): {txt[:70]}...')
    print('  text re-wrap    %s' % ('n/a - SMath has re-saved this file'
                                    if smath_saved else rewrap))
    bad += rewrap

    funcs = sorted(set(re.findall(r'type="function" args="\d+">([^<]+)<', raw)))
    stray = [f for f in funcs if f not in ALLOWED and f not in extra]
    print(f'  functions      {funcs}')
    if stray:
        print(f'    ** not in the confirmed set: {stray}')
    bad += len(stray)

    # What PRINTS, not how tall the file is. A collapsed area takes no
    # paper, so the absolute height counted 58 pages for a sheet that came
    # out of the printer as 40 - and 58 was the number the documentation
    # repeated. Divide the VISIBLE height by what a page holds, which is
    # the same arithmetic the page-straddle test above uses.
    ybot = max((y + h) for x, y, w, h, k in regs)
    pages = -(-(_vy(ybot) - PAGE_ORIGIN) // PAGE_CONTENT)
    print(f'  height         {ybot} px, {_vy(ybot)} px of it printed '
          f'=  {pages} pages')
    print(f'  plots {sum(1 for r in regs if r[4] == "plot")}   '
          f'zedgraph {sum(1 for r in regs if r[4] == "zedgraph")}   '
          f'pictures {sum(1 for r in regs if r[4] == "picture")}   '
          f'yellow inputs {raw.count("#ffff80")}')
    print(f'  VERDICT        {"OK" if bad == 0 else str(bad) + " PROBLEM(S)"}')
    return bad


if __name__ == '__main__':
    # --allow eval,augment,vectorize   for a sheet that is trying something out
    argv = sys.argv[1:]
    allow = ()
    if '--allow' in argv:
        k = argv.index('--allow')
        allow = tuple(x.strip() for x in argv[k + 1].split(',') if x.strip())
        del argv[k:k + 2]
    sys.exit(1 if main(argv[0], extra=allow) else 0)
