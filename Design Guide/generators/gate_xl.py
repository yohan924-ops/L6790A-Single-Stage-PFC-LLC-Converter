# -*- coding: utf-8 -*-
"""Gate driver selection and start-up in the three workbooks (2026-10-22, user: "too many
parameters; start-up into Res. Tank Design, simpler names, no duplicate OCP1/2; the gate
driver in the switch section; recommended value first, mine next, as the other sheets do;
only the checks that matter; a simple gate-driver schematic" - then "there is no guarantee
the driver is an L6498LD: make it like the MOSFET selection").

Power Components, inside the LLC half-bridge switch section (xl_rows.py inserts the rows -
everything below moves down, references follow):
  76-82    the switch's gate data, in its own yellow parameter block next to Rdson / Coss:
           C.g (Qg slope above the plateau)  C.gs.dev  R.g  V.pl  V.th  V.th.min  Q.gd
  88-120   "LLC Half Bridge Gate Driver Selection", laid out like the switch selection:
           the part number (yellow), the driver datasheet values (yellow): I.so I.si
           V.test t.pd MT I.Q Rth.drv Tj.max V.bo.min;
           the gate network - Value is the recommendation, Selected Value is the design:
           V.drv R.on R.off V.F (0 = separate GOFF pin) C.gs C.boot R.boot V.F.boot;
           results, five with a Check: t.on t.off t.D.need V.g.su V.bs.1 V.bs.min k.Miller
           Tj.drv (at Ta, D73) P.Ron P.Roff; the schematic (xl_gate_fig.py) at G100.
  old rows 76-80 -> 83-87, old 81-119 (the secondary section) -> 121-159.
Res. Tank Design 81-86  start-up with the output near 0 V: I.su, k.su (OCP2, Device Setting
  G49), f.su.OCP1.
CC 77-   the working (the model of gate_budget.py) and the two L6790A assumptions
  (start-up dead time 420 ns, FB bus 235 V).

    python gate_xl.py          all three books, idempotent (CHANGELOG mark)
"""
import os
import re

import xlsx_patch as X
import xl_rows
from measured200_xl import sheet_parts

HERE = os.path.dirname(os.path.abspath(__file__))
XL = os.path.normpath(os.path.join(HERE, '..', '..', 'Calculation Excel Sheet'))
PNG = os.path.normpath(os.path.join(HERE, '..', 'figures', 'xl_gate_drive.png'))
MARK = 'gate driver selection in the switch section, start-up in Res. Tank Design'
AT1, N1 = 76, 7                     # switch gate data
AT2 = 88                            # gate driver section (after the first insert)

SHEET = dict(V=14.35, Ron=4.7, Roff=2.2, VF=0.7, Cgs=0, Cb=470, Rb=0, VFb=1.3,
             note='design sheet section 14c.1: V.CC_reg_max 14.35 V, R.G 4.7, R.G_off 2.2 ohm + '
                  '1N4148W, C.BOOT 470 nF, ES1J (V.F 1.3 V) with no series resistor')
BOOKS = {
    'GUIDE_PQ50_657W_workbook_rev0_6_unencrypted.xlsx': SHEET,
    os.path.join('variants', '3CORE_670W_workbook_unencrypted.xlsx'): SHEET,
    os.path.join('variants', 'BENCH_200W_LGE_workbook_unencrypted.xlsx'): dict(
        V=18.0, Ron=47.0, Roff=10.0, VF=0.7, Cgs=0, Cb=100, Rb=3.3, VFb=1.0,
        note='LGE bench board: VCC_GD 18 V, R115 47 ohm, R114 10 ohm + 1N4148WS, C63/C72 100 nF, '
             'MURS160 (V.F 1.0 V), boot resistor R113/R155 10 -> 3.3 ohm (user, 2026-10-21)'),
}
DV, DS, RT, PCq = "'Device Setting'!", "'Design Spec'!", "'Res. Tank Design'!", "'Power Components'!"

