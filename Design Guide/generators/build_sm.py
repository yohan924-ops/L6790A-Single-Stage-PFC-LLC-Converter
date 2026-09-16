# -*- coding: utf-8 -*-
import sys, os, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smgen import Sheet
COMPACT = os.environ.get('COMPACT')=='1'

S=Sheet('L6790A Single-Stage PF LLC - Section 3 : power stage and resonant tank',
        'design guide rev 1.1',
        'SMath port of equations [6]-[54]. rev 0.8: every displayed quantity now really evaluates, region spacing widened, no hand-typed values.')

if COMPACT:
    # one printed page : no figures, no prose, short tags, three columns
    S.pic = lambda *a, **k: None
    _text = S.text
    def _t(lines, size=10, bold=False, box=False, color='#000000', w=760):
        if box: _text(lines, size=10, bold=True, box=True, color=color, w=600)   # section headings only
    S.text = _t
    _math, _show = S.math, S.show
    def _tag(d):
        m = re.match(r'\s*(\[[0-9a-z]+\])', d or '')
        return m.group(1) if m else ''
    def _m(lhs, srcx, desc='', h=None, contract=None):
        _math(lhs, srcx, _tag(desc), h=h, contract=contract)
    def _s(srcx, desc='', contract=None, h=32):
        _show(srcx, '', contract=contract, h=h)
    S.math, S.show = _m, _s

OHM = "'ohm"   # lowercase: SMath's resistance unit.  'Ohm (capital O) is NOT recognised.

if COMPACT:
    S.gap=10
    S.setcols([20, 590, 1160, 1730], 2830, ytop=70)   # 4 columns, one A1 page
S.text(['L6790A  Single-Stage PF LLC  —  Section 3 :  power stage and resonant tank'],size=14,bold=True)
S.text(['This sheet sizes the resonant tank of a single-stage power-factor-corrected LLC converter.',
        'It is equations [6]-[54] of the design guide, made live: change any input, press F9, everything follows.',
        '',
        'EVERY number in this sheet is computed. Nothing is typed in by hand. The boxed note to the right of a',
        'result says what the quantity is; the cross-check lines in bold list the values it should land on.',
        '',
        'rev 1.1 : the resistance unit is written  ohm  (lowercase).  The token  Ohm  with a capital O is NOT',
        'recognised by SMath and behaves as a dimension of its own - that was the original cause of the error 74',
        'on Pd.BR, eta.tot and Pin.  The V/A workaround used in rev 1.0 is no longer needed.',
        '',
        'rev 1.0 : the real cause of the [36]/[37] failures, found by running the probes in 3.8b.',
        '  (1) MV.min carried a hidden unit tag, so ln() and any fractional power on it were refused with',
        '      "Operation cannot be performed with units".  The tag came from Vin.min, where abs() had been',
        '      applied to a quantity in volts.  Both are fixed: abs() now acts on pure numbers, and the gains',
        '      are formed from voltages that are explicitly divided by 1 V.',
        '  (2) The inverse tangent is  atan .  arctan does not exist in this build - rev 0.9 guessed wrong.',
        'Section 3.8b keeps five one-line probes so the cause is visible immediately if it ever breaks again.',
        '',
        'rev 0.8 : each displayed quantity carries a real result element, so SMath actually evaluates and prints it',
        '(in rev 0.7 only the note appeared, which made the notes look like hand-entered values).',
        'Region spacing was widened so nothing overlaps in print.',
        '',
        'rev 0.7 fixed three things that broke the rev 0.6 sheet:',
        '  (1) every expression now carries explicit display brackets, so the printed formula matches what is computed;',
        "  (2) the unit  Ohm  is replaced everywhere by  V/A  — SMath did not treat 'Ohm as V/A, which made P_d.BR",
        '      a mismatched sum (W + Ohm*A^2) and put an error on eta.tot, P.in and everything downstream;',
        '  (3) fn.min and fn.act are rewritten with a positive exponent and a reciprocal instead of a negative exponent.'],size=9)

