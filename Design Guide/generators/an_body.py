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


def build(A):
    """A is the an_pdf module, handed in - importing it here would load a
    second copy whenever an_pdf is run as __main__."""
    import cores as _CORE          # the datasheet figures, in one place
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
    add(p('A conventional universal-input LLC power supply has two stages: a '
          'boost power-factor corrector that holds a 400&nbsp;V bus, and an '
          'LLC converter that steps that bus down. The capacitor between them '
          'does two jobs. It stores the energy that a unity-power-factor '
          'input cannot deliver evenly, and it gives the LLC an almost '
          'constant input, so the resonant tank only has to cover a narrow '
          'range.'))
    add(p('A <b>single-stage PFC LLC</b> removes both the boost stage and '
          'that capacitor. The rectified mains feeds the resonant tank '
          'directly. The result is a converter whose input is a '
          '100/120&nbsp;Hz half sine, whose gain is no longer something the '
          'controller can set, and whose output capacitor must absorb '
          'everything the bus capacitor used to. It is a different converter, '
          'not an LLC with one stage removed, and most of the design habits '
          'from the two-stage case do not apply.'))
    add(p('This note explains how such a converter works and how to design '
          'one with the STMicroelectronics <b>L6790A</b> controller. One '
          'worked design runs through it, from specification to component '
          'values: <b>90 to 264&nbsp;Vac in, %(Vout).0f&nbsp;V / '
          '%(Iout).1f&nbsp;A = %(Pout).1f&nbsp;W out</b>, a low-voltage, '
          'high-current dc rail.' % V))
    add(note('<b>Scope.</b> Covered: the power stage, the resonant tank, the '
             'output bank, the controller network and the voltage loop. Not '
             'covered: EMI filtering, magnetics construction, layout and '
             'safety approval.'))

    # =============================================================== 2
    add(h1('The two converters this one is made of'))
    add(p('What comes later is easier to follow if the two halves are '
          'understood separately first. This section covers an ordinary LLC '
          'and ordinary power factor correction. A reader who has designed '
          'both can skip to Section&nbsp;%s.'
          % SR('Why single stage, and what it costs')))
    add(h2('What an LLC converter is'))
    add(p('An LLC converter is a square-wave generator that drives a '
          'resonant network; the network feeds a transformer and a rectifier. '
          'The switches only chop the input into a square wave whose '
          'frequency can be varied. There is no duty cycle to set and no '
          'inductor current to program.'))
    add(fig('an_llc_stage',
            'An LLC stage: a square-wave generator, the resonant network, a '
            'transformer and a rectifier. The switches only set the '
            'frequency &mdash; the tank decides how much power flows and '
            'the transformer sets the voltage.'))
    add(p('The three tank elements are named in the order they appear in '
          '&ldquo;LLC&rdquo;: the series inductance L<sub>r</sub>, the '
          'magnetising inductance L<sub>m</sub> of the transformer, and the '
          'series capacitance C<sub>r</sub>. The middle one is not a separate '
          'part: it is the transformer&rsquo;s own magnetising inductance. So '
          'only C<sub>r</sub> and L<sub>r</sub> are added components, and '
          'L<sub>r</sub> is often the leakage inductance of the transformer '
          'itself.'))
    ext(bullets([
        '<b>The square wave sets the frequency, and nothing else.</b> The '
        'output voltage is controlled by moving f<sub>sw</sub>, because the '
        'impedance of the tank, and so its voltage division, depends on '
        'frequency.',
        '<b>The tank current is almost a sine wave.</b> That is the purpose: '
        'the switches turn on and off while the current is small, or while it '
        'flows through the body diode, so most of the switching loss '
        'disappears.',
        '<b>The transformer steps the voltage and provides isolation</b>, and '
        'its leakage inductance can be used <i>as</i> L<sub>r</sub> instead '
        'of being a problem. That is the usual construction at these power '
        'levels.']))
    add(h2('Why an LLC, and not something simpler'))
    add(p('An LLC is more work than a forward or a flyback converter, and it '
          'does not regulate by duty cycle, which is what most designers are '
          'used to. At a few hundred watts and above, it is worth the extra '
          'work for these reasons:'))
    ext(bullets([
        '<b>Soft switching over the whole load range, on both sides.</b> The '
        'primary switches turn on at zero voltage, and below resonance the '
        'secondary rectifiers turn off at zero current. A phase-shifted full '
        'bridge loses ZVS at light load; an LLC does not, because the '
        'magnetising current that does the work is present at any load.',
        '<b>The frequency can be raised.</b> In a hard-switched converter, '
        'switching loss limits the frequency, and with it the size of the '
        'magnetics and the filter. Remove that loss and hundreds of kHz '
        'become practical.',
        '<b>The transformer leakage is used, not fought.</b> In a forward '
        'converter the leakage inductance is a problem that needs a snubber. '
        'Here it can <i>be</i> L<sub>r</sub>, so the resonant inductor costs '
        'nothing and the snubber is not needed.',
        '<b>No output inductor.</b> The rectifier feeds the output capacitor '
        'directly. That removes a wound component, and its loss, from the '
        'high-current side, where it hurts most.',
        '<b>Low noise.</b> The currents are sine waves rather than '
        'trapezoids, and the switching edges are slow and damped, so the '
        'conducted and radiated emissions are much lower than in a '
        'hard-switched converter of the same power.']))
    add(p('The costs are real too. Regulation is by frequency, so the '
          'operating frequency moves with line and load, and the magnetics '
          'must work over that whole range. The magnetising current '
          'circulates whether or not the load takes power, so light-load '
          'efficiency is not a strong point. And the design does not come from '
          'a duty-cycle expression: it comes from the gain curve, which is '
          'what the rest of this section is about.'))
    add(h2('What resonance is for'))
    add(p('In a hard-switched converter a switch turns on with the full input '
          'voltage across it, so the energy stored in its output capacitance '
          'is lost in the channel every cycle. That loss grows with '
          'frequency. It is what limits the frequency, and with it the size '
          'of the magnetics.'))
    add(p('An LLC that runs <b>in its inductive region</b> presents an '
          'inductive load to the bridge. The tank current then lags the '
          'drive voltage. In the dead time between the two switches of a '
          'leg, that lagging current discharges the mid-point capacitance by '
          'itself, and the next switch turns on at zero volts. <b>That is '
          'zero-voltage switching, and it is the whole reason for the '
          'topology.</b> Section&nbsp;%s shows the mechanism and what it '
          'requires of the design.'
          % SR('ZVS and ZCS are not the same thing')))
    add(fig('an_llc_waves',
            'One switching period below resonance. i<sub>Lr</sub> is the tank '
            'current and i<sub>Lm</sub> the magnetising current; the '
            'difference between them is what crosses to the secondary, and '
            'it is gone once the two meet. The switch turns on while its own '
            'current is still negative, and that is what discharges the '
            'mid-point.'))
    add(p('The two frequencies that bound this are the subject of '
          'Section&nbsp;' + SR('The two resonances')
          + ', and the operating regions they divide are in Section&nbsp;'
          + SR('The gain function and the three regions') + '.'))
    add(note('The condition is <i>inductive operation</i>, not a particular '
             'frequency. Go low enough in frequency and the tank becomes '
             'capacitive: the current leads, the dead time works against the '
             'transition instead of for it, and the bridge hard-switches into '
             'a low impedance. It is the one failure mode that destroys parts '
             'rather than just heating them. <b>Where that happens is not a '
             'fixed frequency</b>: the boundary moves with load, and '
             'Section&nbsp;'
             + SR('The two boundaries are not the same boundary')
             + ' is about exactly that.'))
    add(h2('How the circuit becomes M(f<sub>n</sub>, Q)'))
    add(p('Every gain curve in every LLC note comes from three '
          'simplifications, applied in order. They are worth doing once, '
          'because each one throws something away, and it is useful to know '
          'what.'))
    add(fig('an_rac',
            'Why the rectifier and the load can be replaced by one '
            'resistance. The output is stiff, so the voltage the tank sees is '
            'a square wave; the tank filters everything except the '
            'fundamental, so the current is a sine wave. A sine of current in '
            'phase with a square of voltage delivers the same fundamental '
            'power as a resistor would take.'))
    add(fig('an_fha_steps',
            'The reduction, in three steps: as built; the secondary referred '
            'to the primary; the fundamental only. What is left is one ac '
            'network whose voltage transfer is the gain M and whose damping '
            'is Q.'))
    ext(bullets([
        '<b>Refer the secondary to the primary.</b> The ideal transformer '
        'disappears and the load resistance is multiplied by n&sup2;.',
        '<b>Replace the rectifier and the output filter by one resistor.</b> '
        'The rectifier draws a square current wave and the output is stiff, '
        'so at the fundamental frequency the whole of it looks like a '
        'resistor.',
        '<b>Keep only the fundamental of the drive.</b> The tank is a filter '
        'centred near the switching frequency, so the harmonics of the '
        'square wave contribute little. This is the <i>first harmonic '
        'approximation</i>, and it is why every LLC design ends with a '
        'simulation or a measurement rather than with the equations.']))
    add(p('What is left is one ac network: a voltage divider whose ratio '
          'changes with frequency. Two numbers describe it, and both are used '
          'on every page from here on:'))
    ext(bullets([
        '<b>The gain M</b>: the voltage across R<sub>ac</sub> divided by the '
        'fundamental that drives it. Because C<sub>r</sub> and L<sub>r</sub> '
        'cancel at the series resonance f<sub>r</sub>, <b>M = 1 there at any '
        'load</b>. Below f<sub>r</sub> the network can step up '
        '(M&nbsp;&gt;&nbsp;1); above it, it steps down.',
        '<b>The quality factor Q = Z<sub>0</sub>/R<sub>ac</sub></b>, where '
        'Z<sub>0</sub> = &radic;(L<sub>r</sub>/C<sub>r</sub>) is the '
        'characteristic impedance of the tank. Q says how heavily the tank '
        'is loaded: <b>Q rises with output power</b>. At Q = 0 (no load) the '
        'gain curve is tall and peaked; loading flattens the curve and pulls '
        'the peak down.']))
    add(p('In symbols, with f<sub>n</sub> the frequency normalised to the '
          'series resonance so that one family of curves serves every '
          'tank:'))
    add(eq(r'f_{n}=\frac{f_{sw}}{f_{r}}\,,\qquad '
           r'Z_{0}=\sqrt{\frac{L_{r}}{C_{r}}}\,,\qquad '
           r'Q=\frac{Z_{0}}{R_{ac}}\,,\qquad '
           r'\lambda=\frac{L_{r}}{L_{m}}', key='Qdef'))
    add(p('M(f<sub>n</sub>, Q) always means the gain of the right-hand '
          'circuit above.'))

    add(h2('The two resonances'))
    add(p('Every LLC has two. While the secondary conducts, the reflected '
          'output voltage clamps L<sub>m</sub> and it drops out of the '
          'circuit, leaving the series resonance'))
    add(eq(r'f_r=\frac{1}{2\pi\sqrt{L_rC_r}}', key='fr'))
    add(p('At no load nothing clamps L<sub>m</sub>, and the tank resonates '
          'with both inductances:'))
    add(eq(r'f_o=\frac{1}{2\pi\sqrt{(L_r+L_m)\,C_r}}', key='fo'))
    add(p('At f<sub>r</sub> the gain is exactly 1 for any load, because the '
          'load term disappears. At f<sub>o</sub> the no-load gain is '
          'unlimited. Between the two the tank can boost; above f<sub>r</sub> '
          'it cannot. An LLC fed from a fixed dc bus runs close to '
          'f<sub>r</sub> nearly all the time, and drops into that band only '
          'when the bus sags.'))
    add(fig('f02_two_resonances',
            'The two resonances, and the band between them in which the tank '
            'can boost. The shaded edge is the no-load position of the '
            'capacitive boundary; under load it moves up.'))

    add(p('The two expressions are not much use without knowing what each '
          'one does to the current, because the current is where the '
          'difference shows.'))
    add(p('First, the two things the circuit can be doing. Below resonance a '
          'half cycle contains both, in this order: power delivery first, '
          'then freewheeling, <b>with the same pair of switches on '
          'throughout</b>. At resonance the half cycle is power delivery '
          'only; above resonance the power delivery is cut short.'))
    add(fig('an_modes_12',
            '<b>One switching period, first half, steps 1 and 2.</b> '
            '<b>1</b>&nbsp;Power delivery &mdash; S<sub>1</sub>,S<sub>4</sub> '
            'are on, the resonant current exceeds the magnetising current '
            'and the difference passes through the transformer to '
            'D<sub>1</sub> and the load. L<sub>m</sub> is clamped to the '
            'reflected output, so this interval resonates at '
            'f<sub>r</sub>. <b>2</b>&nbsp;Freewheeling &mdash; the resonant '
            'current has fallen to the magnetising current, nothing is left '
            'for the secondary, the rectifiers are off and L<sub>m</sub> '
            'joins the resonance: this interval rings at f<sub>o</sub>. The '
            'same pair of switches is still on. Each switch is drawn with '
            'its body diode and its C<sub>oss</sub> beside it, greyed while '
            'they do nothing.'))
    add(fig('an_modes_34',
            '<b>Steps 3 and 4: the dead time.</b> <b>3</b>&nbsp;All four '
            'switches are off, so the tank current &mdash; now the '
            'magnetising current alone &mdash; can only reach the rails '
            'through the four C<sub>oss</sub>. It arrives at A from both, '
            'so A is pulled down, and leaves B into both, so B is pushed '
            'up: that swap is the transition. <b>4</b>&nbsp;The swing is '
            'complete and the body diodes of S<sub>2</sub>,S<sub>3</sub> '
            'clamp their V<sub>ds</sub> at zero. This is the ZVS window: '
            'the gate that follows has to arrive inside it.'))
    add(fig('an_modes_56',
            '<b>Second half, steps 5 and 6</b>, the mirror image of 1 and '
            '2. S<sub>2</sub>,S<sub>3</sub> carry the power delivery '
            '(<b>5</b>, through D<sub>2</sub>) and then the freewheeling '
            '(<b>6</b>), again with the same pair on throughout.'))
    add(fig('an_modes_78',
            '<b>Steps 7 and 8</b>, the second dead time. The mid-points '
            'swing back (<b>7</b>) and the body diodes of '
            'S<sub>1</sub>,S<sub>4</sub> clamp (<b>8</b>), which is where '
            'S<sub>1</sub>,S<sub>4</sub> then close on zero volts and step '
            '1 begins again. ZVS happens in steps 4 and 8, and in none of '
            'the other six.'))
    add(fig('an_modes_wave',
            '<b>Where each step sits on the waveforms.</b> The numbered '
            'bands are the eight panels above, in time order across one '
            'switching period: the gates, the two mid-point voltages, the '
            'tank and magnetising currents, and the two rectifier currents. '
            'Read a panel, then find its band here. Drawn below resonance '
            'at f<sub>sw</sub>&nbsp;/&nbsp;f<sub>r</sub> = 0.70, with the '
            'dead time wider than scale so that steps 3, 4, 7 and 8 have '
            'room to be seen; the current amplitudes are this design&rsquo;s '
            'own I<sub>Lr,pk</sub> and I<sub>Lm,pk</sub> at the low-line '
            'corner.', width=CW))
    add(note('<b>Steps 1 and 2 are the two resonances</b>, and they are the '
             'two parts of <i>one</i> half cycle: the same pair of switches '
             'stays on through both. <b>ZVS happens in neither.</b> It '
             'happens in the dead time, steps 3&ndash;4 and 7&ndash;8, when '
             'both switches of a leg are off and the tank current carries '
             'the mid-point to the other rail &mdash; the step in '
             'v<sub>d</sub> between the gate pulses in Figure&nbsp;%s.'
             % FR('an_llc_waves')))
    add(note('<b>The word &ldquo;freewheeling&rdquo; is used for two '
             'different intervals.</b> Here it means steps 2 and 6: the '
             'secondary is off, L<sub>m</sub> has rejoined the resonance, and '
             'the same pair of switches is still on. Other documents, among '
             'them Toshiba&rsquo;s <i>Resonant Circuits and Soft '
             'Switching</i> (2019), use the word for the <b>dead time</b>, '
             'when the current circulates in the body diodes. Both intervals '
             'carry current without delivering power, but the dead time '
             'exists at every frequency and steps 2 and 6 exist only below '
             'resonance. Check which one a source means before comparing '
             'numbers.'))
    add(fig('an_three_cases',
            'The three cases side by side. Gate signals, the bridge voltage, '
            'the resonant current i<sub>Lr</sub> with the magnetising '
            'current i<sub>Lm</sub> dashed over it, and the rectifier '
            'current. What changes across the three columns is how the '
            'resonant half period compares with the switching half period. '
            'Below resonance there is time left over, and it is spent '
            'freewheeling; at resonance the two coincide; above resonance '
            'the half period ends first and cuts off the rectifier current '
            'while it is still flowing.', width=CW))
    ext(bullets([
        '<b>Below f<sub>r</sub> (left).</b> The resonant half period is '
        'shorter than the switching half period. i<sub>Lr</sub> finishes its '
        'half sine early and <b>lands on i<sub>Lm</sub></b>. From that '
        'instant the two are one current and no power crosses to the '
        'secondary: that is the freewheeling interval.',
        '<b>At f<sub>r</sub> (centre).</b> The two half periods are the same '
        'length. i<sub>Lr</sub> meets i<sub>Lm</sub> exactly when the bridge '
        'switches, and the rectifier current reaches zero at the same '
        'instant. This is the most efficient point an LLC has, and it is '
        'where a conventional design puts its nominal input.',
        '<b>Above f<sub>r</sub> (right).</b> The switching half period ends '
        'first, so the resonant half sine is <b>cut off part way</b>: '
        'i<sub>Lr</sub> is still well above i<sub>Lm</sub> when the bridge '
        'switches. The primary switches turn off more current, and the '
        'rectifier is interrupted while it is still conducting: hard '
        'commutation on the secondary.']))
    add(p('<b>That freewheeling interval is what f<sub>o</sub> is.</b> '
          'While it lasts nothing clamps L<sub>m</sub>, so the tank is '
          'L<sub>r</sub> + L<sub>m</sub> with C<sub>r</sub>, ringing at '
          'f<sub>o</sub>. It looks flat only because f<sub>o</sub> is so much '
          'lower than f<sub>r</sub>. Lower the switching frequency towards '
          'f<sub>o</sub> and the interval grows until it fills the whole '
          'half period, and the converter delivers no power. So the two '
          'frequencies are the two ends of one range: at f<sub>r</sub> the '
          'flat interval has just disappeared, at f<sub>o</sub> it has taken '
          'over, and everything useful happens between them.'))
    add(note('<b>Symbols are not standard across the literature.</b> Before '
             'using a manufacturer\u2019s application note alongside this '
             'one, check which frequency that document calls f<sub>o</sub>. '
             'At least one widely used guide gives that name to the series '
             'resonance, which is the opposite of the meaning here.'))
    add(p('A conventional LLC picks one side and stays there, usually just '
          'above f<sub>r</sub> at nominal input, where the gain is close to 1 '
          'and the circulating current is smallest. Which side the converter '
          'designed here runs on is a different question. It is answered in '
          'Section&nbsp;'
          + SR('Which side of resonance this converter runs on')
          + ', once the rest of the method is in place.'))
    add(h2('The gain function and the three regions'))
    add(p('With the usual first-harmonic approximation the tank gain is'))
    add(eq(r'M(f_n,Q,\lambda)=\frac{1}'
           r'{\sqrt{\left(1+\lambda-\frac{\lambda}{f_n^{2}}\right)^{2}'
           r'+Q^{2}\left(f_n-\frac{1}{f_n}\right)^{2}}}', key='M'))
    add(p('with f<sub>n</sub>, Q and &lambda; as defined in the conventions. '
          'Two checks can be made on it by eye before trusting any curve '
          'drawn from it. At f<sub>n</sub>&nbsp;=&nbsp;1 the second term '
          'under the root disappears and the first becomes 1, so '
          '<b>M&nbsp;=&nbsp;1 at any Q</b>. That is the series resonance, and '
          'it is why every gain curve passes through the same point. <b>At '
          'no load</b> (Q&nbsp;=&nbsp;0, so the second term is gone) raising '
          'f<sub>n</sub> without limit only brings M down to 1/(1+&lambda;) '
          'and no further; that floor is the subject of Section&nbsp;%s. '
          'Under load the Q term grows with f<sub>n</sub> and the gain keeps '
          'falling towards zero.'
          % SR('The other bound on &lambda;, and where it has no solution')))
    add(p('The curve has three regions. Below the capacitive/inductive '
          'boundary the tank is capacitive and the bridge hard-switches, '
          'which must never be allowed. Between that boundary and '
          'f<sub>r</sub> the tank is inductive and boosts; above '
          'f<sub>r</sub> it is inductive and bucks. In the figure the lower '
          'boundary is drawn for the full-load curve. At no load it would '
          'sit at f<sub>o</sub>; it moves up as load is added, and the next '
          'sections are about that.'))
    add(fig('f04_three_regions',
            'The three operating regions, shaded for the full-load curve '
            'drawn. Only the inductive ones are usable, and the boundary '
            'between them moves up as the converter is loaded. Region '
            'framing after ROHM TechWeb.'))

    add(h2('Capacitive and inductive, and why those words'))
    add(p('The names have nothing to do with which component dominates. They '
          'describe <b>what the bridge sees</b>: the phase of the tank input '
          'current relative to the square wave that drives it. The tank is a '
          'series network. At low frequency C<sub>r</sub> dominates and the '
          'current <i>leads</i>: the bridge is driving something that '
          'behaves like a capacitor. At high frequency the inductances '
          'dominate and the current <i>lags</i>: the bridge is driving '
          'something that behaves like an inductor. The word describes the '
          'load the bridge works into, not a part.'))
    add(p('That phase decides whether the switching is soft or hard, which '
          'is why the distinction matters:'))
    add(fig('an_cap_ind',
            'The same converter on either side of the boundary. Above: where '
            'the boundary sits on the gain curve. Note that it is not at the '
            'peak, but a little above it. Below, for each case: the bridge '
            'voltage v<sub>d</sub>, the tank current at the phase the tank '
            'actually presents there, and <b>the drain current of the switch '
            'that is closing</b>. On the left the current leads and is '
            'positive at turn-on, and the drain current carries the recovery '
            'spike of the opposite body diode. On the right it lags and is '
            'still negative, so the switch closes on its own conducting body '
            'diode. The two drain currents are drawn to one scale.'))
    ext(bullets([
        '<b>Inductive: the current lags.</b> When a switch turns off, the '
        'current is still flowing in the direction that pushes the bridge '
        'node towards the other rail. The dead time lets it do exactly that, '
        'and the next device turns on at zero volts. <b>ZVS.</b>',
        '<b>Capacitive: the current leads.</b> By the time the switch turns '
        'off, the current has already reversed, so it pushes the node '
        '<i>back</i> where it came from. The next device then turns on into '
        'the full rail voltage. Worse, the body diode of the device that was '
        'conducting is forced off with reverse recovery through a low '
        'impedance. <b>Hard switching, and the failure mode that destroys '
        'parts.</b>']))
    add(note('This is why the capacitive region is not a performance '
             'trade-off to be balanced against something else. It is a '
             'boundary the design stays on one side of, and the controller '
             'has a dedicated protection for the case where it does not.'))

    add(h2('Why a diode has to recover on one side and not on the other'))
    add(p('The drain-current row above is the difference that reaches the '
          'hardware, so it is worth following one switching instant through '
          'in both cases. Take the leg alone: a high-side switch, a low-side '
          'switch, and the tank hanging off the mid-point. Whichever device '
          'has just been turned off, <b>the tank current does not stop</b> '
          '&mdash; it is the current in an inductor. The only question is '
          'what carries it during the dead time, and the answer decides '
          'everything.'))
    add(fig('an_recovery',
            'One switching instant in the same leg, either side of the '
            'boundary. Left: the tank current is already positive, so it is '
            'flowing in the body diode of the low-side device; when the '
            'high-side device is gated on, the rail is short-circuited '
            'through both until that diode recovers. Right: the tank current '
            'is negative, it has carried the mid-point up to the rail during '
            'the dead time, and the closing device finds its own body diode '
            'already conducting at zero volts. After ON Semiconductor '
            'AN-4151.'))
    ext(bullets([
        '<b>Inductive.</b> At turn-off the current is flowing in the '
        'direction that carries the mid-point towards the <i>other</i> rail. '
        'It charges one C<sub>oss</sub> and discharges the other, the node '
        'arrives, and the body diode of the incoming device picks the '
        'current up and holds the node there. That device is then gated on '
        'with V<sub>ds</sub> already at zero. When its channel takes over, '
        'the current in its own body diode falls away with no reverse '
        'voltage applied to it, so <b>there is nothing to recover</b>.',
        '<b>Capacitive.</b> At turn-off the current has already reversed. It '
        'pushes the mid-point back onto the rail it came from, so the body '
        'diode of the device that just turned off picks it up and clamps the '
        'node there. <b>The node never moves.</b> The incoming device is '
        'then gated on across the full rail, straight onto a conducting '
        'diode.']))
    add(p('A diode carrying forward current holds stored charge in its '
          'junction, and it cannot block reverse voltage until that charge '
          'has been swept out. For as long as that takes, both devices in '
          'the leg are conducting and the input rail is short-circuited '
          'through them. Three things follow, and all three are bad:'))
    ext(bullets([
        'The current is limited only by the stray inductance of the loop, so '
        'it is a <b>spike, not a current</b> &mdash; many times the tank '
        'current, as the drain-current row shows.',
        'It flows in the incoming device while that device still stands at '
        'the full rail voltage, so it is dissipated there, in a few tens of '
        'nanoseconds, every cycle.',
        'When the diode finally does snap off, the di/dt in the loop '
        'inductance appears across it as overshoot, which is what actually '
        'breaks the part.']))
    add(note('<b>This is the reason this note asks for a fast-recovery body '
             'diode on the primary</b> (Section&nbsp;%(ref)s). A '
             'superjunction device stores a great deal of charge in a body '
             'diode that was never designed to be commutated, and in a full '
             'bridge that diode conducts before every turn-on even when the '
             'converter is behaving. It is also the reason the oscillator '
             'floor exists: f<sub>Min</sub> above f<sub>o</sub> is what '
             'keeps the converter out of the left-hand picture, and the '
             'anti-capacitive protection is what catches it if that fails.'
             % dict(ref=SR('Semiconductor requirements'))))
    add(h2('The two boundaries are not the same boundary'))
    add(p('This is the point that is most easily confused, because both '
          'pairs of words describe positions on the same frequency axis. '
          'They are different lines on it.'))
    add(tbl('Two classifications, two boundaries, two consequences.',
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
            widths=[CW * 0.19, CW * 0.40, CW * 0.41], key='capind'))
    add(p('The peak-gain frequency sits between f<sub>o</sub> and '
          'f<sub>r</sub>, and it <b>rises as the converter is loaded</b>. At '
          'no load it coincides with f<sub>o</sub>; at full load it has moved '
          'some way up towards f<sub>r</sub>. So the capacitive region is not '
          'a fixed band below f<sub>o</sub>. It grows as load is added, and a '
          'frequency that is safely inductive at light load can be '
          'capacitive at overload.'))
    add(note('<b>The edge is not quite the gain peak.</b> The tank is '
             'capacitive while the phase of its input impedance is negative, '
             'so the edge is where <b>arg Z<sub>in</sub> = 0</b>, and that '
             'sits a little <i>above</i> the peak of the gain curve. The '
             'peak is the usual stand-in because it needs only the gain '
             'curve, but it is optimistic in the dangerous direction: it '
             'calls a band inductive while the bridge is still '
             'hard-switching. Section&nbsp;%(ref)s gives both frequencies '
             'for the worked design; the verdict there comes from '
             'Section&nbsp;%(zvsref)s, which measures the condition '
             'directly as the time the tank current takes to reach zero '
             'after the bridge changes state.'
             % dict(ref=SR('ZVS over the whole operating space'),
                    zvsref=SR('ZVS verification'))))
    add(fig('an_loadshift',
            'The boundary is not fixed. Loading the converter pushes it to a '
            'higher frequency, so a frequency that is inductive at light '
            'load can be capacitive at overload. The dashed curve is the '
            'boundary itself, traced out as Q varies.'))
    ext(bullets([
        'A converter can be <b>below f<sub>r</sub> and still inductive</b>. '
        'That is the ordinary boosting region, and it is where an LLC '
        'normally runs.',
        'It can be <b>below f<sub>r</sub> and capacitive</b>, which is the '
        'fault. Going below f<sub>r</sub> is not the danger; going below the '
        'boundary is.',
        'It cannot be <b>above f<sub>r</sub> and capacitive</b>, because the '
        'boundary is always below f<sub>r</sub>. Everything above '
        'f<sub>r</sub> is inductive at every load.']))
    add(note('<b>What this means for the design rule.</b> Keep the '
             'oscillator floor f<sub>Min</sub> above f<sub>o</sub>. That is '
             'the <i>no-load</i> position of the boundary, so it is the '
             'weakest form of the requirement: necessary, but not enough on '
             'its own. The real check is the ZVS sweep in '
             'Section&nbsp;' + SR('ZVS verification')
             + ', which is run under load and at every phase of the line '
               'cycle. Behind that, the controller has an anti-capacitive '
               'protection.'))
    add(h2('ZVS and ZCS are not the same thing'))
    add(p('Both are ways of switching a device while one of its two '
          'quantities, voltage or current, is zero, so that their product, '
          'the loss, is zero. Here they apply to different devices, for '
          'different reasons, and only one of them is guaranteed.'))
    add(fig('an_zvs_zcs',
            'Zero-voltage switching on the primary and zero-current '
            'switching on the secondary. Different devices, different '
            'mechanisms, different conditions.', width=CW))
    ext(bullets([
        '<b>ZVS, zero-voltage switching, on the primary switches.</b> The '
        'device turns on with no voltage across it. It works because the '
        'tank current is still flowing when the previous device turns off, '
        'and that current discharges the bridge node during the dead time. '
        'It needs <b>inductive operation</b>, that is, anywhere above the '
        'capacitive/inductive boundary. So it is available on both sides of '
        'f<sub>r</sub>, and f<sub>o</sub> is that limit only at no load. It '
        'is required everywhere, and Section&nbsp;' + SR('ZVS verification')
        + ' says how much margin this design has.',
        '<b>ZCS, zero-current switching, on the secondary rectifiers.</b> '
        'The device turns off with no current through it, so a diode is not '
        'forced out of conduction and a synchronous rectifier has no reverse '
        'recovery. It happens because the resonant current reaches zero by '
        'itself, which only occurs <b>below f<sub>r</sub></b>. Above '
        'f<sub>r</sub> the rectifier is cut off while it is still '
        'conducting, and reverse recovery returns.']))
    add(note('<b>So ZCS is not a property of the circuit but of the '
             'operating point.</b> Below f<sub>r</sub> the secondary '
             'rectifiers turn off at zero current and reverse recovery never '
             'appears; above f<sub>r</sub> they do not, and it does. A '
             'converter that stays on one side settles the question once. A '
             'converter whose input moves far enough to cross f<sub>r</sub> '
             'has to be checked on both sides: its secondary body diode and '
             'synchronous-rectifier dead time matter whenever it runs above '
             'f<sub>r</sub>.'))
    add(h2('Sizing the dead time so that ZVS actually happens'))
    add(p('ZVS is what makes an LLC efficient, and it is a charge problem '
          'rather than a voltage problem. During the dead time the '
          'magnetising current must move enough charge to swing the bridge '
          'node across the rail before the opposite device turns on. The '
          'design quantity is T<sub>ZC</sub>, the time the tank current '
          'takes to reach zero after the bridge transition, and the '
          'requirement is simply that it must be longer than the dead '
          'time:'))
    add(eq(r'T_{ZC}\;>\;t_D', key='zvs'))
    add(fig('f05_zvs_mechanism',
            'How ZVS happens: the magnetising current, not the load current, '
            'discharges the bridge node during the dead time. Two conditions '
            'are needed: the current must still be flowing when the gates '
            'drop (T<sub>ZC</sub> &gt; t<sub>D</sub>), and the swing must '
            'finish inside the dead time.'))
    add(note('<b>Use the output charge, not the small-signal '
             'capacitance.</b> A MOSFET datasheet quotes C<sub>oss</sub>, '
             'C<sub>o(er)</sub> and C<sub>o(tr)</sub>, and they differ by '
             'three to five times. ZVS is a charge question, so '
             '<b>C<sub>o(tr)</sub></b> (equivalently Q<sub>oss</sub>) is the '
             'one to use. Sizing the dead time from the headline '
             'C<sub>oss</sub> is optimistic by a large factor.'))
    add(h2('Not a flyback, and why that changes the core'))
    add(p('Almost everybody meets a transformer first in a flyback, and '
          'almost every habit formed there is wrong here. Two of them cost '
          'money: <b>why a core area matters at all in a converter that '
          'stores none of the energy it delivers</b>, and <b>why the '
          'saturation test current is nothing like the peak winding '
          'current</b>. Both come from one difference, which is when the '
          'two windings conduct.'))
    add(p('<b>In a flyback they never conduct together.</b> The secondary '
          'polarity dot is inverted, so the rectifier can only conduct while '
          'the switch is off. At every instant exactly one winding is '
          'carrying current, and therefore at every instant the whole '
          'winding current is magnetising current. Energy goes into the core '
          'during the on-time and comes out of it during the off-time, and '
          'every joule that reaches the output was first stored in the core. '
          'The flux follows the <i>current</i>, the core is gapped so that '
          'it can hold that energy without saturating, and A<sub>e</sub> is '
          'sized from the peak current.'))
    add(p('<b>In an LLC they conduct together.</b> While the secondary is '
          'rectifying, both windings are carrying current and their '
          'ampere-turns oppose. Only what is left after the subtraction '
          'magnetises the core:'))
    add(eq(r'N_{p}\,i_{p}\;-\;N_{s}\,i_{s}\;=\;N_{p}\,i_{\mu}', key='mmf'))
    add(p('The load current passes <i>through</i>, by transformer action; it '
          'never enters the core as stored energy. What the core does hold '
          'is the magnetising energy &frac12;L<sub>m</sub>'
          'i<sub>&mu;</sub>&sup2;, and in this converter that is not a '
          'by-product but the mechanism: i<sub>&mu;</sub> is the current '
          'that charges and discharges the bridge node during the dead '
          'time, which is to say it is what makes ZVS possible '
          '(Section&nbsp;' + SR('Sizing the dead time so that ZVS actually happens') + '). An LLC transformer is gapped too, but the gap is '
          'there to hold L<sub>m</sub> at the value the tank asked for, '
          'not to store what goes to the load.'))
    add(fig('an_flyback_llc',
            'The two transformers from the same four rows. Left: the switch '
            'and the rectifier are never on together, so whichever winding '
            'conducts carries all of the magnetising current, and the flux '
            'is a one-sided ramp that follows it. Right: both windings '
            'conduct at once, their ampere-turns oppose, and only the '
            'difference i<sub>&mu;</sub> = i<sub>p</sub> &minus; '
            'i<sub>s</sub> magnetises the core. The i<sub>s</sub> traces are '
            'referred to the primary, with the sign each polarity dot gives. '
            'In the bottom row the dashed curves are what each winding would '
            'drive on its own, the solid one is their sum, and the shaded '
            'band is what the secondary did to the core: taken away at the '
            'same instant on the right, handed over afterwards on the left.'))
    add(note('<b>&ldquo;An LLC transformer stores no energy&rdquo; is a '
             'slogan, not a statement.</b> It stores the magnetising energy, '
             'twice every switching period, and the design leans on it. What '
             'it does not store is the energy delivered to the load.'))
    add(p('So why does A<sub>e</sub> come into it at all? Because Faraday\'s '
          'law does not ask whether anything is being stored:'))
    add(eq(r'B(t)\;=\;\frac{1}{N\,A_{e}}\int v\,dt', key='faraday'))
    add(p('A winding with a voltage across it makes flux; flux in a finite '
          'area is a flux density; and ferrite saturates at a flux density. '
          'That is equally true of a flyback, an LLC, a mains transformer '
          'and a plain choke. <b>What differs is only the input to the '
          'calculation.</b> In a flyback the volt-seconds are the input '
          'voltage times the on-time, which is another way of writing the '
          'peak current. In an LLC the conducting secondary clamps the '
          'winding to the output for a resonant half period, so the '
          'volt-seconds &mdash; and with them the flux &mdash; are set by '
          'the <b>output voltage alone</b>. Section&nbsp;'
          + SR('Peak flux is set by the secondary, not the primary')
          + ' turns that into an equation with neither the input voltage '
            'nor the load in it.'))
    add(p('Three consequences follow, and they are worth having in mind '
          'long before a core is chosen:'))
    ext(bullets([
        '<b>The flux does not rise with load.</b> Twice the output current '
        'is twice i<sub>s</sub>, and the primary has to carry that extra '
        'current as well &mdash; so both grow together and their '
        'difference, i<sub>&mu;</sub>, does not move at all. (i<sub>p</sub> '
        'itself does not simply double: it is i<sub>&mu;</sub> plus the '
        'reflected load current, and only the second term grows.) A core '
        'that is adequate at full load is adequate in overload; what '
        'overload threatens is the copper and the semiconductors, not the '
        'core.',
        '<b>The flux does rise with output voltage.</b> Anything that lets '
        'V<sub>out</sub> climb raises the flux in proportion, so the ceiling '
        'to design against is the over-voltage threshold and not the nominal '
        'output.',
        '<b>The flux does not fall with switching frequency</b>, below '
        'resonance. The rectifier clamps the winding for a resonant half '
        'period T<sub>r</sub>/2 whatever f<sub>sw</sub> is doing, which is '
        'why f<sub>r</sub> and not f<sub>sw</sub> appears in the flux '
        'equation.']))
    add(p('The same difference decides what the vendor is asked to test. A '
          'DC-overlap measurement is made with the secondary open, which '
          'removes the cancellation and puts the transformer back into the '
          'flyback condition &mdash; all of the test current is magnetising '
          'current. Section&nbsp;'
          + SR('The saturation test is not the peak winding current')
          + ' takes that to a number.'))

    add(h2('How an LLC is normally designed'))
    add(p('The sequence below is the standard one, and every step exists '
          'because of something already established above. It is worth '
          'having in mind before Section&nbsp;' + SR('Design procedure')
          + ', which follows the same order and departs from it in exactly '
            'two places.'))
    ext(bullets([
        '<b>1  Turns ratio from the nominal point.</b> Choose n so that the '
        'converter runs at or near M&nbsp;=&nbsp;1 at nominal input, that '
        'is, at f<sub>r</sub>. That is where the circulating current is '
        'lowest and where the converter should normally run.',
        '<b>2  The gain range the tank must cover.</b> From the input range '
        'and the output tolerance, find M<sub>min</sub> and M<sub>max</sub>. '
        'M<sub>max</sub> is needed at minimum input and full load, '
        'M<sub>min</sub> at maximum input and minimum load.',
        '<b>3  Load resistance referred to the primary</b>, R<sub>ac</sub>, '
        'which gives Q its meaning at full load.',
        '<b>4  m (equivalently &lambda;) and Q, together, from the peak-gain '
        'chart.</b> They are not independent: for each m there is a curve '
        'of attainable peak gain against Q, and the design has to sit under '
        'that curve with margin. A larger m gives less circulating current '
        'and less peak gain; a smaller m gives the opposite.',
        '<b>5  The component values.</b> Q and R<sub>ac</sub> give '
        'Z<sub>0</sub>; Z<sub>0</sub> with the chosen f<sub>r</sub> gives '
        'C<sub>r</sub> and L<sub>r</sub>; m then gives L<sub>m</sub>.',
        '<b>6  Verify.</b> Check that the gain at the worst corner is still '
        'under the peak with margin, that ZVS holds at the worst point '
        'rather than at the nominal one, and that the currents and the flux '
        'are ones real parts can carry.']))
    add(fig('an_peakgain',
            'Step 4, and the reason m and Q cannot be chosen separately: the '
            'peak gain a tank can reach depends on both. Choosing a required '
            'gain and a Q leaves only a band of usable m.'))
    add(note('<b>That is the first half.</b> Everything above is the LLC on '
             'its own: a tank, a gain curve, and a frequency that moves the '
             'operating point along it. None of it involves the mains. The '
             'rest of this section is the other half: what a power factor '
             'corrector is for, and how the ordinary one works. It can be '
             'read without reference to any of the above. Section&nbsp;'
             + SR('Why single stage, and what it costs')
             + ' is where the two halves are put together.'))
    add(h2('What power factor correction is'))
    add(p('Start with what happens if nothing is done. A bridge rectifier '
          'feeding a capacitor holds the bus near the peak of the mains, so '
          'the diodes can only conduct during the short window in which the '
          'mains voltage is above the capacitor voltage. All the charge the '
          'load will use over the whole cycle has to arrive inside that '
          'window.'))
    add(fig('an_pfc_cap',
            'A capacitor-input rectifier and what it draws. v<sub>C</sub> '
            'stays near the crest, so the diodes conduct only in the narrow '
            'windows where the mains is above it, and the current inside '
            'them is correspondingly tall.'))
    add(p('All the consequences follow from that one fact. The peak current '
          'is several times what a resistor of the same average power would '
          'draw, so the wiring, the fuse, the bridge and the source all have '
          'to be sized for it. And a pulse train that narrow is mostly '
          'harmonics.'))
    add(h2('Power factor, and why it is not the same as distortion'))
    add(p('<b>Power factor</b> is the ratio of real power to apparent power:'))
    add(eq(r'PF=\frac{P}{V_{rms}I_{rms}}\;=\;\cos\varphi_{1}\;\times\;\frac{I_{1,rms}}{I_{rms}}'))
    add(p('It has two independent factors, and they fail for different '
          'reasons. <b>Displacement</b> is the phase between the voltage and '
          'the fundamental of the current; it is what a motor gets wrong. '
          '<b>Distortion</b> is how much of the rms current is at the '
          'fundamental at all; it is what a rectifier gets wrong. The '
          'current in the figure above is roughly in phase, so its '
          'displacement factor is near 1, and it still scores only about '
          '0.6, because the rest of the rms is harmonics.'))
    add(p('The related figure of merit is <b>total harmonic distortion</b>, '
          'the harmonic content as a fraction of the fundamental:'))
    add(eq(r'THD=\frac{\sqrt{I_{rms}^{2}-I_{1,rms}^{2}}}{I_{1,rms}}'
           r'\,,\qquad \frac{I_{1,rms}}{I_{rms}}=\frac{1}{\sqrt{1+THD^{2}}}'))
    add(note('<b>The two are not interchangeable.</b> A converter can hold '
             'PF above 0.99 and still fail a harmonic limit, because the '
             'standard limits <i>individual</i> harmonics in amperes rather '
             'than one ratio. Harmonics do not deliver power; they heat the '
             'neutral, saturate distribution transformers and disturb other '
             'equipment on the same supply, which is why they are regulated. '
             'IEC&nbsp;61000-3-2 sets the limits, and the limit depends on '
             'the class. A mains rectifier of this kind is Class&nbsp;D: '
             'exempt below 75&nbsp;W, and limited in milliamps per watt '
             'above it. <b>But Class&nbsp;D only reaches 600&nbsp;W</b>; a '
             'supply above that falls under the absolute Class&nbsp;A '
             'limits. Settle the class first.'))
    add(h2('How a corrector fixes it'))
    add(p('Force the input current to follow the input voltage, and the '
          'converter looks like a resistor to the mains: both factors go to '
          'one at once. The standard implementation is a <b>boost converter '
          'placed directly after the bridge</b>, switching fast enough that '
          'the mains looks constant within one switching cycle.'))
    add(fig('an_pfc_boost',
            'A boost corrector, with the current path traced for each half of '
            'the switching period: the reactor charges from the line while '
            'the switch is on, and delivers to the bus in series with the '
            'line while it is off.'))
    ext(bullets([
        '<b>Why a boost.</b> The input is a rectified sine that passes '
        'through zero, so the stage must be able to step up by an unlimited '
        'ratio near the zero crossing; only a boost can. Its input current is '
        'also continuous, which is what makes shaping it possible at all.',
        '<b>The inner loop</b> regulates the inductor current to a '
        'reference. It has to be fast compared with the switching frequency.',
        '<b>The outer loop</b> regulates the bus voltage, and it is '
        'deliberately made <b>slower than 2f<sub>l</sub></b>. If it were '
        'fast, it would fight the ripple on the bus, modulate the current '
        'level within the line cycle, and flatten the very shape the '
        'corrector exists to make. A slow voltage loop is not a compromise '
        'here; it is a requirement.',
        '<b>The multiplier</b> joins them: the shape comes from the mains, '
        'the level from the output. That is the whole control law.']))
    add(fig('an_pfc_ccm',
            'The result, in continuous conduction mode. Switching ripple '
            'rides on the reactor current and never brings it to zero; its '
            'average follows the input voltage, which is what the two loops '
            'were arranged to produce.'))
    add(note('<b>This comes back later.</b> Take the boost stage away and '
             'the same conflict returns in a sharper form: the outer loop is '
             'then the <i>only</i> loop, its output is a power command, and '
             'any 2f<sub>l</sub> ripple that gets through it becomes input '
             'current distortion directly. That is '
             'Section&nbsp;' + SR('Why the crossover must be low: the 2f<sub>l</sub> ripple') + '.'))
    add(p('The corrector delivers what was asked for, and creates a new '
          'problem in doing so. A current that follows the voltage means an '
          'input power that follows sin&sup2;&thinsp;&theta;: zero twice per '
          'cycle, twice the average at the crests. The load still wants '
          'constant power. <b>Something has to store the difference</b>, and '
          'where that something sits is the subject of the next section.'))
    add(h2('Why they are normally two stages'))
    add(fig('an_two_stage',
            'The usual two-stage arrangement, with the waveform at every '
            'node. The correction happens in the first block and the LLC '
            'works from the dc bus it produces &mdash; and the buffer that '
            'absorbs the twice-line-frequency pulsation sits between them, '
            'at 400&nbsp;V. The ripple on the dc nodes is drawn larger than '
            'it is.', width=CW))
    add(p('The bus capacitor between a boost PFC and an LLC does two jobs at '
          'once, and they are often confused with each other:'))
    ext(bullets([
        'it <b>buffers</b> the difference between the pulsating input power '
        'and the constant output power;',
        'it <b>isolates</b> the LLC from the mains waveform, so the tank sees '
        'a nearly constant input and has to cover only a narrow gain range.']))
    add(p('Removing the boost stage removes both services at once. The '
          'buffering has to be done somewhere else, and the tank now has to '
          'work directly from a rectified sine that goes to zero a hundred '
          'times a second. What that costs, and why it works anyway, is the '
          'rest of this note.'))
    add(h1('Why single stage, and what it costs'))
    add(note('<b>Two steps of that standard sequence are the ones this '
             'converter breaks.</b> Step&nbsp;1 has no nominal point to settle at, '
             'because the input sweeps a half sine; and step&nbsp;2 asks for '
             'a gain range that no single tank can cover, which is why the '
             'bridge itself has to change. Sections&nbsp;'
             + SR('Gain is a boundary condition, not a control variable')
             + ' and '
             + SR('Topology morphing')
             + ' are those two departures.'))
    add(h2('The energy a unity power factor cannot deliver'))
    add(p('Drawing a sinusoidal current in phase with a sinusoidal voltage '
          'makes the instantaneous input power a raised sine squared. It '
          'swings between zero and twice the average, at twice the line '
          'frequency:'))
    add(eq(r'p_{in}(t)=V_{ac}I_{ac}\,\left[\,1-\cos(2\omega_l t)\,\right]'))
    add(p('The load wants constant power. The difference has to be stored and '
          'returned a few milliseconds later. This requirement does not '
          'depend on topology; it follows from asking for unity power factor '
          'at all. Figure&nbsp;%s shows the imbalance that must be '
          'buffered.' % FR('f11_power_balance')))
    add(fig('f11_power_balance',
            'Unity power factor forces a 2f<sub>l</sub> energy imbalance. The '
            'two shaded areas are equal, and they are what a capacitor '
            'somewhere must absorb and give back.'))

    add(h2('Moving the buffer from 400 V to the output'))
    add(p('In the two-stage converter that buffer is the bus capacitor, at '
          '400&nbsp;V. In the single-stage converter there is no bus, so the '
          'buffer moves to the output. <b>The joules do not change &mdash; '
          'the voltage they sit at does</b>, and a capacitor only ever '
          'returns the energy between its starting voltage and the lowest '
          'the load will accept:'))
    add(eq(r'E=\frac{1}{2}C\left(V^{2}-V_{min}^{2}\right)'))
    add(p('Hold-up is the clearest way to see the price, because both '
          'architectures must ride out the same T<sub>hold</sub> at full '
          'power, so they must store the same energy. On a 400&nbsp;V bus '
          'that may fall to about 320&nbsp;V the usable window is '
          '400&sup2;&nbsp;&minus;&nbsp;320&sup2;; on an output of a few tens '
          'of volts that may fall to V<sub>o,min</sub> it is '
          'V<sub>out</sub>&sup2;&nbsp;&minus;&nbsp;V<sub>o,min</sub>&sup2;, '
          'smaller by a factor in the hundreds. The capacitance grows by '
          'the same factor. That single ratio is the price of the '
          'architecture, and it should be settled before anything else is '
          'designed: if the enclosure cannot house the bank, the output '
          'voltage is what has to change. Section&nbsp;%(ref)s works it out '
          'for the worked design, where ripple, not hold-up, finally sets '
          'the bank.' % dict(ref=SR('The output bank, as sized'))))
    add(note('<b>The trade in one line.</b> Removing the boost stage removes '
             'a switch, an inductor, a diode and a 400&nbsp;V electrolytic, '
             'and their losses with them. It adds a very large low-voltage '
             'capacitor bank, a 2f<sub>l</sub> ripple on the output that the '
             'load must tolerate, and a resonant tank that has to work over a '
             'much wider range. Whether that is a good trade depends almost '
             'entirely on how much output ripple the load will accept.'))

    add(h2('What the load must tolerate'))
    add(p('Because the buffer is on the output, the output carries the '
          '2f<sub>l</sub> ripple directly; there is no second stage to reject '
          'it. The ripple is set by the bank and the load, not by the control '
          'loop, and it cannot be regulated away &mdash; attempting that puts '
          'distortion on the input current instead (Section&nbsp;'
          + SR('Why the crossover must be low: the 2f<sub>l</sub> ripple')
          + '). <b>How tight the figure has to be is a property of the '
            'load, not of the converter</b>, and it has to come from the '
            'specification rather than from a design rule; the worked '
            'design allows a few per cent peak-to-peak.'))

    # =============================================================== 3
    add(h1('Operating principle'))
    add(h2('Gain is a boundary condition, not a control variable'))
    add(p('In a two-stage LLC the controller commands gain: it moves the '
          'switching frequency until the output is right. In a single-stage '
          'PFC LLC it cannot, because <b>both ports are voltage sources</b>. '
          'The output is a millifarad-class capacitor whose voltage cannot '
          'move within a switching cycle, and the input is the rectified '
          'mains, which the converter does not control either. The '
          'instantaneous gain is therefore forced:'))
    add(eq(r'M(\theta)=\frac{n\,V_{o,eff}}{V_{drive}(\theta)}'
           r'=\frac{n\,V_{o,eff}}{\sqrt{2}\,V_{ac,eq}\,\sin\theta}', key='Mreq'))
    add(p('with &theta; the line phase angle. In a two-stage converter the '
          'output voltage is free to move &mdash; the loop moves it &mdash; '
          'so commanding a gain is the same as commanding an output. Here '
          'both voltages are pinned from outside, so their ratio is fixed '
          'moment by moment and the controller cannot change it.'))
    add(p('So what does moving the switching frequency do? It moves <b>Q</b> '
          '&mdash; the loading &mdash; and Q is power. The tank is given the '
          'gain it must produce, and the frequency decides how much current '
          'it draws while doing so. <b>In this converter frequency is a power command, '
          'not a voltage command.</b>'))

    add(h2('Two divergences that cancel'))
    add(p('Near the mains zero crossing that equation looks impossible to '
          'satisfy: as &theta;&nbsp;&rarr;&nbsp;0 the required gain rises '
          'as 1/sin&thinsp;&theta; without limit. The converter survives '
          'because the load disappears at the same time. A unity-power-factor '
          'input draws power proportional to sin&sup2;&thinsp;&theta;, so'))
    add(eq(r'Q(\theta)=Q_{pk}\,\sin^{2}\theta', key='Qtheta'))
    add(p('and an unloaded (lossless) LLC has unlimited gain at its lower '
          'resonance f<sub>o</sub>. The two infinities cancel, and the '
          'operating point moves down towards f<sub>o</sub> as the mains '
          'voltage approaches zero '
          '(Section&nbsp;'
          + SR('Which side of resonance this design runs on')
          + ' draws it for the worked design). <b>f<sub>o</sub> is '
            'therefore the frequency floor of the '
            'entire design</b>, and putting the oscillator clamp below it is '
            'one of the few mistakes that destroys hardware.'))
    add(h2('Frequency modulation is the power factor correction'))
    add(p('Putting these together gives the control law. Over a line half '
          'cycle the controller sweeps the switching frequency so the power '
          'drawn follows sin&sup2;&thinsp;&theta;. There is no current loop, '
          'no multiplier and no separate PFC stage: <b>the frequency profile '
          'f<sub>sw</sub>(&theta;) is the power factor correction</b>. '
          'Section&nbsp;%s shows the profile of the worked design over the '
          'whole equivalent input range.'
          % SR('Which side of resonance this design runs on')))
    add(p('Computing that profile seems to need a numerical root '
          'search: at each &theta; the gain equation has to be solved for '
          'f<sub>n</sub>, and it has two roots: a capacitive one and an '
          'inductive one. <b>It does not.</b> Substituting '
          'M<sub>req</sub> = M<sub>pk</sub>/sin&thinsp;&theta; and '
          'Q = Q<sub>pk</sub>sin&sup2;&thinsp;&theta; and writing '
          'x = 1/f<sub>n</sub>&sup2; turns the gain equation into a cubic '
          'in x:'))
    add(eq(r'\lambda^{2}x^{3}+(q-2\lambda(1+\lambda))x^{2}'
           r'+((1+\lambda)^{2}-2q-\frac{u}{M_{pk}^{2}})x+q=0,'
           r'\qquad u=\sin^{2}\theta,\;\; q=Q_{pk}^{2}u^{2}', key='cubic'))
    add(p('One root is always negative: the cubic equals +q&nbsp;&gt;&nbsp;0 '
          'at x&nbsp;= 0 and goes to &minus;&infin; as x goes to '
          '&minus;&infin;, so it crosses zero somewhere below x&nbsp;= 0. '
          'The other two roots are where one curve is crossed twice. For '
          'x&nbsp;&gt; 0 the inverse gain 1/M&sup2; of the tank, as a '
          'function of x, starts at infinity, falls to a single minimum '
          'and rises again. So a required gain that the tank can produce '
          'is met at <b>exactly two</b> positive values of x: the capacitive '
          'crossing and the inductive one. All three roots are then real. '
          'The physical, inductive root is the <b>middle</b> one, because '
          'x&nbsp;= 1/f<sub>n</sub>&sup2; decreases as frequency increases. '
          'There is no branch to choose: in the trigonometric form of '
          'Cardano it is always the k&nbsp;= 1 branch. If the required gain '
          'is below that minimum there is no positive root at all, which is '
          'the no-solution case of Section&nbsp;'
          + SR('The other bound on &lambda;, and where it has no solution')
          + ' rather than a numerical failure.'))
    add(note('<b>Why this matters beyond elegance.</b> A grid search needs an '
             'upper bound on f<sub>n</sub>, and a bound taken from the ac '
             'maximum instead of the morphing corner quietly leaves out '
             'the real operating point. The closed form has no '
             'grid, no bracket and no starting guess, so that failure '
             'cannot happen. The inverse problem &mdash; finding the '
             'sin&sup2;&thinsp;&theta; that gives a required f<sub>n</sub> '
             '&mdash; is a quadratic and is also exact.'))

    add(note('<b>The zero-crossing dead zone.</b> Very near &theta;&nbsp;= 0 '
             'the required gain exceeds anything the tank can produce and the '
             'converter simply stops drawing current. This is inherent to the '
             'topology and shows up as third-harmonic distortion on the input '
             'current. It is one of two mechanisms that set the achievable '
             'THD; the other is the voltage loop (Section&nbsp;%s).'
             % SR('Voltage loop and compensation')))

    add(h2('The feedback pin is a power command'))
    add(p('Combining the burst-mode expression in the datasheet with the '
          'multiplier in the block diagram gives the physical meaning of the '
          'feedback voltage. It is not an error signal in the usual sense:'))
    add(eq(r'V_{FB}\;=\;V_{os}+\frac{2K_{HV}}{K_{M}K_{FF}}\,R_{CS}\,P_{in}'
           r'\;=\;0.5\,\mathrm{V}+0.167\,'
           r'\frac{\mathrm{V}}{\Omega\cdot\mathrm{W}}\,R_{CS}\,P_{in}', key='VFB'))
    add(p('Substituting the 2.8&nbsp;V feedback span gives '
          '2.8/0.167 = 16.8&nbsp;&Omega;&middot;W, which is exactly the '
          'maximum-power rule in the datasheet. <b>Maximum power limiting, '
          'burst entry and overload detection therefore all sit on one '
          'scale</b>, and that scale is R<sub>CS</sub>. The outer '
          'optocoupler loop commands an <i>input power</i>; the internal loop '
          'distributes that power over the line cycle as '
          'sin&sup2;&thinsp;&theta;.'))
    add(note('This is why the current-sense pin tolerates no filter and no '
             'series resistor. The maximum-power law and the over-current '
             'threshold read the same pin, so anything that shifts it shifts '
             'both.'))

    add(h2('Which side of resonance this converter runs on'))
    add(p('Section&nbsp;%s left this question open. Now it can be answered: '
          'a single-stage converter does not pick one side. The equivalent '
          'input follows a half sine every 10&nbsp;ms, the required gain '
          'follows it, and the operating point crosses f<sub>r</sub> and '
          'comes back within one line cycle. How much of the cycle it spends '
          'on each side depends on the mains voltage.'
          % SR('The two resonances')))
    add(p('Section&nbsp;' + SR('Which side of resonance this design runs on')
          + ' shows the profile of the worked design at four inputs.'))
    add(note('<b>Both sides have to be designed for.</b> The boosting side '
             'sets the gain requirement and the ZVS margin. The bucking side '
             'sets the top switching frequency, and it takes the secondary '
             'out of zero-current switching &mdash; so the rectifier body '
             'diode and the SR dead time matter here in a way they do not in '
             'a conventional LLC. A design checked only at the line peak, or '
             'only at low line, has checked only one of the two.'))

    add(h2('Why &lambda; must be about 0.5'))
    add(p('A classic LLC uses m&nbsp;=&nbsp;L<sub>p</sub>/L<sub>r</sub> '
          'between 5 and 10, that is &lambda; between 0.11 and 0.25. A '
          'single-stage converter cannot: it has to produce very high gain '
          'near the zero crossing, and peak gain falls as &lambda; falls. '
          'The evaluation board ST publishes for this part runs '
          '&lambda;&nbsp;=&nbsp;0.500, and the worked design comes out close '
          'to it (Section&nbsp;%s): the value comes from the topology, not '
          'from one particular design.'
          % SR('Following the numbers through')))
    add(p('The price is circulating current. A small L<sub>m</sub> means a '
          'large magnetising current that carries no power but does carry '
          'conduction loss, at every load. <b>A single-stage PFC LLC is less '
          'efficient than a two-stage LLC, and that is inherent rather than a '
          'design defect.</b>'))

    add(h2('f<sub>sw,max</sub> does not check the tank &mdash; it computes it'))
    add(p('Two of the four candidates for &lambda; carry the specified '
          'maximum switching frequency in a denominator:'))
    add(eq(r'\lambda_{2}=\frac{\lambda_{1}}'
           r'{1-\left(\frac{f_r}{f_{sw,max}}\right)^{2}}'
           r'\qquad\qquad'
           r'\lambda_{TD}=\frac{\lambda_{1}}'
           r'{1-\frac{\pi^{2}}{8}\left(\frac{f_r}{f_{sw,max}}\right)^{2}}', key='lam'))
    add(p('&lambda;<sub>1</sub> is the plain minimum-gain condition. The other '
          'two are the same condition with the frequency ceiling folded in: '
          'the tank has to reach the lowest required gain <i>before</i> it '
          'runs out of frequency. With the usual f<sub>sw,max</sub> = '
          '1.5&nbsp;f<sub>r</sub> the squared ratio is 0.44, both '
          'denominators fall well below one, and <b>the number typed as '
          'f<sub>sw,max</sub> roughly doubles the &lambda; the tank is asked '
          'for</b>. Set it close to f<sub>r</sub> and the denominators go to '
          'zero and the required &lambda; to infinity.'))
    add(note('<b>So where does f<sub>sw,max</sub> come from?</b> The common '
             'rule is 1.5&nbsp;&times;&nbsp;f<sub>r</sub>. It is a '
             '<b>choice</b>, not a limit &mdash; and it sits upstream of the '
             'tank, so changing it changes L<sub>m</sub>. A maximum in a '
             'design sheet usually only checks a result; this one is an '
             'input, so a round number typed into it changes the tank '
             'without anyone noticing.'))
    add(p('It should not be confused with f<sub>Max</sub>, the oscillator '
          'ceiling. That one <i>is</i> a limit: R<sub>T</sub>, C<sub>T</sub> '
          'and the idle time fix it in silicon, the control loop cannot push '
          'past it however much gain it wants, and it is checked after the '
          'fact by k<sub>ceil</sub> (Section&nbsp;%s). The two sit at '
          'opposite ends of the design: one decides the tank, the other '
          'reports whether the oscillator can serve it.'
          % SR('What a verification margin is')))

    add(h2('The other bound on &lambda;, and where it has no solution'))
    add(p('The condition above sets a floor under &lambda;. The ceiling comes '
          'from the opposite end: the tank must also be able to reach the '
          '<i>lowest</i> required gain, which happens at the highest '
          'equivalent input and no load. That is where the usual design rule '
          'quietly breaks down, because the no-load gain of an LLC does not '
          'fall without limit. Raising the frequency only brings it down '
          'towards a limit (an asymptote):'))
    add(eq(r'M_{\infty}\;=\;\lim_{f\to\infty}M_{no\;load}'
           r'\;=\;\frac{1}{1+\lambda}', key='Minf'))
    add(p('<b>If the required minimum gain lies below M<sub>&infin;</sub>, no '
          'frequency satisfies the condition at all.</b> A spreadsheet '
          'solving for that frequency returns an error rather than a number, '
          'and the error is easy to mistake for a broken formula. It is not: '
          'the question simply has no answer.'))
    add(p('Whether a given tank sits above or below the asymptote is a '
          'matter of a per cent or so, and no full-load check shows it; '
          'Section&nbsp;%s reports it for the worked design.'
          % SR('Following the numbers through')))
    add(note('Losing the solution is not a failure. No load at high line is '
             'the region <b>burst mode</b> owns, not frequency control. Under '
             'load the gain curve falls further and the corner arrives '
             'sooner, so every full-load check is unaffected &mdash; which is '
             'exactly why this can go unnoticed. What matters is to know which '
             'of the candidate turns ratios can still regulate by frequency '
             'alone at no load, because no full-load number shows it.'))

    # =============================================================== 4
    add(h1('Topology morphing'))
    add(p('A resonant tank has a usable gain range of roughly 1.5:1 at full '
          'load. A universal mains asks for 2.93:1. No single tank covers '
          'that and keeps ZVS, so the L6790A changes the bridge instead.'))
    add(p('Below a mains peak of 235&nbsp;V the part runs a <b>full '
          'bridge</b>, which drives the tank with twice the rail. Above '
          '245&nbsp;V<sub>pk</sub> it runs a <b>half bridge</b>. The tank '
          'therefore sees %(Veqlo).1f to %(Veqhi).1f&nbsp;Vac equivalent, a '
          'range of 1.92:1, and one tank can cover it.' % V))
    add(fig('f13_morphing',
            'Morphing collapses a 2.93:1 mains range into a 1.92:1 range at '
            'the tank. The worst corners are the morphing edges, not the ends '
            'of the mains range.'))

    add(h2('Full bridge'))
    add(p('Diagonal pairs conduct together. S1 and S4 put +V<sub>in</sub> '
          'across the tank, S2 and S3 put &minus;V<sub>in</sub> across it, so '
          'the drive is a square wave of amplitude V<sub>in</sub> and its '
          'fundamental is (4/&pi;)&thinsp;V<sub>in</sub>. All four devices '
          'switch, and each carries the tank current for half of every '
          'period.'))
    add(fig('f15_bridge_fb',
            'Full bridge: conduction path in each half period, and the '
            'resulting tank drive.'))

    add(h2('Half bridge'))
    add(p('LOUT2 is held statically high. S3 never turns on and S4 never '
          'turns off, so the leg-2 midpoint becomes ground and the bridge '
          'output swings between 0 and V<sub>in</sub>. C<sub>r</sub> is '
          'already in series with the tank, so it blocks the '
          'V<sub>in</sub>/2 of dc for free and the tank sees '
          '&plusmn;V<sub>in</sub>/2 &mdash; a fundamental of '
          '(2/&pi;)&thinsp;V<sub>in</sub>, exactly half. No extra hardware is '
          'involved.'))
    add(fig('f16_bridge_hb',
            'Half bridge: leg 2 stops switching, and C<sub>r</sub> removes '
            'the dc that the asymmetric drive creates.'))
    add(note('<b>The standing device is the hottest one.</b> S4 never '
             'switches, but it conducts the full tank current continuously. '
             'It is easy to overlook exactly because it is not switching, '
             'and in the worked design it is the single largest loss item '
             '(Section&nbsp;' + SR('Where the power goes') + ').'))

    add(h2('How the controller does it'))
    add(p('Only one gate signal changes between the two modes, which is why '
          'morphing costs nothing in hardware. The thresholds themselves are '
          '<b>fixed constants inside the IC</b> and cannot be moved by the '
          'designer; R<sub>CFG</sub> decides only whether morphing is enabled '
          'at all and where the brown-out threshold sits.'))
    add(fig('f17_morph_gates',
            'The four bridge drive signals in each mode. LOUT2 held high is '
            'the entire mechanism.'))

    add(h2('The hysteresis band, and the range it really implies'))
    add(p('The two thresholds are not the same number: the part drops to half '
          'bridge at 245&nbsp;V<sub>pk</sub> going up and returns to full '
          'bridge at 235&nbsp;V<sub>pk</sub> coming down. The 10&nbsp;V of '
          'hysteresis stops the mode from toggling back and forth at the '
          'threshold, but it also means that <b>between 235 and '
          '245&nbsp;V<sub>pk</sub> the '
          'mains voltage alone does not determine the mode</b> &mdash; the '
          'direction of travel does.'))
    add(p('Taking each threshold on the side where its mode is '
          'guaranteed gives the design range %(Veqlo).1f to '
          '%(Veqhi).1f&nbsp;Vac (1.92:1). Including the band gives '
          '<b>%(Veqlo2).1f to %(Veqhi2).1f&nbsp;Vac (2.08:1)</b>. This design '
          'passes every check at the wider range as well, but a design with '
          'less margin would not, and the narrower figure must not be used '
          'when tightening a specification.' % V))
    add(fig('f18_morph_levels',
            'Where each mode applies. Inside the band the mode depends on '
            'which direction the mains arrived from.'))
    add(note('<b>Where you will actually meet the band.</b> Real mains never '
             'sits at 166 to 173&nbsp;Vrms, so in service the mode is settled '
             'at start-up and stays. The band is met on a programmable ac '
             'source and in line dip and surge testing. Test it with a '
             '<b>step</b> across the threshold, not a ramp &mdash; a ramp '
             'gives the voltage loop time to follow, and a step does not.'))
    add(note('<b>Transition transient.</b> Crossing a threshold changes the '
             'tank drive 2:1 within one line cycle, and f<sub>sw</sub> must '
             'follow it against a voltage loop that crosses in the tens of '
             'hertz. The output droops until the loop recovers. This event '
             'is <b>less severe than the hold-up case</b>, which removes '
             'power entirely for T<sub>hold</sub> and is already met, so it '
             'is not a reason to enlarge C<sub>out</sub> or speed up the '
             'loop. That comparison has not yet been checked in the time '
             'domain, by simulation or by measurement.'))

    # =============================================================== 5
    # the sweep populates ZVS_WORST, which the summary tables of the
    # design example read before the grid itself is printed
    _zvs_grid(A)

    add(h1('Design procedure'))
    add(fig('bom_power_stage',
            'The complete power stage. The bridge rectifier feeds the '
            'half/full-bridge leg pair directly &mdash; there is no bulk '
            'capacitor and no boost stage. The secondary is drawn both ways: '
            'centre tap (Solution&nbsp;1) and full bridge (Solution&nbsp;2).',
            width=CW))
    add(p('Pick the secondary before the tank: it sets N<sub>rect</sub>, and '
          'N<sub>rect</sub> sets the reflected voltage. A centre tap puts one '
          'device in the conduction path, a full bridge puts two, so at a low '
          'output voltage the centre tap halves the secondary conduction '
          'loss. The price is twice the reverse voltage on each device, and a '
          'secondary winding that works only half of the time. This design '
          'uses the centre tap.'))
    add(p('The sequence below is the order in which the quantities actually '
          'depend on one another. Working out of order will produce a tank '
          'that has to be redone.'))

    add(h2('The specification'))
    add(p('The worked example in Section&nbsp;%(ref)s states the '
          'specification in full, sorted by what kind of number each one is; '
          'the procedure below refers to it but does not repeat it. Two '
          'qualifiers matter to every step here: <b>the worst line frequency '
          'is the lowest</b>, so everything that depends on f<sub>l</sub> '
          'uses f<sub>l,min</sub>, and <b>hold-up is specified at the worst '
          'line phase</b>, the ripple trough.'
          % dict(V, ref=SR('The specification, sorted by what kind of number '
                           'it is'))))

    add(h2('The equivalent input range'))
    add(p('This is the step that is most often done wrong. With morphing the tank does '
          'not see 90&nbsp;Vac at the bottom and %(Vacmax).0f&nbsp;Vac at the '
          'top. It sees an <b>equivalent</b> input given by the bridge mode:'
          % V))
    # matplotlib mathtext has no cases environment and no \text
    add(eq(r'V_{ac,eq}=2\,V_{ac}\;\;\mathrm{(full\;bridge)}'
           r'\;\;\;\;\;\;\;\;V_{ac,eq}=V_{ac}\;\;\mathrm{(half\;bridge)}', key='Veq'))
    add(p('At the half-bridge edge the mains is 245&nbsp;V<sub>pk</sub> and '
          'the tank sees %(Veqlo).1f&nbsp;Vac equivalent; at the full-bridge '
          'edge the mains is 235&nbsp;V<sub>pk</sub> in full bridge and the '
          'tank sees %(Veqhi).1f&nbsp;Vac equivalent. <b>These two edges are '
          'the design corners, not the ends of the mains range:</b> the low '
          'edge is the worst case for gain and ZVS, the high edge for '
          'switching frequency.' % V))

    add(h2('Turns ratio and reflected voltage'))
    add(p('The turns ratio only ever appears multiplied by the effective '
          'output voltage, so what matters is the <b>reflected voltage</b>:'))
    add(eq(r'V_{refl}=n\,V_{o,eff}=n\left(V_{out}+N_{rect}V_{f}\right)', key='Vrefl'))
    add(p('Two ratios have to be kept apart: <b>n</b> is the '
          'equivalent-model ratio in the gain equation, <b>n<sub>T</sub></b> '
          'the physical turns ratio with the leakage folded into '
          'L<sub>r</sub>. At &lambda;&nbsp;&asymp;&nbsp;0.5 they differ by '
          'more than 20&nbsp;%%; Section&nbsp;%(ref)s has the relation, and '
          'the transformer drawing must carry open- and short-circuit '
          'inductance as well as turns.'
          % dict(ref=SR('Two ratios, two inductances'))))

    add(h2('The resonant tank'))
    add(p('The equivalent ac load resistance for a centre-tapped secondary '
          'is'))
    add(eq(r'R_{ac}=\frac{4}{\pi^{2}}\,'
           r'\frac{n^{2}V_{o,eff}^{2}}{P_{in,LLC}}', key='Rac'))
    add(p('with P<sub>in,LLC</sub> the power into the resonant stage. The '
          '4 is the usual 8 with the <i>line-peak</i> power 2P in the '
          'denominator rather than the average &mdash; see the note below.'))
    add(p('The gain requirement at the low equivalent corner and the ZVS '
          'requirement together cap the quality factor at Q<sub>ZVS</sub>, '
          'and R<sub>ac</sub>Q<sub>ZVS</sub> is then the impedance the tank '
          'is <i>sized</i> from: it fixes C<sub>r</sub> through '
          'equation&nbsp;%(e)s, and C<sub>r</sub> with the target '
          'f<sub>r</sub> fixes L<sub>r</sub>. Three rules govern what happens '
          'next, and they matter more than the arithmetic:'
          % dict(e=ER('fr'))))
    ext(bullets([
        'The three <i>calculated</i> figures are not one tank. C<sub>r</sub> '
        'comes from the design impedance; L<sub>r</sub> is then whatever '
        'pairs with the <b>selected</b> C<sub>r</sub>, which is why it is not '
        'R<sub>ac</sub>Q<sub>ZVS</sub>/2&pi;f<sub>r</sub>; and the '
        'L<sub>m</sub> figure is L<sub>r</sub> divided by the &lambda; that '
        '<i>no load at the high corner</i> asks for &mdash; a condition a '
        'design may knowingly not meet (Section&nbsp;'
        + SR('The other bound on &lambda;, and where it has no solution')
        + '), so it is not a value to round towards.',
        '<b>Never round L<sub>m</sub> up.</b> That lowers &lambda; and takes '
        'the ZVS margin with it. C<sub>r</sub> above its calculated value and '
        'L<sub>m</sub> below have the opposite effect: Q<sub>pk</sub> falls '
        'and &lambda; is held.',
        '<b>Stay below the Q<sub>ZVS</sub> cap, not on it.</b> That gap '
        'is where most of a design&rsquo;s ZVS margin comes from, and it is a '
        'deliberate choice, not an accident of rounding. L<sub>m</sub> is chosen '
        'together with n so that n<sub>T</sub>&nbsp;=&nbsp;'
        'n&radic;(1+&lambda;<sub>act</sub>) lands on a ratio that can '
        'actually be wound.']))
    add(note('<b>The same expression, evaluated at the line peak.</b> Every '
             'LLC text writes R<sub>ac</sub> = '
             '(8/&pi;&sup2;)n&sup2;V<sub>o</sub>&sup2;/P with the one output '
             'power a two-stage converter has. Here the drawn power is '
             'p(&theta;) = 2P&thinsp;sin&sup2;&thinsp;&theta;, so R<sub>ac</sub> '
             'has to be pinned to one instant. Pinned to the <b>line peak</b>, '
             'where p = 2P and the tank is most heavily loaded, the 8 becomes '
             'a 4. It is not a different formula and it has nothing to do with '
             'half against full bridge &mdash; the bridge factor belongs to '
             'the equivalent input voltage. Q then means the quality factor '
             'at the line peak, with Q(&theta;) = Q<sub>pk</sub>'
             'sin&sup2;&thinsp;&theta; elsewhere. Using the two-stage value '
             'understates the loading by two, and every tank value that '
             'follows is wrong.'))

    add(h2('ZVS verification'))
    add(p('The closed-form ZVS estimate in most design guides is a fitted '
          'approximation evaluated at the design Q<sub>ZVS</sub>, not at the '
          'Q the converter runs at. Against a full sweep it errs in '
          '<b>either</b> direction by tens of per cent, and the sign depends '
          'on the tank; optimistic is the dangerous direction, because it '
          'reports ZVS margin that is not there.'))
    add(note('<b>And it has to be told which &lambda; to use.</b> The shortcut '
             'is written with a bare &lambda;, and it means the <i>design</i> '
             '&lambda; &mdash; the largest of the four candidates &mdash; '
             'together with the design Q<sub>ZVS</sub>. Read the same '
             'expression with &lambda;<sub>act</sub>, which is what the '
             'symbol means everywhere after the tank is chosen, and the phase '
             'can come out <b>negative</b> &mdash; a capacitive answer for '
             'a tank that is well inside the inductive region. The sweep carries no such '
             'ambiguity: it uses &lambda;<sub>act</sub> and the Q of the '
             'moment, which is what the hardware has.'))
    add(p('The reliable procedure is to sweep &theta;, input voltage and '
          'load with the <b>selected</b> tank and take the minimum. '
          'Section&nbsp;%(ref)s runs it for this design, with numbers on both '
          'directions of the closed-form error, and the worst point is not '
          'where one would expect.'
          % dict(ref=SR('ZVS over the whole operating space'))))

    add(h2('Which side of resonance the converter runs on'))
    add(p('Below f<sub>r</sub> the secondary current is a truncated sine with '
          'a dead interval and the conduction ratio d = '
          'f<sub>sw</sub>/f<sub>r</sub> is less than one; above f<sub>r</sub> '
          'the current is continuous and d clamps at one. The rms figures '
          'that ratings and losses are built on contain d, so the difference '
          'is real, not a matter of words.'))
    add(p('<b>Which side of resonance the converter runs on is not a '
          'separate choice. The turns ratio decides it.</b> The demand is '
          'M<sub>req</sub> = '
          '2nV<sub>o,eff</sub>/(&radic;2&nbsp;V<sub>eq</sub>), so a larger n '
          'asks for more gain, and more gain means further below resonance. '
          'Two candidate transformers on the same tank can end up on opposite '
          'sides of f<sub>r</sub> at the same mains voltage.'))
    add(note('Worth settling before the transformer is ordered. Comparing '
             'candidate turns ratios on gain margin alone hides it, and the '
             'two sides do not stress the secondary the same way: below '
             'resonance the rectifiers turn off at zero current, above it '
             'they do not.'))

    add(h2('Currents over the line cycle'))
    add(p('Ratings come from the worst switching cycle; losses come from the '
          'line-cycle rms. They are different numbers and must not be '
          'confused. Two further rules apply to a single-stage converter in '
          'particular.'))
    ext(bullets([
        'The <b>composite</b> tank current is what the primary devices and '
        'the sense resistor see. It is the sum of the reflected load current '
        'and the magnetising current, and its peak is neither the sum nor the '
        'larger of the two peaks, because they occur at different instants.',
        'Below resonance the secondary conducts for only '
        'd&nbsp;=&nbsp;f<sub>sw</sub>/f<sub>r</sub> of each half period. '
        'Omitting that conduction ratio over-estimates the rms, and the '
        'loss by the square of that.']))
    add(p('Section&nbsp;' + SR('The currents this design has to carry')
          + ' draws the composite current of the worked design.'))
    add(h2('The transformer'))
    add(p('The tank has fixed L<sub>r</sub>, L<sub>m</sub> and a ratio; the '
          'transformer has turns, an open-circuit inductance and a leakage. '
          'Getting from one to the other is where most of the errors in a '
          'resonant design are made, because <b>two different turns ratios '
          'and two different inductances carry almost the same names</b>. '
          'Section&nbsp;'
          + SR('Not a flyback, and why that changes the core')
          + ' has already set out why this transformer is sized the way it '
            'is; this section turns that into the numbers a supplier can '
            'measure.'))
    add(p('Every number on the drawing is read off one of three waveforms '
          '&mdash; the primary winding current, the current in each '
          'secondary winding, and the secondary winding voltage &mdash; or '
          'off one bench test. Figure&nbsp;%(f)s, in the design example, '
          'marks where on the worked design&rsquo;s waveforms, and '
          'Table&nbsp;%(t)s says what each mark sets and over which interval '
          'it is taken. The sections that follow derive the entries.'
          % dict(f=FR('an_xfmr_read'), t=TR('xfmr-read'))))
    _J = _CORE.J_CU
    add(tbl('What each mark in the figure sets. Currents are per unit of '
            'the assembly: the primaries are in series and the secondaries '
            'in parallel.',
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
              'then over the line half cycle. Every unit carries the same '
              'current: the primaries are in series.',
              'Primary copper: A<sub>cu</sub> = I<sub>rms</sub>/J per unit'],
             ['<b>3</b>', 'Magnetising peak',
              'The dashed i<sub>Lm</sub> at the switching instant. Below '
              'resonance it depends on neither f<sub>sw</sub> nor load, '
              'only on V<sub>out</sub>, so it is the same on every cycle.',
              'The peak flux; and, scaled to V<sub>OVP2</sub>, the '
              'DC-overlap test current (mark 7)'],
             ['<b>4</b>', 'Secondary peak current',
              'Top of the pulse in either secondary winding, same worst '
              'cycle. Per unit it is 1/N<sub>x</sub> of the rectifier-leg '
              'value: the secondaries are in parallel.',
              'Rectifier peak rating; the foil termination'],
             ['<b>5</b>', 'Secondary rms current, each winding',
              'One pulse per period in each winding, so the rms is taken '
              'over the whole period with the idle half counted, then over '
              'the line half cycle.',
              'Secondary copper: A<sub>cu</sub> = I<sub>rms</sub>/J, per '
              'winding and per unit'],
             ['<b>6</b>', 'Winding volt-seconds',
              'The secondary winding voltage is V<sub>out</sub> for the '
              'resonant half period T<sub>r</sub>/2 while the rectifier '
              'conducts. That area is the flux swing 2&thinsp;N<sub>s</sub>'
              'A<sub>e</sub>B<sub>pk</sub>; f<sub>r</sub> is the worst case '
              'because the interval never gets longer than T<sub>r</sub>/2.',
              'Core area and N<sub>s</sub>: A<sub>e</sub> &ge; '
              'V<sub>out</sub>/(4 f<sub>r</sub> N<sub>s</sub> B<sub>max</sub>)'],
             ['<b>7</b>', 'DC-overlap (saturation) test',
              'Not a waveform. Secondaries open, dc current in the primary, '
              'inductance at the primary read against current. The test '
              'current is mark 3 scaled to the highest output the controller '
              'allows, V<sub>OVP2</sub>/V<sub>out</sub>.',
              'Core saturation margin; the number the supplier tests to'],
             ['&mdash;', 'L<sub>open</sub>, L<sub>short</sub>',
              'LCR meter at the primary with the secondaries open, then '
              'shorted. Terminal quantities, so a supplier can test them.',
              'L<sub>m</sub> + L<sub>r</sub> and L<sub>r</sub>: the tank '
              'itself']],
            widths=[CW * 0.07, CW * 0.17, CW * 0.48, CW * 0.28],
            key='xfmr-read'))

    add(h2('Two ratios, two inductances'))
    add(p('When all of the leakage is referred to the primary, the tank sees '
          'an ideal transformer of ratio n, a series L<sub>r</sub> and a '
          'shunt L<sub>m</sub>. That n is <b>not</b> the wound ratio. With k '
          'the coupling coefficient,'))
    add(eq(r'n \;=\; k\,n_{T},\qquad k \;=\; \sqrt{\frac{L_{m}}{L_{m}+L_{r}}}'
           r'\;=\;\frac{1}{\sqrt{1+\lambda}}', key='nnT'))
    add(p('so n<sub>T</sub> = n &radic;(1+&lambda;). At &lambda; &asymp; 0.5 '
          'the two differ by more than 20&nbsp;%%, which is far more than any '
          'gain margin.' % {}))
    add(p('The same split appears in the inductances. The tank model uses '
          'L<sub>r</sub> and L<sub>m</sub>; the physical transformer is '
          'described by a magnetising inductance L<sub>&mu;</sub> with '
          'leakage on both sides:'))
    add(eq(r'L_{\mu}=\sqrt{L_{m}\,(L_{m}+L_{r})}\,,\qquad '
           r'L_{L1}=L_{m}+L_{r}-L_{\mu}\,,\qquad '
           r'L_{L2}=\frac{L_{L1}}{n_{T}^{2}}', key='Lmu'))
    add(fig('an_integrated',
            'The same transformer drawn both ways. Above, as wound: the '
            'leakage split between the two sides, the <b>physical</b> '
            'magnetising inductance L<sub>&mu;</sub> in shunt, and the '
            'wound ratio n<sub>T</sub>&nbsp;:&nbsp;1. Below, referred to '
            'the primary: one L<sub>r</sub>, one L<sub>m</sub>, and an '
            'ideal ratio n&nbsp;:&nbsp;1 that is no longer the wound one. '
            'The two shunt elements are not the same number &mdash; '
            'L<sub>&mu;</sub> = &radic;(L<sub>m</sub>(L<sub>m</sub>+'
            'L<sub>r</sub>)) &mdash; and neither are the two ratios.'))
    add(note('That three-element form assumes the leakage splits evenly '
             'between the two sides. The real split is set by the winding '
             'arrangement rather than by the design, and it does not matter: '
             'the tank sees only the two quantities a meter can read.'))

    add(h2('What the transformer specification must say'))
    add(p('Only two inductances are measurable at terminals, and they are '
          'exactly the two the tank needs:'))
    add(eq(r'L_{open}=L_{\mu}+L_{L1}=L_{m}+L_{r},\qquad '
           r'L_{short}=L_{L1}+\frac{L_{\mu}\,n_{T}^{2}L_{L2}}'
           r'{L_{\mu}+n_{T}^{2}L_{L2}}=L_{r}', key='Lopen'))
    add(p('L<sub>open</sub> is read at the primary with every other winding '
          'open, L<sub>short</sub> with the secondary shorted. <b>Specify '
          'those two and the turns, never L<sub>&mu;</sub></b> &mdash; no '
          'terminal pair exposes L<sub>&mu;</sub>, so a supplier cannot test '
          'it, and a part that meets it can still miss the tank. Also state '
          'the turns as numbers: with one or two secondary turns, the '
          'inductance of that winding is dominated by the lead-out loop, '
          'so &radic;(L<sub>1</sub>/L<sub>2</sub>) does not give the turns '
          'ratio.'))

    add(h2('Peak flux is set by the secondary, not the primary'))
    add(p('Mark <b>6</b> of Figure&nbsp;%(f)s: the secondary winding voltage '
          'is a rectangle of height V<sub>out</sub> and width T<sub>r</sub>/2, '
          'and the flux swings from &minus;B<sub>pk</sub> to +B<sub>pk</sub> '
          'across it. The equation is that area divided by 2&thinsp;'
          'N<sub>s</sub>A<sub>e</sub>, and nothing else enters.'
          % dict(f=FR('an_xfmr_read'))))
    add(p('Below resonance the secondary conducts for a resonant half period '
          'and the output voltage stands across the secondary winding for all '
          'of it. Above resonance it conducts for a shorter switching half '
          'period, so f<sub>r</sub> is the worst case everywhere on the line '
          'cycle:'))
    add(eq(r'B_{pk}=\frac{V_{out,eff}}{4\,f_{r}\,N_{s}\,A_{e}}'
           r'\qquad\Longrightarrow\qquad '
           r'A_{e}\;\geq\;\frac{V_{out,eff}}{4\,f_{r}\,N_{s}\,B_{max}}', key='Bpk'))
    add(p('<b>N<sub>p</sub> does not appear.</b> Adding primary turns does '
          'not reduce the flux; only adding secondary turns does. That is an '
          'uncomfortable result for a low-voltage, high-current output, where '
          'the secondary wants to be a single turn: halving N<sub>s</sub> '
          'doubles the core area needed. That is why a single-turn secondary '
          'is expensive in core area even though it is the obvious choice for '
          'the current.'))
    add(note('Computing the same flux from an inductance is correct only with '
             'the <b>physical</b> L<sub>&mu;</sub>: B<sub>pk</sub> = '
             'L<sub>&mu;</sub> i<sub>&mu;,pk</sub> / (N<sub>p</sub> '
             'A<sub>e</sub>) reduces exactly to the expression above. Using '
             'the tank model L<sub>m</sub> with the real N<sub>p</sub> '
             'understates the flux by &radic;(1+&lambda;) &mdash; about a '
             'quarter at &lambda;&nbsp;&asymp;&nbsp;0.5 &mdash; because the '
             'L<sub>m</sub> branch carries n V<sub>out</sub> while the '
             'winding reflects n<sub>T</sub> V<sub>out</sub>.'))

    add(h2('Choosing the core: two areas, and the one that usually decides'))
    add(p('A core has to satisfy two independent conditions, and they have '
          'nothing to do with each other. The magnetic one is the equation '
          'above: enough cross-section A<sub>e</sub> to carry the flux at '
          'the turns chosen. The electrical one is the winding window '
          'A<sub>N</sub>: enough room for the copper the currents need. '
          'Catalogues quote both, and their product is what handbooks call '
          'the <b>area product</b>. Either can be the binding one.'))
    add(note('<b>Read the flux check against A<sub>min</sub>, not '
             'A<sub>e</sub>.</b> A<sub>e</sub> is the effective area for '
             'inductance; A<sub>min</sub> is the narrowest section the flux '
             'actually has to pass. On a PQ core the two differ by ten to '
             'twenty per cent, and it is A<sub>min</sub> that saturates '
             'first: the real peak is B<sub>pk</sub>&thinsp;A<sub>e</sub>/'
             'A<sub>min</sub>. Both numbers are in the datasheet, and only '
             'one of them is usually used.'))
    add(p('In a <b>single-stage PFC LLC there is a third condition, and it is '
          'normally the one that decides</b>: the leakage inductance has to '
          'come out at L<sub>r</sub>. Written as a fraction of what a meter '
          'reads at the primary,'))
    add(eq(r'\frac{L_{short}}{L_{open}}=\frac{L_{r}}{L_{m}+L_{r}}'
           r'=\frac{\lambda}{1+\lambda}', key='lkfrac'))
    add(p('At &lambda;&nbsp;&asymp;&nbsp;0.5 that is <b>about a third</b>. '
          'A conventional transformer, wound to '
          'couple as well as it can, leaks a few per cent; this one has to '
          'leak an order of magnitude more, <i>on purpose</i>. Leakage that '
          'large is not a winding tolerance, it is a winding <b>geometry</b> '
          '&mdash; and geometry costs window area. A core that passes on '
          'A<sub>e</sub> and on copper can still fail here.'))

    add(h2('The winding arrangement is the leakage'))
    add(p('Leakage is the flux that links one winding and not the other, so '
          'it is set by how far apart the two windings are and by how much '
          'of the window separates them. That gives the designer one knob '
          'and a well-known ordering:'))
    ext(bullets([
        '<b>Interleaved</b> &mdash; primary, secondary, primary, all '
        'concentric. Lowest leakage, typically one or two per cent. This is '
        'what a conventional forward or flyback transformer wants, and it is '
        'the opposite of what is needed here.',
        '<b>Concentric, not interleaved</b> &mdash; the whole primary, then '
        'the whole secondary, over it. A few per cent. Still far short.',
        '<b>Side by side</b> &mdash; the primary on one half of the winding '
        'width, the secondary on the other. Tens of per cent, and adjustable '
        'by the gap left between them. <b>This is the arrangement a '
        'single-stage tank asks for</b>, and it is why the window has to be '
        'generous: half of it goes to each winding, and part of what is left '
        'is deliberately empty.',
        '<b>A magnetic shunt</b> &mdash; a ferrite bar in the window between '
        'the two windings, which carries leakage flux on purpose. It buys '
        'leakage without spending winding width, at the cost of a part and '
        'of a tolerance that is harder to hold.']))
    add(note('<b>This inverts the usual advice.</b> Every transformer text '
             'says to interleave, because in every other topology leakage is '
             'loss and overshoot. Here L<sub>r</sub> is a design value that '
             'the tank needs, and a supplier who "improves" the coupling has '
             'broken the converter &mdash; f<sub>r</sub> moves, &lambda; '
             'collapses and the gain curve goes with it. Say so on the '
             'drawing, in words, next to L<sub>short</sub>.'))

    add(h2('The gap, and why the drawing must not name it'))
    add(p('L<sub>m</sub> is two orders below what an ungapped core of this '
          'size gives, so the core is gapped. The inductance factor that '
          'follows from the turns is'))
    add(eq(r'A_{L}=\frac{L_{open}/N_{x}}{N_{p}^{2}}'
           r'\qquad\qquad '
           r'g\;\approx\;\frac{\mu_{0}\,A_{e}}{A_{L}}', key='ALgap'))
    add(p('with N<sub>x</sub> the number of units the assembly is built '
          'from. The second expression is only an estimate: it assumes the '
          'gap carries the whole reluctance and it ignores fringing, which '
          'always makes the real gap larger than it predicts. <b>Specify '
          'A<sub>L</sub>, or better L<sub>open</sub> itself, and leave the '
          'gap to the supplier</b> &mdash; that is the number they grind to, '
          'and it is the number a meter can check.'))

    add(h2('The window: wire, current density and what actually fits'))
    add(p('Marks <b>2</b> and <b>5</b> of Figure&nbsp;%(f)s. The copper is '
          'sized on the <b>line-cycle</b> rms: the rms of each switching '
          'period (the bracket under the trace), averaged in I&sup2; over '
          'the line half cycle (the lower-left panel). The secondary value '
          'is per winding and per unit &mdash; each winding carries one '
          'pulse per period, and its idle half is inside the average.'
          % dict(f=FR('an_xfmr_read'))))
    add(p('Each winding needs a conductor cross-section set by its own rms '
          'current and the current density the design can cool:'))
    add(eq(r'A_{cu}=\frac{I_{rms}}{J}\qquad\qquad '
           r'\sum_{w} N_{w}A_{cu,w}\;\leq\;k_{u}A_{N}', key='window'))
    add(p('J is an assumption, not a constant: 4 to 5&nbsp;A/mm&sup2; is '
          'usual for a transformer of this size in free air, less if it is '
          'enclosed. k<sub>u</sub> is the window utilisation, and it is '
          'small &mdash; round wire in a round bundle, insulation, the '
          'bobbin wall, the margins and the layer-to-layer tape leave '
          '<b>0.3 or less</b> of the window as copper when the wire is '
          'Litz. Sizing on bare copper alone overstates what fits by three '
          'times.'))
    add(note('<b>The primary current does not divide between units.</b> With '
             'the primaries in series every unit carries the whole primary '
             'current, and only the secondaries share. So the primary '
             'copper is the same in each unit as it would be in one big '
             'transformer, while the secondary copper is divided &mdash; '
             'which is exactly why splitting helps a low-voltage, '
             'high-current output.'))

    add(h2('Skin depth, and why the wire is not a wire'))
    add(p('At the switching frequency current does not fill a conductor. It '
          'crowds into a surface layer of depth'))
    add(eq(r'\delta=\sqrt{\frac{\rho}{\pi f\mu_{0}}}', key='skin'))
    add(p('which for a series resonance in the 100 to 200&nbsp;kHz range '
          'is about <b>0.2&nbsp;mm</b> in copper at 100&nbsp;&deg;C. A '
          'conductor thicker '
          'than about 2&delta; carries no more current than one of 2&delta; '
          '&mdash; it only adds weight. Worse, the field from the '
          '<i>other</i> turns drives circulating current in each conductor '
          '(the proximity effect), and in a side-by-side winding, where the '
          'two windings sit in each other’s leakage field, that term '
          'can dominate the skin term.'))
    ext(bullets([
        'Use <b>Litz</b> on the primary: many strands, each well under '
        '2&delta;, individually insulated and transposed. Strand diameter '
        'around %(ds).1f&nbsp;mm is a usual choice at this frequency.'
        % dict(ds=0.2),
        'On a two-turn, high-current secondary, <b>copper foil</b> is '
        'usually better than wire: the thickness can be held near &delta; '
        'while the width fills the window, and it terminates well into a '
        'centre tap.',
        'Whatever is chosen, the ac resistance is what heats the winding. '
        'The dc resistance &rho;&thinsp;l<sub>N</sub>N/A<sub>cu</sub> is a '
        'floor, not an answer.']))

    add(h2('Isolation, margins and what they cost in window'))
    add(p('The transformer is the isolation barrier of the whole supply, so '
          'the winding that looks like a copper problem is also a safety '
          'one. Two arrangements are common, and they spend the window '
          'differently. <b>Margin tape</b> leaves a creepage margin at each '
          'end of the bobbin &mdash; typically 3&nbsp;mm each side for '
          'reinforced isolation from a universal mains &mdash; so it takes '
          '6&nbsp;mm off the usable winding width and costs nothing in '
          'material. <b>Triple-insulated wire</b> needs no margin, so the '
          'winding uses the full width, but the wire is thicker for the same '
          'copper and it costs more.'))
    add(note('On a side-by-side winding the margin is taken twice over: once '
             'for the isolation, and once again for the gap that sets the '
             'leakage. Work the window budget with both in it, or the part '
             'that is ordered will not be the part that was calculated.'))

    add(h2('Loss, and the temperature the drawing has to survive'))
    ext(bullets([
        '<b>Core loss</b> comes off the material curve at the operating '
        'flux and frequency, not off the headline figure. A datasheet '
        'quotes P<sub>V</sub> at one point &mdash; 100 or 200&nbsp;mT at '
        '100&nbsp;kHz &mdash; and a design at a different flux and a '
        'different frequency has to be read from the curve.',
        '<b>Copper loss</b> is I&sup2;R<sub>ac</sub>, and R<sub>ac</sub> is '
        'the number the previous section is about. Both windings count, and '
        'in a side-by-side arrangement the proximity term is not small.',
        '<b>The temperature rise</b> is what actually limits the design, '
        'and it depends on the surface area and the airflow, neither of '
        'which is in any of the equations above. Treat the computed loss as '
        'an input to a thermal measurement, not as an answer.']))
    add(note('<b>Flux and loss do not move together here.</b> B<sub>pk</sub> '
             'is set at f<sub>r</sub> by the secondary volt-seconds, so it '
             'does not change when the converter runs faster &mdash; but '
             'core loss does, and in a single-stage converter the frequency '
             'sweeps over the line cycle. The core sees its worst flux at '
             'the bottom of the sweep and its worst loss per cycle count at '
             'the top.'))

    add(h2('The saturation test is not the peak winding current'))
    add(p('Mark <b>3</b> and the bench panel of Figure&nbsp;%(f)s. The '
          'current to ask for is the peak of the dashed magnetising trace at '
          'the switching instant, scaled to the over-voltage ceiling &mdash; '
          'not the peak of the winding current at mark 1.'
          % dict(f=FR('an_xfmr_read'))))
    add(p('A DC-overlap test leaves every other winding open, so none of the '
          'primary ampere-turns is cancelled by the secondary and the same '
          'current makes far more flux than it does in operation. It is the '
          'flyback condition of Section&nbsp;'
          + SR('Not a flyback, and why that changes the core')
          + ', reached deliberately. Ask for the current that reproduces the '
            'operating flux in that test:'))
    add(eq(r'I_{eq}=\frac{B_{pk}\,N_{p}\,A_{e}}{L_{\mu}}', key='Isat'))
    add(note('<b>That denominator is L<sub>&mu;</sub>, not '
             'L<sub>open</sub>.</b> In the open-circuit test the primary '
             'current is entirely magnetising current, so what links the '
             'core is the L<sub>&mu;</sub> part of the flux linkage and the '
             'rest is primary leakage, which goes round no core at all. '
             'Dividing by L<sub>open</sub> understates the current by '
             '1/&radic;(1+&lambda;) &mdash; about a fifth at '
             '&lambda;&nbsp;&asymp;&nbsp;0.5. There is a check that costs '
             'nothing: the answer <b>must</b> come out equal to '
             'i<sub>&mu;,pk</sub>, because in that test they are the same '
             'current.'))
    add(p('Giving the supplier the peak tank current instead asks for a flux '
          'density no ferrite reaches, and the supplier will either '
          'oversize the core or ask why. Nor is an arbitrary margin wanted '
          'on top of I<sub>eq</sub>: the flux ceiling the core has to '
          'survive is already defined, by the highest output voltage the '
          'controller allows before it shuts down. Scale I<sub>eq</sub> by '
          'that ratio and there is no number left to invent.'))
    add(eq(r'I_{sat}\;=\;I_{eq}\;\frac{V_{OVP2}}{V_{out,eff}}',
           key='Isatspec'))

    add(h2('The specification, and what it is not allowed to leave out'))
    add(note('<b>The open-circuit inductance tolerance cannot simply be the '
             'usual round number.</b> f<sub>o</sub> goes as '
             '1/&radic;L<sub>open</sub>, so a low part raises the frequency '
             'floor towards the oscillator clamp. The fall a tank can '
             'tolerate follows from k<sub>floor</sub> and is typically a few '
             'per cent, so the usual &plusmn;10&nbsp;%% can allow a part that '
             'meets its specification to hard switch. Section&nbsp;' % {}
             + SR('Controller network') + ' derives the figure and gives the '
             'two ways out. Ask the supplier for a tighter low-side limit, '
             'or first make room in the oscillator setting and then ask for '
             '&plusmn;10&nbsp;%.'))
    add(note('Core, bobbin, wire and winding order are the supplier choice, '
             'and insulation and creepage follow the applicable safety '
             'standard. '
             'Nothing above constrains them; everything above is measurable '
             'at the terminals.'))

    add(h2('If one transformer is not practical'))
    add(p('At a low output voltage and high current the secondary is a single '
          'heavy turn and the core comes out large, which may not fit a '
          'height or footprint limit. The transformer can then be built as '
          'N<sub>x</sub> identical units with <b>primaries in series and '
          'secondaries in parallel</b>. Series primaries carry the same '
          'current, so the paralleled secondaries share automatically without '
          'balancing resistors.'))
    ext(bullets([
        'Open-circuit and leakage inductance divide by N<sub>x</sub>, and so '
        'do the secondary currents. <b>The primary current does not divide.</b>',
        'The DC-overlap test current does not change: flux and primary '
        'ampere-turns scale together.',
        'The wound ratio of the assembly becomes '
        'N<sub>x</sub>N<sub>p</sub>/N<sub>s</sub>, so <b>the achievable '
        'ratios are quantised in steps of N<sub>x</sub>/N<sub>s</sub></b>. '
        'That has to be respected when the tank is chosen, not discovered '
        'afterwards.']))

    add(h2('The input capacitor'))
    add(p('With no bulk capacitor, C<sub>in</sub> is a film capacitor that '
          'absorbs switching ripple and nothing else. A large value is not '
          'the safe choice: it holds charge across the zero crossing and '
          'distorts the line current, so it is a THD term, not a filter '
          'term.'))
    add(eq(r'C_{in}\;=\;3\,\frac{\mathrm{nF}}{\mathrm{W}}\times P_{in}', key='Cin'))
    add(p('That is a <b>lower</b> bound, so round up to the next standard '
          'value and rate it for the full line voltage.'))

    add(h2('The output capacitor bank'))
    add(p('Two conditions apply, and the larger wins. The ripple condition '
          'is'))
    add(eq(r'C_{out}\;\geq\;\frac{P_{out}}'
           r'{2\pi f_{l,min}\,\Delta v\,V_{out}^{2}}', key='Crip'))
    add(p('and the hold-up condition is'))
    add(eq(r'C_{out}\;\geq\;\frac{2P_{out}T_{hold}}'
           r'{\left(V_{out}-\frac{1}{2}\Delta v_{pp}\right)^{2}'
           r'-V_{o,min}^{2}}', key='Chold'))
    add(note('<b>Hold-up starts at the worst line phase, and that belongs in '
             'the sizing.</b> If the mains disappears at the trough of the '
             '2f<sub>l</sub> ripple the bank is already half a ripple below '
             'nominal when it starts, which is why V<sub>out</sub> above '
             'carries the &minus;&frac12;&Delta;v term. The difference is not '
             'small: it costs about a tenth of the ride-out time. Note also '
             'that &Delta;v<sub>pp</sub> there is the ripple the bank '
             'actually produces, not the allowance. The condition therefore '
             'depends on its own answer, which is why it is checked once the '
             'bank is chosen.'))
    add(p('Which one wins is a question about the specification and not '
          'about the output voltage: both conditions scale as '
          '1/V<sub>out</sub>&sup2;, so V<sub>out</sub> cancels when they are '
          'divided. Writing k&nbsp;=&nbsp;V<sub>o,min</sub>/V<sub>out</sub>, '
          'ripple dominates when'))
    add(eq(r'\left(1-\frac{\Delta v}{2}\right)^{2}-k^{2}'
           r'\;>\;4\pi f_{l}\,\Delta v\,T_{hold}', key='ripscreen'))
    add(p('This screening form uses the <i>allowed</i> &Delta;v rather than '
          'the achieved ripple, because it is asked before the bank exists. '
          'Section&nbsp;%s evaluates it for the worked design.'
          % SR('The output bank, as sized')))
    ext(bullets([
        'Include the <b>2f<sub>l</sub> component</b> in the ripple current. '
        'The switching-frequency part alone is far too small: the '
        '2f<sub>l</sub> envelope carries a comparable rms of its own, and '
        'the two are orthogonal so they add in quadrature.',
        'With a centre-tapped secondary, judge the capacitor ripple current '
        'at the <b>output node</b>, not per winding.',
        'Use the ESR at the <b>switching frequency</b>. An electrolytic '
        'tan&thinsp;&delta; is quoted at 120&nbsp;Hz and is five to ten times '
        'larger there.']))
    add(note('<b>A risk this architecture creates.</b> The controller '
             'start-up window is finite, and a bank of this size is a far '
             'heavier start-up load than the few millifarads a conventional '
             'design presents. Cold start into the full bank should be one of '
             'the first things measured on hardware.'))

    add(h2('Semiconductor requirements'))
    add(p('State requirements rather than pick parts: what to pick depends '
          'on package, thermal design and cost. Four rules decide whether the '
          'requirement is even stated correctly.'))
    ext(bullets([
        'Rate the primary switches on the <b>composite tank peak</b>, not '
        'on the reflected load current. The load component alone under-rates '
        'the device by more than a tenth here, because the magnetising '
        'current is missing from it.',
        'Divide currents by the number of devices actually in parallel before '
        'judging stress. Tabulated currents are <b>per switch position</b> on '
        'the primary and <b>per leg</b> on the secondary; a centre-tapped leg '
        'carries the whole secondary current, not half of it.',
        'Compute loss from R<sub>DS(on)</sub> at <b>T<sub>j,max</sub></b>, '
        'not at 25&nbsp;&deg;C. The datasheet maximum is process spread at '
        '25&nbsp;&deg;C; temperature is a separate multiplier, close to two '
        'for a superjunction device, read from its normalised '
        'R<sub>DS(on)</sub> curve at T<sub>j,max</sub>. Using the '
        '25&nbsp;&deg;C value to size a heatsink is optimistic by about a '
        'factor of two.',
        'A curve plotted against T<sub>a</sub> may still be read as '
        'T<sub>j</sub> <b>if it is a pulse test</b> &mdash; the die does not '
        'self-heat during the pulse. For any non-pulsed curve this is not '
        'valid.']))
    add(note('<b>The standing device in half-bridge morphing is the one to '
             'watch</b> (Section&nbsp;' + SR('Half bridge') + '). It never '
             'switches and carries the whole tank current, and it is where '
             'the conduction-loss budget is met or knowingly missed &mdash; '
             'Section&nbsp;' + SR('Where the power goes') + ' shows which '
             'happened here.'))

    add(h2('Controller network'))
    add(fig('bom_pin_config',
            'The controller and its passive network. HVSU is fed from the AC '
            'side of the bridge; the auxiliary winding drives ZCD through a '
            'divider; R<sub>T</sub> and C<sub>T</sub> set the oscillator '
            'limits; R<sub>CFG</sub> and R<sub>BM</sub> are read at power-up.',
            width=CW))
    add(p('Decide first what the auxiliary winding is for. When it also '
          'supplies V<sub>CC</sub>, the rectified auxiliary voltage at OVP2 '
          'must stay under the V<sub>CC</sub> rating, and that caps its '
          'turns ratio. Here V<sub>CC</sub> comes from elsewhere, so the '
          'winding only senses, the only constraint is that the turns come '
          'out whole, and the datasheet ratio check is not applicable '
          '(Section&nbsp;'
          + SR('Output sensing and over-voltage: the ZCD divider') + ').'))
    add(p('Each of these parts follows from something already fixed, and '
          'Section&nbsp;' + SR('The parts around the controller')
          + ' sizes them one at a time in the '
          'order they have to be done. The one that deserves the most '
          'attention throughout is R<sub>T</sub>, because it sets the '
          'oscillator floor and that floor must stay above f<sub>o</sub>.'))
    add(note('<b>That floor is usually the thinnest margin in the '
             'design.</b> f<sub>Min</sub> must sit above f<sub>o</sub>, or '
             'nothing but the anti-capacitive protection stands between the '
             'converter and the capacitive region. It also depends on the '
             'oscillator idle time, which the draft datasheet states '
             'inconsistently, so whatever it computes to has to be confirmed '
             'by measuring f<sub>sw</sub>(&theta;) on hardware.'))
    add(p('That ratio is also what the transformer tolerance has to fit '
          'inside, and this is easy to miss because the two numbers are in '
          'different documents. Since f<sub>o</sub> = 1/(2&pi;&radic;(L<sub>open</sub>'
          'C<sub>r</sub>)), a <b>low</b> open-circuit inductance raises '
          'f<sub>o</sub>. The fall that can be tolerated is'))
    add(eq(r'\frac{\Delta L}{L}\;=\;1-\frac{1}{k_{floor}^{2}}', key='Ldrop'))
    add(p('A floor margin of a few per cent allows a fall of a few per cent '
          'in inductance. A transformer drawing asking for the usual '
          '&plusmn;10&nbsp;%% does <b>not</b> fit inside that: at the bottom '
          'of the tolerance the converter hard switches. There are two ways '
          'out &mdash; tighten the tolerance on the low side, or lower '
          'R<sub>T</sub> to lift f<sub>Min</sub> and make the room. '
          '<b>Check this before the transformer is ordered</b>, not '
          'after.' % {}))

    add(h2('Voltage loop and compensation'))
    add(p('The voltage loop holds the output at its set point. It is the '
          'chain of Figure&nbsp;%(f)s. A divider measures the output. A '
          'TL431 compares the divided voltage with its reference and drives '
          'the LED of an optocoupler. The optocoupler transistor pulls the '
          'FB pin of the controller. The FB voltage is the power command of '
          'Section&nbsp;%(s)s, the converter delivers that power into the '
          'output capacitor, and the output voltage closes the loop.'
          % dict(f=FR('an_loop_blocks'),
                 s=SR('The feedback pin is a power command'))))
    add(fig('an_loop_blocks',
            'The voltage loop as blocks. Everything left of the FB pin is '
            'the compensator G<sub>EA</sub>(s); everything right of it is '
            'the plant G<sub>plant</sub>(s). The loop gain is T(s) = '
            'G<sub>plant</sub>(s)&nbsp;G<sub>EA</sub>(s).'))
    add(p('<b>The plant.</b> The converter delivers the power the FB pin '
          'commands, and that power goes into a capacitor. A change of the '
          'FB voltage changes the power in proportion. The power divided by '
          'the output voltage is the current into C<sub>out</sub>. A current '
          'into a capacitor gives a voltage that keeps rising for as long as '
          'the current flows. So the plant is an <b>integrator</b>:'))
    add(eq(r'G_{plant}(s)=\frac{v_{out}(s)}{v_{FB}(s)}=\frac{G_{o}}{s},'
           r'\qquad G_{o}=\frac{P_{out}}{V_{out}\,V_{FB}\,C_{out}}'
           r'\quad[\mathrm{rad/s}]', key='Gplant'))
    add(p('V<sub>FB</sub> is the feedback voltage above its 0.5&nbsp;V '
          'offset at rated power (Equation&nbsp;%(e)s), so '
          'P<sub>out</sub>/V<sub>FB</sub> is the slope of the power command. '
          'An integrator has a gain that falls by 20&nbsp;dB per decade and '
          'a phase of &minus;90&deg; at every frequency. On its own it would '
          'cross 0&nbsp;dB at f<sub>cto</sub> = G<sub>o</sub>/2&pi;. There '
          'is no second pole and no right-half-plane zero. That makes this '
          'loop easy to stabilise. What makes it hard to place is the '
          'output ripple, in Section&nbsp;%(r)s.'
          % dict(e=ER('VFB'),
                 r=SR('Why the crossover must be low: the 2f<sub>l</sub> ripple'))))

    add(h2('What the loop must achieve, and what goes wrong when it does not'))
    add(p('Three numbers are read from the Bode plot of the loop gain '
          'T(s): the <b>crossover frequency</b> f<sub>c</sub>, where |T| = 1 '
          '(0&nbsp;dB); the <b>phase margin</b>, which is 180&deg; + '
          'arg&nbsp;T at f<sub>c</sub>; and the <b>gain margin</b>, which is '
          'how far |T| is below 0&nbsp;dB at the frequency f<sub>180</sub> '
          'where arg&nbsp;T reaches &minus;180&deg;. Table&nbsp;%(t)s says '
          'what each one should be and what happens when it is not.'
          % dict(t=TR('loop-aims'))))
    add(tbl('What the loop must achieve.',
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
            key='loop-aims'))

    add(h2('Why the crossover must be low: the 2f<sub>l</sub> ripple'))
    add(p('The output carries a ripple at twice the line frequency, '
          'because the input power pulses at 2f<sub>l</sub> and the '
          'capacitor buffers the difference (Section&nbsp;%(s)s). Its '
          'peak-to-peak value is'
          % dict(s=SR('The energy a unity power factor cannot deliver'))))
    add(eq(r'\Delta V_{loop}=\frac{P_{out}}{V_{out}}\,\frac{1}{2\pi f_{l}\,C_{out}}',
           key='dVloop'))
    add(p('The compensator passes a fraction G<sub>EA</sub>(2f<sub>l</sub>) '
          'of that ripple to the FB pin. The FB pin is a power command, so '
          'a ripple on it makes the input power, and the input current, '
          'swing at 2f<sub>l</sub> over the line cycle. A sine wave whose '
          'amplitude is modulated at twice its own frequency gains a '
          'third harmonic. The ripple amplitude is half the peak-to-peak '
          'value, and a modulation of the command by a fraction m puts '
          'm/2 into the third harmonic, so'))
    add(eq(r'D_{3}=\frac{G_{EA}(2f_{l})\,\Delta V_{loop}}{4\,V_{FB}}',
           key='D3'))
    add(p('Turned around, the third-harmonic budget D<sub>3</sub> fixes '
          'the largest compensator gain the loop may have at '
          '2f<sub>l</sub>:'))
    add(eq(r'G_{EA}(2f_{l})\;\leq\;\frac{4\,V_{FB}\,D_{3}}{\Delta V_{loop}}',
           key='GEAreq'))
    add(p('The compensator gain falls with frequency, so a small gain at '
          '2f<sub>l</sub> means a crossover well below 2f<sub>l</sub>. With '
          '5&nbsp;% of third harmonic allowed this lands at 15 to '
          '20&nbsp;Hz. A faster loop would give less output ripple and a '
          'quicker load-step response, and it would put more distortion on '
          'the input current. The two pull in opposite directions, and the '
          'distortion limit wins. This is the ripple rejection every '
          'power-factor corrector needs; onsemi TND381 calls the failure '
          '&ldquo;tail chasing&rdquo;.'))

    add(h2('The compensator: TL431, optocoupler and the FB pin'))
    add(fig('comp_network_st',
            'The compensator on the secondary side. R<sub>I</sub> and '
            'R<sub>O</sub> set the regulated output; the TL431 is the error '
            'amplifier; R<sub>f</sub>, C<sub>f</sub> and C<sub>fo</sub> '
            'shape its gain; R<sub>B</sub> feeds the optocoupler LED from '
            'the regulated V<sub>Z</sub> rail; R<sub>P</sub> keeps the TL431 '
            'above its minimum current; C<sub>fx</sub> sits on the FB pin.'))
    add(p('<b>How it works.</b> The divider R<sub>I</sub>, R<sub>O</sub> '
          'brings the output down to the TL431 reference '
          'V<sub>R</sub>&nbsp;=&nbsp;2.495&nbsp;V:'))
    add(eq(r'V_{out}=V_{R}\left(1+\frac{R_{I}}{R_{O}}\right)', key='RoVout'))
    add(p('When the output rises above the set point the TL431 sinks more '
          'current from its cathode. That current flows through the '
          'optocoupler LED, which is fed by R<sub>B</sub> from a regulated '
          'rail V<sub>Z</sub>. The optocoupler transistor then pulls the FB '
          'pin down against the pull-up R<sub>FB</sub> inside the '
          'controller, the power command falls, and the output comes back. '
          'R<sub>P</sub> in parallel with the LED carries the minimum '
          'cathode current the TL431 needs to work as an amplifier, so it '
          'has an upper limit:'))
    add(eq(r'R_{P}\leq\frac{V_{Fo}}{I_{min}}', key='RPmax'))
    add(p('Because the LED is fed from V<sub>Z</sub> and not from the output, '
          'the output ripple reaches the LED only through the TL431. There '
          'is no second path (what TND381 calls the &ldquo;fast '
          'lane&rdquo;), and the compensator is the TL431 network alone.'))
    add(p('<b>The same network as an op-amp.</b> Figure&nbsp;%(f)s redraws '
          'it with every part as a circuit symbol. The TL431 is an op-amp '
          'whose non-inverting input is tied to an internal 2.495&nbsp;V '
          'reference V<sub>R</sub>, drawn as a voltage source, whose output '
          'is the cathode, and whose anode is ground. '
          'R<sub>I</sub> is the input resistor of an inverting amplifier, '
          'and C<sub>Fo</sub> in parallel with R<sub>F</sub> + C<sub>F</sub> '
          'is its feedback impedance Z<sub>f</sub>, so the cathode moves by '
          '&minus;Z<sub>f</sub>/R<sub>I</sub> times the output change. '
          'R<sub>O</sub> sets only the dc point: the inverting input is '
          'held at V<sub>R</sub>, so no signal current flows in it. The '
          'cathode current flows through the LED, which R<sub>B</sub> feeds '
          'from the V<sub>Z</sub> rail with R<sub>P</sub> across it, so it '
          'is the LED current. The transistor side of the optocoupler is '
          'drawn as its small-signal model, a current-controlled current '
          'source: it sinks CTR times i<sub>LED</sub> from the FB node, '
          'with the optocoupler capacitance across it. That current makes the FB voltage across '
          'the pull-up R<sub>FB</sub>, with the pole of C<sub>opto</sub> + '
          'C<sub>fx</sub>. Multiplying the three blocks gives the transfer '
          'function below; the sign is negative, which is the negative '
          'feedback the loop needs.'
          % dict(f=FR('an_comp_opamp'))))
    add(fig('an_comp_opamp',
            'The TL431 compensator drawn as an op-amp circuit. Inside the '
            'TL431: an op-amp with its non-inverting input on the internal '
            '2.495&nbsp;V reference V<sub>R</sub>, output at the cathode, '
            'anode at ground. Around it: R<sub>I</sub> and Z<sub>f</sub> '
            'make an inverting amplifier; R<sub>B</sub>, R<sub>P</sub> and '
            'the LED turn the cathode voltage into the current '
            'i<sub>LED</sub>; the optocoupler is a current-controlled '
            'current source, CTR&thinsp;i<sub>LED</sub> sinking from the FB '
            'node; R<sub>FB</sub> '
            'with C<sub>opto</sub> + C<sub>fx</sub> turns it into '
            'v<sub>FB</sub>. The three factors multiply to '
            'G<sub>EA</sub>(s).'))
    add(p('<b>Its transfer function</b> from the output to the FB pin is a '
          'Type&nbsp;II network with one more pole:'))
    add(eq(r'G_{EA}(s)=\frac{EA_{o}}{s}\cdot'
           r'\frac{1+s/\omega_{z}}{(1+s/\omega_{p})(1+s/\omega_{px})}',
           key='GEAtf'))
    add(eq([r'EA_{o}=\frac{CTR\;R_{FB}}{(C_{F}+C_{Fo})\,R_{I}\,R_{B}}\quad[\mathrm{rad/s}],'
            r'\qquad f_{z}=\frac{1}{2\pi R_{F}C_{F}}',
            r'f_{p}=\frac{1}{2\pi R_{F}C_{ser}},\quad C_{ser}=\frac{C_{F}C_{Fo}}{C_{F}+C_{Fo}},'
            r'\qquad f_{px}=\frac{1}{2\pi R_{FB}\,(C_{opto}+C_{fx})}'],
           key='fzp'))
    add(p('Each part has one job. C<sub>F</sub> and C<sub>Fo</sub> together '
          'make the pole at the origin: the gain keeps rising toward dc, so '
          'the static error is zero. R<sub>F</sub> with C<sub>F</sub> makes '
          'the zero f<sub>z</sub>: above it the phase comes back up, and '
          'that is where the phase margin comes from. C<sub>Fo</sub> with '
          'R<sub>F</sub> makes the pole f<sub>p</sub>: above it the gain '
          'falls at 40&nbsp;dB per decade again, so the gain at '
          '2f<sub>l</sub> is small. The optocoupler capacitance '
          'C<sub>opto</sub> with R<sub>FB</sub> makes a third pole, and '
          'C<sub>fx</sub> is added to put it at about a kilohertz where it '
          'removes switching noise from the FB pin. The optocoupler CTR '
          'multiplies the whole gain, which is why its spread matters.'))
    add(p('<b>The bias window.</b> The datasheet gives a window for '
          'R<sub>B</sub>. The LED must be able to drive the FB pin at its '
          'steady-state current with the lowest CTR (upper bound), and must '
          'not push the pin past its maximum current with the highest CTR '
          'when the TL431 is fully on (lower bound):'))
    add(eq([r'R_{B,max}=\frac{V_{Z}-(V_{R}+V_{Fo})}'
            r'{V_{Fo}/R_{P}+I_{FB,steady}/CTR_{s}}',
            r'R_{B,min}=\frac{V_{Z}-(V_{R}+V_{Fo})}'
            r'{V_{Fo}/R_{P}+I_{FB,max}/CTR_{m}}'], key='RBwin'))
    add(note('<b>Two currents, two CTR values.</b> The gain EA<sub>o</sub> '
             'is computed with the CTR at the steady-state LED current, '
             'CTR<sub>s</sub>. The lower bound of R<sub>B</sub> uses the '
             'CTR at the maximum LED current, CTR<sub>m</sub>, which is '
             'higher because CTR rises with current. Take both from the '
             'optocoupler datasheet for the bin that will be fitted, and '
             'check the loop again with the CTR at the top of the bin: the '
             'crossover moves up with the square root of CTR and the phase '
             'margin comes down.'))

    add(h2('Placing the zero and the pole: the K-factor method'))
    add(p('The compensator has three things to set: its gain '
          'EA<sub>o</sub>, its zero and its pole. The Venable K-factor '
          'method sets them from two targets, the phase margin '
          '&Phi;<sub>M</sub> and the gain the loop is allowed at '
          '2f<sub>l</sub>. First a spread factor K<sub>v</sub> is computed '
          'from the phase margin, with &alpha;<sub>v</sub> a weighting '
          'constant of the method (1.2 in the ST tool):'))
    add(eq(r'K_{v}=\frac{1}{2\alpha_{v}}\left[(1+\alpha_{v}^{2})\tan\Phi_{M}'
           r'+\sqrt{(1+\alpha_{v}^{2}\tan\Phi_{M})^{2}'
           r'+4\alpha_{v}^{2}}\;\right]', key='Kv'))
    add(p('The zero goes a factor K<sub>v</sub> below the crossover and the '
          'pole the same factor above it. Above the pole the compensator '
          'gain is EA<sub>o</sub>K<sub>v</sub>&sup2;/&omega;, so the gain '
          'limit at 2f<sub>l</sub> fixes EA<sub>o</sub>:'))
    add(eq(r'EA_{o}=\frac{2\pi\,(2f_{l})\,G_{EA}(2f_{l})}{K_{v}^{2}}',
           key='EAotarget'))
    add(p('The point the zero and pole are placed about follows from the '
          'plant gain, with &Gamma;<sub>v</sub> = 0.744 '
          'V<sub>eq,max</sub>/V<sub>eq,min</sub> an input-voltage margin '
          'factor of the ST tool (its constant is listed in '
          'Appendix&nbsp;%(a)s as not derived here):'
          % dict(a=SR('Constants used here without a derivation'))))
    add(eq(r'f_{MB}=\frac{1}{2\pi}\sqrt{\frac{G_{o}K_{v}EA_{o}}{\Gamma_{v}}},'
           r'\qquad f_{p}=K_{v}f_{MB},\qquad f_{z}=\frac{f_{MB}}{K_{v}}', key='fMB'))
    add(p('The parts then follow from Equation&nbsp;%(e)s, solved for each '
          'one in turn. The high-frequency pole is placed at a chosen '
          'f<sub>pHF</sub>, and C<sub>fx</sub> is what is left after the '
          'optocoupler capacitance:' % dict(e=ER('fzp'))))
    add(eq([r'C_{Fo}=\frac{f_{z}}{f_{p}}\cdot\frac{CTR_{s}\,R_{FB}}{R_{I}R_{B}\,EA_{o}},'
            r'\qquad C_{F}=C_{Fo}\left(\frac{f_{p}}{f_{z}}-1\right)',
            r'R_{F}=\frac{1}{2\pi f_{z}C_{F}},'
            r'\qquad C_{fx}=\frac{1}{2\pi f_{pHF}\,R_{FB}}-C_{opto}'],
           key='Ccomp'))
    add(p('Each value is then rounded to a standard part, and the zero, '
          'pole and gain the standard parts actually give are computed '
          'back with Equation&nbsp;%(e)s. The loop is checked on those, '
          'not on the targets.' % dict(e=ER('fzp'))))

    add(h2('Checking the loop: crossover, phase margin and gain margin'))
    add(p('With the plant of Equation&nbsp;%(a)s and the compensator of '
          'Equation&nbsp;%(b)s the loop gain is two integrators, one zero '
          'and two poles. Its magnitude and phase at any frequency are'
          % dict(a=ER('Gplant'), b=ER('GEAtf'))))
    add(eq([r'|T(\omega)|=\frac{G_{o}\,EA_{o}}{\omega^{2}}\cdot'
            r'\frac{\sqrt{1+(\omega/\omega_{z})^{2}}}'
            r'{\sqrt{1+(\omega/\omega_{p})^{2}}\;\sqrt{1+(\omega/\omega_{px})^{2}}}',
            r'\arg T(\omega)=-180^{\circ}+\arctan\frac{\omega}{\omega_{z}}'
            r'-\arctan\frac{\omega}{\omega_{p}}-\arctan\frac{\omega}{\omega_{px}}'],
           key='Tloop'))
    add(p('The &minus;180&deg; is the two integrators. Everything after it '
          'is the compensator&rsquo;s own phase, so the <b>phase margin is '
          'simply the compensator phase at the crossover</b>. The crossover '
          'is where |T| = 1. Writing A(&omega;) for the fraction in '
          'Equation&nbsp;%(t)s, the condition is '
          '&omega;<sub>c</sub>&sup2; = G<sub>o</sub>EA<sub>o</sub>A(&omega;<sub>c</sub>). '
          'A(&omega;) changes slowly, so it is solved by repeating'
          % dict(t=ER('Tloop'))))
    add(eq(r'\omega_{c}\leftarrow\sqrt{G_{o}\,EA_{o}\,A(\omega_{c})},'
           r'\qquad\mathrm{starting\ from}\ \ \omega_{c}=\sqrt{G_{o}\,EA_{o}}',
           key='wc'))
    add(p('a few times until it stops moving; no solver is needed. The '
          'phase margin is then'))
    add(eq(r'\Phi_{M}=\arctan\frac{\omega_{c}}{\omega_{z}}'
           r'-\arctan\frac{\omega_{c}}{\omega_{p}}'
           r'-\arctan\frac{\omega_{c}}{\omega_{px}}', key='PMeq'))
    add(p('Figure&nbsp;%(f)s shows where the three numbers are read on '
          'the Bode plot of such a loop. It is drawn in units of its own '
          'crossover, with the zero a factor K below f<sub>c</sub> and the '
          'pole K above, so it is the shape of every loop of this kind and '
          'not of one design. The gain falls at 40&nbsp;dB per decade where '
          'both integrators act, at 20&nbsp;dB per decade between the zero '
          'and the pole, and steeper again above the pole and above '
          'f<sub>px</sub>. The phase starts at &minus;180&deg;, is lifted by '
          'the zero, peaks near the crossover, and is pulled down again by '
          'the two poles until it crosses &minus;180&deg; at f<sub>180</sub>. '
          'Section&nbsp;%(s)s puts this design&rsquo;s numbers on the same '
          'plot.' % dict(f=FR('an_loop_example'),
                         s=SR('The voltage loop, as built'))))
    add(fig('an_loop_example',
            'A two-integrator loop with a Type II compensator, in units of '
            'its own crossover f<sub>c</sub>. The crossover is where |T| '
            'crosses 0&nbsp;dB; the phase margin is the distance from '
            '&minus;180&deg; there; the gain margin is how far |T| is below '
            '0&nbsp;dB at f<sub>180</sub>, where the phase reaches '
            '&minus;180&deg;. The dot at 2f<sub>l</sub> is the loop gain the '
            'third-harmonic check reads.'))

    add(h2('Gain margin, and why it needs checking'))
    add(p('Phase margin alone does not prove the loop is safe. Above '
          'f<sub>px</sub> this network has one zero against two poles, so '
          'the phase keeps falling toward &minus;270&deg; and '
          '<b>&minus;180&deg; is crossed at a finite frequency</b>. That '
          'frequency needs no search either. Setting the phase '
          'contributions of the zero and the two poles equal and taking the '
          'tangent of both sides leaves one square root:'))
    add(eq(r'f_{180}=\sqrt{\,f_{p}f_{px}-f_{z}(f_{p}+f_{px})\,}'
           r'\,,\qquad GM=-20\log_{10}|T(f_{180})|', key='f180'))
    add(p('<b>The value under the root is positive whenever the zero sits '
          'well below both poles</b>, which is what the K-factor placement '
          'gives. If it came out negative the loop would not be extra safe: '
          'the two poles would pull the phase below &minus;180&deg; before '
          'the zero could lift it, at every frequency, so the phase margin '
          'at any crossover would be negative. Judge the gain margin '
          'against 6&nbsp;dB as a floor and 10&nbsp;dB as a comfortable '
          'target. With a crossover in the tens of hertz the margin is '
          'usually large in this topology. That is a reason to compute it, '
          'not a reason to assume it.'))
    add(p('The gain the standard parts give at 2f<sub>l</sub> is read from '
          'the same expression, and the third harmonic it causes follows '
          'from Equation&nbsp;%(d)s. That closes the check: the loop is '
          'stable, and it also meets the distortion budget it was slowed '
          'down for.' % dict(d=ER('D3'))))

    add(h2('Feedback ripple against the burst threshold'))
    add(p('A crossover this low leaves 2f<sub>l</sub> ripple on the '
          'feedback pin. Because that pin is a power command, the ripple '
          'moves the commanded power up and down every half line cycle. If '
          'it crosses the burst-entry threshold the converter chatters in '
          'and out of burst. The ripple amplitude at the burst point is'))
    add(eq(r'\Delta V_{FB}\;=\;\frac{P_{in,BM}}{V_{out}}\,'
           r'\frac{1}{2\pi f_{l}\,C_{out}}\;G_{EA}(2f_{l})', key='dVFB'))
    add(p('Lowering R<sub>BM</sub> moves the burst entry point below that '
          'ripple. The burst threshold moves by 0.01&nbsp;V per k&Omega;, '
          'and the ripple has to clear it on both sides:'))
    add(eq(r'\Delta R_{BM}=\frac{\Delta V_{FB}}{2\times 0.01\ \mathrm{V/k\Omega}}',
           key='dRBM'))
    add(p('<b>Raising the crossover would shrink the ripple but worsen the '
          'distortion</b>, so trading it against R<sub>BM</sub> is the '
          'practical answer rather than speeding up the loop.'))
    add(note('<b>A loop this slow cannot recover from a large load step '
             'by itself.</b> The controller&rsquo;s anti-saturation circuit '
             'does that, and it needs the FB pin to reach its full current '
             'range. That is why R<sub>B</sub> must sit inside its window '
             '(Equation&nbsp;%(e)s). Checking the window is not optional.'
             % dict(e=ER('RBwin'))))

    # =============================================================== 6
    add(h1('Design example'))
    add(p('One design, from the specification to the component values. Every '
          'number below is either given, chosen, assumed, or computed from '
          'those, and each computed value shows the arithmetic it came from. '
          'The specification is <b>90 to %(Vacmax).0f&nbsp;Vac in, '
          '%(Vout).0f&nbsp;V / %(Iout).1f&nbsp;A = %(Pout).1f&nbsp;W out</b>, '
          'centre-tapped synchronous rectification, no bulk capacitor and no '
          'boost stage.' % V))

    add(h2('The specification, sorted by what kind of number it is'))
    add(p('The only useful question about a number is whether it can be '
          'moved, so the kind of each one is stated: <b>given</b> by the load '
          'and the mains, <b>chosen</b> by the designer, or <b>assumed</b> in '
          'place of a measurement that has not been made yet.'))
    add(tbl('The specification. Everything else in this chapter is computed '
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
              'halves the secondary conduction loss; doubles the device '
              'reverse voltage'],
             ['Target series resonance', 'f<sub>r</sub>', '%(frt).0f kHz' % V,
              'chosen', 'sets the magnetics size'],
             ['Specified maximum f<sub>sw</sub>', 'f<sub>sw,max</sub>',
              '%(fswspec).0f kHz (1.5 f<sub>r</sub>)' % V, 'chosen',
              'an input to &lambda;, Section&nbsp;'
              + SR('f<sub>sw,max</sub> does not check the tank '
                   '&mdash; it computes it')],
             ['Bridge dead time', 't<sub>D</sub>', '%(tD).0f ns' % V, 'chosen',
              'what the ZVS sweep has to beat'],
             ['V<sub>CC</sub> source', '&mdash;', 'external 12 V rail',
              'chosen', 'no turns-ratio ceiling on the auxiliary winding'],
             ['LLC stage efficiency', '&eta;<sub>HB</sub>',
              '%(etaHB).0f %%' % V, 'assumed',
              'a 95 %% outcome moves R<sub>ac</sub> and R<sub>CS</sub> by '
              'about 3 %%; nothing downstream is sensitive' % {}],
             ['Oscillator idle time', 'T<sub>idle</sub>',
              '%(Tidle).0f ns' % V, 'assumed',
              'the draft datasheet also says 700 ns, which would close the '
              'floor margin &mdash; the first thing to measure'],
             ['R<sub>DS(on)</sub> temperature factor', 'k<sub>T</sub>',
              '%(Rdpk).1f / %(Rdsk).1f' % V, 'assumed',
              'primary / secondary, read off the datasheet curves at '
              'T<sub>j,max</sub>'],
             ['Burst entry point', 'r<sub>BM</sub>',
              '%(PinBM).0f W (%(rBM).0f %% of rated)'
              % dict(V, rBM=A.SH['r.BM'] * 100), 'assumed',
              'sets R<sub>BM</sub>, then checked against the feedback '
              'ripple']],
            widths=[CW * 0.20, CW * 0.12, CW * 0.22, CW * 0.09, CW * 0.37],
            key='spec-given'))
    add(note('<b>Harmonic class.</b> IEC&nbsp;61000-3-2 Class&nbsp;D reaches '
             'only 600&nbsp;W. This design draws %(Pin).0f&nbsp;W at the '
             'input, so the absolute Class&nbsp;A limits apply.' % V))

    add(h2('What the design came out as'))
    add(tbl('Principal values. The rest of the chapter shows where each one '
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
              'B<sub>pk</sub> 0.20 T' % V],
             ['Frequency', 'f<sub>sw</sub> %(fswA).1f kHz at the low corner, '
              '%(fswB).1f kHz at the high corner' % V],
             ['Output', '%(Cout1).0f &micro;F &times; %(nC).0f = '
              '%(Cout).1f mF, ripple %(dVo).2f V (%(dVopc).2f %%), '
              'hold-up %(thold).2f ms' % V],
             ['Controller', 'R<sub>T</sub> %(RT).0f k&Omega;, '
              'C<sub>T</sub> %(CT).0f pF, R<sub>CS</sub> %(RCS).1f m&Omega;, '
              'R<sub>CFG</sub> %(RCFG).0f k&Omega;, '
              'R<sub>BM</sub> %(RBM).0f k&Omega;' % V],
             ['Loop', 'f<sub>cross</sub> %(fcross).2f Hz, '
              '&Phi;<sub>M</sub> %(PM).2f&deg;, '
              'third harmonic %(D3).2f %%' % V]],
            widths=[CW * 0.18, CW * 0.82]))

    # ------------------------------------------------ what a margin ratio is
    add(h2('What a verification margin is'))
    add(p('Every check has the same shape: what the design has, divided by '
          'what it needs.'))
    add(eq(r'k\;=\;\frac{X_{\mathrm{act}}}{X_{\mathrm{req}}}\qquad\Longrightarrow\qquad \mathrm{pass\;when}\;k>1', key='margin'))
    add(p('k&nbsp;=&nbsp;1.05 is five per cent of room, k&nbsp;=&nbsp;0.9 is '
          'ten per cent short. The ratios have no units and all point the '
          'same way, so a frequency check and a power check can sit in one '
          'column, and the smallest k is the thinnest part of the design.'))
    _kb = V['kPloss'] * A.SH['P.mos_dc']          # the budget, recovered
    _ks = V['kPSR'] * A.SH['P.SR'] / 2.0
    add(tbl('The verification margins.',
            [['Check', 'k = has / needs', 'Substituted', 'k'],
             ['ZVS at the worst point of the sweep',
              'T<sub>ZC,min</sub> / t<sub>D</sub>',
              '%(zTzc).0f ns / %(tD).0f ns' % dict(V, **ZVS_WORST),
              '%(zk).3f' % dict(V, **ZVS_WORST)],
             ['Oscillator floor clears the lower resonance',
              'f<sub>Min</sub> / f<sub>o</sub>',
              '%(fMin).2f kHz / %(fo).2f kHz' % V, '<b>%(kfloor).3f</b>' % V],
             ['Oscillator ceiling clears the operating maximum',
              'f<sub>Max</sub> / f<sub>sw,max</sub>',
              '%(fMax).2f kHz / %(fswmaxop).2f kHz' % V, '%(kceil).3f' % V],
             ['Over-current threshold clears the tank peak',
              'I<sub>OCP1</sub> / I<sub>Lr,pk</sub>',
              '%(I).2f A / %(Icomp).2f A' % dict(V, I=A.SH['I.OCP1']),
              '%(kOCP).3f' % V],
             ['Hold-up achieved against hold-up required',
              't<sub>hold</sub> / T<sub>hold</sub>',
              '%(thold).2f ms / %(Thold).0f ms' % V, '%(khold).3f' % V],
             ['Secondary loss against its budget',
              'P<sub>budget</sub> / P<sub>SR,leg</sub>',
              '%(b).2f W / %(a).2f W' % dict(b=_ks, a=A.SH['P.SR'] / 2.0),
              '%(kPSR).3f' % V],
             ['Primary loss against its budget',
              'P<sub>budget</sub> / P<sub>mos,dc</sub>',
              '%(b).2f W / %(a).2f W' % dict(b=_kb, a=A.SH['P.mos_dc']),
              '<b>%(kPloss).3f</b>' % V]],
            widths=[CW * 0.34, CW * 0.18, CW * 0.26, CW * 0.10],
            key='margins'))
    add(note('<b>Two rows need reading with care.</b> k<sub>Ploss</sub> = '
             '%(kPloss).3f is a result, not a failed calculation: the '
             'standing primary device spends %(a).2f&nbsp;W against a '
             '%(b).0f&nbsp;W budget, and Section&nbsp;%(ref)s says why the '
             'design goes ahead anyway. k<sub>floor</sub> = %(kfloor).3f looks '
             'like a safe 2&nbsp;%%, but the transformer tolerance and the '
             'oscillator idle time both move it, and neither is known to '
             '2&nbsp;%% yet.'
             % dict(V, a=A.SH['P.mos_dc'], b=_kb,
                    ref=SR('Semiconductor requirements'))))

    # ------------------------------------------------ the chain, step by step
    add(h2('Following the numbers through'))
    add(p('The design in the order it was computed. Each step names the '
          'equation it uses, shows it again, and puts this design&rsquo;s '
          'numbers into it, so that nothing in the tables above appears '
          'without its arithmetic. Table&nbsp;%s collects the results.'
          % TR('chain')))
    _SH = A.SH
    _rt = (1 + V['lam']) ** 0.5
    # -- power
    add(p('<b>Step 1 &mdash; the power the tank has to pass.</b> The output '
          'is P<sub>out</sub>. The input bridge, the EMI filter and the LLC '
          'stage itself are each given a loss budget, the last one as '
          '&eta;<sub>HB</sub> of the power into the tank:'))
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
    add(p('<b>Step 3 &mdash; the turns ratio.</b> The wound ratio is the '
          'input here, because %(NpSet)d&nbsp;:&nbsp;%(Ns)d is what can be '
          'built; the plain calculation would give n = %(ncalc).3f. The '
          'equivalent-model ratio follows from the wound one and the '
          'realised &lambda; (step 8):'
          % dict(V, ncalc=_SH['n.calc'])))
    add(eqagain('nnT'))
    add(calc(r'n=\frac{n_{T}}{\sqrt{1+\lambda_{act}}}=\frac{%.3f}{%.4f}'
             r'=\mathbf{%.3f}' % (V['nT'], _rt, V['n'])))
    add(eqagain('Vrefl'))
    add(calc(r'V_{refl}=n\,V_{o,eff}=%.3f\times %.1f=\mathbf{%.1f\ V}'
             % (V['n'], V['Vout'], V['Vrefl'])))
    # -- gain demanded
    add(p('<b>Step 4 &mdash; the gain the tank is asked for</b>, at the line '
          'peak (&theta; = 90&deg;) of each corner:'))
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
    add(p('<b>Step 6 &mdash; the cap on the quality factor and the design '
          'impedance.</b> Two limits are evaluated at the low corner, the Q '
          'at which the tank still reaches M<sub>low</sub> and the Q at '
          'which ZVS still completes inside t<sub>D</sub>, and the smaller '
          'is kept. With Q defined by Equation&nbsp;%s:' % ER('Qdef')))
    add(calc(r'Q_{ZVS}=\mathbf{%.4f}\qquad '
             r'Z_{0,design}=R_{ac}\,Q_{ZVS}=%.2f\times %.4f'
             r'=\mathbf{%.2f\ \Omega}'
             % (V['QZVS'], V['Rac'], V['QZVS'], V['Z0'])))
    # -- Cr, Lr
    add(p('<b>Step 7 &mdash; the resonant capacitor and inductor.</b> The '
          'design impedance and the target f<sub>r</sub> give '
          'C<sub>r</sub>; it is taken <b>up</b> on purpose, to gain Q '
          'margin. L<sub>r</sub> then pairs with the <i>selected</i> '
          'C<sub>r</sub>, which is why it is not '
          'Z<sub>0</sub>/2&pi;f<sub>r</sub>:'))
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
    add(p('<b>Step 8 &mdash; &lambda; and the magnetising inductance.</b> '
          'Four candidates for &lambda; are computed and the largest is '
          'binding; two of them carry f<sub>sw,max</sub> in a '
          'denominator:'))
    add(eqagain('lam'))
    add(calc(r'\lambda_{1}=%.3f\,,\quad \lambda_{2}=%.3f\,,\quad '
             r'\lambda_{TD}=\mathbf{%.3f}\quad\Longrightarrow\quad '
             r'L_{m}=\frac{L_{r}}{\lambda_{TD}}=\frac{%.0f}{%.3f}'
             r'=%.2f\ \mu\mathrm{H}'
             % (_SH['λ.1'], _SH['λ.2'], _SH['λ.TD'], V['Lr'], _SH['λ.TD'],
                V['Lmc'])))
    add(p('That %(Lmc).1f&nbsp;&micro;H is the <i>no-load</i> condition at '
          'the high corner, which this design knowingly does not meet '
          '(Section&nbsp;%(ref)s), so it is not rounded to. L<sub>m</sub> is '
          'chosen with n so that n<sub>T</sub> lands on a windable ratio, '
          'and the &lambda; that results is:'
          % dict(V, ref=SR('The other bound on &lambda;, and where it has '
                           'no solution'))))
    add(calc(r'L_{m}=\mathbf{%.0f\ \mu H}\qquad '
             r'\lambda_{act}=\frac{L_{r}}{L_{m}}=\frac{%.0f}{%.0f}'
             r'=\mathbf{%.3f}' % (V['Lm'], V['Lr'], V['Lm'], V['lam'])))
    # -- realised
    add(p('<b>Step 9 &mdash; what the selected parts actually make.</b> '
          'These, not the targets, are what every later check is measured '
          'against:'))
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
                r'\ =\ %d:%d\ \mathrm{across the assembly},\ %d:%d\ \mathrm{per unit}'
                % (V['NpSet'], V['Ns'], V['Np'], V['Ns']))))
    add(tbl('The design, step by step: the results of the nine steps.',
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
            key='chain'))
    add(note('<b>Steps 7 and 8 are the judgement calls.</b> C<sub>r</sub> was '
             'taken to %(Cr).0f&nbsp;nF against a calculated %(Crc).1f&nbsp;nF '
             'and L<sub>m</sub> to %(Lm).0f&nbsp;&micro;H against '
             '%(Lmc).1f&nbsp;&micro;H; both lower Q<sub>pk</sub> and hold '
             '&lambda;, which is where the ZVS margin comes from. Everything '
             'else is arithmetic any two engineers would reproduce '
             'identically.' % V))
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
            '%(Tzc).0f&nbsp;ns, so it understates the margin by '
            '%(mag).0f&nbsp;%%; on another tank in the same family it '
            'overstates by about 23&nbsp;%%. Read with &lambda;<sub>act</sub> '
            '= %(lam).3f instead of the design &lambda; = %(lamreq).3f it '
            'returns %(TzcCFact).0f&nbsp;ns, a capacitive answer for a tank '
            'well inside the inductive region. So this design is judged by '
            'the sweep.'
          % dict(V, mag=abs(V['TzcCFpc']), lamreq=A.SH['λ'])))
    add(p('The capacitive edge of the full-load curve is where arg '
          'Z<sub>in</sub> = 0, at %(fnEdge).1f&nbsp;kHz; the gain peak sits '
          'lower, at %(fnPk).1f&nbsp;kHz, and there the bridge still sees '
          '%(phPk).1f&deg; of capacitive phase (Section&nbsp;%(ref)s). Neither '
          'is used for the verdict: the sweep measures T<sub>ZC</sub> '
          'directly.'
          % dict(V, ref=SR('The two boundaries are not the same boundary'),
                 **_edge_numbers(A))))
    _z = dict(V, **ZVS_WORST)
    if ZVS_WORST['same']:
        add(p('The worst point in that sweep is full load at the low '
              'equivalent corner, <b>T<sub>ZC</sub>&nbsp;=&nbsp;'
              '%(zTzc).0f&nbsp;ns against t<sub>D</sub>&nbsp;=&nbsp;'
              '%(tD).0f&nbsp;ns</b>, a margin of %(zk).2f times &mdash; the '
              'same corner the tank was designed at.' % _z))
    else:
        add(p('<b>The worst point is not the corner the tank was designed '
              'at.</b> Full load at the low equivalent input is where the '
              '<i>gain</i> requirement is set, and it gives '
              'T<sub>ZC</sub>&nbsp;=&nbsp;%(cTzc).0f&nbsp;ns, a margin of '
              '%(ck).2f. The smallest number in the table is '
              '<b>%(zTzc).0f&nbsp;ns at %(zLoad).0f&nbsp;%% load and the '
              '%(zVin).1f&nbsp;Vac equivalent corner</b>, a margin of '
              '%(zk).2f against t<sub>D</sub>&nbsp;=&nbsp;'
              '%(tD).0f&nbsp;ns. That is the number this design is held '
              'to.' % _z))
        add(note('<b>Why light load at high line can be the ZVS corner.</b> '
                 'The charge that swings the bridge node is carried by the '
                 'magnetising current, and its peak goes as '
                 'V<sub>in</sub>/(4f<sub>sw</sub>L<sub>m</sub>). Shed load '
                 'and the controller raises f<sub>sw</sub> to cut the gain, '
                 'so that current falls while the node still has the same '
                 'capacitance to move. Sweeping only the design corner '
                 'therefore reports a margin that is not there.'))

    add(h2('Which side of resonance this design runs on'))
    add(p('Section&nbsp;' + SR('Which side of resonance the converter runs on')
          + ' says the turns ratio decides this. With n<sub>T</sub> = '
            '%(nT).2f, at all but the lowest line conditions the tank spends '
            'part of every line cycle above f<sub>r</sub>, where the '
            'secondary loses zero-current turn-off, so the rectifier body '
            'diode and the SR dead time both need checking.' % V))
    add(fig('an_above_below',
            'Which side of f<sub>r</sub> the converter is on over a line '
            'half cycle, at four equivalent inputs. At the low corner it '
            'never leaves the boosting region; at the high corner it spends '
            'most of the cycle bucking. Every curve converges on '
            'f<sub>o</sub> at the zero crossing.', width=CW))
    add(tbl('Peak f<sub>sw</sub> over the half cycle against f<sub>r</sub> = '
            '%(fr).1f kHz. %(nAbove)d of the seven line conditions cross into '
            'above-resonance operation for part of the cycle.' % V,
            [['Line condition', 'V<sub>eq</sub>', 'peak f<sub>sw</sub>',
              'side of f<sub>r</sub>']]
            + [[nm, '%.0f V' % veq, '%.1f kHz' % pk,
                '<b>above</b>' if ab else 'below']
               for nm, veq, pk, ab in V['fswPk']],
            widths=[CW * 0.30, CW * 0.18, CW * 0.22, CW * 0.30]))
    add(fig('f12_two_divergences',
            'Near the zero crossing the required gain diverges and the load '
            'vanishes together, so the operating point converges on '
            'f<sub>o</sub> = %(fo).1f&nbsp;kHz (Section&nbsp;%(ref)s).'
            % dict(V, ref=SR('Two divergences that cancel'))))

    add(h2('The currents this design has to carry'))
    add(p('Ratings come from the worst switching cycle and losses from the '
          'line-cycle rms, so both are listed. The row to watch is the '
          'composite tank peak: it is what the primary devices and '
          'R<sub>CS</sub> see, and it is neither the sum of the two component '
          'peaks nor the larger of them.'))
    add(fig('an_tank_current',
            'The composite tank current at the low equivalent corner, full '
            'load, and why its peak is not the sum of the two component '
            'peaks: they occur at different instants.'))
    add(tbl('Currents at the low equivalent corner, full load, '
            '&theta; = 90&deg;.',
            [['Quantity', 'Value', 'Where it is used'],
             ['f<sub>sw</sub>', '%(fswA).1f kHz' % V,
              'oscillator floor check'],
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
            widths=[CW * 0.36, CW * 0.20, CW * 0.44]))

    add(h2('The transformer, as built'))
    add(p('The tank asks for L<sub>r</sub> = %(Lr).0f&nbsp;&micro;H, '
          'L<sub>m</sub> = %(Lm).0f&nbsp;&micro;H and n<sub>T</sub> = '
          '%(nT).2f. The transformer is one part: a %(Np)d-turn primary and '
          'two secondary windings of N<sub>s</sub> = %(Ns)d turns, NS2 and '
          'NS3, joined at the centre tap, one conducting in each half '
          'period. Several units in series are the alternative when one '
          'window will not take the copper (Section&nbsp;%(ref2)s); that is '
          'not needed here.'
          % dict(V, ref2=SR('If one transformer is not practical'))))
    add(fig('an_xfmr_read',
            'Where each number of the table below is read. Top: the primary winding '
            'current, the current in its two secondary windings '
            'and the secondary winding voltage over one switching period, at '
            'the worst cycle (line peak, %(Veqlo).0f&nbsp;Vac equivalent, '
            'full load). Lower left: the rms of the two winding currents '
            'over the line half cycle, and the line-cycle values the copper '
            'is sized on. Lower right: the DC-overlap test, a bench '
            'condition. The circled marks are the rows of Table&nbsp;%(t)s.'
            % dict(V, t=TR('xfmr-read'))))
    add(tbl('The transformer as wound and specified.',
            [['Quantity', 'Value', 'Note'],
             ['Turns', 'N<sub>p</sub> %(Np)d T; NS2 %(Ns)d T, NS3 %(Ns)d T; '
              'NAUX %(Naux)d T' % V,
              'n<sub>T</sub> = %(Np)d / %(Ns)d = %(nT).1f; the auxiliary is '
              'ZCD sense only' % V],
             ['Open-circuit inductance', '%(Lopen).1f &micro;H' % V,
              'L<sub>r</sub> + L<sub>m</sub>, every other winding open'],
             ['Short-circuit inductance', '%(Lshort).1f &micro;H' % V,
              'this is L<sub>r</sub>: no separate resonant inductor'],
             ['A<sub>L</sub>', '%(AL).0f nH' % V,
              'open-circuit inductance / N<sub>p</sub>&sup2;; the core is '
              'gapped to it']],
            widths=[CW * 0.24, CW * 0.30, CW * 0.46],
            key='trafo-built'))
    _w = _CORE.winding(V)
    _B = _CORE.BOBBIN
    add(p('<b>Pins.</b> The part is wound on the %(former)s coil former of '
          'the %(chosen)s core, %(pins)d pins in two rows of %(half)d. NP1 '
          'and the ZCD auxiliary take one row, NS2 and NS3 the other. Each '
          'secondary terminal uses two pins, because one winding carries '
          'the whole secondary current. The centre tap is made on the '
          'board: the finish of NS2 and the start of NS3 come out on '
          'neighbouring pins.'
          % dict(former=_B['former'], pins=_B['pins'], half=_B['pins'] // 2,
                 chosen=_CORE.CHOSEN)))
    add(fig('an_xfmr_pins',
            'The transformer: the schematic symbol with its pin numbers, and '
            'the same pins on the %(former)s coil former in the '
            'mounting-direction view of the TDK drawing (%(pins)d pins, '
            'pitch %(pitch).2f&nbsp;mm, rows %(rows).2f&nbsp;mm apart). A '
            'ring in the colour of a winding marks the pins it uses; grey '
            'pins are free. The dot end of every winding is the first pins '
            'of its pair. %(note)s'
            % dict(former=_B['former'], pins=_B['pins'], pitch=_B['pitch'],
                   rows=_B['rows_apart'], note=_CORE.PIN_NOTE)))
    _PM = _CORE.PINMAP
    add(tbl('Winding-to-pin assignment.',
            [['Winding', 'Pins (start &ndash; finish)', 'Turns', 'Conductor',
              'Row'],
             ['NP1 primary', _CORE.pins('NP1', '&ndash;'), '%d T' % V['Np'],
              'Litz %d &times; &oslash;%.2f mm' % (_w['n_strand'], _CORE.D_STRAND),
              _B['rows'][0]],
             ['NAUX auxiliary (ZCD)', _CORE.pins('NAUX', '&ndash;'),
              '%d T' % V['Naux'], 'any wire, sense only', _B['rows'][0]],
             ['NS2 secondary', _CORE.pins('NS2', '&ndash;'), '%d T' % V['Ns'],
              'foil %.2f &times; %.1f mm, %d in parallel'
              % (_w['t_foil'], _w['w_foil'], _w['n_foil']),
              _B['rows'][1]],
             ['NS3 secondary', _CORE.pins('NS3', '&ndash;'), '%d T' % V['Ns'],
              'the same foil, on top of NS2', _B['rows'][1]],
             ['Centre tap', '%s, joined on the PCB' % _CORE.tap_text(),
              '&mdash;', '&mdash;', _B['rows'][1]],
             ['Free', ', '.join(str(n) for n in _CORE.free_pins()),
              '&mdash;', 'not connected', 'both rows']],
            widths=[CW * 0.20, CW * 0.26, CW * 0.09, CW * 0.27, CW * 0.18],
            key='pins'))
    add(p('<b>Polarity.</b> With the dots as drawn, the ZCD pin is positive '
          'while the low-side switch of leg 1 is on, as the controller '
          'requires. NS2 and NS3 are wound in the same sense; the tap joins '
          'the finish of NS2 to the start of NS3.'))
    add(p('Three more numbers follow from Table&nbsp;%s.'
          % TR('trafo-built')))
    add(p('<b>Peak flux density</b>, at f<sub>r</sub>:'))
    add(eqagain('Bpk'))
    add(calc([r'B_{pk}=\frac{%.1f\ \mathrm{V}}{4\times %.2f\ \mathrm{kHz}'
              r'\times %d\times %.1f\ \mathrm{mm^{2}}}=\mathbf{%.0f\ mT}'
              % (V['Vout'], V['fr'], V['Ns'], V['Aemm'], V['Bpk']),
              r'A_{e}\geq\frac{%.1f\ \mathrm{V}}{4\times %.2f\ \mathrm{kHz}\times %d'
              r'\times 0.20\ \mathrm{T}}=\mathbf{%.0f\ mm^{2}}'
              % (V['Vout'], V['fr'], V['Ns'], V['Aereq'])]))
    add(p('<b>Magnetising peak</b>, over L<sub>&mu;</sub> (it equals '
          'i<sub>&mu;,pk</sub>):'))
    add(eqagain('Isat'))
    add(calc(r'I_{eq}=\frac{%.4f\ \mathrm{T}\times %d\times %.1f\ \mathrm{mm^{2}}}'
             r'{%.2f\ \mu\mathrm{H}}=\mathbf{%.2f\ A}\ =\ i_{\mu,pk}'
             % (V['Bpk'] / 1e3, V['Np'], V['Aemm'], V['Lmu'] / V['nser'],
                V['Isateq'])))
    add(p('<b>Saturation test current</b>, the magnetising peak at the '
          'OVP2 output voltage:'))
    add(eqagain('Isatspec'))
    add(calc(r'I_{sat}=%.2f\ \mathrm{A}\times\frac{%.2f\ \mathrm{V}}{%.1f\ \mathrm{V}}'
             r'=%.2f\times %.4f=\mathbf{%.1f\ A}'
             % (V['Isateq'], V['OVP2'], V['Vout'], V['Isateq'],
                V['OVP2'] / V['Vout'], V['Isatspec'])))
    add(fig('an_mmf',
            'In service the secondary cancels most of the primary '
            'ampere-turns; with the secondary open, the whole test current '
            'magnetises the core. The design flux is therefore reached at '
            '%(ILm).2f&nbsp;A on the bench, not at the %(Icomp).2f&nbsp;A '
            'tank peak.' % V))

    # ------------------------------------------------ the core, chosen
    add(h2('The core and the winding'))
    _w = _CORE.winding(V)
    _R = _CORE.CORES[_CORE.CHOSEN]
    _cw = _CORE.window(V) / _CORE.K_U
    add(p('The core is TDK <b>%(chosen)s</b>, %(mat)s (core %(core)s, coil '
          'former %(former)s). The centre leg is ground to '
          'A<sub>L</sub>&nbsp;=&nbsp;%(AL).0f&nbsp;nH, about %(gap).1f&nbsp;mm '
          'of gap in total. Figure&nbsp;%(f)s shows the core in section and '
          'the winding in its window; Table&nbsp;%(t)s names each item and '
          'Table&nbsp;%(t2)s gives the arithmetic behind the winding.'
          % dict(chosen=_CORE.CHOSEN, mat=_R['material'], core=_R['core'],
                 former=_R['former'], AL=V['AL'], gap=_CORE.dg_gap(V),
                 f=FR('an_core_section'), t=TR('legend42'),
                 t2=TR('winding'))))
    add(fig('an_core_section',
            'The core in section (left, to scale), the winding unrolled '
            'along the bobbin (top right, to scale) and the secondary layer '
            'by layer (bottom right, not to scale). Primary and secondary '
            'sit side by side with %(g).2f&nbsp;mm between them. The '
            'circled numbers are the rows of Table&nbsp;%(t)s.'
            % dict(g=_w['gap'], t=TR('legend42')), shrink=False))
    add(tbl('Items of the figure.',
            [['Mark', 'Item', 'Turns', 'Conductor, placement'],
             ['1', 'NP1 primary, pins %s' % _CORE.pins('NP1', '&ndash;'),
              '%d T' % V['Np'],
              'Litz %d &times; &oslash;%.2f mm (bundle &oslash;%.2f mm), '
              '%d layers of %s turns'
              % (_w['n_strand'], _CORE.D_STRAND, _w['d_litz'], _w['layers'],
                 '/'.join(str(n) for n in _w['rows_p']))],
             ['2', 'NS2 secondary, pins %s' % _CORE.pins('NS2', '&ndash;'),
              '%d T' % V['Ns'],
              'foil %.2f &times; %.1f mm, %d foils in parallel per turn; '
              'on the bobbin'
              % (_w['t_foil'], _w['w_foil'], _w['n_foil'])],
             ['3', 'NS3 secondary, pins %s' % _CORE.pins('NS3', '&ndash;'),
              '%d T' % V['Ns'], 'the same foil, on top of NS2'],
             ['4', 'Separation', '&mdash;',
              '%.2f mm between primary and secondary; sets L<sub>short</sub>'
              % _w['gap']],
             ['5', 'Margin tape', '&mdash;',
              '%.1f mm at each flange' % _CORE.MARGIN],
             ['6', 'Centre-leg gap', '&mdash;',
              'about %.1f mm in total, ground to A<sub>L</sub> = %.0f nH'
              % (_CORE.dg_gap(V), V['AL'])],
             ['7', 'Window', '&mdash;',
              'A<sub>N</sub> = %.0f mm&sup2;, %.0f mm&sup2; of copper in it'
              % (_R['AN'], _CORE.window(V))],
             ['&mdash;', 'NAUX auxiliary, pins %s'
              % _CORE.pins('NAUX', '&ndash;'), '%d T' % V['Naux'],
              'any wire; ZCD sense only']],
            widths=[CW * 0.07, CW * 0.30, CW * 0.09, CW * 0.54],
            key='legend42'))
    _rows = _CORE.copper(V)
    _rp, _rs = _rows[0], _rows[1]
    add(tbl('The winding, from current to copper. NS3 is the same as NS2.',
            [['Step', 'Primary NP1', 'Secondary NS2'],
             ['Rms current', '%.2f A' % _rp[2], '%.2f A' % _rs[2]],
             ['Copper area at J = %.1f A/mm&sup2;' % _CORE.J_CU,
              '%.2f / %.1f = <b>%.2f mm&sup2;</b>'
              % (_rp[2], _CORE.J_CU, _rp[3]),
              '%.2f / %.1f = <b>%.2f mm&sup2;</b>'
              % (_rs[2], _CORE.J_CU, _rs[3])],
             ['Conductor (skin depth %.2f mm at f<sub>r</sub>)' % V['delta'],
              'Litz, &oslash;%.2f mm strands: %.2f / %.4f = <b>%d strands</b>; '
              'bundle &oslash;%.2f mm'
              % (_CORE.D_STRAND, _rp[3],
                 3.141592653589793 * _CORE.D_STRAND ** 2 / 4, _w['n_strand'],
                 _w['d_litz']),
              'foil %.2f mm thick: %.2f / %.2f = %.1f mm wide, made as '
              '<b>%d foils of %.1f mm</b> in parallel'
              % (_w['t_foil'], _rs[3], _w['t_foil'],
                 _w['w_foil'] * _w['n_foil'], _w['n_foil'], _w['w_foil'])],
             ['Turns', '%d, in %d layers (%s)'
              % (V['Np'], _w['layers'],
                 '/'.join(str(n) for n in _w['rows_p'])),
              '%d' % V['Ns']],
             ['Width on the bobbin',
              '%d &times; %.2f = <b>%.2f mm</b>'
              % (_w['per_layer'], _w['d_litz'], _w['w_pri']),
              '<b>%.1f mm</b>' % _w['w_foil']],
             ['Radial build',
              '%d &times; %.2f = %.2f mm' % (_w['layers'], _w['d_litz'],
                                             _w['build_p']),
              'NS2 + NS3: %d &times; (%.2f + %.2f) = %.1f mm'
              % (2 * V['Ns'] * _w['n_foil'], _w['t_foil'], _CORE.T_FOIL_INS,
                 _w['build_s'])],
             ['Left between the windings',
              '%.1f &minus; 2 &times; %.1f &minus; %.2f &minus; %.1f = '
              '<b>%.2f mm</b>'
              % (_w['M']['wind_w'], _CORE.MARGIN, _w['w_pri'], _w['w_foil'],
                 _w['gap']), ''],
             ['Copper in the window',
              '%d &times; %.2f + %d &times; %.2f = %.1f mm&sup2;, '
              '%.0f %% of A<sub>N</sub> at k<sub>u</sub> = %.2f'
              % (V['Np'], _rp[3], 2 * V['Ns'], _rs[3], _CORE.window(V),
                 100 * _cw / _R['AN'], _CORE.K_U),
              '']],
            widths=[CW * 0.26, CW * 0.40, CW * 0.34],
            key='winding'))
    add(p('Reduced to what a supplier can measure at the terminals, this '
          'gives the specification sheet. L<sub>&mu;</sub> is deliberately '
          'absent (Section&nbsp;'
          + SR('What the transformer specification must say') + ').'))
    add(tbl('Transformer specification for the worked design.',
            [['Item', 'Value', 'Condition'],
             ['Core', '%s, %s, A<sub>L</sub> %.0f nH' % (
                 _CORE.CHOSEN, _R['material'], V['AL']),
              'core %s, coil former %s; distributed gap' % (_R['core'], _R['former'])],
             ['Turns', 'N<sub>p</sub> %(Np)d T; NS2 %(Ns)d T and NS3 %(Ns)d T; '
              'NAUX %(Naux)d T' % V,
              'two secondary windings, centre tap outside the part'],
             ['Open-circuit inductance',
              '%(Lopen).1f &micro;H, &minus;%(Ldrop).1f %% at worst'
              % V,
              'primary, all other windings open'],
             ['Leakage inductance', '%(Lshort).1f &micro;H &plusmn;10 %%' % V,
              'primary, secondary shorted'],
             ['DC overlap', '&ge; 90 %% of initial inductance' % V,
              'test current %(Isatspec).0f A (mark 7)' % V],
             ['Primary current', '%(Iprilc).1f A rms / %(Icomp).1f A pk' % V,
              'line-cycle rms (mark 2), composite peak (mark 1)'],
             ['Secondary current, each winding',
              '%(Idio).1f A rms / %(Isec).0f A pk' % V,
              'line-cycle rms (mark 5), peak (mark 4)'],
             ['Core area', 'A<sub>e</sub> &ge; %(Aereq).0f mm&sup2;' % V,
              'holds B<sub>pk</sub> at or below 0.20 T (mark 6)'],
             ['Switching frequency', '%(fswA).0f to %(fswB).0f kHz' % V,
              'at full load']],
            widths=[CW * 0.28, CW * 0.34, CW * 0.38]))

    add(h2('The output bank, as sized'))
    add(p('Both conditions of Section&nbsp;%(ref)s, on this specification; '
          'the larger wins.' % dict(V, ref=SR('The output capacitor bank'))))
    add(p('<b>The ripple condition</b>, with &Delta;v as a fraction and '
          'V<sub>out</sub> in volts:'))
    add(eqagain('Crip'))
    add(calc(r'C_{out}\geq\frac{%.1f\ \mathrm{W}}{2\pi\times %.0f\ \mathrm{Hz}'
             r'\times %.2f\times %.0f\ \mathrm{V^{2}}}=\mathbf{%.2f\ mF}'
             % (V['Pout'], V['flmin'], V['dv'] / 100.0, V['Vout'] ** 2,
                V['Crip'])))
    add(p('<b>The hold-up condition</b>, starting half a ripple below '
          'V<sub>out</sub> because the mains may disappear at the ripple '
          'trough:'))
    add(eqagain('Chold'))
    add(calc(r'C_{out}\geq\frac{2\times %.1f\ \mathrm{W}\times %.3f\ \mathrm{s}}'
             r'{%.2f^{2}-%.0f^{2}}=\mathbf{%.2f\ mF}'
             r'\qquad(\mathrm{started at }V_{out}:\ %.2f\ \mathrm{mF})'
             % (V['Pout'], V['Thold'] / 1e3, V['Vout'] - V['dVo'] / 2,
                V['Vomin'], V['Chold'],
                2 * V['Pout'] * V['Thold'] / 1e3
                / (V['Vout'] ** 2 - V['Vomin'] ** 2) * 1e3)))
    add(p('<b>Which one wins</b> is settled by the screening inequality, '
          'at k = V<sub>o,min</sub>/V<sub>out</sub> = %(k).3f:'
          % dict(k=V['Vomin'] / V['Vout'])))
    add(eqagain('ripscreen'))
    add(calc(r'%.3f\ >\ %.3f\quad\Longrightarrow\quad\mathrm{ripple decides}'
             % (V['ripLHS'], V['ripRHS'])))
    add(p('The two are only %(ripK).3f apart; relaxed to 10&nbsp;%% ripple '
          'the two sides would swap. The bank fitted is the next assembly '
          'up from %(Crip).1f&nbsp;mF: <b>%(Cout1).0f&nbsp;&micro;F &times; '
          '%(nC).0f = %(Cout).1f&nbsp;mF</b>.' % V))
    add(fig('f19_cout_criterion',
            'Left: both sizing conditions fall as 1/V<sub>out</sub>&sup2;, '
            'so only the specification separates them; at %(Vout).0f&nbsp;V '
            'ripple asks for %(Crip).1f&nbsp;mF and hold-up for '
            '%(Chold).1f&nbsp;mF. Right: the hold-up energy is the same '
            '%(Ehold).1f&nbsp;J either side of the boost stage; on a '
            '400&nbsp;V bus falling to 320&nbsp;V it is a '
            '%(Cbulk).0f&nbsp;&micro;F part, on this output it is '
            '%(Chold).1f&nbsp;mF, %(Cratio).0f&nbsp;times more, because the '
            'usable voltage window is so much smaller. That ratio is the '
            'price of the architecture.' % V))
    add(tbl('What the selected bank then delivers, and what it has to '
            'survive.',
            [['Quantity', 'Value', 'Against'],
             ['Achieved ripple', '%(dVo).2f V (%(dVopc).2f %%)' % V,
              '%(dv).0f %% allowed' % V],
             ['Achieved hold-up', '%(thold).2f ms' % V,
              '%(Thold).0f ms required &mdash; %(tholdVo).2f ms if started '
              'at V<sub>out</sub> instead of at the trough' % V],
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
            widths=[CW * 0.30, CW * 0.22, CW * 0.48], key='bank-built'))

    # ------------------------------------------------ loss budget
    add(h2('Where the power goes'))
    add(p('The specification allowed %(diff).1f&nbsp;W of loss between '
          'P<sub>in</sub> = %(Pin).1f&nbsp;W and P<sub>out</sub> = '
          '%(Pout).1f&nbsp;W, split three ways before any component existed. '
          'The device losses computed afterwards do not have to agree with '
          'that split, and here they do not.'
          % dict(V, diff=V['Pin'] - V['Pout'])))
    add(tbl('The budget as assumed, and the device losses as computed. The '
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
              'the half-bridge leg that never switches &mdash; the single '
              'largest item'],
             ['Primary switching, three positions', '%(a).2f W'
              % dict(a=A.SH['P.mos_sw']), 'not a problem'],
             ['Secondary rectifiers', '%(a).2f W'
              % dict(a=A.SH['P.SR']),
              '%(PSR).3f W per device, %(nSR).0f in parallel per leg' % V],
             ['Current-sense resistors', '%(a).2f W'
              % dict(a=A.SH['P.RCS']),
              '%(b).2f W at the worst switching cycle'
              % dict(b=A.SH['P.RCS_pk'])],
             ['Output capacitor ESR', '%(a).3f W'
              % dict(a=A.SH['P.Cout']), '&mdash;'],
             ['<b>Itemised total</b>', '<b>%(t).2f W</b>'
              % dict(t=A.SH['P.mos_dc'] + A.SH['P.mos_sw'] + A.SH['P.SR']
                     + A.SH['P.RCS'] + A.SH['P.Cout']),
              'and the magnetics are not in it']],
            widths=[CW * 0.34, CW * 0.14, CW * 0.52], key='loss'))
    add(note('<b>The efficiency assumption is optimistic.</b> The itemised '
             'device losses already come to %(t).1f&nbsp;W against the '
             '%(b).1f&nbsp;W that &eta;<sub>HB</sub> = %(etaHB).0f&nbsp;%% '
             'allows the LLC stage, before the transformer. Nothing '
             'electrical depends on it (95&nbsp;%% moves R<sub>ac</sub> and '
             'R<sub>CS</sub> by about 3&nbsp;%%); the thermal design does, '
             'and that is settled by measurement.'
             % dict(V, t=A.SH['P.mos_dc'] + A.SH['P.mos_sw'] + A.SH['P.SR']
                    + A.SH['P.RCS'] + A.SH['P.Cout'], b=A.SH['P.d_LLC'])))

    # ------------------------------------------------ the loop as built
    add(h2('What the semiconductors have to be'))
    add(p('Requirements, not part numbers; the four rules of Section&nbsp;'
          + SR('Semiconductor requirements') + ' decide whether they are '
          'stated correctly.'))
    add(tbl('Semiconductor requirements for the worked design.',
            [['Item', 'Requirement'],
             ['Primary drain-source voltage',
              '&ge; %(VDS).0f V, so a 600 V class part' % V],
             ['Primary body diode',
              'fast recovery: in full bridge the body diode conducts before '
              'turn-on'],
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
              'check the lead and clip rating, not only the die']],
            widths=[CW * 0.36, CW * 0.64]))
    add(h2('The voltage loop, as built'))
    from math import atan, degrees, sqrt, pi
    _at = lambda w, w0: degrees(atan(w / w0))
    _A = lambda w: (sqrt(1 + (w / V['wz']) ** 2)
                    / (sqrt(1 + (w / V['wp']) ** 2) * sqrt(1 + (w / V['wpx']) ** 2)))
    add(p('Sections&nbsp;%(a)s to %(b)s give the method. These are its '
          'numbers on this converter, in the order they are found. Every '
          'value comes from the design sheet.'
          % dict(a=SR('Voltage loop and compensation'),
                 b=SR('Feedback ripple against the burst threshold'))))
    add(p('<b>Step 1 &mdash; the output divider.</b> R<sub>I</sub> is '
          'chosen as %(RI).0f&nbsp;k&Omega; and R<sub>O</sub> follows from '
          'Equation&nbsp;%(e)s solved for it:'
          % dict(V, e=ER('RoVout'))))
    add(eqagain('RoVout'))
    add(calc(r'R_{O}=\frac{V_{R}\,R_{I}}{V_{out}-V_{R}}'
             r'=\frac{%.3f\ \mathrm{V}\times %.0f\ \mathrm{k\Omega}}'
             r'{%.1f\ \mathrm{V}-%.3f\ \mathrm{V}}=%.2f\ \mathrm{k\Omega}'
             r'\;\rightarrow\;\mathbf{%.0f\ k\Omega}'
             % (V['VR'], V['RI'], V['Vout'], V['VR'], V['Roc'], V['Ro'])))
    add(calc(r'V_{out}=%.3f\ \mathrm{V}\times\left(1+\frac{%.0f}{%.0f}\right)'
             r'=\mathbf{%.2f\ V}' % (V['VR'], V['RI'], V['Ro'], V['VoutAct'])))
    add(p('<b>Step 2 &mdash; the plant.</b> The feedback voltage above its '
          'offset at rated power is V<sub>FB</sub> = K<sub>pwr</sub> '
          'R<sub>CS</sub> P<sub>in,LLC</sub> = %(Kpwr).3f &times; '
          '%(RCS).0f&nbsp;m&Omega; &times; %(PinLLC).1f&nbsp;W = '
          '%(VFBv).3f&nbsp;V (Equation&nbsp;%(e)s). Then'
          % dict(V, PinLLC=V['Pout'] / (V['etaHB'] / 100.0), RCSo=V['RCS'] / 1e3,
                 e=ER('VFB'))))
    add(eqagain('Gplant'))
    add(calc(r'G_{o}=\frac{%.1f\ \mathrm{W}}{%.1f\ \mathrm{V}\times %.3f\ \mathrm{V}'
             r'\times %.1f\ \mathrm{mF}}=\mathbf{%.1f\ rad/s},\qquad'
             r'f_{cto}=\frac{%.1f}{2\pi}=%.1f\ \mathrm{Hz}'
             % (V['Pout'], V['Vout'], V['VFBv'], V['Cout'], V['Go'], V['Go'],
                V['fcto'])))
    add(p('<b>Step 3 &mdash; the gain the loop may have at '
          '2f<sub>l</sub>.</b> The output ripple at the lowest line '
          'frequency, and the compensator gain that keeps the third '
          'harmonic at %(D3set).0f&nbsp;%%:' % V))
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
    add(p('<b>Step 6 &mdash; where the zero and pole go.</b> With '
          '&Gamma;<sub>v</sub> = 0.744 &times; %(Veqhi).1f / %(Veqlo).2f = '
          '%(Gammav).4f:' % dict(V, Veqhi=V['Vacmax'])))
    add(eqagain('fMB'))
    add(calc([r'f_{MB}=\frac{1}{2\pi}\sqrt{\frac{%.2f\times %.4f\times %.2f}{%.4f}}'
              r'=\mathbf{%.2f\ Hz}'
              % (V['Go'], V['Kv'], V['EAo'], V['Gammav'], V['fMB']),
              r'f_{p}=%.4f\times %.2f=\mathbf{%.2f\ Hz},'
              r'\qquad f_{z}=\frac{%.2f}{%.4f}=\mathbf{%.3f\ Hz}'
              % (V['Kv'], V['fMB'], V['fp'], V['fMB'], V['Kv'], V['fz'])]))
    add(p('<b>Step 7 &mdash; the bias parts.</b> R<sub>P</sub> from '
          'Equation&nbsp;%(a)s with the TL431 minimum current '
          '%(Imin).1f&nbsp;mA, and the R<sub>B</sub> window from '
          'Equation&nbsp;%(b)s with V<sub>Z</sub> = %(VZ).0f&nbsp;V, '
          'V<sub>Fo</sub> = %(VFo).2f&nbsp;V, I<sub>FB,steady</sub> = '
          '%(IFBs).0f&nbsp;&micro;A, I<sub>FB,max</sub> = '
          '%(IFBm).0f&nbsp;&micro;A, CTR<sub>s</sub> = %(CTRs).2f and '
          'CTR<sub>m</sub> = %(CTRm).2f:'
          % dict(V, a=ER('RPmax'), b=ER('RBwin'))))
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
    add(p('<b>Step 9 &mdash; what the standard parts actually give.</b> '
          'Equation&nbsp;%(e)s with the rounded values:' % dict(e=ER('fzp'))))
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
    add(p('<b>Step 10 &mdash; the crossover and the phase margin.</b> '
          'G<sub>o</sub>EA<sub>o</sub> = %(Go).2f &times; %(EAoi).2f = '
          '%(g0).0f, so the iteration of Equation&nbsp;%(e)s starts at '
          '&omega;<sub>c</sub> = &radic;%(g0).0f = %(w0).1f&nbsp;rad/s '
          '(%(f0).1f&nbsp;Hz) and settles after a few steps at'
          % dict(V, e=ER('wc'), f0=V['w0'] / (2 * pi))))
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
    add(p('<b>Step 12 &mdash; the third harmonic the built loop causes.</b> '
          'The compensator gain at 2f<sub>l</sub> = %(f2).0f&nbsp;Hz '
          '(&omega; = %(w2fl).1f&nbsp;rad/s), from Equation&nbsp;%(a)s '
          'without the plant, and Equation&nbsp;%(b)s:'
          % dict(V, f2=2 * V['flmin'], a=ER('GEAtf'), b=ER('D3'))))
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
    add(fig('an_loop_bode',
            'Open-loop gain |T| and 180&deg; + arg&nbsp;T of the loop as '
            'built (Steps 9 to 11). The distance from &minus;180&deg; is the '
            'phase margin only at the crossover, where |T| = 0&nbsp;dB. The '
            'gain margin is read at f<sub>180</sub>, where that distance '
            'reaches zero.'))
    add(tbl('The voltage loop, as built.',
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
              'R<sub>BM</sub> %(RBMsel).0f &rarr; %(RBMrec).1f k&Omega;' % V]],
            widths=[CW * 0.34, CW * 0.28, CW * 0.38], key='loop-result'))

    # ------------------------------------------------ the controller network
    add(h2('The parts around the controller'))
    add(p('These are the results. The sections after this one derive each '
          'value in the order it has to be done, because every one of them '
          'is sized against something already fixed.'))
    add(tbl('Controller network for the worked design.',
            [['Part', 'Value', 'Result'],
             ['C<sub>T</sub> / R<sub>T</sub>',
              '%(CT).0f pF / %(RT).0f k&Omega;' % V,
              'f<sub>Min</sub> %(fMin).1f kHz, f<sub>Max</sub> %(fMax).1f kHz'
              % V],
             ['R<sub>CS</sub>', '%(RCS).1f m&Omega; (%(RCS1).0f m&Omega; '
              '&times; 5 in parallel)' % V,
              'OCP1 at %(kOCP).3f &times; the composite peak' % V],
             ['R<sub>CFG</sub>', '%(RCFG).0f k&Omega;' % V,
              'V<sub>BO</sub> %(VBO).1f V, morphing enabled' % V],
             ['R<sub>BM</sub>', '%(RBM).0f k&Omega;' % V,
              'burst-mode entry point'],
             ['ZCD divider', '%(RZH).0f k&Omega; / %(RZL).0f k&Omega;' % V,
              'OVP1 %(OVP1).2f V, OVP2 %(OVP2).2f V' % V],
             ['C<sub>in</sub>', '%(Cin).0f nF film' % V,
              'about 3.2 nF/W &mdash; there is no bulk capacitor'],
             ['Compensation',
              '%(CFo).0f nF / %(CF).0f nF / %(RF).0f k&Omega; / %(Cfx).2f nF'
              % V,
              'f<sub>cross</sub> %(fcross).2f Hz, &Phi;<sub>M</sub> '
              '%(PM).2f&deg;' % V]],
            widths=[CW * 0.20, CW * 0.34, CW * 0.46]))

    add(h2('The oscillator: C<sub>T</sub> first, then R<sub>T</sub>'))
    add(p('The VCO charges C<sub>T</sub> from the sum of a fixed current '
          'V<sub>ref</sub>/R<sub>T</sub> and the error-amplifier current '
          'I<sub>EA</sub>, up to V<sub>ref</sub>&nbsp;=&nbsp;1.5&nbsp;V, then '
          'adds a fixed idle time:'))
    add(eq(r'\frac{T_{sw}}{2}=\frac{C_{T}V_{ref}}'
           r'{\frac{V_{ref}}{R_{T}}+I_{EA}}+T_{idle}', key='Tsw'))
    add(p('<b>I<sub>EA</sub> is the only control input in the converter.</b> More '
          'current means a higher frequency, which means less power. '
          'Everything the control loop does, it does through this one term.'))
    add(p('C<sub>T</sub> is chosen first because it sets the <i>span</i>, and '
          'R<sub>T</sub> after it because it sets the <i>floor</i>:'))
    add(eq(r'C_{T,max}=\frac{I_{EA,max}}{2V_{ref}}\cdot'
           r'\frac{(1-2T_{idle}f_{sw,max})(1-2T_{idle}f_{sw,min})}'
           r'{f_{sw,max}-f_{sw,min}}\,,\qquad '
           r'C_{T,min}=\frac{1}{R_{T,max}}'
           r'\left(\frac{1}{2f_{sw,min}}-T_{idle}\right)', key='CT'))
    add(eq(r'R_{T,ceil}=\frac{1}{C_{T}}'
           r'\left(\frac{1}{2f_{sw,min}}-T_{idle}\right)', key='RTceil'))
    add(p('with f<sub>sw,min</sub> set to f<sub>o</sub> &mdash; the frequency '
          'floor of the whole design, for the reason in Section&nbsp;'
          + SR('Two divergences that cancel') + '. Here that window is '
            '%(CTmin).0f to %(CTmax).0f&nbsp;pF, the datasheet allows 270 to '
            '1000&nbsp;pF, and the part is taken from the middle of the '
            'overlap rather than from either edge: <b>C<sub>T</sub> = '
            '%(CT).0f&nbsp;pF</b>, C0G. Then R<sub>T,ceil</sub> = '
            '%(RTceil).2f&nbsp;k&Omega; gives <b>R<sub>T</sub> = '
            '%(RT).0f&nbsp;k&Omega;</b>.'
          % dict(V, CTmin=A.SH['C.T_min'], CTmax=A.SH['C.T_max'],
                 RTceil=A.SH['R.T_ceil'] / 1e3)))
    add(note('<b>R<sub>T,ceil</sub> is a maximum, not a minimum</b>, '
             'whatever the name suggests. f<sub>Min</sub> = '
             '1/[2(C<sub>T</sub>R<sub>T</sub>+T<sub>idle</sub>)] '
             '<i>falls</i> as R<sub>T</sub> grows. Round this number up and '
             'the VCO clamp drops below f<sub>o</sub>, leaving only the '
             'anti-capacitive protection between the converter and the '
             'capacitive region. Round it <b>down</b>.'))
    add(p('The three frequencies the selected pair actually produce are'))
    add(eq(r'f_{Min}=\frac{1}{2(C_{T}R_{T}+T_{idle})}\,,\qquad '
           r'f_{Max}=\frac{1}{2\left(\frac{C_{T}}'
           r'{\frac{I_{EA,max}}{V_{ref}}+\frac{1}{R_{T}}}+T_{idle}\right)}', key='fMinMax'))
    add(p('Putting the selected pair into the first of those, with '
          'T<sub>idle</sub>&nbsp;=&nbsp;%(Tidle).0f&nbsp;ns: '
          'f<sub>Min</sub>&nbsp;=&nbsp;1/[2(%(CT).0f&nbsp;pF&times;%(RT).0f&nbsp;k&Omega; '
          '+ %(Ts).2f&nbsp;&micro;s)] &nbsp;=&nbsp; 1/(2&times;%(tot).3f&nbsp;&micro;s) '
          '&nbsp;=&nbsp; <b>%(fMin).2f&nbsp;kHz</b>, which is what has to '
          'clear f<sub>o</sub>.'
          % dict(V, Ts=V['Tidle'] / 1e3,
                 tot=V['CT'] * 1e-12 * V['RT'] * 1e3 * 1e6
                 + V['Tidle'] / 1e3)))
    add(tbl('Oscillator: what the two parts produce, and the limits each '
            'result has to clear.',
            [['Quantity', 'Value', 'Limit', 'Margin'],
             ['f<sub>Min</sub>', '%(fMin).1f kHz' % V,
              'above f<sub>o</sub> = %(fo).1f kHz' % V,
              '%(kfloor).3f' % V],
             ['f<sub>Max</sub>', '%(fMax).1f kHz' % V,
              'above f<sub>sw,max</sub> = %(fswmaxop).1f kHz' % V,
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
            widths=[CW * 0.18, CW * 0.20, CW * 0.44, CW * 0.18]))
    add(note('<b>T<sub>idle</sub> is the weakest number in this chapter.</b> '
             'The draft datasheet gives 700&nbsp;ns in the text and a table '
             'that back-solves to 250&nbsp;ns; this design is worked at '
             '%(Tidle).0f&nbsp;ns. At 700&nbsp;ns the same R<sub>T</sub> and '
             'C<sub>T</sub> put f<sub>Min</sub> essentially on top of '
             'f<sub>o</sub> and the floor margin disappears. <b>It is not a '
             'precision question, it is whether the two clamps still bracket '
             'the operating range</b>, and it is the first thing to measure '
             'on hardware.' % V))

    add(h2('The current-sense resistor, which sets three things at once'))
    add(p('R<sub>CS</sub> is asked for by two conditions and the smaller one '
          'wins:'))
    add(eq(r'R_{CS,max1}=\frac{16.8\,\Omega\!\cdot\!\mathrm{W}}{P_{in}}'
           r'\qquad\qquad '
           r'R_{CS,max2}=\frac{0.55\,\mathrm{V}}{I_{Lr,pk}}', key='RCS'))
    add(p('The first is the maximum-power law of Section&nbsp;'
          + SR('The feedback pin is a power command')
          + '; the second is the OCP1 trip point. Opened out, equation&nbsp;'
          + ER('RCS') + ' is two divisions &mdash; 16.8/P<sub>in</sub> and '
            '0.55/I<sub>Lr,pk</sub> &mdash; and they give '
            '%(a).2f and %(b).2f&nbsp;m&Omega;, so the power law is the limiting one. '
            'Dissipation then fixes how many resistors that has to be split '
            'over. At the worst switching cycle that is %(P).2f&nbsp;W, so '
            '<b>%(N).0f in parallel</b>; %(R1).0f&nbsp;m&Omega; each gives '
            '<b>R<sub>CS</sub> = %(RCS).1f&nbsp;m&Omega;</b>.'
          % dict(V, a=A.SH['R.CS1'], b=A.SH['R.CS2'],
                 P=A.SH['P.RCS_pk'], N=A.SH['N.RCS'],
                 R1=A.SH['R.CS_single'])))
    add(note('<b>The denominator of R<sub>CS,max2</sub> is the composite tank '
             'peak, not the reflected load current.</b> R<sub>CS</sub> sits '
             'in the bridge return, so it carries the magnetising component '
             'too. Using I<sub>trafo,pk</sub> = %(Itr).2f&nbsp;A instead of '
             'I<sub>Lr,pk</sub> = %(Icomp).2f&nbsp;A loosens the limit by '
             'about 12&nbsp;%% and the over-current protection with it.' % V))
    add(tbl('What the selected R<sub>CS</sub> then fixes.',
            [['Result', 'Value', 'Against'],
             ['Maximum input power', '%(P).1f W'
              % dict(P=A.SH['P.in_max_act']),
              'P<sub>in</sub> = %(Pin).1f W' % V],
             ['OCP1 trip', '%(I).2f A' % dict(I=A.SH['I.OCP1']),
              'composite peak %(Icomp).2f A, margin %(kOCP).3f' % V],
             ['OCP2 trip', '%(I).2f A' % dict(I=A.SH['I.OCP2']),
              'immediate stop, 50 &micro;s, restart at f<sub>SU</sub>'],
             ['Sense dissipation', '%(P).2f W total, %(Pe).3f W each'
              % dict(P=A.SH['P.RCS_pk'], Pe=A.SH['P.RCS_each_pk']),
              '1 W parts, margin %(k).3f' % dict(k=A.SH['k.NRCS'])]],
            widths=[CW * 0.26, CW * 0.26, CW * 0.48]))

    add(h2('Burst mode: one resistor, read once at power-up'))
    add(eq(r'R_{BM}=16.7\,\frac{\mathrm{k}\Omega}{\mathrm{V}^{2}}'
           r'\,R_{CS}\,P_{in,BM}\,,\qquad '
           r'V_{BM,eq}=\frac{R_{BM}}{100\,\mathrm{k}\Omega}+0.5\,\mathrm{V}', key='RBM'))
    add(p('Entering burst at %(PinBM).0f&nbsp;W of input power &mdash; about '
          '%(rBM).0f&nbsp;%% of rated &mdash; asks for %(calc).2f&nbsp;'
          'k&Omega;, so <b>R<sub>BM</sub> = %(RBM).0f&nbsp;k&Omega;</b> and '
          'the equivalent threshold on the FB pin is %(V).3f&nbsp;V. The '
          'valid range is 15 to 140&nbsp;k&Omega;. Tie the pin to ground and '
          'burst mode is off altogether; deep burst stays active either way.'
          % dict(V, rBM=100 * A.SH['r.BM'], calc=A.SH['R.BM'],
                 V=A.SH['V.BM_eq'])))
    add(note('This threshold and the feedback ripple have to be checked '
             'against each other, or the converter chatters in and out of '
             'burst once per half line cycle &mdash; Section&nbsp;'
             + SR('Feedback ripple against the burst threshold') + '.'))

    add(h2('Brown-out and bridge configuration: the CFG pin'))
    add(p('One resistor does two unrelated jobs, and both are read once at '
          'power-up:'))
    add(eq(r'V_{BO,pk}=R_{CFG}\times 4\,\frac{\mathrm{V}}{\mathrm{k}\Omega}'
           r'\,,\qquad V_{BO,rms}=\frac{V_{BO,pk}}{\sqrt{2}}', key='VBO'))
    add(p('The brown-out threshold is compared against the <i>peak</i> of the '
          'mains, so it has to be converted before it is compared with an rms '
          'specification &mdash; a &radic;2 that is easy to drop. Asking for '
          'brown-out just below the minimum line gives R<sub>CFG,max</sub> = '
          '%(max).2f&nbsp;k&Omega;; <b>this is a maximum, so it rounds '
          'down</b>, to <b>%(RCFG).0f&nbsp;k&Omega;</b>, and '
          'V<sub>BO</sub> = %(VBO).2f&nbsp;V<sub>rms</sub> against a '
          '%(Vacmin).0f&nbsp;Vac minimum &mdash; margin %(k).3f. Rounding up '
          'instead would stop the converter starting at low line.'
          % dict(V, max=A.SH['R.CFG_max'] / 1e3, k=A.SH['k.BO'])))
    add(tbl('What R<sub>CFG</sub> and LOUT2 select together. The 235 and '
            '245 V thresholds are fixed inside the IC and cannot be moved.',
            [['R<sub>CFG</sub>', 'LOUT2', 'Configuration'],
             ['15 k&Omega;', 'open',
              'morphing, fixed brown-out (60 V / 70 V peak)'],
             ['15 to 47 k&Omega;', 'open',
              '<b>morphing, adjustable brown-out &mdash; this design</b>'],
             ['47 to 100 k&Omega;', 'open', 'fixed full bridge'],
             ['15 k&Omega;', 'to GND',
              'fixed half bridge, split C<sub>r</sub>, fixed brown-out'],
             ['15 to 100 k&Omega;', 'to GND',
              'fixed half bridge, split C<sub>r</sub>, adjustable brown-out']],
            widths=[CW * 0.20, CW * 0.14, CW * 0.66]))
    add(note('<b>For a universal-input design there is only one window.</b> '
             'The datasheet floor is 15&nbsp;k&Omega; and brown-out at the '
             'minimum line is the ceiling at %(max).1f&nbsp;k&Omega;, so the '
             '47&nbsp;k&Omega; morphing limit never comes into play. And '
             'hang nothing on LOUT2. The pin-strap drives '
             '300&nbsp;&micro;A into it and needs 2.5&nbsp;V, so any '
             'pull-down under about 8&nbsp;k&Omega; reads as a request for a '
             'fixed half bridge.'
             % dict(max=A.SH['R.CFG_max'] / 1e3)))

    add(h2('Output sensing and over-voltage: the ZCD divider'))
    add(p('The auxiliary winding is divided down to the ZCD pin, and the '
          'divider ratio alone sets both over-voltage thresholds &mdash; the '
          'absolute resistor values only set the bias current:'))
    add(eq(r'R_{ZCD,L}=\frac{2.3\,\mathrm{V}}{I_{bias}}\,,\qquad '
           r'R_{ZCD,H}=R_{ZCD,L}\left('
           r'\frac{n_{aux}}{n_{sec}}\frac{V_{OVP1,out}}{2.3\,\mathrm{V}}'
           r'-1\right)', key='RZCD'))
    add(eq(r'V_{OVP1}=\frac{2.3\,\mathrm{V}}{n_{aux}/n_{sec}}'
           r'\left(\frac{R_{ZCD,H}}{R_{ZCD,L}}+1\right)\,,\qquad '
           r'V_{OVP2}=\frac{2.5}{2.3}\,V_{OVP1}', key='OVP'))
    add(p('Aiming OVP1 %(pc).0f&nbsp;%% above the output gives '
          '%(t).2f&nbsp;V as a target. With '
          'n<sub>aux</sub>/n<sub>sec</sub> = %(naux).1f the calculated pair '
          'is %(rl).2f / %(rh).1f&nbsp;k&Omega;. The parts fitted are '
          '<b>%(RZL).0f&nbsp;k&Omega; and %(RZH).0f&nbsp;k&Omega;</b>. The '
          'upper one is deliberately the <i>next E24 value above</i> the '
          'calculation, so OVP1 lands clear of the ripple crest rather than '
          'on it. The result is OVP1 %(OVP1).2f&nbsp;V and OVP2 '
          '%(OVP2).2f&nbsp;V, and start-up hands over to the loop at '
          '%(su).2f&nbsp;V of output.'
          % dict(V, pc=100 * (A.SH['V.OVP1_out'] / V['Vout'] - 1),
                 t=A.SH['V.OVP1_out'], naux=A.SH['n.aux'],
                 rl=A.SH['R.ZCD_L'], rh=A.SH['R.ZCD_H'],
                 su=A.SH['V.out_SUend'])))
    add(note('<b>Two ways to get this wrong, and both stop the converter '
             'completely.</b> Swapping the two resistors inverts the ratio and OVP1 '
             'trips at well under a volt of output, so the converter never '
             'starts. And the winding polarity must make ZCD <i>positive</i> '
             'when the low side of leg&nbsp;1 is on; reversed, the bridge hard '
             'switches from the first pulse.'))
    add(note('<b>The turns-ratio ceiling in the datasheet does not apply '
             'here.</b> It asks that the rectified auxiliary voltage stay '
             'under the V<sub>CC</sub> rating at OVP2, which is a question '
             'only when that winding supplies V<sub>CC</sub>. In this design '
             'V<sub>CC</sub> comes from a housekeeping rail and the winding '
             'senses only, so its voltage is free &mdash; %(va).1f&nbsp;V '
             'nominal, %(vo).1f&nbsp;V at OVP2 &mdash; and the only remaining '
             'constraint is that the turns come out whole. Carrying that check '
             'over from a self-supplied design reports a failure that is not '
             'one.' % dict(va=A.SH['V.aux'],
                           vo=A.SH['n.aux'] * A.SH['V.OVP2_act'])))

    add(h2('HVSU and V<sub>CC</sub>'))
    ext(bullets([
        '<b>HVSU connects ahead of the input bridge</b>, on the ac side, '
        'through one 1000&nbsp;V diode per line. Behind the bridge both the '
        'X-capacitor discharge and the brown-out detection stop working, '
        'because neither can see the mains disappear.',
        'The V<sub>CC</sub> capacitor has to hold the IC from '
        'V<sub>CCon</sub> = 17&nbsp;V down to V<sub>CCoff</sub> = '
        '8&nbsp;V for as long as it takes the supply to take over. The '
        'start-up unit stops %s&nbsp;ms after V<sub>CCon</sub> is reached, '
        'whether or not the supply has taken over by then.' % '120',
        'Where a linear regulator feeds V<sub>CC</sub>, put a diode between '
        'its output and the pin so the start-up charging current cannot be '
        'pushed back into it.',
        'A 100&nbsp;nF bypass sits at the pin itself.']))

    # =============================================================== 7
    add(h2('Controller pin rules'))
    add(p('These follow from the datasheet and each one causes immediate '
          'misbehaviour if broken.'))
    add(tbl('Pin rules that must not be broken.',
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
            widths=[CW * 0.16, CW * 0.84]))

    add(h2('Protections, and where each threshold is set'))
    add(p('Every one of these is a design constant fixed by a resistor this '
          'note has already chosen, so a change made for one reason moves a '
          'threshold set for another. The table is here because the '
          'thresholds are otherwise spread over five sections.'))
    add(tbl('Protections and the component that sets each one.',
            [['Protection', 'Set by', 'This design'],
             ['Brown-out, on the rectified mains',
              'R<sub>CFG</sub>, read at power-up',
              'V<sub>BO</sub> %(VBO).1f V, clear of the %(Vacmin).0f Vac '
              'minimum by %(kBO).3f' % dict(V, kBO=A.SH['k.BO'])],
             ['Cycle-by-cycle over-current, OCP1',
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
              'internal; it watches the ZCD edge against the gate',
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
            widths=[CW * 0.24, CW * 0.30, CW * 0.46]))
    add(note('<b>Two of these share one resistor.</b> R<sub>CS</sub> sets '
             'the over-current thresholds <i>and</i> the maximum-power law, '
             'because the controller reads both from the same pin. Changing '
             'it to fix a power limit moves OCP1, and the other way round. '
             'That is also why the pin tolerates no filter.'))

    add(h2('System design rules'))
    add(p('The same material as a checklist, in the order a design meets '
          'it. Every line is argued for somewhere above; collected here so a '
          'reviewer can run down the list without re-reading the argument.'))
    ext(bullets([
        '<b>Design the tank at the real ends of the equivalent range.</b> '
        'With morphing that is %(Veqlo).1f and %(Veqhi).1f&nbsp;Vac, not '
        '2&times;%(Vacmin).0f and %(Vacmax).0f. Looking only at the mains '
        'range misses both worst corners.' % V,
        '<b>Expect &lambda; near 0.5.</b> The 5-to-10 inductance ratio of a '
        'two-stage LLC will not start at low line.',
        '<b>Keep the oscillator floor above f<sub>o</sub></b>, and treat the '
        'anti-capacitive protection as the last line, not the first.',
        '<b>Size the output bank from both conditions</b> &mdash; ripple and '
        'hold-up &mdash; take the larger, and then check the rms ripple '
        'current separately. The capacitance and the current are different '
        'questions.',
        '<b>Put the voltage-loop crossover in the tens of hertz</b>, then deal '
        'with the feedback ripple that survives by moving R<sub>BM</sub>, not '
        'by speeding the loop up.',
        '<b>Measure both morphing edges</b>, at full load and at light load. '
        'The half-bridge edge is the worst case for gain and ZVS, the '
        'full-bridge edge for switching frequency.',
        '<b>Check the turns ratio as a reflected voltage</b>, '
        'n&thinsp;V<sub>o,eff</sub>, never as a bare ratio &mdash; that is '
        'what keeps n and n<sub>T</sub> from being interchanged.',
        '<b>Judge the over-current margin on the composite tank peak</b>, not '
        'on the reflected load current.',
        '<b>Include the 2f<sub>l</sub> component</b> in the output capacitor '
        'ripple current, and judge a centre tap at the output node rather '
        'than per winding.',
        '<b>Carry the conduction ratio &radic;d into the secondary rms.</b> '
        'Dropping it overstates the rms by about 12&nbsp;%% here, and the '
        'loss &mdash; which goes as the square &mdash; by about '
        '26&nbsp;%%.' % {},
        '<b>Decide how L<sub>r</sub> is built before specifying the '
        'transformer</b>, and put open-circuit and short-circuit inductance '
        'on the drawing alongside the turns.',
        '<b>Use capacitor ESR at the switching frequency</b>, not the '
        '120&nbsp;Hz tan&thinsp;&delta;.',
        '<b>Never round L<sub>m</sub> up.</b> It lowers &lambda; and takes '
        'the ZVS margin with it.',
        '<b>Verify ZVS by sweeping the selected tank</b>, not with the closed '
        'form &mdash; and if the closed form is used anyway, feed it '
        '&lambda;<sub>act</sub> and the Q of the moment, and know that its '
        'error has no fixed sign.',
        '<b>Record calculated and selected values separately</b>, and make '
        'every downstream check read the selected one. A sheet that quietly '
        'reads the calculated value reports margins the hardware does not '
        'have.']))

    add(h2('What to measure first on hardware'))
    add(p('In order. The first four decide whether the design is sound at '
          'all; the rest confirm margins that are computed but never yet '
          'seen.'))
    ext(bullets([
        '<b>f<sub>sw</sub>(&theta;) over a line half cycle.</b> This settles '
        'T<sub>idle</sub>, and with it both oscillator clamps &mdash; the '
        'thinnest margin in the design. Everything else in the controller '
        'network hangs off it.',
        '<b>Cold start into the full output bank.</b> A %(Cout).1f&nbsp;mF '
        'bank is a far heavier start-up load than a conventional design '
        'presents, and the start-up window is finite. This risk is new to '
        'this architecture, so there is no earlier design to compare with.' % V,
        '<b>ZVS at the half-bridge morphing edge</b> (245&nbsp;'
        'V<sub>pk</sub>, full load), on the gate and mid-point waveforms. '
        'The calculation says %(cTzc).0f&nbsp;ns against %(tD).0f&nbsp;ns; '
        'confirm it is not hard switching, and that the adaptive dead time '
        'actually settles where it is assumed to. <b>Then measure the worst '
        'point of the sweep as well</b> &mdash; %(zLoad).0f&nbsp;%% load at '
        'the %(zVin).1f&nbsp;Vac equivalent corner, %(zTzc).0f&nbsp;ns &mdash; '
        'because that, not the design corner, is the figure this design is '
        'held to.' % dict(V, **ZVS_WORST),
        '<b>Switching frequency at the full-bridge morphing edge</b> '
        '(235&nbsp;V<sub>pk</sub>, full load). Calculated '
        '%(fswB).1f&nbsp;kHz; check it does not run into the VCO ceiling and '
        'get power-limited.' % V,
        '<b>Input current and THD at %(Vacmin).0f&nbsp;Vac, full load</b>, to '
        'put a number on the zero-crossing dead zone.' % V,
        '<b>Output ripple against what the load actually tolerates.</b> The '
        'bank is sized from a specification; this is where the specification '
        'is tested.',
        '<b>Ripple current and temperature rise in the output bank</b> '
        '&mdash; %(ICout).2f&nbsp;A rms calculated, %(Icout1).2f&nbsp;A per '
        'capacitor.' % V,
        '<b>Device temperatures, primary and secondary.</b> This is where the '
        'accepted loss-budget shortfall is decided: measure it in <b>half-bridge '
        'morphing</b>, above 245&nbsp;V<sub>pk</sub>, because in full bridge '
        'the standing device is switching and dissipates far less.',
        '<b>Feedback ripple against the burst threshold</b> at light load.',
        '<b>An ac dropout at the worst line phase</b> &mdash; cut the mains '
        'at the trough of the ripple and confirm the output is still above '
        '%(Vomin).0f&nbsp;V after %(Thold).0f&nbsp;ms.' % V,
        '<b>A step across the morphing band</b>, both directions, on a '
        'programmable source. A ramp gives the loop time to follow and hides '
        'the transition.']))

    # =============================================================== 8
    add(h1('List of symbols'))
    add(p('The symbols used in this note. The controller&rsquo;s own '
          'electrical parameters are in its datasheet.'))
    _SYM = [
        ('A<sub>e</sub>, A<sub>min</sub>', 'core effective area, and its narrowest section'),
        ('A<sub>L</sub>', 'inductance factor of the gapped core (inductance per turn squared)'),
        ('A<sub>N</sub>', 'winding window area of the coil former'),
        ('B<sub>pk</sub>, B<sub>max</sub>', 'peak flux density, and the ceiling it is designed to'),
        ('C<sub>r</sub>, L<sub>r</sub>, L<sub>m</sub>', 'resonant capacitor, series inductance and magnetising inductance of the tank model'),
        ('C<sub>out</sub>, C<sub>in</sub>', 'output capacitor bank, input film capacitor'),
        ('C<sub>o(tr)</sub>', 'time-related output capacitance of a MOSFET (charge equivalent)'),
        ('C<sub>T</sub>, R<sub>T</sub>', 'oscillator timing capacitor and resistor'),
        ('C<sub>Fo</sub>, C<sub>F</sub>, R<sub>F</sub>, C<sub>fx</sub>', 'compensator parts: the two capacitors and the resistor of the TL431 network, and the FB-pin capacitor'),
        ('CTR<sub>s</sub>, CTR<sub>m</sub>', 'optocoupler current transfer ratio at the steady-state and at the maximum LED current'),
        ('D<sub>3</sub>', 'third harmonic on the input current, as a fraction of the fundamental'),
        ('EA<sub>o</sub>', 'gain constant of the compensator, in rad/s'),
        ('d', 'conduction ratio f<sub>sw</sub>/f<sub>r</sub> of the secondary, 1 above resonance'),
        ('f<sub>l</sub>', 'line frequency; f<sub>l,min</sub> its lowest value'),
        ('f<sub>r</sub>, f<sub>o</sub>', 'series resonance, and the lower resonance with L<sub>m</sub> included'),
        ('f<sub>sw</sub>, f<sub>n</sub>', 'switching frequency, and the same normalised to f<sub>r</sub>'),
        ('f<sub>sw,max</sub>', 'the specified maximum switching frequency, an input to &lambda;'),
        ('f<sub>Min</sub>, f<sub>Max</sub>', 'oscillator floor and ceiling set by R<sub>T</sub>, C<sub>T</sub> and T<sub>idle</sub>'),
        ('f<sub>cross</sub>, &Phi;<sub>M</sub>, GM', 'loop crossover frequency, phase margin, gain margin'),
        ('f<sub>z</sub>, f<sub>p</sub>, f<sub>px</sub>, f<sub>180</sub>', 'compensator zero, pole and high-frequency pole; the frequency where arg T = &minus;180&deg;'),
        ('G<sub>o</sub>', 'gain of the plant integrator, in rad/s'),
        ('&Gamma;<sub>v</sub>, &alpha;<sub>v</sub>', 'input-voltage margin factor and weighting constant of the K-factor method'),
        ('I<sub>Lr,pk</sub>', 'composite tank current peak: reflected load plus magnetising'),
        ('I<sub>trafo,pk</sub>', 'peak of the reflected load current alone'),
        ('i<sub>Lm</sub>, i<sub>&mu;</sub>', 'magnetising current of the tank model, and of the physical transformer'),
        ('I<sub>sec,pk</sub>', 'peak secondary current per rectifier leg'),
        ('I<sub>eq</sub>, I<sub>sat</sub>', 'open-circuit current that reproduces the operating flux; the DC-overlap test current'),
        ('I<sub>OCP1</sub>, I<sub>OCP2</sub>', 'over-current thresholds set by R<sub>CS</sub>'),
        ('J', 'current density the copper is sized to'),
        ('k', 'a verification margin, what the design has over what it needs'),
        ('k<sub>T</sub>', 'R<sub>DS(on)</sub> multiplier from 25 &deg;C to T<sub>j,max</sub>'),
        ('K<sub>v</sub>', 'K factor of the Type II compensator'),
        ('L<sub>open</sub>, L<sub>short</sub>', 'primary inductance with the secondaries open, and shorted'),
        ('L<sub>&mu;</sub>, L<sub>L1</sub>, L<sub>L2</sub>', 'physical magnetising inductance and the two leakage inductances'),
        ('&lambda;, m', 'L<sub>r</sub>/L<sub>m</sub>, and (L<sub>r</sub>+L<sub>m</sub>)/L<sub>r</sub> = 1 + 1/&lambda;'),
        ('&lambda;<sub>act</sub>', 'the &lambda; of the selected parts'),
        ('M', 'tank gain, n V<sub>o,eff</sub> over the drive'),
        ('M<sub>&infin;</sub>', 'no-load gain asymptote 1/(1+&lambda;)'),
        ('n, n<sub>T</sub>', 'equivalent-model turns ratio, and the physical (wound) turns ratio'),
        ('N<sub>p</sub>, N<sub>s</sub>, N<sub>x</sub>', 'primary turns, secondary turns per winding, number of units in the assembly'),
        ('N<sub>rect</sub>', 'devices in the secondary conduction path: 1 centre tap, 2 full bridge'),
        ('P<sub>in</sub>, P<sub>in,LLC</sub>, P<sub>out</sub>', 'input power, power into the tank, output power'),
        ('Q, Q<sub>pk</sub>, Q<sub>ZVS</sub>', 'quality factor Z<sub>0</sub>/R<sub>ac</sub>; its value at the line peak; the cap the ZVS condition puts on it'),
        ('R<sub>ac</sub>', 'the rectifier and load as one resistance at the fundamental'),
        ('R<sub>BM</sub>, R<sub>CFG</sub>, R<sub>CS</sub>', 'burst-mode, configuration and current-sense resistors'),
        ('R<sub>I</sub>, R<sub>O</sub>', 'output divider of the compensator'),
        ('R<sub>B</sub>, R<sub>P</sub>, R<sub>FB</sub>', 'optocoupler LED resistor, TL431 bias resistor, and the pull-up inside the FB pin'),
        ('R<sub>ZCD,H</sub>, R<sub>ZCD,L</sub>', 'the ZCD divider'),
        ('t<sub>D</sub>, T<sub>ZC</sub>', 'bridge dead time, and the time the tank current takes to reach zero after the transition'),
        ('T<sub>hold</sub>, V<sub>o,min</sub>', 'hold-up time, and the lowest output allowed at its end'),
        ('T<sub>idle</sub>', 'oscillator idle time'),
        ('&theta;', 'line phase angle'),
        ('V<sub>ac,eq</sub>', 'equivalent input voltage the tank sees after morphing'),
        ('V<sub>o,eff</sub>', 'V<sub>out</sub> + N<sub>rect</sub> V<sub>f</sub>'),
        ('V<sub>refl</sub>', 'reflected output voltage n V<sub>o,eff</sub>'),
        ('V<sub>OVP1</sub>, V<sub>OVP2</sub>', 'the two over-voltage thresholds'),
        ('V<sub>BO</sub>', 'brown-out threshold'),
        ('&Delta;v, &Delta;v<sub>pp</sub>', 'allowed and achieved 2f<sub>l</sub> output ripple'),
        ('Z<sub>0</sub>', 'characteristic impedance &radic;(L<sub>r</sub>/C<sub>r</sub>)'),
        ('&delta;', 'skin depth in copper at f<sub>r</sub>'),
        ('V<sub>FB</sub>', 'feedback voltage above its 0.5 V offset at rated power'),
        ('V<sub>R</sub>, V<sub>Z</sub>, V<sub>Fo</sub>', 'TL431 reference, the regulated rail that feeds the LED, and the LED forward drop'),
        ('&Delta;V<sub>loop</sub>, &Delta;V<sub>FB</sub>', '2f<sub>l</sub> output ripple seen by the loop, and the ripple it leaves on the FB pin'),
        ('&eta;<sub>HB</sub>', 'assumed efficiency of the LLC stage'),
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
        'ON Semiconductor / Fairchild, <i>Half-bridge LLC resonant converter '
        'design using FSFR-series Fairchild power switch</i>, AN-4151.',
        'Monolithic Power Systems, <i>Understanding LLC operation</i>, '
        'part&nbsp;2.',
        'Toshiba Electronic Devices &amp; Storage, <i>Power factor '
        'correction (PFC) circuits</i>, application note.',
        'ROHM Semiconductor, TechWeb, <i>LLC operating regions</i> '
        '(region framing of Figure&nbsp;' + FR('f04_three_regions') + ').',
        'W. Wenbo et al., <i>A single-stage 1.65 kW ac-dc LLC converter</i>, '
        'IEEE ECCE.',
        'onsemi, <i>The TL431 in the control of switching power supplies</i>, '
        'TND381-D (compensator design with a TL431 and an optocoupler).']))

    # =============================================================== 10
    add(h1('Errata and open items'))
    add(p('Everything in this chapter is something the note works around '
          'rather than something it solves. It is last because none of it is '
          'needed to follow the design, and first to be re-read before a '
          'production release &mdash; most of it is a question that only the '
          'released datasheet or a prototype can close.'))

    add(h2('Datasheet: the draft is not self-consistent'))
    add(tbl('Points where the draft datasheet contradicts itself or leaves a '
            'value open. Every one of them must be re-checked against the '
            'released document.',
            [['Item', 'What the draft says', 'What is used here, and why'],
             ['Oscillator idle time T<sub>idle</sub>',
              'Section 5.3.2 says 700 ns; Table 5 back-solves to about 250 ns '
              'from the frequency expressions',
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
              'the pin that is strapped and held high in half bridge']],
            widths=[CW * 0.22, CW * 0.40, CW * 0.38]))

    add(h2('Traps in the obvious way of building a design sheet'))
    add(p('These are not datasheet problems. They are places where the '
          'obvious way to set a design sheet up gives an answer that is wrong '
          'in a way nothing flags, so they are worth stating as traps rather '
          'than as corrections to any particular tool.'))
    add(tbl('Traps that produce a plausible wrong number.',
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
              'of over a hundred in one case &mdash; and L<sub>m</sub> with '
              'it'],
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
              'About 12 % under-rated &mdash; the switch carries the '
              '<i>composite</i> tank current'],
             ['Loss and thermal resistance',
              'computing loss from the 25 &deg;C R<sub>DS(on)</sub> and then '
              'asking for a heatsink that holds 125 &deg;C',
              'The required thermal resistance comes out only about half as '
              'demanding as it really is'],
             ['ZVS check',
              'the closed-form shortcut, at the design Q and with the design '
              '&lambda;',
              'Error of either sign; on this tank %(pc).0f %% conservative, '
              'on another about 23 %% optimistic. Optimistic is the '
              'dangerous direction'
              % dict(pc=abs(V['TzcCFpc']))],
             ['Selected versus calculated',
              'a check that reads the calculated value while the board '
              'carries the selected one',
              'Every downstream margin is reported for a design that was not '
              'built']],
            widths=[CW * 0.20, CW * 0.38, CW * 0.42]))

    add(h2('Constants used here without a derivation'))
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
        'The <b>16.8 &Omega;&middot;W</b> maximum-power constant is '
        'consistent with the feedback span and the multiplier gains quoted '
        'in the datasheet &mdash; 2.8&nbsp;V / 0.167 = 16.8 &mdash; so it is '
        'derived rather than assumed, and is listed here only because the '
        'gains themselves are draft values.']))

    add(h2('Open items in this design'))
    add(tbl('What is not settled, and what would settle it.',
            [['Item', 'State', 'What closes it'],
             ['T<sub>idle</sub>', 'two candidate values, 250 and 700 ns',
              'Measure f<sub>sw</sub>(&theta;) on the first board'],
             ['Primary conduction loss',
              '%(kPloss).3f against the budget &mdash; <b>not met, and '
              'accepted</b>' % V,
              'No single 600 V device meets a 3 W budget in the standing '
              'position. Whether it needs a heatsink is a thermal '
              'measurement, not a calculation'],
             ['Secondary loss budget',
              '%(kPSR).3f &mdash; essentially exhausted' % V,
              'One more device in parallel per leg recovers it; the decision '
              'waits on the measured temperature'],
             ['Transformer inductance tolerance',
              'the tank tolerates a %(Ldrop).1f %% fall in open-circuit '
              'inductance and the usual specification asks for '
              '&plusmn;10 %%' % V,
              'Either tighten the low side with the supplier, or lower '
              'R<sub>T</sub> to lift f<sub>Min</sub> first. <b>Before the '
              'transformer is ordered</b>'],
             ['Output bank volume and height',
              '%(Cout).1f mF, %(nC).0f parts' % V,
              'A mechanical question, not an electrical one, and it can send '
              'the whole architecture back to the output voltage'],
             ['Standby power', 'burst entry assumed at %(PinBM).0f W' % V,
              'Measure, then trade R<sub>BM</sub> against the feedback '
              'ripple'],
             ['Efficiency assumption',
              '&eta;<sub>HB</sub> = %(etaHB).0f %% assumed' % V,
              'Optimistic. Taking 95 % instead moves R<sub>CS</sub> and '
              'R<sub>ac</sub> by about 3 %, so nothing downstream is '
              'sensitive &mdash; but it should be replaced by a measurement']],
            widths=[CW * 0.22, CW * 0.34, CW * 0.44]))
    add(note('<b>Every cross-check here is a consistency check, not a '
             'correctness check.</b> The numbers agree across three '
             'independent implementations, which means the three implement '
             'the same equations &mdash; not that the equations describe the '
             'hardware. That is '
             'what the measurement list in Section&nbsp;'
             + SR('What to measure first on hardware') + ' is for.'))

    return s


ZVS_WORST = {}          # filled by _zvs_grid, read by the text beside it


def _zvs_grid(A, head=('Load', '%.1f Vac eq.')):
    """T_ZC over load and equivalent input, recomputed - never transcribed

    head lets the Korean edition label the same grid in its own language;
    the numbers are computed here either way, never transcribed.
    """
    import l6790
    cols = (A.R['Vin_min'], 180., 225., 264., 332.34)
    rows = [[head[0]] + [head[1] % c for c in cols]]
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
                     same=abs(worst[0] - corner) < 0.5)
    return rows
