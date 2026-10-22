# -*- coding: utf-8 -*-
"""Insert rows into one sheet of the ST workbook, in the XML - what Excel's "Insert rows"
does, for the parts this workbook has (2026-10-22, gate_xl.py: the gate-drive rows go
INSIDE Power Components' switch section, so the rows under it move down).

    insert_rows(parts, 'Power Components', at=81, n=22)

Moves every row >= at of that sheet down by n and fixes everything that points at them:
  - the sheet's own cells, rows, merged cells, dimension, selection
  - every formula in every sheet: references to that sheet ('Power Components'!D96, ranges
    too), and in the sheet itself its unqualified references; string literals untouched
  - its drawing anchors (pictures) and its comments (comments part + VML anchors)
Refuses (raises) on parts it does not handle - shared or array formulas in the sheet,
conditional formatting, data validation, defined names or charts that name the sheet - so
a workbook that grew one of those cannot be shifted silently wrong.

Check after use: recalculate before / after copies and compare every cell (gate_xl.py
prints how).
"""
import re

from measured200_xl import sheet_parts

REF = re.compile(r"(?<![A-Za-z0-9_.$'])(?:('[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!)?"
                 r"(\$?[A-Z]{1,3})(\$?)(\d+)(?::(\$?[A-Z]{1,3})(\$?)(\d+))?(?![0-9A-Za-z_(!])")


def _shift_formula(f, sheet, local, at, n):
    """f as it stands in the XML (&amp; etc. left alone - no reference contains them)"""
    quoted = "'%s'" % sheet

    def fix(m):
        sh = m.group(1)
        mine = (sh is None and local) or sh == quoted or sh == sheet
        if not mine:
            return m.group(0)
        r1 = int(m.group(4))
        r1 = r1 + n if r1 >= at else r1
        out = (sh + '!' if sh else '') + m.group(2) + m.group(3) + str(r1)
        if m.group(5):
            r2 = int(m.group(7))
            r2 = r2 + n if r2 >= at else r2
            out += ':' + m.group(5) + m.group(6) + str(r2)
        return out
    parts = re.split(r'("[^"]*")', f)            # keep string literals as they are
    return ''.join(p if p.startswith('"') else REF.sub(fix, p) for p in parts)


def _shift_formulas(xml, sheet, local, at, n):
    return re.sub(r'(<f(?: [^>]*)?>)(.*?)(</f>)',
                  lambda m: m.group(1) + _shift_formula(m.group(2), sheet, local, at, n) + m.group(3),
                  xml, flags=re.S)


def _cellref(ref, at, n):
    m = re.fullmatch(r'([A-Z]+)(\d+)', ref)
    r = int(m.group(2))
    return m.group(1) + str(r + n if r >= at else r)


def _sqref(s, at, n):
    return ' '.join(':'.join(_cellref(c, at, n) for c in rng.split(':')) for rng in s.split())


def insert_rows(parts, sheet, at, n):
    sp = sheet_parts(parts)
    part = sp[sheet]
    xml = parts[part].decode('utf-8')
    for bad in ('t="shared"', 't="array"', '<conditionalFormatting', '<dataValidation',
                '<hyperlink '):
        if bad in xml:
            raise ValueError('%s: %s not handled' % (sheet, bad))
    wbx = parts['xl/workbook.xml'].decode('utf-8')
    if re.search(r"<definedName[^>]*>[^<]*'?%s'?!" % re.escape(sheet), wbx):
        raise ValueError('a defined name refers to %s' % sheet)
    for k, v in parts.items():
        if k.startswith('xl/charts/') and ("'%s'!" % sheet) in v.decode('utf-8', 'ignore'):
            raise ValueError('%s refers to %s' % (k, sheet))

    # ---- the sheet itself: formulas first (they read the OLD row numbers), then addresses
    xml = _shift_formulas(xml, sheet, True, at, n)
    xml = re.sub(r'<row r="(\d+)"', lambda m: '<row r="%d"' % (int(m.group(1)) + n
                 if int(m.group(1)) >= at else int(m.group(1))), xml)
    xml = re.sub(r'<c r="([A-Z]+\d+)"', lambda m: '<c r="%s"' % _cellref(m.group(1), at, n), xml)
    xml = re.sub(r'<mergeCell ref="([^"]+)"/>', lambda m: '<mergeCell ref="%s"/>' % _sqref(m.group(1), at, n), xml)
    xml = re.sub(r'<dimension ref="([^"]+)"/>', lambda m: '<dimension ref="%s"/>' % _sqref(m.group(1), at, n), xml)
    xml = re.sub(r'(<selection [^>]*?activeCell=")([A-Z]+\d+)(" sqref=")([^"]+)"',
                 lambda m: m.group(1) + _cellref(m.group(2), at, n) + m.group(3) + _sqref(m.group(4), at, n) + '"', xml)
    parts[part] = xml.encode('utf-8')

    # ---- every other sheet: only references that name this sheet
    for name, p in sp.items():
        if p == part:
            continue
        x = parts[p].decode('utf-8')
        y = _shift_formulas(x, sheet, False, at, n)
        if y != x:
            parts[p] = y.encode('utf-8')

    # ---- the sheet's drawing and comments
    rels_name = part.replace('worksheets/', 'worksheets/_rels/') + '.rels'
    rels = parts.get(rels_name, b'').decode('utf-8')
    for tgt in re.findall(r'Target="([^"]+)"', rels):
        tp = 'xl/' + tgt.replace('../', '')
        if tp not in parts:
            continue
        t = parts[tp].decode('utf-8')
        if 'drawings/drawing' in tp and tp.endswith('.xml'):
            t = re.sub(r'(<xdr:(?:from|to)>.*?<xdr:row>)(\d+)(</xdr:row>)',
                       lambda m: m.group(1) + str(int(m.group(2)) + n if int(m.group(2)) >= at - 1
                                                  else int(m.group(2))) + m.group(3), t, flags=re.S)
        elif 'comments' in tp:
            t = re.sub(r'<comment ref="([A-Z]+\d+)"', lambda m: '<comment ref="%s"' % _cellref(m.group(1), at, n), t)
        elif tp.endswith('.vml'):
            t = re.sub(r'<x:Row>(\d+)</x:Row>', lambda m: '<x:Row>%d</x:Row>' % (
                int(m.group(1)) + n if int(m.group(1)) >= at - 1 else int(m.group(1))), t)

            def anchor(m):
                v = [int(s) for s in m.group(1).split(',')]
                for i in (2, 6):
                    if v[i] >= at - 1:
                        v[i] += n
                return '<x:Anchor>%s</x:Anchor>' % ', '.join(str(s) for s in v)
            t = re.sub(r'<x:Anchor>\s*([\d, ]+?)\s*</x:Anchor>', anchor, t)
        parts[tp] = t.encode('utf-8')
    return parts