S.head('0.  Symbols used in this sheet')
S.text(['INPUTS      Vac.min/max mains rms range | fl line frequency | Vout, Pout output | Nrect 1 = centre tap, 2 = full bridge',
        '            Vrect one rectifier drop | ηHB assumed LLC efficiency | frT target series resonance',
        '            fswMax/fswMin design frequency window | cHB half-bridge midpoint capacitance | tD dead time',
        '            VfBR, Rd input bridge drop and dynamic resistance | REMI EMI filter resistance',
        '            Vin.nom equivalent input for resonant operation | δres above-resonance margin | mZVS ZVS margin on Q',
        '',
        'DERIVED     Vo.eff reflected output voltage = Vout + Nrect*Vrect  (do NOT divide by Nrect again)',
        '            n equivalent-model turns ratio Np/Ns | n.T real ratio if Lr is the transformer leakage',
        '            MV.min / MV.max required tank gain at the two ends of the EQUIVALENT input range',
        '            lambda = Lr/Lm  — sets how tall and how steep the gain curve is',
        '            Rac  the transformer + rectifier + load collapsed into one resistor',
        '            Q = Z0/Rac  how heavily the tank is loaded | Z0 tank characteristic impedance',
        '            fr = 1/(2*pi*sqrt(Lr*Cr)) series resonance | fo lower resonance = the FREQUENCY FLOOR',
        '            fn = fsw/fr normalised frequency | TZC instant at which the tank current crosses zero'],size=9)

S.head('First, what the circuit actually is')
S.pic('fig/f_llc_sch.png','Figure: half-bridge LLC resonant converter — square-wave generator, resonant network, rectifier network.  [ onsemi / Fairchild AN-4151, Fig. 3 ]',w=520)
S.pic('fig/f_llc_wave.png','Figure: typical waveforms. Ip is the sum of the magnetising current Im and the reflected secondary current.  [ onsemi / Fairchild AN-4151, Fig. 4 ]',w=440)
S.text(['The idea in three lines:',
        '  1. The switches make a square wave. Only its FREQUENCY can be changed, never its height.',
        '  2. The tank turns that square wave into a sine and decides how much voltage reaches the transformer.',
        '  3. In THIS converter the input is the raw rectified mains, so the voltage the tank must produce is',
        '     forced on it from outside. Frequency then controls POWER, not voltage.'],size=9)
S.pic('fig/c_block.png','Two-stage versus single-stage: the boost PFC and the 400 V bulk capacitor both disappear; the energy store moves to the output.',w=560)

# ---------------- 3.1 ----------------
S.head('3.1   Target specification  (inputs)')
S.text(['Everything below is a number you choose. Everything after it is derived. Come back here when a check fails.'],size=9)
for lhs,src,d in [
 ('Vac.min',"90*'V",'minimum mains voltage'),
 ('Vac.max',"264*'V",'maximum mains voltage'),
 ('fl',"50*'Hz",'line frequency'),
 ('fl.min',"47*'Hz",'minimum line frequency'),
 ('Vout',"60*'V",'regulated output voltage'),
 ('Pout',"240*'W",'output power'),
 ('Nrect','2','secondary rectifier:  1 = centre tap,  2 = full bridge'),
 ('Vrect',"0*'V",'rectifier forward drop, ONE device'),
 ('ηHB','0.98','assumed LLC stage efficiency'),
 ('frT',"150*'kHz",'target series resonant frequency'),
 ('fswMax',"225*'kHz",'design maximum switching frequency'),
 ('fswMin',"50*'kHz",'design minimum switching frequency'),
 ('cHB',"500*'pF",'half-bridge midpoint parasitic capacitance'),
 ('tD',"220*'ns",'reference dead time   (rev0.5 : 270 -> 220 ns, see guide 3.8 / [38a])'),
 ('VfBR',"0.08*'V",'input bridge forward drop, one diode'),
 ('Rd',"0.04*"+OHM,'input bridge dynamic resistance, one diode'),
 ('REMI',"0.15*"+OHM,'EMI filter equivalent resistance'),
 ('Vin.nom',"225*'V",'equivalent input voltage for resonant operation'),
 ('δres','0.05','above-resonance modulation depth'),
 ('mZVS','0.15','ZVS margin on Q'),
]:
    S.math(lhs,src,d,h=30)

# ---------------- 3.2 ----------------
S.head('3.2   Power budget   [6] - [17]')
S.text(['Before sizing anything, find how much power has to go INTO the converter — that is what the tank',
        'and the current-sense resistor are sized for. Work backwards from Pout.'],size=9)
