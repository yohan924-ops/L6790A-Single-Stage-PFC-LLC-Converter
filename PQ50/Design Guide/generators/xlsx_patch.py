# -*- coding: utf-8 -*-
"""Edit the ST workbook by rewriting its XML - safely.

openpyxl cannot round-trip this workbook (30 charts, 11 images, 7 comments are
all lost on save), so cells are edited inside the zip. That is fine as long as
three rules hold, and Excel gives no warning when they do not - it just repairs
the file on open and throws the sheet's cell information away.

    1. one <row> must not carry the same r= reference twice
    2. cells inside a <row> must be in ascending column order
    3. xl/calcChain.xml describes the old formula set and must go

This module is what enforces them. set_cell() replaces-or-inserts in the right
place and recomputes spans; validate() walks every row of every sheet and
refuses to write a workbook that breaks rule 1 or 2.

Typical use:

    import xlsx_patch as xp

    z = xp.open_book('...rev0_6.xlsx')
    sheet = z['xl/worksheets/sheet6.xml']
    sheet = xp.set_cell(sheet, 'F108', xp.cell_n('F108', xp.style_of(sheet, 'F108'), '30'))
    z['xl/worksheets/sheet6.xml'] = sheet
    xp.write_book('...rev0_6.xlsx', z)      # validates first, refuses if broken

Run it directly to check a workbook without changing it:

    python xlsx_patch.py "../../Calculation Excel Sheet/L6790_...rev0_6.xlsx"
"""
import io
import os
import re
import sys
import zipfile

CELL_RE = re.compile(r'<c r="([A-Z]+)(\d+)"(?: [^>]*?)?(?:/>|>.*?</c>)', re.S)
ROW_RE = re.compile(r'<row r="(\d+)"[^>]*>.*?</row>', re.S)


# --------------------------------------------------------------- cell builders
def esc(t):
    return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def colnum(ref):
    """'AV122' -> 48"""
    n = 0
    for ch in re.match(r'([A-Z]+)', ref).group(1):
        n = n * 26 + ord(ch) - 64
    return n


def cell_t(ref, style, text):
    """inline string - use this for labels, NOT a shared-string index"""
    return ('<c r="%s" s="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
            % (ref, style, esc(text)))


def cell_f(ref, style, formula):
    """formula with no cached value, so Excel must recalculate it"""
    return '<c r="%s" s="%s"><f>%s</f></c>' % (ref, style, esc(formula))


def cell_n(ref, style, num):
    return '<c r="%s" s="%s"><v>%s</v></c>' % (ref, style, num)


def style_of(xml, ref, default='0'):
    """keep the formatting that is already on the cell being replaced"""
    m = re.search(r'<c r="%s"(?: [^>]*?)?(?:/>|>.*?</c>)' % ref, xml, re.S)
    if not m:
        return default
    s = re.search(r's="(\d+)"', m.group(0))
    return s.group(1) if s else default


# ------------------------------------------------------------------- the edit
def ensure_row(xml, row):
    """Make sure <row r="row"> exists, inserting it in ascending order.

    set_cell deliberately refuses to create rows - appending one in the wrong
    place puts sheetData out of order, which Excel repairs by discarding data.
    """
    if re.search(r'<row r="%d"[^>]*[>/]' % row, xml):
        return xml
    body = re.search(r'<sheetData\s*/?>', xml)
    if not body:
        raise KeyError('no sheetData')
    if body.group(0).endswith('/>'):            # empty sheet
        return xml[:body.start()] + '<sheetData><row r="%d"></row></sheetData>' % row \
            + xml[body.end():]
    after = None
    for m in re.finditer(r'<row r="(\d+)"', xml):
        if int(m.group(1)) > row:
            after = m.start()
            break
    new = '<row r="%d"></row>' % row
    if after is None:
        end = xml.index('</sheetData>')
        return xml[:end] + new + xml[end:]
    return xml[:after] + new + xml[after:]


def set_cell(xml, ref, new):
    """Replace ref if it exists, otherwise insert it in ascending column order.

    Appending blindly is what corrupted the workbook once already: the cell was
    already present further left, so the row ended up with two of it.
    """
    row = int(re.search(r'(\d+)$', ref).group(1))
    m = re.search(r'<row r="%d"[^>]*>.*?</row>' % row, xml, re.S)
    if not m:
        raise KeyError('row %d does not exist - this function does not create rows' % row)
    block = m.group(0)
    tag = re.match(r'<row [^>]*>', block).group(0)
    body = block[len(tag):-len('</row>')]
    cells = [(c.group(1) + c.group(2), c.group(0)) for c in CELL_RE.finditer(body)]
    cells = [c for c in cells if c[0] != ref]
    cells.append((ref, new))
    cells.sort(key=lambda c: colnum(c[0]))
    tag = re.sub(r'spans="[^"]*"',
                 'spans="%d:%d"' % (colnum(cells[0][0]), colnum(cells[-1][0])), tag)
    return xml[:m.start()] + tag + ''.join(c[1] for c in cells) + '</row>' + xml[m.end():]


