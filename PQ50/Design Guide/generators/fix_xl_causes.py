# -*- coding: utf-8 -*-
"""Apply the workbook fixes for root causes A, C and D (HISTORY.md 3.7).

  A  the ZVS check never re-runs on the tank that was actually selected.
     D28 recomputes f.n from the fitted approximation [36] (0.82111) and D29
     evaluates the phase at the DESIGN bound Q_ZVS (0.8466). The realised
     numbers - f.n 0.84006 and Q 0.7717 - are already in the workbook, in
     RTC!BB149 and RTC!C41, put there by the grid search. D30 also scales by
     the TARGET resonant frequency (Design Spec D102 = 150 kHz) instead of the
     one the selected tank actually has (Res. Tank D55 = 151.748 kHz).
     Nothing else reads D28/D29 - they feed only D30 and the C32 verdict - so
     the tank selection chain (D26 -> D27 -> D43..D45) is untouched.

  C  the verification block carries its own line-frequency input, D110 = 50 Hz,
     while the design block works at 47 Hz (D7, D68, D73, D83). The workbook
     designs for the worst case and then verifies at a milder one.

  D  hold-up starts the discharge from the nominal 25 V. The output actually
     rides a 1.184 V ripple, and the mains can fail anywhere on it, so the
     start voltage is the trough. D31 already holds that ripple.

E (RTC's Vin_max) is NOT applied: pointing it at the FB corner drives M_req
below the tank's zero-load gain floor 1/(1+lambda), so fn.max goes imaginary and
the whole f_n grid - and the 23 charts on it - fails. That needs the grid range
logic redesigned, not a link changed.

Run once. Re-running is harmless: each edit is checked against the text it
expects and skipped if already applied.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                               # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')

# sheet name -> part, resolved from the workbook itself rather than assumed
SHEET = {'Res. Tank Design': 'xl/worksheets/sheet4.xml',
         'Power Components': 'xl/worksheets/sheet5.xml',
         'CompensationNet&Check': 'xl/worksheets/sheet7.xml'}

EDITS = [
    # (sheet, cell, kind, expected-fragment-of-current, new)
    ('Res. Tank Design', 'D28', 'f', '1/SQRT((1)+((1/D16)', "RTC!$BB$149"),
    # D29 also read the CALCULATED lambda (D16 = 0.54132) where the phase of the
    # tank that was actually built depends on the REALISED one (D50 = 0.55).
    # D18/D19/D20/D45 keep D16 - those are selection formulas and D16 is right
    # there. D29 is the only verification cell that had it.
    ('Res. Tank Design', 'D29', 'f', '(D26*(D28)^3)',
     'ATAN(((((D50^2)+(D50)+(((D28^2)-1)*(RTC!$C$41^2)))*(D28^2))-(D50^2))'
     '/(RTC!$C$41*(D28)^3))'),
    ('Res. Tank Design', 'D29', 'f', '(D16^2)',
     'ATAN(((((D50^2)+(D50)+(((D28^2)-1)*(RTC!$C$41^2)))*(D28^2))-(D50^2))'
     '/(RTC!$C$41*(D28)^3))'),
    ('Res. Tank Design', 'D30', 'f', "'Design Spec'!D102",
     '(D29)/(2*PI()*D28*D55)*1000000'),
    ('CompensationNet&Check', 'D110', 'n', '<v>50</v>', '47'),
    ('Power Components', 'D22', 'f', '/((D14^2)-(D15^2))',
     '(2*D12*D17*(10^-3))/(((D14-D31/2)^2)-(D15^2))*10^6'),
    ('Power Components', 'D33', 'f', '*((D14^2)-(D15^2))',
     'D26/(2*D12)*(((D14-D31/2)^2)-(D15^2))/1000'),
]


def main():
    bak = X.backup(XL)
    print('백업 %s' % os.path.basename(bak))
    parts = X.open_book(XL)
    applied = skipped = 0
    for sheet, ref, kind, expect, new in EDITS:
        part = SHEET[sheet]
        xml = parts[part].decode('utf-8')
        import re
        m = re.search(r'<c r="%s"[^>]*(?:/>|>.*?</c>)' % ref, xml, re.S)
        if not m:
            raise SystemExit('%s!%s 를 찾지 못했다' % (sheet, ref))
        cur = m.group(0)
        if expect not in cur:
            print('  건너뜀 %-22s %-6s (이미 적용됐거나 내용이 다르다)' % (sheet, ref))
            skipped += 1
            continue
        style = X.style_of(xml, ref)
        cell = (X.cell_f(ref, style, new) if kind == 'f'
                else X.cell_n(ref, style, new))
        parts[part] = X.set_cell(xml, ref, cell).encode('utf-8')
        print('  적용   %-22s %-6s -> %s' % (sheet, ref, new[:58]))
        applied += 1
    if not applied:
        print('바뀐 것이 없다. 쓰지 않는다.')
        return 0
    X.write_book(XL, parts)
    print()
    print('적용 %d건 · 건너뜀 %d건' % (applied, skipped))
    print('Excel 에서 한 번 열었다 저장할 것 — 수식이 바뀌어 캐시가 낡았다.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