for lhs,src,d,h in [
 ('Iout','Pout/Vout','[6]   output current',46),
 ('ηrect','Vout/(Vout+Nrect*Vrect)','[7]   rectifier efficiency',46),
 ('Psec','Pout/ηrect','[8]   transformer output power',46),
 ('Pin.LLC','Pout/(ηrect*ηHB)','[9]   LLC input power',46),
 ('Iin.max','Pin.LLC/Vac.min','[10]  maximum mains rms current',46),
 ('Pd.rect','Pout*(1-ηrect)/ηrect','[11]  output rectifier loss',46),
 ('Pd.LLC','Psec*(1-ηHB)/ηHB','[12]  transformer + MOSFET loss',46),
 ('Pd.BR',"2*(2*sqrt(2)/π*Iin.max*VfBR)+2*Rd*Iin.max^2",'[13]  input bridge loss',48),
 ('Pd.EMI','REMI*Iin.max^2','[14]  EMI filter loss',34),
 ('ηac','Pin.LLC/(Pin.LLC+Pd.BR+Pd.EMI)','[15]  front-end efficiency',48),
 ('ηtot','ηHB*ηrect*ηac','[16]  total efficiency',32),
 ('Pin','Pout/ηtot','[17]  rated input power',46),
]:
    S.math(lhs,src,d,h=h)
S.text(['Results  —  expected:  Iout 4 A, eta.rect 1, Psec 240 W, Pin.LLC 244.90 W, Iin.max 2.721 A,',
        'Pd.LLC 4.898 W, Pd.BR 0.9843 W, Pd.EMI 1.111 W, eta.ac 0.9915, eta.tot 0.9717, Pin 246.99 W'],size=9,bold=True)
S.show('Iout','output current',"'A")
S.show('\u03b7rect','rectifier efficiency')
S.show('Psec','transformer output power',"'W")
S.show('Pin.LLC','expected 244.898 W',"'W")
S.show('Iin.max','expected 2.7211 A',"'A")
S.show('Pd.LLC','transformer + MOSFET loss',"'W")
S.show('Pd.BR','expected 0.9843 W  — this is the sum that failed in rev 0.6',"'W")
S.show('Pd.EMI','EMI filter loss',"'W")
S.show('\u03b7ac','front-end efficiency')
S.show('\u03b7tot','expected 0.9717')
S.show('Pin','expected 246.993 W',"'W")

# ---------------- 3.3 ----------------
S.head('3.3   Equivalent design input voltage — the effect of morphing   [18] - [20]')
S.pic('fig/c_morph.png','Topology morphing: below 235 Vpk the IC runs a full bridge (tank sees 2x Vin), above 245 Vpk a half bridge (tank sees Vin/2).',w=560)
S.text(['A full bridge drives the tank twice as hard as a half bridge from the same supply. So at low line the chip',
        'uses the full bridge and the tank behaves as if the input were doubled. BUT the worst equivalent input is',
        'NOT 2*Vac.min : it is the HB side of the morphing threshold, VmorHB/sqrt2 = 173.2 Vac. The highest',
        'equivalent input is the FB side, 2*VmorFB/sqrt2 = 332.3 Vac.'],size=9)
S.pic('fig/c_range.png','The two morphing edges are the real ends of the equivalent input range: 173.2 ... 332.3 Vac  (1.92 : 1).',w=520)
S.math('VmorHB',"245*'V",'[DS]  HB <- FB morphing threshold, peak mains',h=30)
S.math('VmorFB',"235*'V",'[DS]  FB -> HB morphing threshold, peak mains',h=30)
S.math('Vin.min',"(2*(Vac.min/'V)+(VmorHB/'V)/sqrt(2)-abs(2*(Vac.min/'V)-(VmorHB/'V)/sqrt(2)))/2*'V",
       '[18]  min( 2*Vac.min , VmorHB/sqrt2 ).  abs() is applied to PURE NUMBERS and the volt is put back afterwards '
       '\u2014 abs() on a unit quantity leaves a tag that later blocks ln() and fractional powers.',h=60)
S.math('Vin.max','Vac.max','[19]  half bridge at high line',h=30)
S.math('Vin.res','Vin.nom*(1-δres)','[20]  input voltage for resonant operation',h=32)
S.show('Vin.min','expected 173.241 Vac',"'V")
S.show('Vin.max','expected 264 Vac',"'V")
S.show('Vin.res','expected 213.75 Vac',"'V")

# ---------------- 3.4 ----------------
S.head('3.4   Turns ratio   [21] - [22]      <-- corrected definition, differs from the ST tool')
S.text(['Vo.eff is the reflected equivalent output voltage. The rectifier drop is counted once per series device',
        '(Nrect of them). Do NOT divide by Nrect a second time — see appendix C.5 of the guide.'],size=9)
S.math('Vo.eff','Vout+Nrect*Vrect','[21]  reflected equivalent output voltage',h=32)
S.show('Vo.eff','expected 60 V',"'V")
S.math('n.calc','sqrt(2)*Vin.res/(2*Vo.eff)','[22]  physical turns ratio Np/Ns',h=48)
S.show('n.calc','expected 2.5191')
S.math('n','2.5','SELECTED turns ratio (rounded)',h=30)
S.show('n*Vo.eff','reflected voltage — expected 150 V.  ALWAYS check this number, not n alone',"'V")