#  STO60N045DM9 DS14711 Rev 4 (Figures 4-6 read as vectors, gate_wave.py) - one set for all books
MOS_ROWS = [   # key, label, name, value, unit
    ('Cg', 'Gate capacitance above the plateau, Qg slope (per device)', 'C.g', 7.5, 'nF'),
    ('Cgsd', 'Gate-source capacitance C.iss - C.rss (per device)', 'C.gs.dev', 4.76, 'nF'),
    ('Rgi0', 'Internal gate resistance (per device)', 'R.g', 4.5, 'Ω'),
    ('Vpl', 'Miller plateau voltage', 'V.pl', 6.3, 'V'),
    ('Vth', 'Gate threshold, typ (for timing)', 'V.th', 4.0, 'V'),
    ('Vthm', 'Gate threshold, min', 'V.th.min', 3.5, 'V'),
    ('Qgd', 'Miller charge over the bus swing (per device)', 'Q.gd', 13, 'nC'),
]

#  gate driver section rows from AT2: (key, kind, label, name, D, unit, F)
#  kind: title / part / head / data (yellow D) / net (D recommended, F yellow) / res (D, F check)
DRV_ROWS = [
    ('t', 'title', 'LLC Half Bridge Gate Driver Selection', None, None, None, None),
    ('part', 'part', 'Please Select a dedicated Gate Driver part number ', 'L6498LD', None, None, None),
    ('h1', 'head', 'Parameter', 'Name', 'Value', 'Unit', None),
    ('Iso', 'data', 'Source current, min (full temperature)', 'I.so', 1.4, 'A', None),
    ('Isi', 'data', 'Sink current, min (full temperature)', 'I.si', 1.55, 'A', None),
    ('Vt', 'data', 'Supply voltage those currents are given at', 'V.test', 15, 'V', None),
    ('tpd', 'data', 'Propagation delay, typ', 't.pd', 85, 'ns', None),
    ('MT', 'data', 'Delay matching, max', 'MT', 30, 'ns', None),
    ('IQ', 'data', 'Quiescent current, VCC + floating, max', 'I.Q', 0.6, 'mA', None),
    ('Rth', 'data', 'Thermal resistance junction-ambient', 'Rth.drv', 120, '˚C/W', None),
    ('Tjmax', 'data', 'Junction temperature, recommended max', 'Tj.max', 125, '˚C', None),
    ('Vbo', 'data', 'Floating (bootstrap) supply, recommended min', 'V.bo.min', 9.3, 'V', None),
    ('h2', 'head', 'Parameter', 'Name', 'Value', 'Unit', 'Selected Value'),
    ('V', 'net', 'Gate drive voltage (Value: the driver test voltage)', 'V.drv', '{Vt}', 'V', 'in'),
    ('Ron', 'net', 'Turn-on resistor (Value: min, driver temperature)', 'R.on', '{cc:Ronmin}', 'Ω', 'in'),
    ('Roff', 'net', 'Turn-off resistor with D.off (Value: max, no overlap)', 'R.off', '{cc:Roffmax}', 'Ω', 'in'),
    ('VF', 'net', 'D.off forward voltage (0 = separate GOFF pin)', 'V.F', None, 'V', 'in'),
    ('Cgs', 'net', 'Gate-source capacitor, option (Value: needed)', 'C.gs', '{cc:Cgsmin}', 'nF', 'in'),
    ('Cb', 'net', 'Bootstrap capacitor (Value: min, 10 x C.gate)', 'C.boot', '{cc:Cbmin}', 'nF', 'in'),
    ('Rb', 'net', 'Bootstrap resistor (Value: max, 1st pulse to V.bo.min)', 'R.boot', '{cc:Rbmax}', 'Ω', 'in'),
    ('VFb', 'net', 'D.boot forward voltage', 'V.F.boot', None, 'V', 'in'),
    ('h3', 'head', 'Results', 'Name', 'Value', 'Unit', 'Check'),
    ('ton', 'res', 'Gate on delay: IC edge -> channel on', 't.on', '{cc:ton}', 'ns', None),
    ('toff', 'res', 'Gate off delay: IC edge -> channel off', 't.off', '{cc:toff}', 'ns', None),
    ('tD', 'res', 'Dead time needed in run (ADT 40-420 ns)', 't.D.need', '{cc:tDneed}', 'ns',
     'IF(AND({tD}>=40,{tD}<=420),"OK","CHECK")'),
    ('Vg', 'res', 'Gate voltage, end of start-up pulse (>= 10 V)', 'V.g.su', '{cc:Vgsu}', 'V',
     'IF({Vg}>=10,"OK","CHECK")'),
    ('Vbs1', 'res', 'V.BS after the first LOUT pulse (>= V.bo.min)', 'V.bs.1', '{cc:Vbs1}', 'V',
     'IF({Vbs1}>={Vbo},"OK","CHECK")'),
    ('Vbs', 'res', 'V.BS lowest, steady at f.SU', 'V.bs.min', '{cc:Vbsmin}', 'V', None),
    ('kM', 'res', 'Gate-off margin vs Miller kick (> 1)', 'k.Miller', '{cc:kM}', '-', 'IF({kM}>=1,"OK","CHECK")'),
    ('Tj', 'res', 'Driver junction at f.Max and Ta (<= Tj.max)', 'Tj.drv', '{cc:Tj}', '˚C',
     'IF({Tj}<={Tjmax},"OK","CHECK")'),
    ('PRon', 'res', 'R.on dissipation at f.Max (rating >= 2x)', 'P.Ron', '{cc:PRon}', 'W', None),
    ('PRoff', 'res', 'R.off dissipation at f.Max (rating >= 2x)', 'P.Roff', '{cc:PRoff}', 'W', None),
    ('gap', 'gap', None, None, None, None, None),
]

