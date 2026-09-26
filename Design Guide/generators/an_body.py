# -*- coding: utf-8 -*-
"""The text of the application note.

Kept apart from an_pdf.py, which is the layout engine, so that editing the
prose never risks the page furniture. Every number is interpolated from
an_pdf.V, which comes from l6790.py and the SMath sheet - there are no typed
constants in this file, and there must never be.
"""


def _edge_numbers(A):
    """the capacitive edge at full load, and the gain peak people quote for it

    Two different frequencies.  Printed side by side so the reader can see how
    far apart they are rather than being told they are the same thing.
    """
    import l6790
    lam, Q, fr = A.V['lam'], A.V['Qpk'], A.V['fr']
    edge = l6790.zvs_edge(Q, lam)
    fn = [0.30 + 0.7e-5 * i for i in range(100001)]
    pk = max(fn, key=lambda x: l6790.M(x, Q, lam))
    from math import degrees
    return {'fnEdge': edge * fr, 'fnPk': pk * fr,
            'phPk': abs(degrees(l6790.phase(pk, Q, lam)))}



def _d_overstate(A):
    """how much dropping the conduction ratio d overstates the secondary loss

    Line-cycle loss at the low equivalent corner with d left out, over the
    same with d in: the sweep's own rows, not a typed "about 26 %".
    """
    import l6790
    rows, _ = l6790.sweep(A.R, A.R['Vin_min'], 1.0, N=721)
    ok = [r for r in rows if r]
    return 100 * (sum(r['Isec_w'] ** 2 / r['d'] for r in ok)
                  / sum(r['Isec_w'] ** 2 for r in ok) - 1)

def build(A):
    """A is the an_pdf module, handed in - importing it here would load a
    second copy whenever an_pdf is run as __main__."""
    import cores as _CORE          # the datasheet figures, in one place
    import insulation as _INS      # the safety requirements, with sources
    _INS_ALT = _INS.ALTITUDE_M
    import figs_pf as _GAIN        # the crossings the gain chart marks
    h1, h2, p, eq, fig, tbl, note = A.h1, A.h2, A.p, A.eq, A.fig, A.tbl, A.note
    bullets, V, CW = A.bullets, A.V, A.CW
    FR, TR, SR = A.figref, A.tblref, A.secref
    ER = A.eqref
    eqagain, calc = A.eqagain, A.calc
    s = []
    add = s.append
    ext = s.extend

    # =============================================================== 1
    add(h1('Introduction'))
    add(p('A conventional universal-input LLC supply has two stages: a '
          'boost power-factor corrector that holds a 400&nbsp;V bus, and an '
          'LLC converter that steps the bus down. The bus capacitor stores '
          'the energy a unity-power-factor input cannot deliver evenly, and '
          'it gives the LLC an almost constant input, so the tank covers only '
          'a narrow gain range.'))
    add(p('A <b>single-stage PFC LLC</b> removes the boost stage and the bus '
          'capacitor. The rectified mains feeds the resonant tank directly. '
          'The input is then a 100/120&nbsp;Hz half sine, the gain the tank '
          'must provide follows the input through the line cycle, and the output capacitor '
          'must absorb what the bus capacitor used to. Most two-stage design '
          'habits do not apply.'))
    add(p('This note explains how the converter works and how to design one '
          'with the STMicroelectronics <b>L6790A</b>. One design runs through '
          'it: <b>90 to 264&nbsp;Vac in, %(Vout).0f&nbsp;V / '
          '%(Iout).1f&nbsp;A = %(Pout).1f&nbsp;W out</b>.' % V))
    add(note('<b>Scope.</b> Power stage, resonant tank, transformer, output '
             'bank, controller network, V<sub>CC</sub> supply, voltage loop '
             'and the insulation the transformer must carry. Not covered: EMI '
             'filter, layout, and the safety approval itself.'))

    # =============================================================== 2
    add(h1('The two converters this one is made of'))
    add(p('This chapter covers an ordinary LLC and ordinary power factor '
          'correction. Readers who know both can skip to Section&nbsp;%s.'
          % SR('Why single stage, and what it costs')))
    add(h2('What an LLC converter is'))
    add(p('An LLC converter is a square-wave generator driving a resonant '
          'network, which feeds a transformer and a rectifier. The switches '
          'only set the frequency. There is no duty cycle and no programmed '
          'inductor current.'))
    add(fig('an_llc_stage',
            'An LLC stage. The switches set the frequency; the tank sets the '
            'power; the transformer sets the voltage. The bridge output '
            'v<sub>d</sub> = v<sub>A</sub> &minus; v<sub>B</sub> drives the '
            'tank. Each arrow is the positive direction of a current plotted '
            'in Figure&nbsp;%s.' % FR('an_llc_waves')))
    add(p('The three tank elements are the series inductance L<sub>r</sub>, '
          'the magnetising inductance L<sub>m</sub> of the transformer, and '
          'the series capacitance C<sub>r</sub>. L<sub>m</sub> is the '
          'transformer&rsquo;s own inductance and L<sub>r</sub> is usually its '
          'leakage inductance, so only C<sub>r</sub> is always an added '
          'part.'))
    add(h2('Why an LLC, and not something simpler'))
    add(p('Compared with a forward or flyback converter, an LLC gives:'))
    ext(bullets([
        '<b>Soft switching at every load.</b> The primary switches turn on '
        'at zero voltage, and below resonance the rectifiers turn off at '
        'zero current. The magnetising current that discharges the mid-point '
        'flows at any load, so ZVS is not lost at light load.',
        '<b>Higher frequency</b>, because switching loss no longer limits '
        'it, so smaller magnetics and filters.',
        '<b>The leakage inductance is used as L<sub>r</sub></b> instead of '
        'needing a snubber, and there is no output inductor.']))
    add(p('The costs: the frequency moves with line and load, the '
          'magnetising current circulates at any load so light-load '
          'efficiency is modest, and the design comes from a gain curve, not '
          'from a duty-cycle expression.'))
    add(h2('What resonance is for'))
    add(p('In a hard-switched converter the energy in each switch&rsquo;s '
          'output capacitance is lost at every turn-on, and that loss limits '
          'the frequency.'))
    add(p('An LLC running <b>in its inductive region</b> presents an '
          'inductive load to the bridge, so the tank current lags the drive '
          'voltage. In the dead time that lagging current discharges the '
          'mid-point by itself, and the next switch turns on at zero volts. '
          '<b>That is zero-voltage switching</b>; Section&nbsp;%s gives the '
          'condition.' % SR('ZVS and ZCS are not the same thing')))
    add(fig('an_llc_waves',
            'One switching period below resonance. The difference between '
            'i<sub>Lr</sub> and i<sub>Lm</sub> crosses to the secondary. The '
            'switch turns on while its current is still negative; that current '
            'has already discharged the mid-point. The secondary conducts for the '
            'resonant half period T<sub>r</sub>/2 = 1/(2f<sub>r</sub>); the '
            'bridge changes over every T<sub>sw</sub>/2 = 1/(2f<sub>sw</sub>), '
            'which below resonance is the longer of the two.'))
    add(note('The condition is <i>inductive operation</i>, not a fixed '
             'frequency. Below the capacitive boundary the current leads, the '
             'bridge hard-switches into a low impedance, and parts are '
             'destroyed rather than heated. The boundary moves with load '
             '(Section&nbsp;%s).'
             % SR('The two boundaries are not the same boundary')))
    add(h2('How the circuit becomes M(f<sub>n</sub>, Q)'))
    add(p('The gain curve comes from three simplifications, each of which '
          'discards something.'))
    add(fig('an_rac',
            'Why the rectifier and load can be one resistance. The output is '
            'stiff, so the tank sees a square voltage v<sub>RI</sub>; the tank '
            'passes only the fundamental, so the current i<sub>RI</sub> is a '
            'sine. At the fundamental the pair takes the same power as a '
            'resistor.'))
    add(fig('an_fha_steps',
            'The reduction in three steps: as built; secondary referred to '
            'the primary; fundamental only. The result is one ac network '
            'with gain M and damping Q.'))
    ext(bullets([
        '<b>Refer the secondary to the primary.</b> The load resistance is '
        'multiplied by n&sup2;.',
        '<b>Replace the rectifier and output filter by one resistor.</b> '
        'At the fundamental they look like one.',
        '<b>Keep only the fundamental of the drive.</b> This is the '
        '<i>first harmonic approximation</i>. It is why an LLC design ends '
        'with a simulation or a measurement, not with the equations.']))
    add(p('Two numbers describe the remaining network:'))
    ext(bullets([
        '<b>The gain M</b>: the voltage across R<sub>ac</sub> over the '
        'fundamental that drives it. C<sub>r</sub> and L<sub>r</sub> cancel '
        'at the series resonance f<sub>r</sub>, so <b>M = 1 there at any '
        'load</b>. Below f<sub>r</sub> the tank can step up; above it, only '
        'down.',
        '<b>The quality factor Q = Z<sub>0</sub>/R<sub>ac</sub></b>, with '
        'Z<sub>0</sub> = &radic;(L<sub>r</sub>/C<sub>r</sub>). <b>Q rises '
        'with output power.</b> At Q = 0 the curve is tall and peaked; load '
        'flattens it.']))
    add(p('With f<sub>n</sub> normalised to the series resonance and '
          '&lambda; the ratio of the two inductances:'))
    add(eq(r'f_{n}=\frac{f_{sw}}{f_{r}}\,,\qquad '
           r'Z_{0}=\sqrt{\frac{L_{r}}{C_{r}}}\,,\qquad '
           r'Q=\frac{Z_{0}}{R_{ac}}\,,\qquad '
           r'\lambda=\frac{L_{r}}{L_{m}}', key='Qdef'))
    add(p('M(f<sub>n</sub>, Q) always means the gain of this reduced '
          'circuit.'))

    add(h2('The two resonances'))
    add(p('While the secondary conducts, the reflected output voltage clamps '
          'L<sub>m</sub>, leaving the series resonance'))
    add(eq(r'f_r=\frac{1}{2\pi\sqrt{L_rC_r}}', key='fr'))
    add(p('When the secondary is off, both inductances resonate:'))
    add(eq(r'f_o=\frac{1}{2\pi\sqrt{(L_r+L_m)\,C_r}}', key='fo'))
    add(p('At f<sub>r</sub> the gain is 1 for any load. At f<sub>o</sub> the '
          'no-load gain is unlimited. The tank can boost between the two; '
          'above f<sub>r</sub> it cannot.'))
    add(fig('f02_two_resonances',
            'The two resonances and the band between them in which the tank '
            'can boost. The shaded edge is the no-load capacitive boundary; '
            'it moves up under load.'))

    add(p('Below resonance each half cycle has two parts, with the same pair '
          'of switches on throughout: power delivery, then freewheeling. At '
          'resonance the half cycle is power delivery only; above resonance '
          'power delivery is cut short.'))
    add(fig('an_modes_12',
            '<b>First half, steps 1 and 2.</b> <b>1</b>&nbsp;Power delivery: '
            'S<sub>1</sub>,S<sub>4</sub> on, the resonant current exceeds the '
            'magnetising current and the difference reaches D<sub>1</sub>. '
            'L<sub>m</sub> is clamped, so this interval resonates at '
            'f<sub>r</sub>. <b>2</b>&nbsp;Freewheeling: the resonant current '
            'has fallen to the magnetising current, the rectifiers are off, '
            'and L<sub>m</sub> joins the resonance at f<sub>o</sub>. The same '
            'switches are still on. Greyed body diodes and C<sub>oss</sub> '
            'do nothing in that step.'))
    add(fig('an_modes_34',
            '<b>Steps 3 and 4, the dead time.</b> <b>3</b>&nbsp;All switches '
            'off; the magnetising current can only flow through the four '
            'C<sub>oss</sub>, pulling A down and pushing B up. '
            '<b>4</b>&nbsp;The swing is complete and the body diodes of '
            'S<sub>2</sub>,S<sub>3</sub> clamp V<sub>ds</sub> at zero. The '
            'next gate must arrive inside this window.'))
    add(fig('an_modes_56',
            '<b>Second half, steps 5 and 6</b>: the mirror image of 1 and 2 '
            'with S<sub>2</sub>,S<sub>3</sub> and D<sub>2</sub>.'))
    add(fig('an_modes_78',
            '<b>Steps 7 and 8</b>, the second dead time. The mid-points swing '
            'back (<b>7</b>), the body diodes of S<sub>1</sub>,S<sub>4</sub> '
            'clamp (<b>8</b>), and step 1 begins at zero volts. ZVS happens '
            'in steps 4 and 8 only.'))
    add(fig('an_modes_wave',
            '<b>Where each step sits on the waveforms.</b> The numbered bands '
            'are the eight panels above in time order. Drawn below resonance '
            'at f<sub>sw</sub>/f<sub>r</sub> = 0.70 with the dead time '
            'widened so that steps 3, 4, 7 and 8 are visible; the current '
            'amplitudes are this design&rsquo;s I<sub>Lr,pk</sub> and '
            'I<sub>Lm,pk</sub> at the lowest voltage the tank sees. The rectifier '
            'current is drawn referred to the primary, i<sub>D</sub>/n = '
            'i<sub>Lr</sub> &minus; i<sub>Lm</sub>.', width=CW))
    add(note('<b>&ldquo;Freewheeling&rdquo; means two different intervals in '
             'the literature.</b> Here it is steps 2 and 6: rectifiers off, '
             'L<sub>m</sub> in the resonance, same switches on. Toshiba&rsquo;s '
             '<i>Resonant Circuits and Soft Switching</i> (2019) uses it for '
             'the dead time, when the body diodes conduct. The dead time '
             'exists at every frequency; steps 2 and 6 exist only below '
             'resonance.'))
    add(fig('an_three_cases',
            'Below, at and above resonance. <b>Top:</b> gates, bridge voltage, '
            'resonant current with the magnetising current dashed, and '
            'rectifier current. <b>Bottom:</b> the same three switching '
            'frequencies as points on the half-load gain curve. At full load '
            'f<sub>sw</sub>/f<sub>r</sub> = 0.70 is already capacitive, so the '
            'full-load curve is drawn only from its ZVS edge up.', width=CW))
    add(p('The bottom panel is the gain M of Section&nbsp;%s. Which side of '
          'f<sub>r</sub> the converter runs on decides whether the tank '
          'boosts or bucks:' % SR('The gain function and the three regions')))
    ext(bullets([
        '<b>Below f<sub>r</sub>: M&nbsp;&gt;&nbsp;1, boost.</b> The resonant '
        'half sine ends early and i<sub>Lr</sub> <b>lands on '
        'i<sub>Lm</sub></b>. From then on no power crosses to the '
        'secondary: freewheeling.',
        '<b>At f<sub>r</sub>: M&nbsp;=&nbsp;1 at any load.</b> '
        'i<sub>Lr</sub> meets i<sub>Lm</sub> as the bridge switches, and the '
        'rectifier current reaches zero at the same instant. This is the '
        'most efficient point.',
        '<b>Above f<sub>r</sub>: M&nbsp;&lt;&nbsp;1, buck.</b> The switching '
        'half period ends first and the resonant half sine is <b>cut '
        'off</b>. The switches turn off more current and the rectifier is '
        'interrupted while conducting.']))
    add(p('<b>The freewheeling interval rings at f<sub>o</sub>.</b> Nothing '
          'clamps '
          'L<sub>m</sub>, so L<sub>r</sub>&nbsp;+&nbsp;L<sub>m</sub> rings '
          'with C<sub>r</sub>. It looks nearly flat because it is short '
          'against the period of f<sub>o</sub> and sits near the crest of '
          'that ring. The lower f<sub>sw</sub>, the larger its share of the '
          'half period. Everything useful happens between the two '
          'frequencies.'))
    add(note('<b>Symbols are not standard.</b> At least one widely used '
             'guide calls the <i>series</i> resonance f<sub>o</sub>, the '
             'opposite of the meaning here. Check before comparing.'))
    add(p('A conventional LLC runs close to f<sub>r</sub> at nominal input, '
          'where the circulating current is smallest, and goes below it only '
          'in hold-up. This converter runs on both sides, depending on the '
          'input voltage and the line phase (Section&nbsp;'
          + SR('Which side of resonance this converter runs on') + ').'))
    add(h2('The gain function and the three regions'))
    add(p('With the first-harmonic approximation the tank gain is'))
    add(eq(r'M(f_n,Q,\lambda)=\frac{1}'
           r'{\sqrt{\left(1+\lambda-\frac{\lambda}{f_n^{2}}\right)^{2}'
           r'+Q^{2}\left(f_n-\frac{1}{f_n}\right)^{2}}}', key='M'))
    add(p('Two checks by eye: at f<sub>n</sub>&nbsp;=&nbsp;1 the Q term '
          'vanishes and <b>M&nbsp;=&nbsp;1 at any Q</b>, so every curve '
          'passes through that point. At no load (Q&nbsp;=&nbsp;0) raising '
          'f<sub>n</sub> only brings M down to 1/(1+&lambda;); that floor '
          'matters in Section&nbsp;%s.'
          % SR('The other bound on &lambda;, and where it has no solution')))
    add(p('The curve has three regions. Below the capacitive/inductive '
          'boundary the bridge hard-switches: not allowed. Between the '
          'boundary and f<sub>r</sub> the tank is inductive and boosts; above '
          'f<sub>r</sub> it is inductive and bucks. The boundary is drawn for '
          'the full-load curve; at no load it sits at f<sub>o</sub> and it '
          'moves up with load.'))
    add(fig('f04_three_regions',
            'The three regions, shaded for the full-load curve. Only the '
            'inductive ones are usable. Framing after ROHM TechWeb.'))
    add(p('<b>The side can be read from the chart without a waveform.</b> '
          'Draw the required gain as a horizontal line and find where it '
          'crosses the curve for the present load. Above 1 the crossing is '
          'left of f<sub>n</sub>&nbsp;=&nbsp;1 (below resonance, the left '
          'column of Figure&nbsp;%s); at 1 it is f<sub>r</sub> at any load; '
          'below 1 it is to the right (above resonance).'
          % FR('an_three_cases')))
    add(p('So the input voltage decides the side, not the load: the required '
          'gain is the reflected output voltage over the input the tank '
          'sees, and the load only picks the curve. A higher input lowers the '
          'line and moves the crossing right. The load decides whether the '
          'crossing is still to the right of the capacitive boundary '
          '(Section&nbsp;%s).'
          % SR('The two boundaries are not the same boundary')))

    add(h2('Capacitive and inductive, and why those words'))
    add(p('The names describe <b>what the bridge sees</b>: the phase of the '
          'tank current against the square wave that drives it. At low '
          'frequency C<sub>r</sub> dominates and the current <i>leads</i>; at '
          'high frequency the inductances dominate and it <i>lags</i>. That '
          'phase decides whether the switching is soft or hard.'))
    add(fig('an_cap_ind',
            'Either side of the boundary. <b>Top:</b> the boundary sits a '
            'little above the gain peak. <b>Middle:</b> the leg as '
            'S<sub>1</sub> is gated on. Left, the tank current is already '
            'positive, flowing in S<sub>2</sub>&rsquo;s body diode, so '
            'S<sub>1</sub> closes onto a conducting diode. Right, it is '
            'negative, has carried the mid-point up during the dead time, and '
            'S<sub>1</sub> finds its own body diode conducting at zero volts. '
            '<b>Bottom:</b> the mid-point voltage v<sub>A</sub> (to 0), the '
            'tank current and the drain current i<sub>S1</sub> of the closing '
            'switch, to one scale.', width=CW))
    ext(bullets([
        '<b>Inductive: the current lags.</b> At turn-off it still pushes the '
        'bridge node towards the other rail; the dead time lets it, and the '
        'next device turns on at zero volts. <b>ZVS.</b>',
        '<b>Capacitive: the current leads.</b> It has already reversed, so it '
        'pushes the node back. The next device turns on into the full rail, '
        'and the other body diode is forced off with reverse recovery '
        'through a low impedance. <b>Hard switching, and the failure that '
        'destroys parts.</b> The design stays out of this region; the '
        'controller has a protection in case it does not.']))

    add(h2('Why a diode has to recover on one side and not on the other'))
    add(p('Take one leg: a high-side switch, a low-side switch and the tank '
          'on the mid-point. When either device turns off, <b>the tank '
          'current does not stop</b>. What carries it during the dead time '
          'decides everything. The middle row of Figure&nbsp;%s shows the two '
          'cases, after onsemi AN-4151.' % FR('an_cap_ind')))
    ext(bullets([
        '<b>Inductive.</b> The current carries the mid-point to the '
        '<i>other</i> rail through the two C<sub>oss</sub>, the incoming '
        'body diode picks it up, and that device is gated on at zero volts. '
        'Its own body diode then hands over to the channel with no reverse '
        'voltage: <b>nothing to recover</b>.',
        '<b>Capacitive.</b> The current has already reversed. It holds the '
        'mid-point on the rail it came from through the body diode of the '
        'device that just turned off. The incoming device is gated on across '
        'the full rail, onto a conducting diode.']))
    add(p('That diode cannot block until its stored charge is swept out, so '
          'for that time both devices conduct and the rail is shorted through '
          'them. The current is a spike limited only by loop inductance, '
          'dissipated in the incoming device at full rail voltage; when the '
          'diode snaps off, the di/dt in the loop inductance appears as '
          'overshoot across it.'))
    add(note('<b>This is why a fast-recovery body diode is required on the '
             'primary</b> (Section&nbsp;%(ref)s): any excursion into the '
             'capacitive region turns a device on onto the conducting body '
             'diode of the other. It is also why f<sub>Min</sub> is kept '
             'above f<sub>o</sub>, and why the anti-capacitive protection '
             'exists.'
             % dict(ref=SR('What the semiconductors have to be'))))
    add(h2('The two boundaries are not the same boundary'))
    add(p('Both pairs of words describe positions on the same frequency '
          'axis, but they are different lines on it.'))
    ext(tbl('Two classifications, two boundaries, two consequences.',
            [['', 'capacitive / inductive', 'below / above resonance'],
             ['the boundary', 'where <b>arg Z<sub>in</sub> = 0</b>',
              '<b>f<sub>r</sub></b>, the series resonance'],
             ['does it move?', '<b>yes &mdash; with load</b>',
              'no, it is fixed by L<sub>r</sub> and C<sub>r</sub>'],
             ['what it decides',
              'ZVS or hard switching, on the <b>primary</b>',
              'boost or buck, and ZCS or not, on the <b>secondary</b>'],
             ['which side is allowed', 'inductive only, always',
              'both sides are legitimate']],
            widths=[CW * 0.19, CW * 0.40, CW * 0.41], key='capind', split=True))
    add(p('The capacitive boundary <b>rises with load</b>, from '
          'f<sub>o</sub> at no load towards f<sub>r</sub> as the load grows, so a '
          'frequency that is inductive at light load can be capacitive at '
          'overload.'))
    add(note('<b>The boundary is not the gain peak.</b> It is where '
             '<b>arg Z<sub>in</sub> = 0</b>, a little <i>above</i> the peak. '
             'Using the peak is optimistic in the dangerous direction. '
             'Section&nbsp;%(ref)s gives both frequencies for this design; '
             'the verdict comes from the ZVS check of Section&nbsp;%(zvsref)s.'
             % dict(ref=SR('ZVS over the whole operating space'),
                    zvsref=SR('ZVS verification'))))
    add(fig('an_loadshift',
            'The boundary moves up with load. The dashed curve is the '
            'boundary itself, traced as Q varies.'))
    ext(bullets([
        '<b>Below f<sub>r</sub> and inductive</b> is the normal boosting '
        'region.',
        '<b>Below f<sub>r</sub> and capacitive</b> is the fault. Going below '
        'f<sub>r</sub> is not the danger; going below the boundary is.',
        '<b>Above f<sub>r</sub></b> is inductive at every load.']))
    add(note('<b>Design rule.</b> Keep f<sub>Min</sub> above f<sub>o</sub>. '
             'That is only the no-load boundary, so it is necessary but not '
             'sufficient; the real check is the ZVS sweep of Section&nbsp;'
             + SR('ZVS verification') + ', run under load at every line '
             'phase.'))
    add(h2('ZVS and ZCS are not the same thing'))
    add(p('Both switch a device while its voltage or its current is zero. '
          'They apply to different devices, and only one is guaranteed.'))
    add(fig('an_zvs_zcs',
            'ZVS on the primary, ZCS on the secondary: different devices, '
            'different mechanisms, different conditions.', width=CW))
    ext(bullets([
        '<b>ZVS on the primary switches</b> needs inductive operation, which '
        'is possible on both sides of f<sub>r</sub>. It is required everywhere; '
        'Section&nbsp;' + SR('ZVS verification') + ' gives the margin.',
        '<b>ZCS on the secondary rectifiers</b> happens when the resonant '
        'current reaches zero by itself, which is only <b>below '
        'f<sub>r</sub></b>. Above f<sub>r</sub> the rectifier is cut off '
        'while conducting and reverse recovery returns.']))
    add(note('A converter whose input crosses f<sub>r</sub> must be checked '
             'on both sides: its rectifier body diode and synchronous-rectifier '
             'dead time matter whenever it runs above f<sub>r</sub>.'))
    add(h2('Sizing the dead time so that ZVS actually happens'))
    add(p('ZVS is a charge problem. During the dead time the magnetising '
          'current must move enough charge to swing the bridge node across '
          'the rail. The design quantity is T<sub>ZC</sub>, the time the tank '
          'current takes to reach zero after the gates turn off, and it must '
          'exceed the dead time:'))
    add(eq(r'T_{ZC}\;>\;t_D', key='zvs'))
    add(fig('f05_zvs_mechanism',
            'The magnetising current discharges the bridge node during the '
            'dead time. Two conditions: the current must not reach zero '
            'before the dead time ends (T<sub>ZC</sub> &gt; t<sub>D</sub>), '
            'and the swing T<sub>T</sub> must finish inside the dead time.'))
    add(note('<b>Use C<sub>o(tr)</sub></b> (equivalently Q<sub>oss</sub>), '
             'not the headline C<sub>oss</sub>: the datasheet values differ '
             'by three to five times, and ZVS is a charge question.'))
    add(h2('Not a flyback, and why that changes the core'))
    add(p('Two flyback habits are wrong here and cost money: sizing the '
          'core from the current, and asking for saturation at the peak '
          'winding current. Both come from when the two windings conduct.'))
    add(p('<b>In a flyback they never conduct together</b>, so at every '
          'instant the whole winding current is magnetising current. Every '
          'joule delivered was first stored in the core, the flux follows '
          'the <i>current</i>, and A<sub>e</sub> is sized from the peak '
          'current.'))
    add(p('<b>In an LLC they conduct together.</b> Their ampere-turns '
          'oppose, and only the difference magnetises the core:'))
    add(eq(r'N_{p}\,i_{p}\;-\;N_{s}\,i_{s}\;=\;N_{p}\,i_{\mu}', key='mmf'))
    add(p('The load current passes through by transformer action and never '
          'enters the core. What the core holds is the magnetising energy '
          '&frac12;L<sub>&mu;</sub>i<sub>&mu;</sub>&sup2;, with '
          'L<sub>&mu;</sub> the magnetising inductance of the physical '
          'transformer (it is not quite the tank&rsquo;s L<sub>m</sub>; '
          'Section&nbsp;%s). That energy is not a by-product: '
          'i<sub>&mu;</sub> is what swings the bridge node in the dead time. '
          'The gap exists to set L<sub>&mu;</sub>, and through it '
          'L<sub>m</sub>, not to store load energy.'
          % SR('Two ratios, two inductances')))
    add(fig('an_flyback_llc',
            'Left: a flyback in discontinuous conduction, as in '
            'Figure&nbsp;%s. The switch and the rectifier are never on '
            'together, so '
            'the conducting winding carries all the magnetising current and '
            'the flux ramps with it. Right: both conduct at once and only '
            'i<sub>&mu;</sub> = i<sub>p</sub> &minus; i<sub>s</sub> '
            'magnetises the core. The secondary current is drawn referred '
            'to the primary. The arrows are the reference directions: '
            'i<sub>s</sub> is taken into the dot in the flyback and out of it '
            'in the LLC, so the flyback&rsquo;s ampere-turns add. '
            'Bottom row: dashed, what each winding would drive alone; solid, '
            'their sum; shaded, what the secondary removed.'
            % FR('an_flux_steps')))
    add(p('Figure&nbsp;%s follows one period of each converter interval by '
          'interval: which winding conducts, what voltage it holds, and so '
          'which way the flux moves and what stops it.'
          % FR('an_flux_steps')))
    add(fig('an_flux_steps',
            'The flux built step by step. Left, a flyback in discontinuous '
            'conduction; right, an LLC below resonance, drawn from the '
            'eight-interval model with this design&rsquo;s currents and '
            'numbered with its steps (Figure&nbsp;%s). '
            'Compare the bottom row, the flux.' % FR('an_modes_wave')))
    ext(bullets([
        '<b>Flyback, 1.</b> The switch closes. V<sub>in</sub> sits on the '
        'primary, i<sub>p</sub> ramps at V<sub>in</sub>/L<sub>p</sub>, and '
        'because no other winding conducts every ampere-turn magnetises: B '
        'rises at V<sub>in</sub>/(N<sub>p</sub>A<sub>e</sub>). The energy '
        'goes into the gap.',
        '<b>Flyback, 2.</b> The switch opens. The flux cannot jump, so the '
        'ampere-turns pass to the secondary at once, '
        'N<sub>s</sub>i<sub>s</sub> = N<sub>p</sub>I<sub>p,pk</sub>. The '
        'rectifier conducts, V<sub>out</sub> sits on the secondary, and B '
        'falls at V<sub>out</sub>/(N<sub>s</sub>A<sub>e</sub>) while the gap '
        'energy leaves for the output.',
        '<b>Flyback, 3.</b> The secondary current reaches zero; both '
        'windings are off and the flux rests near zero until the next '
        'cycle. The peak flux was fixed at the turn-off instant by '
        'I<sub>p,pk</sub>, which is whatever the load and the input asked '
        'for.',
        '<b>LLC, 1.</b> A bridge switch closes. As soon as the secondary '
        'voltage reaches V<sub>out</sub> the rectifier conducts, so the '
        'secondary is clamped to V<sub>out</sub> and the magnetising branch '
        'sees n&thinsp;V<sub>out</sub>. The load current flows in both '
        'windings at once, their ampere-turns cancel, and only '
        'i<sub>&mu;</sub> ramps: B rises at '
        'V<sub>out</sub>/(N<sub>s</sub>A<sub>e</sub>).',
        '<b>LLC, 2.</b> The resonant half period ends: i<sub>s</sub> reaches '
        'zero, the rectifier turns off and the clamp is gone. L<sub>m</sub> '
        'joins the resonance with C<sub>r</sub>, i<sub>&mu;</sub> is nearly '
        'flat, and B holds at its peak. That peak was set by V<sub>out</sub> '
        'and T<sub>r</sub>/2 and by nothing else.',
        '<b>LLC, 3 and 4.</b> Dead time. i<sub>&mu;</sub> swings the bridge '
        'node to the other rail; the flux hardly moves.',
        '<b>LLC, 5.</b> The other switch closes and the other rectifier '
        'clamps the secondary to &minus;V<sub>out</sub>; B ramps back down '
        'at the same slope to &minus;B<sub>pk</sub>.']))
    ext(tbl('The same two cores, compared.',
            [['', 'Flyback', 'LLC'],
             ['Which winding sets the flux',
              'whichever one conducts; B follows its current',
              'the clamped secondary; B follows its volt-seconds'],
             ['What the peak flux depends on',
              'I<sub>p,pk</sub>: load, input voltage and conduction mode',
              'V<sub>out</sub>, T<sub>r</sub> and N<sub>s</sub> only'],
             ['Flux against load', 'rises with load', 'does not move'],
             ['Flux against switching frequency',
              'falls as the frequency rises (shorter on-time)',
              'constant below resonance, falls above it'],
             ['What the gap does',
              'stores the load energy; gap and A<sub>e</sub> together set '
              'the power',
              'sets L<sub>m</sub>, i.e. the magnetising current and ZVS; '
              'holds only the magnetising energy'],
             ['What threatens the core', 'overload, over-current',
              'over-voltage on the output'],
             ['Which protection guards the core', 'the current limit',
              'the output OVP; the current limit only where there is no OVP '
              '(Section&nbsp;%s)' % SR('The saturation test is not the peak winding current')],
             ['Saturation test current',
              'the peak winding current, with margin',
              'i<sub>&mu;,pk</sub> scaled to the OVP ceiling; below the '
              'winding peak'],
             ['What sizes A<sub>e</sub>',
              'peak current and L<sub>p</sub>: energy',
              'output volt-seconds at f<sub>r</sub>: Faraday']],
            widths=[CW * 0.26, CW * 0.37, CW * 0.37], key='flyllc',
            split=True))
    add(note('&ldquo;An LLC transformer stores no energy&rdquo; is a slogan. '
             'It stores the magnetising energy twice per period; it does not '
             'store the load energy.'))
    add(p('A<sub>e</sub> still matters because Faraday&rsquo;s law does not '
          'ask whether energy is stored:'))
    add(eq(r'B(t)\;=\;\frac{1}{N\,A_{e}}\int v\,dt', key='faraday'))
    add(p('with v the winding voltage, N its turns and A<sub>e</sub> the '
          'core area. <b>Only the input to the calculation differs.</b> In a '
          'flyback the volt-seconds are the input voltage times the on-time. '
          'In an LLC the conducting secondary clamps the winding to the '
          'output for a resonant half period, so the flux is set by the '
          '<b>output voltage alone</b> (Section&nbsp;'
          + SR('Peak flux is set by the secondary, not the primary') + ').'))
    add(p('Three consequences:'))
    ext(bullets([
        '<b>The flux does not rise with load.</b> More load raises '
        'i<sub>s</sub> and the reflected part of i<sub>p</sub> together; '
        'their difference i<sub>&mu;</sub> does not move. Overload threatens '
        'the copper and the semiconductors, not the core.',
        '<b>The flux rises with output voltage</b>, so the saturation '
        'specification is set at the over-voltage threshold, not the '
        'nominal output (Section&nbsp;'
        + SR('The saturation test is not the peak winding current') + ').',
        '<b>The flux does not fall with switching frequency</b> below '
        'resonance: the rectifier clamps the winding for T<sub>r</sub>/2 '
        'whatever f<sub>sw</sub> is, which is why f<sub>r</sub> appears in '
        'the flux equation.']))
    add(p('<b>What to keep in mind when designing.</b>'))
    ext(bullets([
        '<b>Size A<sub>e</sub> from volt-seconds, not from current.</b> '
        'The input is V<sub>out</sub>, N<sub>s</sub> and f<sub>r</sub> '
        '(Section&nbsp;'
        + SR('Peak flux is set by the secondary, not the primary')
        + '); the winding current does not enter.',
        '<b>Do not add gap for margin.</b> In a flyback more gap means more '
        'stored energy. Here more gap means a smaller L<sub>m</sub>: more '
        'magnetising current, more circulating loss, a different '
        '&lambda;, and no change in the flux at all. The gap is set by '
        'L<sub>m</sub> and checked by L<sub>open</sub>; the flux margin is '
        'set by the OVP ceiling and checked by the DC-overlap test.',
        '<b>The test current follows L<sub>&mu;</sub>; the flux does '
        'not.</b> A smaller gap raises L<sub>&mu;</sub> and lowers '
        'i<sub>&mu;,pk</sub> at the same flux. Recompute I<sub>eq</sub> from '
        'the actual L<sub>&mu;</sub> whenever the gap changes; never carry '
        'it over.',
        '<b>B<sub>pk</sub> is fixed, so core loss follows frequency.</b> '
        'The flux is the same at every point of the line cycle below '
        'resonance, and the loss per cycle at that flux rises with '
        'f<sub>sw</sub>. Above resonance the flux falls as 1/f<sub>sw</sub> and the '
        'loss falls with it, so the worst core loss is near f<sub>r</sub>.',
        '<b>The flyback habit that costs the most</b> is asking the '
        'supplier for saturation at the tank peak current. That asks for a '
        'larger core than the converter needs, for a flux the converter can '
        'never produce.']))
    add(p('A DC-overlap test is made with every other winding open, which removes '
          'the cancellation: all of the test current is magnetising current. '
          'Section&nbsp;'
          + SR('The saturation test is not the peak winding current')
          + ' takes that to a number.'))

    add(h2('How an LLC is normally designed'))
    add(p('The standard sequence. Section&nbsp;' + SR('Design procedure')
          + ' follows it and departs from it in two places.'))
    ext(bullets([
        '<b>1  Turns ratio</b> so that the converter runs near '
        'M&nbsp;=&nbsp;1 at nominal input, where circulating current is '
        'lowest.',
        '<b>2  Gain range</b> M<sub>min</sub>&hellip;M<sub>max</sub> from the '
        'input range and output tolerance.',
        '<b>3  Load resistance referred to the primary</b>, R<sub>ac</sub>.',
        '<b>4  m = (L<sub>r</sub>+L<sub>m</sub>)/L<sub>r</sub> (or &lambda;) and Q together</b> from the peak-gain chart. '
        'For each m there is a curve of attainable peak gain against Q, and '
        'the design must sit under it with margin. Larger m: less '
        'circulating current, less peak gain.',
        '<b>5  Component values.</b> Q and R<sub>ac</sub> give '
        'Z<sub>0</sub>; Z<sub>0</sub> and f<sub>r</sub> give C<sub>r</sub> '
        'and L<sub>r</sub>; m gives L<sub>m</sub>.',
        '<b>6  Verify</b> gain margin at the worst corner, ZVS at the worst '
        'point, and currents and flux against real parts.']))
    add(fig('an_peakgain',
            'Step 4: the peak gain depends on both m and Q, so a required '
            'gain and a Q leave only a band of usable m.'))
    add(h2('What power factor correction is'))
    add(p('A bridge rectifier feeding a capacitor holds the bus near the '
          'mains peak, so the diodes conduct only in the short window when '
          'the mains is above the capacitor voltage. All the charge for the '
          'whole cycle arrives in that window.'))
    add(fig('an_pfc_cap',
            'A capacitor-input rectifier: v<sub>C</sub> stays near the '
            'crest, the diodes conduct in narrow windows, and the current '
            'inside them is tall.'))
    add(p('The peak current is several times what a resistor of the same '
          'power would draw, and a pulse train that narrow is mostly '
          'harmonics.'))
    add(h2('Power factor, and why it is not the same as distortion'))
    add(p('<b>Power factor</b> is the ratio of real power to apparent power, '
          'with V<sub>ac</sub> and I<sub>ac</sub> the rms input voltage and '
          'current:'))
    add(eq(r'PF=\frac{P}{V_{ac}I_{ac}}\;=\;\cos\varphi_{1}\;\times\;\frac{I_{1,rms}}{I_{ac}}'))
    add(p('with P the average power, I<sub>1,rms</sub> the rms of the '
          'fundamental alone, and &phi;<sub>1</sub> its phase against the '
          'voltage. <b>Displacement</b> (the phase) is what a motor gets '
          'wrong; <b>distortion</b> (the harmonic share of the rms) is what '
          'a rectifier gets wrong. The current above is roughly in phase '
          'and still scores about 0.6.'))
    add(p('Total harmonic distortion, THD, is the harmonic content as a '
          'fraction of the fundamental:'))
    add(eq(r'THD=\frac{\sqrt{I_{ac}^{2}-I_{1,rms}^{2}}}{I_{1,rms}}'
           r'\,,\qquad \frac{I_{1,rms}}{I_{ac}}=\frac{1}{\sqrt{1+THD^{2}}}'))
    add(note('A converter can hold PF above 0.99 and still fail '
             'IEC&nbsp;61000-3-2, which limits <i>individual</i> harmonics '
             'in amperes. Class&nbsp;D covers only the product types the '
             'standard lists, up to 600&nbsp;W; above that the absolute '
             'Class&nbsp;A limits apply. '
             'Settle the class first.'))
    add(h2('How a corrector fixes it'))
    add(p('Force the input current to follow the input voltage and the '
          'converter looks like a resistor to the mains. The standard '
          'implementation is a <b>boost converter after the bridge</b>, '
          'switching fast enough that the mains is constant within one '
          'switching cycle.'))
    add(fig('an_pfc_boost',
            'A boost corrector: the inductor charges from the line while the '
            'switch is on and delivers to the bus in series with the line '
            'while it is off.'))
    ext(bullets([
        '<b>Why a boost.</b> Near the zero crossing the stage must step up '
        'by an unlimited ratio. A boost can, and its input current is '
        'continuous, which makes shaping possible.',
        '<b>The inner loop</b> regulates the inductor current, fast.',
        '<b>The outer loop</b> regulates the bus voltage and is made '
        '<b>slower than 2f<sub>l</sub></b>. A fast voltage loop would fight '
        'the bus ripple and flatten the current shape the corrector exists '
        'to make.',
        '<b>The multiplier</b> joins them: shape from the mains, level from '
        'the output.']))
    add(fig('an_pfc_ccm',
            'The result in continuous conduction: switching ripple rides on '
            'the inductor current, and its average follows the input '
            'voltage.'))
    add(p('A current that follows the voltage means an input power that '
          'follows sin&sup2;&thinsp;&theta;: zero twice per cycle, twice the '
          'average at the crests. The load wants constant power, so '
          '<b>something must store the difference</b>.'))
    add(h2('Why they are normally two stages'))
    add(fig('an_two_stage',
            'The two-stage arrangement with the waveform at every node. The '
            'buffer that absorbs the twice-line-frequency pulsation sits '
            'between the stages at 400&nbsp;V. Ripple on the dc nodes is '
            'exaggerated; v<sub>ac</sub> is the instantaneous mains voltage.',
            width=CW))
    add(p('The bus capacitor does two jobs:'))
    ext(bullets([
        'it <b>buffers</b> the difference between the pulsating input power '
        'and the constant output power;',
        'it <b>isolates</b> the LLC from the mains waveform, so the tank sees '
        'a nearly constant input and has to cover only a narrow gain range.']))
    add(p('Removing the boost stage removes both. The buffering must be done '
          'elsewhere, and the tank must work from a rectified sine that goes '
          'to zero 100 or 120 times a second.'))
    add(h1('Why single stage, and what it costs'))
    add(p('Two steps of the standard LLC sequence (Section&nbsp;'
          + SR('How an LLC is normally designed') + ') do not survive '
          'here. There is no '
          'nominal point, because the input sweeps a half sine; and no single '
          'tank covers the gain range, so the bridge itself changes '
          '(Sections&nbsp;'
          + SR('Gain is a boundary condition, not a control variable')
          + ' and ' + SR('Topology morphing') + ').'))
    add(h2('The energy a unity power factor cannot deliver'))
    add(p('Unity power factor makes the instantaneous input power follow '
          'sin&sup2;&thinsp;&theta;, swinging between zero and twice the '
          'average at twice the line frequency:'))
    add(eq(r'p_{in}(t)=V_{ac}I_{ac}\,\left[\,1-\cos(2\omega_l t)\,\right]'))
    add(p('with V<sub>ac</sub> and I<sub>ac</sub> the rms mains voltage and '
          'current and &omega;<sub>l</sub> = 2&pi;f<sub>l</sub>. The load wants constant power, so the difference must be '
          'stored and returned a few milliseconds later, whatever the '
          'topology.'))
    add(p('Panel&nbsp;2 of Figure&nbsp;%s draws it: the surplus above the flat '
          'load equals the deficit below it, and a capacitor somewhere must '
          'absorb the one and return it as the other.'
          % FR('an_pf_chain')))

    add(h2('Moving the buffer from 400 V to the output'))
    add(p('In the two-stage converter the buffer is the 400&nbsp;V bus '
          'capacitor. Here there is no bus, so it moves to the output. '
          '<b>The joules do not change; the voltage they sit at does</b>, '
          'and a capacitor returns only the energy between its starting '
          'voltage and the lowest the load accepts:'))
    add(eq(r'E=\frac{1}{2}C\left(V^{2}-V_{min}^{2}\right)'))
    add(p('Hold-up shows the price. Both architectures must store the same '
          'energy for the same T<sub>hold</sub>. On a 400&nbsp;V bus that may '
          'fall to 320&nbsp;V the window is 400&sup2;&nbsp;&minus;&nbsp;'
          '320&sup2;; on an output of a few tens of volts it is '
          'V<sub>out</sub>&sup2;&nbsp;&minus;&nbsp;V<sub>o,min</sub>&sup2;, '
          'smaller by a factor in the hundreds, so the capacitance grows by '
          'that factor. Settle this first: if the enclosure cannot house the '
          'bank, the output voltage must change. Section&nbsp;%(ref)s sizes '
          'the bank for this design, where ripple, not hold-up, decides.'
          % dict(ref=SR('The output bank, as sized'))))
    add(note('<b>The trade.</b> Out: a switch, an inductor, a diode, a '
             '400&nbsp;V electrolytic and their losses. In: a very large '
             'low-voltage capacitor bank, 2f<sub>l</sub> ripple on the output, '
             'and a tank that must cover a much wider range. Whether it is a '
             'good trade depends on how much output ripple the load '
             'accepts.'))

    add(h2('What the load must tolerate'))
    add(p('The output carries the 2f<sub>l</sub> ripple directly. It is set '
          'by the bank and the load, not by the loop, and it cannot be '
          'regulated away: trying puts the distortion on the input current '
          'instead (Section&nbsp;'
          + SR('Why the crossover must be low: the 2f<sub>l</sub> ripple')
          + '). <b>The allowed ripple is a property of the load</b> and must '
            'come from the specification. This design allows a few per cent '
            'peak-to-peak.'))

    # =============================================================== 3
    add(h1('Operating principle'))
    add(h2('Gain is a boundary condition, not a control variable'))
    add(p('In a two-stage LLC the controller commands gain. Here it cannot, '
          'because <b>both ports are voltage sources</b>: the output is a '
          'millifarad-class capacitor bank and the input is the rectified '
          'mains. The '
          'instantaneous gain is forced:'))
    add(eq(r'M(\theta)=\frac{n\,V_{o,eff}}{V_{drive}(\theta)}'
           r'=\frac{2\,n\,V_{o,eff}}{\sqrt{2}\,V_{ac,eq}\,\sin\theta}', key='Mreq'))
    add(p('with &theta; the line phase and V<sub>drive</sub> the amplitude '
          'the bridge applies to the tank: the rectified mains in full '
          'bridge, half of it in half bridge. V<sub>ac,eq</sub> is the mains '
          'voltage a half bridge would need for the same drive, so twice the '
          'mains in full bridge and the mains itself in half bridge; '
          'V<sub>o,eff</sub> is the output plus the rectifier drop '
          '(Equation&nbsp;%s). Both voltages are pinned from '
          'outside, so their ratio is fixed moment by moment.' % ER('Vrefl')))
    add(p('Moving the frequency therefore moves <b>Q</b>, that is, power. '
          '<b>Frequency is a power command, not a voltage command.</b>'))

    add(h2('Two divergences that cancel'))
    add(p('Near the zero crossing the required gain rises as '
          '1/sin&thinsp;&theta; without limit. The converter survives because '
          'the load disappears at the same time:'))
    add(eq(r'Q(\theta)=Q_{pk}\,\sin^{2}\theta', key='Qtheta'))
    add(p('with Q<sub>pk</sub> its value at the line peak, and an unloaded '
          'LLC has unlimited gain at f<sub>o</sub>. The two '
          'infinities cancel, and the operating point walks down towards '
          'f<sub>o</sub> as the mains approaches zero (Section&nbsp;'
          + SR('Which side of resonance this design runs on')
          + '). <b>f<sub>o</sub> is the frequency floor of the whole '
            'design</b>; an oscillator clamp below it destroys hardware.'))
    add(h2('Frequency modulation is the power factor correction'))
    add(p('Figure&nbsp;%s follows the control law round one line half cycle. '
          'The first three steps are forced by the two voltage sources; only '
          'the fourth is something the controller does.'
          % FR('an_pf_chain')))
    add(fig('an_pf_chain',
            'How the power factor is corrected, over one line half cycle. '
            '<b>1</b>&nbsp;Unity power factor: the current has the shape of '
            'the rectified mains. <b>2</b>&nbsp;The power drawn is '
            'sin&sup2;, while the load takes a steady P<sub>out</sub>; the '
            'shaded areas are what the bank buffers. <b>3</b>&nbsp;The tank '
            'is handed a gain and a load, and both run away at the zero '
            'crossing. <b>4</b>&nbsp;The switching frequency is the only free '
            'variable; this profile satisfies 1 to 3. Normalised; with '
            'numbers in Section&nbsp;%s.'
            % SR('Which side of resonance this design runs on'), width=CW))
    add(p('Unity power factor fixes the instantaneous power at '
          '2&nbsp;P<sub>in</sub>&thinsp;sin&sup2;&thinsp;&theta;, which fixes '
          'both the gain (Equation&nbsp;%(m)s) and the loading '
          '(Equation&nbsp;%(q)s) at every instant. The controller answers '
          'with the one variable it has. There is no current loop and no '
          'multiplier against a rectified reference: <b>the frequency '
          'profile f<sub>sw</sub>(&theta;) is the power factor correction.</b>'
          % dict(m=ER('Mreq'), q=ER('Qtheta'))))
    ext(tbl('The half cycle at six instants, normalised as in '
            'Figure&nbsp;%s. Trigonometry only; no part value enters.'
            % FR('an_pf_chain'),
            [['At the line phase', 'sin&thinsp;&theta;',
              'instantaneous power p/P<sub>in</sub>',
              'required gain M<sub>req</sub>/M<sub>pk</sub>',
              'loading Q/Q<sub>pk</sub>'],
             ['&theta; = 90&deg;, the peak', '1.000', '2.000', '1.000',
              '1.000'],
             ['&theta; = 60&deg;', '0.866', '1.500', '1.155', '0.750'],
             ['&theta; = 45&deg;', '0.707', '1.000', '1.414', '0.500'],
             ['&theta; = 30&deg;', '0.500', '0.500', '2.000', '0.250'],
             ['&theta; = 10&deg;', '0.174', '0.060', '5.759', '0.030'],
             ['&theta; &rarr; 0', '0', '0', '&infin;', '0']],
            widths=[CW * 0.22, CW * 0.13, CW * 0.22, CW * 0.23, CW * 0.20],
            key='pfwalk', split=True))
    add(p('In the last two rows the gain demand runs away, but so does the '
          'ability to meet it: an unloaded tank has unlimited gain at '
          'f<sub>o</sub>. The frequency walks down towards f<sub>o</sub> and '
          'the current goes to zero with the voltage.'))
    add(p('The controller has two signals on two time scales:'))
    ext(bullets([
        '<b>FB says how much.</b> It carries the error amplifier output '
        'through the optocoupler and commands an input <i>power</i> '
        '(Section&nbsp;%s). The loop behind it crosses well below the line '
        'frequency, so within one half cycle it is a constant: the '
        '<i>height</i> of the profile in panel 4.'
        % SR('The feedback pin is a power command'),
        '<b>HVSU says where in the cycle.</b> The start-up pin is also the '
        'input-voltage sense, so the controller knows the instantaneous '
        'rectified mains without a divider. That is the fast signal, the '
        '<i>shape</i> of the profile.',
        '<b>The internal PFC and THD block combines them</b> into '
        'I<sub>EA</sub>, the one current that moves the oscillator '
        '(Equation&nbsp;%s).' % ER('Tsw')]))
    add(note('<b>The draft datasheet does not publish the law inside that '
             'block.</b> This note therefore computes, from the tank, the '
             'profile that <i>must</i> come out if the current is to follow '
             'the voltage. Measuring f<sub>sw</sub>(&theta;) on the first '
             'board is how the block gets characterised.'))

    add(note('<b>Zero-crossing dead zone.</b> Very near &theta;&nbsp;= 0 the '
             'profile asks for a frequency below f<sub>Min</sub>, and the '
             'converter stops drawing current until the mains comes back. '
             'This is inherent and appears as third-harmonic distortion. The '
             'other THD mechanism is the voltage loop (Section&nbsp;%s).'
             % SR('Why the crossover must be low: the 2f<sub>l</sub> ripple')))

    add(h2('Solving for the profile without a root search'))
    add(p('The profile does not need a numerical root search. With '
          'M<sub>req</sub> = M<sub>pk</sub>/sin&thinsp;&theta;, '
          'Q = Q<sub>pk</sub>sin&sup2;&thinsp;&theta; and '
          'x = 1/f<sub>n</sub>&sup2; the gain equation is a cubic in x:'))
    add(eq(r'\lambda^{2}x^{3}+(q-2\lambda(1+\lambda))x^{2}'
           r'+((1+\lambda)^{2}-2q-\frac{u}{M_{pk}^{2}})x+q=0,'
           r'\qquad u=\sin^{2}\theta,\;\; q=Q_{pk}^{2}u^{2}', key='cubic'))
    add(p('One root is negative (the cubic is +q at x&nbsp;= 0 and tends to '
          '&minus;&infin; as x&nbsp;&rarr;&nbsp;&minus;&infin;). The other two '
          'are the capacitive and the '
          'inductive crossing of the same curve, and the inductive one is the '
          '<b>middle</b> root, because x falls as frequency rises. In the '
          'trigonometric form of Cardano it is always the k&nbsp;= 1 branch. '
          'No positive root means the no-solution case of Section&nbsp;'
          + SR('The other bound on &lambda;, and where it has no solution')
          + ', not a numerical failure. A grid search would also need an '
            'upper bound on f<sub>n</sub>, and a bound taken from the ac '
            'maximum instead of the morphing corner misses the real '
            'operating point.'))

    add(h2('Reading the gain chart of a single-stage converter'))
    add(p('The chart in Figure&nbsp;%(f)s is the standard picture: a family '
          'of curves, one required-gain line, one crossing. A single-stage '
          'converter is drawn the same way and <b>read differently</b>. '
          'Figure&nbsp;%(c)s puts the two side by side.'
          % dict(f=FR('f02_two_resonances'), c=FR('an_gain_compare'))))
    add(fig('an_gain_compare',
            'The ordinary chart and the single-stage one: same axes, same '
            'equation, read differently. Left, the family is <b>load</b> and '
            'the converter sits at one crossing. Right, the family is '
            '<b>line phase</b>, each curve has its own required-gain line in '
            'its own colour, and the converter travels the family twice per '
            'line cycle. The right panel is drawn for the input at which the '
            'line peak needs M&nbsp;=&nbsp;1 (M<sub>pk</sub> = 1); a lower '
            'input raises every dashed line by the same factor.', width=CW))
    add(p('Six differences:'))
    ext(bullets([
        '<b>The family parameter is line phase, not load.</b> The load is '
        'fixed at full and the curves are &theta;&nbsp;= 90&deg;, 60&deg;, '
        '45&deg;&thinsp;&hellip;, because Q&nbsp;= '
        'Q<sub>pk</sub>sin&sup2;&thinsp;&theta; falls as the mains falls.',
        '<b>The operating point moves, 100 or 120 times a second.</b> There '
        'is no single point to check; the design is checked along a path.',
        '<b>There is a ladder of required gains</b>, '
        'M<sub>req</sub>(&theta;) = M<sub>pk</sub>/sin&thinsp;&theta;, one '
        'line per phase, climbing without limit towards the zero crossing. '
        '<b>Each curve is compared with its own line only.</b>',
        '<b>The curves get taller as the lines get higher.</b> Halve '
        'sin&thinsp;&theta; and the requirement doubles, but Q falls by '
        'four and the curve grows far more than twice as tall. The margin '
        'grows towards the zero crossing.',
        '<b>M<sub>Z</sub>, the capacitive boundary, is drawn.</b> It is '
        'where arg Z<sub>in</sub> = 0 (Section&nbsp;%(b)s), a little to the '
        'right of each curve&rsquo;s peak, and every crossing must lie to '
        'its <b>right</b>. It has to be cleared at every phase, so it is a '
        'curve of its own.'
        % dict(b=SR('The two boundaries are not the same boundary')),
        '<b>M<sub>&infin;</sub> = 1/(1+&lambda;) is on the chart.</b> An '
        'ordinary LLC never needs a gain that small; a single-stage '
        'converter at high input voltage does. Below this line there is <b>no '
        'solution at no load, at any frequency</b>, and burst mode takes over '
        '(Section&nbsp;%(l)s).'
        % dict(l=SR('The other bound on &lambda;, and where it has no '
                    'solution'))]))
    add(note('<b>The mistake this chart invites:</b> checking the tallest '
             'curve against the lowest line. There is no such operating '
             'point. &theta; sets the curve <i>and</i> the line together, so '
             'only the same-coloured pairs mean anything.'))
    add(p('At the lowest equivalent input the chart answers &ldquo;can the '
          'tank make the gain and stay inductive?&rdquo; At the highest it '
          'answers &ldquo;how high does the frequency go, and is there a '
          'solution at light load?&rdquo; Section&nbsp;%s draws it at all six '
          'input voltages for that reason.' % SR('The gain chart of this design')))

    add(h2('The feedback pin is a power command'))
    add(p('Combining the burst-mode expression with the multiplier in the '
          'block diagram gives the meaning of the feedback voltage '
          'V<sub>FB</sub>:'))
    add(eq(r'V_{FB}\;=\;V_{os}+\frac{2K_{HV}}{K_{M}K_{FF}}\,R_{CS}\,P_{in,LLC}'
           r'\;=\;0.5\,\mathrm{V}+0.167\,'
           r'\frac{\mathrm{V}}{\Omega\cdot\mathrm{W}}\,R_{CS}\,P_{in,LLC}', key='VFB'))
    add(p('P<sub>in,LLC</sub> is the power drawn by the bridge: R<sub>CS</sub> '
          'sits in the bridge return, so that is the power the controller '
          'senses. V<sub>os</sub> is the 0.5&nbsp;V the pin sits at with no power '
          'commanded; K<sub>HV</sub>, K<sub>M</sub> and K<sub>FF</sub> are the '
          'input-voltage sense, multiplier and feed-forward gains of the '
          'block diagram. The 2.8&nbsp;V feedback span gives '
          '2.8/0.167 = 16.8&nbsp;&Omega;&middot;W, the maximum-power rule of '
          'the datasheet. <b>Maximum power, burst entry and overload '
          'detection all sit on one scale, R<sub>CS</sub>.</b> The optocoupler '
          'loop commands an input power; the internal loop distributes it '
          'over the line cycle as sin&sup2;&thinsp;&theta;.'))
    add(note('This is why the current-sense pin tolerates no filter and no '
             'series resistor: the power law and the over-current threshold '
             'read the same pin.'))

    add(h2('Which side of resonance this converter runs on'))
    add(p('A single-stage converter does not pick one side. The equivalent '
          'input follows a half sine and the required gain follows it, so '
          'the operating point can cross f<sub>r</sub> and come back within '
          'one line cycle. Whether it crosses, and for how long, depends on '
          'the mains voltage; at a low input it can stay below f<sub>r</sub> '
          'all the way. Section&nbsp;'
          + SR('Which side of resonance this design runs on')
          + ' shows the profile at the six input voltages.'))
    add(note('<b>Both sides must be designed for.</b> The boosting side sets '
             'the gain requirement and the ZVS margin. The bucking side sets '
             'the top frequency and takes the secondary out of ZCS, so the '
             'rectifier body diode and the SR dead time matter here.'))

    add(h2('Why &lambda; must be about 0.5'))
    add(p('A classic LLC uses m&nbsp;=&nbsp;(L<sub>r</sub>+L<sub>m</sub>)/L<sub>r</sub> of 5 '
          'to 10, that is &lambda; of 0.11 to 0.25. A single-stage converter '
          'needs very high gain near the zero crossing, and peak gain falls '
          'as &lambda; falls. ST&rsquo;s evaluation board runs '
          '&lambda;&nbsp;=&nbsp;0.500 and this design comes out close to it '
          '(Section&nbsp;%s): the value comes from the topology.'
          % SR('Following the numbers through')))
    add(p('The price is circulating current: a small L<sub>m</sub> means a '
          'large magnetising current with conduction loss at every load. '
          '<b>A single-stage PFC LLC is less efficient than a two-stage LLC, '
          'inherently.</b>'))

    add(h2('f<sub>sw,max</sub> does not check the tank &mdash; it computes it'))
    add(p('Two of the four candidates for &lambda; carry the specified '
          'maximum switching frequency in a denominator:'))
    add(eq(r'\lambda_{2}=\frac{\lambda_{1}}'
           r'{1-\left(\frac{f_r}{f_{sw,max}}\right)^{2}}'
           r'\qquad\qquad'
           r'\lambda_{TD}=\frac{\lambda_{1}}'
           r'{1-\frac{\pi^{2}}{8}\left(\frac{f_r}{f_{sw,max}}\right)^{2}}', key='lam'))
    add(p('&lambda;<sub>1</sub> is the plain minimum-gain condition; '
          '&lambda;<sub>2</sub> and &lambda;<sub>TD</sub> fold in the '
          'frequency ceiling: the tank must reach the lowest required gain '
          '<i>before</i> it runs out of frequency. With the usual '
          'f<sub>sw,max</sub> = 1.5&nbsp;f<sub>r</sub> the squared ratio is '
          '0.44 and <b>the value typed as f<sub>sw,max</sub> roughly doubles '
          'the &lambda; asked for</b>. Set it near f<sub>r</sub> and the '
          'required &lambda; goes to infinity. The fourth candidate, '
          '&lambda;<sub>3</sub>, comes from the specified minimum switching '
          'frequency; it is small in this converter and does not bind.'))
    add(note('The common 1.5&nbsp;&times;&nbsp;f<sub>r</sub> is a '
             '<b>choice</b>, not a limit, and it sits upstream of the tank: '
             'a round number typed into it changes L<sub>m</sub>.'))
    add(p('f<sub>Max</sub>, the oscillator ceiling, is different. It '
          '<i>is</i> a limit, fixed by R<sub>T</sub>, C<sub>T</sub>, '
          'I<sub>EA,max</sub> and the idle time, and it is checked after the '
          'fact by k<sub>ceil</sub> '
          '(Section&nbsp;%s). One decides the tank; the other reports whether '
          'the oscillator can serve it.'
          % SR('What a verification margin is')))

    add(h2('The other bound on &lambda;, and where it has no solution'))
    add(p('The ceiling on &lambda; comes from the lowest required gain, at '
          'the highest equivalent input and no load. The no-load gain does '
          'not fall without limit; raising the frequency only brings it '
          'down to an asymptote:'))
    add(eq(r'M_{\infty}\;=\;\lim_{f\to\infty}M_{OL}'
           r'\;=\;\frac{1}{1+\lambda}', key='Minf'))
    add(p('with M<sub>OL</sub> the gain curve at no load (Q = 0, output '
          'open).'))
    add(p('<b>If the required minimum gain is below M<sub>&infin;</sub>, no '
          'frequency satisfies it.</b> A spreadsheet solving for that '
          'frequency returns an error, and the error looks like a broken '
          'formula. It is not: the question has no answer. Whether a tank '
          'sits above or below the asymptote is a matter of a per cent, and '
          'no full-load check shows it; Section&nbsp;%s reports it for this '
          'design.' % SR('Following the numbers through')))
    add(note('Losing the solution is not a failure: no load at high input voltage '
             'belongs to <b>burst mode</b>. But it decides which candidate '
             'turns ratios can still regulate by frequency alone at no '
             'load.'))

    # =============================================================== 4
    add(h1('Topology morphing'))
    add(p('A resonant tank has a usable gain range of roughly 1.5:1 at full '
          'load. A universal mains asks for %(rm).2f:1. No single tank covers '
          'that and keeps ZVS, so the L6790A changes the bridge instead.'
          % dict(V, rm=V['Vacmax'] / V['Vacmin'], rt=V['Veqhi'] / V['Veqlo'], rt2=V['Veqhi2'] / V['Veqlo2'])))
    add(p('Below a mains peak of 235&nbsp;V the part runs a <b>full '
          'bridge</b>, which drives the tank with twice the rail. Above '
          '245&nbsp;V<sub>pk</sub> it runs a <b>half bridge</b>. The tank '
          'therefore sees %(Veqlo).1f to %(Veqhi).1f&nbsp;Vac equivalent, a '
          'range of %(rt).2f:1, and one tank can cover it.' % dict(V, rm=V['Vacmax'] / V['Vacmin'], rt=V['Veqhi'] / V['Veqlo'], rt2=V['Veqhi2'] / V['Veqlo2'])))
    add(fig('f13_morphing',
            'Morphing collapses a %.2f:1 mains range into a %.2f:1 range at '
            'the tank. The worst corners are the morphing edges, not the ends '
            'of the mains range. Drawn for a falling mains; Figure&nbsp;%s '
            'shows the band in which the mode depends on the direction.'
            % (V['Vacmax'] / V['Vacmin'], V['Veqhi'] / V['Veqlo'],
               FR('f18_morph_levels'))))

    add(h2('Full bridge'))
    add(p('Diagonal pairs conduct together, so the drive is a square wave of '
          'amplitude V<sub>in</sub> with fundamental '
          '(4/&pi;)&thinsp;V<sub>in</sub>. All four devices switch.'))
    add(fig('f15_bridge_fb',
            'Full bridge: conduction path in each half period, and the '
            'resulting tank drive.'))

    add(h2('Half bridge'))
    add(p('LOUT2 is held high: S3 never turns on and S4 never turns off, so '
          'the bridge output swings between 0 and V<sub>in</sub>. '
          'C<sub>r</sub> blocks the V<sub>in</sub>/2 of dc, and the tank '
          'sees &plusmn;V<sub>in</sub>/2, a fundamental of '
          '(2/&pi;)&thinsp;V<sub>in</sub>. No extra hardware.'))
    add(fig('f16_bridge_hb',
            'Half bridge: leg 2 stops switching, and C<sub>r</sub> removes '
            'the dc that the asymmetric drive creates.'))
    add(note('<b>The standing device is the hottest one.</b> S4 never '
             'switches but conducts the full tank current continuously, and '
             'in this design it is the hottest single device '
             '(Section&nbsp;' + SR('Where the power goes') + ').'))

    add(h2('How the controller does it'))
    add(p('Only leg 2 changes between the modes: HOUT2 stops and stays low, '
          'LOUT2 stops and stays high. The thresholds '
          'are <b>fixed inside the IC</b>; R<sub>CFG</sub> only enables '
          'morphing and sets the brown-out threshold.'))
    add(fig('f17_morph_gates',
            'The four bridge drive signals in each mode. Holding LOUT2 high '
            'and HOUT2 low is the entire mechanism.'))

    add(h2('The hysteresis band, and the range it really implies'))
    add(p('The part drops to half bridge at 245&nbsp;V<sub>pk</sub> going up '
          'and returns to full bridge at 235&nbsp;V<sub>pk</sub> coming down. '
          'The hysteresis stops toggling, but <b>between the two the mode '
          'depends on the direction of travel</b>, not on the voltage.'))
    add(p('Taking each threshold where its mode is guaranteed gives '
          '%(Veqlo).1f to %(Veqhi).1f&nbsp;Vac (%(rt).2f:1). Including the band '
          'gives <b>%(Veqlo2).1f to %(Veqhi2).1f&nbsp;Vac (%(rt2).2f:1)</b>. This '
          'design passes at the wider range too; do not use the narrower '
          'figure when tightening a specification.' % dict(V, rm=V['Vacmax'] / V['Vacmin'], rt=V['Veqhi'] / V['Veqlo'], rt2=V['Veqhi2'] / V['Veqlo2'])))
    add(fig('f18_morph_levels',
            'Where each mode applies. Inside the band the mode depends on '
            'which direction the mains arrived from. V<sub>BO</sub> is the '
            'brown-out threshold, set by R<sub>CFG</sub> (Section&nbsp;%s).'
            % SR('Brown-out and bridge configuration: the CFG pin')))
    add(note('No nominal mains voltage lies in 166 to 173&nbsp;Vrms; the '
             'band is met in sags, on a programmable ac source and in dip and '
             'surge tests. '
             'Test it with a <b>step</b> across the threshold, not a ramp.'))
    add(note('<b>Transition transient.</b> Crossing a threshold changes the '
             'drive 2:1 within one line cycle, against a loop that crosses '
             'in the tens of hertz, so the output dips (going up) or '
             'overshoots (coming down) until the loop recovers. The dip is '
             'less severe than hold-up, which is already met, so it is no '
             'reason to enlarge C<sub>out</sub>; neither has been checked in '
             'the time domain.'))

    # =============================================================== 5
    # the sweep populates ZVS_WORST, which the summary tables of the
    # design example read before the grid itself is printed
    _zvs_grid(A)

    add(h1('Design procedure'))
    add(fig('bom_power_stage',
            'The power stage. The bridge rectifier feeds the leg pair '
            'directly: no bulk capacitor, no boost stage. The secondary is '
            'drawn as centre tap (Solution&nbsp;1) and full bridge '
            '(Solution&nbsp;2). Drawing from the ST L6790A design '
            'spreadsheet.', width=CW))
    add(p('Pick the secondary first: it sets N<sub>rect</sub>, and '
          'N<sub>rect</sub> sets the reflected voltage. A centre tap has one '
          'device in the conduction path, a full bridge two, so at a low '
          'output voltage the centre tap halves the rectifier conduction '
          'loss at the price of twice the reverse voltage per device. This '
          'design uses the centre tap. The steps below are in dependency '
          'order.'))

    add(h2('The specification'))
    add(p('The full specification is in Section&nbsp;%(ref)s. Two '
          'qualifiers apply to every step: <b>the worst line frequency is '
          'the lowest</b>, and <b>hold-up is specified at the ripple '
          'trough</b>.'
          % dict(V, ref=SR('The specification, sorted by what kind of number '
                           'it is'))))

    add(h2('The equivalent input range'))
    add(p('With morphing the tank does not see 90 to %(Vacmax).0f&nbsp;Vac. '
          'It sees an <b>equivalent</b> input given by the bridge mode:'
          % V))
    # matplotlib mathtext has no cases environment and no \text
    add(eq(r'V_{ac,eq}=2\,V_{ac}\;\;\mathrm{(full\;bridge)}'
           r'\;\;\;\;\;\;\;\;V_{ac,eq}=V_{ac}\;\;\mathrm{(half\;bridge)}', key='Veq'))
    add(p('At the half-bridge edge (245&nbsp;V<sub>pk</sub>) the tank sees '
          '%(Veqlo).1f&nbsp;Vac; at the full-bridge edge '
          '(235&nbsp;V<sub>pk</sub>) it sees %(Veqhi).1f&nbsp;Vac. <b>These '
          'edges are the design corners</b>: the low one for gain and ZVS, '
          'the high one for switching frequency. The mains voltages a supply '
          'actually meets map onto the same axis: 90 and 110&nbsp;Vac in '
          'full bridge become 180 and 220&nbsp;Vac equivalent, 230 and '
          '264&nbsp;Vac in half bridge stay 230 and 264. All four lie inside '
          'the two edges, and this note reports at all six conditions.'
          % V))

    add(h2('Turns ratio and reflected voltage'))
    add(p('The turns ratio appears only multiplied by the effective output '
          'voltage, so what matters is the <b>reflected voltage</b> '
          'V<sub>refl</sub>:'))
    add(eq(r'V_{refl}=n\,V_{o,eff}=n\left(V_{out}+N_{rect}V_{f}\right)', key='Vrefl'))
    add(p('V<sub>f</sub> is the forward drop of one rectifier and '
          'N<sub>rect</sub> the number in the conduction path. '
          '<b>n</b> is the model ratio in the gain equation; '
          '<b>n<sub>T</sub></b> is the wound ratio with the leakage folded '
          'into L<sub>r</sub>. At &lambda;&nbsp;&asymp;&nbsp;0.5 they differ '
          'by more than 20&nbsp;%% (Section&nbsp;%(ref)s), so the drawing '
          'must carry open- and short-circuit inductance as well as turns.'
          % dict(ref=SR('Two ratios, two inductances'))))

    add(h2('The resonant tank'))
    add(p('The equivalent ac load resistance for a centre-tapped secondary, '
          'evaluated at the line peak, is'))
    add(eq(r'R_{ac}=\frac{4}{\pi^{2}}\,'
           r'\frac{n^{2}V_{o,eff}^{2}}{P_{in,LLC}}', key='Rac'))
    add(p('with P<sub>in,LLC</sub> the power into the resonant stage. The '
          'usual LLC form writes 8/&pi;&sup2; with the one output power a two-stage '
          'converter has. Here the drawn power is '
          '2P&thinsp;sin&sup2;&thinsp;&theta;, so R<sub>ac</sub> is pinned '
          'to the line peak, where p = 2P: the 8 becomes a 4, and Q means '
          'the quality factor at the peak, with '
          'Q(&theta;) = Q<sub>pk</sub>sin&sup2;&thinsp;&theta; elsewhere. '
          'Using the two-stage value understates the loading by two.'))
    add(p('The gain requirement at the low corner and the ZVS requirement '
          'cap the quality factor at Q<sub>ZVS</sub>. '
          'R<sub>ac</sub>Q<sub>ZVS</sub> is the impedance the tank is sized '
          'from: it fixes C<sub>r</sub> through Equations&nbsp;%(q)s and '
          '%(e)s, and C<sub>r</sub> with f<sub>r</sub> fixes L<sub>r</sub>. '
          'Three rules matter more than the arithmetic:'
          % dict(q=ER('Qdef'), e=ER('fr'))))
    ext(bullets([
        'The three calculated figures are not one tank. L<sub>r</sub> is '
        'whatever pairs with the <b>selected</b> C<sub>r</sub>, and the '
        'L<sub>m</sub> figure is L<sub>r</sub> over the &lambda; that '
        '<i>no load at the high corner</i> asks for, a condition a design '
        'may knowingly not meet (Section&nbsp;'
        + SR('The other bound on &lambda;, and where it has no solution')
        + '). It is not a value to round towards.',
        '<b>A larger L<sub>m</sub> costs ZVS margin.</b> It lowers '
        '&lambda; and the magnetising current that swings the node. '
        'C<sub>r</sub> above and L<sub>m</sub> below their calculated values '
        'do the opposite.',
        '<b>Stay below the Q<sub>ZVS</sub> cap.</b> That gap is most of the '
        'ZVS margin. Choose L<sub>m</sub> with n so that '
        'n<sub>T</sub>&nbsp;=&nbsp;n&radic;(1+&lambda;<sub>act</sub>) is a '
        'ratio that can be wound.']))

    add(h2('ZVS verification'))
    add(p('The closed-form ZVS estimate in most guides is a fitted '
          'approximation at the design Q<sub>ZVS</sub>, not at the Q the '
          'converter runs at. Against a full sweep it is off by tens of per '
          'cent, and nothing in it guarantees which way; optimistic is the '
          'dangerous direction.'))
    add(note('The shortcut is written with a bare &lambda; and means the '
             '<i>design</i> &lambda;. Read it with &lambda;<sub>act</sub> and '
             'the phase can come out <b>negative</b> for a tank well inside '
             'the inductive region. The sweep has no such ambiguity.'))
    add(p('Sweep &theta;, input voltage and load with the <b>selected</b> '
          'tank and take the minimum. Section&nbsp;%(ref)s does it for this '
          'design; the worst point is not where one would expect.'
          % dict(ref=SR('ZVS over the whole operating space'))))

    add(h2('Which side of resonance the converter runs on'))
    add(p('Below f<sub>r</sub> the secondary current is a full resonant '
          'half sine followed by the freewheeling interval, and the conduction ratio '
          'd = f<sub>sw</sub>/f<sub>r</sub> is less than one; above '
          'f<sub>r</sub> the half sine is cut short and d clamps at one. The '
          'rms figures behind ratings and losses contain d.'))
    add(p('<b>The turns ratio decides the side.</b> M<sub>req</sub> = '
          '2n&thinsp;V<sub>o,eff</sub>/(&radic;2&nbsp;V<sub>ac,eq</sub>), so a '
          'larger n asks for more gain and sits further below resonance. '
          'Two candidate transformers on the same tank can end up on '
          'opposite sides of f<sub>r</sub> at the same mains voltage.'))
    add(note('Settle this before the transformer is ordered: below '
             'resonance the rectifiers turn off at zero current, above it '
             'they do not.'))

    add(h2('Currents over the line cycle'))
    add(p('Ratings come from the worst switching cycle; losses from the '
          'line-cycle rms. Two further rules:'))
    ext(bullets([
        'The primary devices and the sense resistor see the '
        '<b>composite</b> tank current: reflected load current plus '
        'magnetising current. Its peak is neither the sum nor the larger of '
        'the two peaks, because they occur at different instants.',
        'Below resonance the secondary conducts for d of each half period. '
        'The rms is the pulse peak times &radic;d; omitting d '
        'over-estimates it, and the loss by its square. '
        'Section&nbsp;' + SR('The currents this design has to carry')
        + ' draws the composite current of this design.']))
    add(h2('The transformer'))
    add(p('The tank fixed L<sub>r</sub>, L<sub>m</sub> and a ratio; the '
          'transformer has turns, an open-circuit inductance and a leakage. '
          '<b>Two turns ratios and two inductances carry almost the same '
          'names</b>, and that is where most errors are made. This section '
          'turns Section&nbsp;'
          + SR('Not a flyback, and why that changes the core')
          + ' into numbers a supplier can measure.'))
    add(p('Every number on the drawing is read off the primary current, the '
          'current in each secondary winding, the secondary winding voltage, '
          'or one bench test. Figure&nbsp;%(f)s marks where on this '
          'design&rsquo;s waveforms; Table&nbsp;%(t)s says what each mark '
          'sets.' % dict(f=FR('an_xfmr_read'), t=TR('xfmr-read'))))
    _J = _CORE.J_CU
    ext(tbl('What each mark in the figure sets. Currents are per unit: for '
            'one transformer that is the whole part; split into N<sub>x</sub> '
            'units (Section&nbsp;%s), the primaries are in series and the '
            'secondaries in parallel.' % SR('If one transformer is not practical'),
            [['Mark', 'Item', 'Read from &mdash; and over what',
              'What it sets'],
             ['<b>1</b>', 'Primary peak current',
              'Top of i<sub>p</sub>: the half sine of load current riding '
              'on the magnetising ramp. Worst switching cycle: line peak, '
              'minimum equivalent input, full load.',
              'Primary switch and OCP1 headroom. <b>Not</b> the saturation '
              'test.'],
             ['<b>2</b>', 'Primary rms current',
              'i<sub>p</sub>&sup2; averaged over the whole switching period, '
              'then over the line half cycle. With N<sub>x</sub> units each '
              'carries all of it: the primaries are in series.',
              'Primary copper: A<sub>cu</sub> = I<sub>rms</sub>/J per unit'],
             ['<b>3</b>', 'Magnetising peak',
              'The dashed i<sub>Lm</sub> at the switching instant. Below '
              'resonance it depends on neither f<sub>sw</sub> nor load, '
              'only on V<sub>o,eff</sub>, so it is the same on every cycle.',
              'The peak flux; and, scaled to V<sub>OVP2</sub>, the '
              'DC-overlap test current (mark 7)'],
             ['<b>4</b>', 'Secondary peak current',
              'Top of the pulse in either secondary winding, same worst '
              'cycle. With N<sub>x</sub> units each carries 1/N<sub>x</sub> of '
              'the rectifier-leg value: the secondaries are in parallel.',
              'Rectifier peak rating; the secondary terminations'],
             ['<b>5</b>', 'Secondary rms current, each winding',
              'One pulse per period in each winding, so the rms is taken '
              'over the whole period with the idle half counted, then over '
              'the line half cycle.',
              'Secondary copper: A<sub>cu</sub> = I<sub>rms</sub>/J, per '
              'winding and per unit'],
             ['<b>6</b>', 'Winding volt-seconds',
              'The secondary winding voltage is V<sub>o,eff</sub> for the '
              'resonant half period T<sub>r</sub>/2 while the rectifier '
              'conducts. That area is the flux swing 2&thinsp;N<sub>s</sub>'
              'A<sub>e</sub>B<sub>pk</sub>; f<sub>r</sub> is the worst case '
              'because the interval never gets longer than T<sub>r</sub>/2.',
              'Core area and N<sub>s</sub>: A<sub>e</sub> &ge; '
              'V<sub>o,eff</sub>/(4 f<sub>r</sub> N<sub>s</sub> B<sub>max</sub>)'],
             ['<b>7</b>', 'DC-overlap (saturation) test',
              'Not a waveform. LCR meter across the primary NP1, every other '
              'winding open (secondaries NS2 and NS3, auxiliary NAUX); a dc current overlapped on the primary and the '
              'primary inductance read against it. The test '
              'current is mark 3 scaled to the highest output the controller '
              'allows, V<sub>OVP2</sub>/V<sub>out</sub>.',
              'Core saturation margin; the number the supplier tests to'],
             ['&mdash;', 'L<sub>open</sub>, L<sub>short</sub>',
              'LCR meter across NP1 at %s. L<sub>open</sub>: every other winding '
              'open. L<sub>short</sub>: NS2 and NS3 both shorted, NAUX open. '
              'Terminal quantities, so a supplier can test them.' % '100&nbsp;kHz, 1&nbsp;V',
              'L<sub>m</sub> + L<sub>r</sub> and L<sub>r</sub>: the tank '
              'itself']],
            widths=[CW * 0.07, CW * 0.17, CW * 0.48, CW * 0.28],
            key='xfmr-read', split=True))

    add(h2('Two ratios, two inductances'))
    add(p('With all leakage referred to the primary the tank sees an ideal '
          'transformer of ratio n, a series L<sub>r</sub> and a shunt '
          'L<sub>m</sub>. That n is <b>not</b> the wound ratio. With k the '
          'coupling coefficient,'))
    add(eq(r'n \;=\; k\,n_{T},\qquad k \;=\; \sqrt{\frac{L_{m}}{L_{m}+L_{r}}}'
           r'\;=\;\frac{1}{\sqrt{1+\lambda}}', key='nnT'))
    add(p('so n<sub>T</sub> = n&radic;(1+&lambda;): more than 20&nbsp;%% '
          'apart at &lambda; &asymp; 0.5, far more than any gain margin.'
          % {}))
    add(p('The inductances split the same way. The tank model uses '
          'L<sub>r</sub> and L<sub>m</sub>; the physical transformer has a '
          'magnetising inductance L<sub>&mu;</sub> with leakage on both '
          'sides:'))
    add(eq(r'L_{\mu}=\sqrt{L_{m}\,(L_{m}+L_{r})}\,,\qquad '
           r'L_{L1}=L_{m}+L_{r}-L_{\mu}\,,\qquad '
           r'L_{L2}=\frac{L_{L1}}{n_{T}^{2}}', key='Lmu'))
    add(p('with L<sub>L1</sub> the primary leakage and L<sub>L2</sub> the '
          'secondary leakage, each on its own side of the ratio.'))
    add(fig('an_integrated',
            'The same transformer drawn both ways. Above, as wound: leakage '
            'on both sides, the physical L<sub>&mu;</sub> in shunt, ratio '
            'n<sub>T</sub>&nbsp;:&nbsp;1, driven by v<sub>d</sub>. Below, referred to '
            'the primary and driven by the fundamental of v<sub>d</sub>: one '
            'L<sub>r</sub>, one L<sub>m</sub>, ratio n&nbsp;:&nbsp;1. Neither '
            'the shunt elements nor the ratios are the same numbers.'))
    add(note('The as-wound form (L<sub>L1</sub>, L<sub>&mu;</sub>, L<sub>L2</sub>) assumes the leakage splits evenly. The '
             'real split does not matter: the tank sees only the two '
             'quantities a meter can read.'))

    add(h2('What the transformer specification must say'))
    add(p('Only two inductances are measurable at the terminals, and they '
          'are the two the tank needs:'))
    add(eq(r'L_{open}=L_{\mu}+L_{L1}=L_{m}+L_{r},\qquad '
           r'L_{short}=L_{L1}+\frac{L_{\mu}\,n_{T}^{2}L_{L2}}'
           r'{L_{\mu}+n_{T}^{2}L_{L2}}=L_{r}', key='Lopen'))
    add(p('Both are read across the primary. L<sub>open</sub>: every other '
          'winding open. L<sub>short</sub>: every secondary shorted (on a '
          'centre-tapped part both halves), the auxiliary open. <b>Specify '
          'those two and the turns, never L<sub>&mu;</sub></b>: no terminal '
          'pair exposes it. State the turns as numbers, because with one or '
          'two secondary turns the lead-out loop dominates that '
          'winding&rsquo;s inductance, and the root of the open-circuit '
          'inductances read at the primary and at one secondary, '
          '&radic;(L<sub>1</sub>/L<sub>2</sub>), does not give the ratio.'))

    add(h2('Peak flux is set by the secondary, not the primary'))
    add(p('Mark <b>6</b> of Figure&nbsp;%(f)s: the secondary winding voltage '
          'is a rectangle of height V<sub>o,eff</sub> and width '
          'T<sub>r</sub>/2, and the flux swings &plusmn;B<sub>pk</sub> across '
          'it. Above resonance the secondary conducts for a shorter '
          'switching half period, so f<sub>r</sub> is the worst case '
          'everywhere on the line cycle:' % dict(f=FR('an_xfmr_read'))))
    add(eq(r'B_{pk}=\frac{V_{o,eff}}{4\,f_{r}\,N_{s}\,A_{e}}'
           r'\qquad\Longrightarrow\qquad '
           r'A_{e}\;\geq\;\frac{V_{o,eff}}{4\,f_{r}\,N_{s}\,B_{max}}', key='Bpk'))
    add(p('<b>N<sub>p</sub> does not appear.</b> Only secondary turns reduce '
          'the flux. For a low-voltage, high-current output, where the '
          'secondary wants to be one turn, halving N<sub>s</sub> doubles the '
          'core area.'))
    add(note('From an inductance the same flux is B<sub>pk</sub> = '
             'L<sub>&mu;</sub>i<sub>&mu;,pk</sub>/(N<sub>p</sub>A<sub>e</sub>) '
             'with the <b>physical</b> L<sub>&mu;</sub>. Using the tank '
             'L<sub>m</sub> understates it by &radic;(1+&lambda;).'))

    add(h2('Choosing the core: two areas, and the one that usually decides'))
    add(p('A core must satisfy two independent conditions: enough '
          'cross-section A<sub>e</sub> for the flux at the chosen turns, and '
          'enough window A<sub>N</sub> for the copper. Their product is the '
          '<b>area product</b>, and either can bind.'))
    #  no core figures here: 'on a PQ core ten to twenty per cent' was
    #  typed, and a chapter-6 note has no business quoting cores this
    #  design does not use (2026-09-23, user)
    add(note('<b>Check the flux against A<sub>min</sub>, not A<sub>e</sub>.</b> '
             'The narrowest section saturates first: the real peak is '
             'B<sub>pk</sub>&thinsp;A<sub>e</sub>/A<sub>min</sub>.'))
    add(p('In a single-stage PFC LLC <b>a third condition normally '
          'decides</b>: the leakage must come out at L<sub>r</sub>. As a '
          'fraction of what a meter reads,'))
    add(eq(r'\frac{L_{short}}{L_{open}}=\frac{L_{r}}{L_{m}+L_{r}}'
           r'=\frac{\lambda}{1+\lambda}', key='lkfrac'))
    add(p('At &lambda;&nbsp;&asymp;&nbsp;0.5 that is <b>about a third</b>. A '
          'conventional transformer leaks a few per cent; this one must leak '
          'ten times more, on purpose. Leakage that large is a winding '
          '<b>geometry</b>, and geometry costs window. A core that passes '
          'on A<sub>e</sub> and copper can still fail here.'))

    add(h2('The winding arrangement is the leakage'))
    add(p('Leakage is set by how the windings are arranged and how far '
          'apart they sit:'))
    ext(bullets([
        '<b>Interleaved</b> (primary, secondary, primary): one or two per '
        'cent. What a forward or flyback transformer wants; the opposite of '
        'what is needed here.',
        '<b>Concentric, not interleaved</b>: a few per cent. Still short.',
        '<b>Side by side</b>, primary on one half of the width and '
        'secondary on the other: tens of per cent, adjustable by the gap '
        'between them. <b>This is what a single-stage tank asks for</b>, '
        'and why the window must be generous.',
        '<b>Split</b>, the primary in two parts, one on either side of the '
        'secondary: each gap carries only its own part&rsquo;s ampere-turns, '
        'so the leakage is a fraction of the side-by-side value and the '
        'gaps still trim it. The ratio of the parts sets where the target '
        'falls in the range the gaps can reach.',
        '<b>A magnetic shunt</b> in the window: leakage without winding '
        'width, at the cost of a part and a harder tolerance.']))
    add(p('The leakage of a sectioned winding can be estimated before '
          'anything is wound. Along the bobbin the ampere-turns rise across '
          'part A, stay flat across the first gap, fall through the '
          'secondary and come back to zero across part B; the field crosses '
          'the window depth h<sub>w</sub>, and its energy gives'))
    add(eq(r'L_{short}\approx\frac{\mu_{0}\,l_{N}}{h_{w}}\left[N_{A}^{2}'
           r'\left(\frac{w_{A}}{3}+g_{1}\right)+\left(N_{A}^{2}-N_{A}N_{B}'
           r'+N_{B}^{2}\right)\frac{w_{S}}{3}+N_{B}^{2}\left(g_{2}'
           r'+\frac{w_{B}}{3}\right)\right]', key='leak'))
    add(p('with N<sub>A</sub> + N<sub>B</sub> = N<sub>p</sub> the turns of '
          'the two primary parts, w<sub>A</sub>, w<sub>S</sub>, w<sub>B</sub> '
          'the axial widths of part A, the secondary and part B, '
          'g<sub>1</sub> and g<sub>2</sub> the gaps and l<sub>N</sub> the '
          'mean turn. N<sub>B</sub>&nbsp;=&nbsp;0 is the side-by-side '
          'winding. It is an upper estimate: it takes the whole turn as '
          'inside the core, and the part outside, with no outer leg to '
          'return the field, leaks less. A field solution of the actual '
          'layout narrows it; the first samples decide.'))
    add(note('The usual transformer advice is to interleave. Here L<sub>r</sub> '
             'is a design value, and a supplier who &ldquo;improves&rdquo; '
             'the coupling breaks the converter. Say so on the drawing, next '
             'to L<sub>short</sub>.'))

    add(h2('The gap, and why the drawing must not name it'))
    add(p('L<sub>m</sub> is far below what an ungapped core gives, so the '
          'core is gapped:'))
    add(eq(r'A_{L}=\frac{L_{open}/N_{x}}{N_{p}^{2}}'
           r'\qquad\qquad '
           r'g\;\approx\;\frac{\mu_{0}\,A_{e}}{A_{L}}', key='ALgap'))
    add(p('with N<sub>x</sub> the number of units in the assembly (1 for a '
          'single transformer; Section&nbsp;%s), g the '
          'total centre-leg gap and &mu;<sub>0</sub> the permeability of free '
          'space. The gap expression ignores fringing, which '
          'makes the gap actually needed larger. <b>Specify A<sub>L</sub>, or '
          'better L<sub>open</sub>, and leave the gap to the supplier</b>: '
          'that is what they grind to and what a meter can check.'
          % SR('If one transformer is not practical')))

    add(h2('The window: wire, current density and what actually fits'))
    add(p('Marks <b>2</b> and <b>5</b> of Figure&nbsp;%(f)s. Copper is sized '
          'on the <b>line-cycle</b> rms: the rms of each switching period, '
          'averaged in I&sup2; over the line half cycle. The secondary value '
          'is per winding and per unit, with the idle half inside the '
          'average.' % dict(f=FR('an_xfmr_read'))))
    add(p('Each winding needs a copper area set by its rms current and the '
          'current density the design can cool:'))
    add(eq(r'A_{cu}=\frac{I_{rms}}{J}\qquad\qquad '
           r'\sum_{w} N_{w}A_{cu,w}\;\leq\;k_{u}A_{N}', key='window'))
    add(p('with N<sub>w</sub> the turns of winding w and A<sub>cu,w</sub> '
          'its copper area. J is an assumption: 4 to 5&nbsp;A/mm&sup2; in '
          'free air, less enclosed. k<sub>u</sub>, the window utilisation, '
          'is <b>0.3 or less</b> with Litz wire once insulation, bobbin '
          'wall, margins and tape are counted. Sizing on bare copper '
          'overstates what fits by three times.'))
    add(note('Split into N<sub>x</sub> units (Section&nbsp;%s), every unit '
             'carries the whole primary current, because the primaries are in '
             'series; only the secondaries share. That is why splitting helps '
             'a low-voltage, high-current output.' % SR('If one transformer is not practical')))

    add(h2('Skin depth, and why the wire is not a wire'))
    add(p('At the switching frequency current crowds into a surface layer '
          'of depth'))
    add(eq(r'\delta=\sqrt{\frac{\rho}{\pi f\mu_{0}}}', key='skin'))
    add(p('with &rho; the resistivity of copper at the winding temperature '
          'and f the frequency it carries, here f<sub>r</sub>. Copper deeper than '
          '&delta; below the surface carries little current, so a conductor '
          'thicker than 2&delta; gains little. The field from the other turns '
          'also drives circulating current in each conductor (the proximity '
          'effect), and in a side-by-side winding that term can dominate.'))
    add(p('So a winding is not one wire. There are two ways out:'))
    ext(bullets([
        '<b>Litz wire</b>: a bundle of many fine wires, '
        'twisted so that each takes a turn at every position, and each '
        'insulated by its own enamel. One fine wire is a <b>strand</b>; '
        'd<sub>s</sub> is its diameter and a<sub>s</sub> its copper '
        'cross-section. The rule is d<sub>s</sub>&nbsp;&le;&nbsp;2&delta; '
        '<b>per strand</b>.',
        '<b>Copper foil</b> on a low-voltage, high-current secondary: '
        'thickness t<sub>f</sub> near &delta;, width does the carrying. It '
        'terminates well into a centre tap, but <b>only in a concentric '
        'winding</b>, where the leakage field runs along the foil. Between '
        'the sections of a side-by-side or split winding the field crosses '
        'the window, straight through the face of the foil, and drives '
        'eddy currents across its whole width. There the secondary is Litz '
        'too.',
        'The ac resistance heats the winding; the dc resistance is a floor, '
        'not an answer.']))
    add(p('<b>Litz.</b> Pick a standard strand at or below 2&delta;; the '
          'strand count is the copper needed over what one strand gives:'))
    add(eq(r'a_{s}=\frac{\pi d_{s}^{2}}{4}\,,\qquad '
           r'n_{s}=\left\lceil\frac{A_{cu}}{a_{s}}\right\rceil',
           key='astrand'))
    add(p('with A<sub>cu</sub> from Equation&nbsp;%s. The bundle is wider '
          'than its copper: gaps between round strands, enamel and serving '
          'are collected into a fill factor k<sub>litz</sub> of about 0.5 '
          'to 0.6, and the outside diameter is' % ER('window')))
    add(eq(r'd_{litz}=\sqrt{\frac{4A_{cu}}{\pi k_{litz}}}', key='litz'))
    add(p('<b>Foil.</b> Choose the thickness from the skin depth and what '
          'the supplier stocks; the width follows. If it exceeds the bobbin '
          'width, use several narrower strips in parallel, stacked '
          'radially:'))
    add(eq(r'w_{f}=\frac{A_{cu}}{t_{f}}\,,\qquad '
           r'n_{f}=\left\lceil\frac{w_{f}}{w_{f,max}}\right\rceil',
           key='foil'))

    add(h2('Safety insulation: what the winding has to carry'))
    add(p('The transformer is the isolation barrier, and a product sold in '
          'several markets needs one construction that passes all of them. '
          'Take every requirement at its strictest market: the insulation '
          'grade of a Class&nbsp;II set, <b>reinforced</b> between everything '
          'mains-referenced and the secondary (it covers Class&nbsp;I too); '
          'the highest altitude any market assumes, because clearances grow '
          'with it; and the working voltage at the top of the input range.'))
    ext(bullets([
        '<b>Clearance</b> follows the mains transient of overvoltage '
        'category&nbsp;II. Reinforced insulation is taken one withstand step '
        'higher, and above 2000&nbsp;m the result is multiplied by the '
        'altitude factor.',
        '<b>Creepage</b> follows the rms working voltage, the pollution '
        'degree and the material group of the surface; reinforced is twice '
        'basic. Without a tracking index for the bobbin, take the lowest '
        'group.',
        '<b>Solid insulation</b> &mdash; tape, bobbin wall, sleeving &mdash; '
        'needs either a minimum thickness or several layers that each pass '
        'the reinforced electric-strength test.',
        '<b>Between the sections, either the distance or the wire carries '
        'the reinforced insulation.</b> By distance, the gap between a '
        'primary and a secondary section is the creepage along the tube and '
        'the clearance across it, so it can be no narrower than the '
        'reinforced creepage. It is also the leakage, so the insulation then '
        'puts a floor under L<sub>short</sub>: check that floor with '
        'Equation&nbsp;%s before committing to it. By the wire, '
        'triple-insulated wire (made as Litz too) carries the reinforced '
        'insulation itself, and the gaps are free to be whatever the leakage '
        'asks.' % ER('leak'),
        '<b>The core counts as the side it cannot be kept away from.</b> '
        'With plain wire the primary fills the window almost to the outer '
        'legs, so the core is primary, and the secondary needs reinforced '
        'distances to it: through the tube wall, over the flange, to the '
        'outer legs and at the leads. With a triple-insulated primary the '
        'core is on the secondary&rsquo;s side, and what is left to check is '
        'where the insulation ends: the stripped wire ends at the primary '
        'pins, against the core and the secondary leads.',
        '<b>An auxiliary winding that feeds V<sub>CC</sub> and senses the '
        'output belongs over the secondary</b>, where it follows the output. '
        'It is mains-referenced, so there it must carry reinforced insulation '
        'itself; triple-insulated wire does that without tape.']))
    add(note('Where the windings are stacked instead, margin tape at both '
             'flanges buys the creepage and costs winding width. '
             'Triple-insulated wire needs no margin but is thicker for the '
             'same copper and costs more.'))

    add(h2('Loss, and the temperature the drawing has to survive'))
    ext(bullets([
        '<b>Core loss</b> comes off the material curve at the operating flux '
        'and frequency, not off the headline figure. The flux is fixed below '
        'resonance, so the worst loss is near f<sub>r</sub>, the top of the sweep below '
        'resonance; above it the flux falls as 1/f<sub>sw</sub>.',
        '<b>Copper loss</b> is I&sup2;R<sub>ac</sub> for both windings, and '
        'in a side-by-side arrangement the proximity term is not small.',
        '<b>Temperature rise</b> is what limits the design, and it depends '
        'on surface area and airflow. The computed loss is an input to a '
        'thermal measurement, not an answer.']))

    add(h2('The saturation test is not the peak winding current'))
    add(p('<b>What the line on the specification says.</b> A transformer '
          'specification usually carries a line of the form &ldquo;DC overlap: '
          'inductance more than 90&nbsp;% of initial, test current '
          'I<sub>sat</sub>, normal temperature&rdquo;. The name is the '
          'measurement. An LCR meter reads the primary inductance with a '
          'small ac signal (100&nbsp;kHz, 1&nbsp;V is a common setting, the '
          'same one the leakage test uses) while a bias source overlaps a '
          'dc current on the same winding; every other winding is open. The '
          'dc current is stepped up and the inductance is read at each '
          'step. The same test is called dc bias or dc superposition.'))
    add(fig('an_dc_overlap',
            'The DC-overlap test. Left: the bench. Right: inductance against '
            'the dc current, an illustrative shape, with this '
            'design&rsquo;s three currents marked: the operating magnetising '
            'peak, the test current the specification asks for, and the '
            'current that would have to be used if the controller had no '
            'voltage ceiling.'))
    add(p('<b>What it reveals.</b> With the other windings open the dc '
          'current alone sets the flux, so the inductance stays flat while '
          'the core is linear and falls as the core approaches saturation; '
          'the 90&nbsp;% point marks the knee. It is the only test at the '
          'terminals that reads the flux margin. Turns and A<sub>L</sub> do '
          'not: the same A<sub>L</sub> comes from a different gap, a '
          'different A<sub>min</sub> or a different material, and '
          'L<sub>open</sub> confirms the inductance, not the margin. A part '
          'with the right L<sub>open</sub> and the wrong core is caught here '
          'and nowhere else.'))
    add(p('<b>Which current to write on the line.</b> Mark <b>3</b> and the '
          'bench panel of Figure&nbsp;%(f)s. The current to ask for is the '
          'peak of the magnetising trace, scaled to the over-voltage '
          'ceiling, not the peak winding current at mark&nbsp;1.'
          % dict(f=FR('an_xfmr_read'))))
    add(p('In the test nothing cancels the primary ampere-turns, so the '
          'same current makes far more flux than in operation. Ask for the '
          'current that reproduces the operating flux in that test:'))
    add(eq(r'I_{eq}=\frac{B_{pk}\,N_{p}\,A_{e}}{L_{\mu}}', key='Isat'))
    add(note('<b>The denominator is L<sub>&mu;</sub>, not L<sub>open</sub></b>: '
             'the primary leakage links no core. Dividing by L<sub>open</sub> '
             'understates the current by a factor &radic;(1+&lambda;). A free '
             'check: '
             'the answer <b>must</b> equal i<sub>&mu;,pk</sub>.'))
    add(p('Testing at the peak tank current would ask for a flux the '
          'converter never produces. No arbitrary margin is wanted on '
          'I<sub>eq</sub> either: the flux '
          'ceiling is already defined by the highest output the controller '
          'allows before it shuts down.'))
    #  The derivation the user asked for (2026-09-25): why the saturation
    #  test current is tied to OVP2 and to nothing else.  Two expressions
    #  of the same flux; A_e cancels; the magnetising peak is proportional
    #  to the output voltage; the bench current obeys the same relation.
    add(p('<b>Why the ceiling is OVP2.</b> Write the same peak flux twice: '
          'from the volt-seconds the clamped secondary applies '
          '(Equation&nbsp;%(b)s), and from the current that magnetises the '
          'core (Equation&nbsp;%(i)s). A<sub>e</sub> cancels:'
          % dict(b=ER('Bpk'), i=ER('Isat'))))
    add(eq(r'B_{pk}=\frac{V_{o,eff}}{4\,f_{r}\,N_{s}\,A_{e}}'
           r'=\frac{L_{\mu}\,i_{\mu,pk}}{N_{p}\,A_{e}}'
           r'\qquad\Longrightarrow\qquad '
           r'i_{\mu,pk}=\frac{n_{T}\,V_{o,eff}}{4\,f_{r}\,L_{\mu}}',
           key='imuVo'))
    add(p('with n<sub>T</sub> = N<sub>p</sub>/N<sub>s</sub>. Nothing that '
          'the load or the input sets is left in it. Below resonance the '
          'secondary is clamped for T<sub>r</sub>/2 whatever f<sub>sw</sub> '
          'is; above resonance for less, so the flux is lower. '
          '<b>The magnetising peak, and the flux with it, is proportional to '
          'the output voltage and to nothing else in operation.</b> The '
          'worst case is therefore the highest output voltage at which the '
          'bridge is still switching.'))
    add(p('The L6790A has two levels on the ZCD pin. At OVP1 '
          '(2.3&nbsp;V on the pin) it keeps switching at reduced power, so '
          'the output can sit between OVP1 and OVP2 with the transformer '
          'still driven. At OVP2 (2.5&nbsp;V) it stops switching for '
          '100&nbsp;ms and restarts with a soft start. While the core is '
          'driven, the output therefore stays at or below V<sub>OVP2</sub>, '
          'and Equation&nbsp;%(m)s gives the largest magnetising peak the '
          'core ever carries.'
          % dict(m=ER('imuVo'))))
    add(p('On the bench every other winding is open, so the dc current is '
          'the only ampere-turns on the core and makes '
          'B&nbsp;=&nbsp;L<sub>&mu;</sub>&thinsp;I<sub>dc</sub>/'
          '(N<sub>p</sub>A<sub>e</sub>), the same relation as in operation. '
          'The test current that reproduces the flux at OVP2 is the '
          'magnetising peak scaled by the voltage ratio, and the ratio of the '
          'two voltages is the whole margin. No arbitrary factor goes on top '
          'of it:'))
    #  V_out, not V_o,eff, below: the exact ratio is (V_OVP2 + N V_f) /
    #  (V_out + N V_f), and only V_OVP2 / V_out sits above it, which is what
    #  the next paragraph says and what the design example substitutes.
    #  Printed with V_o,eff in round 61, it was the one ratio SMALLER than the
    #  exact one (round 62).
    add(eq(r'I_{sat}\;=\;I_{eq}\;\frac{V_{OVP2}}{V_{out}}',
           key='Isatspec'))
    add(p('With V<sub>f</sub> = 0 this is the exact flux ratio. With a '
          'rectifier drop the flux ratio is (V<sub>OVP2</sub> + '
          'N<sub>rect</sub>V<sub>f</sub>)/(V<sub>out</sub> + '
          'N<sub>rect</sub>V<sub>f</sub>), a little smaller, so '
          'Equation&nbsp;%s errs on the safe side.'
          % ER('Isatspec')))
    add(p('Overload, start-up, burst mode and the switching frequency do '
          'not raise the flux (Section&nbsp;%s); an output over-voltage '
          'does, and temperature lowers the ceiling. B<sub>s</sub> of a MnZn power '
          'ferrite falls by about a fifth between 25 and 100&nbsp;&deg;C, '
          'so a test made at normal temperature is read against the '
          'material&rsquo;s hot B<sub>s</sub>, and the design flux at OVP2 '
          'has to sit under it with margin. The 90&nbsp;%% criterion is '
          'that margin.' % SR('Not a flyback, and why that changes the core')))
    add(p('<b>If the controller has no OVP2-like ceiling.</b> Then '
          'something else has to bound the output voltage, and the '
          'specification follows whichever bound exists.'))
    ext(bullets([
        '<b>A protection that stops the drive</b>, on either side of the '
        'barrier: a secondary crowbar or latch, an SR-controller OVP, a '
        'primary OVP that latches. Use its threshold in place of '
        'V<sub>OVP2</sub>.',
        '<b>A protection that only reduces power</b>, like OVP1, is not a '
        'ceiling: the output can rest at it while the core is driven. Do '
        'not use it.',
        '<b>No voltage ceiling at all.</b> The output is then bounded only '
        'by what the tank can deliver at the oscillator floor into the '
        'lightest load, and with the floor near f<sub>o</sub> that bound '
        'is not useful. What remains is the current limit: with nothing '
        'clamping the secondary the primary current is the magnetising '
        'current, so the core must not saturate at the largest current the '
        'controller ever lets through the primary, '
        'I<sub>sat</sub>&nbsp;=&nbsp;I<sub>OCP1</sub>. Safe, and expensive; '
        'Section&nbsp;' + SR('Checking the flux, and the specification')
        + ' gives the ratio for this design.',
        '<b>The rule of thumb</b>, 1.2 to 1.5 times i<sub>&mu;,pk</sub> or '
        'the winding peak at normal temperature, is what a specification '
        'carries when nobody asked the question. It names no event, so it '
        'is neither safe nor economical. Replace it with one of the three '
        'above.']))

    add(h2('The specification, and what it is not allowed to leave out'))
    add(note('<b>Check the open-circuit inductance tolerance against the '
             'frequency floor.</b> f<sub>o</sub> goes as '
             '1/&radic;L<sub>open</sub>, so a low part raises f<sub>o</sub> '
             'towards the oscillator floor f<sub>Min</sub>; unless the floor '
             'margin covers the fall, a part that meets &plusmn;10&nbsp;%% '
             'can hard switch. Section&nbsp;' % {}
             + SR('Controller network') + ' gives the check.'))
    add(p('Core, bobbin, wire and winding order are the supplier&rsquo;s '
          'choice, inside the insulation of Section&nbsp;'
          + SR('Safety insulation: what the winding has to carry')
          + '. Everything above is measurable at the terminals.'))

    add(h2('If one transformer is not practical'))
    add(p('At low voltage and high current the secondary is one heavy turn '
          'and the core comes out large. The transformer can then be built '
          'as N<sub>x</sub> identical units with <b>primaries in series and '
          'secondaries in parallel</b>; series primaries carry the same '
          'current, so the secondaries share without balancing '
          'resistors.'))
    ext(bullets([
        'Open-circuit and leakage inductance divide by N<sub>x</sub>, and so '
        'do the secondary currents. <b>The primary current does not.</b>',
        'The DC-overlap test current does not change.',
        'The wound ratio becomes N<sub>x</sub>N<sub>p</sub>/N<sub>s</sub>, '
        'so <b>achievable ratios are quantised in steps of '
        'N<sub>x</sub>/N<sub>s</sub></b>. Respect that when the tank is '
        'chosen.']))

    add(h2('The input capacitor'))
    #  The floor and the ceiling were run together: "a large value
    #  distorts, so it is a THD term:" followed by a LOWER bound (round 63).
    add(p('C<sub>in</sub> is a film capacitor that absorbs switching ripple '
          'only. It has a floor, the ST rule of thumb that the evaluation '
          'board also follows:'))
    add(eq(r'C_{in}\;=\;3\,\frac{\mathrm{nF}}{\mathrm{W}}\times P_{in}', key='Cin'))
    add(p('That is a <b>lower</b> bound; round up to the next standard value '
          'and rate it for the full input voltage. Do not go far above it: a '
          'large value holds charge across the zero crossing and distorts '
          'the line current, so it is a THD term.'))

    add(h2('The output capacitor bank'))
    add(p('Two conditions apply, and the larger wins. The ripple condition '
          'is'))
    add(eq(r'C_{out}\;\geq\;\frac{P_{out}}'
           r'{2\pi f_{l,min}\,\Delta v\,V_{out}^{2}}', key='Crip'))
    add(p('and the hold-up condition is'))
    add(eq(r'C_{out}\;\geq\;\frac{2P_{out}T_{hold}}'
           r'{\left(V_{out}-\frac{1}{2}\Delta v_{pp}\right)^{2}'
           r'-V_{o,min}^{2}}', key='Chold'))
    add(note('<b>Hold-up starts at the worst line phase.</b> If the mains '
             'fails at the ripple trough the bank is already half a ripple '
             'down, hence the &minus;&frac12;&Delta;v<sub>pp</sub> term; it shortens '
             'the ride-out. &Delta;v<sub>pp</sub> is the ripple the '
             'bank produces, not the allowance, so this is checked once the '
             'bank is chosen.'))
    add(p('Both conditions scale as 1/V<sub>out</sub>&sup2;, so which wins '
          'depends only on the specification. With '
          'k&nbsp;=&nbsp;V<sub>o,min</sub>/V<sub>out</sub>, ripple dominates '
          'when'))
    add(eq(r'\left(1-\frac{\Delta v}{2}\right)^{2}-k^{2}'
           r'\;>\;4\pi f_{l}\,\Delta v\,T_{hold}', key='ripscreen'))
    add(p('using the <i>allowed</i> &Delta;v, since it is asked before the '
          'bank exists. Section&nbsp;%s evaluates it.'
          % SR('The output bank, as sized')))
    ext(bullets([
        'Include the <b>2f<sub>l</sub> component</b> in the ripple current; '
        'it is comparable to the switching part and adds in quadrature.',
        'With a centre-tapped secondary, judge capacitor ripple current at '
        'the <b>output node</b>, not per winding.',
        'Use the ESR at the frequency of each current component: the '
        '<b>switching-frequency</b> ESR for the switching part, the '
        '<b>120&nbsp;Hz</b> figure from tan&thinsp;&delta; for the '
        '2f<sub>l</sub> part. Here the two parts are of similar size.']))
    add(note('The controller start-up window is finite and this bank is a '
             'far heavier start-up load than a conventional design. Cold '
             'start into the full bank should be measured early.'))

    add(h2('Semiconductor requirements'))
    add(p('State requirements rather than pick parts. Four rules:'))
    ext(bullets([
        'Rate the primary switches on the <b>composite tank peak</b>; the '
        'load component alone under-rates them.',
        'Divide by the number of devices in parallel. Tabulated currents are '
        '<b>per switch position</b> on the primary and <b>per leg</b> on the '
        'secondary; a centre-tapped leg carries the whole secondary '
        'current.',
        'Compute loss from R<sub>DS(on)</sub> at <b>T<sub>j,max</sub></b>. '
        'The datasheet maximum is 25&nbsp;&deg;C process spread; temperature '
        'is a separate multiplier, about two for a superjunction device.',
        'A curve against T<sub>a</sub> may be read as T<sub>j</sub> '
        '<b>only if it is a pulse test</b>.']))
    add(note('The standing device in half-bridge morphing '
             '(Section&nbsp;' + SR('Half bridge') + ') never switches and '
             'carries the whole tank current; Section&nbsp;'
             + SR('Where the power goes') + ' shows what that cost here.'))

    add(h2('Controller network'))
    add(fig('bom_pin_config',
            'The controller and its passive network. HVSU is fed from the AC '
            'side of the bridge; the auxiliary winding drives ZCD through a '
            'divider; R<sub>T</sub> and C<sub>T</sub> set the oscillator '
            'limits; R<sub>CFG</sub> and R<sub>BM</sub> are read at power-up. '
            'The drawing feeds V<sub>CC</sub> from the auxiliary winding '
            'through a diode alone; the worked design puts a Zener-referenced '
            'regulator in between (Section&nbsp;%s). '
            'Drawing from the ST L6790A design spreadsheet.'
            % SR('V<sub>CC</sub> from the auxiliary winding, as built'),
            width=CW))
    add(p('Decide first what the auxiliary winding is for. Wired straight to '
          'V<sub>CC</sub>, its voltage at OVP2 must stay under the '
          'V<sub>CC</sub> rating, which caps its ratio. With a regulator in '
          'between the cap moves to the regulator output, and the ratio is '
          'set by two other things (Section&nbsp;'
          + SR('Supplying V<sub>CC</sub> from the auxiliary winding') + ').'))
    add(p('Section&nbsp;' + SR('The parts around the controller')
          + ' sizes the parts in order. R<sub>T</sub> deserves the most '
          'attention: it sets the oscillator floor, and that floor must stay '
          'above f<sub>o</sub>.'))
    add(note('<b>That floor is usually the thinnest margin.</b> It also '
             'depends on the oscillator idle time, which the draft datasheet '
             'states inconsistently, so it must be confirmed by measuring '
             'f<sub>sw</sub>(&theta;) on hardware.'))
    add(p('The transformer tolerance must fit inside the same margin. A '
          '<b>low</b> L<sub>open</sub> raises f<sub>o</sub>; the fall that '
          'can be tolerated is'))
    add(eq(r'\frac{\Delta L}{L}\;=\;1-\frac{1}{k_{floor}^{2}}', key='Ldrop'))
    add(p('with k<sub>floor</sub> = f<sub>Min</sub>/f<sub>o</sub> the floor '
          'margin. A floor margin of only a few per cent allows a fall of only a '
          'few per cent, and then the usual &plusmn;10&nbsp;%% does '
          '<b>not</b> fit: at the bottom of the tolerance f<sub>o</sub> rises '
          'above f<sub>Min</sub> and the bridge can hard switch near the zero '
          'crossing. Either tighten the low-side tolerance or lower '
          'R<sub>T</sub> to lift f<sub>Min</sub>; a higher floor widens the '
          'zero-crossing dead zone (Section&nbsp;%s). <b>Check before the '
          'transformer is ordered.</b>'
          % SR('Frequency modulation is the power factor correction')))

    add(h2('Supplying V<sub>CC</sub> from the auxiliary winding'))
    add(p('The winding charges a capacitor through a diode, and an NPN '
          'emitter follower whose base a Zener holds passes it on to the pin '
          'through the bypass diode the datasheet asks for, which keeps the '
          'start-up current out of the regulator. The pin then sits at '
          'V<sub>CC,reg</sub>, the Zener voltage V<sub>DZ</sub> less the '
          'base-emitter drop V<sub>BE</sub> and the diode drop V<sub>D</sub>:'))
    add(eq(r'V_{CC,reg}=V_{DZ}-V_{BE}-V_{D}', key='vccreg'))
    add(p('and the Zener tolerance puts it in a band. The bottom of the band '
          'is kept above V<sub>CC,HVSUon</sub>, the level below which the '
          'start-up unit turns its charge current on; the draft datasheet '
          'does not say whether it still does after its start-up timeout, '
          'and above that level the question never arises. The top must stay '
          'under the pin&rsquo;s operating limit. The load I<sub>VCC</sub> is '
          'the controller&rsquo;s own I<sub>CC</sub> and the gate drivers, '
          'whose share is the gate charge Q<sub>g</sub> of each of the '
          'N<sub>sw</sub> switch positions, once per period:'))
    add(eq(r'I_{VCC}=I_{CC}+N_{sw}\,Q_{g}\,f_{sw}', key='ivcc'))
    add(p('<b>The winding ratio has a floor and a cost.</b> At the end of '
          'hold-up, output V<sub>o,min</sub>, the winding must still lift the '
          'base above the highest Zener voltage V<sub>DZ,max</sub> with enough '
          'current left for the base, I<sub>VCC</sub>/&beta;<sub>min</sub>, '
          'and the Zener bias I<sub>Z,min</sub>; that caps the feed resistor '
          'R<sub>BZ</sub>,'))
    add(eq(r'R_{BZ}\leq\frac{n_{aux}V_{o,min}-V_{D}-V_{DZ,max}}'
           r'{I_{VCC}/\beta_{min}+I_{Z,min}}', key='rbz'))
    add(p('and at OVP1 the pass transistor burns the difference between the '
          'capacitor and the pin, times I<sub>VCC</sub>. The lowest '
          'whole-turn ratio that meets the floor therefore also minimises the '
          'cost.'))
    add(p('<b>Start-up is the other sizing case.</b> The start-up unit fills '
          'C<sub>VCC</sub> to V<sub>CCon</sub>; switching begins, and until the '
          'output is high enough for the winding to hold the pin, '
          'C<sub>VCC</sub> feeds the drivers: alone down to '
          'V<sub>CC,HVSUon</sub>, then helped by the start-up charge current '
          'I<sub>HVSU</sub> down to V<sub>CCoff</sub>. That has to last '
          't<sub>hand</sub>, until the output reaches V<sub>out,UV</sub>, '
          'the level at which the winding holds the pin at '
          'V<sub>CCoff</sub>. With the output bank charged at rated current '
          'and no load, and I<sub>VCC,SU</sub> the supply current at the '
          'start-up frequency,'))
    add(eq([r't_{hand}=\frac{C_{out}V_{out,UV}}{I_{out}}',
            r'C_{VCC}\geq\frac{t_{hand}}'
            r'{\dfrac{V_{CCon}-V_{CC,HVSUon}}{I_{VCC,SU}}'
            r'+\dfrac{V_{CC,HVSUon}-V_{CCoff}}{I_{VCC,SU}-I_{HVSU}}}'],
           key='cvcc'))
    add(p('A larger C<sub>VCC</sub> is paid for in the delay before the first '
          'pulse, C<sub>VCC</sub>V<sub>CCon</sub>/I<sub>HVSU</sub>.'))

    add(h2('Voltage loop and compensation'))
    add(p('The loop is the chain of Figure&nbsp;%(f)s: a divider measures '
          'the output, a TL431 compares it with its reference and drives an '
          'optocoupler LED, the optocoupler transistor pulls the FB pin, the '
          'FB voltage commands power (Section&nbsp;%(s)s), and that power '
          'goes into the output capacitor.'
          % dict(f=FR('an_loop_blocks'),
                 s=SR('The feedback pin is a power command'))))
    add(fig('an_loop_blocks',
            'The voltage loop as blocks. Everything left of the FB pin is '
            'the compensator G<sub>EA</sub>(s); everything right of it is '
            'the plant G<sub>plant</sub>(s). The loop gain is T(s) = '
            'G<sub>plant</sub>(s)&nbsp;G<sub>EA</sub>(s).'))
    add(p('<b>The plant.</b> The FB voltage sets the power, the power over '
          'the output voltage is the current into C<sub>out</sub>, and a '
          'current into a capacitor integrates. In small signal, with '
          'v<sub>out</sub> and v<sub>FB</sub> the changes of V<sub>out</sub> '
          'and V<sub>FB</sub>:'))
    add(eq(r'G_{plant}(s)=\frac{v_{out}(s)}{v_{FB}(s)}=\frac{G_{o}}{s},'
           r'\qquad G_{o}=\frac{P_{out}}{V_{out}\,V_{FB}\,C_{out}}'
           r'\quad[\mathrm{rad/s}]', key='Gplant'))
    add(p('V<sub>FB</sub> is the feedback voltage above its 0.5&nbsp;V '
          'offset at rated power (Equation&nbsp;%(e)s). An integrator falls '
          'at 20&nbsp;dB per decade with &minus;90&deg; everywhere and would '
          'cross 0&nbsp;dB at f<sub>cto</sub> = G<sub>o</sub>/2&pi;. There '
          'is no second pole and no right-half-plane zero, so the loop is '
          'easy to stabilise. What makes it hard to place is the output '
          'ripple (Section&nbsp;%(r)s).'
          % dict(e=ER('VFB'),
                 r=SR('Why the crossover must be low: the 2f<sub>l</sub> ripple'))))
    add(p('The integrator assumes a load that draws constant power as the '
          'output moves, which a downstream converter does. A resistive load '
          'R<sub>L</sub> draws less as the output falls, and in small signal '
          'the integrator becomes a pole at 1/(&pi;R<sub>L</sub>C<sub>out</sub>). '
          'Above that pole the plant is the same; below it the loop gain is '
          'lower, and at the crossover the phase is up to 90&deg; less '
          'negative, so the integrator is the worst case for phase margin.'))

    add(h2('What the loop must achieve, and what goes wrong when it does not'))
    add(p('Three numbers are read from the Bode plot of T(s): the '
          '<b>crossover</b> f<sub>c</sub> where |T| = 1, the <b>phase '
          'margin</b> 180&deg; + arg&nbsp;T at f<sub>c</sub>, and the '
          '<b>gain margin</b>, how far |T| is below 0&nbsp;dB at '
          'f<sub>180</sub> where arg&nbsp;T = &minus;180&deg;. '
          'Table&nbsp;%(t)s gives the aims.' % dict(t=TR('loop-aims'))))
    ext(tbl('What the loop must achieve.',
            [['Quantity', 'Aim', 'If it is too low', 'If it is too high'],
             ['Crossover f<sub>c</sub>',
              '15 to 20 Hz in this converter (Section&nbsp;%s). The general '
              'rules are below f<sub>sw</sub>/5 and below the ripple '
              'frequency the loop must not follow.'
              % SR('Why the crossover must be low: the 2f<sub>l</sub> ripple'),
              'The loop is slow. The output dips further and recovers '
              'later after a load step or a morphing transition.',
              'The loop follows the 2f<sub>l</sub> output ripple. The '
              'power command, and so the input current, is modulated at '
              '2f<sub>l</sub>: third harmonic on the input current, and '
              'chatter across the burst threshold.'],
             ['Phase margin &Phi;<sub>M</sub>',
              '45&deg; is the floor; 50 to 60&deg; is the target. At 76&deg; '
              'the step response has no overshoot; at 45&deg; it rings '
              '(Q &asymp; 1.2) [onsemi TND381].',
              'Ringing after every disturbance. At 0&deg; the loop '
              'oscillates at f<sub>c</sub>.',
              'The response is over-damped and slow. Not a fault, but no '
              'longer free: the crossover has to drop to get it.'],
             ['Gain margin GM',
              '6 dB is the floor; 10 dB is comfortable.',
              'Part spread moves |T| up. The optocoupler CTR alone spreads '
              'by 2:1 over bins, current and temperature; a loop with a '
              'small gain margin oscillates at f<sub>180</sub> on a warm '
              'board with a high-CTR part.',
              '&mdash;'],
             ['G<sub>EA</sub> at 2f<sub>l</sub>',
              'At or below the value that keeps the third harmonic inside '
              'its budget (Equation&nbsp;%s).' % ER('GEAreq'),
              'Nothing wrong with the loop; the crossover is lower than it '
              'needs to be.',
              'Third harmonic above budget, burst chatter.']],
            widths=[CW * 0.16, CW * 0.30, CW * 0.27, CW * 0.27],
            key='loop-aims', split=True))

    add(h2('Why the crossover must be low: the 2f<sub>l</sub> ripple'))
    add(p('The output ripple at 2f<sub>l</sub> (Section&nbsp;%(s)s) has the '
          'peak-to-peak value'
          % dict(s=SR('The energy a unity power factor cannot deliver'))))
    add(eq(r'\Delta V_{loop}=\frac{P_{out}}{V_{out}}\,\frac{1}{2\pi f_{l}\,C_{out}}',
           key='dVloop'))
    add(p('The compensator passes a fraction G<sub>EA</sub>(2f<sub>l</sub>) '
          'of it to the FB pin, which is a power command, so the input '
          'current is modulated at 2f<sub>l</sub>. A sine modulated at twice '
          'its own frequency gains a third harmonic; a modulation of the '
          'command by m puts m/2 into it, and the ripple amplitude is half '
          'the peak-to-peak, so'))
    add(eq(r'D_{3}=\frac{G_{EA}(2f_{l})\,\Delta V_{loop}}{4\,V_{FB}}',
           key='D3'))
    add(p('Turned around, the third-harmonic budget fixes the largest '
          'compensator gain at 2f<sub>l</sub>:'))
    add(eq(r'G_{EA}(2f_{l})\;\leq\;\frac{4\,V_{FB}\,D_{3}}{\Delta V_{loop}}',
           key='GEAreq'))
    add(p('A small gain at 2f<sub>l</sub> means a crossover well below it; '
          'with 5&nbsp;% third harmonic allowed, 15 to 20&nbsp;Hz. A faster '
          'loop would give less output ripple and a quicker load-step '
          'response, and more input distortion. The distortion limit wins. '
          'onsemi TND381 calls the failure &ldquo;tail chasing&rdquo;.'))

    add(h2('The compensator: TL431, optocoupler and the FB pin'))
    add(fig('comp_network_st',
            'The compensator on the secondary side. R<sub>I</sub> and '
            'R<sub>O</sub> set the regulated output; the TL431 is the error '
            'amplifier; R<sub>F</sub>, C<sub>F</sub> and C<sub>Fo</sub> '
            '(Rf, Cf, Cfo on the drawing) shape its gain; R<sub>B</sub> feeds '
            'the optocoupler LED from the regulated V<sub>Z</sub> rail; '
            'R<sub>P</sub> keeps the TL431 above its minimum current; '
            'C<sub>fx</sub> sits on the FB pin. Drawing from the ST L6790A '
            'design spreadsheet.'))
    add(p('The divider R<sub>I</sub>, R<sub>O</sub> brings the output down '
          'to the TL431 reference V<sub>R</sub>&nbsp;=&nbsp;2.495&nbsp;V:'))
    add(eq(r'V_{out}=V_{R}\left(1+\frac{R_{I}}{R_{O}}\right)', key='RoVout'))
    add(p('When the output rises the TL431 sinks more cathode current '
          'through the LED, which R<sub>B</sub> feeds from a regulated rail '
          'V<sub>Z</sub>; the optocoupler transistor pulls FB down against '
          'the internal pull-up R<sub>FB</sub> and the power command falls. '
          'R<sub>P</sub> across the LED carries the minimum cathode current '
          'the TL431 needs, so it has an upper limit:'))
    add(eq(r'R_{P}\leq\frac{V_{Fo}}{I_{min}}', key='RPmax'))
    add(p('with V<sub>Fo</sub> the LED forward voltage and I<sub>min</sub> '
          'the least cathode current the TL431 needs. Because the LED is fed from V<sub>Z</sub>, the output ripple '
          'reaches it only through the TL431: there is no second path '
          '(TND381&rsquo;s &ldquo;fast lane&rdquo;).'))
    add(p('<b>The same network as an op-amp.</b> Figure&nbsp;%(f)s redraws '
          'it. Inside the TL431 an amplifier compares REF with the internal '
          'V<sub>R</sub> and drives an NPN whose collector is the cathode; '
          'the transistor inverts, so from REF to cathode the part is a '
          'high-gain inverting amplifier that holds REF at V<sub>R</sub>. '
          'R<sub>I</sub> is its input resistor and C<sub>Fo</sub> in '
          'parallel with R<sub>F</sub> + C<sub>F</sub> its feedback '
          'impedance Z<sub>f</sub>, so the cathode moves by '
          '&minus;Z<sub>f</sub>/R<sub>I</sub> times the output change; '
          'R<sub>O</sub> sets only the dc point. The cathode current is the '
          'LED current, and the optocoupler transistor is a '
          'current-controlled current source sinking CTR&thinsp;'
          'i<sub>LED</sub> from the FB node into R<sub>FB</sub> with the '
          'pole of C<sub>opto</sub> + C<sub>fx</sub>. The three blocks '
          'multiply to a negative gain, which is the negative feedback. '
          'G<sub>EA</sub> is written without that sign: G<sub>EA</sub> = '
          '&minus;v<sub>FB</sub>/v<sub>out</sub>.'
          % dict(f=FR('an_comp_opamp'))))
    add(fig('an_comp_opamp',
            'The TL431 compensator as an op-amp circuit: R<sub>I</sub> and '
            'Z<sub>f</sub> make an inverting amplifier; R<sub>B</sub>, '
            'R<sub>P</sub> and the LED turn the cathode voltage into '
            'i<sub>LED</sub>; the optocoupler is a current source '
            'CTR&thinsp;i<sub>LED</sub> into R<sub>FB</sub> and '
            'C<sub>opto</sub> + C<sub>fx</sub>. The two sides return to '
            'different grounds across the isolation barrier.'))
    add(p('Its transfer function from output to FB pin is a Type&nbsp;II '
          'network with one more pole:'))
    add(eq(r'G_{EA}(s)=\frac{EA_{o}}{s}\cdot'
           r'\frac{1+s/\omega_{z}}{(1+s/\omega_{p})(1+s/\omega_{px})}',
           key='GEAtf'))
    add(eq([r'EA_{o}=\frac{CTR\;R_{FB}}{(C_{F}+C_{Fo})\,R_{I}\,R_{B}}\quad[\mathrm{rad/s}],'
            r'\qquad f_{z}=\frac{1}{2\pi R_{F}C_{F}}',
            r'f_{p}=\frac{1}{2\pi R_{F}C_{ser}},\quad C_{ser}=\frac{C_{F}C_{Fo}}{C_{F}+C_{Fo}},'
            r'\qquad f_{px}=\frac{1}{2\pi R_{FB}\,(C_{opto}+C_{fx})}'],
           key='fzp'))
    add(p('&omega; = 2&pi;f throughout, and C<sub>ser</sub> is C<sub>F</sub> '
          'and C<sub>Fo</sub> in series. C<sub>F</sub> + C<sub>Fo</sub> make '
          'the pole at the origin (zero static error); R<sub>F</sub>C<sub>F</sub> '
          'the zero f<sub>z</sub> that returns the phase; R<sub>F</sub> with '
          'C<sub>Fo</sub> the pole f<sub>p</sub> that brings the gain down '
          'again by 2f<sub>l</sub>; C<sub>opto</sub> + C<sub>fx</sub> with '
          'R<sub>FB</sub> a third pole f<sub>px</sub> at about a kilohertz that removes '
          'switching noise. CTR multiplies the whole gain, which is why its '
          'spread matters.'))
    add(p('<b>The bias window.</b> The LED must drive the FB pin at its '
          'steady-state current with the lowest CTR (upper bound), and must '
          'not exceed the pin&rsquo;s maximum current with the highest CTR '
          'when the TL431 is fully on (lower bound). I<sub>FB,steady</sub> '
          'and I<sub>FB,max</sub> are those two FB-pin currents:'))
    add(eq([r'R_{B,max}=\frac{V_{Z}-(V_{R}+V_{Fo})}'
            r'{V_{Fo}/R_{P}+I_{FB,steady}/CTR_{s}}',
            r'R_{B,min}=\frac{V_{Z}-(V_{R}+V_{Fo})}'
            r'{V_{Fo}/R_{P}+I_{FB,max}/CTR_{m}}'], key='RBwin'))
    add(note('EA<sub>o</sub> uses the CTR at the steady-state LED current, '
             'CTR<sub>s</sub>; the lower bound of R<sub>B</sub> uses the CTR '
             'at maximum LED current, CTR<sub>m</sub>. Take both from the '
             'bin that will be fitted, and re-check the loop at the top of '
             'the bin: the crossover rises almost in proportion to CTR, '
             'because the loop falls at close to 20&nbsp;dB per decade there, '
             'and the phase margin falls.'))

    add(h2('Placing the zero and the pole: the K-factor method'))
    add(p('The Venable K-factor method sets EA<sub>o</sub>, the zero and the '
          'pole from two targets: the phase margin &Phi;<sub>M</sub> and the '
          'gain allowed at 2f<sub>l</sub>. A spread factor K<sub>v</sub> '
          'comes from the phase margin, with &alpha;<sub>v</sub> a weighting '
          'constant (1.2 in the ST tool):'))
    add(eq(r'K_{v}=\frac{1}{2\alpha_{v}}\left[(1+\alpha_{v}^{2})\tan\Phi_{M}'
           r'+\sqrt{(1+\alpha_{v}^{2}\tan\Phi_{M})^{2}'
           r'+4\alpha_{v}^{2}}\;\right]', key='Kv'))
    add(p('The zero goes K<sub>v</sub> below the crossover and the pole '
          'K<sub>v</sub> above it. Above the pole the gain is '
          'EA<sub>o</sub>K<sub>v</sub>&sup2;/&omega;, so the limit at '
          '2f<sub>l</sub> fixes EA<sub>o</sub>:'))
    add(eq(r'EA_{o}=\frac{2\pi\,(2f_{l})\,G_{EA}(2f_{l})}{K_{v}^{2}}',
           key='EAotarget'))
    add(p('The centre point follows from the plant gain, with '
          '&Gamma;<sub>v</sub> = 0.744 V<sub>eq,max</sub>/V<sub>eq,min</sub> '
          'an input-voltage margin factor of the ST tool (Appendix&nbsp;%(a)s). '
          'The tool takes V<sub>eq,min</sub> as the lowest equivalent input '
          'and V<sub>eq,max</sub> as the mains maximum, not the highest '
          'equivalent input:'
          % dict(a=SR('Constants used here without a derivation'))))
    add(eq(r'f_{MB}=\frac{1}{2\pi}\sqrt{\frac{G_{o}K_{v}EA_{o}}{\Gamma_{v}}},'
           r'\qquad f_{p}=K_{v}f_{MB},\qquad f_{z}=\frac{f_{MB}}{K_{v}}', key='fMB'))
    add(p('The parts follow from Equation&nbsp;%(e)s. The high-frequency '
          'pole is placed at a chosen f<sub>pHF</sub>, and C<sub>fx</sub> is '
          'what is left after the optocoupler capacitance:'
          % dict(e=ER('fzp'))))
    add(eq([r'C_{Fo}=\frac{f_{z}}{f_{p}}\cdot\frac{CTR_{s}\,R_{FB}}{R_{I}R_{B}\,EA_{o}},'
            r'\qquad C_{F}=C_{Fo}\left(\frac{f_{p}}{f_{z}}-1\right)',
            r'R_{F}=\frac{1}{2\pi f_{z}C_{F}},'
            r'\qquad C_{fx}=\frac{1}{2\pi f_{pHF}\,R_{FB}}-C_{opto}'],
           key='Ccomp'))
    add(p('Round each value to a standard part, then compute the zero, pole '
          'and gain the standard parts give and check the loop on those.'))

    add(h2('Checking the loop: crossover, phase margin and gain margin'))
    add(p('The loop gain (Equations&nbsp;%(a)s and %(b)s) is two '
          'integrators, one zero and two poles:'
          % dict(a=ER('Gplant'), b=ER('GEAtf'))))
    add(eq([r'|T(\omega)|=\frac{G_{o}\,EA_{o}}{\omega^{2}}\cdot'
            r'\frac{\sqrt{1+(\omega/\omega_{z})^{2}}}'
            r'{\sqrt{1+(\omega/\omega_{p})^{2}}\;\sqrt{1+(\omega/\omega_{px})^{2}}}',
            r'\arg T(\omega)=-180^{\circ}+\arctan\frac{\omega}{\omega_{z}}'
            r'-\arctan\frac{\omega}{\omega_{p}}-\arctan\frac{\omega}{\omega_{px}}'],
           key='Tloop'))
    add(p('The &minus;180&deg; is the two integrators, so the <b>phase '
          'margin is the compensator phase at the crossover</b>. With '
          'A(&omega;) the fraction in Equation&nbsp;%(t)s, the crossover '
          'condition &omega;<sub>c</sub>&sup2; = '
          'G<sub>o</sub>EA<sub>o</sub>A(&omega;<sub>c</sub>) is solved by '
          'repeating' % dict(t=ER('Tloop'))))
    add(eq(r'\omega_{c}\leftarrow\sqrt{G_{o}\,EA_{o}\,A(\omega_{c})},'
           r'\qquad\mathrm{starting\ from}\ \ \omega_{c}=\sqrt{G_{o}\,EA_{o}}',
           key='wc'))
    add(p('a few times; each pass cuts the error by more than half, because '
          'the square root halves the change in A, so no solver is needed. '
          'Then'))
    add(eq(r'\Phi_{M}=\arctan\frac{\omega_{c}}{\omega_{z}}'
           r'-\arctan\frac{\omega_{c}}{\omega_{p}}'
           r'-\arctan\frac{\omega_{c}}{\omega_{px}}', key='PMeq'))
    add(p('Figure&nbsp;%(f)s shows where the three numbers are read, in '
          'units of the loop&rsquo;s own crossover, so it is the shape of '
          'every loop of this kind. Section&nbsp;%(s)s puts this '
          'design&rsquo;s numbers on the same plot.'
          % dict(f=FR('an_loop_example'), s=SR('The voltage loop, as built'))))
    add(fig('an_loop_example',
            'A two-integrator loop with a Type II compensator, in units of '
            'its crossover. Phase margin is the distance from '
            '&minus;180&deg; at f<sub>c</sub>; gain margin is |T| below '
            '0&nbsp;dB at f<sub>180</sub>. The dot at 2f<sub>l</sub> is the '
            'gain the third-harmonic check reads.'))

    add(h2('Gain margin, and why it needs checking'))
    add(p('Above f<sub>px</sub> one zero faces two poles, so the phase '
          'keeps falling and <b>&minus;180&deg; is crossed at a finite '
          'frequency</b>, which also needs no search:'))
    add(eq(r'f_{180}=\sqrt{\,f_{p}f_{px}-f_{z}(f_{p}+f_{px})\,}'
           r'\,,\qquad GM=-20\log_{10}|T(f_{180})|', key='f180'))
    add(p('The root is real whenever the zero sits well below both poles, '
          'which the K-factor placement gives; if its argument were '
          'negative the phase would sit below &minus;180&deg; at every '
          'frequency, and the phase margin would be negative at any '
          'crossover. Judge against '
          '6&nbsp;dB as a floor and 10&nbsp;dB as comfortable. With a '
          'crossover in the tens of hertz the margin is usually large; that '
          'is a reason to compute it, not to assume it.'))
    add(p('The same expression at 2f<sub>l</sub> gives the third harmonic '
          'through Equation&nbsp;%(d)s, which closes the check.'
          % dict(d=ER('D3'))))

    add(h2('Feedback ripple against the burst threshold'))
    add(p('A crossover this low leaves 2f<sub>l</sub> ripple on the FB pin, '
          'which moves the commanded power every half cycle. If it crosses '
          'the burst-entry threshold the converter chatters. At the burst '
          'point the ripple is'))
    add(eq(r'\Delta V_{FB}\;=\;\frac{P_{in,BM}}{V_{out}}\,'
           r'\frac{1}{2\pi f_{l}\,C_{out}}\;G_{EA}(2f_{l})', key='dVFB'))
    add(p('with P<sub>in,BM</sub> the input power at the burst entry point. '
          'Lowering R<sub>BM</sub> moves the burst entry below that ripple, '
          'at 0.01&nbsp;V per k&Omega;, and the ripple must clear it on both '
          'sides:'))
    add(eq(r'\Delta R_{BM}=\frac{\Delta V_{FB}}{2\times 0.01\ \mathrm{V/k\Omega}}',
           key='dRBM'))
    add(p('Raising the crossover would shrink the ripple but worsen the '
          'distortion, so R<sub>BM</sub> is the practical answer.'))
    add(note('A loop this slow cannot recover from a large load step by '
             'itself; the anti-saturation circuit does, and it needs the FB '
             'pin to reach its full current range. That is why R<sub>B</sub> '
             'must sit inside its window (Equation&nbsp;%(e)s).'
             % dict(e=ER('RBwin'))))

    # =============================================================== 6
    add(h1('Design example'))
    add(p('One design from specification to component values; every '
          'computed value shows its arithmetic. <b>90 to %(Vacmax).0f&nbsp;Vac '
          'in, %(Vout).0f&nbsp;V / %(Iout).1f&nbsp;A = %(Pout).1f&nbsp;W '
          'out</b>, centre-tapped synchronous rectification, no bulk '
          'capacitor, no boost stage.' % V))

    add(h2('The specification, sorted by what kind of number it is'))
    add(p('Each number is <b>given</b> by the load and the mains, '
          '<b>chosen</b> by the designer, or <b>assumed</b> in place of a '
          'measurement not yet made.'))
    ext(tbl('The specification. Everything else in this chapter is computed '
            'from these.',
            [['Item', 'Symbol', 'Value', 'Kind', 'Note'],
             ['Mains input', 'V<sub>ac</sub>, f<sub>l</sub>',
              '90 to %(Vacmax).0f Vac, %(flmin).0f to %(flmax).0f Hz' % V,
              'given',
              'the worst line frequency is the lowest, so every f<sub>l</sub> '
              'term uses %(flmin).0f Hz' % V],
             ['Output', 'V<sub>out</sub>, I<sub>out</sub>',
              '%(Vout).0f V, %(Iout).1f A  (%(Pout).1f W)' % V, 'given',
              'V<sub>o,eff</sub> = V<sub>out</sub> + N<sub>rect</sub>'
              'V<sub>f</sub> = %(Vout).1f V with V<sub>f</sub> = 0' % V],
             ['Output ripple, 2f<sub>l</sub> pk-pk', '&Delta;v',
              '&le; %(dv).0f %% of V<sub>out</sub> (%(dVpp).2f V)'
              % dict(V, dVpp=V['Vout'] * V['dv'] / 100), 'given',
              'a property of the load, not of the converter'],
             ['Hold-up', 'T<sub>hold</sub>, V<sub>o,min</sub>',
              '%(Thold).0f ms down to %(Vomin).0f V, at 100 Vac' % V, 'given',
              'starts at the ripple trough, the worst line phase'],
             ['Secondary rectifier', 'N<sub>rect</sub>', '1 (centre tap, SR)',
              'chosen',
              'halves the rectifier conduction loss; doubles the device '
              'reverse voltage'],
             ['Target series resonance', 'f<sub>r</sub>', '%(frt).0f kHz' % V,
              'chosen', 'sets the magnetics size'],
             ['Specified maximum f<sub>sw</sub>', 'f<sub>sw,max</sub>',
              '%(fswspec).0f kHz (%(fx).1f f<sub>r</sub>)' % dict(V, fx=V['fswspec'] / V['frt']), 'chosen',
              'an input to &lambda;, Section&nbsp;'
              + SR('f<sub>sw,max</sub> does not check the tank '
                   '&mdash; it computes it')],
             ['Bridge dead time', 't<sub>D</sub>', '%(tD).0f ns' % V, 'chosen',
              'what the ZVS sweep has to beat'],
             ['V<sub>CC</sub> source', '&mdash;',
              'auxiliary winding, %(Naux)d T, through a Zener regulator' % V,
              'chosen', 'no external rail; the regulator, not the turns '
              'ratio, keeps the pin under its rating'],
             ['LLC stage efficiency', '&eta;<sub>HB</sub>',
              '%(etaHB).0f %%' % V, 'assumed',
              'a 95 %% outcome moves R<sub>ac</sub> and R<sub>CS</sub> by '
              'about %.0f %%; nothing downstream is sensitive' % (100 * (V['etaHB'] / 95.0 - 1))],
             ['Oscillator idle time', 'T<sub>idle</sub>',
              '%(Tidle).0f ns' % V, 'assumed',
              'the draft datasheet also implies 350 and 700 ns; 700 ns would '
              'close the floor margin &mdash; the first thing to measure'],
             ['R<sub>DS(on)</sub> temperature factor', 'k<sub>T</sub>',
              '%(Rdpk).1f / %(Rdsk).1f' % V, 'assumed',
              'primary / secondary, read off the datasheet curves at '
              'T<sub>j,max</sub>'],
             ['Burst entry point', 'r<sub>BM</sub>',
              '%(rBM).0f %% of P<sub>in</sub> (%(PinBM).0f W)'
              % dict(V, rBM=A.SH['r.BM'] * 100), 'assumed',
              'sets R<sub>BM</sub>, then checked against the feedback '
              'ripple'],
             ['Primary MOSFET gate charge', 'Q<sub>g</sub>',
              '%(Qg).1f nC' % V, 'assumed',
              'the candidate part, typical, from a parameter listing; sets '
              'the V<sub>CC</sub> load (Section&nbsp;%s)'
              % SR('V<sub>CC</sub> from the auxiliary winding, as built')],
             ['Regulator parts', 'V<sub>BE</sub>, V<sub>D</sub>, '
              '&beta;<sub>min</sub>, I<sub>Z,min</sub>',
              '%(VFj).1f V, %(VFj).1f V, %(bmin).0f, %(IDZmin).0f mA' % V,
              'assumed', 'junction drops assumed; gain and bias are '
              'requirements put on the parts'],
             ['Safety conditions', '&mdash;',
              'US, EU, Japan, Korea, China; household AV; %d m'
              % _INS_ALT, 'given',
              'sets the transformer insulation (Section&nbsp;%s)'
              % SR('Safety insulation of this transformer')],
             ['Transformer construction', '&mdash;',
              'section winding on a custom coil former: NP1 in '
              'triple-insulated Litz in one section, the Litz secondary in '
              'the other, the sections touching, tape over every layer',
              'chosen', 'the insulation in the wire; the window shape sets '
              'L<sub>short</sub> (Section&nbsp;%s)'
              % SR('Choosing the core')],
             ['Winding figures', 'J, k<sub>litz</sub>, k<sub>w</sub>',
              '%.1f A/mm&sup2;, %.2f, %.2f; %.1f mm of triple insulation'
              % (_CORE.J_CU, _CORE.K_LITZ, _CORE.K_WIND,
                 _CORE.TIW_LITZ_ADD), 'assumed',
              'the copper and the diameters of the transformer; k<sub>w</sub> '
              'is the winding pitch over the bundle, from the first sample; '
              'the insulation thickness comes from the wire vendor']],
            widths=[CW * 0.20, CW * 0.12, CW * 0.21, CW * 0.11, CW * 0.36],
            key='spec-given', split=True))
    add(note('<b>Harmonic class.</b> IEC&nbsp;61000-3-2 Class&nbsp;D reaches '
             'only 600&nbsp;W. This design draws %(Pin).0f&nbsp;W at the '
             'input, so the absolute Class&nbsp;A limits apply.' % V))

    add(h2('What the design came out as'))
    ext(tbl('Principal values. The rest of the chapter shows where each one '
            'comes from.',
            [['Block', 'Values'],
             ['Tank', 'C<sub>r</sub> %(Cr).0f nF, L<sub>r</sub> %(Lr).0f '
              '&micro;H, L<sub>m</sub> %(Lm).0f &micro;H, '
              '&lambda; %(lam).2f, f<sub>r</sub> %(fr).1f kHz, '
              'f<sub>o</sub> %(fo).1f kHz' % V],
             ['Transformer', 'N<sub>p</sub>:N<sub>s</sub> '
              '%(NpSet)d:%(Ns)d, n %(n).2f, n<sub>T</sub> %(nT).2f, '
              'L<sub>open</sub> %(Lopen).1f &micro;H, '
              'L<sub>short</sub> %(Lshort).1f &micro;H, '
              'A<sub>e</sub> &ge; %(Aereq).0f mm&sup2; at '
              'B<sub>pk</sub> %(Bmx).2f T' % dict(V, Bmx=_CORE.B_MAX)],
             ['Frequency', 'f<sub>sw</sub> at the line peak, full load: %(fswA).1f kHz '
              'at the low corner, %(fswB).1f kHz at the high corner' % V],
             ['Output', '%(Cout1).0f &micro;F &times; %(nC).0f = '
              '%(Cout).1f mF, ripple %(dVo).2f V (%(dVopc).2f %%), '
              'hold-up %(thold).2f ms' % V],
             ['Controller', 'R<sub>T</sub> %(RT).0f k&Omega;, '
              'C<sub>T</sub> %(CT).0f pF, R<sub>CS</sub> %(RCS).1f m&Omega;, '
              'R<sub>CFG</sub> %(RCFG).0f k&Omega;, '
              'R<sub>BM</sub> %(RBM).0f k&Omega;' % V],
             ['Loop', 'f<sub>c</sub> %(fcross).2f Hz, '
              '&Phi;<sub>M</sub> %(PM).2f&deg;, '
              'third harmonic %(D3).2f %%' % V],
             ['V<sub>CC</sub>', 'N<sub>aux</sub> %d T, Zener %.0f V, '
              'R<sub>BZ</sub> %.0f &Omega;, C<sub>VCC</sub> %.0f &micro;F, '
              'V<sub>CC,reg</sub> %.2f V'
              % (V['Naux'], V['DZ'], V['RBZ'], V['CVCC'], A.SH['V.CC_reg'])],
             ['Insulation', 'reinforced, primary to secondary, carried by '
              'triple-insulated NP1 and NAUX; clearance %.1f mm and creepage '
              '%.1f mm at the pins, %d V ac for 60 s'
              % (_INS.req()['clearance'], _INS.req()['creep'],
                 _INS.req()['hipot_ac'])]],
            widths=[CW * 0.18, CW * 0.82], split=True))

    # ------------------------------------------------ what a margin ratio is
    add(h2('What a verification margin is'))
    add(p('Every check is what the design has divided by what it needs:'))
    add(eq(r'k\;=\;\frac{X_{\mathrm{act}}}{X_{\mathrm{req}}}\qquad\Longrightarrow\qquad \mathrm{pass\;when}\;k>1', key='margin'))
    add(p('k&nbsp;=&nbsp;1.05 is five per cent of room; the smallest k is '
          'the thinnest part of the design.'))
    _kb = V['kPloss'] * A.SH['P.mos_dc']          # the budget, recovered
    _ks = V['kPSR'] * A.SH['P.SR'] / 2.0
    ext(tbl('The verification margins.',
            [['Check', 'k = has / needs', 'Substituted', 'k'],
             ['ZVS at the worst point of the sweep',
              'T<sub>ZC,min</sub> / t<sub>D</sub>',
              '%(zTzc).0f ns / %(tD).0f ns' % dict(V, **ZVS_WORST),
              '%(zk).3f' % dict(V, **ZVS_WORST)],
             ['Oscillator floor clears the lower resonance',
              'f<sub>Min</sub> / f<sub>o</sub>',
              '%(fMin).2f kHz / %(fo).2f kHz' % V, '<b>%(kfloor).3f</b>' % V],
             ['Oscillator ceiling clears the highest operating frequency',
              'f<sub>Max</sub> / f<sub>sw</sub> (FB edge, line peak)',
              '%(fMax).2f kHz / %(fswmaxop).2f kHz' % V, '%(kceil).3f' % V],
             ['Over-current threshold clears the tank peak',
              'I<sub>OCP1</sub> / I<sub>Lr,pk</sub>',
              '%(I).2f A / %(Icomp).2f A' % dict(V, I=A.SH['I.OCP1']),
              '%(kOCP).3f' % V],
             ['Hold-up achieved against hold-up required',
              't<sub>hold</sub> / T<sub>hold</sub>',
              '%(thold).2f ms / %(Thold).0f ms' % V, '%(khold).3f' % V],
             ['Secondary loss per rectifier leg against its budget',
              'P<sub>budget</sub> / P<sub>SR,leg</sub>',
              '%(b).2f W / %(a).2f W' % dict(b=_ks, a=A.SH['P.SR'] / 2.0),
              '%(kPSR).3f' % V],
             ['Loss of the standing primary device against its budget',
              'P<sub>budget</sub> / P<sub>mos,dc</sub>',
              '%(b).2f W / %(a).2f W' % dict(b=_kb, a=A.SH['P.mos_dc']),
              '<b>%(kPloss).3f</b>' % V],
             ['V<sub>CC</sub> stays above the start-up threshold',
              'V<sub>CC,reg,min</sub> / V<sub>CC,HVSUon</sub>',
              '%.2f V / %.0f V' % (A.SH['V.CC_reg_min'], V['VCCHV']),
              '%.3f' % A.SH['k.VCClo']],
             ['The Zener feed still regulates at the end of hold-up',
              'R<sub>BZ,max</sub> / R<sub>BZ</sub>',
              '%.0f &Omega; / %.0f &Omega;' % (A.SH['R.BZ_max'], V['RBZ']),
              '<b>%.3f</b>' % A.SH['k.RBZ']],
             ['C<sub>VCC</sub> bridges the start-up hand-over',
              'C<sub>VCC</sub> / C<sub>VCC,req</sub>',
              '%.0f &micro;F / %.0f &micro;F' % (V['CVCC'], A.SH['C.VCC_req']),
              '%.3f' % A.SH['k.CVCC']]],
            widths=[CW * 0.34, CW * 0.18, CW * 0.26, CW * 0.10],
            key='margins', split=True))
    add(note('k<sub>Ploss</sub> = %(kPloss).3f is a result, not a failed '
             'calculation: the standing primary device spends %(a).2f&nbsp;W '
             'against a %(b).0f&nbsp;W budget; no single 600&nbsp;V device meets '
             'that budget in the standing position, so the design goes ahead '
             'and the heatsink question is settled by measurement '
             '(Section&nbsp;%(ref)s). k<sub>RBZ</sub> = %(krbz).3f is the '
             'thinnest that passes, but every input to it is already a worst '
             'case (the Zener at the top of its tolerance, the least current '
             'gain, the end of hold-up). k<sub>floor</sub> = %(kfloor).3f is '
             'the thinnest that rests on unknowns: the transformer tolerance '
             'and the idle time both move it, and neither is known to '
             '2&nbsp;%% yet.'
             % dict(V, a=A.SH['P.mos_dc'], b=_kb, krbz=A.SH['k.RBZ'],
                    ref=SR('What to measure first on hardware'))))

    # ------------------------------------------------ the chain, step by step
    add(h2('Following the numbers through'))
    add(p('The design in the order it was computed; each step shows its '
          'equation and the numbers in it. Table&nbsp;%s collects the '
          'results.' % TR('chain')))
    _SH = A.SH
    _rt = (1 + V['lam']) ** 0.5
    # -- power
    add(p('<b>Step 1 &mdash; the power the tank passes.</b> The bridge, the '
          'EMI filter and the LLC stage each get a loss budget, the last as '
          '&eta;<sub>HB</sub>:'))
    add(calc(r'P_{in}=P_{out}+P_{LLC}+P_{EMI}+P_{BR}'
             r'=%.1f+%.2f+%.2f+%.2f=\mathbf{%.1f\ W}'
             % (V['Pout'], _SH['P.d_LLC'], _SH['P.d_EMI'], _SH['P.d_BR'],
                V['Pin'])))
    add(calc(r'P_{in,LLC}=P_{in}-P_{BR}-P_{EMI}=%.1f-%.2f-%.2f'
             r'=\mathbf{%.1f\ W}'
             % (V['Pin'], _SH['P.d_BR'], _SH['P.d_EMI'], _SH['P.in_LLC'])))
    # -- corners
    add(p('<b>Step 2 &mdash; the two corners of the equivalent input.</b> '
          'They are the morphing thresholds, not the mains limits:'))
    add(eqagain('Veq'))
    add(calc(r'V_{ac,eq,low}=\frac{245\ \mathrm{V_{pk}}}{\sqrt{2}}'
             r'=\mathbf{%.1f\ V_{ac}}\qquad '
             r'V_{ac,eq,high}=\frac{2\times 235\ \mathrm{V_{pk}}}{\sqrt{2}}'
             r'=\mathbf{%.1f\ V_{ac}}' % (V['Veqlo'], V['Veqhi'])))
    # -- turns ratio
    add(p('<b>Step 3 &mdash; the turns ratio.</b> The wound ratio '
          '%(NpSet)d:%(Ns)d is the input, because it is what can '
          'be built (the plain calculation gives n = %(ncalc).3f); the model '
          'ratio follows from it and the realised &lambda; (step 8):'
          % dict(V, ncalc=_SH['n.calc'])))
    add(eqagain('nnT'))
    add(calc(r'n=\frac{n_{T}}{\sqrt{1+\lambda_{act}}}=\frac{%.3f}{%.4f}'
             r'=\mathbf{%.3f}' % (V['nT'], _rt, V['n'])))
    add(eqagain('Vrefl'))
    add(calc(r'V_{refl}=n\,V_{o,eff}=%.3f\times %.1f=\mathbf{%.1f\ V}'
             % (V['n'], V['Vout'], V['Vrefl'])))
    # -- gain demanded
    add(p('<b>Step 4 &mdash; the gain the tank is asked for</b>, at the line '
          'peak (&theta; = 90&deg;) of each corner: M<sub>low</sub> at the '
          'low corner, M<sub>high</sub> at the high one:'))
    add(eqagain('Mreq'))
    add(calc(r'M_{low}=\frac{2\times %.3f\times %.1f}{\sqrt{2}\times %.2f}'
             r'=\mathbf{%.4f}\qquad '
             r'M_{high}=\frac{2\times %.3f\times %.1f}{\sqrt{2}\times %.2f}'
             r'=\mathbf{%.4f}'
             % (V['n'], V['Vout'], V['Veqlo'], _SH['M.HBmin'],
                V['n'], V['Vout'], V['Veqhi'], _SH['M.FBthr'])))
    # -- load
    add(p('<b>Step 5 &mdash; the load the tank sees.</b> The 4, not the '
          'textbook 8, because P<sub>in,LLC</sub> is the line-peak power '
          '(Section&nbsp;%s):' % SR('The resonant tank')))
    add(eqagain('Rac'))
    add(calc(r'R_{ac}=\frac{4}{\pi^{2}}\,\frac{%.3f^{2}\times %.1f^{2}}{%.1f}'
             r'=\mathbf{%.2f\ \Omega}'
             % (V['n'], V['Vout'], _SH['P.in_LLC'], V['Rac'])))
    # -- Q cap and impedance
    add(p('<b>Step 6 &mdash; the Q cap and the design impedance.</b> At the '
          'low corner, the Q at which the tank still reaches M<sub>low</sub> '
          'and the Q at which ZVS still completes inside t<sub>D</sub>; the '
          'smaller is kept (Equation&nbsp;%s). The design impedance '
          'Z<sub>0,design</sub> follows from it:' % ER('Qdef')))
    add(calc(r'Q_{ZVS}=\mathbf{%.4f}\qquad '
             r'Z_{0,design}=R_{ac}\,Q_{ZVS}=%.2f\times %.4f'
             r'=\mathbf{%.2f\ \Omega}'
             % (V['QZVS'], V['Rac'], V['QZVS'], V['Z0'])))
    # -- Cr, Lr
    add(p('<b>Step 7 &mdash; C<sub>r</sub> and L<sub>r</sub>.</b> '
          'C<sub>r</sub> is taken <b>up</b> on purpose for Q margin; '
          'L<sub>r</sub> pairs with the <i>selected</i> C<sub>r</sub>:'))
    add(eqagain('fr'))
    add(calc(r'C_{r}=\frac{1}{2\pi f_{r}Z_{0,design}}'
             r'=\frac{1}{2\pi\times %.0f\ \mathrm{kHz}\times %.2f\ \Omega}'
             r'=%.2f\ \mathrm{nF}\ \rightarrow\ \mathbf{%.0f\ nF}'
             % (V['frt'], V['Z0'], V['Crc'], V['Cr'])))
    add(calc(r'L_{r}=\frac{1}{(2\pi f_{r})^{2}C_{r}}'
             r'=\frac{1}{(2\pi\times %.0f\ \mathrm{kHz})^{2}\times %.0f\ \mathrm{nF}}'
             r'=%.2f\ \mu\mathrm{H}\ \rightarrow\ \mathbf{%.0f\ \mu H}'
             % (V['frt'], V['Cr'], V['Lrc'], V['Lr'])))
    # -- lambda and Lm
    add(p('<b>Step 8 &mdash; &lambda; and L<sub>m</sub>.</b> Four candidates '
          'for &lambda;, the largest binding:'))
    add(eqagain('lam'))
    add(calc(r'\lambda_{1}=%.3f\,,\quad \lambda_{2}=%.3f\,,\quad '
             r'\lambda_{3}=%.3f\,,\quad '
             r'\lambda_{TD}=\mathbf{%.3f}\quad\Longrightarrow\quad '
             r'L_{m}=\frac{L_{r}}{\lambda_{TD}}=\frac{%.0f}{%.3f}'
             r'=%.2f\ \mu\mathrm{H}'
             % (_SH['λ.1'], _SH['λ.2'], _SH['λ.3'], _SH['λ.TD'], V['Lr'], _SH['λ.TD'],
                V['Lmc'])))
    add(p('That %(Lmc).1f&nbsp;&micro;H is the no-load condition at the high '
          'corner, which this design knowingly does not meet '
          '(Section&nbsp;%(ref)s), so it is not rounded to. L<sub>m</sub> is '
          'chosen with n so that n<sub>T</sub> is windable:'
          % dict(V, ref=SR('The other bound on &lambda;, and where it has '
                           'no solution'))))
    add(calc(r'L_{m}=\mathbf{%.0f\ \mu H}\qquad '
             r'\lambda_{act}=\frac{L_{r}}{L_{m}}=\frac{%.0f}{%.0f}'
             r'=\mathbf{%.3f}' % (V['Lm'], V['Lr'], V['Lm'], V['lam'])))
    # -- realised
    add(p('<b>Step 9 &mdash; what the selected parts make.</b> Every later '
          'check is measured against these:'))
    add(eqagain('fo'))
    add(calc(r'f_{r}=\frac{1}{2\pi\sqrt{%.0f\ \mu\mathrm{H}\times %.0f\ \mathrm{nF}}}'
             r'=\mathbf{%.1f\ kHz}\qquad '
             r'f_{o}=\frac{1}{2\pi\sqrt{%.0f\ \mu\mathrm{H}\times %.0f\ \mathrm{nF}}}'
             r'=\mathbf{%.1f\ kHz}'
             % (V['Lr'], V['Cr'], V['fr'], V['Lr'] + V['Lm'], V['Cr'], V['fo'])))
    add(calc(r'Z_{0}=\sqrt{\frac{%.0f\ \mu\mathrm{H}}{%.0f\ \mathrm{nF}}}'
             r'=%.2f\ \Omega\qquad '
             r'Q_{pk}=\frac{Z_{0}}{R_{ac}}=\frac{%.2f}{%.2f}=\mathbf{%.3f}'
             % (V['Lr'], V['Cr'], V['Z0s'], V['Z0s'], V['Rac'], V['Qpk'])))
    add(calc((r'n_{T}=n\sqrt{1+\lambda_{act}}=%.3f\times %.4f=\mathbf{%.3f}'
              % (V['n'], _rt, V['nT']))
             + (r'\ =\ %d:%d' % (V['NpSet'], V['Ns']) if V['nser'] == 1 else
                r'\ =\ %d:%d\ \mathrm{across\ the\ assembly},\ %d:%d\ \mathrm{per\ unit}'
                % (V['NpSet'], V['Ns'], V['Np'], V['Ns']))))
    ext(tbl('The design, step by step: the results of the nine steps. '
            'In a &rarr; b, a is the calculated value and b the part selected.',
            [['Step', 'Quantity', 'Eq.', 'Result'],
             ['1', 'P<sub>in</sub>, P<sub>in,LLC</sub>', '&mdash;',
              '%(Pin).1f W, %(PL).1f W' % dict(V, PL=_SH['P.in_LLC'])],
             ['2', 'V<sub>ac,eq</sub>, low and high corner', ER('Veq'),
              '%(Veqlo).1f, %(Veqhi).1f Vac' % V],
             ['3', 'n, V<sub>refl</sub>', ER('nnT') + ', ' + ER('Vrefl'),
              '%(n).3f, %(Vrefl).1f V' % V],
             ['4', 'M<sub>low</sub>, M<sub>high</sub>', ER('Mreq'),
              '%(a).4f, %(b).4f' % dict(a=_SH['M.HBmin'], b=_SH['M.FBthr'])],
             ['5', 'R<sub>ac</sub>', ER('Rac'), '%(Rac).2f &Omega;' % V],
             ['6', 'Q<sub>ZVS</sub>, Z<sub>0,design</sub>', ER('Qdef'),
              '%(QZVS).4f, %(Z0).2f &Omega;' % V],
             ['7', 'C<sub>r</sub>, L<sub>r</sub>', ER('fr'),
              '%(Crc).1f &rarr; %(Cr).0f nF, %(Lrc).2f &rarr; %(Lr).0f '
              '&micro;H' % V],
             ['8', '&lambda;<sub>req</sub>, L<sub>m</sub>, '
              '&lambda;<sub>act</sub>', ER('lam'),
              '%(lTD).3f, %(Lm).0f &micro;H, %(lam).3f'
              % dict(V, lTD=_SH['λ.TD'])],
             ['9', 'f<sub>r</sub>, f<sub>o</sub>, Q<sub>pk</sub>, '
              'n<sub>T</sub>', ER('fr') + ', ' + ER('fo') + ', ' + ER('Qdef'),
              '%(fr).1f kHz, %(fo).1f kHz, %(Qpk).3f, %(nT).3f' % V]],
            widths=[CW * 0.07, CW * 0.36, CW * 0.14, CW * 0.43],
            key='chain', split=True))
    add(note('<b>Steps 7 and 8 are the judgement calls.</b> C<sub>r</sub> is '
             '%(Cr).0f&nbsp;nF against a calculated %(Crc).1f: the larger '
             'capacitor lowers Q<sub>pk</sub>, which is where the ZVS margin '
             'comes from. L<sub>m</sub> is %(Lm).0f&nbsp;&micro;H against '
             '%(Lmc).1f: it lets the wound %(NpSet)d:%(Ns)d give the n the '
             'tank needs, and gives up the no-load solution (next note).'
             % V))
    if V['fnl'] is not None:
        add(note('<b>No-load solution.</b> The no-load gain of this tank '
                 'bottoms out at M<sub>&infin;</sub> = %(Minf).4f, and the '
                 'high corner asks for %(MFBmax).4f, so a frequency exists, '
                 'at about %(fnl).0f&nbsp;kHz (Section&nbsp;%(ref)s).'
                 % dict(V, ref=SR('The other bound on &lambda;, and where '
                                  'it has no solution'))))
    else:
        add(note('<b>No-load solution: none.</b> The no-load gain of this '
                 'tank bottoms out at M<sub>&infin;</sub> = %(Minf).4f, and '
                 'the high corner asks for %(MFBmax).4f, below it. No '
                 'frequency reaches that gain without load, and the margin '
                 'is under one per cent, so no full-load check would show '
                 'it. Burst mode owns that region (Section&nbsp;%(ref)s).'
                 % dict(V, ref=SR('The other bound on &lambda;, and where '
                                  'it has no solution'))))

    add(h2('ZVS over the whole operating space'))
    add(p('The closed form of Section&nbsp;' + SR('ZVS verification')
          + ' reads %(TzcCF).0f&nbsp;ns on this tank against a swept '
            '%(Tzc).0f&nbsp;ns (%(mag).0f&nbsp;%% pessimistic), and it also '
            'reads low, by tens of per cent, on the other tanks computed for '
            'this project. Being low there is no guarantee for another tank. '
            'Read with '
            '&lambda;<sub>act</sub> = %(lam).3f instead of the design '
            '&lambda; = %(lamreq).3f it returns %(TzcCFact)s&nbsp;ns, a '
            'capacitive answer for an inductive tank. This design is judged '
            'by the sweep.'
          % dict(V, mag=abs(V['TzcCFpc']), lamreq=A.SH['λ'],
                 TzcCFact=_minus(V['TzcCFact'], '%.0f'))))
    add(p('The capacitive edge of the full-load curve (arg Z<sub>in</sub> = '
          '0) is at %(fnEdge).1f&nbsp;kHz; the gain peak is lower, at '
          '%(fnPk).1f&nbsp;kHz, with %(phPk).1f&deg; of capacitive phase '
          'still there (Section&nbsp;%(ref)s). Neither is used for the '
          'verdict.'
          % dict(V, ref=SR('The two boundaries are not the same boundary'),
                 **_edge_numbers(A))))
    add(tbl('T<sub>ZC,min</sub> in nanoseconds, the smallest over the line '
            'half cycle, at each load and input voltage; FB is full bridge '
            '(the tank sees twice the mains), HB half bridge; '
            't<sub>D</sub>&nbsp;=&nbsp;%(tD).0f&nbsp;ns.' % V,
            ZVS_WORST['rows'], widths=[CW * 0.10] + [CW * 0.15] * 6,
            key='zvsgrid'))
    _z = dict(V, t=TR('zvsgrid'), **ZVS_WORST)
    if ZVS_WORST['same']:
        add(p('The worst point in Table&nbsp;%(t)s is full load at the HB '
              'edge, <b>T<sub>ZC</sub>&nbsp;=&nbsp;'
              '%(zTzc).0f&nbsp;ns against t<sub>D</sub>&nbsp;=&nbsp;'
              '%(tD).0f&nbsp;ns</b>, a margin of %(zk).2f times &mdash; the '
              'same corner the tank was designed at.' % _z))
    else:
        add(p('<b>The worst point is not the corner the tank was designed '
              'at.</b> Full load at the HB edge is where the '
              '<i>gain</i> requirement is set, and it gives '
              'T<sub>ZC</sub>&nbsp;=&nbsp;%(cTzc).0f&nbsp;ns, a margin of '
              '%(ck).2f. The smallest number in Table&nbsp;%(t)s is '
              '<b>%(zTzc).0f&nbsp;ns at %(zLoad).0f&nbsp;%% load, %(zAt)s</b>, '
              'a margin of '
              '%(zk).2f against t<sub>D</sub>&nbsp;=&nbsp;'
              '%(tD).0f&nbsp;ns. That is the number this design is held '
              'to.' % dict(_z, zAt=_where(ZVS_WORST['zVin'], A.R))))
        add(note('<b>Why light load at high input voltage can be the ZVS corner.</b> '
                 'The charge that swings the bridge node is carried by the '
                 'magnetising current, and above resonance, where this corner runs, '
                 'its peak goes as '
                 'n&thinsp;V<sub>o,eff</sub>/(4f<sub>sw</sub>L<sub>m</sub>). '
                 'Shed load '
                 'and the controller raises f<sub>sw</sub> to cut the gain, '
                 'so that current falls while the node still has the same '
                 'capacitance to move. Sweeping only the design corner '
                 'therefore reports a margin that is not there.'))

    add(h2('The gain chart of this design'))
    add(p('Figure&nbsp;%(f)s is the chart of Section&nbsp;%(s)s on this '
          'tank (&lambda;<sub>act</sub>&nbsp;=&nbsp;%(lam).3f, '
          'Q<sub>pk</sub>&nbsp;=&nbsp;%(Qpk).3f), one panel per input '
          'voltage: the two morphing edges and the four mains voltages a '
          'supply meets. Each panel names the mains voltage and the bridge; '
          'in full bridge the tank sees twice the mains, so each panel also '
          'says what the tank sees. The curves are the same in every panel; only the '
          'required-gain lines move. The marked crossings are the operating '
          'points the sweep is built from.'
          % dict(V, s=SR('Reading the gain chart of a single-stage '
                         'converter'), f=FR('an_gain_design'))))
    add(fig('an_gain_design',
            'The gain chart of this design at the six input voltages, low '
            'to high as the tank sees them. Top left, the HB edge '
            '(%(lo).0f&nbsp;Vac, half bridge): highest required gain, '
            'crossings below f<sub>r</sub>. Bottom right, the FB edge '
            '(%(fb).0f&nbsp;Vac, full bridge, so the tank sees '
            '%(hi).0f&nbsp;Vac): lowest required gain, crossings above '
            'f<sub>r</sub>. Each phase is compared with the dashed line of '
            'its own colour only.'
            % dict(lo=V['Veqlo'], hi=V['Veqhi'], fb=V['Veqhi'] / 2),
            width=CW))
    _gp = _GAIN.gain_points(A.R)
    import l6790 as _L
    _cn = {veq: nm for nm, veq, _m in _L.line_conditions(A.R)}
    _byv = [[g for g in _gp if abs(g[0] - veq) < 1e-6]
            for _nm, veq, _m in _L.line_conditions(A.R)]
    _lo = [g for g in _gp if abs(g[0] - A.R['Vin_min']) < 1e-6]
    _hi = [g for g in _gp if abs(g[0] - A.R['Vin_FBmax']) < 1e-6]
    ext(tbl('The marked crossings of Figure&nbsp;%(s)s, at every input '
            'voltage. Q&nbsp;=&nbsp;Q<sub>pk</sub>&thinsp;sin&sup2;&thinsp;'
            '&theta; and M<sub>req</sub>&nbsp;=&nbsp;M<sub>pk</sub>/sin&thinsp;'
            '&theta;; M<sub>pk</sub> scales as 1/V<sub>ac,eq</sub>, from '
            '%(a).3f at the HB edge to %(b).3f at the FB edge.'
            % dict(a=V['MVmin'], b=V['MFBmax'], s=FR('an_gain_design')),
            [['Input voltage', '&theta;', 'Q(&theta;)',
              'M<sub>req</sub>(&theta;)', 'f<sub>sw</sub>/f<sub>r</sub>',
              'f<sub>sw</sub>']]
            + [[_cn[v] if i == 0 else '',
                '%.0f&deg;' % (th * 180.0 / 3.141592653589793),
                '%.3f' % q, '%.3f' % mr,
                '&mdash;' if fn is None else '%.3f' % fn,
                '&mdash;' if fs is None else '%.1f kHz' % fs]
               for rows in _byv
               for i, (v, th, q, mr, fn, fs) in enumerate(rows)],
            widths=[CW * 0.26, CW * 0.09, CW * 0.13, CW * 0.18, CW * 0.17,
                    CW * 0.17],
            key='gainpts', split=True))
    add(p('Four readings matter:'))
    ext(bullets([
        '<b>The HB edge sets the tank.</b> %(lo).0f&nbsp;Vac in half bridge '
        'is the lowest voltage the tank ever sees, so its line-peak requirement '
        'M<sub>pk</sub>&nbsp;=&nbsp;%(m).3f is the largest of the six. It '
        'is met at f<sub>sw</sub>/f<sub>r</sub>&nbsp;=&nbsp;%(fn).3f, '
        'well to the right of M<sub>Z</sub>: inductive.'
        % dict(lo=V['Veqlo'], m=V['MVmin'], fn=_lo[0][4]),
        '<b>The FB edge sets the frequency.</b> At %(fb).0f&nbsp;Vac in full '
        'bridge the tank sees %(hi).0f&nbsp;Vac, the most it ever sees; the '
        'line-peak crossing is %(f).0f&nbsp;kHz, and that, '
        'not the mains maximum, is what the oscillator ceiling must clear '
        '(Section&nbsp;%(o)s).'
        % dict(hi=V['Veqhi'], fb=V['Veqhi'] / 2, f=_hi[0][5] or 0.0,
               o=SR('The oscillator: C<sub>T</sub> first, then '
                    'R<sub>T</sub>')),
        '<b>The four mains voltages sit between the edges.</b> 90&nbsp;Vac '
        'in full bridge puts 2 &times; 90 = 180&nbsp;Vac on the tank, only '
        '%(p90).0f&nbsp;%% above the HB edge, so a 90&nbsp;Vac system runs '
        'close to the gain worst case. 110&nbsp;Vac in full bridge '
        '(220&nbsp;Vac on the tank) and 230&nbsp;Vac in half bridge '
        '(230&nbsp;Vac on the tank) are within %(p23).0f&nbsp;%% of each '
        'other: morphing makes the two mains systems nearly alike to the '
        'tank. 264&nbsp;Vac in half bridge is still %(p264).0f&nbsp;%% below '
        'what the tank sees at the FB edge.'
        % dict(p90=100 * (180.0 / V['Veqlo'] - 1),
               p23=100 * (230.0 / 220.0 - 1),
               p264=100 * (1 - 264.0 / V['Veqhi'])),
        '<b>The FB edge also judges &lambda;.</b> The line-peak '
        'requirement there is %(mm).3f and the no-load floor '
        'M<sub>&infin;</sub>&nbsp;=&nbsp;%(mi).3f; below it there is no '
        'no-load solution and burst mode takes over (Section&nbsp;%(l)s).'
        % dict(mm=V['MFBmax'], mi=V['Minf'],
               l=SR('The other bound on &lambda;, and where it has no '
                    'solution'))]))
    add(note('The six panels are six places on one axis, not six designs. '
             'The curves do not depend on input voltage: '
             'M(f<sub>n</sub>,&nbsp;Q) is fixed by &lambda;<sub>act</sub> '
             'and Q<sub>pk</sub>. <b>The input voltage enters only through '
             'M<sub>req</sub>.</b>'))

    add(h2('Which side of resonance this design runs on'))
    add(p('With n<sub>T</sub> = %(nT).2f, at %(a)s of the %(b)s input '
          'voltages the tank spends part of every line cycle above '
          'f<sub>r</sub>, where the secondary loses zero-current turn-off, so '
          'the rectifier body diode and the SR dead time need checking.'
          % dict(V, a=_WORDS[V['nAbove']], b=_WORDS[len(V['fswPk'])])))
    add(fig('an_above_below',
            'Which side of f<sub>r</sub> the converter is on over a line '
            'half cycle, at the six input voltages. Every curve converges '
            'on f<sub>o</sub> at the zero crossing. The percentage in each '
            'legend entry is the fraction of the half cycle spent above '
            'f<sub>r</sub>, without zero-current turn-off.', width=CW))
    ext(tbl('Peak f<sub>sw</sub> over the half cycle against f<sub>r</sub> = '
            '%(fr).1f kHz. %(nAbove)d of the %(nc)d input voltages cross into '
            'above-resonance operation for part of the cycle.'
            % dict(V, nc=len(V['fswPk'])),
            [['Input voltage and bridge', 'the tank sees (Vac rms)',
              'peak f<sub>sw</sub>', 'side of f<sub>r</sub>']]
            + [[nm, '%.0f Vac' % veq, '%.1f kHz' % pk,
                '<b>above</b>' if ab else 'below']
               for nm, veq, pk, ab in V['fswPk']],
            widths=[CW * 0.36, CW * 0.16, CW * 0.20, CW * 0.28], split=True))
    add(fig('f12_two_divergences',
            'Near the zero crossing the required gain diverges and the load '
            'vanishes together, so the operating point converges on '
            'f<sub>o</sub> = %(fo).1f&nbsp;kHz (Section&nbsp;%(ref)s).'
            % dict(V, ref=SR('Two divergences that cancel'))))

    add(h2('The currents this design has to carry'))
    add(p('Ratings come from the worst switching cycle and losses from the '
          'line-cycle rms, so both are listed. The peaks are read off one '
          'cycle at the HB edge, line peak '
          '(&theta;&nbsp;=&nbsp;90&deg; in Table&nbsp;%(t)s). The composite '
          'peak is the peak of the sum, because the two components peak at '
          'different instants:'
          % dict(t=TR('gainpts'))))
    add(calc(r'I_{Lr,pk}=\max_{t}\left|i_{Lm}(t)+i_{trafo}(t)\right|'
             r'=%(Icomp).2f\;\mathrm{A}\;<\;'
             r'%(ILm).2f+%(Itr).2f=%(sum).2f\;\mathrm{A}'
             % dict(V, sum=V['ILm'] + V['Itr'])))
    add(p('The rms values are the rms of one switching period, averaged in '
          'I&sup2; over the line half cycle by the five-point Simpson rule:'))
    add(calc(r'I_{lc}=\sqrt{\frac{2}{\pi}\int_{0}^{\pi/2}'
             r'I_{rms}^{2}(\theta)\,d\theta}'
             r'\;\simeq\;\sqrt{\frac{1}{12}\sum_{k}w_{k}'
             r'I_{rms}^{2}(\theta_{k})}\,,\qquad '
             r'w=\{1,4,2,4,1\}'))
    add(p('That is why the line-cycle primary rms, %(Iprilc).2f&nbsp;A, is '
          'lower than the worst cycle&rsquo;s %(Iprims).2f&nbsp;A.' % V))
    add(fig('an_tank_current',
            'The composite tank current at the HB edge, full '
            'load, and why its peak is not the sum of the two component '
            'peaks: they occur at different instants. Drawn as the '
            'calculation models it: the reflected load current a half sine '
            'over the whole switching half period, the magnetising current '
            'a linear ramp.'))
    ext(tbl('Currents at the HB edge (%.0f&nbsp;Vac, half bridge), full load. '
            % V['Veqlo'] +
            'Peaks and worst-cycle rms are taken in the switching cycle at '
            'the line peak, &theta; = 90&deg;; line-cycle rms values are over '
            'the whole line half cycle.',
            [['Quantity', 'Value', 'Where it is used'],
             ['f<sub>sw</sub>', '%(fswA).1f kHz' % V,
              'the switching cycle the peaks below are read in'],
             ['I<sub>sec,pk</sub>', '%(Isec).1f A' % V,
              'secondary rectifier peak'],
             ['I<sub>trafo,pk</sub>', '%(Itr).2f A' % V,
              'reflected load component'],
             ['I<sub>Lm,pk</sub>', '%(ILm).2f A' % V,
              'magnetising component'],
             ['<b>composite tank peak</b>', '<b>%(Icomp).2f A</b>' % V,
              '<b>primary device rating, OCP margin</b>'],
             ['I<sub>pri,rms</sub> (worst cycle)', '%(Iprims).2f A' % V,
              'primary rms rating'],
             ['I<sub>pri</sub> (line-cycle rms)', '%(Iprilc).2f A' % V,
              'primary conduction loss'],
             ['I<sub>rect</sub> per leg (line-cycle rms)',
              '%(Idio).2f A' % V, 'secondary conduction loss'],
             ['I<sub>Cout</sub> (line-cycle rms)', '%(ICout).2f A' % V,
              'output bank ripple current']],
            widths=[CW * 0.36, CW * 0.20, CW * 0.44], key='currents',
            split=True))

    add(h2('What the transformer must provide'))
    add(p('The tank asks for L<sub>r</sub> = %(Lr).0f&nbsp;&micro;H, '
          'L<sub>m</sub> = %(Lm).0f&nbsp;&micro;H and n<sub>T</sub> = '
          '%(nT).2f. The transformer is one part: a %(Np)d-turn primary and '
          'two %(Ns)d-turn secondaries, NS2 and NS3, joined at the centre '
          'tap. NS2 is N<sub>s1</sub> of Figure&nbsp;%(f1)s and NS3 is '
          'N<sub>s2</sub>, so NS3 conducts while S1 and S4 are on. Several units in series (Section&nbsp;%(ref2)s) are not '
          'needed here.'
          % dict(V, ref2=SR('If one transformer is not practical'),
                 f1=FR('an_llc_stage'))))
    add(fig('an_xfmr_read',
            'Where each number is read. Top: primary current, the two '
            'secondary winding currents and the secondary winding voltage '
            'over one switching period at the worst cycle: line peak at '
            'the HB edge (%(Veqlo).0f&nbsp;Vac, half bridge), full load. '
            'Lower left and centre: the rms of the two winding currents '
            'over the input half cycle at the six input voltages; the HB '
            'edge draws the most in both windings, which is why the table '
            'is read there. Lower right: the DC-overlap bench test. The '
            'circled marks are the rows of Table&nbsp;%(t)s.'
            % dict(V, t=TR('xfmr-read'))))
    ext(tbl('What the tank asks of the transformer.',
            [['Quantity', 'Value', 'Note'],
             ['Turns', 'N<sub>p</sub> %(Np)d T; NS2 %(Ns)d T, NS3 %(Ns)d T; '
              'NAUX %(Naux)d T' % V,
              'n<sub>T</sub> = %(Np)d / %(Ns)d = %(nT).1f; the auxiliary '
              'feeds V<sub>CC</sub> and ZCD' % V],
             ['Open-circuit inductance', '%(Lopen).1f &micro;H' % V,
              'L<sub>r</sub> + L<sub>m</sub>; across NP1, every other winding '
              'open'],
             ['Short-circuit inductance', '%(Lshort).1f &micro;H' % V,
              'this is L<sub>r</sub>, no separate resonant inductor; across NP1, '
              'NS2 and NS3 shorted, NAUX open'],
             ['A<sub>L</sub>', '%(AL).0f nH' % V,
              'open-circuit inductance / N<sub>p</sub>&sup2;; the core is '
              'gapped to it (Section&nbsp;%s)' % SR('Choosing the core')]],
            widths=[CW * 0.24, CW * 0.30, CW * 0.46],
            key='trafo-built', split=True))

    # ------------------------------------------------ the core, from the numbers
    #  The requirements come first and the core is checked against them; the
    #  section used to open on the chosen core and the pin drawing, so the
    #  choice read as made before the arithmetic (2026-09-25, user).
    add(h2('Choosing the core'))
    _w = _CORE.winding(V)
    _R = _CORE.CORES[_CORE.CHOSEN]
    _cw = _CORE.window(V) / _CORE.K_U
    add(p('Three requirements come before any core is picked: the flux sets '
          'the core area, the copper sets the window, and the leakage sets '
          'the winding width.'))
    add(p('<b>Core area.</b> The flux at f<sub>r</sub>, with B<sub>pk</sub> '
          'held to %.2f&nbsp;T:' % _CORE.B_MAX))
    add(eqagain('Bpk'))
    add(calc(r'A_{e}\geq\frac{%.1f\ \mathrm{V}}{4\times %.2f\ \mathrm{kHz}\times %d'
             r'\times %.2f\ \mathrm{T}}=\mathbf{%.0f\ mm^{2}}'
             % (V['Vout'], V['fr'], V['Ns'], _CORE.B_MAX, V['Aereq'])))
    add(p('<b>Copper.</b> Each winding carries its line-cycle rms current '
          '(Table&nbsp;%(t)s) at J&nbsp;=&nbsp;%(j).1f&nbsp;A/mm&sup2;. '
          'Summed over the windings, that is the copper the window must '
          'hold:'
          % dict(t=TR('currents'), j=_CORE.J_CU)))
    add(eqagain('window'))
    _cp, _cs = _CORE.copper(V)[0], _CORE.copper(V)[1]
    add(calc([r'\mathrm{NP1:}\ A_{cu}=\frac{%.2f\ \mathrm{A}}{%.1f\ \mathrm{A/mm^{2}}}'
              r'=%.2f\;\mathrm{mm^{2}}\,,\qquad '
              r'\mathrm{NS2:}\ A_{cu}=\frac{%.2f\ \mathrm{A}}{%.1f\ \mathrm{A/mm^{2}}}'
              r'=%.2f\;\mathrm{mm^{2}}'
              % (_cp[2], _CORE.J_CU, _cp[3], _cs[2], _CORE.J_CU, _cs[3]),
              r'\sum_{w} N_{w}A_{cu,w}=%d\times %.2f+%d\times %.2f'
              r'=%.1f\;\mathrm{mm^{2}}\;\leq\;%.2f\,A_{N}'
              r'\;\Rightarrow\;A_{N}\geq\mathbf{%.0f\ mm^{2}}'
              % (V['Np'], _cp[3], 2 * V['Ns'], _cs[3], _CORE.window(V),
                 _CORE.K_U, _CORE.window(V) / _CORE.K_U)]))
    add(p('The conductor for each follows from the skin depth.'))
    _rows = _CORE.copper(V)
    _rp, _rs = _rows[0], _rows[1]
    add(p('<b>Skin depth</b> at f<sub>r</sub>, with copper at '
          '100&nbsp;&deg;C (&rho;&nbsp;=&nbsp;2.26&nbsp;&times;'
          '&thinsp;10<sup>&minus;8</sup>&nbsp;&Omega;m):'))
    add(eqagain('skin'))
    add(calc(r'\delta=\sqrt{\frac{2.26\times10^{-8}}'
             r'{\pi\cdot%(fr).1f\times10^{3}\cdot4\pi\times10^{-7}}}'
             r'=%(d).3f\;\mathrm{mm}'
             % dict(fr=V['fr'], d=V['delta'])))
    add(p('A conductor thicker than 2&delta;&nbsp;=&nbsp;%(d2).2f&nbsp;mm '
          'gains little, so <b>both windings are Litz</b>. The standard '
          'strand safely inside that is <b>d<sub>s</sub> = '
          '&oslash;%(ds).2f&nbsp;mm</b>, %(rat).1f times smaller than '
          '2&delta;. For the primary, its copper area and the strand count '
          'are Equation&nbsp;%(e)s:'
          % dict(d2=2 * V['delta'], ds=_CORE.D_STRAND,
                 rat=2 * V['delta'] / _CORE.D_STRAND, e=ER('astrand'))))
    add(eqagain('astrand'))
    _asn = 3.141592653589793 * _CORE.D_STRAND ** 2 / 4
    _np1 = int(_rp[3] / _asn + 0.9999)
    _ns1 = int(_rs[3] / _asn + 0.9999)
    _dp1 = _CORE.litz(_rp[3])[0]
    _ds1 = _CORE.litz(_rs[3])[0]
    add(calc(r'a_{s}=\frac{\pi\cdot(%(ds).2f)^{2}}{4}'
             r'=%(a).5f\;\mathrm{mm^{2}}\,,\qquad '
             r'n_{s}=\left\lceil\frac{%(ap).2f}{%(a).5f}\right\rceil'
             r'=%(n)d'
             % dict(ds=_CORE.D_STRAND, ap=_rp[3], n=_np1, a=_asn)))
    add(p('As one served bundle, with '
          'k<sub>litz</sub>&nbsp;=&nbsp;%(kl).2f, that would be:'
          % dict(kl=_CORE.K_LITZ)))
    add(eqagain('litz'))
    add(calc(r'd_{litz}=\sqrt{\frac{4\cdot%(ap).2f}{\pi\cdot%(kl).2f}}'
             r'=%(dl).2f\;\mathrm{mm}'
             % dict(ap=_rp[3], kl=_CORE.K_LITZ, dl=_dp1)))
    add(p('<b>The secondary is Litz too.</b> Between the two sections of '
          'the winding chosen below the field crosses the secondary '
          '(Section&nbsp;%(ref)s), and foil would carry eddy currents across '
          'its width. One turn of NS2 or NS3 needs %(a).2f&nbsp;mm&sup2;:'
          % dict(ref=SR('Skin depth, and why the wire is not a wire'),
                 a=_rs[3])))
    add(calc(r'n_{s}=\left\lceil\frac{%(a2).2f}{%(a).5f}\right\rceil=%(n)d'
             r'\,,\qquad d_{litz}=\sqrt{\frac{4\cdot%(a2).2f}{\pi\cdot'
             r'%(kl).2f}}=%(d).2f\;\mathrm{mm}'
             % dict(a2=_rs[3], a=_asn, n=_ns1, kl=_CORE.K_LITZ, d=_ds1)))
    add(p('A secondary bundle of &oslash;%(d2).1f&nbsp;mm is too stiff to '
          'lay flat in a layer by hand, so <b>each turn of NS2 and NS3 is '
          '%(sp)d thinner bundles side by side</b>; NP1 stays one '
          'triple-insulated Litz bundle. Their size comes from the window, '
          'below.'
          % dict(d2=_ds1, sp=_w['sec_par'])))

    #  the arrangement, from the leakage (leakage.py)
    import leakage as _LK
    import insulation as _INS
    from math import pi as _pi
    _M, _mm = _w['M'], 1e-3
    _hw = _M['r_win_out'] - _M['d_centre'] / 2.0
    _sep = _INS.separation_min()
    _wsb = (-(-V['Np'] // 3)) * _dp1             # plain Litz, 3 layers
    _L1 = _LK.one_d(V['Np'], 0, _wsb * _mm, _w['w_S'] * _mm, 0.0, _sep * _mm,
                    0.0, _hw * _mm, _R['lN'] * _mm) * 1e6
    _L2 = _LK.one_d_of(V) * 1e6
    _ef = _LK.estimate(V)
    _et = _LK.estimate(V, k=1.0)['L']
    _g01 = _LK.estimate(V, g=0.1)['L']
    _ords = _LK.orders(V)
    _h2, _h3 = _ords[_w['order']]
    _o22 = _ords[('NS2', 'NS2', 'NS3', 'NS3')]
    _o33 = _ords[('NS2', 'NS3', 'NS3', 'NS2')]
    _hmax = max(_h2, _h3)
    _Lmax = V['Lshort'] * 1.10
    _wt = _CORE.winding(V, k=1.0)
    _sh = _LK.sharing(V)
    _pa = _LK.proximity(V, V['fswA'])
    _pb = _LK.proximity(V, V['fr'])
    _pdc = _LK.dc_loss(V)
    #  what the current around the parallel bundles adds: it runs out along
    #  one outer bundle and back along the other, in both windings, all the
    #  time the field is there (first order, like the current itself)
    _asn_m = _pi * (_CORE.D_STRAND * 1e-3) ** 2 / 4.0
    _rb = 2.26e-8 * V['Ns'] * _R['lN'] * 1e-3 / (_w['n_strand_s'] * _asn_m)
    _pcirc = 2 * 2 * _sh['turned'] ** 2 * _rb
    _psdc = 2 * V['Idio'] ** 2 * _rb / _w['sec_par']
    _gl, _gin = _CORE.gap_len(V)
    _wall = (_M['tube_od'] - _M['d_centre']) / 2.0
    _mid = _w['wind_w'] / 2.0                    # the gap, from the NP1 flange
    _under = _w['yA'][1] - (_mid - _gl / 2.0)
    add(p('<b>The arrangement.</b> L<sub>short</sub> must come out at '
          '%(Ls).1f&nbsp;&micro;H. Side by side, with the gap as the '
          'reinforced insulation, the gap is at least the %(sep).1f&nbsp;mm '
          'creepage (Section&nbsp;%(ins)s). On the window chosen below '
          '(depth h<sub>w</sub> = %(hw).2f&nbsp;mm, mean turn '
          'l<sub>N</sub> = %(ln).0f&nbsp;mm), Equation&nbsp;%(e)s with '
          'N<sub>B</sub>&nbsp;=&nbsp;0, the primary as one plain Litz bundle '
          'in three layers (w<sub>A</sub> = %(wa).2f&nbsp;mm) and the '
          'secondary group (w<sub>S</sub> = %(ws).2f&nbsp;mm) gives'
          % dict(Ls=V['Lshort'], sep=_sep, e=ER('leak'), wa=_wsb,
                 ws=_w['w_S'], hw=_hw, ln=_R['lN'],
                 ins=SR('Safety insulation of this transformer'))))
    add(calc(r'L_{short}\approx\frac{4\pi\times10^{-7}\times %(ln).0f\ '
             r'\mathrm{mm}}{%(hw).2f\ \mathrm{mm}}\times %(np)d^{2}\left('
             r'\frac{%(wa).2f}{3}+%(g).1f+\frac{%(ws).2f}{3}\right)\ \mathrm{mm}'
             r'=\mathbf{%(L).0f\ \mu H}'
             % dict(ln=_R['lN'], hw=_hw, np=V['Np'], wa=_wsb, g=_sep,
                    ws=_w['w_S'], L=_L1)))
    add(p('That is %(r).1f times the target. So <b>the insulation goes into '
          'the wire</b>: NP1 is triple-insulated Litz and NAUX is '
          'triple-insulated wire. The winding is then the <b>section '
          'winding</b> of the usual LLC reference transformer: NP1 in one '
          'section, the secondary group in the other, <b>the two sections '
          'touching</b>, and a wrap of tape over every layer.'
          % dict(r=_L1 / V['Lshort'])))
    add(p('<b>The window this winding needs.</b> When each section fills '
          'the window depth, its width is its copper area over the depth, '
          'so Equation&nbsp;%(e)s goes as l<sub>N</sub> times the copper '
          'area over h<sub>w</sub>&sup2;: the leakage of a filled section '
          'winding is set by the SHAPE of the window. It has to be deep and '
          'short, on a centre leg no thicker than the flux asks. The '
          'E&nbsp;60/22/16 window, %(hw).1f&nbsp;mm deep and '
          '%(wh).1f&nbsp;mm high, takes it near L<sub>r</sub> with both '
          'sections filling the depth and the flux well inside its limit.'
          % dict(e=ER('leak'), hw=_hw, wh=_M['win_h'])))
    add(p('<b>The build.</b> Both sections fill the radial room, '
          'h<sub>r</sub> = %(hr).2f&nbsp;mm between the tube and the outer '
          'legs at their tolerance limits. A real winding is not packed '
          'tight: bundles in a layer, and layers on each other, sit a little '
          'apart. The build is therefore laid out at a pitch of '
          'k<sub>w</sub>&nbsp;=&nbsp;%(k).2f times the bundle diameter, '
          'along the layer and from layer to layer, with a %(t).2f&nbsp;mm '
          'wrap of tape over every layer. k<sub>w</sub> is an assumption '
          'that the first sample&rsquo;s measured build replaces; a winding '
          'tighter than that leaves the difference to the margin tape and a '
          'finishing wrap. NP1, one bundle in %(lp)d layers of %(per)d turns '
          '(the last layer %(last)d, spread over the width), and NS2 and '
          'NS3, %(ls)d layers of one turn of %(sp)d bundles under NAUX '
          '(&oslash;%(tiw).1f&nbsp;mm TIW) and its tape, give the bundle '
          'diameters d<sub>b,p</sub> and d<sub>b,s</sub> and the current '
          'densities J<sub>p</sub> and J<sub>s</sub> they run at:'
          % dict(hr=_w['r_free'], k=_w['k_wind'], t=_w['t_tape'],
                 lp=_w['layers_A'], per=_w['per_A'], last=_w['rows_A'][-1],
                 ls=_w['sec_layers'], sp=_w['sec_par'],
                 tiw=_w['tiw_od'])))
    add(calc([r'd_{b,p}=\frac{%(hr).2f/%(lp)d-%(t).2f}{%(k).2f}=%(dp).2f\;'
              r'\mathrm{mm}\ \ (\mathrm{bundle}\ %(dl).2f+%(ta).1f\ '
              r'\mathrm{TIW})'
              % dict(hr=_w['r_free'], lp=_w['layers_A'], t=_w['t_tape'],
                     k=_w['k_wind'], dp=_w['d_pri'], dl=_w['d_litz'],
                     ta=_w['tiw_add']),
              r'd_{b,s}=\frac{(%(hr).2f-%(tk).2f)/%(ls)d-%(t).2f}'
              r'{%(k).2f}=%(ds).2f\;\mathrm{mm}'
              % dict(hr=_w['r_free'], t=_w['t_tape'], k=_w['k_wind'],
                     ls=_w['sec_layers'], ds=_w['d_sec'],
                     tk=_w['tiw_od'] * _w['k_wind'] + _w['t_tape']),
              r'J_{p}=\frac{%(ip).2f\ \mathrm{A}}{%(ap).2f\ '
              r'\mathrm{mm^{2}}}=\mathbf{%(jp).2f\ A/mm^{2}}\,,\qquad '
              r'J_{s}=\frac{%(isec).2f\ \mathrm{A}}{%(sp)d\times '
              r'%(asec).2f\ \mathrm{mm^{2}}}=\mathbf{%(js).2f\ A/mm^{2}}'
              % dict(ip=_rp[2], ap=_w['area_p'], jp=_w['j_p'], isec=_rs[2],
                     sp=_w['sec_par'], asec=_w['area_s'], js=_w['j_s'])]))
    add(p('The primary bundle is %(np)d strands against the %(n1)d the '
          'copper asks; the secondary bundle %(ns)d, %(sss)d a turn against '
          '%(n2)d. Both run under the %(jc).1f&nbsp;A/mm&sup2; of this note: '
          'the room the leakage leaves goes into copper.'
          % dict(np=_w['n_strand'], n1=_np1, ns=_w['n_strand_s'],
                 sss=_w['sec_par'] * _w['n_strand_s'], n2=_ns1,
                 jc=_CORE.J_CU)))
    add(p('<b>The leakage.</b> Equation&nbsp;%(e)s with the widths of '
          'Table&nbsp;%(t)s and nothing between the sections gives the upper '
          'estimate'
          % dict(e=ER('leak'), t=TR('winding'))))
    add(calc(r'L_{short}\approx\frac{4\pi\times10^{-7}\times %(ln).0f\ '
             r'\mathrm{mm}}{%(hw).2f\ \mathrm{mm}}\times %(np)d^{2}\left('
             r'\frac{%(wa).2f}{3}+\frac{%(ws).2f}{3}\right)\ \mathrm{mm}'
             r'=\mathbf{%(L).1f\ \mu H}'
             % dict(ln=_R['lN'], hw=_hw, np=V['Np'], wa=_w['w_A'],
                    ws=_w['w_S'], L=_L2)))
    add(p('A field solution of the drawn layout (the window solved exactly '
          'with the core as an ideal boundary, the part of each turn outside '
          'the core solved in free space over the centre leg, where it leaks '
          '%(ro).2f times as much per length) gives <b>%(Lf).2f&nbsp;&micro;H'
          '</b>, %(pc).1f&nbsp;%% over L<sub>r</sub> and inside the '
          '&plusmn;10&nbsp;%% of the specification. Wound tight '
          '(k<sub>w</sub>&nbsp;=&nbsp;1) the same winding would leak '
          '%(Lt).2f&nbsp;&micro;H, so the looseness of the winding moves '
          'L<sub>short</sub> by %(dl).0f&nbsp;%%. <b>Nothing in this '
          'construction trims it after the first samples.</b> A space left '
          'between the sections raises it, %(d01).2f&nbsp;&micro;H for every '
          '0.1&nbsp;mm, so the secondary group is wound tight against the '
          'primary section; lowering it would take narrower sections. Both '
          'figures are estimates; the first samples decide.'
          % dict(ro=_ef['out_ratio'], Lf=_ef['L'],
                 pc=100 * (_ef['L'] / V['Lshort'] - 1), Lt=_et,
                 dl=100 * (1 - _et / _ef['L']), d01=_g01 - _ef['L'])))
    add(p('<b>The order of the secondary layers.</b> In service only one '
          'half of the centre tap conducts at a time, so the tank sees the '
          'leakage with that half shorted and the other open, not the '
          'both-shorted figure the specification measures. The four '
          'secondary layers are one turn each, and their order decides '
          'those two values. Wound %(ord)s from the tube out, the halves come '
          'to <b>%(h2).2f and %(h3).2f&nbsp;&micro;H</b> (NS2, NS3 shorted '
          'alone); both turns of NS2 under both of NS3 would give %(a2).2f '
          'and %(a3).2f&nbsp;&micro;H, and NS2 on either side of NS3 %(b2).2f '
          'and %(b3).2f&nbsp;&micro;H. The alternating order gives the '
          'closest and the lowest pair. Even so, the higher half is '
          '%(hp).0f&nbsp;%% over L<sub>r</sub>, outside the '
          '&plusmn;10&nbsp;%% the both-shorted figure is held to, and its '
          'resonant frequency is %(df).1f&nbsp;%% below the other&rsquo;s. '
          'The first samples measure both halves (Table&nbsp;%(t)s). The '
          'winder lays one turn of NS2, tape, one turn of NS3, tape, and so '
          'on; each group steps up past the other&rsquo;s turn at the '
          'lead-out side.'
          % dict(ord=', '.join(_w['order']), h2=_h2, h3=_h3,
                 a2=_o22[0], a3=_o22[1], b2=_o33[0], b3=_o33[1],
                 hp=100 * (_hmax / V['Lshort'] - 1),
                 df=100 * (1 - (min(_h2, _h3) / _hmax) ** 0.5),
                 t=TR('spec-out'))))
    add(p('<b>The bundles in parallel.</b> Across the secondary section the '
          'leakage field runs radially and falls from the primary side to '
          'the far flange, so the %(sp)d bundles of a turn, side by side, '
          'link different flux and a current runs around them. The second '
          'turn of each winding lays its bundles in the reverse order (the '
          'group is turned over on its way up), so each bundle takes a near '
          'place once and a far place once. That cuts the current, to a '
          'first order, from %(nt).0f to %(tw).1f&nbsp;A rms against the '
          '%(ld).1f&nbsp;A each bundle carries. It adds about '
          '%(pc).2f&nbsp;W, %(pr).0f&nbsp;%% of the secondary dc loss; '
          'the first sample checks it with a current probe on each pin.'
          % dict(sp=_w['sec_par'], nt=_sh['not_turned'], tw=_sh['turned'],
                 ld=_sh['load'], pc=_pcirc, pr=100 * _pcirc / _psdc)))
    add(p('<b>The ac loss.</b> The dc resistance is a floor. Every strand '
          'also sits in the leakage field, up to %(bp).1f&nbsp;mT rms in '
          'the primary section and %(bs).1f in the secondary, and a strand '
          'of diameter d<sub>s</sub> in a field B loses '
          '&pi;&omega;&sup2;&sigma;d<sub>s</sub>&#8308;B&sup2;/64 per '
          'metre. Summed over the strands of the drawn layout, at the '
          'line-cycle rms current, that is %(pa).1f to %(pb).1f&nbsp;W in NP1 '
          'and %(sa).1f to %(sb).1f&nbsp;W in NS2 and NS3 between '
          '%(fa).0f&nbsp;kHz (the line peak at the half-bridge edge) and '
          'f<sub>r</sub>, against %(dc).1f&nbsp;W of dc loss: a first-order '
          'estimate, and <b>%(ra).0f to %(rb).0f times the dc loss</b>. It '
          'is the price of using the leakage field as the resonant inductor, '
          'and the strand sets it: for the same copper it goes as '
          'd<sub>s</sub>&sup2;, so &oslash;0.071&nbsp;mm strands halve it and '
          '&oslash;0.05&nbsp;mm quarter it, at a lower k<sub>litz</sub> that '
          'the wire vendor gives. The thermal measurement of the first sample '
          'decides the strand.'
          % dict(bp=1e3 * _pa['B_pri'], bs=1e3 * _pa['B_sec'],
                 pa=_pa['P_pri'], pb=_pb['P_pri'], sa=_pa['P_sec'],
                 sb=_pb['P_sec'], fa=V['fswA'], dc=_pdc,
                 ra=(_pa['P_pri'] + _pa['P_sec']) / _pdc,
                 rb=(_pb['P_pri'] + _pb['P_sec']) / _pdc)))
    _built = (V['Np'] * _w['area_p']
              + 2 * V['Ns'] * _w['sec_par'] * _w['area_s'])
    add(p('<b>What the core must offer.</b> A<sub>e</sub> of at least '
          '%(ae).0f&nbsp;mm&sup2;; a window of at least %(cu).1f/%(ku).2f = '
          '%(win).0f&nbsp;mm&sup2; for the copper of NP1, NS2 and NS3 (NAUX '
          'carries only the V<sub>CC</sub> load, %(ivcc).0f&nbsp;mA on '
          'average, and is left out) at k<sub>u</sub>&nbsp;=&nbsp;%(ku).2f; '
          'and, for the leakage, a window deep and short enough that the '
          'filled section winding comes out at L<sub>r</sub>.'
          % dict(ae=V['Aereq'], cu=_CORE.window(V), ku=_CORE.K_U, win=_cw,
                 ivcc=A.SH['I.VCC'])))
    _pc = _R['P_core_max']
    add(p('<b>The core.</b> TDK <b>%(core)s</b>, an %(chosen)s in %(mat)s '
          'ferrite: A<sub>e</sub> = %(ae).0f&nbsp;mm&sup2;, %(rae).1f times '
          'what the flux needs, so B<sub>pk</sub> is %(bpk).0f&nbsp;mT; a '
          'window %(hw).2f&nbsp;mm deep and %(wh).1f&nbsp;mm high with a '
          'rectangular centre leg %(f).1f&nbsp;mm across, all at the '
          'catalogue limits that make the window smallest. No coil former is '
          'catalogued for it, so the former is <b>custom</b>, made to this '
          'winding: its tube leaves %(hr).2f&nbsp;mm of radial room, which '
          'both sections fill; the winding takes %(ww).2f&nbsp;mm of the '
          '%(wh).1f&nbsp;mm window height, and the flanges take the rest, '
          '%(fl).2f&nbsp;mm each. That is %(un).2f&nbsp;mm a side more than '
          'the thinnest flange assumed (%(fm).2f&nbsp;mm), together less '
          'than one bundle pitch, so no bundle place is lost. Its '
          'A<sub>N</sub> at the thinnest flanges is %(an).0f&nbsp;mm&sup2;; '
          'the copper as built is %(bu).1f&nbsp;mm&sup2;. The catalogue '
          'gives the core loss at one point only, %(p0).2f&nbsp;W at most at '
          '%(pf).0f&nbsp;kHz, %(pb).0f&nbsp;mT and %(pt).0f&nbsp;&deg;C; the '
          'loss at %(bpk).0f&nbsp;mT and f<sub>r</sub> comes from the '
          '%(mat)s material curve. Table&nbsp;%(t2)s is the arithmetic.'
          % dict(chosen=_CORE.CHOSEN, mat=_R['material'], core=_R['core'],
                 ae=_R['Ae'], rae=_R['Ae'] / V['Aereq'],
                 bpk=_CORE.flux(V, _R['Ae']), hw=_hw, wh=_M['win_h'],
                 f=_M['d_centre'], hr=_w['r_free'], ww=_w['wind_w'],
                 fl=_w['flange'], un=_w['unused'], fm=_CORE.FLANGE_MIN,
                 an=_R['AN'], bu=_built, p0=_pc[0], pf=_pc[1], pb=_pc[2],
                 pt=_pc[3], t2=TR('winding'))))
    add(p('<b>The gap is one piece, and the winding is close to it.</b> '
          'TDK stocks this core gapped to %(al1)s nH only; '
          'A<sub>L</sub>&nbsp;=&nbsp;%(AL).0f&nbsp;nH is ground to order. The '
          'catalogue&rsquo;s A<sub>L</sub>-against-gap curve, a fit to its '
          'measurement with the fringing in it, gives <b>about '
          '%(cg).1f&nbsp;mm</b> for it%(ex)s; the vendor grinds to '
          'A<sub>L</sub>, not to the length. The one gap is at the middle of '
          'the centre leg, under the last %(ud).1f&nbsp;mm of the primary '
          'section next to the face where the sections meet, with the first '
          'layer of NP1 %(wall).2f&nbsp;mm away across the tube. Its '
          'fringing field reaches into the inner layers; whether it is split '
          'into several gaps, and what the fringing costs in the Litz, is '
          'open (Table&nbsp;%(t)s).'
          % dict(al1='250 and 500', AL=V['AL'], cg=_gl,
                 ex=('' if _gin else ', past the %.0f&nbsp;mm end of the drawn '
                     'curve, so the figure is extrapolated'
                     % _R['AL_curve'][3]),
                 ud=min(_under, _w['w_A']), wall=_wall,
                 t=TR('openitems'))))
    ext(tbl('The winding, from current to copper. NS3 is the same as NS2 '
            'and is wound with it.',
            [['Step', 'Primary NP1', 'Secondary NS2'],
             ['Line-cycle rms current', '%.2f A' % _rp[2], '%.2f A' % _rs[2]],
             ['Copper asked at J = %.1f A/mm&sup2;' % _CORE.J_CU,
              '%.2f / %.1f = <b>%.2f mm&sup2;</b>, %d strands'
              % (_rp[2], _CORE.J_CU, _rp[3], _np1),
              '%.2f / %.1f = <b>%.2f mm&sup2;</b>, %d strands'
              % (_rs[2], _CORE.J_CU, _rs[3], _ns1)],
             ['Pitch, radial room',
              'k<sub>w</sub> = %.2f (assumed), tape %.2f mm; h<sub>r</sub> '
              '= %.2f mm' % (_w['k_wind'], _w['t_tape'], _w['r_free']),
              'the same; NAUX %.1f &times; %.2f + %.2f mm on top'
              % (_w['tiw_od'], _w['k_wind'], _w['t_tape'])],
             ['Conductor as built',
              'one triple-insulated Litz bundle, %d &times; &oslash;%.2f mm: '
              '&oslash;%.2f + %.1f = <b>&oslash;%.2f mm</b>'
              % (_w['n_strand'], _CORE.D_STRAND, _w['d_litz'],
                 _w['tiw_add'], _w['d_pri']),
              '%d Litz bundles side by side a turn, %d &times; &oslash;%.2f '
              'mm each: <b>&oslash;%.2f mm</b>'
              % (_w['sec_par'], _w['n_strand_s'], _CORE.D_STRAND,
                 _w['d_sec'])],
             ['Current density as built',
              '%.2f / %.2f = <b>%.2f A/mm&sup2;</b>'
              % (_rp[2], _w['area_p'], _w['j_p']),
              '%.2f / (%d &times; %.2f) = <b>%.2f A/mm&sup2;</b>'
              % (_rs[2], _w['sec_par'], _w['area_s'], _w['j_s'])],
             ['Turns and layers',
              '%d T in %d layers of %s turns, the last layer spread'
              % (V['Np'], _w['layers_A'],
                 ', '.join(str(n) for n in _w['rows_A'])),
              '%d T, one turn a layer; %d layers with NS3, from the tube %s'
              % (V['Ns'], _w['sec_layers'], ', '.join(_w['order']))],
             ['Width on the former',
              '%d &times; %.2f &times; %.2f = <b>%.2f mm</b>'
              % (_w['per_A'], _w['d_pri'], _w['k_wind'], _w['w_A']),
              '%d &times; %.2f &times; %.2f = <b>%.2f mm</b>'
              % (_w['sec_par'], _w['d_sec'], _w['k_wind'], _w['w_S'])],
             ['Radial build, tape included',
              '%d &times; (%.2f &times; %.2f + %.2f) = <b>%.2f mm</b> of %.2f'
              % (_w['layers_A'], _w['d_pri'], _w['k_wind'], _w['t_tape'],
                 _w['h_A'], _w['r_free']),
              '%d &times; (%.2f &times; %.2f + %.2f) = %.2f mm, + NAUX = '
              '<b>%.2f mm</b> of %.2f'
              % (_w['sec_layers'], _w['d_sec'], _w['k_wind'], _w['t_tape'],
                 _w['h_S'], _w['h_S_aux'], _w['r_free'])],
             ['Former, custom',
              'margin %.1f + %.2f + %.2f + margin %.1f = <b>%.2f mm</b> of '
              'the %.1f mm window height; flanges %.2f mm each'
              % (_w['margin'], _w['w_A'], _w['w_S'], _w['margin'],
                 _w['wind_w'], _M['win_h'], _w['flange']), ''],
             ['Copper in the window',
              'asked: %d &times; %.2f + %d &times; %.2f = %.1f mm&sup2;, '
              'which at k<sub>u</sub> = %.2f needs %.0f mm&sup2; of window; '
              'as built %.1f mm&sup2;; A<sub>N</sub> = %.0f mm&sup2;'
              % (V['Np'], _rp[3], 2 * V['Ns'], _rs[3], _CORE.window(V),
                 _CORE.K_U, _cw, _built, _R['AN']),
              '']],
            widths=[CW * 0.20, CW * 0.42, CW * 0.38],
            key='winding', split=True))

    add(h2('The winding and the pins'))
    add(p('Figure&nbsp;%(f)s shows the section and the winding; '
          'Table&nbsp;%(t)s names each item.'
          % dict(f=FR('an_core_section'), t=TR('legend42'))))
    add(fig('an_core_section',
            'The core in section (left, to scale), the winding unrolled '
            'along the custom former (top right, to scale) and the secondary '
            'group layer by layer (bottom right, not to scale). NP1 in one '
            'section, the secondaries in the other, the two sections '
            'touching; the yellow lines are the layer tape. The circled '
            'numbers are the rows of Table&nbsp;%(t)s.'
            % dict(t=TR('legend42')), shrink=False))
    ext(tbl('Items of the figure.',
            [['Mark', 'Item', 'Turns', 'Conductor, placement'],
             ['1', 'NP1 primary, pins %s' % _CORE.pins('NP1', '&ndash;'),
              '%d T' % V['Np'],
              'one triple-insulated Litz bundle, %d &times; &oslash;%.2f mm '
              '(&oslash;%.2f mm), %d layers of %s turns in the primary '
              'section, tape over each layer'
              % (_w['n_strand'], _CORE.D_STRAND, _w['d_pri'],
                 _w['layers_A'], ', '.join(str(n) for n in _w['rows_A']))],
             ['2', 'NS2 secondary, pins %s' % _CORE.pins('NS2', '&ndash;'),
              '%d T' % V['Ns'],
              '%d Litz bundles side by side a turn, %d &times; &oslash;%.2f '
              'mm each, one turn a layer, the bundle order reversed on the '
              'second turn; tape over each layer'
              % (_w['sec_par'], _w['n_strand_s'], _CORE.D_STRAND)],
             ['3', 'NS3 secondary, pins %s' % _CORE.pins('NS3', '&ndash;'),
              '%d T' % V['Ns'], 'the same; from the tube out the layers are '
              '%s' % ', '.join(_w['order'])],
             ['4', 'NAUX auxiliary, pins %s'
              % _CORE.pins('NAUX', '&ndash;'), '%d T' % V['Naux'],
              'triple-insulated wire, &oslash;%.1f mm assumed, one layer over '
              'the secondaries; feeds V<sub>CC</sub> and ZCD'
              % _w['tiw_od']],
             ['5', 'Tape', '&mdash;',
              'margin %.1f mm at each flange, as high as the section beside '
              'it; layer tape %.2f mm (assumed) over every layer and over '
              'NAUX' % (_w['margin'], _w['t_tape'])],
             ['6', 'Centre-leg gap', '&mdash;',
              'one gap, about %.1f mm from the catalogue curve, ground to '
              'A<sub>L</sub> = %.0f nH' % (_gl, V['AL'])],
             ['7', 'Coil former', '&mdash;',
              'custom: tube %.1f mm across, flanges %.2f mm; no insulation '
              'role' % (_M['tube_od'], _w['flange'])]],
            widths=[CW * 0.07, CW * 0.30, CW * 0.09, CW * 0.54],
            key='legend42', split=True))
    _B = _CORE.BOBBIN
    add(p('<b>Pins.</b> The former is custom, so its pins are specified '
          'here: %(pins)d in two rows of %(half)d at %(pitch).2f&nbsp;mm, '
          'rows %(rows).2f&nbsp;mm apart under the core. NP1 and the '
          'auxiliary NAUX take the row at the primary-section flange, NS2 '
          'and NS3 the other. Each end of NP1 and NAUX is one pin. Each end '
          'of NS2 and NS3 is %(np)d pins, one for each bundle: %(np)d '
          'bundles soldered to one pin would make it too thick for its hole '
          'in the board. A pin then carries %(ip).1f&nbsp;A rms, line-cycle; '
          'the bobbin maker confirms the rating. The NAUX leads cross the '
          'primary section to their row inside their triple insulation. The '
          'centre tap is made on the board.'
          % dict(pins=_B['pins'], half=_B['pins'] // 2, pitch=_B['pitch'],
                 rows=_B['rows_apart'], np=_w['sec_par'],
                 ip=V['Idio'] / _w['sec_par'])))
    add(fig('an_xfmr_pins',
            'The schematic symbol with its pin numbers, and the same pins on '
            'the %(former)s coil former (%(pins)d pins, pitch '
            '%(pitch).2f&nbsp;mm, rows %(rows).2f&nbsp;mm apart). A ring in a '
            'winding&rsquo;s colour marks its pins; grey pins are free. The '
            'dot end is the start of each winding. %(note)s'
            % dict(former=_B['former'], pins=_B['pins'], pitch=_B['pitch'],
                   rows=_B['rows_apart'], note=_CORE.PIN_NOTE)))
    _PM = _CORE.PINMAP

    def PIN_ROW0(n):
        return _CORE.PIN_XY[n][1] < 0
    ext(tbl('Winding-to-pin assignment.',
            [['Winding', 'Pins (start &ndash; finish)', 'Turns', 'Conductor',
              'Row'],
             ['NP1 primary', _CORE.pins('NP1', '&ndash;'), '%d T' % V['Np'],
              'one triple-insulated Litz bundle of %d &times; &oslash;%.2f '
              'mm' % (_w['n_strand'], _CORE.D_STRAND),
              _B['rows'][0]],
             ['NAUX auxiliary (V<sub>CC</sub>, ZCD)',
              _CORE.pins('NAUX', '&ndash;'), '%d T' % V['Naux'],
              'triple-insulated wire over the secondary', _B['rows'][0]],
             ['NS2 secondary', _CORE.pins('NS2', '&ndash;'), '%d T' % V['Ns'],
              'Litz, %d bundles side by side, one to each pin'
              % _w['sec_par'], _B['rows'][1]],
             ['NS3 secondary', _CORE.pins('NS3', '&ndash;'), '%d T' % V['Ns'],
              'the same, wound with NS2', _B['rows'][1]],
             ['Centre tap', '%s, joined on the PCB' % _CORE.tap_text(),
              '&mdash;', '&mdash;', _B['rows'][1]],
             ['Free', ', '.join(str(n) for n in _CORE.free_pins()),
              '&mdash;', 'not connected',
              _B['rows'][0] if all(PIN_ROW0(n) for n in _CORE.free_pins())
              else 'both rows']],
            widths=[CW * 0.20, CW * 0.26, CW * 0.09, CW * 0.27, CW * 0.18],
            key='pins', split=True))
    #  Which auxiliary pin goes to ground was not said, and the sentence
    #  is true only one way round: the primary dot is negative while the
    #  low side of leg 1 (LOUT1) is on, so ZCD must come off the finish
    #  (round 63; datasheet 5.3.4).
    add(p('<b>Polarity.</b> The datasheet asks for ZCD positive while the '
          'low-side switch of leg 1 (LOUT1) is on. The primary dot is then '
          'negative, so the auxiliary start, pin %(a)d (the dot), goes to '
          'ground and its finish, pin %(b)d, to R<sub>ZCD,H</sub> and to the '
          'V<sub>CC</sub> rectifier. NS2 and NS3 are wound in the same sense; '
          'the tap joins the finish of NS2 to the start of NS3.'
          % dict(a=_PM['NAUX'][0][0], b=_PM['NAUX'][1][0])))

    add(h2('Safety insulation of this transformer'))
    _IR = _INS.req()
    _ck, _cw2 = _INS.checks(V)
    add(p('The set is a TV sold in the US, the EU, Japan, Korea and China, '
          'so each requirement is taken where it is strictest: '
          '<b>reinforced</b> insulation, because a Class&nbsp;II set needs it '
          'and it covers Class&nbsp;I; <b>%(alt)d&nbsp;m</b>, because '
          'GB&nbsp;4943.1-2022 assumes that altitude unless the manufacturer '
          'specifies otherwise [GB]; and the working voltage at '
          '<b>%(vm).0f&nbsp;Vac</b>, the top of the design range. Primary '
          'means NP1 and NAUX; secondary means NS2, NS3 and the core, which '
          'sits on the secondary side because the primary carries its own '
          'insulation (Section&nbsp;%(s)s).'
          % dict(alt=_INS.ALTITUDE_M, vm=_INS.V_MAINS_DESIGN,
                 s=SR('Safety insulation: what the winding has to carry'))))
    add(p('<b>The working voltage</b> between the primary winding and the '
          'secondary is estimated from the design: the mains neutral and the '
          'secondary at earth, the bridge taking the primary ground to the '
          'line in one half-cycle, the leg voltages and the C<sub>r</sub> '
          'swing of the sweep at every point of the line cycle. At '
          '%(vm).0f&nbsp;Vac it comes to %(ur).0f&nbsp;V rms and '
          '%(up).0f&nbsp;V peak, below the mains itself, so the mains sets the '
          'creepage row. The certifying body measures it; the row taken '
          'covers %(row)d&nbsp;V.'
          % dict(vm=_INS.V_MAINS_DESIGN, ur=_IR['u_rms'], up=_IR['u_pk'],
                 row=_IR['row'])))
    ext(tbl('The insulation requirements and where each number comes from. '
            'The sources are listed under References.',
            [['Item', 'Requirement', 'Basis'],
             ['Grade', 'reinforced, primary to secondary',
              'Class II set [TUV]'],
             ['Conditions', 'pollution degree 2, overvoltage category II, '
              'material group IIIb, %d m' % _INS.ALTITUDE_M,
              'IIIb because the bobbin&rsquo;s tracking index is not known; '
              'altitude [GB]'],
             ['Clearance', '%.1f &times; %.2f = %.2f &rarr; <b>%.1f mm</b>'
              % (_IR['cl_2000'], _INS.K_ALT, _IR['cl_2000'] * _INS.K_ALT,
                 _IR['clearance']),
              'mains transient %.0f V; reinforced at the next step, 4000 V, '
              'which reads %.1f mm [ATIS, TUV]; the temporary-overvoltage '
              'route gives only %.2f mm [PI]; &times;%.2f for %d m, rounded '
              'up [PI]' % (_INS.V_TRANSIENT, _INS.CL_TABLE14_R,
                           _INS.CL_TABLE10_R, _INS.K_ALT, _INS.ALTITUDE_M)],
             ['Creepage', '2 &times; %.1f = <b>%.1f mm</b>'
              % (_IR['creep_basic'], _IR['creep']),
              'basic at the %d V row [PI]; reinforced is twice basic [TI]; '
              'the same rows a CB report applies [TUV]' % _IR['row']],
             ['Solid insulation', 'thickness &ge; %.1f mm, or &ge; %d tape '
              'layers' % (_IR['dti'], _IR['layers']),
              'each layer must pass the reinforced electric-strength test '
              '[TUV]'],
             ['Electric strength', '%d V ac for 60 s, or %d V dc'
              % (_IR['hipot_ac'], _IR['hipot_dc']),
              'type test, NP1 + NAUX against NS2 + NS3 and the core; the '
              'value a CB report applies to a Class II 100&ndash;240 V '
              'product at %d m [TUV]; one minute after humidity conditioning '
              '[PI]' % _INS.ALTITUDE_M],
             ['NP1 and NAUX wire', 'triple-insulated wire approved as '
              'reinforced; Litz for NP1',
              'approvals exist to EN IEC 62368-1 and to IEC 62368-1:2018 '
              'Annex&nbsp;J at %d V rms and %d kHz, insulation Class %s, '
              'the Litz version on the same approvals [TIW]'
              % (_INS.TIW_VRMS, _INS.TIW_FMAX / 1e3, _INS.TIW_CLASS)]],
            widths=[CW * 0.16, CW * 0.30, CW * 0.54], key='insreq',
            split=True))
    add(p('Table&nbsp;%(t)s takes every path between the two sides and '
          'names what carries it. The wire carries all of them inside the '
          'winding: where the two sections touch, only the triple insulation '
          'of NP1 is between them.' % dict(t=TR('inscheck'))))
    ext(tbl('What carries the insulation on each path, on the %s.'
            % _cw2['name'],
            [['Path', 'Carried by', 'Required', 'Status']]
            + [[pth, by, need, st] for pth, by, need, st in _ck],
            widths=[CW * 0.26, CW * 0.34, CW * 0.30, CW * 0.10],
            key='inscheck', split=True))
    add(p('NP1 and NAUX stay in their triple insulation from pin to pin, '
          'crossings included; only the ends at the pins are stripped, and '
          'that is where the drawing stops. What it cannot settle goes to '
          'the certifying body and the vendors:'))
    ext(bullets([
        'The primary pins and the stripped wire ends against the core yoke '
        'and the secondary leads: set by the coil former and the lead '
        'dress. Reinforced distances, or sleeving qualified as reinforced '
        'insulation.',
        'The triple-insulated Litz itself: one bundle of %d &times; '
        '&oslash;%.2f mm is the size this design asks for; the '
        '%.1f mm of insulation over the bundle is assumed, and the size and '
        'its approval come from the wire vendor.'
        % (_w['n_strand'], _CORE.D_STRAND, _w['tiw_add']),
        'The electric-strength value under the edition the certificate will '
        'cite, and the production test voltage and time.',
        'Clearance for the high-frequency part of the working voltage: the '
        'sources quoted do not give that table. A CB report applied the '
        'ordinary values at 133 kHz and 588 V peak [UL].',
        'The TIW approval quoted stops at %d kHz; the start-up frequency is '
        '%.0f kHz for the first milliseconds of safe start, and NP1 now '
        'sees it too. Ask the wire vendor. Its Class %s rating also caps '
        'the winding hot spot; the thermal measurement has to show it.'
        % (_INS.TIW_FMAX / 1e3, A.SH['f.SU'], _INS.TIW_CLASS),
        'L<sub>short</sub> is a field-solution estimate, %.2f&nbsp;&micro;H '
        'with the sections touching at the assumed winding pitch; the first '
        'samples decide.' % _ef['L']]))

    add(h2('Checking the flux, and the specification'))
    add(p('<b>Peak flux density</b> on the chosen core, at f<sub>r</sub> '
          '(Equation&nbsp;%s):' % ER('Bpk')))
    add(calc(r'B_{pk}=\frac{%.1f\ \mathrm{V}}{4\times %.2f\ \mathrm{kHz}'
             r'\times %d\times %.1f\ \mathrm{mm^{2}}}=\mathbf{%.0f\ mT}'
             % (V['Vout'], V['fr'], V['Ns'], V['Aemm'], V['Bpk'])))
    add(p('<b>Magnetising peak</b>, over L<sub>&mu;</sub> (it equals '
          'i<sub>&mu;,pk</sub>):'))
    add(eqagain('Isat'))
    add(calc(r'I_{eq}=\frac{%.4f\ \mathrm{T}\times %d\times %.1f\ \mathrm{mm^{2}}}'
             r'{%.2f\ \mu\mathrm{H}}=\mathbf{%.2f\ A}\ =\ i_{\mu,pk}'
             % (V['Bpk'] / 1e3, V['Np'], V['Aemm'], V['Lmu'] / V['nser'],
                V['Isateq'])))
    add(p('The same current from the output voltage alone '
          '(Equation&nbsp;%s), with no core data in it:' % ER('imuVo')))
    add(calc(r'i_{\mu,pk}=\frac{%.2f\times %.1f\ \mathrm{V}}'
             r'{4\times %.2f\ \mathrm{kHz}\times %.2f\ \mu\mathrm{H}}'
             r'=\mathbf{%.2f\ A}'
             % (V['nT'], _SH['V.o_eff'], V['fr'], V['Lmu'] / V['nser'],
                V['nT'] * _SH['V.o_eff'] / (4 * V['fr'] * 1e3
                                       * V['Lmu'] / V['nser'] * 1e-6))))
    add(p('<b>Saturation test current</b>, the magnetising peak at the '
          'OVP2 output voltage:'))
    add(eqagain('Isatspec'))
    add(calc(r'I_{sat}=%.2f\ \mathrm{A}\times\frac{%.2f\ \mathrm{V}}{%.1f\ \mathrm{V}}'
             r'=%.2f\times %.4f=\mathbf{%.1f\ A}'
             % (V['Isateq'], V['OVP2'], V['Vout'], V['Isateq'],
                V['OVP2'] / V['Vout'], V['Isatspec'])))
    add(fig('an_mmf',
            'In service the secondary cancels most of the primary '
            'ampere-turns; with every other winding open, the whole test current '
            'magnetises the core. The design flux is therefore reached at '
            '%(ILm).2f&nbsp;A on the bench, not at the %(Icomp).2f&nbsp;A '
            'tank peak.' % V))
    _r1, _r2 = V['OVP1'] / V['Vout'], V['OVP2'] / V['Vout']
    _iocp = float(A.SH['I.OCP1'])
    add(p('<b>Why OVP2, in this design&rsquo;s numbers.</b> OVP1 is set at '
          '%(o1).2f&nbsp;V, %(r1).3f times the output, and OVP2 at '
          '%(o2).2f&nbsp;V, %(r2).3f times. At OVP1 the controller keeps '
          'switching, so the flux can reach %(b1).0f&nbsp;mT with the core '
          'still driven; at OVP2 it stops, and %(b2).0f&nbsp;mT is the '
          'largest flux this core is ever asked to carry. That is the '
          'number to hold against the hot B<sub>s</sub> of %(mat)s from '
          'the material data. The line on the specification reads: DC '
          'overlap, inductance at least 90&nbsp;%% of initial at '
          '%(isat).0f&nbsp;A (%(calc).1f&nbsp;A rounded up), normal '
          'temperature (Table&nbsp;%(t)s).'
          % dict(o1=V['OVP1'], r1=_r1, o2=V['OVP2'], r2=_r2,
                 b1=V['Bpk'] * _r1, b2=V['Bpk'] * _r2,
                 mat=_CORE.CORES[_CORE.CHOSEN]['material'],
                 isat=V['IsatTest'], calc=V['Isatspec'],
                 t=TR('spec-out'))))
    add(p('<b>How to run it on this part.</b> LCR meter across the primary '
          '(NP1, the pins of Table&nbsp;%(t)s) with both secondaries, the '
          'centre tap and the auxiliary winding open. Small signal '
          '100&nbsp;kHz, 1&nbsp;V, the same as the leakage test; bias '
          'current stepped from zero to past %(isat).0f&nbsp;A, inductance '
          'recorded at each step. Pass if L at %(isat).0f&nbsp;A is at least '
          '0.9 of L at zero, where L at zero is L<sub>open</sub> '
          '&asymp; %(lo).1f&nbsp;&micro;H. Keep each step short: the dc '
          'heats the winding through its resistance, and a warm core '
          'saturates earlier. A part whose curve knees below '
          '%(isat).0f&nbsp;A has too little gap or the wrong core, even when '
          'L<sub>open</sub> is on target; the margin against a hot core '
          'is in B<sub>pk</sub>, not in the test.'
          % dict(t=TR('pins'), isat=V['IsatTest'], lo=V['Lopen'])))
    add(p('<b>If there were no OVP2.</b> The current limit would be the '
          'only ceiling: OCP1 trips at %(io).2f&nbsp;A, %(rr).2f times the '
          'OVP2-based %(isat).1f&nbsp;A. At the same L<sub>&mu;</sub> that is '
          '%(bo).0f&nbsp;mT on this core, which has %(ra).1f times the area '
          'the flux target needs. On a core sized to the %(bt).2f&nbsp;T target '
          'it would be %(bt2).0f&nbsp;mT; holding it to the %(bt3).0f&nbsp;mT '
          'that OVP2 allows would take %(rr).2f times the core area or '
          'N<sub>s</sub>. The rule of '
          'thumb of 1.3 times i<sub>&mu;,pk</sub> would give '
          '%(rule).1f&nbsp;A, near the OVP2 figure by coincidence and with '
          'no event behind it.'
          % dict(io=_iocp, rr=_iocp / V['Isatspec'], isat=V['Isatspec'],
                 bo=V['Bpk'] * _iocp / V['Isateq'], bt=_CORE.B_MAX,
                 bt2=1e3 * _CORE.B_MAX * _iocp / V['Isateq'],
                 bt3=1e3 * _CORE.B_MAX * _r2,
                 rule=1.3 * V['Isateq'], ra=V['Aemm'] / V['Aereq'])))
    add(p('Reduced to what a supplier can measure, this is the '
          'specification sheet. L<sub>&mu;</sub> is deliberately absent '
          '(Section&nbsp;'
          + SR('What the transformer specification must say') + ').'))
    ext(tbl('Transformer specification for the worked design.',
            [['Item', 'Value', 'Condition'],
             ['Core', '%s, %s, A<sub>L</sub> %.0f nH' % (
                 _CORE.CHOSEN, _R['material'], V['AL']),
              'TDK %s; %s, to this specification; one centre-leg gap, '
              'ground to A<sub>L</sub>' % (_R['core'], _R['former'])],
             ['Turns', 'N<sub>p</sub> %(Np)d T; NS2 %(Ns)d T and NS3 %(Ns)d T; '
              'NAUX %(Naux)d T' % V,
              'section winding: NP1 as one triple-insulated Litz bundle in '
              'one section, %d layers; NS2 and NS3 in the other, each turn %d '
              'Litz bundles side by side, one turn a layer, layers %s from '
              'the tube, the bundle order reversed on the second turn; the '
              'two sections touching; tape over every layer; each bundle on '
              'its own pin; centre tap outside the part; NAUX in '
              'triple-insulated wire over the secondary'
              % (_w['layers_A'], _w['sec_par'], ', '.join(_w['order']))],
             ['Open-circuit inductance',
              '%(Lopen).1f &micro;H, no more than %(Ldrop).1f %% low '
              '(Equation&nbsp;%(e)s)' % dict(V, e=ER('Ldrop')),
              'measured across NP1; every other winding (NS2, NS3, NAUX) open; '
              'LCR meter 100 kHz, 1 V'],
             ['Leakage inductance', '%(Lshort).1f &micro;H &plusmn;10 %%' % V,
              'measured across NP1; NS2 and NS3 both shorted, NAUX open; '
              'LCR meter 100 kHz, 1 V; estimated at %.2f &micro;H with the '
              'sections touching (Section&nbsp;%s)'
              % (_ef['L'], SR('Choosing the core'))],
             ['Leakage, each half', 'record both',
              'as above with NS2 shorted alone, then NS3 alone: the two halves '
              'of the centre tap, the values the tank sees (field solution '
              '%.2f and %.2f &micro;H); a larger difference means the layer '
              'order was not kept' % (_h2, _h3)],
             ['DC overlap', '&ge; 90 %% of initial inductance' % V,
              'measured across NP1, every other winding open; dc %(IsatTest).0f A '
              'overlapped on the 100 kHz, 1 V signal; normal temperature '
              '(mark 7)' % V],
             ['Primary current', '%(Iprilc).1f A rms / %(Icomp).1f A pk' % V,
              'line-cycle rms (mark 2) and composite peak (mark 1), both at the '
              'HB edge (%(Veqlo).0f Vac, half bridge), full load' % V],
             ['Secondary current, each winding',
              '%(Idio).1f A rms / %(Isec).0f A pk' % V,
              'line-cycle rms (mark 5) and peak (mark 4), both at the HB edge, '
              'full load'],
             ['Core area', 'A<sub>e</sub> &ge; %(Aereq).0f mm&sup2;' % V,
              'holds B<sub>pk</sub> at or below %.2f T at f<sub>r</sub> (mark 6)' % _CORE.B_MAX],
             ['Switching frequency', '%(fswA).0f to %(fswB).0f kHz' % V,
              'at the line peak, full load, from the HB edge to the FB edge; '
              'near the zero crossings it falls towards f<sub>o</sub> = '
              '%(fo).0f kHz' % V],
             ['Insulation', 'reinforced, NP1 + NAUX to NS2 + NS3 and the '
              'core: by the triple-insulated wire; at the pins clearance '
              '&ge; %.1f mm, creepage &ge; %.1f mm'
              % (_INS.req()['clearance'], _INS.req()['creep']),
              'Table&nbsp;%s; nothing between the sections but the wire'
              % TR('inscheck')],
             ['Electric strength', '%d V ac for 60 s (%d V dc)'
              % (_INS.req()['hipot_ac'], _INS.req()['hipot_dc']),
              'NP1 + NAUX against NS2 + NS3 and the core; type test, no '
              'breakdown']],
            widths=[CW * 0.28, CW * 0.34, CW * 0.38], key='spec-out', split=True))

    add(h2('The output bank, as sized'))
    add(p('Both conditions of Section&nbsp;%(ref)s; the larger wins. '
          '<b>Ripple</b>, with &Delta;v as a fraction:'
          % dict(V, ref=SR('The output capacitor bank'))))
    add(eqagain('Crip'))
    add(calc(r'C_{out}\geq\frac{%.1f\ \mathrm{W}}{2\pi\times %.0f\ \mathrm{Hz}'
             r'\times %.2f\times %.0f\ \mathrm{V^{2}}}=\mathbf{%.2f\ mF}'
             % (V['Pout'], V['flmin'], V['dv'] / 100.0, V['Vout'] ** 2,
                V['Crip'])))
    add(p('<b>Hold-up</b>, starting half a ripple below V<sub>out</sub>:'))
    add(eqagain('Chold'))
    add(calc(r'C_{out}\geq\frac{2\times %.1f\ \mathrm{W}\times %.3f\ \mathrm{s}}'
             r'{%.3f^{2}-%.0f^{2}}=\mathbf{%.2f\ mF}'
             r'\qquad(\mathrm{started\ at\ }V_{out}:\ %.2f\ \mathrm{mF})'
             % (V['Pout'], V['Thold'] / 1e3, V['Vout'] - V['dVo'] / 2,
                V['Vomin'], V['Chold'],
                2 * V['Pout'] * V['Thold'] / 1e3
                / (V['Vout'] ** 2 - V['Vomin'] ** 2) * 1e3)))
    add(p('<b>Which wins</b>, at k = V<sub>o,min</sub>/V<sub>out</sub> = '
          '%(k).3f:' % dict(k=V['Vomin'] / V['Vout'])))
    add(eqagain('ripscreen'))
    add(calc(r'%.3f\ >\ %.3f\quad\Longrightarrow\quad\mathrm{ripple\ decides}'
             % (V['ripLHS'], V['ripRHS'])))
    #  the margin of the screen just shown, not the sheet's C ratio: that
    #  one uses the ripple of the bank as built and read 1.060 under a
    #  line whose two sides divide to 1.053 (2026-09-23)
    add(p('The left side is only %(pks).1f&nbsp;%% larger; allow more than %(swap).1f&nbsp;%% '
          'ripple and hold-up would decide instead. The bank fitted is the next assembly above '
          '%(Crip).1f&nbsp;mF: <b>%(Cout1).0f&nbsp;&micro;F &times; '
          '%(nC).0f = %(Cout).1f&nbsp;mF</b>.'
          % dict(V, pks=100 * (V['ripKs'] - 1), swap=V['ripSwap'])))
    add(fig('f19_cout_criterion',
            'Left: both conditions fall as 1/V<sub>out</sub>&sup2;; at '
            '%(Vout).0f&nbsp;V ripple asks for %(Crip).1f&nbsp;mF and hold-up '
            'for %(Chold).1f&nbsp;mF. Right: the same %(Ehold).1f&nbsp;J of '
            'hold-up energy is a %(Cbulk).0f&nbsp;&micro;F part on a '
            '400&nbsp;V bus and %(Chold).1f&nbsp;mF here, %(Cratio).0f times '
            'more. That ratio is the price of the architecture.' % V))
    ext(tbl('What the selected bank then delivers, and what it has to '
            'survive.',
            [['Quantity', 'Value', 'Against'],
             ['Achieved ripple', '%(dVo).2f V (%(dVopc).2f %%)' % V,
              '%(dv).0f %% allowed' % V],
             ['Achieved hold-up', '%(thold).2f ms' % V,
              '%(Thold).0f ms required at 100 Vac, from the ripple trough down to '
              '%(Vomin).0f V &mdash; %(tholdVo).2f ms if started at V<sub>out</sub> '
              'instead of at the trough' % V],
             ['Ripple current, switching component',
              '%(ICouthf).1f A rms' % V, '&mdash;'],
             ['Ripple current, 2f<sub>l</sub> component',
              '%(ICout2f).1f A rms' % V, 'orthogonal to the above'],
             ['Ripple current, total', '<b>%(ICout).2f A rms</b>' % V,
              '%(each).2f A in each of %(nC).0f parts'
              % dict(V, each=A.SH['I.Cout_each'])],
             ['Bank ESR', '%(esr).4f m&Omega;'
              % dict(V, esr=A.SH['ESR.out']),
              '%(esr1).0f m&Omega; each, %(nC).0f in parallel'
              % dict(V, esr1=A.SH['ESR.single'])],
             ['Ripple and noise', '%(RN).1f mV' % V,
              'with the %(Ccer).0f &micro;F ceramic bypass' % V]],
            widths=[CW * 0.30, CW * 0.22, CW * 0.48], key='bank-built', split=True))

    # ------------------------------------------------ loss budget
    add(h2('Where the power goes'))
    add(p('The specification allowed %(diff).1f&nbsp;W of loss, split three '
          'ways before any component existed. The device losses computed '
          'afterwards need not agree with that split, and here they do not.'
          % dict(V, diff=V['Pin'] - V['Pout'])))
    ext(tbl('The budget as assumed, and the device losses as computed. The '
            'second block is not a breakdown of the first.',
            [['Item', 'Value', 'Note'],
             ['<b>Budget</b> &mdash; input bridge', '%(a).2f W'
              % dict(a=A.SH['P.d_BR']), 'synchronous bridge assumed'],
             ['<b>Budget</b> &mdash; EMI filter', '%(a).2f W'
              % dict(a=A.SH['P.d_EMI']), '&mdash;'],
             ['<b>Budget</b> &mdash; LLC stage', '%(a).2f W'
              % dict(a=A.SH['P.d_LLC']),
              '&eta;<sub>HB</sub> = %(etaHB).0f %% of P<sub>in,LLC</sub>' % V],
             ['Primary conduction, standing device', '%(Ploss).2f W' % V,
              'the half-bridge leg that never switches &mdash; the '
              'hottest single device'],
             #  The two SWITCHING positions of half-bridge mode, S1 and S2,
             #  each P.mos_sw.  This row read "three positions" with ONE
             #  position's loss, and the total counted it once: 4.83 W
             #  short (round 63).  With the standing device the two rows
             #  make the sheet's P.pri_tot.
             ['Primary conduction, the two switching positions',
              '%(a).2f W' % dict(a=A.SH['P.pri_tot'] - A.SH['P.mos_dc']),
              'S1 and S2 in half bridge, %(b).2f W each; conduction only, '
              'switching loss not in it' % dict(b=A.SH['P.mos_sw'])],
             ['Secondary rectifiers', '%(a).2f W'
              % dict(a=A.SH['P.SR']),
              '%(PSR).3f W per device, %(nSR).0f in parallel per leg' % V],
             ['Current-sense resistors', '%(a).2f W'
              % dict(a=A.SH['P.RCS']),
              'line-cycle average; %(b).2f W at the worst switching cycle'
              % dict(b=A.SH['P.RCS_pk'])],
             ['Output capacitor ESR', '%(a).3f W'
              % dict(a=A.SH['P.Cout']),
              'all of the ripple current in the switching-frequency ESR; '
              'the 2f<sub>l</sub> part in the higher 120&nbsp;Hz ESR is not '
              'in it (tan&thinsp;&delta; of the fitted part not known)'],
             ['V<sub>CC</sub> pass transistor', '%(a).2f W'
              % dict(a=A.SH['P.Qpass_nom']),
              'at the nominal output; the gate drive itself, up to '
              'I<sub>VCC</sub>V<sub>CC,reg</sub> = %(g).2f W at f<sub>Max</sub>, '
              'is spent in the drivers and gate resistors and is not in the '
              'total' % dict(g=A.SH['I.VCC'] * 1e-3 * A.SH['V.CC_reg'])],
             ['<b>Itemised total</b>', '<b>%(t).2f W</b>'
              % dict(t=A.SH['P.pri_tot'] + A.SH['P.SR']
                     + A.SH['P.RCS'] + A.SH['P.Cout'] + A.SH['P.Qpass_nom']),
              'and the magnetics are not in it']],
            widths=[CW * 0.34, CW * 0.14, CW * 0.52], key='loss', split=True))
    add(p('<b>The standing primary device</b>, the low-side switch of the '
          'idle leg in half-bridge morphing, carries the whole line-cycle '
          'rms continuously, with R<sub>DS(on)</sub> <b>hot</b> at '
          'k<sub>T</sub>&nbsp;=&nbsp;%(kT).1f times the 25&nbsp;&deg;C '
          '%(R25).0f&nbsp;m&Omega; (Section&nbsp;%(ref)s):'
          % dict(V, kT=V['Rdpk'], R25=V['Rdp'],
                 ref=SR('Semiconductor requirements'))))
    add(calc(r'P_{mos,dc}=I_{pri}^{2}\,k_{T}R_{DS(on),25}'
             r'=(%(I).3f)^{2}\cdot%(kT).1f\cdot%(R).0f\times10^{-3}'
             r'=%(P).2f\;\mathrm{W}'
             % dict(I=A.SH['I.pri_lc'], kT=V['Rdpk'], R=V['Rdp'],
                    P=A.SH['P.mos_dc'])))
    add(p('<b>Each secondary rectifier</b> carries the leg current over the '
          '%(nSR).0f devices in parallel, with k<sub>T</sub>&nbsp;=&nbsp;'
          '%(kTs).1f on %(Rs).1f&nbsp;m&Omega;:'
          % dict(V, kTs=V['Rdsk'], Rs=V['Rds'])))
    add(calc(r'P_{SR}=\left(\frac{%(I).2f}{%(n).0f}\right)^{2}'
             r'\cdot%(kT).1f\cdot%(R).1f\times10^{-3}'
             r'=%(P).3f\;\mathrm{W\;per\;device}'
             % dict(I=V['Idio'], n=V['nSR'], kT=V['Rdsk'], R=V['Rds'],
                    P=A.SH['P.SR_dev'])))
    add(note('<b>The efficiency assumption is optimistic.</b> The itemised '
             'device losses are %(t).1f&nbsp;W against the %(b).1f&nbsp;W '
             'that &eta;<sub>HB</sub> = %(etaHB).0f&nbsp;%% allows, before '
             'the transformer. Nothing electrical depends on it; the thermal '
             'design does, and that is settled by measurement.'
             % dict(V, t=A.SH['P.pri_tot'] + A.SH['P.SR']
                    + A.SH['P.RCS'] + A.SH['P.Cout'] + A.SH['P.Qpass_nom'],
                    b=A.SH['P.d_LLC'])))

    # ------------------------------------------------ the loop as built
    add(h2('What the semiconductors have to be'))
    add(p('Requirements, not part numbers (Section&nbsp;'
          + SR('Semiconductor requirements') + ').'))
    ext(tbl('Semiconductor requirements for the worked design.',
            [['Item', 'Requirement'],
             ['Primary drain-source voltage',
              '&ge; %(VDS).0f V, so a 600 V class part' % V],
             ['Primary body diode',
              'fast recovery: a capacitive excursion turns a device on onto '
              'the other&rsquo;s conducting body diode (Section&nbsp;%s)'
              % SR('Why a diode has to recover on one side and not on the '
                   'other')],
             ['Primary R<sub>DS(on)</sub> per device',
              '&le; %(Rdreq).1f m&Omega; <b>hot</b> to meet the loss budget'
              % V],
             ['Primary C<sub>o(tr)</sub>',
              'small enough that the tank can swing the node inside '
              '%(tD).0f ns' % V],
             ['Secondary drain-source voltage',
              '&ge; %(VDSs).0f V including the centre-tap doubling' % V],
             ['Secondary rectifier current',
              '%(Idio).2f A rms per leg, %(Isec).1f A peak' % V],
             ['Secondary package',
              'check the lead and clip rating, not only the die'],
             ['V<sub>CC</sub> pass transistor (NPN)',
              '&beta; &ge; %.0f at %.0f mA; dissipates %.2f W at OVP1; blocks '
              '%.1f V plus the winding spike'
              % (V['bmin'], A.SH['I.VCC'], A.SH['P.Qpass'],
                 A.SH['V.Caux_OVP2'])],
             ['V<sub>CC</sub> Zener',
              '%.0f V &plusmn;%.0f %%, rated above %.0f mW'
              % (V['DZ'], 100 * V['tolDZ'], A.SH['P.DZ'])],
             ['V<sub>CC</sub> rectifier and bypass diodes',
              'reverse rating above %.1f V plus the winding spike'
              % A.SH['V.Caux_OVP2']]],
            widths=[CW * 0.36, CW * 0.64], split=True))
    add(h2('The voltage loop, as built'))
    from math import atan, degrees, sqrt, pi
    _at = lambda w, w0: degrees(atan(w / w0))
    _A = lambda w: (sqrt(1 + (w / V['wz']) ** 2)
                    / (sqrt(1 + (w / V['wp']) ** 2) * sqrt(1 + (w / V['wpx']) ** 2)))
    add(p('The method of Sections&nbsp;%(a)s to %(b)s, with this '
          'converter&rsquo;s numbers, in the order they are found.'
          % dict(a=SR('Voltage loop and compensation'),
                 b=SR('Feedback ripple against the burst threshold'))))
    add(p('<b>Step 1 &mdash; the output divider</b>, with R<sub>I</sub> = '
          '%(RI).0f&nbsp;k&Omega; chosen:' % V))
    add(eqagain('RoVout'))
    add(calc(r'R_{O}=\frac{V_{R}\,R_{I}}{V_{out}-V_{R}}'
             r'=\frac{%.3f\ \mathrm{V}\times %.0f\ \mathrm{k\Omega}}'
             r'{%.1f\ \mathrm{V}-%.3f\ \mathrm{V}}=%.2f\ \mathrm{k\Omega}'
             r'\;\rightarrow\;\mathbf{%.0f\ k\Omega}'
             % (V['VR'], V['RI'], V['Vout'], V['VR'], V['Roc'], V['Ro'])))
    add(calc(r'V_{out}=%.3f\ \mathrm{V}\times\left(1+\frac{%.0f}{%.0f}\right)'
             r'=\mathbf{%.2f\ V}' % (V['VR'], V['RI'], V['Ro'], V['VoutAct'])))
    add(p('<b>Step 2 &mdash; the plant.</b> With K<sub>pwr</sub> = '
          '2K<sub>HV</sub>/(K<sub>M</sub>K<sub>FF</sub>), the slope of '
          'Equation&nbsp;%(e)s, V<sub>FB</sub> = K<sub>pwr</sub> '
          'R<sub>CS</sub> P<sub>in,LLC</sub> = %(Kpwr).3f &times; '
          '%(RCS).0f&nbsp;m&Omega; &times; %(PinLLC).1f&nbsp;W = '
          '%(VFBv).3f&nbsp;V (Equation&nbsp;%(e)s). Then'
          % dict(V, PinLLC=V['Pout'] / (V['etaHB'] / 100.0), e=ER('VFB'))))
    add(eqagain('Gplant'))
    add(calc(r'G_{o}=\frac{%.1f\ \mathrm{W}}{%.1f\ \mathrm{V}\times %.3f\ \mathrm{V}'
             r'\times %.1f\ \mathrm{mF}}=\mathbf{%.1f\ rad/s},\qquad '
             r'f_{cto}=\frac{%.1f}{2\pi}=%.1f\ \mathrm{Hz}'
             % (V['Pout'], V['Vout'], V['VFBv'], V['Cout'], V['Go'], V['Go'],
                V['fcto'])))
    add(p('<b>Step 3 &mdash; the gain allowed at 2f<sub>l</sub></b>, for '
          '%(D3set).0f&nbsp;%% third harmonic:' % V))
    add(eqagain('dVloop'))
    add(calc(r'\Delta V_{loop}=\frac{%.1f\ \mathrm{W}}{%.1f\ \mathrm{V}}\cdot'
             r'\frac{1}{2\pi\times %.0f\ \mathrm{Hz}\times %.1f\ \mathrm{mF}}'
             r'=\mathbf{%.3f\ V}' % (V['Pout'], V['Vout'], V['flmin'], V['Cout'],
                                     V['dVloop'])))
    add(eqagain('GEAreq'))
    add(calc(r'G_{EA}(2f_{l})\leq\frac{4\times %.3f\ \mathrm{V}\times %.2f}'
             r'{%.3f\ \mathrm{V}}=\mathbf{%.4f}'
             % (V['VFBv'], V['D3set'] / 100.0, V['dVloop'], V['GEAreq'])))
    add(p('<b>Step 4 &mdash; the K factor</b>, for a target phase margin of '
          '%(PhiM).0f&deg; (tan&nbsp;%(PhiM).0f&deg; = %(tPM).4f) and '
          '&alpha;<sub>v</sub> = %(alphav).1f:' % V))
    add(eqagain('Kv'))
    add(calc(r'K_{v}=\frac{1}{2\times %.1f}\left[(1+%.1f^{2})\times %.4f'
             r'+\sqrt{(1+%.1f^{2}\times %.4f)^{2}+4\times %.1f^{2}}\right]'
             r'=\mathbf{%.4f}'
             % (V['alphav'], V['alphav'], V['tPM'], V['alphav'], V['tPM'],
                V['alphav'], V['Kv'])))
    add(p('<b>Step 5 &mdash; the compensator gain constant:</b>'))
    add(eqagain('EAotarget'))
    add(calc(r'EA_{o}=\frac{2\pi\times %.0f\ \mathrm{Hz}\times %.4f}{%.4f^{2}}'
             r'=\mathbf{%.2f\ rad/s}'
             % (2 * V['flmin'], V['GEAreq'], V['Kv'], V['EAo'])))
    add(p('<b>Step 6 &mdash; zero and pole</b>, with &Gamma;<sub>v</sub> = '
          '0.744 &times; %(Veqhi).1f / %(Veqlo).2f = %(Gammav).4f:'
          % dict(V, Veqhi=V['Vacmax'])))
    add(eqagain('fMB'))
    add(calc([r'f_{MB}=\frac{1}{2\pi}\sqrt{\frac{%.2f\times %.4f\times %.2f}{%.4f}}'
              r'=\mathbf{%.2f\ Hz}'
              % (V['Go'], V['Kv'], V['EAo'], V['Gammav'], V['fMB']),
              r'f_{p}=%.4f\times %.2f=\mathbf{%.2f\ Hz},'
              r'\qquad f_{z}=\frac{%.2f}{%.4f}=\mathbf{%.3f\ Hz}'
              % (V['Kv'], V['fMB'], V['fp'], V['fMB'], V['Kv'], V['fz'])]))
    add(p('<b>Step 7 &mdash; the bias parts</b>, with the TL431 minimum '
          'current %(Imin).1f&nbsp;mA, V<sub>Z</sub> = %(VZ).0f&nbsp;V, '
          'V<sub>Fo</sub> = %(VFo).2f&nbsp;V, I<sub>FB,steady</sub> = '
          '%(IFBs).0f&nbsp;&micro;A, I<sub>FB,max</sub> = '
          '%(IFBm).0f&nbsp;&micro;A, CTR<sub>s</sub> = %(CTRs).2f, '
          'CTR<sub>m</sub> = %(CTRm).2f:' % V))
    add(eqagain('RPmax'))
    add(calc(r'R_{P}\leq\frac{%.2f\ \mathrm{V}}{%.1f\ \mathrm{mA}}=%.3f\ \mathrm{k\Omega}'
             r'\;\rightarrow\;\mathbf{%.1f\ k\Omega}\ (\mathrm{rounded\ down})'
             % (V['VFo'], V['Imin'], V['RPmax'], V['RP'])))
    add(eqagain('RBwin'))
    _hd = V['VZ'] - V['VR'] - V['VFo']
    add(calc(r'R_{B,max}=\frac{%.0f-(%.3f+%.2f)\ \mathrm{V}}'
             r'{%.2f/%.1f\ \mathrm{mA}+%.0f\,\mu\mathrm{A}/%.2f}'
             r'=\frac{%.3f\ \mathrm{V}}{%.3f\ \mathrm{mA}+%.3f\ \mathrm{mA}}'
             r'=\mathbf{%.2f\ k\Omega}'
             % (V['VZ'], V['VR'], V['VFo'], V['VFo'], V['RP'], V['IFBs'],
                V['CTRs'], _hd, V['VFo'] / V['RP'], V['IFBs'] / V['CTRs'] / 1e3,
                V['RBmax'])))
    add(calc(r'R_{B,min}=\frac{%.3f\ \mathrm{V}}{%.3f\ \mathrm{mA}+'
             r'%.0f\,\mu\mathrm{A}/%.2f}=\mathbf{%.2f\ k\Omega}'
             r'\qquad\rightarrow\ R_{B}=\mathbf{%.1f\ k\Omega}'
             % (_hd, V['VFo'] / V['RP'], V['IFBm'], V['CTRm'], V['RBmin'],
                V['RB'])))
    add(p('<b>Step 8 &mdash; the compensation parts</b>, with '
          'R<sub>FB</sub> = %(RFB).0f&nbsp;k&Omega;, C<sub>opto</sub> = '
          '%(Copto).0f&nbsp;nF and the high-frequency pole placed at '
          '%(fpHF).0f&nbsp;Hz:' % V))
    add(eqagain('Ccomp'))
    add(calc(r'C_{Fo}=\frac{%.3f}{%.2f}\cdot\frac{%.2f\times %.0f\ \mathrm{k\Omega}}'
             r'{%.0f\ \mathrm{k\Omega}\times %.1f\ \mathrm{k\Omega}\times %.2f}'
             r'=%.1f\ \mathrm{nF}\;\rightarrow\;\mathbf{%.0f\ nF}'
             % (V['fz'], V['fp'], V['CTRs'], V['RFB'], V['RI'], V['RB'],
                V['EAo'], V['CFoc'], V['CFo'])))
    add(calc([r'C_{F}=%.0f\ \mathrm{nF}\times\left(\frac{%.2f}{%.3f}-1\right)'
              r'=%.0f\ \mathrm{nF}\;\rightarrow\;\mathbf{%.0f\ nF}'
              % (V['CFo'], V['fp'], V['fz'], V['CFc'], V['CF']),
              r'R_{F}=\frac{1}{2\pi\times %.3f\ \mathrm{Hz}\times %.0f\ \mathrm{nF}}'
              r'=%.1f\ \mathrm{k\Omega}\;\rightarrow\;\mathbf{%.0f\ k\Omega}'
              % (V['fz'], V['CF'], V['RFc'], V['RF'])]))
    add(calc(r'C_{fx}=\frac{1}{2\pi\times %.0f\ \mathrm{Hz}\times %.0f\ \mathrm{k\Omega}}'
             r'-%.0f\ \mathrm{nF}=%.3f\ \mathrm{nF}\;\rightarrow\;\mathbf{%.2f\ nF}'
             % (V['fpHF'], V['RFB'], V['Copto'], V['Cfxc'], V['Cfx'])))
    add(p('<b>Step 9 &mdash; what the standard parts give:</b>'))
    add(eqagain('fzp'))
    add(calc([r'EA_{o}=\frac{%.2f\times %.0f\ \mathrm{k\Omega}}'
              r'{(%.0f+%.0f)\ \mathrm{nF}\times %.0f\ \mathrm{k\Omega}\times %.1f\ \mathrm{k\Omega}}'
              r'=\mathbf{%.2f\ rad/s}'
              % (V['CTRs'], V['RFB'], V['CF'], V['CFo'], V['RI'], V['RB'],
                 V['EAoi']),
              r'f_{z}=\frac{1}{2\pi\times %.0f\ \mathrm{k\Omega}\times %.0f\ \mathrm{nF}}'
              r'=\mathbf{%.3f\ Hz}' % (V['RF'], V['CF'], V['fzi'])]))
    add(calc([r'C_{ser}=\frac{%.0f\times %.0f}{%.0f+%.0f}\ \mathrm{nF}=%.1f\ \mathrm{nF},'
              r'\qquad f_{p}=\frac{1}{2\pi\times %.0f\ \mathrm{k\Omega}\times %.1f\ \mathrm{nF}}'
              r'=\mathbf{%.2f\ Hz}'
              % (V['CF'], V['CFo'], V['CF'], V['CFo'], V['Cser'], V['RF'],
                 V['Cser'], V['fpi']),
              r'f_{px}=\frac{1}{2\pi\times %.0f\ \mathrm{k\Omega}\times(%.0f+%.2f)\ \mathrm{nF}}'
              r'=\mathbf{%.0f\ Hz}' % (V['RFB'], V['Copto'], V['Cfx'], V['fpx'])]))
    add(p('<b>Step 10 &mdash; crossover and phase margin.</b> '
          'G<sub>o</sub>EA<sub>o</sub> = %(g0).0f, so the iteration starts at '
          '&omega;<sub>c</sub> = %(w0).1f&nbsp;rad/s and settles at'
          % dict(V, f0=V['w0'] / (2 * pi))))
    add(eqagain('wc'))
    add(calc(r'\omega_{c}=\mathbf{%.1f\ rad/s},\qquad f_{c}=\frac{%.1f}{2\pi}'
             r'=\mathbf{%.2f\ Hz},\qquad |T(\omega_{c})|=%.4f\ \ (\mathrm{check:}\ 1)'
             % (V['wc'], V['wc'], V['fcross'], V['Tres'])))
    add(eqagain('PMeq'))
    add(calc(r'\Phi_{M}=\arctan\frac{%.1f}{%.1f}-\arctan\frac{%.1f}{%.1f}'
             r'-\arctan\frac{%.1f}{%.0f}=%.1f^{\circ}-%.1f^{\circ}-%.1f^{\circ}'
             r'=\mathbf{%.1f^{\circ}}'
             % (V['wc'], V['wz'], V['wc'], V['wp'], V['wc'], V['wpx'],
                _at(V['wc'], V['wz']), _at(V['wc'], V['wp']),
                _at(V['wc'], V['wpx']), V['PM'])))
    add(p('<b>Step 11 &mdash; the gain margin:</b>'))
    add(eqagain('f180'))
    add(calc([r'f_{180}=\sqrt{%.2f\times %.0f-%.3f\times(%.2f+%.0f)}\ \mathrm{Hz}'
              r'=\mathbf{%.0f\ Hz}'
              % (V['fpi'], V['fpx'], V['fzi'], V['fpi'], V['fpx'], V['f180']),
              r'|T(f_{180})|=%.4f,\qquad GM=-20\log_{10}%.4f=\mathbf{%.1f\ dB}'
              % (V['T180'], V['T180'], V['GM'])]))
    add(p('<b>Step 12 &mdash; the third harmonic of the built loop</b>, at '
          '2f<sub>l</sub> = %(f2).0f&nbsp;Hz (&omega; = %(w2fl).1f&nbsp;rad/s):'
          % dict(V, f2=2 * V['flmin'])))
    add(calc(r'G_{EA}(2f_{l})=\frac{%.2f}{%.1f}\cdot'
             r'\frac{\sqrt{1+(%.1f/%.1f)^{2}}}'
             r'{\sqrt{1+(%.1f/%.1f)^{2}}\,\sqrt{1+(%.1f/%.0f)^{2}}}'
             r'=\mathbf{%.4f}\ \ (\leq %.4f)'
             % (V['EAoi'], V['w2fl'], V['w2fl'], V['wz'], V['w2fl'], V['wp'],
                V['w2fl'], V['wpx'], V['GEAact'], V['GEAreq'])))
    add(eqagain('D3'))
    add(calc(r'D_{3}=\frac{%.4f\times %.3f\ \mathrm{V}}{4\times %.3f\ \mathrm{V}}'
             r'=\mathbf{%.2f\ \%%}\ \ (\mathrm{budget}\ %.0f\ \%%)'
             % (V['GEAact'], V['dVloop'], V['VFBv'], V['D3'], V['D3set'])))
    add(p('<b>Step 13 &mdash; the feedback ripple at the burst point</b>, '
          'with burst entry at %(PinBM).0f&nbsp;W:' % V))
    add(eqagain('dVFB'))
    add(calc(r'\Delta V_{FB}=\frac{%.0f\ \mathrm{W}}{%.1f\ \mathrm{V}}\cdot'
             r'\frac{1}{2\pi\times %.0f\ \mathrm{Hz}\times %.1f\ \mathrm{mF}}'
             r'\times %.4f=\mathbf{%.1f\ mV}'
             % (V['PinBM'], V['Vout'], V['flmin'], V['Cout'], V['GEAact'],
                V['dVFBBM'])))
    add(eqagain('dRBM'))
    add(calc(r'\Delta R_{BM}=\frac{%.1f\ \mathrm{mV}}{2\times 0.01\ \mathrm{V/k\Omega}}'
             r'=\mathbf{%.2f\ k\Omega},\qquad R_{BM}=%.0f-%.2f'
             r'=\mathbf{%.1f\ k\Omega}'
             % (V['dVFBBM'], V['dRBM'], V['RBMsel'], V['dRBM'], V['RBMrec'])))
    add(p('The fitted %(RBMsel).0f&nbsp;k&Omega; is kept for now: the burst '
          'entry it is set from is an assumption (Table&nbsp;%(t)s), so '
          'R<sub>BM</sub> is traded against this ripple once the standby '
          'power has been measured (Appendix&nbsp;%(a)s).'
          % dict(V, t=TR('spec-given'), a=SR('Open items in this design'))))
    add(fig('an_loop_bode',
            '|T| and 180&deg; + arg&nbsp;T of the loop as built. The second '
            'trace is the phase margin only at the crossover; the gain margin '
            'is read at f<sub>180</sub>.'))
    ext(tbl('The voltage loop, as built.',
            [['Quantity', 'Value', 'Against'],
             ['Divider R<sub>I</sub> / R<sub>O</sub>',
              '%(RI).0f / %(Ro).0f k&Omega;' % V,
              'regulates to %(VoutAct).2f V' % V],
             ['Bias R<sub>P</sub>, R<sub>B</sub>',
              '%(RP).1f k&Omega;, %(RB).1f k&Omega;' % V,
              'R<sub>P</sub> &le; %(RPmax).2f k&Omega;; R<sub>B</sub> in '
              '%(RBmin).2f to %(RBmax).2f k&Omega;' % V],
             ['Compensation C<sub>Fo</sub>, C<sub>F</sub>, R<sub>F</sub>, '
              'C<sub>fx</sub>',
              '%(CFo).0f nF, %(CF).0f nF, %(RF).0f k&Omega;, %(Cfx).2f nF' % V,
              'zero %(fzi).2f Hz, pole %(fpi).1f Hz, pole %(fpx).0f Hz' % V],
             ['Crossover f<sub>c</sub>', '%(fcross).2f Hz' % V,
              'the 15 to 20 Hz this topology lands in'],
             ['Phase margin', '%(PM).1f&deg;' % V,
              'target %(PhiM).0f&deg;, floor 45&deg;' % V],
             ['Gain margin', '%(GM).1f dB at %(f180).0f Hz' % V,
              '6 dB floor, %(GMt).0f dB comfortable' % V],
             ['Third harmonic on the input current', '%(D3).2f %%' % V,
              'budget %(D3set).0f %%' % V],
             ['Feedback ripple at the burst point',
              '%(dVFBBM).0f mV' % V,
              'clears the burst threshold if R<sub>BM</sub> moves from the fitted '
              '%(RBMsel).0f k&Omega; to %(RBMrec).1f k&Omega;' % V]],
            widths=[CW * 0.34, CW * 0.28, CW * 0.38], key='loop-result', split=True))

    # ------------------------------------------------ the controller network
    add(h2('The parts around the controller'))
    add(p('The results; the following sections derive each value in the '
          'order it has to be done.'))
    ext(tbl('Controller network for the worked design.',
            [['Part', 'Value', 'Result'],
             ['C<sub>T</sub> / R<sub>T</sub>',
              '%(CT).0f pF / %(RT).0f k&Omega;' % V,
              'f<sub>Min</sub> %(fMin).1f kHz, f<sub>Max</sub> %(fMax).1f kHz'
              % V],
             ['R<sub>CS</sub>', '%(RCS).1f m&Omega; (%(RCS1).0f m&Omega; '
              '&times; %(nR).0f in parallel)' % dict(V, nR=A.SH['N.RCS']),
              'OCP1 at %(kOCP).3f &times; the composite peak' % V],
             ['R<sub>CFG</sub>', '%(RCFG).0f k&Omega;' % V,
              'V<sub>BO</sub> %(pk).0f V peak (%(VBO).1f Vac rms), morphing enabled' % dict(V, pk=V['VBO'] * 2 ** 0.5)],
             ['R<sub>BM</sub>', '%(RBM).0f k&Omega;' % V,
              'burst-mode entry point'],
             ['ZCD divider', '%(RZH).0f k&Omega; / %(RZL).0f k&Omega;' % V,
              'OVP1 %(OVP1).2f V, OVP2 %(OVP2).2f V' % V],
             ['C<sub>in</sub>', '%(Cin).0f nF film' % V,
              'about %.1f nF/W &mdash; there is no bulk capacitor'
              % (V['Cin'] / V['Pin'])],
             ['V<sub>CC</sub> regulator',
              'Zener %.0f V, R<sub>BZ</sub> %.0f &Omega;, C<sub>VCC</sub> '
              '%.0f &micro;F' % (V['DZ'], V['RBZ'], V['CVCC']),
              'V<sub>CC</sub> %.2f V (%.2f to %.2f V) from N<sub>aux</sub> '
              '%d T' % (A.SH['V.CC_reg'], A.SH['V.CC_reg_min'],
                        A.SH['V.CC_reg_max'], V['Naux'])],
             ['Compensation',
              '%(CFo).0f nF / %(CF).0f nF / %(RF).0f k&Omega; / %(Cfx).2f nF'
              % V,
              'f<sub>c</sub> %(fcross).2f Hz, &Phi;<sub>M</sub> '
              '%(PM).2f&deg;' % V]],
            widths=[CW * 0.20, CW * 0.34, CW * 0.46], split=True))

    add(h2('The oscillator: C<sub>T</sub> first, then R<sub>T</sub>'))
    add(p('The VCO charges C<sub>T</sub> from V<sub>ref</sub>/R<sub>T</sub> '
          'plus the error-amplifier current I<sub>EA</sub> up to '
          'V<sub>ref</sub>&nbsp;=&nbsp;1.5&nbsp;V, then adds a fixed idle '
          'time:'))
    add(eq(r'\frac{T_{sw}}{2}=\frac{C_{T}V_{ref}}'
           r'{\frac{V_{ref}}{R_{T}}+I_{EA}}+T_{idle}', key='Tsw'))
    add(p('<b>I<sub>EA</sub> is the only control input.</b> More current, '
          'higher frequency, less power. C<sub>T</sub> is chosen first '
          'because it sets the <i>span</i>, R<sub>T</sub> after it because it '
          'sets the <i>floor</i>:'))
    add(eq(r'C_{T,max}=\frac{I_{EA,max}}{2V_{ref}}\cdot'
           r'\frac{(1-2T_{idle}f_{sw,max,op})(1-2T_{idle}f_{sw,min})}'
           r'{f_{sw,max,op}-f_{sw,min}}\,,\qquad '
           r'C_{T,min}=\frac{1}{R_{T,max}}'
           r'\left(\frac{1}{2f_{sw,min}}-T_{idle}\right)', key='CT'))
    add(eq(r'R_{T,ceil}=\frac{1}{C_{T}}'
           r'\left(\frac{1}{2f_{sw,min}}-T_{idle}\right)', key='RTceil'))
    add(p('with f<sub>sw,min</sub> = f<sub>o</sub>&nbsp;=&nbsp;'
          '%(fo).1f&nbsp;kHz; f<sub>sw,max,op</sub>&nbsp;=&nbsp;'
          '%(fop).1f&nbsp;kHz, the highest frequency the converter actually '
          'runs at (the full-bridge edge at the line peak), not the '
          '%(fswspec).0f&nbsp;kHz specification; I<sub>EA,max</sub>&nbsp;=&nbsp;'
          '400&nbsp;&micro;A, V<sub>ref</sub>&nbsp;=&nbsp;1.5&nbsp;V and '
          'T<sub>idle</sub>&nbsp;=&nbsp;%(Tidle).0f&nbsp;ns:' % dict(V, fop=A.SH['f.sw_max_des'])))
    add(calc(r'C_{T,max}=\frac{400\times10^{-6}}{2\cdot1.5}\cdot'
             r'\frac{(1-2\cdot%(t).0f\!\times\!10^{-9}\cdot'
             r'%(fmx).1f\!\times\!10^{3})'
             r'(1-2\cdot%(t).0f\!\times\!10^{-9}\cdot'
             r'%(fmn).1f\!\times\!10^{3})}'
             r'{(%(fmx).1f-%(fmn).1f)\times10^{3}}'
             r'=%(CTmax).0f\;\mathrm{pF}'
             % dict(t=V['Tidle'], fmx=A.SH['f.sw_max_des'], fmn=V['fo'],
                    CTmax=A.SH['C.T_max'])))
    add(p('and the floor condition, f<sub>Min</sub> brought down to f<sub>o</sub> '
          'with R<sub>T</sub> at its 30&nbsp;k&Omega; maximum, gives '
          'C<sub>T,min</sub>&nbsp;=&nbsp;%(CTmin).0f&nbsp;pF. '
          'The datasheet allows 270 to 1000&nbsp;pF, so the window is '
          '%(lo).0f to %(CTmax).0f&nbsp;pF, and the part is taken from its '
          'middle: <b>C<sub>T</sub> = %(CT).0f&nbsp;pF</b>, C0G. Then'
          % dict(V, CTmin=A.SH['C.T_min'], CTmax=A.SH['C.T_max'],
                 lo=max(270.0, A.SH['C.T_min']))))
    add(calc(r'R_{T,ceil}=\frac{1}{%(CT).0f\times10^{-12}}'
             r'\left(\frac{1}{2\cdot%(fo).1f\times10^{3}}'
             r'-%(t).0f\times10^{-9}\right)'
             r'=%(RTceil).2f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(RT).0f\;\mathrm{k\Omega}'
             % dict(V, t=V['Tidle'], RTceil=A.SH['R.T_ceil'] / 1e3)))
    add(note('<b>R<sub>T,ceil</sub> is a maximum.</b> f<sub>Min</sub> '
             '<i>falls</i> as R<sub>T</sub> grows, so rounding up drops the '
             'clamp below f<sub>o</sub>. Round it <b>down</b>.'))
    add(p('The selected pair produces'))
    add(eq(r'f_{Min}=\frac{1}{2(C_{T}R_{T}+T_{idle})}\,,\qquad '
           r'f_{Max}=\frac{1}{2\left(\frac{C_{T}}'
           r'{\frac{I_{EA,max}}{V_{ref}}+\frac{1}{R_{T}}}+T_{idle}\right)}', key='fMinMax'))
    add(p('f<sub>Min</sub>&nbsp;=&nbsp;1/[2(%(CT).0f&nbsp;pF&times;%(RT).0f'
          '&nbsp;k&Omega; + %(Ts).2f&nbsp;&micro;s)] = '
          '<b>%(fMin).2f&nbsp;kHz</b>, which must clear f<sub>o</sub>.'
          % dict(V, Ts=V['Tidle'] / 1e3)))
    ext(tbl('Oscillator: what the two parts produce, and the limits each '
            'result has to clear.',
            [['Quantity', 'Value', 'Limit', 'Margin'],
             ['f<sub>Min</sub>', '%(fMin).1f kHz' % V,
              'above f<sub>o</sub> = %(fo).1f kHz' % V,
              '%(kfloor).3f' % V],
             ['f<sub>Max</sub>', '%(fMax).1f kHz' % V,
              'above the highest operating f<sub>sw</sub> = %(fswmaxop).1f kHz (FB edge, line peak)' % V,
              '%(kceil).3f' % V],
             ['f<sub>SU</sub>', '%(fSU).1f kHz' % dict(V, fSU=A.SH['f.SU']),
              'below the 675 kHz silicon ceiling', '%(kSU).3f'
              % dict(V, kSU=A.SH['k.SU'])],
             ['R<sub>T</sub>C<sub>T</sub>',
              '%(tau).2f &micro;s' % dict(V, tau=A.SH['τ.RT']),
              '2.5 to 12 &micro;s', '%(a).3f / %(b).3f'
              % dict(a=A.SH['k.tau_lo'], b=A.SH['k.tau_hi'])],
             ['R<sub>T</sub>', '%(RT).0f k&Omega;' % V, '5 to 30 k&Omega;',
              '%(a).3f / %(b).3f'
              % dict(a=A.SH['k.RT_lo'], b=A.SH['k.RT_hi'])],
             ['C<sub>T</sub>', '%(CT).0f pF' % V, '270 to 1000 pF',
              '%(a).3f / %(b).3f'
              % dict(a=A.SH['k.CT_lo'], b=A.SH['k.CT_hi'])]],
            widths=[CW * 0.18, CW * 0.20, CW * 0.44, CW * 0.18], split=True))
    add(note('<b>T<sub>idle</sub> is the weakest number in this chapter.</b> '
             'The draft datasheet implies 700&nbsp;ns in its frequency '
             'expressions and 350&nbsp;ns in its C<sub>T,max</sub> '
             'expression, and its Table&nbsp;2 back-solves to about '
             '250&nbsp;ns; this design uses '
             '%(Tidle).0f&nbsp;ns. At 700&nbsp;ns f<sub>Min</sub> would be '
             '%(a).1f&nbsp;kHz, below f<sub>o</sub>, and f<sub>Max</sub> '
             '%(b).1f&nbsp;kHz against the %(c).1f&nbsp;kHz the FB edge '
             'needs. Measure it first.'
             % dict(V, a=_f_idle(V, 700.0)[0], b=_f_idle(V, 700.0)[1],
                    c=V['fswmaxop'])))

    add(h2('The current-sense resistor, which sets three things at once'))
    add(p('Two conditions, the smaller wins:'))
    add(eq(r'R_{CS,max1}=\frac{16.8\,\Omega\!\cdot\!\mathrm{W}}{P_{in}}'
           r'\qquad\qquad '
           r'R_{CS,max2}=\frac{0.55\,\mathrm{V}}{I_{Lr,pk}}', key='RCS'))
    add(p('The first is the maximum-power law (Section&nbsp;'
          + SR('The feedback pin is a power command')
          + '), the second the OCP1 trip point. The first is written with '
          'P<sub>in</sub>, as the datasheet writes it, not with the '
          'P<sub>in,LLC</sub> the pin senses; that is %.0f&nbsp;%% '
          'conservative:' % (100 * (V['Pin'] / _SH['P.in_LLC'] - 1))))
    add(calc(r'R_{CS,max1}=\frac{16.8}{%(Pin).1f}=%(a1).5f\;\Omega'
             r'=%(a).2f\;\mathrm{m\Omega}\,,\qquad '
             r'R_{CS,max2}=\frac{0.55}{%(Ipk).2f}=%(b1).5f\;\Omega'
             r'=%(b).2f\;\mathrm{m\Omega}'
             % dict(Pin=V['Pin'], a1=A.SH['R.CS1'] / 1e3, a=A.SH['R.CS1'],
                    Ipk=V['Icomp'], b1=A.SH['R.CS2'] / 1e3,
                    b=A.SH['R.CS2'])))
    add(p('so the power law limits. Dissipation at the worst switching cycle '
          'fixes how many resistors share it:'))
    add(calc(r'P_{CS}=I_{pri,rms}^{2}R_{CS}=(%(I).2f)^{2}\cdot%(R).1f'
             r'\times10^{-3}=%(P).2f\;\mathrm{W}'
             r'\;\Rightarrow\;N=%(N).0f\;\mathrm{in\;parallel}'
             % dict(I=V['Iprims'], R=V['RCS'], P=A.SH['P.RCS_pk'],
                    N=A.SH['N.RCS'])))
    add(p('%(N).0f &times; %(R1).0f&nbsp;m&Omega; in parallel give '
          '<b>R<sub>CS</sub> = %(RCS).1f&nbsp;m&Omega;</b>.'
          % dict(V, N=A.SH['N.RCS'], R1=A.SH['R.CS_single'])))
    add(note('R<sub>CS</sub> sits in the bridge return, so R<sub>CS,max2</sub> '
             'uses the composite peak. I<sub>trafo,pk</sub> = %(Itr).2f&nbsp;A '
             'instead of I<sub>Lr,pk</sub> = %(Icomp).2f&nbsp;A would loosen '
             'the over-current protection by about %(pc).0f&nbsp;%%.'
             % dict(V, pc=100 * (V['Icomp'] / V['Itr'] - 1))))
    ext(tbl('What the selected R<sub>CS</sub> then fixes.',
            [['Result', 'Value', 'Against'],
             ['Maximum input power', '%(P).1f W'
              % dict(P=A.SH['P.in_max_act']),
              'P<sub>in</sub> = %(Pin).1f W' % V],
             ['OCP1 trip', '%(I).2f A' % dict(I=A.SH['I.OCP1']),
              'composite peak %(Icomp).2f A, margin %(kOCP).3f' % V],
             ['OCP2 trip', '%(I).2f A' % dict(I=A.SH['I.OCP2']),
              'switching stops at once; restart after 50 &micro;s at f<sub>SU</sub>'],
             ['Sense dissipation, worst switching cycle', '%(P).2f W total, %(Pe).3f W each'
              % dict(P=A.SH['P.RCS_pk'], Pe=A.SH['P.RCS_each_pk']),
              '1 W parts, margin %(k).3f' % dict(k=A.SH['k.NRCS'])]],
            widths=[CW * 0.26, CW * 0.26, CW * 0.48], split=True))

    add(h2('Burst mode: one resistor, read once at power-up'))
    add(eq(r'R_{BM}=16.7\,\frac{\mathrm{k}\Omega}{\mathrm{V}^{2}}'
           r'\,R_{CS}\,P_{in,BM}\,,\qquad '
           r'V_{BM,eq}=0.01\,\frac{\mathrm{V}}{\mathrm{k}\Omega}\,R_{BM}+0.5\,\mathrm{V}', key='RBM'))
    add(p('Burst starts at P<sub>in,BM</sub> = %(rBM).0f&nbsp;%% &times; '
          '%(Pin).1f&nbsp;W = %(PinBM).1f&nbsp;W:'
          % dict(V, rBM=100 * A.SH['r.BM'],
                 PinBM=A.SH['r.BM'] * V['Pin'])))
    add(calc(r'R_{BM}=16.7\cdot%(R).1f\times10^{-3}\cdot%(P).1f'
             r'=%(RB).1f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(sel).0f\;\mathrm{k\Omega}\,,\qquad '
             r'V_{BM,eq}=0.01\times %(sel).0f+0.5=%(V).3f\;\mathrm{V}'
             % dict(R=V['RCS'], P=A.SH['r.BM'] * V['Pin'], RB=A.SH['R.BM'],
                    sel=A.SH['R.BM_sel'], V=A.SH['V.BM_eq'])))
    add(p('Valid range 15 to 140&nbsp;k&Omega;; tied to ground, burst mode '
          'is off. Check this threshold against the feedback ripple '
          '(Section&nbsp;'
          + SR('Feedback ripple against the burst threshold')
          + ') or the converter chatters in and out of burst.'))

    add(h2('Brown-out and bridge configuration: the CFG pin'))
    add(p('One resistor, two jobs, both read at power-up:'))
    add(eq(r'V_{BO,pk}=R_{CFG}\times 4\,\frac{\mathrm{V}}{\mathrm{k}\Omega}'
           r'\,,\qquad V_{BO,rms}=\frac{V_{BO,pk}}{\sqrt{2}}', key='VBO'))
    add(p('Brown-out is compared against the <i>peak</i> of the mains, so '
          'the &radic;2 is easy to drop. Brown-out just below the lowest '
          'input voltage:'))
    add(calc(r'R_{CFG,max}=\frac{\sqrt{2}\cdot%(Vac).0f}{4}'
             r'=%(max).2f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(sel).0f\;\mathrm{k\Omega}'
             % dict(Vac=V['Vacmin'], max=A.SH['R.CFG_max'] / 1e3,
                    sel=V['RCFG'])))
    add(p('That is a maximum, so it rounds down; the selected part sets'))
    add(calc(r'V_{BO,rms}=\frac{%(R).0f\cdot4}{\sqrt{2}}'
             r'=%(V).2f\;\mathrm{Vac}'
             % dict(R=V['RCFG'], V=V['VBO'])))
    add(p('against a %(Vacmin).0f&nbsp;Vac minimum, margin %(k).3f. Rounding '
          'up would stop the converter starting at the lowest input voltage.'
          % dict(V, k=A.SH['k.BO'])))
    ext(tbl('What R<sub>CFG</sub> and LOUT2 select together. The 235 and '
            '245 V thresholds are fixed inside the IC and cannot be moved.',
            [['R<sub>CFG</sub>', 'LOUT2', 'Configuration'],
             ['15 k&Omega;', 'open',
              'morphing, fixed brown-out: off below 60 V peak, on above 70 V peak'],
             ['15 to 47 k&Omega;', 'open',
              '<b>morphing, adjustable brown-out &mdash; this design</b>'],
             ['47 to 100 k&Omega;', 'open', 'fixed full bridge'],
             ['15 k&Omega;', 'to GND',
              'fixed half bridge, split C<sub>r</sub>, fixed brown-out'],
             ['15 to 100 k&Omega;', 'to GND',
              'fixed half bridge, split C<sub>r</sub>, adjustable brown-out']],
            widths=[CW * 0.20, CW * 0.14, CW * 0.66], split=True))
    add(note('For universal input the window is 15&nbsp;k&Omega; to '
             '%(max).1f&nbsp;k&Omega;; the 47&nbsp;k&Omega; morphing limit '
             'never applies. Hang nothing on LOUT2: a pull-down under about '
             '8&nbsp;k&Omega; reads as fixed half bridge.'
             % dict(max=A.SH['R.CFG_max'] / 1e3)))

    add(h2('Output sensing and over-voltage: the ZCD divider'))
    add(p('The divider ratio alone sets both over-voltage thresholds; the '
          'absolute values only set the bias current:'))
    add(eq(r'R_{ZCD,L}=\frac{2.3\,\mathrm{V}}{I_{bias}}\,,\qquad '
           r'R_{ZCD,H}=R_{ZCD,L}\left('
           r'\frac{n_{aux}}{n_{sec}}\frac{V_{OVP1,out}}{2.3\,\mathrm{V}}'
           r'-1\right)', key='RZCD'))
    add(eq(r'V_{OVP1}=\frac{2.3\,\mathrm{V}}{n_{aux}/n_{sec}}'
           r'\left(\frac{R_{ZCD,H}}{R_{ZCD,L}}+1\right)\,,\qquad '
           r'V_{OVP2}=\frac{2.5}{2.3}\,V_{OVP1}', key='OVP'))
    add(p('OVP1 %(pc).0f&nbsp;%% above the output is %(t).2f&nbsp;V. The '
          'lower resistor comes from the bias current, %(ib).0f&nbsp;&micro;A, '
          'the upper from the ratio, with n<sub>aux</sub>/n<sub>sec</sub> = '
          '%(naux).1f:'
          % dict(V, pc=100 * (A.SH['V.OVP1_out'] / V['Vout'] - 1),
                 t=A.SH['V.OVP1_out'], naux=A.SH['n.aux'],
                 ib=2.3 / A.SH['R.ZCD_L'] * 1e3)))
    add(calc(r'R_{ZCD,L}=\frac{2.3}{%(ib).0f\times10^{-6}}'
             r'=%(rl).2f\;\mathrm{k\Omega}\;\rightarrow\;'
             r'%(RZL).0f\;\mathrm{k\Omega}'
             % dict(V, ib=2.3 / A.SH['R.ZCD_L'] * 1e3,
                    rl=A.SH['R.ZCD_L'])))
    add(calc(r'R_{ZCD,H}=%(RZL).0f\left(\frac{%(naux).1f\cdot%(t).1f}'
             r'{2.3}-1\right)=%(rh).1f\;\mathrm{k\Omega}'
             r'\;\rightarrow\;%(RZH).0f\;\mathrm{k\Omega}'
             % dict(V, naux=A.SH['n.aux'], t=A.SH['V.OVP1_out'],
                    rh=A.SH['R.ZCD_H'])))
    add(p('The upper resistor is the <i>next E24 value above</i> the '
          'calculation, so OVP1 lands clear of the ripple crest. The fitted '
          'pair gives'))
    add(calc(r'V_{OVP1}=\frac{2.3}{%(naux).1f}'
             r'\left(\frac{%(RZH).0f}{%(RZL).0f}+1\right)'
             r'=%(OVP1).2f\;\mathrm{V}\,,\qquad '
             r'V_{OVP2}=\frac{2.5}{2.3}\cdot%(OVP1).2f'
             r'=%(OVP2).2f\;\mathrm{V}'
             % dict(V, naux=A.SH['n.aux'])))
    add(p('Start-up hands over to the loop when the ZCD pin reaches '
          '%(zs).2f&nbsp;V, the datasheet&rsquo;s start-up end threshold. '
          'Through the same divider that is %(zs).2f/2.3 of the OVP1 output '
          'voltage: %(su).2f&nbsp;V of output.'
          % dict(V, su=A.SH['V.out_SUend'], zs=A._builder_const('V.ZCD_SUend'))))
    add(note('Swapping the two resistors makes OVP1 trip below a volt of '
             'output, so the converter never starts. Reversed winding '
             'polarity makes the bridge hard switch from the first pulse.'))
    add(note('Wired straight to V<sub>CC</sub>, this winding would put '
             '%(vo).2f&nbsp;V on the pin at OVP2, over its 25&nbsp;V rating; '
             'the ST tool&rsquo;s ratio test reads %(k).3f. The regulator of '
             'the next section is why that does not matter here.'
             % dict(vo=A.SH['n.aux'] * A.SH['V.OVP2_act'], k=A.SH['k.auxr'])))

    add(h2('V<sub>CC</sub> from the auxiliary winding, as built'))
    add(p('There is no external rail. The auxiliary winding is %(Naux)d turns '
          'of triple-insulated wire over the secondary, n<sub>aux</sub> = '
          '%(na).1f, so it sits at the output voltage: %(va).1f&nbsp;V on the '
          'winding and %(vc).1f&nbsp;V on its capacitor after the diode. With '
          'a %(DZ).0f&nbsp;V Zener of &plusmn;%(tp).0f&nbsp;%% and '
          'V<sub>BE</sub> = V<sub>D</sub> = %(VFj).1f&nbsp;V assumed, '
          'Equation&nbsp;%(e)s gives'
          % dict(V, na=A.SH['n.aux'], va=A.SH['V.aux'], vc=A.SH['V.Caux'],
                 tp=100 * V['tolDZ'], e=ER('vccreg'))))
    add(calc(r'V_{CC,reg}=%(DZ).0f-%(VFj).1f-%(VFj).1f=%(r).2f\;\mathrm{V}'
             r'\,,\qquad %(lo).2f\ldots%(hi).2f\;\mathrm{V}'
             % dict(V, r=A.SH['V.CC_reg'], lo=A.SH['V.CC_reg_min'],
                    hi=A.SH['V.CC_reg_max'])))
    add(p('The bottom of the band clears V<sub>CC,HVSUon</sub> = '
          '%(hv).0f&nbsp;V by %(k1).3f; the top stays under '
          'the %(mx).0f&nbsp;V operating limit by %(k2).3f. The load is the '
          'controller, %(ICC).0f&nbsp;mA, and %(Nsw).0f switch positions at '
          'the gate charge of the candidate MOSFET, %(Qg).1f&nbsp;nC typical, '
          'bounded at f<sub>Max</sub> (Equation&nbsp;%(e)s):'
          % dict(V, hv=V['VCCHV'], mx=V['VCCmax'], k1=A.SH['k.VCClo'],
                 k2=A.SH['k.VCC'], e=ER('ivcc'))))
    add(calc(r'I_{VCC}=%(ICC).0f\,\mathrm{mA}+%(Nsw).0f\cdot%(Qg).1f'
             r'\,\mathrm{nC}\cdot%(fk).1f\,\mathrm{kHz}'
             r'=%(I).1f\;\mathrm{mA}'
             % dict(V, fk=A.SH['f.Max'], I=A.SH['I.VCC'])))
    add(p('The feed resistor comes from Equation&nbsp;%(e)s at the end of '
          'hold-up, with &beta;<sub>min</sub> = %(b).0f and '
          'I<sub>Z,min</sub> = %(iz).0f&nbsp;mA set as requirements on the '
          'parts:' % dict(e=ER('rbz'), b=V['bmin'], iz=V['IDZmin'])))
    add(calc(r'R_{BZ}\leq\frac{%(na).1f\cdot%(vm).0f-%(VFj).1f-%(zm).2f}'
             r'{%(I).1f/%(b).0f+%(iz).0f}=%(r).3f\;\mathrm{k\Omega}'
             r'\;\rightarrow\;%(RBZ).0f\;\Omega'
             % dict(V, na=A.SH['n.aux'], vm=V['Vomin'], zm=A.SH['V.DZ_max'],
                    I=A.SH['I.VCC'], b=V['bmin'], iz=V['IDZmin'],
                    r=A.SH['R.BZ_max'] / 1e3)))
    add(p('What the two parts burn is set at OVP1, where the capacitor stays '
          'highest, %(c1).2f&nbsp;V: the Zener, with no load to share the '
          'feed current, %(pz).0f&nbsp;mW; the pass transistor, at '
          'I<sub>VCC</sub>, %(pq).2f&nbsp;W (%(pn).2f&nbsp;W at the nominal '
          'output, the figure that goes into the loss account). Both are '
          'ratings to buy, not margins. The transistor must also block %(c2).2f&nbsp;V at OVP2 '
          'plus any spike the winding carries, which only a measurement '
          'gives.' % dict(c1=A.SH['V.Caux_OVP1'], pz=A.SH['P.DZ'],
                          pq=A.SH['P.Qpass'], c2=A.SH['V.Caux_OVP2'],
                          pn=A.SH['P.Qpass_nom'])))
    add(p('<b>Start-up.</b> In full bridge at the start-up frequency the '
          'drivers take'))
    add(calc(r'I_{VCC,SU}=%(ICC).0f\,\mathrm{mA}+%(Nsw).0f\cdot%(Qg).1f'
             r'\,\mathrm{nC}\cdot%(fk).1f\,\mathrm{kHz}'
             r'=%(I).1f\;\mathrm{mA}'
             % dict(V, fk=A.SH['f.SU'], I=A.SH['I.VCC_SU'])))
    add(p('and the winding can hold the pin at V<sub>CCoff</sub> once the '
          'output reaches (V<sub>CCoff</sub> + 3V<sub>D</sub> + '
          'I<sub>VCC,SU</sub>R<sub>BZ</sub>/&beta;<sub>min</sub>)/'
          'n<sub>aux</sub> = %(uv).2f&nbsp;V. Equation&nbsp;%(e)s then gives'
          % dict(uv=A.SH['V.out_UV'], e=ER('cvcc'))))
    add(calc(r't_{hand}=\frac{%(co).1f\cdot%(uv).2f}{%(Iout).1f}'
             r'=%(th).1f\;\mathrm{ms}'
             % dict(V, co=A.SH['C.out'], uv=A.SH['V.out_UV'],
                    th=A.SH['t.hand'])))
    add(calc(r'C_{VCC}\geq\frac{%(th).1f}{\dfrac{%(VCCon).0f-%(VCCHV).0f}'
             r'{%(I).1f}+\dfrac{%(VCCHV).0f-%(VCCoff).0f}{%(I).1f-%(IHVlo).0f}}'
             r'=%(cr).0f\;\mathrm{\mu F}\;\rightarrow\;%(CVCC).0f\;'
             r'\mathrm{\mu F}'
             % dict(V, th=A.SH['t.hand'], I=A.SH['I.VCC_SU'],
                    cr=A.SH['C.VCC_req'])))
    add(p('The hand-over falls well inside the %(t).0f&nbsp;ms the start-up '
          'unit stays available. The price is the delay before the first '
          'pulse, %(d).2f&nbsp;s at 230&nbsp;Vac, during which the start-up '
          'unit carries the whole charge; check its temperature on the '
          'prototype.' % dict(t=V['tHVSU'], d=A.SH['t.VCCchg'])))
    add(note('t<sub>hand</sub> assumes the set holds its load off until the '
             'rail is up, as a TV sequences its panel. Any load during '
             'start-up stretches it, and C<sub>VCC</sub> with it.'))
    ext(bullets([
        '<b>HVSU connects ahead of the bridge</b>, on the ac side, through '
        'one 1000&nbsp;V diode per line; behind the bridge X-capacitor '
        'discharge and brown-out detection both stop working.',
        '100&nbsp;nF at the pin, beside C<sub>VCC</sub>.']))

    # =============================================================== 7
    add(h2('Controller pin rules'))
    ext(tbl('Pin rules that must not be broken.',
            [['Pin', 'Rule'],
             ['ISEN', 'No filter and no series resistor. The maximum-power '
              'law and the over-current threshold share this pin.'],
             ['CFG, BM', 'No capacitor. Both are strapped at power-up. An '
              'out-of-range CFG resistor latches the controller off.'],
             ['DRV_EN, RT', 'No capacitor. Both are sampled briefly every few '
              'milliseconds and a capacitor is read as a fault.'],
             ['LOUT2', 'No pull-down if morphing is used. A few kilohms to '
              'ground reads as a fixed half bridge.'],
             ['HVSU', 'Connect ahead of the input bridge, on the ac side. '
              'Behind the bridge, both X-capacitor discharge and brown-out '
              'detection stop working.'],
             ['ZCD', 'Auxiliary winding polarity must make ZCD positive when '
              'the low side of leg 1 is on. Reversed, the bridge hard '
              'switches.'],
             ['HOUTx, LOUTx', 'Logic-level outputs, not gate drivers. '
              'External half-bridge drivers are required.']],
            widths=[CW * 0.16, CW * 0.84], split=True))

    add(h2('Protections, and where each threshold is set'))
    add(p('Each threshold is fixed by a resistor already chosen, so a change '
          'made for one reason moves a threshold set for another.'))
    ext(tbl('Protections and the component that sets each one.',
            [['Protection', 'Set by', 'This design'],
             ['Brown-out, on the rectified mains',
              'R<sub>CFG</sub>, read at power-up',
              'V<sub>BO</sub> %(pk).0f V peak = %(VBO).1f Vac rms, clear of the '
              '%(Vacmin).0f Vac minimum by %(kBO).3f' % dict(V, kBO=A.SH['k.BO'], pk=V['VBO'] * 2 ** 0.5)],
             ['First-level over-current, OCP1: raises the switching frequency',
              'R<sub>CS</sub> &mdash; the same resistor as the '
              'maximum-power law',
              '%(IOCP1).2f A against a composite peak of %(Icomp).2f A, '
              'a margin of %(kOCP).3f'
              % dict(V, IOCP1=A.SH['I.OCP1'])],
             ['Second-level over-current, OCP2',
              'R<sub>CS</sub>, fixed ratio to OCP1',
              '%(IOCP2).2f A' % dict(V, IOCP2=A.SH['I.OCP2'])],
             ['Output over-voltage, OVP1',
              'the ZCD divider on the auxiliary winding',
              '%(OVP1).2f V, above the ripple crest and below OVP2' % V],
             ['Second-level over-voltage, OVP2',
              'the same divider',
              '%(OVP2).2f V' % V],
             ['Capacitive-mode protection',
              'internal, on the ISEN pin: ACP-soft raises the frequency, ACP-hard '
              'stops for 50 &micro;s and restarts at the maximum frequency',
              'the last line of defence only &mdash; the frequency floor '
              'f<sub>Min</sub> is the first'],
             ['Burst mode at light load',
              'R<sub>BM</sub>, read at power-up',
              '%(RBM).0f k&Omega;; the 2f<sub>l</sub> feedback ripple is '
              '%(dVFBBM).0f mV, so see Section&nbsp;' % V
              + SR('Feedback ripple against the burst threshold')],
             ['Loss of ZVS at the worst corner',
              'not a protection &mdash; a design margin',
              'swept, not estimated; Section&nbsp;'
              + SR('ZVS verification')]],
            widths=[CW * 0.24, CW * 0.30, CW * 0.46], split=True))

    add(h2('System design rules'))
    add(p('The same material as a checklist.'))
    ext(bullets([
        '<b>Design the tank at the equivalent range</b>, %(Veqlo).1f to '
        '%(Veqhi).1f&nbsp;Vac, not at the mains range.' % V,
        '<b>Expect &lambda; near 0.5.</b> A two-stage inductance ratio '
        'cannot reach the gain at the lowest input voltage.',
        '<b>Keep f<sub>Min</sub> above f<sub>o</sub></b>; the anti-capacitive '
        'protection is the last line, not the first.',
        '<b>Size the output bank from ripple and hold-up</b>, take the '
        'larger, then check the rms ripple current separately.',
        '<b>Crossover in the tens of hertz</b>; handle the surviving '
        'feedback ripple with R<sub>BM</sub>, not a faster loop.',
        '<b>Measure both morphing edges</b> at full and light load.',
        '<b>Check the turns ratio as n&thinsp;V<sub>o,eff</sub></b>, never '
        'as a bare ratio.',
        '<b>Judge over-current on the composite tank peak.</b>',
        '<b>Include the 2f<sub>l</sub> component</b> in the capacitor ripple '
        'current; judge a centre tap at the output node.',
        '<b>Carry &radic;d into the secondary rms</b>; dropping it overstates '
        'the loss by about %.0f&nbsp;%% here.' % _d_overstate(A),
        '<b>Put L<sub>open</sub> and L<sub>short</sub> on the transformer '
        'drawing</b> beside the turns.',
        '<b>ESR at each current component&rsquo;s own frequency</b>: '
        'switching and 2f<sub>l</sub>.',
        '<b>Recheck ZVS after raising L<sub>m</sub>.</b>',
        '<b>Verify ZVS by sweeping the selected tank</b>; the closed form '
        'has no fixed error sign.',
        '<b>Record calculated and selected values separately</b>, and make '
        'every downstream check read the selected one.',
        '<b>Estimate the leakage before the insulation is placed.</b> If a '
        'gap carries the reinforced insulation it cannot be narrower than '
        'the creepage, and Equation&nbsp;%s then puts a floor under '
        'L<sub>short</sub>. Where that floor is above L<sub>r</sub>, put the '
        'insulation in the wire, and check the section winding against '
        'L<sub>r</sub> again before the tank is fixed.' % ER('leak'),
        '<b>Foil only in a concentric winding.</b> Between sections the '
        'leakage field crosses the window and the face of a foil.',
        '<b>An auxiliary winding that feeds V<sub>CC</sub></b>: take the '
        'lowest whole-turn ratio that still regulates at the end of hold-up, '
        'and size C<sub>VCC</sub> for the start-up hand-over, not for the '
        'steady state.']))

    add(h2('What to measure first on hardware'))
    add(p('In order; the first four decide whether the design is sound.'))
    ext(bullets([
        '<b>f<sub>sw</sub>(&theta;) over a line half cycle.</b> It settles '
        'T<sub>idle</sub> and both oscillator clamps, the thinnest margin in '
        'the design.',
        '<b>Cold start into the full %(Cout).1f&nbsp;mF bank.</b> The '
        'start-up window is finite and this risk is new to the '
        'architecture.' % V,
        '<b>ZVS at the half-bridge edge</b> (245&nbsp;V<sub>pk</sub>, full '
        'load): calculated %(cTzc).0f&nbsp;ns against %(tD).0f&nbsp;ns. '
        'Then the worst point of the sweep, %(zLoad).0f&nbsp;%% load, '
        '%(zAt)s, %(zTzc).0f&nbsp;ns, which is the '
        'figure this design is held to.'
        % dict(V, zAt=_where(ZVS_WORST['zVin'], A.R), **ZVS_WORST),
        '<b>Switching frequency at the full-bridge edge</b> '
        '(235&nbsp;V<sub>pk</sub>, full load): calculated %(fswB).1f&nbsp;kHz; '
        'it must not hit the VCO ceiling.' % V,
        '<b>Input current and THD at %(Vacmin).0f&nbsp;Vac, full load</b>: '
        'the zero-crossing dead zone.' % V,
        '<b>Output ripple against what the load tolerates.</b>',
        '<b>Ripple current and temperature rise in the bank</b>: '
        '%(ICout).2f&nbsp;A rms calculated, %(Icout1).2f&nbsp;A per part.' % V,
        '<b>Device temperatures</b>, in <b>half-bridge morphing</b> above '
        '245&nbsp;V<sub>pk</sub>, where the standing device dissipates most. '
        'This decides the accepted loss-budget shortfall.',
        '<b>Feedback ripple against the burst threshold</b> at light load.',
        '<b>An ac dropout at the ripple trough</b>: output still above '
        '%(Vomin).0f&nbsp;V after %(Thold).0f&nbsp;ms.' % V,
        '<b>A step across the morphing band</b>, both directions.',
        '<b>V<sub>CC</sub> and the auxiliary voltage against the output</b>, '
        'at no load, at full load and through a cold start: whether the '
        'winding follows the output, and when it takes over from '
        'C<sub>VCC</sub>.',
        '<b>The transformer&rsquo;s working voltage and an electric-strength '
        'test</b> on the first samples, before they go to the certifying '
        'body.']))

    # =============================================================== 8
    add(h1('List of symbols'))
    add(p('The symbols used in this note. The controller&rsquo;s own '
          'electrical parameters are in its datasheet.'))
    _SYM = [
        ('<b>The tank and its gain</b>', ''),
        ('C<sub>r</sub>, L<sub>r</sub>, L<sub>m</sub>', 'resonant capacitor, series inductance and magnetising inductance of the tank model'),
        ('Z<sub>0</sub>, Z<sub>0,design</sub>', 'characteristic impedance &radic;(L<sub>r</sub>/C<sub>r</sub>); the value the tank is designed to, R<sub>ac</sub>Q<sub>ZVS</sub>'),
        ('Z<sub>in</sub>', 'input impedance the bridge drives; arg Z<sub>in</sub> = 0 is the capacitive boundary'),
        ('f<sub>r</sub>, f<sub>o</sub>', 'series resonance, and the lower resonance with L<sub>m</sub> included'),
        ('f<sub>sw</sub>, f<sub>n</sub>', 'switching frequency, and the same normalised to f<sub>r</sub>'),
        ('f<sub>sw,max</sub>, f<sub>sw,min</sub>', 'the specified maximum switching frequency, an input to &lambda;; and the lowest frequency the oscillator must reach, f<sub>o</sub> in this design'),
        ('f<sub>sw,max,op</sub>', 'the highest switching frequency the converter actually runs at (the full-bridge edge at the line peak); the oscillator span is sized to it'),
        ('T<sub>sw</sub>, T<sub>r</sub>', 'switching period 1/f<sub>sw</sub>, and the resonant period 1/f<sub>r</sub>'),
        ('&lambda;, m', 'L<sub>r</sub>/L<sub>m</sub>, and (L<sub>r</sub>+L<sub>m</sub>)/L<sub>r</sub> = 1 + 1/&lambda;'),
        ('&lambda;<sub>act</sub>, &lambda;<sub>req</sub>', 'the &lambda; of the selected parts, and the &lambda; the design asked for'),
        ('&lambda;<sub>1</sub>, &lambda;<sub>2</sub>, &lambda;<sub>TD</sub>, &lambda;<sub>3</sub>', 'the four candidate &lambda;: minimum gain, the same with the frequency ceiling, the dead-time condition, and the minimum-frequency condition; the largest binds'),
        ('Q, Q<sub>pk</sub>, Q<sub>ZVS</sub>', 'quality factor Z<sub>0</sub>/R<sub>ac</sub>; its value at the line peak; the cap the ZVS condition puts on it'),
        ('R<sub>ac</sub>', 'the rectifier and load as one resistance at the fundamental'),
        ('v<sub>RI</sub>, v<sub>RI</sub><sup>F</sup>, i<sub>RI</sub>', 'the square voltage at the rectifier input, referred to the primary; its fundamental; and the sine current the tank delivers into the rectifier'),
        ('M', 'tank gain, n V<sub>o,eff</sub> over the drive'),
        ('M<sub>req</sub>, M<sub>pk</sub>', 'the gain the operating point demands, and its value at the line peak'),
        ('M<sub>min</sub>, M<sub>max</sub>', 'in the classic LLC procedure: the gain range the tank must cover, from the input range and the output tolerance'),
        ('M<sub>low</sub>, M<sub>high</sub>', 'the required gain at the low and the high equivalent corner'),
        ('M<sub>OL</sub>, M<sub>&infin;</sub>', 'the gain curve at no load (Q = 0, output open), and the floor 1/(1+&lambda;) it flattens onto'),
        ('M<sub>Z</sub>', 'the gain on the capacitive/inductive boundary (arg Z<sub>in</sub> = 0), traced as Q varies; a little to the right of the gain peaks'),
        ('x, u, q', 'the substitutions that turn the gain equation into a cubic: 1/f<sub>n</sub>&sup2;, sin&sup2;&thinsp;&theta;, and Q<sub>pk</sub>&sup2;u&sup2;'),
        ('d', 'conduction ratio f<sub>sw</sub>/f<sub>r</sub> of the secondary, 1 above resonance'),
        ('n, n<sub>T</sub>', 'equivalent-model turns ratio, and the physical (wound) turns ratio'),
        ('N<sub>rect</sub>', 'devices in the secondary conduction path: 1 centre tap, 2 full bridge'),
        ('V<sub>drive</sub>', 'the amplitude the bridge applies to the tank: the rectified mains in full bridge, half of it in half bridge'),
        ('V<sub>refl</sub>', 'reflected output voltage n V<sub>o,eff</sub>'),
        ('V<sub>o,eff</sub>', 'V<sub>out</sub> + N<sub>rect</sub> V<sub>f</sub>'),
        ('V<sub>f</sub>', 'forward drop of one secondary rectifier'),

        ('<b>The mains, and power factor</b>', ''),
        ('&theta;', 'line phase angle'),
        ('f<sub>l</sub>, f<sub>l,min</sub>, &omega;<sub>l</sub>', 'line frequency, its lowest specified value, and 2&pi;f<sub>l</sub>'),
        ('v<sub>ac</sub>, V<sub>ac</sub>, I<sub>ac</sub>', 'the instantaneous mains voltage, and the rms voltage and current drawn'),
        ('I<sub>1,rms</sub>', 'the rms of the input current&rsquo;s fundamental alone'),
        ('p<sub>in</sub>(t), P', 'instantaneous and average input power'),
        ('v<sub>in</sub>(&theta;), i<sub>in</sub>(&theta;)', 'the rectified mains voltage and the current drawn from it, over the line half cycle'),
        ('PF, THD', 'power factor, and total harmonic distortion of the input current'),
        ('&phi;<sub>1</sub>, D', 'displacement angle of the fundamental, and the distortion factor I<sub>1,rms</sub>/I<sub>ac</sub>'),
        ('D<sub>3</sub>', 'third harmonic on the input current, as a fraction of the fundamental'),
        ('V<sub>in</sub>, V<sub>pk</sub>', 'the rail the bridge works from, and the peak of the mains'),
        ('V<sub>bus</sub>', 'the regulated dc bus between the two stages of a two-stage converter'),
        ('V<sub>ac,eq</sub>, V<sub>ac,eq,low</sub>, V<sub>ac,eq,high</sub>', 'equivalent input voltage the tank sees after morphing, and its value at the two morphing thresholds'),
        ('V<sub>eq,min</sub>, V<sub>eq,max</sub>', 'the lowest equivalent input (the HB edge) and the mains maximum, as the ST tool&rsquo;s margin factor &Gamma;<sub>v</sub> uses them'),

        ('<b>Power and loss</b>', ''),
        ('P<sub>in</sub>, P<sub>out</sub>', 'input power, output power'),
        ('P<sub>LLC</sub>, P<sub>EMI</sub>, P<sub>BR</sub>', 'the three budgeted losses: the LLC stage, the EMI filter, the input bridge'),
        ('P<sub>in,LLC</sub>', 'power into the tank, P<sub>out</sub>/&eta;<sub>HB</sub>'),
        ('&eta;<sub>HB</sub>', 'assumed efficiency of the LLC stage'),
        ('P<sub>mos,dc</sub>', 'conduction loss of the primary device that stands on in half-bridge morphing'),
        ('P<sub>SR</sub>, P<sub>SR,leg</sub>', 'secondary rectifier loss, per device and per rectifier leg'),
        ('P<sub>CS</sub>', 'dissipation in the current-sense resistors'),
        ('P<sub>budget</sub>', 'the loss a device position is allowed, before parts are chosen'),
        ('E, C, V, V<sub>min</sub>', 'the energy a capacitance C gives up between two voltages, in the hold-up expression'),

        ('<b>Currents and times of one switching cycle</b>', ''),
        ('i<sub>Lr</sub>, I<sub>Lr,pk</sub>', 'tank current, and its peak: reflected load plus magnetising'),
        ('i<sub>trafo</sub>, I<sub>trafo,pk</sub>', 'the reflected load current alone, and its peak'),
        ('i<sub>Lm</sub>, I<sub>Lm,pk</sub>', 'magnetising current of the tank model, and its peak'),
        ('i<sub>&mu;</sub>, i<sub>&mu;,pk</sub>', 'magnetising current of the physical transformer, and its peak'),
        ('i<sub>p</sub>, i<sub>s</sub>', 'the instantaneous primary and secondary winding currents'),
        ('I<sub>sec,pk</sub>', 'peak secondary current per rectifier leg'),
        ('I<sub>pri,rms</sub>', 'primary rms over the worst switching cycle'),
        ('I<sub>lc</sub>, I<sub>pri</sub>, I<sub>rect</sub>', 'a line-cycle rms: the rms of each switching period, averaged in I&sup2; over the line half cycle; for the primary and for one rectifier leg'),
        ('I<sub>Cout</sub>, I<sub>out</sub>', 'ripple current in the output bank, and the load current'),
        ('t<sub>D</sub>, T<sub>ZC</sub>, T<sub>ZC,min</sub>', 'bridge dead time; the time the tank current takes to reach zero after the gates turn off, and its smallest value over the operating space'),
        ('T<sub>T</sub>', 'the swing time: how long the bridge node takes to cross the rail in the dead time'),
        ('v<sub>d</sub>, v<sub>d</sub><sup>F</sup>, V<sub>ds</sub>', 'bridge mid-point voltage, its fundamental, and a device&rsquo;s drain-source voltage'),
        ('v<sub>A</sub>, v<sub>B</sub>', 'the two bridge mid-points A and B against 0; v<sub>d</sub> = v<sub>A</sub> &minus; v<sub>B</sub>'),
        ('i<sub>S1</sub>', 'drain current of S1, positive drain to source'),
        ('S<sub>1</sub>, S<sub>2</sub>, S<sub>3</sub>, S<sub>4</sub>, D<sub>1</sub>, D<sub>2</sub>', 'the four bridge switches, and the two secondary rectifiers'),
        ('i<sub>D1</sub>, i<sub>D2</sub>, i<sub>D</sub>', 'the current in each secondary rectifier, forward; i<sub>D</sub> is either of them'),

        ('<b>The transformer and its core</b>', ''),
        ('B(t), B<sub>pk</sub>, B<sub>max</sub>', 'flux density, its peak, and the ceiling the design keeps under'),
        ('N', 'turns of the winding a voltage is applied to, in Faraday&rsquo;s law'),
        ('A<sub>e</sub>, A<sub>min</sub>', 'core effective area, and its narrowest section'),
        ('A<sub>N</sub>', 'winding window area of the coil former'),
        ('A<sub>L</sub>, g, &mu;<sub>0</sub>', 'inductance factor of the gapped core, the total centre-leg gap, and the permeability of free space'),
        ('N<sub>p</sub>, N<sub>s</sub>, N<sub>x</sub>', 'primary turns, secondary turns per winding, number of units in the assembly'),
        ('N<sub>s1</sub>, N<sub>s2</sub>', 'the upper and lower halves of the centre-tapped secondary (NS2 and NS3 in the design example)'),
        ('i<sub>NS</sub>, i<sub>NS2</sub>, i<sub>NS3</sub>, v<sub>NS</sub>', 'in the design example: the current of a secondary winding, named by its winding, and the voltage across one'),
        ('N<sub>aux</sub>, n<sub>aux</sub>/n<sub>sec</sub>', 'auxiliary winding turns, and its turns ratio to one secondary'),
        ('L<sub>open</sub>, L<sub>short</sub>', 'inductance across the primary with every other winding open; and with every secondary shorted and the auxiliary open'),
        ('I<sub>dc</sub>', 'the dc current the DC-overlap test overlaps on the LCR signal'),
        ('I<sub>p,pk</sub>, L<sub>p</sub>', 'in the flyback comparison only: the primary peak current and the primary inductance of a flyback'),
        ('&Phi;, &Phi;<sub>p</sub>, &Phi;<sub>s</sub>', 'in the flyback comparison: the core flux, and the flux the primary and the secondary ampere-turns would set up alone'),
        ('B<sub>s</sub>', 'saturation flux density of the core material, from the material data at temperature'),
        ('L<sub>&mu;</sub>, L<sub>L1</sub>, L<sub>L2</sub>', 'physical magnetising inductance and the two leakage inductances'),
        ('L<sub>1</sub>, L<sub>2</sub>', 'the open-circuit inductance measured at the primary and at one secondary'),
        ('L, &Delta;L', 'an inductance and the change of it a tolerance allows'),
        ('I<sub>eq</sub>, I<sub>sat</sub>', 'open-circuit current that reproduces the operating flux; the DC-overlap test current'),

        ('<b>The copper</b>', ''),
        ('A<sub>cu</sub>, J, I<sub>rms</sub>', 'copper cross-section one winding needs, the current density it is sized to, and the rms current of that winding; I<sub>rms</sub>(&theta;) is its rms over one switching period at line phase &theta;'),
        ('N<sub>w</sub>, A<sub>cu,w</sub>', 'turns and copper area of winding w, in the sum over all the windings'),
        ('k<sub>u</sub>', 'window utilisation: the share of A<sub>N</sub> that ends up copper'),
        ('&delta;, &rho;, f', 'skin depth, the resistivity of copper at the working temperature, and the frequency the depth is evaluated at'),
        ('&sigma;', 'conductivity of copper, 1/&rho;, in the strand eddy loss'),
        ('d<sub>s</sub>, a<sub>s</sub>, n<sub>s</sub>', 'Litz strand diameter, the copper cross-section of one strand, and the number of strands a winding needs'),
        ('d<sub>litz</sub>, k<sub>litz</sub>', 'outside diameter of the served bundle, and the share of that area which is copper'),
        ('t<sub>f</sub>, w<sub>f</sub>, w<sub>f,max</sub>, n<sub>f</sub>', 'foil thickness, the width one turn needs, the widest single strip assumed, and the number of strips in parallel'),
        ('N<sub>A</sub>, N<sub>B</sub>', 'the turns of the two parts of a split primary'),
        ('w<sub>A</sub>, w<sub>S</sub>, w<sub>B</sub>', 'axial widths of primary part A, the secondary and primary part B'),
        ('g<sub>1</sub>, g<sub>2</sub>', 'the gaps between the winding sections'),
        ('h<sub>w</sub>, l<sub>N</sub>', 'depth of the winding window, across which the leakage field runs, and the mean turn length'),
        ('h<sub>r</sub>, k<sub>w</sub>', 'radial room between the coil-former tube and the outer legs, and the winding pitch over the bundle diameter (the looseness of a real winding)'),
        ('d<sub>b,p</sub>, d<sub>b,s</sub>', 'outside diameter of one primary bundle (triple insulation included) and of one secondary bundle, as built'),
        ('J<sub>p</sub>, J<sub>s</sub>', 'current density in the primary and in each secondary winding, as built'),

        ('<b>Semiconductors</b>', ''),
        ('R<sub>DS(on)</sub>, R<sub>DS(on),25</sub>, k<sub>T</sub>', 'on-resistance, its 25&nbsp;&deg;C headline value, and the multiplier from 25&nbsp;&deg;C to T<sub>j,max</sub>'),
        ('T<sub>j</sub>, T<sub>j,max</sub>, T<sub>a</sub>', 'junction temperature, its rating, and ambient temperature'),
        ('C<sub>oss</sub>, C<sub>o(tr)</sub>, Q<sub>oss</sub>', 'the small-signal and the time-related output capacitance of a MOSFET, and the charge the time-related one stands for'),

        ('<b>The controller and its network</b>', ''),
        ('V<sub>FB</sub>, v<sub>FB</sub>', 'feedback voltage above its 0.5&nbsp;V offset at rated power, and its small-signal part'),
        ('V<sub>os</sub>, K<sub>HV</sub>, K<sub>M</sub>, K<sub>FF</sub>', 'the offset and the three internal gains of the feedback law, quoted from the datasheet block diagram'),
        ('K<sub>pwr</sub>', 'gain of the power law, V<sub>FB</sub> = K<sub>pwr</sub>R<sub>CS</sub>P<sub>in,LLC</sub>'),
        ('R<sub>CS</sub>, R<sub>CS,max1</sub>, R<sub>CS,max2</sub>', 'current-sense resistor, and the two conditions that bound it: the maximum-power law and the OCP1 trip'),
        ('I<sub>OCP1</sub>, I<sub>OCP2</sub>', 'over-current thresholds set by R<sub>CS</sub>'),
        ('C<sub>T</sub>, R<sub>T</sub>', 'oscillator timing capacitor and resistor'),
        ('C<sub>T,min</sub>, C<sub>T,max</sub>, R<sub>T,ceil</sub>, R<sub>T,max</sub>', 'the window those two have to be chosen inside'),
        ('V<sub>ref</sub>, I<sub>EA</sub>, I<sub>EA,max</sub>', 'the oscillator reference, the error-amplifier current that is the only control input, and its maximum'),
        ('f<sub>Min</sub>, f<sub>Max</sub>, f<sub>SU</sub>', 'oscillator floor, ceiling and start-up frequency set by R<sub>T</sub>, C<sub>T</sub> and T<sub>idle</sub>'),
        ('T<sub>idle</sub>', 'oscillator idle time'),
        ('R<sub>BM</sub>, r<sub>BM</sub>, V<sub>BM,eq</sub>, P<sub>in,BM</sub>', 'burst-mode resistor, the fraction of the rated input power P<sub>in</sub> burst starts at, the equivalent FB threshold, and the input power that corresponds to'),
        ('R<sub>CFG</sub>, R<sub>CFG,max</sub>', 'configuration resistor, and the largest value the lowest input voltage allows'),
        ('V<sub>BO</sub>, V<sub>BO,pk</sub>, V<sub>BO,rms</sub>', 'brown-out threshold, as a mains peak and as an rms voltage'),
        ('R<sub>ZCD,H</sub>, R<sub>ZCD,L</sub>, I<sub>bias</sub>', 'the ZCD divider, and the current it is designed to draw'),
        ('V<sub>OVP1</sub>, V<sub>OVP2</sub>, V<sub>OVP1,out</sub>', 'the two over-voltage thresholds, and the output voltage OVP1 is aimed at'),
        ('V<sub>CC</sub>, V<sub>CCon</sub>, V<sub>CCoff</sub>', 'the IC supply, and the two thresholds of its under-voltage lockout'),
        ('V<sub>CC,reg</sub>, V<sub>CC,reg,min</sub>, C<sub>VCC</sub>, C<sub>VCC,req</sub>', 'the voltage the regulator holds the V<sub>CC</sub> pin at and the bottom of its band; the capacitor on the pin and the value the start-up needs'),
        ('V<sub>CC,HVSUon</sub>', 'the V<sub>CC</sub> level below which the start-up unit turns its charge current on'),
        ('V<sub>DZ</sub>, V<sub>DZ,max</sub>, V<sub>BE</sub>, V<sub>D</sub>', 'regulator Zener voltage and its top of tolerance, the pass transistor base-emitter drop, and a silicon diode forward drop'),
        ('R<sub>BZ</sub>, R<sub>BZ,max</sub>, &beta;<sub>min</sub>, I<sub>Z,min</sub>', 'Zener feed resistor and the largest that still regulates, the least current gain of the pass transistor, and the least Zener bias'),
        ('I<sub>VCC</sub>, I<sub>VCC,SU</sub>, I<sub>CC</sub>', 'current the V<sub>CC</sub> rail supplies in run and at the start-up frequency, and the controller&rsquo;s own share'),
        ('N<sub>sw</sub>, Q<sub>g</sub>', 'switch positions driven, and the gate charge of one primary MOSFET'),
        ('I<sub>HVSU</sub>, t<sub>hand</sub>, V<sub>out,UV</sub>', 'start-up unit charge current; time from the first pulse until the auxiliary winding holds V<sub>CC</sub>, and the output voltage at which it does'),

        ('<b>The voltage loop</b>', ''),
        ('G<sub>plant</sub>(s), G<sub>EA</sub>(s), T(s)', 'plant v<sub>out</sub>/v<sub>FB</sub>, compensator &minus;v<sub>FB</sub>/v<sub>out</sub> (the feedback sign taken out), and loop gain T = G<sub>plant</sub>G<sub>EA</sub>'),
        ('G<sub>o</sub>, EA<sub>o</sub>', 'gain constant of the plant integrator and of the compensator, in rad/s'),
        ('&omega;<sub>z</sub>, &omega;<sub>p</sub>, &omega;<sub>px</sub>, &omega;<sub>c</sub>', 'compensator zero, pole, high-frequency pole, and the crossover, in rad/s'),
        ('f<sub>z</sub>, f<sub>p</sub>, f<sub>px</sub>, f<sub>180</sub>', 'the same zero and poles in hertz, and the frequency where arg T = &minus;180&deg;'),
        ('f<sub>c</sub>, &Phi;<sub>M</sub>, GM', 'loop crossover frequency, phase margin, gain margin'),
        ('f<sub>cto</sub>', 'where the bare plant integrator would cross 0&nbsp;dB, G<sub>o</sub>/2&pi;'),
        ('f<sub>pHF</sub>, f<sub>MB</sub>', 'the high-frequency pole chosen for C<sub>fx</sub>, and the centre frequency the K-factor method places the zero and the pole around'),
        ('K<sub>v</sub>, &Gamma;<sub>v</sub>, &alpha;<sub>v</sub>', 'K factor of the Type II compensator, and the input-voltage margin factor and weighting constant it is built from'),
        ('Z<sub>f</sub>', 'feedback impedance of the compensator, C<sub>Fo</sub> in parallel with R<sub>F</sub>+C<sub>F</sub>'),
        ('v<sub>K</sub>', 'small-signal voltage at the TL431 cathode'),
        ('R<sub>I</sub>, R<sub>O</sub>', 'output divider of the compensator'),
        ('C<sub>Fo</sub>, C<sub>F</sub>, R<sub>F</sub>, C<sub>fx</sub>', 'compensator parts: the two capacitors and the resistor of the TL431 network, and the FB-pin capacitor'),
        ('C<sub>opto</sub>, C<sub>ser</sub>', 'the optocoupler&rsquo;s own output capacitance, and C<sub>F</sub>+C<sub>Fo</sub> in series'),
        ('R<sub>B</sub>, R<sub>B,max</sub>, R<sub>B,min</sub>, R<sub>P</sub>, R<sub>FB</sub>', 'optocoupler LED resistor and the window it has to sit in, the TL431 bias resistor, and the pull-up inside the FB pin'),
        ('CTR, CTR<sub>s</sub>, CTR<sub>m</sub>, i<sub>LED</sub>', 'optocoupler current transfer ratio, its value at the steady-state and at the maximum LED current, and the LED current itself'),
        ('i<sub>FB</sub>', 'small-signal current the optocoupler sinks from the FB pin, CTR&thinsp;i<sub>LED</sub>'),
        ('I<sub>FB,steady</sub>, I<sub>FB,max</sub>, I<sub>min</sub>', 'FB-pin current at steady state and at maximum, and the least current the TL431 needs to stay in regulation'),
        ('V<sub>R</sub>, V<sub>Z</sub>, V<sub>Fo</sub>', 'TL431 reference, the regulated rail that feeds the LED, and the LED forward drop'),
        ('v<sub>out</sub>, i<sub>out</sub>, v<sub>C</sub>', 'small-signal output voltage and the current the converter delivers into the bank; the voltage on a capacitor in a waveform'),
        ('&Delta;V<sub>loop</sub>, &Delta;V<sub>FB</sub>', '2f<sub>l</sub> output ripple seen by the loop, and the ripple it leaves on the FB pin'),

        ('<b>The output, and hold-up</b>', ''),
        ('C<sub>out</sub>, C<sub>in</sub>', 'output capacitor bank, input film capacitor'),
        ('V<sub>out</sub>, I<sub>out</sub>, R<sub>L</sub>', 'output voltage and load current; the load as a resistance'),
        ('&Delta;v, &Delta;v<sub>pp</sub>', 'allowed and achieved 2f<sub>l</sub> output ripple'),
        ('T<sub>hold</sub>, t<sub>hold</sub>, V<sub>o,min</sub>', 'required and achieved hold-up time, and the lowest output allowed at its end'),
        ('ESR', 'equivalent series resistance of the bank, taken at the switching frequency'),

        ('<b>Verification margins</b>', ''),
        ('k, X, X<sub>act</sub>, X<sub>req</sub>', 'a verification margin X<sub>act</sub>/X<sub>req</sub>, where X is whatever quantity the row is about; every k in this note is &ge; 1 when the design passes'),
        ('k<sub>floor</sub>, k<sub>ceil</sub>', 'how far f<sub>Min</sub> clears f<sub>o</sub>, and how far f<sub>Max</sub> clears the highest operating frequency'),
        ('k<sub>Ploss</sub>', 'the loss budget of a device position over the loss computed for it'),
        ('k<sub>RBZ</sub>', 'R<sub>BZ,max</sub>/R<sub>BZ</sub>: how far the Zener feed resistor sits below the largest that still regulates at the end of hold-up'),
        ('w<sub>k</sub>, &theta;<sub>k</sub>', 'the weights and the nodes of the five-point Simpson rule the line-cycle rms values are integrated with'),
    ]
    s.extend(tbl('Symbols.', [['Symbol', 'Meaning']] + [list(r) for r in _SYM],
             widths=[CW * 0.26, CW * 0.74], split=True))

    # =============================================================== 9
    add(h1('References'))
    ext(bullets([
        'STMicroelectronics, <i>L6790A LLC-PFC controller</i>, preliminary '
        'datasheet, 30 April 2026. <b>Draft.</b>',
        'STMicroelectronics, <i>EVL6790_670W</i> evaluation board schematics.',
        'Infineon Technologies, <i>LLC Converter Design Note</i>, AN 2013-03, '
        'V1.0, March 2013.',
        'Infineon Technologies, <i>Resonant LLC converter: operation and '
        'design</i>, AN 2012-09, V1.0, September 2012.',
        'onsemi (formerly Fairchild), <i>Half-bridge LLC resonant converter '
        'design using FSFR-series Fairchild power switch</i>, AN-4151.',
        'Monolithic Power Systems, <i>Understanding LLC operation</i>, '
        'part&nbsp;2.',
        'Toshiba Electronic Devices &amp; Storage, <i>Power factor '
        'correction (PFC) circuits</i>, application note.',
        'Toshiba Electronic Devices &amp; Storage, <i>Resonant circuits and '
        'soft switching</i>, application note, 12 November 2019.',
        'ROHM Semiconductor, TechWeb, <i>LLC operating regions</i> '
        '(region framing of Figure&nbsp;' + FR('f04_three_regions') + ').',
        'W. Wenbo et al., <i>A single-stage 1.65 kW ac-dc LLC converter</i>, '
        'IEEE ECCE.',
        'onsemi, <i>The TL431 in the control of switching power supplies</i>, '
        'TND381-D (compensator design with a TL431 and an optocoupler).',
        '[PI] Power Integrations, <i>If your power converter is not safe, '
        'you may have an expensive recall</i>, PSMA IS293, 2020 '
        '(IEC 62368-1 creepage and clearance tables, altitude factors).',
        '[ATIS] M. Maytum, <i>IEC 62368-1 and pluggable mains powered '
        'equipment surge protection</i>, ATIS PEG, 2019 (mains transients, '
        'Table 14 clearances).',
        '[TUV] TUV Rheinland, CB test report 60431427 001 to IEC 62368-1, '
        'Class II AV/ICT adapter, evaluated for 5000 m.',
        '[UL] UL, CB test report E135803-A6002-CB-1 to IEC 62368-1, '
        'Advanced Energy GB130Q, evaluated for 5000 m.',
        '[TI] Texas Instruments, <i>Demystifying clearance and creepage '
        'distance for high-voltage end equipment</i>, SLUP419, 2024.',
        '[GB] GB 4943.1-2022, <i>Audio/video, information and communication '
        'technology equipment &mdash; Part 1: Safety requirements</i> '
        '(foreword and scope).',
        '[TIW] Furukawa Electric, <i>TEX-E triple-insulated wire, safety '
        'approvals</i>.',
        'DiscoverEE, STO60N045DM9 parameter listing (gate charge of the '
        'candidate primary MOSFET; confirm on the ST datasheet).']))

    # =============================================================== 10
    add(h1('Errata and open items'))
    add(p('Everything here is worked around rather than solved, and most of '
          'it only the released datasheet or a prototype can close. Re-read '
          'it before a production release.'))

    add(h2('Datasheet: the draft is not self-consistent'))
    ext(tbl('Points where the draft datasheet contradicts itself or leaves a '
            'value open. Every one of them must be re-checked against the '
            'released document.',
            [['Item', 'What the draft says', 'What is used here, and why'],
             ['Oscillator idle time T<sub>idle</sub>',
              'Section 5.3.2 implies 700 ns in the frequency expressions and '
              '350 ns in the C<sub>T,max</sub> expression; Table 2 (recommended '
              'operating range) back-solves to about 250 ns',
              '<b>%(Tidle).0f ns.</b> The two clamps bracket the operating '
              'range at 250 ns and stop doing so at 700 ns, so this is a '
              'measurement, not a rounding' % V],
             ['Brown-out expression',
              'V<sub>BO</sub> = min(60 V, R<sub>CFG</sub>&middot;4 V/k&Omega;) '
              '&mdash; read literally this is 60 V for every resistor, which '
              'contradicts the configuration table',
              'Read as R<sub>CFG</sub>&middot;4 V/k&Omega; with 15 k&Omega; as '
              'the floor. That is the only reading consistent with the table'],
             ['Brown-out units',
              'the threshold is a <i>peak</i> voltage; board notes and design '
              'tools quote rms',
              'Converted explicitly wherever it is compared '
              '(&radic;2 = 1.414)'],
             ['Thermal resistance', 'TBD',
              'No junction temperature can be predicted from the datasheet '
              'alone; the loss budget is checked against measured rise '
              'instead'],
             ['ZCD absolute maximum', 'lower limit given as TBD',
              'The divider is sized from the OVP thresholds only'],
             ['Driver naming in Section 5.3.1',
              'LOUT1 and LOUT2 are transposed in one sentence against the '
              'block diagram and the configuration table',
              'The block diagram and the table are taken as correct: LOUT2 is '
              'the pin that is strapped and held high in half bridge'],
             ['Start-up unit after its timeout',
              'the charge current turns on below V<sub>CC,HVSUon</sub> = 12 V '
              'and the generator shuts down 120 ms after V<sub>CCon</sub>; '
              'whether the charge current comes back below 12 V after that is '
              'not stated',
              'V<sub>CC,reg</sub> is kept above 12 V at the bottom of its band, '
              'so the run supply never depends on the answer']],
            widths=[CW * 0.22, CW * 0.40, CW * 0.38], split=True))

    add(h2('Traps in the obvious way of building a design sheet'))
    add(p('Places where the obvious way to set up a design sheet gives a '
          'plausible wrong number that nothing flags.'))
    ext(tbl('Traps that produce a plausible wrong number.',
            [['Where', 'The trap', 'Consequence if missed'],
             ['Equivalent input range',
              'taking the maximum from the ac maximum instead of the '
              'full-bridge morphing edge',
              'The frequency corner is never evaluated. Here it is the '
              'difference between %(Vacmax).0f and %(Veqhi).1f Vac '
              'equivalent, and it also sets &lambda;' % V],
             ['&lambda; from the minimum-gain condition',
              'the same corner again, one step earlier',
              'The required &lambda; comes out far too small &mdash; a factor '
              'of over a hundred in one case &mdash; and L<sub>m</sub> far '
              'too large'],
             ['Line-cycle rms currents',
              'evaluating one phase, usually &theta; = &pi;/4, and calling it '
              'the line-cycle value',
              'The output bank ripple current and the rectifier loss are '
              'both understated. A Simpson rule over the half cycle costs '
              'nothing and is exact enough'],
             ['Secondary rms above resonance',
              'squaring a full half sine when the current is truncated',
              'Up to 8 % at the high corner. Below resonance the factor is '
              'exactly 1, which is why it can sit unnoticed for a long time'],
             ['Primary device rating',
              'rating on the reflected load current I<sub>trafo,pk</sub>',
              'About %.0f %% under-rated &mdash; the switch carries the '
              '<i>composite</i> tank current' % (100 * (V['Icomp'] / V['Itr'] - 1))],
             ['Loss and thermal resistance',
              'computing loss from the 25 &deg;C R<sub>DS(on)</sub> and then '
              'asking for a heatsink that holds 125 &deg;C',
              'The required thermal resistance comes out only about half as '
              'demanding as it really is'],
             ['ZVS check',
              'the closed-form shortcut, at the design Q and with the design '
              '&lambda;',
              'An error of tens of per cent whose sign nothing fixes; on '
              'this tank %(pc).0f %% conservative. Optimistic is the '
              'dangerous direction'
              % dict(pc=abs(V['TzcCFpc']))],
             ['Selected versus calculated',
              'a check that reads the calculated value while the board '
              'carries the selected one',
              'Every downstream margin is reported for a design that was not '
              'built']],
            widths=[CW * 0.20, CW * 0.38, CW * 0.42], split=True))

    add(h2('Constants used here without a derivation'))
    _TPM = A.SH['t.PM']
    _PMT = __import__('math').degrees(__import__('math').atan(_TPM))
    ext(bullets([
        'The <b>&pi;&sup2;/8</b> in the dead-time form of the '
        '&lambda; condition. It behaves like a correction for the '
        'fundamental content of a square wave, but no source states it. It '
        'is indicative; the binding check is the ZVS sweep.',
        'The <b>exponent 5</b> in the closed-form ZVS shortcut. This is a '
        'fitted number, and it is the main reason the shortcut errs '
        'unpredictably near the boundary.',
        'The <b>0.744</b> in the input-voltage margin factor of the '
        'compensator design. It scales the crossover target and nothing '
        'downstream is sensitive to it at the percent level.',
        #  Equation Kv is the ST tool's expression as written (original
        #  workbook, Device Setting D78).  At alpha = 1 it does not become
        #  Venable's tan(45 + Phi/2); with ((1 + alpha^2) tan Phi)^2 under
        #  the root it would.  What ST means by alpha is not published, so
        #  it is reported, not changed (round 63).
        'The <b>K<sub>v</sub> expression</b> (Equation&nbsp;%(e)s) is the ST '
        'tool&rsquo;s as written. With &alpha;<sub>v</sub> = 1 it gives '
        '%(k1).3f for a %(pm).0f&deg; target, not Venable&rsquo;s '
        'tan(45&deg; + &Phi;<sub>M</sub>/2) = %(kv).3f; the tool does not '
        'say what &alpha;<sub>v</sub> weights. The phase margin is '
        'therefore taken from the fitted parts (Equation&nbsp;%(m)s), not '
        'from K<sub>v</sub>.'
        % dict(e=ER('Kv'), m=ER('PMeq'), pm=_PMT,
               k1=(2 * _TPM + ((1 + _TPM) ** 2 + 4) ** 0.5) / 2,
               kv=__import__('math').tan(__import__('math').radians(45 + _PMT / 2))),
        'The <b>16.8 &Omega;&middot;W</b> maximum-power constant follows '
        'from the feedback span and the multiplier gain (2.8&nbsp;V / 0.167); '
        'it is listed because those gains are draft values.']))

    add(h2('Open items in this design'))
    ext(tbl('What is not settled, and what would settle it.',
            [['Item', 'State', 'What closes it'],
             ['T<sub>idle</sub>', 'three values, 250, 350 and 700 ns',
              'Measure f<sub>sw</sub>(&theta;) on the first board'],
             ['Primary conduction loss',
              '%(kPloss).3f against the budget &mdash; <b>not met, and '
              'accepted</b>' % V,
              'No single 600 V device meets a %.0f W budget in the standing '
              'position. Whether it needs a heatsink is a thermal '
              'measurement, not a calculation' % _kb],
             ['Secondary loss budget',
              '%(kPSR).3f &mdash; essentially exhausted' % V,
              'One more device in parallel per leg recovers it; the decision '
              'waits on the measured temperature'],
             ['Transformer inductance tolerance',
              'the tank tolerates a %(Ldrop).1f %% fall in open-circuit '
              'inductance and the usual specification asks for '
              '&plusmn;10 %%' % V,
              'R<sub>T</sub> stays at %(RT).0f k&Omega; until the first '
              'board. A lower R<sub>T</sub> covers &plusmn;10 %% but widens '
              'the zero-crossing dead zone; choose after measuring '
              'f<sub>sw</sub>(&theta;) and the input-current THD at 90 and '
              '230 Vac' % V],
             ['Output bank volume and height',
              '%(Cout).1f mF, %(nC).0f parts' % V,
              'A mechanical question, not an electrical one, and it can send '
              'the whole architecture back to the output voltage'],
             ['Standby power', 'burst entry assumed at %(PinBM).0f W' % V,
              'Measure, then trade R<sub>BM</sub> against the feedback '
              'ripple'],
             ['Efficiency assumption',
              '&eta;<sub>HB</sub> = %(etaHB).0f %% assumed' % V,
              'Optimistic. Taking 95 %% instead moves R<sub>CS</sub> and '
              'R<sub>ac</sub> by about %.0f %%, so nothing downstream is '
              'sensitive &mdash; but it should be replaced by a measurement' % (100 * (V['etaHB'] / 95.0 - 1))],
             ['Gate charge Q<sub>g</sub>',
              '%(Qg).1f nC typical, from a parameter listing' % V,
              'Read it from the datasheet of the part fitted; I<sub>VCC</sub>, '
              'R<sub>BZ</sub> and C<sub>VCC</sub> scale with it'],
             ['Start-up hand-over',
              't<sub>hand</sub> %.1f ms assumes no load until the rail is up'
              % A.SH['t.hand'],
              'Measure V<sub>CC</sub> through a cold start with the real load '
              'sequencing, and the start-up unit temperature'],
             ['Transformer working voltage',
              '%.0f V rms estimated; creepage taken at the %d V row'
              % (_INS.req()['u_rms'], _INS.req()['row']),
              'The certifying body measures it on the first samples'],
             ['Insulation values not read from the standard',
              'from seminars and certification reports (Section&nbsp;%s)'
              % SR('Safety insulation of this transformer'),
              'Confirm with the certifying body under the edition the '
              'certificate will cite: electric strength, the high-frequency '
              'clearance table, the production test'],
             ['TIW approval',
              '%d kHz, Class %s' % (_INS.TIW_FMAX / 1e3, _INS.TIW_CLASS),
              'The start-up frequency is above it for milliseconds; ask the '
              'wire vendor, and hold the winding under 130 &deg;C'],
             ['Leakage of the section winding',
              '%.2f &micro;H with the sections touching and k<sub>w</sub> = '
              '%.2f, a field-solution estimate; %.2f &micro;H wound tight'
              % (_ef['L'], _w['k_wind'], _et),
              'Measure L<sub>short</sub> on the first samples. Nothing trims '
              'it: a space between the sections raises it about %.2f '
              '&micro;H a 0.1 mm, and lowering it takes narrower sections'
              % (_g01 - _ef['L'])],
             ['Leakage of each half',
              'NS2 alone %.2f, NS3 alone %.2f &micro;H; the higher is %.0f %% '
              'over L<sub>r</sub>' % (_h2, _h3,
                                     100 * (_hmax / V['Lshort'] - 1)),
              'The tank sees the half that conducts: measure both, and judge '
              'the tank and R<sub>T</sub> with them'],
             ['Winding pitch k<sub>w</sub>',
              '%.2f, assumed' % _w['k_wind'],
              'Measure the build of the first sample; a looser winding than '
              'that does not fit the %.2f mm of radial room' % _w['r_free']],
             ['Custom coil former',
              'tube %.1f mm across, flanges %.2f mm, %d pins in two rows'
              % (_M['tube_od'], _w['flange'], _CORE.BOBBIN['pins']),
              'No former is catalogued for %s; the bobbin maker draws it to '
              'this specification and confirms the pins, their current '
              'rating and the distances around them' % _CORE.CHOSEN],
             ['Centre-leg gap',
              'one gap of about %.1f mm, from the catalogue curve%s'
              % (_gl, '' if _gin else ' extrapolated past its %.0f mm end'
                 % _R['AL_curve'][3]),
              'The first layer of NP1 is %.2f mm from it: ask the core vendor '
              'for a split or distributed gap, and measure the winding '
              'temperature near it' % _wall],
             ['Core loss',
              '%s at %.0f mT and f<sub>r</sub>: not computed; the catalogue '
              'gives %.2f W at most at %.0f kHz, %.0f mT, %.0f &deg;C'
              % (_R['material'], _CORE.flux(V, _R['Ae']), _pc[0], _pc[1],
                 _pc[2], _pc[3]),
              'Read the %s material curve; measure the core temperature'
              % _R['material']],
             ['Ac loss of the Litz',
              '%.1f to %.1f W from the leakage field on %.1f W dc, first '
              'order, &oslash;%.2f mm strands'
              % (_pa['P_pri'] + _pa['P_sec'], _pb['P_pri'] + _pb['P_sec'],
                 _pdc, _CORE.D_STRAND),
              'Measure the winding temperature; a finer strand (loss as '
              'd<sub>s</sub>&sup2;) is the remedy, its fill from the vendor'],
             ['Parallel secondary bundles',
              'about %.1f A rms around the %d bundles of a turn, against '
              '%.1f A each, first order; about %.2f W'
              % (_sh['turned'], _w['sec_par'], _sh['load'], _pcirc),
              'Measure the bundle currents on the first sample, a current '
              'probe on each pin'],
             ['Triple-insulated Litz for NP1',
              'one bundle of %d &times; &oslash;%.2f mm, %.1f mm of '
              'insulation assumed'
              % (_w['n_strand'], _CORE.D_STRAND, _w['tiw_add']),
              'The wire vendor confirms the size, the diameter and the '
              'approval; a thicker wire takes radial room from %.2f mm'
              % _w['r_free']]],
            widths=[CW * 0.22, CW * 0.34, CW * 0.44], key='openitems',
            split=True))
    add(note('<b>Every cross-check here is a consistency check, not a '
             'correctness check.</b> Three implementations agreeing means '
             'they implement the same equations, not that the equations '
             'describe the hardware. The first prototype is the correctness '
             'check.'))

    return s


ZVS_WORST = {}          # filled by _zvs_grid, read by the text beside it
_WORDS = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
          'eight', 'nine')


def _minus(x, fmt):
    """a number with a typographic minus, not a hyphen"""
    s = fmt % x
    return s.replace('-', '&minus;')


def _f_idle(V, tidle_ns):
    """f_Min and f_Max (kHz) for another oscillator idle time

    Both are 1/(2(tau + T_idle)); tau is recovered from the sheet's own
    f_Min and f_Max at the design idle time, so no constant is typed.
    """
    tmin = 1 / (2 * V['fMin'] * 1e3) - V['Tidle'] * 1e-9
    tmax = 1 / (2 * V['fMax'] * 1e3) - V['Tidle'] * 1e-9
    t = tidle_ns * 1e-9
    return 1 / (2 * (tmin + t)) / 1e3, 1 / (2 * (tmax + t)) / 1e3


def _where(veq, R, fb='at the FB edge (%.0f&nbsp;Vac in full bridge, which the '
                   'tank sees as %.0f&nbsp;Vac)',
        hb='at the HB edge (%.0f&nbsp;Vac, half bridge)',
        other='at %.0f&nbsp;Vac'):
    """a place on the input axis in words: the mains and the bridge, and
    what the tank sees when that differs - never 'Vac eq.' (2026-09-24)"""
    import l6790
    if abs(veq - R['Vin_FBmax']) < 1e-6:
        return fb % (veq / 2, veq)
    if abs(veq - R['Vin_min']) < 1e-6:
        return hb % veq
    for nm, v, m in l6790.line_conditions(R):
        if abs(v - veq) < 1e-6:
            return other % l6790.mains_of(v, m) + (' in full bridge' if m == 'FB' else ' in half bridge')
    return other % veq


def _zvs_grid(A, head=('Load', 'edge')):
    """T_ZC over load and equivalent input, recomputed - never transcribed

    head lets the Korean edition label the same grid in its own language;
    the numbers are computed here either way, never transcribed.
    """
    import l6790
    cols = tuple(v for _n, v, _m in l6790.line_conditions(A.R))
    rows = [[head[0]] + [l6790.cond_short(v, m, A.R, head[1]).replace(' Vac ', ' Vac<br/>')
                         for _n, v, m in l6790.line_conditions(A.R)]]
    worst = None
    for ld in (1.0, 0.75, 0.50, 0.25):
        r = ['%d %%' % (ld * 100)]
        for c in cols:
            t = l6790.sweep(A.R, c, ld)[1]['Tzc_min'] * 1e9
            r.append('%.0f' % t)
            if worst is None or t < worst[0]:
                worst = (t, c, ld)
        rows.append(r)
    # the design corner - full load at the low equivalent input - is where
    # the gain requirement is set, and it is NOT always where ZVS is worst
    corner = l6790.sweep(A.R, A.R['Vin_min'], 1.0)[1]['Tzc_min'] * 1e9
    ZVS_WORST.update(zTzc=worst[0], zVin=worst[1], zLoad=worst[2] * 100,
                     zk=worst[0] / A.V['tD'], cTzc=corner,
                     ck=corner / A.V['tD'],
                     same=abs(worst[0] - corner) < 0.5, rows=rows)
    return rows