# ---------------- 3.5 ----------------
S.head('3.5   Required gain range   [23] - [24]')
S.text(['How much voltage boost the tank must produce at the peak of the mains, at each end of the equivalent range.'],size=9)
S.math('MV.min',"2*n*(Vo.eff/'V)/(sqrt(2)*(Vin.min/'V))","[23]  gain at low line, line peak. Each voltage is divided by 1 V so the gain is a STRICTLY unitless number \u2014 SMath needs that for ln() and for a variable exponent.",h=52)
S.math('MV.max',"2*n*(Vo.eff/'V)/(sqrt(2)*(Vin.max/'V))",'[24]  gain at high line, line peak',h=52)
S.show('MV.min','expected 1.2245   (at 173.2 Vac equivalent, not 180)')
S.show('MV.max','expected 0.8035')

# ---------------- 3.6 ----------------
S.head('3.6   Selection of  lambda = Lr / Lm   [26] - [30]')
S.pic('fig/f_gain_q.png','Figure: gain curves of an LLC tank for several Q. Light load = tall peaky curve, heavy load = flat curve.  [ onsemi / Fairchild AN-4151, Fig. 7 ]',w=470)
S.pic('fig/f_inf_gainm.png','Figure: the same family plotted for different m = Lp/Lr at fixed Q. A LOWER m (larger lambda) lifts the whole curve.  [ Infineon AN 2013-03, Fig. 3.2 ]',w=470)
S.text(['lambda decides how tall and how steep these curves are. Bigger lambda = more gain available, but also',
        'more circulating current. Four conditions each set a floor; take the largest.'],size=9)
S.math('λ1','1/MV.max-1','[26]  minimum gain criterion',h=46)
S.math('λ2','λ1/(1-(frT/fswMax)^2)','[27]  maximum frequency criterion',h=56)
S.math('λTD','λ1/(1-π^2/8*(frT/fswMax)^2)','[28]  maximum frequency including dead time',h=56)
S.math('λ3','(fswMin/frT)^2/(1-(fswMin/frT)^2)','[29]  minimum frequency criterion',h=56)
S.math('λa','(λ1+λ2+abs(λ1-λ2))/2','helper: max of the first two',h=46)
S.math('λb','(λTD+λ3+abs(λTD-λ3))/2','helper: max of the last two',h=46)
S.math('λ','(λa+λb+abs(λa-λb))/2','[30]  take the largest',h=46)
S.text(['Expected:  lambda1 0.2445,  lambda2 0.4401,  lambdaTD 0.5413,  lambda3 0.1250   ->   lambda = 0.5413'],size=9,bold=True)
for v,d in (('λ1','[26] minimum gain'),('λ2','[27] maximum frequency'),('λTD','[28] max frequency incl. dead time'),('λ3','[29] minimum frequency'),('λ','[30] the largest — this is the design lambda')): S.show(v,d)
S.text(['NOTE. lambda = 0.54 means m = 1 + 1/lambda = 2.85, far below the classic 3...8 of a two-stage LLC.',
        'Apply the conventional Lm/Lr = 5...10 here and the converter will not start at low line.'],size=9)

# ---------------- 3.7 ----------------
S.head('3.7   Equivalent load resistance and quality factor   [31] - [35]')
S.pic('fig/f_ac_equiv.png','Figure: the rectifier and load are replaced by one ac resistance Rac; the tank then becomes a simple RLC divider.  [ onsemi / Fairchild AN-4151, Fig. 5 and 6 ]',w=430)
S.text(['CAUTION — this Rac is NOT the classic one. A conventional LLC uses Rac = 8/pi^2 * n^2 * Vo^2 / Po.',
        'Here the coefficient is 4/pi^2 and the power is the LLC INPUT power, because Rac is defined at the',
        'LINE-PEAK instantaneous power 2*Pin. Q therefore is the value at the line peak, and Q(theta) = Q*sin^2(theta).'],size=9)
