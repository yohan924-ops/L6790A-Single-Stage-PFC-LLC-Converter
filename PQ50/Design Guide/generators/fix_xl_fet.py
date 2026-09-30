# -*- coding: utf-8 -*-
"""Make the switch blocks describe the current that flows in one DEVICE.

Four things were wrong or missing, all of them about the same thing - the
sheets stated per-position and per-leg quantities and then used them as if a
single device carried them.

1  PER-DEVICE CURRENT.  Neither block had a parallel-device count, so there
   was nowhere for the current to divide. R_DS(on) was per leg on one sheet and
   per device on the other, and the two could not be compared. n.par (primary,
   D68) and n.SR (secondary, D103) make the split explicit, and four new rows
   carry the rms and peak that one device actually sees.

2  WRONG PEAK ON THE PRIMARY.  D65 sized the primary switch on
   1.3 * CC!E27 = Itrafo.pk = 16.39 A. A bridge switch carries the COMPOSITE
   tank current i_Lr - load plus magnetizing - and the workbook already
   computes that in Device Setting D32 = 18.319 A, for the OCP1 setting. The
   rating was 12 % light. Guide equation [115] has the same error, which is why
   the SMath sheet overrides it.

3  TEMPERATURE.  D78 and D100 computed loss from R_DS(on) at 25 C, and D79 and
   D101 then asked what R_th holds the junction at 125 C. Numerator and
   denominator at different temperatures: a 600 V superjunction part roughly
   doubles over that span and a low-voltage SR FET rises by about half, so the
   required R_th came out about twice as generous as it should be. kT.pri (D80)
   and kT.sec (D98) carry the multiplier.

4  DEVICE MODEL.  The secondary loss was a DIODE model, Vf*Iavg + rd*Irms^2,
   and C92 named a Schottky. This design rectifies synchronously, where the
   channel carries the current and the forward drop does not apply. Conf.SR
   (D93) selects between the two instead of silently assuming one.

Device data moves to this design's numbers at the same time, because the loss
rows say nothing while they describe the ST example's parts. No part number is
chosen: the values are the class the requirement rows ask for.

    python fix_xl_fet.py
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xlsx_patch as X                                               # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                              errors='replace')

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
XL = os.path.join(ROOT, 'Calculation Excel Sheet',
                  'L6790_spreadsheet_r1_0_corrected_rev0_6.xlsx')
SHEET = 'Power Components'

# (row, label, name, value-or-formula, unit, style-donor row)
NEW = [
    (62, 'Primary RMS current in ONE device', 'Imos.rms.dev',
     '=IF(ISNUMBER(F61),F61,D61)/D68', 'A', 61),
    (66, 'Primary peak current in ONE device', 'Ilr.pk.dev',
     "=\'Device Setting\'!D32/D68", 'A', 65),
    (68, 'Devices in parallel per switch position', 'n.par', 2, '-', 70),
    (80, 'Rdson multiplier at Tj,max (read off the Rdson-vs-Tj curve)',
     'kT.pri', 2, '-', 70),
    (87, 'Secondary RMS current in ONE device', 'Isr.rms.dev',
     '=IF(ISNUMBER(F85),F85,D85)/D103', 'A', 85),
    (91, 'Secondary peak current in ONE device', 'Isr.pk.dev',
     '=D86/D103', 'A', 90),
    (93, 'Rectifier device type (1 = diode/Schottky, 2 = SR MOSFET)',
     'Conf.SR', 2, '-', 96),
    (98, 'Rdson multiplier at Tj,max (read off the Rdson-vs-Tj curve)',
     'kT.sec', 1.5, '-', 96),
    (103, 'SR devices in parallel per leg', 'n.SR', 3, '-', 96),
]

VALUES = [
    (70, 0.024, 'primary Rdson @25 C per device - the 600 V superjunction '
                'class D65 asks for'),
    (96, 0.002, 'secondary Rdson @25 C per device - the SR class D90 asks for'),
]

FORMULAS = {
    # a bridge switch carries the COMPOSITE tank current, not the reflected
    # load current alone - the workbook already solves it in Device Setting D32
    'D65': "1.3*'Device Setting'!D32",
    # hot Rdson, and the current one device actually carries
    'D78': "D70*D80*D62^2",
    # SR: no forward drop. diode: the drop splits n.SR ways
    'D100': "IF(D93=2,0,0.5*D95*'Preliminary Calculation'!D7/D103)"
            "+D96*D98*D87^2",
    'D102': "D100*D103*2*'Design Spec'!$D$107",
}

LABELS = {
    'B60': 'Primary RMS current @Vin min - whole tank',
    'B61': 'Primary RMS Switch current @Vin min - per switch POSITION',
    'B65': 'Suggested Min Current rating per switch POSITION',
    'C65': 'IF Switch (composite tank peak)',
    'B70': 'Rdson resistance@25˚C (per device)',
    'B78': 'Maximum Power Losses estimation for ONE device',
    'B79': 'Estimated Rth max j-a, per device, at Tj = 125˚C',
    'B84': 'Secondary RMS current @Vin min - each winding',
    'B85': 'Secondary RMS Switch current @Vin min - each LEG',
    'C85': 'Idiode.rms per leg @θ=π/4',
    'B86': 'Secondary peak Switch current @Vin min - each LEG',
    'B89': 'Suggested Min Voltage rating for each power switch',
    'B90': 'Suggested Min Current rating per LEG',
    'B95': 'Rectifier forward voltage drop (Conf.SR = 1 only)',
    'B96': 'Rdson resistance@25˚C (per device)',
    'B100': 'Maximum Power Losses estimation for ONE device',
    'B101': 'Estimated Rth, per device, at Tj = 125˚C',
    'B102': 'Total Power dissipation, all rectifier devices',
    'C67': 'Superjunction MOSFET - source against D64 / D65 / D70',
    'C92': 'SR MOSFET - source against D89 / D90 / D96',
}

LOG = [
    (SHEET, 'D65 (primary switch current rating)',
     'The primary switch current rating was 1.3 * CC!E27 = 1.3 * Itrafo.pk = '
     '21.31 A. Itrafo.pk is the REFLECTED LOAD current alone. A bridge switch '
     'carries the composite tank current i_Lr, which is the load current plus '
     'the magnetizing current, and those two peak at different instants. Guide '
     'equation [115] is written the same way.',
     "1.3 * 'Device Setting'!D32 = 23.81 A. D32 is the composite peak the "
     'workbook already solves for the OCP1 setting, and it agrees with the '
     'SMath sheet (I.Lr_pk) to five figures.',
     'The rating was 12 % light on the one parameter that decides whether the '
     'switch survives an overload. It is also the quantity OCP1 watches, so '
     'the protection threshold and the device rating are now derived from the '
     'same number instead of two different ones.'),
    (SHEET, 'D62 · D66 · D68 · D87 · D91 · D103 (new)',
     'Every current in these blocks was per switch POSITION (primary) or per '
     'LEG (secondary), and the loss and rating rows then used them as though '
     'one device carried the lot. There was no parallel-device count anywhere, '
     'so R_DS(on) meant per leg here and per device in the SMath sheet and the '
     'two could not be compared.',
     'n.par (D68) = 2 primary devices in parallel per switch position and n.SR '
     '(D103) = 3 SR devices in parallel per leg. Four rows carry what ONE '
     'device sees: Imos.rms.dev (D62) = 3.854 A and Ilr.pk.dev (D66) = 9.159 A '
     'on the primary, Isr.rms.dev (D87) = 9.437 A and Isr.pk.dev (D91) = '
     '32.79 A on the secondary. The loss formulas D78 and D100 are now built '
     'on those per-device currents.',
     'n.par = 2 is set by the LOSS budget, not by the current rating: the '
     'statically-on device in half-bridge mode carries the whole tank current '
     '(10.9 A rms), and at 24 mOhm/25 C - about the best a 600 V superjunction '
     'part offers - a single device dissipates 5.7 W against a 3 W budget. '
     'CAUTION: these rows assume ideal current sharing. R_DS(on) spread means '
     'the hottest device takes more; allow about 20 % when sourcing, or bin '
     'the parts.'),
    (SHEET, 'D80 · D98 (new) · D70 · D96 · D78 · D100 · D102',
     'D78 and D100 computed conduction loss from R_DS(on) at 25 C, and D79 and '
     'D101 then asked what R_th holds the junction at 125 C. The numerator and '
     'the denominator of the same calculation were at different temperatures. '
     'Device data D70 and D96 still held the ST example parts.',
     'kT.pri (D80) = 2.0 and kT.sec (D98) = 1.5 carry the R_DS(on) rise to '
     'Tj,max and enter D78 and D100. D70 = 24 mOhm and D96 = 2 mOhm at 25 C, '
     'the classes the D65 and D90 requirements ask for. Loss per primary '
     'device 2.970 -> 0.713 W with the required Rth 33.7 -> 140 C/W; total '
     'rectifier loss 1.603 W, which is what SMath section 13.3 computes.',
     'A limit evaluated at the wrong temperature is not conservative, it is '
     'wrong in the dangerous direction - the required R_th was about 2x too '
     'generous. KNOWN LIMITATION, unchanged: D78 and D79 describe a SWITCHING '
     'device. In half-bridge morphing mode the L6790A holds LOUT2 high, so the '
     'low-side device of leg 2 conducts continuously and dissipates twice as '
     'much; the workbook has no row for it and SMath section 13.3 does '
     '(P.mos_dc). Also unchanged: Tj,max stays a literal 125 inside D79 and '
     'D101.'),
    (SHEET, 'D93 (new) · D95 · C67 · C92',
     'The secondary loss was a DIODE model, Vf*Iavg + rd*Irms^2, and C92 named '
     'a Schottky - while this design rectifies synchronously, where the channel '
     'carries the current and the forward drop does not apply. C67 and C92 also '
     'named parts that meet none of the requirement rows above them.',
     'Conf.SR (D93) selects 1 = diode/Schottky or 2 = SR MOSFET; at 2 the '
     'forward-drop term drops out of D100. D95 keeps its value and says in its '
     'label that it applies only at Conf.SR = 1. C67 and C92 now state the '
     'requirement the part has to meet instead of naming one.',
     'The sheet can express either rectifier now, rather than silently assuming '
     'a diode. NOT MODELLED at Conf.SR = 2: the body diode conducts during the '
     'SR dead time, and its Qrr is recovered every cycle. Both need an SR dead '
     'time the sheet does not have. A part number in a live sheet also has to '
     'be re-checked by hand on every input change, and it is the one thing on '
     'the sheet no calculation can verify.'),
]


def part_of(parts, name):
    wb = parts['xl/workbook.xml'].decode('utf-8')
    rid = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',
                          parts['xl/_rels/workbook.xml.rels'].decode('utf-8')))
    for nm, r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"', wb):
        if nm.replace('&amp;', '&') == name:
            return 'xl/' + rid[r].lstrip('/')
    raise KeyError(name)


def main():
    print('백업 %s' % os.path.basename(X.backup(XL)))
    parts = X.open_book(XL)
    p = part_of(parts, SHEET)
    xml = parts[p].decode('utf-8')

    for row, label, name, value, unit, donor in NEW:
        xml = X.ensure_row(xml, row)
        for col, val in (('B', label), ('C', name), ('D', value), ('E', unit)):
            ref = col + str(row)
            st = X.style_of(xml, '%s%d' % (col, donor))
            if col == 'D' and isinstance(val, str) and val.startswith('='):
                cell = X.cell_f(ref, st, val[1:])
            elif col == 'D':
                cell = X.cell_n(ref, st, val)
            else:
                cell = X.cell_t(ref, st, val)
            xml = X.set_cell(xml, ref, cell)
        print('  새 행    D%-4d %-13s %-30s %s'
              % (row, name, str(value)[:30], label[:38]))

    for row, value, why in VALUES:
        ref = 'D%d' % row
        xml = X.set_cell(xml, ref, X.cell_n(ref, X.style_of(xml, ref), value))
        print('  값       %-5s %-9s %s' % (ref, value, why[:56]))

    for ref, f in FORMULAS.items():
        xml = X.set_cell(xml, ref, X.cell_f(ref, X.style_of(xml, ref), f))
        print('  수식     %-5s = %s' % (ref, f[:62]))

    for ref, text in LABELS.items():
        xml = X.set_cell(xml, ref, X.cell_t(ref, X.style_of(xml, ref), text))
    print('  라벨     %d칸' % len(LABELS))
    parts[p] = xml.encode('utf-8')

    cl = part_of(parts, 'CHANGELOG_rev0_6')
    xml = parts[cl].decode('utf-8')
    hay = xml + parts.get('xl/sharedStrings.xml', b'').decode('utf-8')
    r = max(int(x) for x in re.findall(r'<row r="(\d+)"', xml))
    for sheet, cells, was, now, why in LOG:
        if cells in hay:
            print('  CHANGELOG 건너뜀 (%s)' % cells)
            continue
        r += 1
        xml = X.ensure_row(xml, r)
        for col, text, st in (('B', sheet, '7'), ('C', cells, '7'),
                              ('D', was, '8'), ('E', now, '8'), ('F', why, '8')):
            xml = X.set_cell(xml, col + str(r), X.cell_t(col + str(r), st, text))
        print('  CHANGELOG 행 %d  %s' % (r, cells))
    parts[cl] = xml.encode('utf-8')

    X.write_book(XL, parts)
    print()
    print('예상  D62 3.854 A · D65 23.81 A · D66 9.159 A · D78 0.713 W · '
          'D79 140.3 C/W')
    print('      D87 9.437 A · D91 32.79 A · D100 0.267 W · D102 1.603 W')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