#  CC working: (key, label, value / formula, unit, is_data). {pc:key} = the Selected Value of a
#  network row, {d:key} = the D cell of a driver or switch data row
CC0 = 77
CC_ROWS = [
    ('title', 'Gate drive working - feeds Power Components 76-82 and 88-119', None, None, False),
    ('tDsu', 'L6790A dead time at start-up, before ADT (DS gives none) [assumed]', 420, 'ns', True),
    ('VbFB', 'L6790A highest FB bus = HB/FB morphing threshold (DS V.HVPK_BOH)', 235, 'V', True),
    ('Rso', 'Driver source resistance: V.test / I.so', '{d:Vt}/{d:Iso}', 'Ω', False),
    ('Rsi', 'Driver sink resistance: V.test / I.si', '{d:Vt}/{d:Isi}', 'Ω', False),
    ('V', 'V.drv (selected)', '{pc:V}', 'V', False),
    ('CG', 'Gate capacitance per position: n.par x C.g + C.gs', PCq + '$D$68*{d:Cg}+{pc:Cgs}', 'nF', False),
    ('Rgi', 'Internal gate resistance per position', '{d:Rgi0}/' + PCq + '$D$68', 'Ω', False),
    ('Reff', 'Turn-off path resistance',
     'IF({pc:VF}=0,{pc:Roff},IF({pc:Roff}>0,{pc:Roff}*{pc:Ron}/({pc:Roff}+{pc:Ron}),{pc:Ron}))', 'Ω', False),
    ('Veff', 'Turn-off path offset (D.off)', 'IF(AND({pc:VF}>0,{pc:Roff}>0),{pc:VF}*{pc:Ron}/({pc:Roff}+{pc:Ron}),0)',
     'V', False),
    ('ton_', 'τ.on = (R.so + R.on + R.gi) C.G', '({Rso}+{pc:Ron}+{Rgi})*{CG}', 'ns', False),
    ('toff_', 'τ.off = (R.si + R.off.eff + R.gi) C.G', '({Rsi}+{Reff}+{Rgi})*{CG}', 'ns', False),
    ('tL1', 'Start-up pulse T/2 - t.D.su (also the first LOUT pulse)', '10^6/(2*%s$D$29)-{tDsu}' % DV, 'ns', False),
    ('trun', 'Pulse at f.Max: T/2 - t.D', '10^6/(2*%s$D$27)-%s$D$47' % (DV, DS), 'ns', False),
    ('Vgsu', 'Gate voltage at the end of the start-up pulse', '{V}*(1-EXP(-{tL1}/{ton_}))', 'V', False),
    ('Vgrun', 'Gate voltage at the end of the f.Max pulse', '{V}*(1-EXP(-{trun}/{ton_}))', 'V', False),
    ('Eon', 'Energy per turn-on at f.Max', '{CG}*{Vgrun}*({V}-{Vgrun}/2)', 'nJ', False),
    ('Eoff', 'Energy per turn-off at f.Max', '{CG}*{Vgrun}^2/2', 'nJ', False),
    ('xon', 'Driver share of the turn-on energy', '{Rso}/({Rso}+{pc:Ron}+{Rgi})', '-', False),
    ('xoff', 'Driver share of the turn-off energy', '{Rsi}/({Rsi}+{Reff}+{Rgi})', '-', False),
    ('Pdrv', 'Driver power at f.Max, both positions + quiescent',
     '2*({Eon}*{xon}+{Eoff}*{xoff})*%s$D$27*10^-6+{d:IQ}*{V}/1000' % DV, 'W', False),
    ('Pbud', 'Driver power budget: (Tj.max - Ta) / Rth - quiescent',
     '({d:Tjmax}-%s$D$73)/{d:Rth}-{d:IQ}*{V}/1000' % PCq, 'W', False),
    ('xneed', 'Turn-on share the budget allows',
     '({Pbud}-2*{Eoff}*{xoff}*%s$D$27*10^-6)/(2*{Eon}*%s$D$27*10^-6)' % (DV, DV), '-', False),
    ('Ronmin', 'R.on minimum for the driver temperature',
     'IF({xneed}<=0,"lower V.drv",MAX(0,{Rso}/{xneed}-{Rso}-{Rgi}))', 'Ω', False),
    ('TTrun', 'Midpoint swing in run: c.HB V.bus,max / I.Lm.pk',
     '%s$D$46*SQRT(2)*%s$D$14/%s$D$73/1000' % (DS, DS, RT), 'ns', False),
    ('TTsu', 'Midpoint swing at start-up: c.HB V.bus,FB / I.su', '%s$D$46*{VbFB}/%s$D$84/1000' % (DS, RT), 'ns', False),
    ('iM', 'Miller current into an off gate during the faster swing',
     PCq + '$D$68*{d:Qgd}/MIN({TTrun},{TTsu})', 'A', False),
    ('dVr', 'Gate kick, resistive estimate: i.M x sink path', '{iM}*({Rsi}+{Reff}+{Rgi})', 'V', False),
    ('dVc', 'Gate kick, capacitive bound: Q.gd / (C.gs + C.gs option)',
     PCq + '$D$68*{d:Qgd}/(%s$D$68*{d:Cgsd}+{pc:Cgs})' % PCq, 'V', False),
    ('kM', 'k.Miller = V.th min / the smaller kick', '{d:Vthm}/MIN({dVr},{dVc})', '-', False),
    ('Cgsmin', 'C.gs needed (0 if the gate holds without it)',
     'IF(MIN({dVr},{dVc})<={d:Vthm},0,MAX(0,%s$D$68*({d:Qgd}/{d:Vthm}-{d:Cgsd})))' % PCq, 'nF', False),
    ('ton', 't.on: IC edge -> V.th', '{d:tpd}+{ton_}*LN({V}/({V}-{d:Vth}))', 'ns', False),
    ('toff', 't.off: IC edge -> below V.th min',
     'IF({d:Vthm}>{Veff},{d:tpd}+{toff_}*LN(({V}-{Veff})/({d:Vthm}-{Veff})),"never")', 'ns', False),
    ('toffpl', 'IC edge -> plateau on the way down', '{d:tpd}+{toff_}*LN(({V}-{Veff})/({d:Vpl}-{Veff}))', 'ns', False),
    ('tDneed', 't.D.need = (t.off.pl - t.pd) + swing - (t.on - t.pd) + MT', '{toffpl}-{ton}+{TTrun}+{d:MT}', 'ns', False),
    ('Reffm', 'Turn-off path that holds the gate below V.th min against the Miller current',
     '{d:Vthm}/{iM}-{Rsi}-{Rgi}', 'Ω', False),
    ('Reffo', 'Turn-off path that has the gate off before the other side turns on (t.D + t.on)',
     '(%s$D$47+{ton}-{d:tpd})/(LN(({V}-{Veff})/({d:Vthm}-{Veff}))*{CG})-{Rsi}-{Rgi}' % DS, 'Ω', False),
    ('Reffmax', 'Turn-off path maximum: the overlap limit, and the Miller limit unless C.gs alone holds',
     'IF({dVc}<={d:Vthm},{Reffo},MIN({Reffo},{Reffm}))', 'Ω', False),
    ('Roffmax', 'R.off maximum (in parallel with R.on unless V.F = 0)',
     'IF({Reffmax}<=0,"lower R.on",IF({pc:VF}=0,{Reffmax},IF({Reffmax}>={pc:Ron},"any",1/(1/{Reffmax}-1/{pc:Ron}))))',
     'Ω', False),
    ('Cbmin', 'C.boot minimum: 10 x C.G', '10*{CG}', 'nF', False),
    ('taub', 'τ.boot (a diode alone taken as 0.5 Ω)', 'MAX({pc:Rb},0.5)*{pc:Cb}', 'ns', False),
    ('Rbmax', 'R.boot maximum: the first LOUT pulse reaches V.bo.min',
     'IF({V}-{pc:VFb}>{d:Vbo},{tL1}/({pc:Cb}*LN(({V}-{pc:VFb})/({V}-{pc:VFb}-{d:Vbo}))),"V.drv too low")', 'Ω', False),
    ('Vbs1', 'V.BS after the first LOUT pulse', '({V}-{pc:VFb})*(1-EXP(-{tL1}/{taub}))', 'V', False),
    ('dVbs', 'V.BS drop per high-side pulse at f.SU (gate charge + floating quiescent 120 uA)',
     '{CG}*{Vgsu}/{pc:Cb}+0.00012*{tL1}/{pc:Cb}', 'V', False),
    ('Vbsmin', 'V.BS lowest, steady at f.SU',
     '{V}-{pc:VFb}-{dVbs}*EXP(-{tL1}/{taub})/(1-EXP(-{tL1}/{taub}))-{dVbs}', 'V', False),
    ('PRon', 'P.Ron at f.Max',
     '({Eon}*{pc:Ron}/({Rso}+{pc:Ron}+{Rgi})+IF({pc:VF}=0,0,{Eoff}*{Reff}/({Rsi}+{Reff}+{Rgi})*{Reff}/{pc:Ron}))'
     '*%s$D$27*10^-6' % DV, 'W', False),
    ('PRoff', 'P.Roff at f.Max',
     'IF({pc:Roff}>0,{Eoff}*{Reff}/({Rsi}+{Reff}+{Rgi})*IF({pc:VF}=0,1,{Reff}/{pc:Roff})*%s$D$27*10^-6,0)' % DV,
     'W', False),
    ('Tj', 'Driver junction at f.Max and Ta (Power Components D73)', '%s$D$73+{Pdrv}*{d:Rth}' % PCq, '˚C', False),
]