S.math('Rac','4/π^2*n^2*Vo.eff^2/Pin.LLC','[31]  defined at the line-peak power 2*Pin',h=56)
S.math('QZ1','λ/MV.min*sqrt(1/λ+MV.min^2/(MV.min^2-1))','[32]  ZVS at Vin.min, full load',h=58)
S.math('QZ2',"2/π*λ*(tD/'s)/((Rac/'ohm)*(cHB/'F))",'[33]  ZVS at Vin.max, no load. Written so that the s / (ohm x F) cancellation is explicit.',h=54)
S.math('QZVS','(QZ1+QZ2-abs(QZ1-QZ2))/(2*(1+mZVS))','[34]  smaller of the two, with margin',h=50)
S.math('Z0','Rac*QZVS','[35]  tank characteristic impedance',h=30)
S.text(['Expected:  Rac 37.24 ohm,  QZ1 0.9736,  QZ2 4.073,  QZVS 0.8466,  Z0 31.52 ohm'],size=9,bold=True)
S.show('Rac','equivalent ac load resistance',OHM)
S.show('QZ1','[32]'); S.show('QZ2','[33]'); S.show('QZVS','[34] selected quality factor')
S.show('Z0','tank characteristic impedance',OHM)
S.pic('fig/f_peakgain.png','Figure: attainable peak gain versus Q for a family of m. Reducing m (raising lambda) is what buys gain.  [ onsemi / Fairchild AN-4151, Fig. 14 ]',w=430)

# ---------------- 3.8 ----------------
S.head('3.8   ZVS verification   [36] - [42]')
S.pic('fig/f_zvs_cap.png','Figure: inductive (ZVS) versus capacitive (hard-switched) operation. The tank must stay on the RIGHT of the gain peak.  [ onsemi / Fairchild AN-4151, Fig. 12 ]',w=430)
S.pic('fig/f_inf_ires.png','Figure: total tank current = reflected load current + magnetising current. The magnetising part is what achieves ZVS.  [ Infineon AN 2013-03, Fig. 3.5 ]',w=430)
S.text(['Both switches are off for a short dead time. The tank current must still be flowing then, so that it can pull',
        'the next switch down to zero volts before it turns on. The test is simply: does that happen in time?',
        '',
        'rev 0.7: the exponent is written as a separate variable kZ and applied as a POSITIVE power followed by a',
        'reciprocal. The rev 0.6 form used a negative exponent and SMath refused to evaluate it.'],size=9)
S.math('kZ','1+(QZVS/QZ1)^5','exponent of [36], kept separate for clarity  (expected 1.4972)',h=34)
S.math('lnM','ln(MV.min)','natural log of the required gain  (expected 0.2025)',h=30)
S.math('MVpow','exp(kZ*lnM)','MV.min raised to kZ, written as exp(kZ*ln M)   (expected 1.3542)',h=32)
S.math('fn.min','1/sqrt(1+(1-1/MVpow)/λ)','[36]  normalised minimum frequency',h=60)
S.math('φmin','atan(((ι^2+λ+(fn.min^2-1)*QZVS^2)*fn.min^2-λ^2)/(QZVS*fn.min^3))','[37]  tank phase shift [rad]',h=62)
S.math('TZC','φmin/(2*π*fn.min*frT)','[38]  resonant-current zero-crossing instant',h=48)
S.math('IR1.pk','2*π*Pout/(sqrt(2)*ηHB*Vin.min*cos(φmin))','[40]  peak resonant current — uses 2*P, see guide 3.8',h=50)
S.math('IR0','IR1.pk*sin(φmin)','[41]  minimum current needed for ZVS',h=32)
S.math('TT','cHB*sqrt(2)*Vin.min/IR0','[42]  midpoint transition time',h=48)
S.text(['Expected:  kZ 1.4972,  lnM 0.2025,  MVpow 1.3542,  fn.min 0.8211,  phi.min 0.2348 rad,  TZC 303.4 ns  (closed form with the DESIGN Q),',
        'IR1.pk 6.458 A,  IR0 1.502 A,  TT 81.6 ns.   Re-check with the AS-BUILT Q in section 3.12.'],size=9,bold=True)
S.show('kZ','exponent of [36]'); S.show('lnM','ln(MV.min)'); S.show('MVpow','MV.min^kZ'); S.show('fn.min','normalised minimum frequency'); S.show('φmin','rad')
S.show('TZC','ns',"'ns"); S.show('IR1.pk','A',"'A"); S.show('IR0','A',"'A"); S.show('TT','ns',"'ns")
S.show('TZC-tD','[39]  must be POSITIVE, otherwise increase mZVS',"'ns")


