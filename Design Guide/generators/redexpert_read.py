# Read the REDEXPERT SVG exports of Wurth 885342208026 (47 nF / 630 V / X7R / 1206):
# the red curve is a cubic-Bezier path; its on-curve points are every third pair after M.
import re, sys, math
D = sys.argv[1]
def curve(name):
    s = open('%s/%s.svg' % (D, name), encoding='utf-8').read()
    m = re.search(r'<path\s+d="(M[^"]+)"\s+stroke="#e3000b"', s)
    toks = re.findall(r'[-+]?\d*\.?\d+(?:e[-+]?\d+)?', m.group(1))
    v = list(map(float, toks))
    pts = [(v[0], v[1])]
    rest = v[2:]
    for i in range(0, len(rest) - 5, 6):      # C c1x c1y c2x c2y x y
        pts.append((rest[i+4], rest[i+5]))
    return pts
def interp(pts, x):
    xs = [q[0] for q in pts]
    x = min(max(x, min(xs)), max(xs))          # clamp to the drawn range
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if (x0 <= x <= x1) or (x1 <= x <= x0):
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0) if x1 != x0 else y0
    return None
# ---- axis maps (from the tick lines and labels in each SVG)
LOGX = lambda f: 78.5 + 325.43 * math.log10(f / 100.0)          # FESR, FZ: 100 Hz -> 1 GHz
esr_of_y = lambda y: 10 ** ((1014.5 - y) / 235.75) * 1e-3        # ohm (1 mOhm .. 10 Ohm)
z_of_y   = lambda y: 10 ** ((1014.5 - y) / 138.43) * 1e-3        # ohm (1 mOhm .. 10 kOhm)
esr, z = curve('FESR'), curve('FZ')
print('== ESR / impedance vs frequency (small signal, REDEXPERT)')
print('%8s %9s %9s %9s %8s' % ('f kHz', 'ESR mOhm', 'Z ohm', 'C nF', 'DF %'))
for f in (1e3, 10e3, 100e3, 130e3, 150e3, 194.5e3, 200e3, 250e3, 300e3, 500e3, 1e6):
    x = LOGX(f); ye, yz = interp(esr, x), interp(z, x)
    R, Z = esr_of_y(ye), z_of_y(yz)
    Xc = math.sqrt(max(Z*Z - R*R, 1e-12)); C = 1/(2*math.pi*f*Xc)
    print('%8.1f %9.1f %9.2f %9.1f %8.2f' % (f/1e3, R*1e3, Z, C*1e9, 100*R/Xc))
# ---- capacitance vs DC bias
cdc = curve('CDC')
x_of_v = lambda V: 67.5 + (2357.5 - 67.5) * V / 700.0
c_of_y = lambda y: (1014.5 - y) / ((1014.5 - 45.5) / 60.0)          # nF
cdcv = curve('CDCV')
x2_of_v = lambda V: 77.5 + (2357.5 - 77.5) * V / 700.0
pct_of_y = lambda y: -(y - 153.5) / ((1014.5 - 153.5) / 80.0)        # %
print('\n== capacitance vs DC bias')
print('%7s %8s %8s   %s' % ('V dc', 'C nF', 'dC %', 'where it matters'))
notes = {0:'FB mode (no bias)', 41:'173 Vac HB edge, line peak, a piece (2S)', 81:'230 Vac HB line peak, a piece', 93:'264 Vac HB line peak, a piece', 163:'230 Vac HB, the whole 2S string (V_in/2)', 187:'264 Vac HB, the whole string'}
for V in (0, 20, 41, 50, 60, 81, 93, 105, 120, 140, 163, 187, 210, 300):
    C = c_of_y(interp(cdc, x_of_v(V))); p = pct_of_y(interp(cdcv, x2_of_v(V)))
    print('%7.0f %8.1f %8.1f   %s' % (V, C, p, notes.get(V, '')))
# effective (charge-averaged) capacitance of a piece over its swing at the line peak, 200 W and 657 W
def c_at(V): return c_of_y(interp(cdc, x_of_v(min(max(V, 0.0), 699.0))))
def c_eff(vlo, vhi, n=200):
    return sum(c_at(vlo + (vhi - vlo) * (i + 0.5) / n) for i in range(n)) / n
print('\n== charge-averaged capacitance of a piece over its swing (DC/4 +- AC/4 of the string)')
for name, dc_string, pp_string in (('230 HB, 200 W', 163, 120), ('264 HB, 200 W', 187, 100), ('173 HB edge, 657 W', 122, 403), ('230 HB, 657 W', 163, 311), ('264 HB, 657 W', 187, 252), ('110 FB, 200 W', 0, 180), ('90 FB, 657 W', 0, 394)):
    dc, pp = dc_string / 2.0, pp_string / 2.0
    ce = c_eff(dc - pp/2, dc + pp/2)
    print('  %-20s piece %5.0f V dc, swing %4.0f Vpp -> C_eff %5.1f nF (%+.0f %%) -> string %5.1f nF, f_r x %.2f' % (name, dc, pp, ce, 100*(ce/47.0-1), ce*5/2, math.sqrt(47.0/ce)))
# ---- capacitance vs AC voltage
cac = curve('CACV')
x3_of_v = lambda V: 77.5 + (2360.5 - 77.5) * V / 12.0
pct3 = lambda y: (608.5 - y) / 40.6
print('\n== capacitance change vs AC voltage (graph ends at 12 V rms; a piece sees ~22 V rms at 200 W)')
for V in (0.5, 1, 2, 5, 8, 9.9):
    print('  %4.1f V rms: %+.1f %%' % (V, pct3(interp(cac, x3_of_v(V)))))
# ---- 200 W loss with the small-signal ESR
print('\n== 200 W loss with the small-signal ESR: 10 pieces x 1.27 A rms each')
for f in (130e3, 150e3, 194.5e3, 250e3):
    R = esr_of_y(interp(esr, LOGX(f)))
    print('  at %.0f kHz: ESR %.0f mOhm -> %.2f W a piece, %.1f W in all' % (f/1e3, R*1e3, 1.27**2*R, 10*1.27**2*R))
# split: magnetising part ~1.0 A rms a piece at ~130 kHz, load pulse ~0.8 A at f_r (the 200 W primary current is mostly magnetising)
Rm, Rl = esr_of_y(interp(esr, LOGX(130e3))), esr_of_y(interp(esr, LOGX(194.5e3)))
print('  split 1.0 A @130 kHz + 0.8 A @194.5 kHz: %.2f W a piece, %.1f W in all' % (1.0**2*Rm + 0.8**2*Rl, 10*(1.0**2*Rm + 0.8**2*Rl)))