def rt_rows(cc):
    a = 'MAX(CC!$C$%d,SQRT(2)*%s$D$14/2)' % (cc['VbFB'], DS)
    return [
        ('I.su', 'Tank peak at f.SU, V.out ~0 (FB, 235 V bus)',
         '%s/D52*TAN(PI()*D55/(2*%s$D$29))' % (a, DV), 'A', None),
        ('k.su', 'OCP2 margin (> 1, else start-up restarts)', '%s$G$49/D84' % DV, '-', 'IF(D85>=1,"OK","CHECK")'),
        ('f.su.OCP1', 'Lowest f before OCP1 while V.out is low',
         'PI()*D55/(2*ATAN(%s$D$49*D52/%s))' % (DV, a), 'kHz', None),
    ]


def set_ht(xml, row, ht):
    return re.sub(r'<row r="%d"(?: [^>]*)?>' % row,
                  '<row r="%d" ht="%s" customHeight="1">' % (row, ht), xml, count=1)


def add_merge(xml, ref):
    m = re.search(r'<mergeCells count="(\d+)">', xml)
    return xml.replace(m.group(0), '<mergeCells count="%d"><mergeCell ref="%s"/>' % (int(m.group(1)) + 1, ref), 1)


def add_picture(parts, sp, png, row0, col0=6):
    """anchor the PNG at (col0, row0) of Power Components, about 760 px wide"""
    rels = parts['xl/worksheets/_rels/' + sp['Power Components'].split('/')[-1] + '.rels'].decode()
    dpath = 'xl/' + re.search(r'Target="\.\./(drawings/drawing\d+\.xml)"', rels).group(1)
    drels = dpath.replace('drawings/', 'drawings/_rels/') + '.rels'
    n = max(int(k[len('xl/media/image'):-4]) for k in parts if re.match(r'xl/media/image\d+\.png$', k)) + 1
    media = 'xl/media/image%d.png' % n
    parts[media] = open(png, 'rb').read()
    parts['__order__'].append(media)            # write_book writes the listed parts only
    r = parts[drels].decode()
    rid = 'rId%d' % (max(int(x) for x in re.findall(r'Id="rId(\d+)"', r)) + 1)
    r = r.replace('</Relationships>', '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
                  'officeDocument/2006/relationships/image" Target="../media/image%d.png"/></Relationships>' % (rid, n))
    parts[drels] = r.encode()
    d = parts[dpath].decode()
    cid = max(int(x) for x in re.findall(r'<xdr:cNvPr id="(\d+)"', d)) + 1
    from PIL import Image
    w, h = Image.open(png).size
    cx = 760 * 9525
    cy = int(cx * h / w)
    anchor = ('<xdr:oneCellAnchor><xdr:from><xdr:col>%d</xdr:col><xdr:colOff>76200</xdr:colOff>'
              '<xdr:row>%d</xdr:row><xdr:rowOff>0</xdr:rowOff></xdr:from><xdr:ext cx="%d" cy="%d"/>'
              '<xdr:pic><xdr:nvPicPr><xdr:cNvPr id="%d" name="Gate drive schematic"/><xdr:cNvPicPr>'
              '<a:picLocks noChangeAspect="1"/></xdr:cNvPicPr></xdr:nvPicPr><xdr:blipFill><a:blip '
              'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" r:embed="%s"/>'
              '<a:stretch><a:fillRect/></a:stretch></xdr:blipFill><xdr:spPr><a:xfrm><a:off x="0" y="0"/>'
              '<a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr>'
              '</xdr:pic><xdr:clientData/></xdr:oneCellAnchor>' % (col0, row0 - 1, cx, cy, cid, rid, cx, cy))
    parts[dpath] = d.replace('</xdr:wsDr>', anchor + '</xdr:wsDr>').encode()