# ---------------- 3.8b  probes ----------------
S.head('3.8b   Three one-line probes  —  read these if section 3.8 still shows errors')
S.text(['rev 0.8 failed here and the cause was not obvious, so the two suspect constructs are isolated below.',
        'Everything in 3.8 is now written the way that avoids them, but leave these probes in place: if the sheet',
        'ever breaks again at [36], one look tells you which construct SMath refused.',
        '',
        'dbg1 : a pure number raised to a VARIABLE exponent.        expected 2.8229',
        'dbg2 : a computed ratio raised to a LITERAL exponent.      expected 1.3542',
        'dbg3 : a computed ratio raised to a VARIABLE exponent.     expected 1.3542   <-- the rev 0.8 form',
        'dbg4 : atan of a plain number.                            expected 0.7854 rad',
        'dbg5 : ln of the required gain.                           expected 0.2025',
        '',
        'How to read them:',
        '   dbg1 OK, dbg2 OK, dbg3 FAILS  ->  SMath will not take a variable exponent on a computed value.',
        '                                     The exp(k*ln M) form used above is the correct workaround.',
        '   dbg2 FAILS as well            ->  MV.min still carries a hidden V/V unit; divide it out explicitly.',
        '   dbg5 FAILS ("Operation cannot be performed with units")',
        '                                 ->  MV.min still carries a unit tag. Divide every voltage by 1 V where',
        '                                     the gain is formed, and keep abs() away from unit quantities.',
        '   dbg4 FAILS                    ->  the inverse tangent is named differently in your build.',
        '                                     SMath 1.5 calls it  atan ;  arctan is NOT defined.'],size=9)
S.math('dbg1','2^kZ','pure number base, VARIABLE exponent',h=30)
S.show('dbg1','expected 2.8229')
S.math('dbg2','MV.min^1.4972','computed base, LITERAL exponent',h=30)
S.show('dbg2','expected 1.3542')
S.math('dbg3','MV.min^kZ','computed base, VARIABLE exponent  —  this is the construct that failed in rev 0.8',h=30)
S.show('dbg3','expected 1.3542')
S.math('dbg4','atan(1)','inverse tangent of 1  \u2014 the function is called atan, NOT arctan',h=30)
S.show('dbg4','expected 0.7854 rad')
S.math('dbg5','ln(MV.min)','natural log of the gain  \u2014 this is the operation that failed in rev 0.9',h=30)
S.show('dbg5','expected 0.2025')

# ---------------- 3.9 ----------------
S.head('3.9   Resonant tank components   [43] - [45]')
S.text(['Each part is calculated, then rounded to a standard value, and the next calculation uses the ROUNDED value.',
        'That is why every part appears twice below.'],size=9)
S.math('Cr.calc','1/(2*π*frT*Z0)','[43]  calculated resonant capacitor',h=48)
S.show('Cr.calc','expected 33.66 nF',"'nF")
S.math('Cr',"33*'nF",'SELECTED standard value',h=30)
S.math('Lr.calc','1/(Cr*(2*π*frT)^2)','[44]  recomputed from the SELECTED Cr',h=50)
S.show('Lr.calc','expected 34.11 uH',"'μH")
S.math('Lr',"34*'μH",'SELECTED',h=30)
S.math('Lm.calc','Lr/λ','[45]  from the SELECTED Lr',h=46)
S.show('Lm.calc','expected 62.81 uH',"'μH")
S.math('Lm',"65*'μH",'SELECTED  —  never round Lm UP, see the note in 3.12',h=30)

# ---------------- 3.10 ----------------
S.head('3.10   Final tank check   [46] - [54]')
S.text(['Recompute everything from the parts actually chosen. These are the numbers to put on the drawing.'],size=9)
S.math('λact','Lr/Lm','[46]  actual inductance ratio',h=46)
S.math('n.T','n*sqrt(1+λact)','[47]  real turns ratio (leakage-integrated build)',h=32)
S.math('Z0.s','sqrt(Lr/Cr)','[48]  series characteristic impedance',h=48)
S.math('Z0.p','sqrt((Lr+Lm)/Cr)','[49]  parallel characteristic impedance',h=48)
S.math('fr','1/(2*π*sqrt(Lr*Cr))','[50]  actual series resonance',h=48)
S.math('fn0','sqrt(λact/(1+λact))','[51a] normalised lower resonance',h=48)
S.math('fo','fr*fn0','[51b] lower resonance — THE FREQUENCY FLOOR',h=30)
S.math('Lμ','sqrt(Lm*(Lm+Lr))','[52]  physical magnetising inductance',h=34)
S.math('LL1','Lm+Lr-Lμ','[53]  primary side leakage',h=30)
S.math('LL2','LL1/n.T^2','[54]  secondary side leakage',h=48)
S.text(['Expected:  lambda.act 0.5231,  n.T 3.085,  Z0.s 32.10,  Z0.p 54.77,  fr 150.25 kHz,',
        'fn0 0.5860,  fo 88.05 kHz,  Lmu 80.22 uH,  LL1 18.78 uH,  LL2 1.973 uH'],size=9,bold=True)