# -------------------------------------------------------------- the safety net
def validate(parts):
    """Walk every row of every sheet. Returns a list of problems, empty if clean."""
    bad = []
    for name, data in parts.items():
        if not re.match(r'xl/worksheets/sheet\d+\.xml$', name):
            continue
        xml = data.decode('utf-8') if isinstance(data, bytes) else xml_text(data)
        for rm in ROW_RE.finditer(xml):
            row = rm.group(1)
            refs = [c.group(1) + c.group(2) for c in CELL_RE.finditer(rm.group(0))]
            seen = set()
            for r in refs:
                if r in seen:
                    bad.append('%s row %s: duplicate cell %s' % (name, row, r))
                seen.add(r)
            nums = [colnum(r) for r in refs]
            if nums != sorted(nums):
                bad.append('%s row %s: cells out of column order (%s)'
                           % (name, row, ' '.join(refs[:12])))
    return bad


def xml_text(x):
    return x if isinstance(x, str) else x.decode('utf-8')


# ------------------------------------------------------------------- zip level
def open_book(path):
    """Read the whole workbook into {name: bytes}. Keeps charts, images, comments."""
    with zipfile.ZipFile(path) as z:
        order = [i.filename for i in z.infolist()]
        parts = {n: z.read(n) for n in order}
    parts['__order__'] = order
    return parts


def write_book(path, parts, drop_calcchain=True, full_calc=True):
    """Validate, then write. Refuses to write a workbook that breaks the rules."""
    order = [n for n in parts.get('__order__', sorted(parts)) if n != '__order__']
    payload = {n: parts[n] for n in order}

    problems = validate(payload)
    if problems:
        raise ValueError('refusing to write - %d structure problem(s):\n  %s'
                         % (len(problems), '\n  '.join(problems[:20])))

    if full_calc and 'xl/workbook.xml' in payload:
        wb = xml_text(payload['xl/workbook.xml'])
        if 'fullCalcOnLoad' not in wb:
            wb = re.sub(r'<calcPr ([^>]*?)/>', r'<calcPr \1 fullCalcOnLoad="1"/>', wb, count=1)
        payload['xl/workbook.xml'] = wb.encode('utf-8')

    if drop_calcchain:
        # the chain describes the OLD formula set; leaving it makes Excel repair
        payload.pop('xl/calcChain.xml', None)
        order = [n for n in order if n != 'xl/calcChain.xml']
        if '[Content_Types].xml' in payload:
            ct = re.sub(r'<Override PartName="/xl/calcChain\.xml"[^>]*/>', '',
                        xml_text(payload['[Content_Types].xml']))
            payload['[Content_Types].xml'] = ct.encode('utf-8')
        if 'xl/_rels/workbook.xml.rels' in payload:
            rels = re.sub(r'<Relationship[^>]*Target="calcChain\.xml"[^>]*/>', '',
                          xml_text(payload['xl/_rels/workbook.xml.rels']))
            payload['xl/_rels/workbook.xml.rels'] = rels.encode('utf-8')

    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as out:
        for n in order:
            d = payload[n]
            out.writestr(n, d if isinstance(d, bytes) else d.encode('utf-8'))
    return len(order)


def backup(path):
    """Copy to BACKUP_<name> beside the original, never overwriting an older one."""
    d, base = os.path.split(path)
    dst = os.path.join(d, 'BACKUP_' + base)
    i = 1
    while os.path.exists(dst):
        i += 1
        dst = os.path.join(d, 'BACKUP_%d_%s' % (i, base))
    with open(path, 'rb') as fh, open(dst, 'wb') as out:
        out.write(fh.read())
    return dst


# ------------------------------------------------------------------------- CLI
if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        target = os.path.join(root, 'Calculation Excel Sheet',
                              'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
    parts = open_book(target)
    problems = validate({k: v for k, v in parts.items() if k != '__order__'})
    sheets = sum(1 for n in parts if re.match(r'xl/worksheets/sheet\d+\.xml$', n))
    print('%s\n  parts %d   sheets %d   calcChain %s'
          % (os.path.basename(target), len(parts) - 1, sheets,
             'present' if 'xl/calcChain.xml' in parts else 'absent'))
    if problems:
        print('  structure problems: %d' % len(problems))
        for p in problems[:20]:
            print('    ' + p)
        sys.exit(1)
    print('  structure problems: 0   VERDICT OK')