def main():
    for rel, sel in BOOKS.items():
        apply(os.path.join(XL, rel), sel)


def apply(path, sel):
    parts = X.open_book(path)
    sp = sheet_parts(parts)
    log = parts[sp['CHANGELOG_rev0_6']].decode('utf-8')
    if MARK in log:
        print('already present in', os.path.basename(path))
        return
    xl_rows.insert_rows(parts, 'Power Components', AT1, N1)
    xl_rows.insert_rows(parts, 'Power Components', AT2, len(DRV_ROWS))

    drow = {r[0]: AT1 + i for i, r in enumerate(MOS_ROWS)}
    drow.update({r[0]: AT2 + i for i, r in enumerate(DRV_ROWS)})
    ccrow = {r[0]: CC0 + i for i, r in enumerate(CC_ROWS)}

    def sub(f, here):
        def one(m):
            k = m.group(1)
            pre = '' if here == 'pc' else PCq
            if k.startswith('pc:'):
                return '%s$F$%d' % (pre, drow[k[3:]])
            if k.startswith('d:'):
                return '%s$D$%d' % (pre, drow[k[2:]])
            if k.startswith('cc:'):
                return '%s$C$%d' % ('' if here == 'cc' else 'CC!', ccrow[k[3:]])
            return 'D%d' % drow[k] if here == 'pc' else 'C%d' % ccrow[k]
        return re.sub(r'\{([\w:]+)\}', one, f)

    # ---- Power Components
    pc = parts[sp['Power Components']].decode('utf-8')
    s_title, s_head, s_lab = X.style_of(pc, 'B57'), X.style_of(pc, 'B59'), X.style_of(pc, 'B58')
    s_in, s_val, s_unit = X.style_of(pc, 'D58'), X.style_of(pc, 'D60'), X.style_of(pc, 'E58')
    s_part, s_partb = X.style_of(pc, 'C67'), X.style_of(pc, 'B67')

    def cell(ref, c):
        nonlocal pc
        pc = X.set_cell(pc, ref, c)

    for key, label, name, val, unit in MOS_ROWS:          # the switch's gate data
        r = drow[key]
        pc = X.ensure_row(pc, r)
        cell('B%d' % r, X.cell_t('B%d' % r, s_lab, label))
        cell('C%d' % r, X.cell_t('C%d' % r, s_lab, name))
        cell('D%d' % r, X.cell_n('D%d' % r, s_in, val))
        cell('E%d' % r, X.cell_t('E%d' % r, s_unit, unit))
    for key, kind, label, name, dval, unit, fcol in DRV_ROWS:
        r = drow[key]
        pc = X.ensure_row(pc, r)
        if kind == 'gap':
            continue
        if kind == 'title':
            cell('B%d' % r, X.cell_t('B%d' % r, s_title, label))
            continue
        if kind == 'part':
            cell('B%d' % r, X.cell_t('B%d' % r, s_partb, label))
            for col in 'CDE':
                cell('%s%d' % (col, r), X.cell_t('%s%d' % (col, r), s_part, name) if col == 'C'
                     else '<c r="%s%d" s="%s"/>' % (col, r, s_part))
            pc = add_merge(pc, 'C%d:E%d' % (r, r))
            continue
        if kind == 'head':
            for col, t in zip('BCDEF', (label, name, dval, unit, fcol)):
                if t:
                    cell('%s%d' % (col, r), X.cell_t('%s%d' % (col, r), s_head, t))
            continue
        cell('B%d' % r, X.cell_t('B%d' % r, s_lab, label))
        cell('C%d' % r, X.cell_t('C%d' % r, s_lab, name))
        if kind == 'data':
            cell('D%d' % r, X.cell_n('D%d' % r, s_in, dval))
        elif dval:
            cell('D%d' % r, X.cell_f('D%d' % r, s_val, sub(dval, 'pc')))
        else:
            cell('D%d' % r, '<c r="D%d" s="%s"/>' % (r, s_val))
        cell('E%d' % r, X.cell_t('E%d' % r, s_unit, unit))
        if fcol == 'in':
            cell('F%d' % r, X.cell_n('F%d' % r, s_in, sel[key]))
        elif fcol:
            cell('F%d' % r, X.cell_f('F%d' % r, s_lab, sub(fcol, 'pc')))
    parts[sp['Power Components']] = pc.encode('utf-8')
    add_picture(parts, sp, PNG, drow['h2'])

    # ---- CC working
    cc = parts[sp['CC']].decode('utf-8')
    st, stv = X.style_of(cc, 'B27'), X.style_of(cc, 'C21')
    for key, label, val, unit, data in CC_ROWS:
        r = ccrow[key]
        cc = X.ensure_row(cc, r)
        cc = X.set_cell(cc, 'B%d' % r, X.cell_t('B%d' % r, st, label))
        if val is None:
            continue
        cc = X.set_cell(cc, 'C%d' % r, X.cell_n('C%d' % r, s_in, val) if data
                        else X.cell_f('C%d' % r, stv, sub(val, 'cc')))
        cc = X.set_cell(cc, 'D%d' % r, X.cell_t('D%d' % r, st, unit))
    last_cc = CC0 + len(CC_ROWS) - 1
    cc = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="B3:AM%d"/>' % last_cc, cc, count=1)
    parts[sp['CC']] = cc.encode('utf-8')

    # ---- Res. Tank Design 81-86 (format of the peak table at 70-79)
    rt = parts[sp['Res. Tank Design']].decode('utf-8')
    s_t, s_h = X.style_of(rt, 'B70'), X.style_of(rt, 'B72')
    s_l, s_v, s_u = X.style_of(rt, 'B73'), X.style_of(rt, 'D73'), X.style_of(rt, 'E73')
    for r, ht in ((80, 14.25), (81, 18), (82, 3), (83, 15.75)):
        rt = X.ensure_row(rt, r)
        rt = set_ht(rt, r, ht)
    rt = X.set_cell(rt, 'B81', X.cell_t('B81', s_t, 'Start-up with the output near 0 V'))
    for col, t in zip('BCDEF', ('Parameters', 'Name', 'Value', 'Unit', 'Check')):
        rt = X.set_cell(rt, '%s83' % col, X.cell_t('%s83' % col, s_h, t))
    for i, (name, label, f, unit, chk) in enumerate(rt_rows(ccrow)):
        r = 84 + i
        rt = X.ensure_row(rt, r)
        rt = set_ht(rt, r, 15)
        rt = X.set_cell(rt, 'B%d' % r, X.cell_t('B%d' % r, s_l, label))
        rt = X.set_cell(rt, 'C%d' % r, X.cell_t('C%d' % r, s_l, name))
        rt = X.set_cell(rt, 'D%d' % r, X.cell_f('D%d' % r, s_v, f))
        rt = X.set_cell(rt, 'E%d' % r, X.cell_t('E%d' % r, s_u, unit))
        if chk:
            rt = X.set_cell(rt, 'F%d' % r, X.cell_f('F%d' % r, s_l, chk))
    rt = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="B4:G86"/>', rt, count=1)
    parts[sp['Res. Tank Design']] = rt.encode('utf-8')

    # ---- CHANGELOG
    last = AT2 + len(DRV_ROWS) - 1
    rr = max(int(x) for x in re.findall(r'<row r="(\d+)"', log)) + 2
    why = ('%s - ADDED (user, 2026-10-22). Power Components rows inserted (xl_rows.py, every reference '
           'followed): 76-82 the switch gate data (STO60N045DM9: C.g 7.5 nF Qg slope, C.gs 4.76 nF, R.g 4.5, '
           'V.pl 6.3, V.th 4.0 / 3.5, Q.gd 13 nC), 88-%d LLC Half Bridge Gate Driver Selection - part number, '
           'driver datasheet values (L6498LD), gate network (Value = recommendation, Selected Value = %s), '
           'results with five checks, schematic at G%d. Old rows 76-80 are now 83-87 and old 81-119 (the '
           'secondary section) 121-159; CHANGELOG entries above this line name the old rows. Res. Tank '
           'Design 81-86: start-up I.su, k.su (OCP2), f.su.OCP1. CC 77-%d: the working (gate_budget.py model).'
           % (MARK, last, sel['note'], drow['h2'], last_cc))
    for sheet, ref, text in ((None, None, why),
                             ('Power Components', 'B76:E82', 'switch gate data (yellow)'),
                             ('Power Components', 'B%d:F%d' % (AT2, last - 1), 'gate driver selection'),
                             ('Res. Tank Design', 'B81:F86', 'start-up: I.su, k.su, f.su.OCP1'),
                             ('CC', 'B77:D%d' % last_cc, 'gate drive working')):
        log = X.ensure_row(log, rr)
        for col, t in (('B', sheet), ('C', ref), ('F', text)):
            if t is not None:
                log = X.set_cell(log, col + str(rr), X.cell_t(col + str(rr), '8', t))
        rr += 1
    parts[sp['CHANGELOG_rev0_6']] = log.encode('utf-8')
    X.write_book(path, parts)
    print('written:', os.path.relpath(path, XL), ' PC 76-82, %d-%d' % (AT2, last))


if __name__ == '__main__':
    main()