S.show('λact','actual inductance ratio'); S.show('n.T','real turns ratio')
S.show('Z0.s','series characteristic impedance',OHM); S.show('Z0.p','parallel characteristic impedance',OHM)
S.show('fr','kHz',"'kHz"); S.show('fn0','normalised lower resonance'); S.show('fo','kHz  <-- keep the VCO minimum clamp at or above this',"'kHz")
S.show('Lμ','physical magnetising inductance',"'μH"); S.show('LL1','primary leakage',"'μH"); S.show('LL2','secondary leakage',"'μH")

# ---------------- 3.11 ----------------
S.head('3.11   Summary of results   (press F9 after any edit)')
S.text(['Every number below is computed by this sheet. The note on the right says only what the quantity IS.',
        'Nothing here is typed in by hand \u2014 if a value looks wrong, fix the input in 3.1 and press F9.'],size=9)
for v,d,c in [('Pin','rated input power',"'W"),
              ('n','turns ratio Np/Ns  (the ST tool prints twice this for Nrect = 2 \u2014 see appendix C.5)',None),
              ('n.T','real turns ratio, leakage-integrated build',None),
              ('\u03bb','design lambda',None),
              ('\u03bbact','actual lambda from the SELECTED parts',None),
              ('QZVS','design quality factor',None),
              ('Z0','design characteristic impedance',OHM),
              ('Cr','selected resonant capacitor',"'nF"),
              ('Lr','selected series inductance',"'\u03bcH"),
              ('Lm','selected magnetising inductance',"'\u03bcH"),
              ('fr','series resonance',"'kHz"),
              ('fo','lower resonance \u2014 the FREQUENCY FLOOR, keep the VCO clamp at or above it',"'kHz"),
              ('Z0.s','as-built series characteristic impedance',OHM),
              ('Z0.p','as-built parallel characteristic impedance',OHM),
              ('L\u03bc','physical magnetising inductance to specify on the drawing',"'\u03bcH"),
              ('LL1','primary side leakage',"'\u03bcH"),
              ('LL2','secondary side leakage',"'\u03bcH"),
              ('TZC','closed-form zero-crossing instant \u2014 must exceed tD (see 3.12 for the as-built value)',"'ns"),
              ('IR1.pk','peak resonant current',"'A")]:
    S.show(v,d,c)
S.text(['Cross-check against the design guide rev 0.7:  Pin 246.99 W | n 2.5 | n.T 3.085 | lambda 0.5413 | lambda.act 0.5231',
        'QZVS 0.8466 | Z0 31.52 | Cr 33 nF | Lr 34 uH | Lm 65 uH | fr 150.25 kHz | fo 88.05 kHz | Z0.s 32.10 | Z0.p 54.77',
        'Lmu 80.22 uH | LL1 18.78 uH | LL2 1.973 uH | TZC 303.4 ns | IR1.pk 6.458 A'],size=9,bold=True)

# ---------------- 3.12 ----------------
S.head('3.12   Morphing corner re-check')
S.pic('fig/c_fsw.png','Switching frequency over one line half cycle. All curves converge to fo at the zero crossing; the maximum is set by the FB morphing edge.',w=560)
S.text(['Sections 3.5 - 3.9 were solved at Vin.min = the HB side of the morphing threshold (173.2 Vac).',
        'Two things still have to be checked, because neither the ST tool nor earlier revisions evaluated them:',
        '   (a) the FB side of the threshold is the HIGHEST equivalent input (332.3 Vac) — it fixes the maximum frequency;',
        '   (b) after rounding Cr / Lr / Lm the real Q is Z0.s / Rac, which is LARGER than the design QZVS.'],size=9)
S.math('Vin.FBmax','2*VmorFB/sqrt(2)','[19]  highest equivalent input : FB side of the morphing threshold',h=48)
S.math('MV.FBmax',"2*n*(Vo.eff/'V)/(sqrt(2)*(Vin.FBmax/'V))",'minimum required gain, at the FB threshold',h=52)
S.math('M.inf','1/(1+λact)','no-load gain asymptote — below this the converter must burst',h=46)
S.text(['Expected: Vin.FBmax 332.34 Vac, MV.FBmax 0.6383, M.inf 0.6566.  MV.FBmax < M.inf, so at light load near',
        'this point the required gain is below the no-load ceiling and the IC has to burst. At FULL load the solution',
        'does exist, at fn = 1.603 -> fsw = 240.9 kHz. That, not 187 kHz, is the maximum operating frequency.'],size=9,bold=True)
