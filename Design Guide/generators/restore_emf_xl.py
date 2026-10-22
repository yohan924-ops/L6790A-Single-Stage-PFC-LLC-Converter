# -*- coding: utf-8 -*-
"""Put back the three EMF pictures the ST tool carries and our books lost (2026-10-22, user:
"the circuit images are gone - VCO and such - take them from the original file").

The ST original has, besides the PNGs, two EMF drawings used three times:
    Device Setting   Picture 75  (image9.emf)  at I19   the oscillator (VCO) circuit
    Device Setting   Picture 3   (image8.emf)  at I108  the pin configuration
    BOM&Schematics   Picture 71  (image8.emf)  at C62   the same pin configuration
openpyxl drops EMF/WMF on load ("image format is not supported"), which is how an early copy
of the workbook lost them.  The rows those sheets anchor to are the same in our books (checked
2026-10-22: Device Setting 18-20 and 104-112, BOM 58-65 line up), so the original anchors are
copied as they are - only the relationship id and the shape id are renumbered.

    python restore_emf_xl.py          all three books, idempotent (anchor name present)
"""
import os
import re
import zipfile

import xlsx_patch as X
from measured200_xl import sheet_parts

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet'))
ORIG = os.path.join(XL, 'ST_ORIGINAL_LGE_670W_workbook_04092026_unencrypted.xlsx')
BOOKS = ['GUIDE_PQ50_657W_workbook_rev0_6_unencrypted.xlsx',
         os.path.join('variants', '3CORE_670W_workbook_unencrypted.xlsx'),
         os.path.join('variants', 'BENCH_200W_LGE_workbook_unencrypted.xlsx')]
WANT = (('Device Setting', 'Picture 75'), ('Device Setting', 'Picture 3'), ('BOM&Schematics', 'Picture 71'))
ANCHOR = re.compile(r'<xdr:(twoCellAnchor|oneCellAnchor|absoluteAnchor)\b.*?</xdr:\1>', re.S)


def drawing_of(parts, sp, sheet):
    rels = parts['xl/worksheets/_rels/' + sp[sheet].split('/')[-1] + '.rels'].decode('utf-8')
    d = re.search(r'Target="\.\./(drawings/drawing\d+\.xml)"', rels).group(1)
    return 'xl/' + d, 'xl/' + d.replace('drawings/', 'drawings/_rels/') + '.rels'


def originals():
    z = zipfile.ZipFile(ORIG)
    parts = {n: z.read(n) for n in z.namelist()}
    sp = sheet_parts(parts)
    out = {}
    for sheet, name in WANT:
        dpath, drels = drawing_of(parts, sp, sheet)
        rid = {m.group(1): m.group(2) for m in
               re.finditer(r'Id="([^"]+)"[^>]*Target="([^"]+)"', parts[drels].decode('utf-8'))}
        for m in ANCHOR.finditer(parts[dpath].decode('utf-8')):
            a = m.group(0)
            if 'name="%s"' % name in a:
                emb = re.search(r'r:embed="([^"]+)"', a).group(1)
                media = 'xl/' + rid[emb].replace('../', '')
                out[(sheet, name)] = (a, media, parts[media])
    return out


def apply(path, orig):
    parts = X.open_book(path)
    sp = sheet_parts(parts)
    done = []
    for (sheet, name), (anchor, media, blob) in orig.items():
        dpath, drels = drawing_of(parts, sp, sheet)
        d = parts[dpath].decode('utf-8')
        if 'name="%s"' % name in d:
            continue
        ext = media.rsplit('.', 1)[1]
        n = max(int(m.group(1)) for k in parts for m in [re.match(r'xl/media/image(\d+)\.\w+$', k)] if m) + 1
        new_media = 'xl/media/image%d.%s' % (n, ext)
        parts[new_media] = blob
        parts['__order__'].append(new_media)
        r = parts[drels].decode('utf-8')
        rid = 'rId%d' % (max([int(x) for x in re.findall(r'Id="rId(\d+)"', r)] + [0]) + 1)
        r = r.replace('</Relationships>', '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
                      'officeDocument/2006/relationships/image" Target="../media/image%d.%s"/></Relationships>'
                      % (rid, n, ext))
        parts[drels] = r.encode('utf-8')
        cid = max([int(x) for x in re.findall(r'<xdr:cNvPr id="(\d+)"', d)] + [1]) + 1
        a = re.sub(r'r:embed="[^"]+"', 'r:embed="%s"' % rid, anchor)
        a = re.sub(r'<xdr:cNvPr id="\d+"', '<xdr:cNvPr id="%d"' % cid, a, count=1)
        parts[dpath] = d.replace('</xdr:wsDr>', a + '</xdr:wsDr>').encode('utf-8')
        ct = parts['[Content_Types].xml'].decode('utf-8')
        if 'Extension="%s"' % ext not in ct:
            ct = ct.replace('<Default Extension="png"', '<Default Extension="%s" ContentType="image/x-%s"/>'
                            '<Default Extension="png"' % (ext, ext), 1)
            parts['[Content_Types].xml'] = ct.encode('utf-8')
        done.append('%s/%s -> %s' % (sheet, name, new_media))
    if done:
        X.write_book(path, parts)
        print('written:', os.path.relpath(path, XL), ' '.join(done))
    else:
        print('already present in', os.path.basename(path))


def main():
    orig = originals()
    assert len(orig) == 3, orig.keys()
    for rel in BOOKS:
        apply(os.path.join(XL, rel), orig)


if __name__ == '__main__':
    main()
