# -*- coding: utf-8 -*-
"""Put the workbook back into one language.

The workbook is an English deliverable. Every correction I made to it since
rev 0.5 was logged in Korean, and a handful of labels went in in Korean too -
57 cells in all. A reader who does not read Korean now gets an English sheet
with an untranslatable changelog, which is worse than either language alone.

The translations are written out cell by cell rather than generated, so each
one can be read against the original. Nothing but text changes: no formula,
no reference, no number.

    python fix_xl_english.py
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

HANGUL = re.compile(r'[가-힣]')

T = {}

T['Design Spec'] = {
    'F23': 'realised value (selected divider) ->',
}
T['RTC'] = {
    'B220': 'note',
    'B232': 'f.n (closed form)',
    'B233': 'f.n (grid)',
    'B234': 'difference [%]',
}
T['CC'] = {
    'J20': 'line cycle (Simpson, 6 points + theta=0)',
    'B32': 'Isec.node.ms.tsw (for the line-cycle integral)',
}
T['CHANGELOG_rev0_6'] = {
    'D62': 'CC!C25/C26/C29/C30 (a SINGLE point, theta=pi/4) were labelled '
           '"mains cycle" rms, and those values fed the semiconductor loss '
           'calculations directly.',
    'E62': 'Relabelled "@theta=pi/4 (approx.)", and added yellow input cells '
           'in column F carrying the line-cycle rms from the SMath sheet '
           '(F60 10.90 / F61 7.707 / F84 and F85 28.31 A). The loss formulas '
           'D78 and D100 prefer the selected value via '
           'IF(ISNUMBER(F..),F..,D..).',
    'F62': 'theta=pi/4 equals the line-cycle rms only if the envelope is '
           'sin(theta). The real envelope is sin^2(theta), so the primary is '
           'understated by 5.9 % and the secondary by 17.6 %; loss goes as the '
           'square, so rectifier loss is out by a factor 1.38 (7.93 -> 10.98 W, '
           'required Rth 12.60 -> 9.11 C/W). The CC sheet had only three theta '
           'columns, too few to integrate, so the SMath figures were imported. '
           'HISTORY.md C.18',
    'C63': 'H132:AV167 (196 cells)',
    'D63': 'The high-frequency pole f_px is computed in D104 and then '
           'referenced by no loop-verification formula at all. Gain, phase and '
           'crossover were built from f_z and f_p alone.',
    'E63': 'Inserted the f_px term into 196 cells: /(1+(f/f_px)^2) into the '
           '120 gain formulas, -ATAN(f/f_px) into the 76 phase formulas.',
    'F63': 'Phase near crossover came out 0.8 to 1.1 degrees optimistic. In a '
           'design whose margin sits close to 45 degrees that can invert the '
           'verdict. Appendix C.12',
    'D64': 'Labelled "Required E/A Gain @ 2fL,min", but the denominator was '
           'D65 - the ripple at the NOMINAL line frequency. D68 computes the '
           'f_l,min ripple and was never referenced.',
    'E64': 'Denominator changed to D68.',
    'F64': '50/47 = 1.064x optimistic. The error propagates EA_o -> f_MB -> '
           'f_z -> C_Fo -> R_F, moving the compensation values by 3 to 6 %. '
           'Where a line-frequency RANGE is specified, the minimum is the worst '
           'case. Appendix C.13',
    'D65': 'The ST tool defaults c.HB = 500 pF and t.D = 270 ns were still in '
           'place.',
    'E65': 'c.HB = 800 pF, t.D = 220 ns - the parts actually selected for this '
           'design.',
    'F65': 'The SMath sheet used 800 pF / 220 ns from the start, so the two '
           'documents disagreed at the INPUT. Q.ZVS.2 is non-dominant, so the '
           'tank does not move; only the T.ZC verdict becomes correct.',
    'D66': 'T_idle = 350 ns (the value implied by the C_T,max expression in DS '
           'section 5.3.2).',
    'E66': '250 ns - back-solved from all eight cells of the f_osc row of DS '
           'Table 5. Now identical to the SMath sheet.',
    'F66': 'The datasheet implies three different values (700 / 350 / 250 ns). '
           'The eight measured cells of Table 5 all land within 0.2 ns of '
           '250.0 ns, so that reading was adopted. The two documents have to '
           'agree on the input for the comparison to mean anything. NOT '
           'CONFIRMED until measured - re-check the margin at 700 ns too. '
           'Appendix C.1',
    'C67': 'C130:E134 (new)',
    'D67': 'Gain margin appears nowhere in the workbook. Only phase margin, in '
           'D124.',
    'E67': 'f.180 = SQRT(f_p*f_px - f_z*(f_p+f_px)) locates arg T = -180 deg in '
           'closed form; GM[dB] and the ratio k.GM against target are computed '
           'from |T| there. Currently f.180 = 206.0 Hz, GM = 34.3 dB, '
           'k.GM = 3.43.',
    'F67': 'Phase margin alone does not close the stability argument. This '
           'compensator has one zero against two poles at high frequency, so '
           'the phase heads for -270 deg and arg T crosses -180 at a finite '
           'frequency. No bisection is needed - take the tangent, divide '
           'through by f, and a single square root remains.',
    'D68': 'R_P selected 1.5 kOhm, while D41 right beside it computes an upper '
           'limit of 1.4375 kOhm. The limit is violated by 4.3 %.',
    'F68': 'R_P,max = V_F/I_min [144]. At 1.5 k the shunt-regulator cathode '
           'current falls to 1.15/1.5 = 0.767 mA, below the 0.8 mA minimum, and '
           'it stops regulating. AN UPPER LIMIT IS ROUNDED DOWN. The 240 W '
           'example in the design guide rounds 1.44 up to 1.5 and commits the '
           'same violation. Side effect: the R_B window moves from '
           '16.02-18.22 to 15.39-17.41 kOhm; the selected 16.5 k is still '
           'inside it (7.2 % low, 5.5 % high). Appendix C.14',
    'D69': 'C_in selected 2000 nF, while D7 computes a lower limit of '
           '2054.32 nF. Short by 2.6 %.',
    'F69': '3 nF/W is a FLOOR. Below it the differential attenuation of the EMI '
           'filter is insufficient.',
    'D70': 'Labelled "RT.min". But f_Min = 1/(2*(C_T*R_T + T_idle)) FALLS as '
           'R_T rises, so this value is the R_T at which f_Min exactly equals '
           'f_o - and R_T must stay BELOW it.',
    'E70': 'Relabelled "RT.ceil (NOT a minimum)".',
    'F70': 'Read as labelled, a designer rounds R_T up, the VCO clamp drops '
           'below f_o, and entry into the capacitive region is left to the ACP '
           'protection alone - which the design rules explicitly forbid. The '
           'selected 11 kOhm is below the 11.02 k ceiling, so the direction is '
           'right.',
    'C71': 'C22 C25 C84 (new)',
    'D71': 'The C_T design ceiling (D19) and floor (D20), the R_T ceiling '
           '(D24) and the n_aux/n_sec ceiling (D83) are all computed, and no '
           'cell compares any of them against the selected value.',
    'E71': 'Three ratio cells added - k.CT, k.RT.ceil, k.naux (C22, C25, C84). '
           'All must read greater than 1.',
    'F71': 'A limit that is computed but never compared lets a violation pass '
           'silently. Same structure as C.15, where the R_CS selection '
           'exceeded its own D44 ceiling by 2.6x without a warning. The SMath '
           'sheet carries the same checks as k.CTd / k.RTd / k.auxr.',
    'D72': 'The same defect C.6 fixed was still present in the 75 % and 50 % '
           'load blocks: IF(\'Design Spec\'!$D$108=1,...) reads Vf.BR (0.08 V) '
           'instead of the rectifier configuration (D107). 0.08 is never 1, so '
           'the condition is always false and the FB branch (/SQRT(2)) runs '
           'even in a CT design.',
    'E72': 'All four cells re-pointed to $D$107.',
    'F72': 'The C.6 fix in rev 0.6 was applied to the 100 % load block (row 26) '
           'only and missed the other two. Nothing currently reads rows 34-54, '
           'so there is no numerical impact today - which is why it survived. '
           'The moment those blocks are used, the per-winding rms comes out '
           '29 % low. Appendix C.25',
    'D73': 'R.ZCD.L (19 k) was described as the "Upper ZCD resistor" and '
           'R.ZCD.H (162 k) as the "Lower ZCD resistor". The values and links '
           'were right; only the two descriptions were swapped.',
    'F73': 'Built as this BOM reads, the divider ratio is inverted: the OVP1 '
           'threshold becomes 2.3/0.8 x (19/162+1) = 3.2 V instead of 27.4 V, '
           'and the converter trips into OVP the instant it starts. '
           'Appendix C.26',
    'D74': "The formula read 'Device Setting'!D$45, which is the "
           "CALCULATED E24 value, and ignored the selected value F45.",
    'F74': 'Invisible today because D45 and F45 happen to be 120 mOhm both. '
           'Change F45 and the BOM does not follow. The workbook idiom is '
           'IF(F,F,D) and every other BOM row uses it. Appendix C.27',
    'D75': 'Two different inputs are both labelled "Config.". D15 selects the '
           'input arrangement and feeds only D80; D59 selects the output '
           'rectifier configuration and drives 125 cells through D107.',
    'F75': 'Going by the name, a user edits the upper one, changes nothing '
           'about the rectifier configuration, and believes they did. The '
           'wiring is correct, so only the labels were fixed.',
    'D76': 'The ZVS check is never recomputed after the tank is selected. D28 '
           're-derives f.n = 0.82111 from the fitted expression [36] (whose '
           'exponent 5 has no basis in any ST document); D29 takes the phase at '
           'the design ceiling Q_ZVS = 0.8466 rather than the Q the converter '
           'runs at; and D30 divides by the TARGET \'Design Spec\'!D102 = '
           '150 kHz rather than the real resonant frequency. Result: T_ZC = '
           '303 ns, 34 % below the truth.',
    'E76': 'The realised values were already inside the workbook - the grid '
           'solution RTC!$BB$149 = 0.84006 and RTC!$C$41 = 0.7717. D28 -> '
           'RTC!$BB$149, both Q occurrences in D29 -> RTC!$C$41, and the '
           'denominator of D30 -> D55 (the real f.r, 151.748 kHz). T_ZC 303 -> '
           '457 ns. The tank-selection path (D26 -> D27 -> D43..D45) was not '
           'touched.',
    'D77': 'The verification block carries its own line-frequency input, '
           'D110 = 50 Hz, while the design block designs at the worst case of '
           '47 Hz (D7, D68, D73, D83). The design is therefore verified at a '
           'gentler line frequency than it was designed for, and D116, AV122, '
           'D125, D126, D128 and D129 all come out optimistic.',
    'E77': 'D110 = 47 (the worst case of the 47-63 Hz specification, matching '
           'Design Spec!D17). Third harmonic 3.86 -> 4.31 %, burst FB ripple '
           '47.3 -> 52.9 mV, R_BM adjustment range 2.37 -> 2.65 kohm.',
    'D78': 'Hold-up is assumed to start discharging from the nominal output, '
           '25 V (D14). The real output swings 24.41 to 25.59 V on the 2f_L '
           'ripple and the AC can be lost at any phase, so the worst case is '
           'the ripple trough. Energy goes as V^2, so the result is 12.5 % '
           'optimistic. The actual ripple is already in D31, one row below.',
    'E78': 'D14^2 replaced by (D14-D31/2)^2 in both formulas. Required '
           'capacitance 59.77 -> 67.22 mF, achieved hold-up 15.10 -> 13.42 ms. '
           'The chain is D22 -> D31 -> D26 -> D23/D24 (selected by hand), so '
           'this is not a circular reference.',
    'D79': 'C.18 - the three currents the design calls line-cycle rms are in '
           'fact a single point at theta=pi/4. Res.Tank D65 = CC!C29, D67 = '
           'CC!C25 and Power D28 = CC!C31 each read one cell of CC. The output '
           'bank ripple current reads 21.77 A where the line-cycle rms is '
           '30.19 A - 28 % low, and that value sets the number of output '
           'capacitors.',
    'E79': 'RTC already solves six theta (pi/12 to pi/2 in 15 deg steps); CC '
           'was only reading three of them. Columns F, G and H now take the '
           'remaining three from RTC!BC150, BC153 and BC154, row 32 holds the '
           'square of the node current, and column J carries a Simpson '
           'integral (weights 1,4,2,4,2,4,1 divided by 18). The theta=0 sample '
           'is exactly zero because the load goes as sin^2(theta). D65 -> '
           'CC!J29, D67 -> CC!J25, Power D28 -> CC!J31. Against a 721-point '
           'sweep: secondary -0.04 %, bank ripple -0.08 %, primary -1.83 %. '
           'Only the primary keeps a residual, because the magnetising current '
           'does not vanish at theta=0; extrapolating the endpoint makes it '
           'worse (+4.7 %), and theta -> 0 is burst territory that is never '
           'reached.',
    'D80': 'The primary switch selection block asks for no body-diode recovery '
           'condition. In normal ZVS the body diode conducts only during the '
           'dead time and the channel takes the current over at almost zero '
           'volts, so no recovery happens; in the CAPACITIVE region the current '
           'leads, the opposite device turns on while this diode is still '
           'conducting, the diode is hard reverse-recovered, and a '
           'shoot-through current crosses the bus. Overload, a load step, low '
           'line and start-up all enter that region for a few cycles, so it has '
           'to be survivable rather than merely avoided.',
    'E80': 'D74 = SQRT(2)*Vac,max = 373.4 V (the capacitive region offers no '
           'soft transition, so it is the raw rectified line peak); D75 = '
           'CC!C28 = the magnetising peak, 12.36 A. No Qrr is assumed - that is '
           'a device number. Specify trr and Qrr AT THESE CONDITIONS, not at '
           'the datasheet default (usually 25 C and a low dI/dt): Qrr roughly '
           'doubles from 25 C to 125 C.',
}


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
    n = 0
    for sheet, cells in T.items():
        p = part_of(parts, sheet)
        xml = parts[p].decode('utf-8')
        for ref, text in cells.items():
            if HANGUL.search(text):
                raise SystemExit('%s!%s: 번역문에 한글이 남아 있다' % (sheet, ref))
            xml = X.set_cell(xml, ref, X.cell_t(ref, X.style_of(xml, ref), text))
            n += 1
        parts[p] = xml.encode('utf-8')
        print('  %-22s %d칸' % (sheet, len(cells)))
    X.write_book(XL, parts)
    print('총 %d칸을 영문으로 교체' % n)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