S.show('Vin.FBmax','Vac',"'V"); S.show('MV.FBmax','required gain at the FB threshold'); S.show('M.inf','no-load gain ceiling')
S.text(['Now the as-built quality factor and the ZVS re-check at the worst corner (Vin.min = 173.2 Vac).',
        'rev 0.6 fix: the as-built check uses the as-built lambda too, not the design lambda.'],size=9)
S.math('Q.act','Z0.s/Rac','real line-peak Q after rounding the tank to standard values',h=46)
S.math('kZa','1+(Q.act/QZ1)^5','exponent of [36] with the as-built Q  (expected 1.5443)',h=34)
S.math('MVpowA','exp(kZa*lnM)','MV.min raised to kZa  (expected 1.3672)',h=32)
S.math('fn.act','1/sqrt(1+(1-1/MVpowA)/λact)','[36] with the as-built Q AND the as-built lambda',h=60)
S.math('φact','atan(((λact^2+λact+(fn.act^2-1)*Q.act^2)*fn.act^2-λact^2)/(Q.act*fn.act^3))',
       '[37] with the as-built Q AND the as-built lambda',h=62)
S.math('TZC.act','φact/(2*π*fn.act*frT)','[38]  zero-crossing instant, as built',h=48)
S.math('ZVSmargin.act','TZC.act-tD','ZVS margin, as built.  MUST be > 0',h=30)
S.show('Q.act','as-built line-peak Q'); S.show('kZa','exponent'); S.show('MVpowA','MV.min^kZa'); S.show('fn.act','normalised frequency'); S.show('φact','rad')
S.show('TZC.act','ns',"'ns"); S.show('ZVSmargin.act','ns  — must be positive',"'ns")
S.text(['Expected: Q.act 0.8620 (design QZVS was 0.8466), fn.act 0.8129, phi.act 0.1841 rad, TZC.act 240.3 ns.',
        'WARNING: this closed form is approximate near the ZVS border. Solving the ACTUAL operating point [38a] gives',
        '246 ns (fn 0.8148, phi 0.1896) — that is the number to trust. With tD = 220 ns that is 12 % margin.',
        'Remedies if you want more: Lm = 62 uH instead of 65 (310 ns), or Cr 39 nF / Lr 29 uH / Lm 54 uH (503 ns).',
        'Never round Lm UP: 62.81 -> 65 uH lowered lambda.act to 0.5231 and cost 64 ns of ZVS margin.',
        'Also check that the VCO MAXIMUM frequency clears 240.9 kHz: with Tidle = 350 ns fMax = 291 kHz (21 % margin),',
        'with Tidle = 700 ns fMax = 241.8 kHz (no margin at all).'],size=9)
S.pic('fig/c_ilr.png','Total tank current at the worst corner. The OCP margin must be judged on the SUM, not on the load component alone.',w=520)

# ---------------- 3.13 ----------------
S.head('3.13   Which ratio do you actually wind ?')
S.text(['n and n.T are the SAME tank, expressed for two different physical builds:',
        '   - discrete resonant inductor : transformer Np/Ns = n = 2.5, Lm = 65 uH, leakage negligible, plus a 34 uH inductor.',
        '   - leakage-integrated transformer : Np/Ns = n.T = 3.085, open-circuit inductance Lmu + LL1 = 99 uH,',
        '     short-circuit inductance = 34 uH.',
        'They are linked exactly by   n = n.T * Lmu / (Lmu + n.T^2 * LL2) = 3.085 * 80.22 / 99 = 2.500 .',
        'The ST tool labels n "Physical Turn Ratio" AND n.T "Real Turn Ratio" — both cannot be the physical ratio.',
        'Put the OPEN-CIRCUIT and SHORT-CIRCUIT inductances on the transformer drawing, not just a turns ratio.'],size=9)
S.math('n.check','n.T*Lμ/(Lμ+n.T^2*LL2)','cross-check: must come back to n = 2.500',h=50)
S.show('n.check','expected 2.5')

if COMPACT:
    S.paper_id=0; S.paper_or='Portrait'; S.paper_w=2295; S.paper_h=S.maxy+40
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Smath', 'L6790A_Section3_Calculation_Sheet_1page.sm')
else:
    OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Smath', 'L6790A_Section3_PowerStage_Tank_rev1_1.sm')
print('bytes',S.save(OUT),'regions',len(S.r),'maxy',S.maxy)
