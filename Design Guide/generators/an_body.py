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
    h1, h2, p, eq, fig, tbl, note = A.h1, A.h2, A.p, A.eq, A.fig, A.tbl, A.note
    bullets, V, CW = A.bullets, A.V, A.CW
    FR, TR, SR = A.figref, A.tblref, A.secref
    ER = A.eqref
    s = []
    add = s.append
    ext = s.extend

    # =============================================================== 1
    add(h1('Introduction'))
    add(p('A conventional universal-input LLC power supply is two stages: a '
          'boost power-factor corrector that holds a 400&nbsp;V bus, and an '
          'LLC converter that steps that bus down. The capacitor between them '
          'does two jobs at once. It buffers the energy a unity-power-factor '
          'input cannot deliver smoothly, and it presents the LLC with an '
          'almost constant input, so the resonant tank only has to cover a '
          'narrow range.'))
    add(p('A <b>single-stage PFC LLC</b> deletes both the boost stage and that '
          'capacitor. The rectified mains feeds the resonant tank directly. '
          'What results is a converter whose input is a 100/120&nbsp;Hz half '
          'sine, whose gain is no longer a control variable, and whose output '
          'capacitor must absorb everything the bus capacitor used to. It is '
          'a genuinely different converter rather than an LLC with a stage '
          'removed, and most of the design habits carried over from the '
          'two-stage case are wrong here.'))
    add(p('What follows is how such a converter works, and how to design one '
          'with the STMicroelectronics <b>L6790A</b> controller. One worked '
          'design runs through it from specification to component values: '
          '<b>90 to 264&nbsp;Vac in, %(Vout).0f&nbsp;V / %(Iout).1f&nbsp;A = '
          '%(Pout).1f&nbsp;W out</b>, a low-voltage, high-current dc rail.'
          % V))
    add(note('<b>Scope.</b> Covered: the power stage, the resonant tank, the '
             'output bank, the controller network and the voltage loop. Not '
             'covered: EMI filtering, magnetics construction, layout and '
             'safety approval.'))

    # =============================================================== 2
    add(h1('The two converters this one is made of'))
    add(p('Everything that follows is easier if the two halves are separate '
          'in your head first. This section is ordinary LLC and ordinary '
          'power factor correction; a reader who has built both can skip to '
          'Section&nbsp;%s.' % SR('Why single stage, and what it costs')))

    add(h2('What an LLC converter is'))
    add(p('An LLC converter is a square-wave generator driving a resonant '
          'network that feeds a transformer and a rectifier. The switches do '
          'nothing but chop the input into a square wave of adjustable '
          'frequency &mdash; there is no duty cycle to set and no inductor '
          'current to program.'))
    add(fig('an_ref_llc',
            'An LLC half bridge: a square-wave generator, the resonant '
            'network, and a rectifier. (ON Semiconductor AN-4151.)',
            width=CW * 0.82))
    add(p('The three tank elements are named in the order they appear in '
          '&ldquo;LLC&rdquo;: the series inductance L<sub>r</sub>, the '
          'magnetising inductance L<sub>m</sub> of the transformer, and the '
          'series capacitance C<sub>r</sub>. The middle element is not an '
          'added part &mdash; it is the transformer&rsquo;s own magnetising '
          'inductance, which is why an LLC has one fewer component than the '
          'name suggests.'))
    ext(bullets([
        '<b>The square wave sets the frequency, and nothing else.</b> Output '
        'voltage is controlled by moving f<sub>sw</sub>, because the '
        'impedance of the tank &mdash; and therefore its voltage division '
        '&mdash; depends on frequency.',
        '<b>The tank current is very nearly sinusoidal.</b> That is the '
        'point: the switches turn on and off while the current is small or '
        'while it is flowing through the body diode, so switching loss '
        'largely disappears.',
        '<b>The transformer does the voltage step and the isolation</b>, and '
        'its leakage inductance can be used <i>as</i> L<sub>r</sub> rather '
        'than fought. That is the usual construction at these powers.']))

    add(h2('Why an LLC, and not something simpler'))
    add(p('An LLC is more work than a forward or a flyback and it does not '
          'regulate by duty cycle, which is the reflex every designer has. '
          'What it buys is worth the trouble at a few hundred watts and '
          'above:'))
    ext(bullets([
        '<b>Soft switching over the whole load range, on both sides.</b> The '
        'primary switches turn on at zero volts and the secondary '
        'rectifiers, below resonance, turn off at zero current. A '
        'phase-shifted full bridge loses ZVS at light load; an LLC does not, '
        'because the magnetising current that does the work is there '
        'whatever the load.',
        '<b>Frequency can be pushed up.</b> Switching loss is what caps the '
        'frequency of a hard-switched converter, and with it the size of the '
        'magnetics and the filter. Take that loss away and hundreds of kHz '
        'becomes reasonable.',
        '<b>The transformer leakage is used, not fought.</b> In a forward '
        'converter leakage is a problem to be snubbed. Here it can <i>be</i> '
        'L<sub>r</sub>, so the resonant inductor costs nothing and the '
        'snubber disappears with it.',
        '<b>No output inductor.</b> The rectifier feeds the output capacitor '
        'directly, which removes a wound component and its loss from the '
        'high-current side &mdash; the side where it hurts most.',
        '<b>Quiet.</b> Currents are sinusoidal rather than trapezoidal and '
        'the switching transitions are slow and damped, so the conducted and '
        'radiated spectrum is far smaller than a hard-switched converter of '
        'the same power.']))
    add(p('The costs are equally real and worth stating in the same breath. '
          'Regulation is by frequency, so the operating frequency moves with '
          'line and load and the magnetics have to work over that whole '
          'range. Circulating magnetising current flows whether or not the '
          'load takes power, so light-load efficiency is not the strong '
          'point. And the design does not fall out of a duty-cycle '
          'expression &mdash; it comes from the gain curve, which is what '
          'the rest of this section is about.'))

    add(h2('Why resonance buys anything'))
    add(p('In a hard-switched converter a switch turns on with the full input '
          'voltage across it, so the energy stored in its output capacitance '
          'is dumped into the channel every cycle. That loss rises with '
          'frequency, which is what caps the frequency and therefore the '
          'size of the magnetics.'))
    add(p('An LLC run <b>above its lower resonance</b> presents an inductive '
          'load to the bridge. The tank current then lags the drive, and in '
          'the dead time between the two switches that lagging current '
          'discharges the mid-point capacitance on its own. The switch turns '
          'on at zero volts. <b>That is zero-voltage switching, and it is the '
          'entire reason for the topology.</b> Section&nbsp;%s shows the '
          'mechanism and what it demands of the design.'
          % SR('ZVS and ZCS are not the same thing')))
    add(fig('an_ref_waveforms',
            'Typical waveforms. I<sub>p</sub> is the tank current and '
            'I<sub>m</sub> the magnetising current; the switch turns on while '
            'the difference between them is still flowing, which is what '
            'discharges the mid-point. (ON Semiconductor AN-4151.)',
            width=CW * 0.62))
    add(p('The two frequencies that bound this are the subject of '
          'Section&nbsp;' + SR('The two resonances')
          + ', and the operating regions they divide are in Section&nbsp;'
          + SR('The gain function and the three regions') + '.'))
    add(note('The condition is <i>inductive operation</i>, not a particular '
             'frequency. Fall low enough and the tank turns capacitive: the '
             'current leads, the dead time works against the transition '
             'instead of for it, and the bridge hard switches into a low '
             'impedance. It is the one failure mode that destroys parts '
             'rather than just heating them. <b>Where that happens is not '
             'a fixed frequency</b> &mdash; it is the peak of the gain '
             'curve, which moves with load, and Section&nbsp;'
             + SR('The two boundaries are not the same boundary')
             + ' is about exactly that.'))

    add(h2('How the circuit becomes M(f<sub>n</sub>, Q)'))
    add(p('Every gain curve in every LLC note comes from three reductions '
          'applied in order. They are worth doing once, because each one '
          'discards something and it is useful to know what.'))
    add(fig('an_ref_rac',
            'Why the rectifier and the load collapse into one resistance. '
            'The rectifier draws a square current wave and the output is '
            'stiff, so on a fundamental basis the whole of it looks '
            'resistive. (ON Semiconductor AN-4151.)', width=CW * 0.66))
    add(fig('an_ref_fha',
            'The result: one ac network. Its voltage transfer is the gain M '
            'and its damping is Q. <b>The R<sub>ac</sub> written here uses '
            'the average output power</b>, which is the only power a '
            'two-stage converter has. Put the line-peak power into the same '
            'expression instead and the result halves; Section&nbsp;'
            + SR('The resonant tank')
            + ' says why. (ON Semiconductor AN-4151.)', width=CW * 0.60))
    ext(bullets([
        '<b>Refer the secondary to the primary.</b> The ideal transformer '
        'disappears and the load resistance is multiplied by n&sup2;.',
        '<b>Replace the rectifier and the output filter by one resistor.</b> '
        'The rectifier draws a square current wave and the output is stiff, '
        'so on a fundamental basis the whole of it looks resistive.',
        '<b>Keep only the fundamental of the drive.</b> The tank is a filter '
        'centred near the switching frequency, so the harmonics of the square '
        'wave contribute little. This is <i>first harmonic approximation</i>, '
        'and it is why every LLC design ends with a simulation or a '
        'measurement rather than with the equations.']))
    add(p('What is left is one ac network, and it is a voltage divider whose '
          'ratio changes with frequency. Two numbers describe it and both are '
          'used on every page from here on:'))
    ext(bullets([
        '<b>the gain M</b> &mdash; the voltage across R<sub>ac</sub> divided '
        'by the fundamental driving it. Because C<sub>r</sub> and '
        'L<sub>r</sub> cancel at the series resonance f<sub>r</sub>, '
        '<b>M = 1 there whatever the load</b>. Below f<sub>r</sub> the '
        'network can step up (M&nbsp;&gt;&nbsp;1) and above it steps down.',
        '<b>the quality factor Q = Z<sub>0</sub>/R<sub>ac</sub></b>, with '
        'Z<sub>0</sub> = &radic;(L<sub>r</sub>/C<sub>r</sub>) the '
        'characteristic impedance of the tank. Q says how heavily the tank '
        'is loaded: <b>Q rises with output power</b>. At Q = 0 (no load) the '
        'gain curve is tall and peaked; loading it pulls the peak down and '
        'flattens the curve.']))
    add(p('Frequency is always written normalised, '
          'f<sub>n</sub> = f<sub>sw</sub>/f<sub>r</sub>, so that one family '
          'of curves serves every tank. M(f<sub>n</sub>, Q) always means the '
          'gain of the right-hand circuit above.'))

    add(h2('The two resonances'))
    add(p('Every LLC has two. When the secondary conducts, the reflected '
          'output voltage clamps L<sub>m</sub> and it drops out of the '
          'circuit, leaving the series resonance'))
    add(eq(r'f_r=\frac{1}{2\pi\sqrt{L_rC_r}}', key='fr'))
    add(p('At no load nothing clamps L<sub>m</sub>, and the tank resonates '
          'with both inductances:'))
    add(eq(r'f_o=\frac{1}{2\pi\sqrt{(L_r+L_m)\,C_r}}', key='fo'))
    add(p('At f<sub>r</sub> the gain is exactly 1 for any load, because the '
          'load term vanishes. At f<sub>o</sub> the no-load gain is '
          'without limit. Between the two the tank can boost; above '
          'f<sub>r</sub> it cannot. An LLC fed from a fixed dc bus runs close '
          'to f<sub>r</sub> nearly all the time, and drops into that band '
          'only when the bus sags.'))
    add(fig('f02_two_resonances',
            'The two resonances, and the band between them in which the tank '
            'can boost.', width=CW * 0.84))

    add(p('Two expressions are not much use without knowing what each one '
          'does to the current, and the current is where the difference is '
          'visible.'))
    add(p('Before the waveforms, the two things the circuit can be doing. '
          'Below resonance a half cycle is both of them, and in this order: '
          'power delivery first, freewheeling after it, <b>with the same '
          'pair of switches on throughout</b>. At resonance the half cycle '
          'is power delivery alone; above resonance it is power delivery cut '
          'short.'))
    add(fig('an_ref_op_power',
            '<b>Power delivery.</b> The tank is excited by the bridge and '
            'the resonant current exceeds the magnetising current, so the '
            'difference passes through the transformer to the rectifier and '
            'the load. The voltage across L<sub>m</sub> is the reflected '
            'output, so L<sub>m</sub> is clamped and takes no part in the '
            'resonance &mdash; which is why this interval resonates at '
            'f<sub>r</sub>. (Infineon AN 2012-09, headings added.)',
            width=CW))
    add(fig('an_ref_op_free',
            '<b>Freewheeling.</b> The resonant current has fallen to the '
            'magnetising current, so nothing is left to pass to the '
            'secondary and the rectifiers are off. With the secondary '
            'disconnected L<sub>m</sub> is no longer clamped and joins the '
            'resonance &mdash; this interval rings at f<sub>o</sub>. '
            '<b>The right-hand panel is redrawn.</b> The source sends its '
            'current backwards through S<sub>1</sub> and S<sub>4</sub> and '
            'out of the + terminal. Nothing can take that path in this half: '
            'S<sub>1</sub> and S<sub>4</sub> are off, and with '
            'S<sub>2</sub>,S<sub>3</sub> holding the two mid-points at 0 and '
            'V<sub>in</sub> their body diodes are reverse biased. It is the '
            'dead-time path, not this one. What is drawn here is the primary '
            'loop of the right-hand panel of Figure&nbsp;%s with the '
            'secondary open &mdash; the same relation the left-hand panel '
            'has to its own. (After Infineon AN 2012-09 Figures 2.7 and 2.8; '
            'second panel redrawn, headings added.)'
            % FR('an_ref_op_power'), width=CW))
    add(note('<b>Those two circuits are the two resonances.</b> The '
             'expressions at the top of this section are not abstractions: '
             'each one is the tank of one of these two pictures. Which one '
             'is running, and for how long, is the whole of what follows.'))
    add(note('<b>Go by the step number on each panel, not by the order on '
             'the page.</b> The two figures are grouped by what the circuit '
             'is doing, so their four panels are not in time order: steps 1 '
             'and 3 are in Figure&nbsp;%s, steps 2 and 4 in Figure&nbsp;%s. '
             'One switching period is <b>1</b> power delivery with '
             'S<sub>1</sub>,S<sub>4</sub> on, <b>2</b> freewheeling with '
             'S<sub>1</sub>,S<sub>4</sub> <i>still</i> on, the dead time, '
             '<b>3</b> power delivery with S<sub>2</sub>,S<sub>3</sub> on, '
             '<b>4</b> freewheeling with those <i>still</i> on, the dead '
             'time. Power delivery and freewheeling are the two parts of '
             '<i>one</i> half cycle &mdash; the pair of switches does not '
             'change between 1 and 2, nor between 3 and 4. <b>ZVS is in none '
             'of the four.</b> It is in the dead time after 2 and after 4, '
             'when both switches of a leg are off and the tank current '
             'carries the mid-point across the rail; Figure&nbsp;%s shows it '
             'as the step in V<sub>ds</sub> in the gap between the gate '
             'pulses, and its brackets carry the same four numbers.'
             % (FR('an_ref_op_power'), FR('an_ref_op_free'),
                FR('an_ref_modes_i'))))
    add(note('<b>The word &ldquo;freewheeling&rdquo; is used for two '
             'different intervals.</b> Here it is steps 2 and 4: the '
             'secondary is off, L<sub>m</sub> has rejoined the resonance, and '
             'the same pair of switches is still on. Other notes use the same '
             'word for the <b>dead time</b>, where the current circulates in '
             'the body diodes and delivers nothing &mdash; the phase-shift '
             'full bridge literature does, and so does an LLC note: Toshiba '
             '<i>Resonant Circuits and Soft Switching</i> (2019) writes '
             '&ldquo;Q<sub>2</sub> turns on while D<sub>Q2</sub> is '
             'freewheeling under the zero-voltage-switching condition&rdquo;, '
             'and leaves the interval this document calls freewheeling '
             '(its operating modes 2 and 6) unnamed. Both circulate current '
             'without delivering '
             'power, which is why one word gets stretched over both, but they '
             'are not the same interval: <b>the dead time is in every '
             'switching period at any frequency, while steps 2 and 4 exist '
             'only below resonance</b> and shrink to nothing at f<sub>r</sub>. '
             'Check which one a source means before comparing numbers.'))

    add(fig('an_ref_modes_i',
            'The three cases side by side. Gate signals, the drain voltage, '
            'the resonant current I<sub>Lr</sub> with the magnetising '
            'current I<sub>Lm</sub> dashed over it, and the current in each '
            'pair of rectifiers. Note T<sub>r</sub>/2 and T<sub>s</sub>/2 '
            'marked on the third panel: that gap is the whole story. The four '
            'intervals of that panel are bracketed and numbered to match the '
            'panels of the two figures above &mdash; each half is power '
            'delivery and then freewheeling, and the second half&rsquo;s is '
            'easy to miss because it ends at the right edge. '
            '(Infineon AN 2012-09; column headings and interval brackets '
            'added.)', width=CW))
    ext(bullets([
        '<b>At f<sub>r</sub> (left).</b> The resonant half period and the '
        'switching half period are the same length. I<sub>Lr</sub> meets '
        'I<sub>Lm</sub> exactly as the bridge changes and the rectifier '
        'current reaches zero exactly then too. Nothing is wasted at either '
        'end &mdash; this is the most efficient point an LLC has, and it is '
        'where a conventional design puts its nominal input.',
        '<b>Above f<sub>r</sub> (centre).</b> The switching half period ends '
        'first, so the resonant half sine is <b>cut off part way</b>: '
        'I<sub>Lr</sub> is still well above I<sub>Lm</sub> when the bridge '
        'changes. The primary switches turn off more current, and the '
        'rectifier is interrupted while still conducting &mdash; hard '
        'commutation on the secondary.',
        '<b>Below f<sub>r</sub> (right).</b> The resonant half period is the '
        'shorter one, marked T<sub>r</sub>/2 against T<sub>s</sub>/2. '
        'I<sub>Lr</sub> finishes its half sine early and <b>lands on '
        'I<sub>Lm</sub></b>; from that instant the two are one current, the '
        'rectifier current has already fallen to zero, and no power crosses '
        'to the secondary. That interval is called freewheeling.']))
    add(p('<b>That freewheeling interval is what f<sub>o</sub> is.</b> '
          'While it lasts the secondary is not conducting, so nothing '
          'clamps '
          'L<sub>m</sub> and the tank is L<sub>r</sub> + L<sub>m</sub> in '
          'series with C<sub>r</sub> &mdash; it is ringing, at '
          'f<sub>o</sub>. It looks flat only because f<sub>o</sub> is so '
          'much lower than f<sub>r</sub> that a fraction of its period is '
          'very nearly a straight line. Lower the switching frequency '
          'towards f<sub>o</sub> and that interval grows until it is the '
          'whole half period, at which point the flat part is visibly a '
          'piece of a slow sine and the converter has stopped delivering '
          'power at all.'))
    add(note('<b>The two frequencies are not two operating points; they are '
             'the two ends of one.</b> f<sub>r</sub> is where the flat '
             'interval has just vanished. f<sub>o</sub> is where it has '
             'taken over completely. Everything useful happens between '
             'them, and the fraction of the half period that is flat is, '
             'in practice, how much the tank is boosting.'))

    add(note('<b>Symbols are not standard across the literature.</b> The '
             'borrowed figures have been relabelled to match, and each '
             'caption says so. Going the other way, to a manufacturer\u2019s '
             'application note, check first which frequency that document '
             'calls f<sub>o</sub> \u2014 at least one widely used guide '
             'gives that name to the series resonance, the opposite of the '
             'meaning here.'))

    add(p('A conventional LLC picks one side and stays there &mdash; usually '
          'just above f<sub>r</sub> at nominal input, where the gain is close '
          'to 1 and the circulating current is smallest. Which side the '
          'converter designed here runs on is a different question, and '
          'it is answered in Section&nbsp;'
          + SR('Which side of resonance this converter runs on')
          + ' once the rest of the machinery is in place.'))

    add(h2('The gain function and the three regions'))
    add(p('With the usual first-harmonic approximation the tank gain is'))
    add(eq(r'M(f_n,Q,\lambda)=\frac{1}'
           r'{\sqrt{\left(1+\lambda-\frac{\lambda}{f_n^{2}}\right)^{2}'
           r'+Q^{2}\left(f_n-\frac{1}{f_n}\right)^{2}}}', key='M'))
    add(p('with f<sub>n</sub>, Q and &lambda; as defined in the conventions. '
          'Two checks are worth making on it by eye before trusting any curve '
          'drawn from it. At f<sub>n</sub>&nbsp;=&nbsp;1 the second term '
          'under the root vanishes and the first becomes 1, so '
          '<b>M&nbsp;=&nbsp;1 whatever Q</b> &mdash; that is the series '
          'resonance, and it is why every gain curve passes through the '
          'same point. <b>At no load</b> &mdash; Q&nbsp;=&nbsp;0, '
          'so the second term is gone &mdash; raising f<sub>n</sub> without '
          'limit walks M down to 1/(1+&lambda;) and no further, which is the '
          'floor that Section&nbsp;%s is about. Under load the Q term grows '
          'with f<sub>n</sub> and the gain keeps falling towards zero '
          'instead.'
          % SR('The other bound on &lambda;, and where it has no solution')))
    add(p('The curve has three regions. Below the gain peak the tank is '
          'capacitive and the bridge hard switches, which must never be '
          'allowed; between the peak and f<sub>r</sub> it is inductive and '
          'boosts; above f<sub>r</sub> it is inductive and bucks. The two '
          'boundaries are drawn here at f<sub>o</sub> and f<sub>r</sub>, '
          'which is exact only at no load &mdash; the capacitive edge moves '
          'up with load, and the next section is about that.'))
    add(fig('f04_three_regions',
            'The three operating regions, shaded for the full-load curve '
            'drawn. Only the inductive ones are usable, and the boundary '
            'between them moves up as the converter is loaded.',
            width=CW * 0.84))

    add(h2('Capacitive and inductive, and why those words'))
    add(p('The names have nothing to do with which component dominates. They '
          'describe <b>what the bridge sees</b>: the phase of the tank input '
          'current relative to the square wave driving it. The tank is a '
          'series network, so at low frequency C<sub>r</sub> dominates and '
          'the current <i>leads</i> &mdash; the bridge is driving something '
          'that behaves like a capacitor. At high frequency the inductances '
          'dominate and the current <i>lags</i> &mdash; the bridge is driving '
          'something that behaves like an inductor. The word describes the '
          'load the bridge works into, not a part.'))
    add(p('That phase is the whole of soft switching, which is why the '
          'distinction matters more than it sounds:'))
    add(fig('an_ref_cap_ind',
            'The same converter either side of the peak gain, and the '
            'waveforms that tell them apart. Above, where the boundary sits '
            'on the gain curve. Below, the bridge voltage V<sub>d</sub>, the '
            'tank current I<sub>p</sub> and the current in one switch '
            'I<sub>DS1</sub>. On the left the tank is capacitive and the '
            'switch current shows a reverse-recovery spike; on the right it '
            'is inductive and the same instant is a clean ZVS transition. '
            '(ON Semiconductor AN-4151.)', width=CW * 0.58))
    ext(bullets([
        '<b>Inductive: current lags.</b> When a switch turns off, the '
        'current is still flowing in the direction that pushes the bridge '
        'node towards the other rail. The dead time lets it do exactly that, '
        'and the next device turns on at zero volts. <b>ZVS.</b>',
        '<b>Capacitive: current leads.</b> By the time the switch turns off '
        'the current has already reversed, so it pushes the node <i>back</i> '
        'where it came from. The next device then turns on into the full '
        'rail, and worse, the body diode of the device that was conducting '
        'is forced out with reverse recovery through a low impedance. '
        '<b>Hard switching, and the failure mode that destroys parts.</b>']))
    add(note('This is why the capacitive region is not a performance '
             'trade-off to be balanced against something else. It is a '
             'boundary the design stays on one side of, and the controller '
             'carries a dedicated protection for the case where it does '
             'not.'))

    add(h2('The two boundaries are not the same boundary'))
    add(p('This is the point most easily confused, because both pairs of '
          'words describe positions on the same axis. They are different '
          'lines on it.'))
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
          'a fixed band below f<sub>o</sub> &mdash; it grows as load is '
          'added, and a frequency that is safely inductive at light load can '
          'be capacitive at overload.'))
    add(note('<b>The edge is not quite the gain peak.</b> The tank is '
             'capacitive while the phase of its input impedance is negative, '
             'so the edge is where <b>arg Z<sub>in</sub> = 0</b>, and that '
             'sits a little <i>above</i> the peak of the gain curve. At full '
             'load in this design the peak is at %(fnPk).1f&nbsp;kHz while '
             'the phase does not reach zero until %(fnEdge).1f&nbsp;kHz, and '
             'at the peak itself the bridge still sees %(phPk).1f&deg; of '
             'capacitive phase. The peak is the usual stand-in because it '
             'needs only the gain curve, but it is optimistic in the '
             'dangerous direction: it calls a band inductive while the '
             'bridge is still hard switching. Both are approximations of one '
             'real condition, and Section&nbsp;%(zvsref)s measures that '
             'condition directly instead &mdash; the time the tank current '
             'takes to reach zero after the bridge changes.'
             % dict(V, zvsref=SR('ZVS verification'), **_edge_numbers(A))))
    add(fig('an_ref_loadshift',
            'The capacitive boundary is not fixed. Loading the converter '
            'pushes the gain peak, and with it the edge of the capacitive '
            'region, to a higher frequency. (Monolithic Power Systems, '
            'Understanding LLC Operation part 2.)', width=CW * 0.62))
    ext(bullets([
        'A converter can be <b>below f<sub>r</sub> and still inductive</b> '
        '&mdash; that is the ordinary boosting region, and it is where an '
        'LLC normally runs.',
        'It can be <b>below f<sub>r</sub> and capacitive</b>, which is the '
        'fault. Going below f<sub>r</sub> is not the danger; going below the '
        'peak is.',
        'It cannot be <b>above f<sub>r</sub> and capacitive</b>, because the '
        'peak is always below f<sub>r</sub>. Everything above f<sub>r</sub> '
        'is inductive at every load.']))
    add(note('<b>What this means for the design rule.</b> Keep the '
             'oscillator floor f<sub>Min</sub> above f<sub>o</sub>. That is '
             'the <i>no-load</i> position of the boundary, so it is the '
             'weakest form of the requirement: necessary, but not enough on '
             'its own. The real check is the ZVS sweep in '
             'Section&nbsp;' + SR('ZVS verification')
             + ', which is run at load and at every phase of the line cycle, '
               'and the controller carries an anti-capacitive protection '
               'behind that.'))

    add(h2('ZVS and ZCS are not the same thing'))
    add(p('Both are ways of switching a device while one of its two '
          'quantities is zero, so that their product &mdash; the loss '
          '&mdash; is zero. They apply to different devices here, for '
          'different reasons, and only one of them is guaranteed.'))
    add(fig('an_zvs_zcs',
            'Zero-voltage switching on the primary and zero-current '
            'switching on the secondary. Different devices, different '
            'mechanisms, different conditions.', width=CW))
    ext(bullets([
        '<b>ZVS &mdash; zero-voltage switching, on the primary switches.</b> '
        'The device turns on with no voltage across it. It works because the '
        'tank current is still flowing when the previous device turns off, '
        'and that current discharges the bridge node during the dead time. '
        'It needs <b>inductive operation</b>, which is to say anywhere above '
        'the gain peak &mdash; so it is available on both sides of '
        'f<sub>r</sub>, and f<sub>o</sub> is that limit only at no load. It '
        'is required everywhere, and Section&nbsp;' + SR('ZVS verification')
        + ' says how much margin this design has.',
        '<b>ZCS &mdash; zero-current switching, on the secondary '
        'rectifiers.</b> The device turns off with no current through it, so '
        'a diode is not forced out of conduction and a synchronous rectifier '
        'has no reverse recovery. It happens because the resonant current '
        'reaches zero on its own &mdash; which only occurs <b>below '
        'f<sub>r</sub></b>. Above f<sub>r</sub> the rectifier is cut off '
        'while still conducting and reverse recovery comes back.']))
    add(note('<b>So ZCS is not a property of the circuit but of the '
             'operating point.</b> Below f<sub>r</sub> the secondary '
             'rectifiers turn off at zero current and reverse recovery never '
             'appears; above f<sub>r</sub> they do not and it does. A '
             'converter that stays on one side settles the question once. '
             'One whose input moves far enough to cross f<sub>r</sub> has to '
             'be checked on both sides: its secondary body diode and '
             'synchronous-rectifier dead time matter whenever it is running '
             'above f<sub>r</sub>.'))

    add(h2('Sizing the dead time so that ZVS actually happens'))
    add(p('ZVS is what makes an LLC efficient, and it is a charge problem '
          'rather than a voltage problem. During the dead time the '
          'magnetising current must move enough charge to swing the bridge '
          'node across the rail before the opposite device turns on. The '
          'design quantity is the time the tank current takes to reach zero '
          'after the bridge transition, T<sub>ZC</sub>, and the requirement '
          'is simply that it outlast the dead time:'))
    add(eq(r'T_{ZC}\;>\;t_D', key='zvs'))
    add(fig('f05_zvs_mechanism',
            'How ZVS happens: the magnetising current, not the load current, '
            'discharges the bridge node during the dead time.',
            width=CW * 0.80))
    add(note('<b>Use the output charge, not the flat-band capacitance.</b> A '
             'MOSFET datasheet quotes C<sub>oss</sub>, C<sub>o(er)</sub> and '
             'C<sub>o(tr)</sub>, and they differ by three to five times. ZVS '
             'is a charge question, so <b>C<sub>o(tr)</sub></b> (equivalently '
             'Q<sub>oss</sub>) is the one to use. Sizing the dead time from '
             'the headline C<sub>oss</sub> is optimistic by a large factor.'))

    add(h2('How an LLC is normally designed'))
    add(p('The sequence below is the standard one, and every step exists '
          'because of something already established. It is worth having in '
          'mind before Section&nbsp;' + SR('Design procedure')
          + ', which follows the same order and diverges from it in exactly '
            'two places.'))
    ext(bullets([
        '<b>1  Turns ratio from the nominal point.</b> Choose n so that the '
        'converter runs at or near M&nbsp;=&nbsp;1 at nominal input, that '
        'is at f<sub>r</sub>. That is where the circulating current is '
        'lowest and where the converter should normally run.',
        '<b>2  The gain range the tank must cover.</b> From the input range '
        'and the output tolerance, M<sub>min</sub> and M<sub>max</sub>. '
        'M<sub>max</sub> is asked at minimum input and full load, '
        'M<sub>min</sub> at maximum input and minimum load.',
        '<b>3  Load resistance referred to the primary</b>, R<sub>ac</sub>, '
        'and with it the meaning of Q at full load.',
        '<b>4  m (equivalently &lambda;) and Q, together, from the peak-gain '
        'chart.</b> These are not independent: for each m there is a curve '
        'of attainable peak gain against Q, and the design has to sit under '
        'the curve with margin. A larger m gives less circulating current '
        'and less peak gain; a smaller m the reverse.',
        '<b>5  The component values.</b> Q and R<sub>ac</sub> give '
        'Z<sub>0</sub>, and Z<sub>0</sub> with the chosen f<sub>r</sub> '
        'gives C<sub>r</sub> and L<sub>r</sub>; m then gives L<sub>m</sub>.',
        '<b>6  Verify.</b> That the gain at the worst corner is still under '
        'the peak with margin, that ZVS holds at the worst point rather than '
        'the nominal one, and that the currents and the flux are ones real '
        'parts can carry.']))
    add(fig('an_ref_peakgain',
            'Step 4, and the reason m and Q cannot be chosen separately: the '
            'peak gain a tank can reach depends on both. Picking a required '
            'gain and a Q leaves only a band of usable m. (ON Semiconductor '
            'AN-4151.)', width=CW * 0.52))
    add(note('<b>That is the first half.</b> Everything above is the LLC on '
             'its own: a tank, a gain curve, and a frequency that moves the '
             'operating point along it. Nothing in it has anything to do '
             'with the mains. The rest of this section is the other half '
             '&mdash; what a power factor corrector is for and how the '
             'ordinary one works &mdash; and it can be read without '
             'reference to any of the above. Section&nbsp;'
             + SR('Why single stage, and what it costs')
             + ' is where the two are put together.'))

    add(h2('What power factor correction is'))
    add(p('Start with what happens if nothing is done. A bridge rectifier '
          'feeding a capacitor holds the bus near the peak of the mains, so '
          'the diodes can only conduct during the short window in which the '
          'mains is above that. All of the charge the load will use over the '
          'whole cycle has to arrive inside that window.'))
    add(fig('an_ref_pfc_cap',
            'A capacitor-input rectifier and what it draws. V<sub>C</sub> '
            'stays near the peak, so the diodes conduct only in the two '
            'narrow windows where the mains is above it, and the current I '
            'inside them is correspondingly tall. (Toshiba, Power Factor '
            'Correction Circuits.)', width=CW * 0.66))
    add(p('The consequences are all consequences of that one fact. The peak '
          'current is several times what a resistor of the same average power '
          'would draw, so the wiring, the fuse, the bridge and the source all '
          'have to be sized for it. And a pulse train that narrow is mostly '
          'harmonics.'))

    add(h2('Power factor, and why it is not the same as distortion'))
    add(p('<b>Power factor</b> is the ratio of real power to apparent power:'))
    add(eq(r'PF=\frac{P}{V_{rms}I_{rms}}\;=\;\cos\varphi_{1}\;\times\;\frac{I_{1,rms}}{I_{rms}}'))
    add(p('It has two independent factors and they fail for different '
          'reasons. <b>Displacement</b> is the phase between the voltage and '
          'the fundamental of the current, and it is what a motor gets wrong. '
          '<b>Distortion</b> is how much of the rms current is at the '
          'fundamental at all, and it is what a rectifier gets wrong. The '
          'current in the figure above is roughly in phase, so its '
          'displacement factor is near 1 &mdash; and it still scores about '
          '0.6, because the rest of the rms is harmonics.'))
    add(p('The related figure of merit is <b>total harmonic distortion</b>, '
          'the harmonic content as a fraction of the fundamental:'))
    add(eq(r'THD=\frac{\sqrt{I_{rms}^{2}-I_{1,rms}^{2}}}{I_{1,rms}}'
           r'\,,\qquad \frac{I_{1,rms}}{I_{rms}}=\frac{1}{\sqrt{1+THD^{2}}}'))
    add(note('<b>The two are not interchangeable.</b> A converter can hold '
             'PF above 0.99 and still fail a harmonic limit, because the '
             'standard limits <i>individual</i> harmonics in amperes rather '
             'than a single ratio. Harmonics do not deliver power; they heat '
             'the neutral, saturate distribution transformers and disturb '
             'other equipment on the same supply, which is why they are '
             'regulated. IEC&nbsp;61000-3-2 sets the limits, and which '
             'limit applies depends on the class: a mains rectifier of '
             'this shape is Class&nbsp;D, exempt below 75&nbsp;W and '
             'held to a milliamp-per-watt line above it. <b>But Class&nbsp;D '
             'only reaches 600&nbsp;W</b> &mdash; this design draws '
             '%(Pin).0f&nbsp;W at the input, above that, so the absolute '
             'Class&nbsp;A limits apply instead. Settle the class first.'
             % V))

    add(h2('How a corrector fixes it'))
    add(p('Force the input current to follow the input voltage and the '
          'converter looks like a resistor to the mains: both factors go to '
          'one at once. The standard implementation is a <b>boost converter '
          'placed straight after the bridge</b>, switching fast enough that '
          'the mains looks frozen within one switching cycle.'))
    add(fig('an_ref_pfc_boost',
            'A boost corrector, with the current path traced for each half '
            'of the line cycle: red while the switch is on and the reactor '
            'charges, green while it is off and the reactor delivers to the '
            'bus. (Toshiba, Power Factor Correction Circuits.)',
            width=CW * 0.62))
    ext(bullets([
        '<b>Why boost.</b> The input is a rectified sine that passes through '
        'zero, so the stage has to be able to step up by an unlimited ratio '
        'near the crossing &mdash; only boost can. Its input current is also '
        'continuous, which is what makes shaping it possible at all.',
        '<b>The inner loop</b> regulates inductor current to a reference. It '
        'has to be fast compared with the switching frequency.',
        '<b>The outer loop</b> regulates the bus voltage, and is deliberately '
        'made <b>slower than 2f<sub>l</sub></b>. If it were fast it would '
        'fight the ripple on the bus, modulate the level within the line '
        'cycle and flatten the very shape the corrector exists to make. A '
        'slow voltage loop is not a compromise here; it is a requirement.',
        '<b>The multiplier</b> joins them: shape from the mains, level from '
        'the output. That is the whole of the control law.']))
    add(fig('an_ref_pfc_ccm',
            'The result, in continuous conduction mode. Switching ripple '
            'rides on the reactor current; its average follows the input '
            'voltage, which is what the two loops were arranged to produce. '
            '(Toshiba, Power Factor Correction Circuits.)', width=CW * 0.66))
    add(note('<b>This comes back later.</b> Take the boost stage away and '
             'the same conflict returns in a sharper form: the outer loop is '
             'then the <i>only</i> loop, its output is a power command, and '
             'any 2f<sub>l</sub> ripple that survives it becomes input '
             'current distortion directly. That is '
             'Section&nbsp;' + SR('Voltage loop and compensation') + '.'))
    add(p('The corrector delivers what was asked for, and hands over a new '
          'problem in doing so. A current that follows the voltage means an '
          'input power that follows sin&sup2;&thinsp;&theta;: zero twice per '
          'cycle, twice the average at the crests. The load still wants '
          'constant power. <b>Something has to store the difference</b>, and '
          'where that something sits is the whole of the next section.'))

    add(h2('Why they are normally two stages'))
    add(fig('an_ref_acdc',
            'The usual two-stage arrangement, with the waveform at every '
            'node. The correction happens in the first block and the LLC '
            'works from the dc bus it produces. (Monolithic Power Systems, '
            'Understanding LLC Operation part 2.)', width=CW))
    add(p('The bus capacitor between a boost PFC and an LLC does two jobs at '
          'once, and they are usually confused with each other:'))
    ext(bullets([
        'it <b>buffers</b> the difference between the pulsating input power '
        'and the constant output power;',
        'it <b>isolates</b> the LLC from the mains waveform, so the tank sees '
        'a nearly constant input and has to cover only a narrow gain range.']))
    add(p('Removing the boost stage removes both services at once. The '
          'buffering has to be done somewhere else, and the tank now has to '
          'work directly from a rectified sine that goes to zero a hundred '
          'times a second. What that costs, and why it works anyway, is the '
          'rest of the story.'))

    add(h1('Why single stage, and what it costs'))
    add(note('<b>Two steps of that recipe are the ones this converter '
             'breaks.</b> Step&nbsp;1 has no nominal point to settle at, '
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
            'shaded areas are what a capacitor somewhere must absorb and give '
            'back.', width=CW * 0.84))

    add(h2('Moving the buffer from 400 V to the output'))
    add(p('In the two-stage converter that buffer is the bus capacitor, at '
          '400&nbsp;V. In the single-stage converter there is no bus, so the '
          'buffer moves to the output. <b>The joules do not change &mdash; '
          'the voltage they sit at does</b>, and a capacitor only ever '
          'returns the energy between its starting voltage and the lowest '
          'the load will accept:'))
    add(eq(r'E=\frac{1}{2}C\left(V^{2}-V_{min}^{2}\right)'))
    add(p('Hold-up is the clearest way to see the price, because both '
          'architectures must ride out the same %(Thold).0f&nbsp;ms at full '
          'power &mdash; %(Ehold).1f&nbsp;J either way. On a 400&nbsp;V bus '
          'falling to 320&nbsp;V that is a %(Cbulk).0f&nbsp;&micro;F part. '
          'On a %(Vout).0f&nbsp;V output falling to %(Vomin).0f&nbsp;V it is '
          '<b>%(Chold).1f&nbsp;mF</b>: the same energy, '
          '%(Cratio).0f&nbsp;times the capacitance, because the usable '
          'voltage window shrank from 400&sup2;&minus;320&sup2; to '
          '%(Vout).0f&sup2;&minus;%(Vomin).0f&sup2;. That single ratio is '
          'the price of the architecture. It should be settled before '
          'anything else is designed: if the enclosure cannot house the '
          'bank, the output voltage is what has to change.' % V))
    add(note('<b>The bank finally built is larger still.</b> '
             '%(Chold).1f&nbsp;mF only satisfies hold-up. Ripple asks for '
             '%(Crip).1f&nbsp;mF on the same output and wins, so the design '
             'carries <b>%(Cout).1f&nbsp;mF</b>. Which of the two decides is '
             'a question about the specification, and Section&nbsp;' % V
             + SR('The output capacitor bank') + ' settles it.'))
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
          + SR('Voltage loop and compensation')
          + '). Here the specification is <b>%(dv).0f&nbsp;%% '
            'peak-to-peak</b>, which is %(dVo).2f&nbsp;V on a '
            '%(Vout).0f&nbsp;V rail. <b>How tight that figure has to be is a '
            'property of the load, not of the converter</b>, and it has to '
            'come from the specification rather than from a design rule.'
            % V))

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
    add(p('with &theta; the line phase angle. The reasoning is worth '
          'spelling out, because it is the hinge of the whole topology. A '
          'gain is a ratio of two voltages. In a two-stage converter the '
          'output voltage is free to move &mdash; the loop moves it &mdash; '
          'so commanding a gain is the same as commanding an output. Here '
          '<b>both of those voltages are already pinned by something outside '
          'the converter</b>: the input by the mains, the output by a bank '
          'so large that it cannot change within a switching cycle. Their '
          'ratio is therefore fixed too, moment by moment, and the '
          'controller has no say in it.'))
    add(p('So what does moving the switching frequency do? It moves <b>Q</b> '
          '&mdash; the loading &mdash; and Q is power. The tank is told what '
          'gain to produce and is left to choose how much current it draws '
          'to produce it. <b>In this converter frequency is a power command, '
          'not a voltage command.</b>'))

    add(h2('Two divergences that cancel'))
    add(p('Read that equation near the mains zero crossing and it looks '
          'impossible: as &theta;&nbsp;&rarr;&nbsp;0 the required gain rises '
          'as 1/sin&thinsp;&theta; without limit. The converter survives '
          'because the load vanishes at the same time. A unity-power-factor '
          'input draws power proportional to sin&sup2;&thinsp;&theta;, so'))
    add(eq(r'Q(\theta)=Q_{pk}\,\sin^{2}\theta', key='Qtheta'))
    add(p('and an unloaded LLC has without limit gain at its lower resonance '
          'f<sub>o</sub>. Two divergences meet, and the operating point walks '
          'down towards f<sub>o</sub> as the mains approaches zero '
          '(Figure&nbsp;' + FR('f12_two_divergences')
          + '). <b>f<sub>o</sub> is therefore the frequency floor of the '
            'entire design</b>, and putting the oscillator clamp below it is '
            'one of the few mistakes that destroys hardware.'))
    add(fig('f12_two_divergences',
            'Near the zero crossing the required gain diverges and the load '
            'vanishes together, so the operating point converges on '
            'f<sub>o</sub>.', width=CW * 0.88))

    add(h2('Frequency modulation is the power factor correction'))
    add(p('Put those together and the control law falls out. Over a line half '
          'cycle the controller sweeps the switching frequency so the power '
          'drawn follows sin&sup2;&thinsp;&theta;. There is no current loop, '
          'no multiplier and no separate PFC stage: <b>the frequency profile '
          'f<sub>sw</sub>(&theta;) is the power factor correction</b>. '
          'Figure&nbsp;%s shows it for this design at both ends of the '
          'equivalent input range.' % FR('f14_fsw_theta')))
    add(fig('f14_fsw_theta',
            'f<sub>sw</sub>(&theta;) over a line half cycle. The excursion is '
            'the power factor correction; the floor is f<sub>o</sub>.',
            width=CW * 0.84))
    add(p('Working that profile out looks like it needs a numerical root '
          'search. At each &theta; the gain equation has to be solved for '
          'f<sub>n</sub>, and it has two roots: a capacitive one and an '
          'inductive one. <b>It does not.</b> Substituting '
          'M<sub>req</sub> = M<sub>pk</sub>/sin&thinsp;&theta; and '
          'Q = Q<sub>pk</sub>sin&sup2;&thinsp;&theta; and writing '
          'x = 1/f<sub>n</sub>&sup2; turns the gain equation into a cubic '
          'in x:'))
    add(eq(r'\lambda^{2}x^{3}+(q-2\lambda(1+\lambda))x^{2}'
           r'+((1+\lambda)^{2}-2q-\frac{u}{M_{pk}^{2}})x+q=0,'
           r'\qquad u=\sin^{2}\theta,\;\; q=Q_{pk}^{2}u^{2}', key='cubic'))
    add(p('One root is always negative: the cubic is +q at x&nbsp;= 0 and '
          'runs to &minus;&infin; as x grows. The other two are the two '
          'crossings of one curve. On x&nbsp;&gt; 0 the right-hand side of '
          'the gain equation starts at infinity, falls to a single minimum '
          'and rises again. So a required gain the tank can actually produce '
          'is met at <b>exactly two</b> positive values of x: the capacitive '
          'crossing and the inductive one. All three roots are then real. '
          'The physical, inductive root is the <b>middle</b> one, because '
          'x&nbsp;= 1/f<sub>n</sub>&sup2; runs backwards against frequency. '
          'There is no branch to choose: in the trigonometric form of '
          'Cardano it is always the k&nbsp;= 1 branch. If the required gain '
          'is below that minimum there is no positive root at all, which is '
          'the no-solution case of Section&nbsp;'
          + SR('The other bound on &lambda;, and where it has no solution')
          + ' rather than a numerical failure.'))
    add(note('<b>Why this matters beyond elegance.</b> A grid search needs an '
             'upper bound on f<sub>n</sub>, and a bound chosen from the ac '
             'maximum rather than the morphing corner with no warning cannot '
             'represent the real operating point. The closed form has no '
             'grid, no bracket and no starting guess, so that failure mode '
             'does not exist. The inverse problem &mdash; the '
             'sin&sup2;&thinsp;&theta; that gives a required f<sub>n</sub> '
             '&mdash; is a quadratic and is likewise exact.'))

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
    add(p('Section&nbsp;%s left the question open. Now it can be answered, '
          'and the answer is that a single-stage converter does not pick a '
          'side. The equivalent input sweeps a half sine every 10&nbsp;ms, '
          'the required gain sweeps with it, and the operating point walks '
          'across f<sub>r</sub> and back within one line cycle. How much of '
          'the cycle it spends on each side depends on the mains voltage.'
          % SR('The two resonances')))
    add(fig('an_above_below',
            'Which side of f<sub>r</sub> the converter is on, over a line '
            'half cycle, at four equivalent inputs. At the low corner it '
            'never leaves the boosting region; at the high corner it spends '
            'most of the cycle bucking.', width=CW))
    add(note('<b>Both sides have to be designed for.</b> The boosting side '
             'sets the gain requirement and the ZVS margin. The bucking side '
             'sets the top switching frequency, and it takes the secondary '
             'out of zero-current switching &mdash; so the rectifier body '
             'diode and the SR dead time matter here in a way they do not in '
             'a conventional LLC. A design checked only at the line peak, or '
             'only at low line, has looked at one of the two converters.'))

    add(h2('Why &lambda; must be about 0.5'))
    add(p('A classic LLC uses m&nbsp;=&nbsp;L<sub>p</sub>/L<sub>r</sub> '
          'between 5 and 10, that is &lambda; between 0.11 and 0.25. A '
          'single-stage converter cannot: it has to produce very high gain '
          'near the zero crossing, and peak gain falls as &lambda; falls. '
          'This design runs <b>&lambda;&nbsp;=&nbsp;%(lam).2f</b>, that is '
          'm&nbsp;=&nbsp;%(m).2f. The evaluation board ST publishes for this '
          'part runs &lambda;&nbsp;=&nbsp;0.500, which is the strongest '
          'available confirmation that the value is structural and not a '
          'quirk of one design.' % V))
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
          'runs out of frequency. Here f<sub>r</sub>/f<sub>sw,max</sub> = '
          '%(frt).0f/%(fswspec).0f, so the squared ratio is '
          '%(frt2).1f&nbsp;%%, both denominators fall well below one, and the '
          'requirement rises from &lambda;<sub>1</sub>&nbsp;=&nbsp;'
          '%(lam1).3f to %(lam2).3f and %(lamTD).3f. <b>The number typed as '
          'f<sub>sw,max</sub> roughly doubles the &lambda; the tank is asked '
          'for</b>, and as it approaches f<sub>r</sub> the denominators go to '
          'zero and the requirement diverges.' % V))
    add(note('<b>So where does f<sub>sw,max</sub> come from?</b> The common '
             'rule is 1.5&nbsp;&times;&nbsp;f<sub>r</sub>, which is what the '
             '%(fswspec).0f&nbsp;kHz here is. It is a <b>choice</b>, not a '
             'limit &mdash; and it sits upstream of the tank, so changing it '
             'changes L<sub>m</sub>. That is the opposite of how a maximum '
             'usually behaves in a design sheet, and a round number can be '
             'typed into it without noticing what moves.' % V))
    add(p('It should not be confused with f<sub>Max</sub>, the oscillator '
          'ceiling. That one <i>is</i> a limit: R<sub>T</sub>, C<sub>T</sub> '
          'and the idle time fix it in silicon, the control loop cannot push '
          'past it however much gain it wants, and it is checked after the '
          'fact by k<sub>ceil</sub> &mdash; %(fMax).0f&nbsp;kHz against an '
          'operating maximum of %(fswmaxop).0f&nbsp;kHz, a factor of '
          '%(kceil).2f. The two sit at opposite ends of the design: one '
          'decides the tank, the other reports whether the oscillator can '
          'serve it.' % V))

    add(h2('The other bound on &lambda;, and where it has no solution'))
    add(p('The condition above sets a floor under &lambda;. The ceiling comes '
          'from the opposite end: the tank must also be able to reach the '
          '<i>lowest</i> required gain, which happens at the highest '
          'equivalent input and no load. That is where the usual design rule '
          'without showing it breaks down, because the no-load gain of an LLC does not '
          'fall indefinitely. Raising the frequency only walks it down to an '
          'asymptote:'))
    add(eq(r'M_{\infty}\;=\;\lim_{f\to\infty}M_{no\;load}'
           r'\;=\;\frac{1}{1+\lambda}', key='Minf'))
    add(p('<b>If the required minimum gain lies below M<sub>&infin;</sub>, no '
          'frequency satisfies the condition at all.</b> A spreadsheet '
          'solving for that frequency returns an error rather than a number, '
          'and the error is easy to mistake for a broken formula. It is not: '
          'the question simply has no answer.'))
    if V['fnl'] is not None:
        add(p('This design sits above the asymptote &mdash; '
              'M<sub>&infin;</sub> = %(Minf).4f against a requirement of '
              '%(MFBmax).4f &mdash; so it does have a solution, at about '
              '%(fnl).0f kHz. Lowering the turns ratio lowers the requirement '
              'and pushes it under the asymptote, at which point the solution '
              'disappears.' % V))
    else:
        add(p('<b>This design is below the asymptote</b>: '
              'M<sub>&infin;</sub> = %(Minf).4f against a requirement of '
              '%(MFBmax).4f. There is no frequency at which the unloaded tank '
              'reaches the required gain, and the margin is thin enough '
              '&mdash; well under one per cent &mdash; that no full-load '
              'check would ever show it. Raising the turns ratio raises the '
              'requirement and brings the solution back.' % V))
    add(note('Losing the solution is not a failure. No load at high line is '
             'the region <b>burst mode</b> owns, not frequency control. Under '
             'load the gain curve falls further and the corner arrives '
             'sooner, so every full-load check is unaffected &mdash; which is '
             'exactly why this can go unnoticed. What is worth knowing is '
             'which of the candidate ratios still regulates on frequency '
             'alone, because no full-load number reveals it.'))

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
    add(p('Diagonal pairs conduct together. Q1 and Q4 put +V<sub>in</sub> '
          'across the tank, Q2 and Q3 put &minus;V<sub>in</sub> across it, so '
          'the drive is a square wave of amplitude V<sub>in</sub> and its '
          'fundamental is (4/&pi;)&thinsp;V<sub>in</sub>. All four devices '
          'switch, and each carries the tank current for half of every '
          'period.'))
    add(fig('f15_bridge_fb',
            'Full bridge: conduction path in each half period, and the '
            'resulting tank drive.'))

    add(h2('Half bridge'))
    add(p('LOUT2 is held statically high. Q3 never turns on and Q4 never '
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
    add(note('<b>The standing device is the hottest one.</b> Q4 never '
             'switches, but it conducts the full tank current continuously '
             '&mdash; %(Iprilc).1f&nbsp;A rms in this design, '
             '%(Ploss).2f&nbsp;W in one package. It is easy to overlook '
             'precisely because it is not switching, and it is the device '
             'that sets the heatsinking requirement.' % V))

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
          'bridge at 235&nbsp;V<sub>pk</sub> coming down. Ten volts of '
          'hysteresis is what stops it chattering at the threshold, but it '
          'also means that <b>between 235 and 245&nbsp;V<sub>pk</sub> the '
          'mains voltage alone does not determine the mode</b> &mdash; the '
          'direction of travel does.'))
    add(p('Assigning each threshold to the side on which its mode is '
          'guaranteed gives the design range %(Veqlo).1f to '
          '%(Veqhi).1f&nbsp;Vac (1.92:1). Including the band gives '
          '<b>%(Veqlo2).1f to %(Veqhi2).1f&nbsp;Vac (2.08:1)</b>. This design '
          'passes every check at the wider range as well, but a design with '
          'less margin would not, and the narrower figure must not be used '
          'when tightening a specification.' % V))
    add(fig('f18_morph_levels',
            'Where each mode applies. Inside the band the mode depends on '
            'which direction the mains arrived from.', width=CW * 0.78))
    add(note('<b>Where you will actually meet the band.</b> Real mains never '
             'sits at 166 to 173&nbsp;Vrms, so in service the mode is settled '
             'at start-up and stays. The band is met on a programmable ac '
             'source and in line dip and surge testing. Test it with a '
             '<b>step</b> across the threshold, not a ramp &mdash; a ramp '
             'gives the voltage loop time to follow, and a step does not.'))
    add(note('<b>Transition transient.</b> Crossing a threshold changes the '
             'tank drive 2:1 within one line cycle, and f<sub>sw</sub> must '
             'follow from %(fswA).0f to %(fswB).0f&nbsp;kHz against a voltage '
             'loop that crosses at %(fcross).1f&nbsp;Hz. The output droops '
             'until the loop recovers. This event is <b>enveloped by the '
             'hold-up case</b>, which removes power entirely for '
             '%(Thold).0f&nbsp;ms and is already met, so it is not a reason '
             'to enlarge C<sub>out</sub> or speed the loop. That containment '
             'has not yet been confirmed in the time domain.' % V))

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
    add(p('The worked example in Section&nbsp;%(ref)s states its '
          'specification in full, sorted by what kind of number each one is '
          '&mdash; imposed, chosen, assumed, or derived &mdash; because the '
          'only useful question about a number is whether it can be moved, '
          'and the answer differs by group. The procedure below refers to it '
          'but does not repeat it. Two of its qualifiers matter to every '
          'step here and are worth stating once. <b>The worst line frequency '
          'is the lowest</b>, so everything that depends on f<sub>l</sub> '
          'uses %(flmin).0f&nbsp;Hz. And <b>hold-up is specified at the worst '
          'line phase</b>, which is the ripple trough rather than the '
          'nominal output.'
          % dict(V, ref=SR('The specification, sorted by what kind of number '
                           'it is'))))

    add(h2('The equivalent input range'))
    add(p('This is the step most often got wrong. With morphing the tank does '
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
    add(p('Two ratios have to be kept apart. <b>n</b> is the '
          'equivalent-model ratio used in the gain equation; '
          '<b>n<sub>T</sub></b> is the physical turns ratio of a transformer '
          'whose leakage is integrated into L<sub>r</sub>. Confusing them '
          'shifts the whole gain curve, and at &lambda;&nbsp;&asymp;&nbsp;0.5 '
          'they differ by more than 20&nbsp;%%. The transformer drawing must '
          'therefore specify open- and short-circuit inductance as well as '
          'turns.' % {}))

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
        '<b>Sit under the Q<sub>ZVS</sub> cap rather than on it.</b> That gap '
        'is where most of a design&rsquo;s ZVS margin comes from, and it is a '
        'choice rather than an accident of rounding. L<sub>m</sub> is chosen '
        'together with n so that n<sub>T</sub>&nbsp;=&nbsp;'
        'n&radic;(1+&lambda;<sub>act</sub>) lands on a ratio that can '
        'actually be wound.']))
    add(note('<b>The same expression, evaluated somewhere else.</b> Every '
             'LLC text writes R<sub>ac</sub> = '
             '(8/&pi;&sup2;)n&sup2;V<sub>o</sub>&sup2;/P, and so does this '
             'one. A two-stage converter has only one output power, so that '
             'is the end of it. Here the drawn power is '
             'p(&theta;) = 2P&thinsp;sin&sup2;&thinsp;&theta;, so '
             'R<sub>ac</sub> varies over the line cycle as well, and a '
             'single number has to be pinned to a chosen instant. Pin it to '
             'the <b>line peak</b>, where p = 2P and the tank is '
             'most heavily loaded &mdash; putting 2P in the denominator of '
             'the same expression is what turns the 8 into a 4. <b>It is not '
             'a different formula and it has nothing to do with half bridge '
             'against full bridge</b>; the bridge factor belongs to the '
             'equivalent input voltage, not in the load. Q then means the '
             'quality factor at the line peak, and every other phase scales '
             'from it as Q(&theta;) = Q<sub>pk</sub>sin&sup2;&thinsp;&theta;. '
             'Taking the two-stage number across instead understates the '
             'loading by two, and every tank value that follows is wrong.'))

    add(h2('ZVS verification'))
    add(p('The closed-form ZVS estimate found in most design guides is a '
          'fitted approximation, and it is evaluated at the design '
          'Q<sub>ZVS</sub> rather than at the Q the converter actually runs '
          'at. Measured against a full sweep it can err in <b>either</b> '
          'direction, by tens of per cent, and the sign of the error is not '
          'fixed &mdash; it depends on the tank. Optimistic is the dangerous '
          'direction, because it reports ZVS margin that is not there. '
          'Section&nbsp;%(ref)s puts numbers on both directions.'
          % dict(ref=SR('ZVS over the whole operating space'))))
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
          'load with the <b>selected</b> tank and take the minimum. That is '
          'a grid, not a formula, and it is the only form of this check that '
          'can be trusted. Section&nbsp;%(ref)s runs it for this design and '
          'says where the worst point turned out to be &mdash; which is not '
          'where a reader would guess.'
          % dict(ref=SR('ZVS over the whole operating space'))))

    add(h2('Which side of resonance the converter runs on'))
    add(p('Below f<sub>r</sub> the secondary current is a truncated sine with '
          'a dead interval and the conduction ratio d = '
          'f<sub>sw</sub>/f<sub>r</sub> is less than one; above f<sub>r</sub> '
          'the current is continuous and d clamps at one. The rms figures '
          'that ratings and losses are built on carry d, so this is not a '
          'matter of wording.'))
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
    add(fig('an_tank_current',
            'The composite tank current, and why its peak is not the sum of '
            'the two component peaks.', width=CW * 0.74))
    add(h2('The transformer'))
    add(p('The tank has fixed L<sub>r</sub>, L<sub>m</sub> and a ratio; the '
          'transformer has turns, an open-circuit inductance and a leakage. '
          'Getting from one to the other is where most of the errors in a '
          'resonant design are made, because <b>two different turns ratios '
          'and two different inductances carry almost the same names</b>.'))

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
    add(fig('an_ref_integrated',
            'The same transformer drawn both ways. Above, the leakage split '
            'between the two sides; below, all of it referred to the primary '
            'so that the tank sees L<sub>r</sub>, a shunt inductance and an '
            'ideal transformer whose ratio is no longer the wound one. '
            'The source calls the total primary inductance L<sub>p</sub>, '
            'which is L<sub>open</sub> here, and its M<sub>V</sub> is '
            '&radic;(1+&lambda;) &mdash; so n<sub>T</sub>/M<sub>V</sub> is '
            'n. (ON Semiconductor AN-4151; the wound ratio relabelled '
            'n<sub>T</sub> to match.)', width=CW * 0.62))
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
          'it, and a part that meets it can still miss the tank. State the '
          'turns ratio in words as well: at one or two secondary turns the '
          'self-inductance of that winding is dominated by the loop of the '
          'lead-out, so &radic;(L<sub>1</sub>/L<sub>2</sub>) does not recover '
          'the ratio.'))

    add(h2('Peak flux is set by the secondary, not the primary'))
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

    add(h2('The saturation test is not the peak winding current'))
    add(p('A DC-overlap test leaves every other winding open, so none of the '
          'primary ampere-turns is cancelled by the secondary and the same '
          'current makes far more flux than it does in operation. Ask for the '
          'current that reproduces the operating flux in that test:'))
    add(eq(r'I_{eq}=\frac{B_{pk}\,N_{p}\,A_{e}}{L_{open}}', key='Isat'))
    add(p('Handing the supplier the peak tank current instead asks for a flux '
          'density no ferrite reaches, and the answer comes back as an '
          'oversized core or as a query.'))

    add(h2('The specification, and what it is not allowed to leave out'))
    add(note('<b>The open-circuit tolerance is not a round number, and it '
             'is not free to be one.</b> f<sub>o</sub> goes as '
             '1/&radic;L<sub>open</sub>, so a low part raises the frequency '
             'floor towards the oscillator clamp. The fall a tank can '
             'tolerate follows from k<sub>floor</sub> and is typically a few '
             'per cent, so the reflex &plusmn;10&nbsp;%% can let a compliant '
             'part hard switch. Section&nbsp;' % {}
             + SR('Controller network') + ' derives the figure and gives the '
             'two ways out. Ask the supplier for the asymmetric limit, or '
             'buy the room in the oscillator first and then ask for '
             '&plusmn;10&nbsp;%.'))
    add(note('Core, bobbin, wire and winding order are the supplier choice, '
             'and insulation and creepage follow the applicable safety '
             'standard. '
             'Nothing above constrains them; everything above is measurable '
             'at the terminals.'))

    add(h2('If one transformer is not practical'))
    add(p('At a low output voltage and high current the secondary is a single '
          'heavy turn and the core comes out large, which can lose against '
          'a height or footprint limit. The transformer can then be built as '
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
          'absorbs switching ripple and nothing else. Making it large is not '
          'conservative: it holds charge across the zero crossing and '
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
          'On the specification below the two come out close, and loosening '
          '&Delta;v to 10&nbsp;%% would hand the decision to hold-up '
          'instead.' % {}))
    add(fig('f19_cout_criterion',
            'Both sizing conditions fall as 1/V<sub>out</sub>&sup2;, so only '
            'the specification separates them. Right: hold-up asks for the '
            'same energy either side of the boost stage &mdash; what changes '
            'is the capacitance that holds it.'))
    ext(bullets([
        'Include the <b>2f<sub>l</sub> component</b> in the ripple current. '
        'The switching-frequency part alone is well short of the truth: the '
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
        'the device by roughly a tenth, because the magnetising current is '
        'missing from it.',
        'Divide currents by the number of devices actually in parallel before '
        'judging stress. Tabulated currents are <b>per switch position</b> on '
        'the primary and <b>per leg</b> on the secondary; a centre-tapped leg '
        'carries the whole secondary current, not half of it.',
        'Compute loss from R<sub>DS(on)</sub> at <b>T<sub>j,max</sub></b>, '
        'not at 25&nbsp;&deg;C. The datasheet maximum is process spread at '
        '25&nbsp;&deg;C; temperature is a separate multiplier, roughly 1.8 '
        'for a 600&nbsp;V superjunction device and 1.9 for a low-voltage '
        'synchronous rectifier. Using the 25&nbsp;&deg;C value to size a '
        'heatsink is optimistic by about a factor of two.',
        'A curve plotted against T<sub>a</sub> may still be read as '
        'T<sub>j</sub> <b>if it is a pulse test</b> &mdash; the die does not '
        'self-heat during the pulse. For any non-pulsed curve this is not '
        'valid.']))
    add(note('<b>The standing device in half-bridge morphing is the one to '
             'watch.</b> It never switches, so it is easy to overlook, and it '
             'carries the whole tank current continuously. On a design of '
             'this power it is where the conduction-loss budget is either met '
             'or knowingly missed, and Section&nbsp;'
             + SR('Where the power goes') + ' shows which of the two happened '
             'here.'))

    add(h2('Controller network'))
    add(fig('bom_pin_config',
            'The controller and its passive network. HVSU is fed from the AC '
            'side of the bridge; the auxiliary winding drives ZCD through a '
            'divider; R<sub>T</sub> and C<sub>T</sub> set the oscillator '
            'limits; R<sub>CFG</sub> and R<sub>BM</sub> are read at power-up.',
            width=CW))
    add(p('Decide first what the auxiliary winding is for, because it '
          'changes one of the rules below. In the usual arrangement it does '
          'two jobs &mdash; it senses the zero crossing and it supplies '
          'V<sub>CC</sub> &mdash; and the second job caps its turns ratio, '
          'since the rectified auxiliary voltage at OVP2 must stay under the '
          'V<sub>CC</sub> rating. That cap is often the binding constraint on '
          'the winding. Where V<sub>CC</sub> is supplied from elsewhere, as it '
          'is here, the cap does not exist: the winding senses only, its '
          'voltage is set by whatever ratio the ZCD divider is designed '
          'around, and the sole remaining constraint is that the turns come '
          'out whole. A ratio check carried over from the self-supplied case '
          'will read as a failure in that arrangement and should be marked '
          'not applicable rather than satisfied.'))
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
          'inside, and this is easy to miss because the two live in different '
          'documents. Since f<sub>o</sub> = 1/(2&pi;&radic;(L<sub>open</sub>'
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
    add(fig('comp_network_st',
            'The secondary-side error amplifier and the optocoupler. '
            'R<sub>I</sub> and R<sub>O</sub> set the regulated output, '
            'R<sub>f</sub>C<sub>f</sub> and C<sub>fo</sub> shape the '
            'compensator, and R<sub>P</sub> and R<sub>B</sub> bias the shunt '
            'regulator and the optocoupler diode.',
            width=CW * 0.68))
    add(p('The output is a capacitor fed by a constant-power source, so the '
          'control-to-output transfer is a <b>pure integrator</b>: '
          '&minus;90&deg; at every frequency. That makes the loop easy to '
          'compensate and hard to place, because the crossover is set by a '
          'constraint that has nothing to do with stability.'))
    add(p('Any 2f<sub>l</sub> ripple that survives the loop and reaches the '
          'feedback pin becomes a power command that varies over the line '
          'cycle, and therefore input current distortion &mdash; mostly third '
          'harmonic. Raising the crossover reduces output ripple and '
          '<b>increases</b> distortion. The two constraints pull in opposite '
          'directions, and the practical answer is in the high teens of '
          'hertz.'))
    add(p('The compensator is a Type&nbsp;II network placed by the Venable '
          'K-factor method. With &alpha;<sub>v</sub> the ratio between the '
          'error-amplifier gain at 2f<sub>l</sub> and the gain the loop needs '
          'there,'))
    add(eq(r'K_{v}=\frac{1}{2\alpha_{v}}\left[(1+\alpha_{v}^{2})\tan\Phi_{M}'
           r'+\sqrt{(1+\alpha_{v}^{2}\tan\Phi_{M})^{2}'
           r'+4\alpha_{v}^{2}}\;\right]', key='Kv'))
    add(p('K<sub>v</sub> puts the zero and the pole the same factor either '
          'side of the crossover. That is what lands the phase bump where it '
          'is needed:'))
    add(eq(r'f_{MB}=\frac{1}{2\pi}\sqrt{\frac{G_{o}K_{v}EA_{o}}{\Gamma_{v}}},'
           r'\qquad f_{p}=K_{v}f_{MB},\qquad f_{z}=\frac{f_{MB}}{K_{v}}', key='fMB'))
    add(p('f<sub>MB</sub> is the point they sit around: the zero goes below '
          'it and the pole above it, by the same factor. A third pole '
          'f<sub>px</sub> is added near a kilohertz to roll off switching '
          'noise.'))

    add(h2('Gain margin, and why it needs checking'))
    add(p('Phase margin alone does not close the stability argument. Above '
          'f<sub>px</sub> this network has one zero against two poles, so the '
          'phase heads for &minus;270&deg; and <b>&minus;180&deg; is crossed '
          'at a finite frequency</b>. That crossing needs no root search '
          'either: setting the zero and pole phase contributions equal and '
          'taking the tangent of both sides leaves one square root,'))
    add(eq(r'f_{180}=\sqrt{\,f_{p}f_{px}-f_{z}(f_{p}+f_{px})\,}'
           r'\,,\qquad GM=-20\log_{10}|T(f_{180})|', key='f180'))
    add(p('<b>A negative value under the root is the answer, not an '
          'error.</b> It means the phase never reaches &minus;180&deg;, so '
          'the gain margin is '
          'infinite. Judge the result against 6&nbsp;dB as a floor and '
          '10&nbsp;dB as a comfortable target. With a crossover in the tens '
          'of hertz the margin is usually large in this topology &mdash; '
          'which is a reason to compute it, not a reason to assume it.'))

    add(h2('Feedback ripple against the burst threshold'))
    add(p('A crossover this low leaves 2f<sub>l</sub> ripple on the feedback '
          'pin. Because that pin is a power command, the ripple walks the '
          'commanded power up and down every half line cycle; if it straddles '
          'the burst-entry threshold the converter chatters in and out of '
          'burst. The ripple amplitude at the burst point is'))
    add(eq(r'\Delta V_{FB}\;=\;\frac{P_{in,BM}}{V_{out}}\,'
           r'\frac{1}{2\pi f_{l}\,C_{out}}\;G_{EA}(2f_{l})', key='dVFB'))
    add(p('Lowering R<sub>BM</sub> by &Delta;R<sub>BM</sub> = '
          '&Delta;V<sub>FB</sub>/(2&nbsp;&times;&nbsp;0.01&nbsp;V/k&Omega;) '
          'moves the burst entry point below that ripple. <b>Raising the '
          'crossover would shrink the ripple but worsen the distortion</b>, '
          'so trading it against R<sub>BM</sub> is the practical answer '
          'rather than speeding up the loop.'))

    add(fig('an_loop_bode',
            'Open-loop gain and phase margin of the selected compensation '
            'network.', width=CW * 0.72))
    add(note('<b>A loop this slow cannot recover from a large load step.</b> '
             'The controller&rsquo;s anti-saturation circuit does that '
             'instead, which is why the optocoupler bias resistor must sit '
             'inside its permitted window. Checking the window is not '
             'optional.'))

    # =============================================================== 6
    add(h1('Design example'))
    add(p('Everything so far is method: what each quantity is, which '
          'equation gives it, and what goes wrong if it is worked out the '
          'wrong way.'))
    add(p('Here are the numbers. One design runs from the specification down '
          'to component values. Each value names the equation it came from '
          'and shows the inputs put into it, so the arithmetic can be '
          'checked. The specification is <b>90 to %(Vacmax).0f&nbsp;Vac in, '
          '%(Vout).0f&nbsp;V / %(Iout).1f&nbsp;A = %(Pout).1f&nbsp;W out</b>, '
          'centre-tapped synchronous rectification, no bulk capacitor and no '
          'boost stage.' % V))

    add(h2('The specification, sorted by what kind of number it is'))
    add(p('A specification sheet usually runs all of its numbers together in '
          'one table, and that is where a good deal of later trouble starts. '
          'Four different kinds of quantity are in there. Some are imposed '
          'from outside and cannot be traded. Some were chosen by the '
          'designer and could have been chosen otherwise. Some are '
          'assumptions standing in for a measurement nobody has made yet. '
          'And some are simply what the first three produce. They are kept '
          'apart here, because the only useful question about a number '
          '&mdash; can I move it? &mdash; has a different answer in each '
          'group.'))

    add(tbl('Set by the load and the mains. Not the designer&rsquo;s to '
            'change.',
            [['Item', 'Symbol', 'Value'],
             ['Mains input', 'V<sub>ac</sub>, f<sub>l</sub>',
              '90 to %(Vacmax).0f Vac, %(flmin).0f to %(flmax).0f Hz' % V],
             ['Output', 'V<sub>out</sub>, I<sub>out</sub>',
              '%(Vout).0f V, %(Iout).1f A  (%(Pout).1f W)' % V],
             ['Output ripple, 2f<sub>l</sub> pk-pk', '&Delta;v',
              '&le; %(dv).0f %% of V<sub>out</sub>' % V],
             ['Hold-up', 'T<sub>hold</sub>, V<sub>o,min</sub>',
              '%(Thold).0f ms down to %(Vomin).0f V, at 100 Vac, worst line '
              'phase' % V]],
            widths=[CW * 0.42, CW * 0.18, CW * 0.40], key='spec-given'))
    add(p(('Two of these four carry a qualifier that is easy to drop and '
           'expensive to drop. <b>The worst line frequency is the lowest</b>, '
           'because the longest line period gives the largest ripple and the '
           'shortest hold-up, so everything that depends on f<sub>l</sub> '
           'uses %(flmin).0f&nbsp;Hz here, not 50 or 60. And '
           '<b>hold-up is specified at the worst line phase</b>, which means '
           'the bank starts half a ripple below nominal rather than at '
           'V<sub>out</sub> &mdash; worth %(pc).0f&nbsp;%% of the ride-out '
           'time here, as Section&nbsp;%(ref)s shows.')
          % dict(V, pc=100 * (1 - V['thold'] / V['tholdVo']),
                 ref=SR('The output bank, as sized'))))

    add(tbl('Chosen here. Each could have been chosen differently; the '
            'section named is where that shows up.',
            [['Item', 'Symbol', 'Value', 'Consequence'],
             ['Secondary rectifier', 'N<sub>rect</sub>',
              '1 (centre tap, SR)',
              'halves the secondary conduction loss; doubles the device '
              'reverse voltage'],
             ['Target series resonance', 'f<sub>r</sub>',
              '%(frt).0f kHz' % V,
              'sets the magnetics size and, with C<sub>r</sub>, fixes '
              'L<sub>r</sub>'],
             ['Specified maximum f<sub>sw</sub>', 'f<sub>sw,max</sub>',
              '%(fswspec).0f kHz' % V,
              'a 1.5 &times; f<sub>r</sub> convention, and it is what sets '
              '&lambda; &mdash; Section&nbsp;'
              + SR('f<sub>sw,max</sub> does not check the tank '
                   '&mdash; it computes it')],
             ['Bridge dead time', 't<sub>D</sub>', '%(tD).0f ns' % V,
              'the time the ZVS sweep has to beat'],
             ['V<sub>CC</sub> source', '&mdash;', 'external 12 V rail',
              'removes the turns-ratio ceiling on the auxiliary winding']],
            widths=[CW * 0.22, CW * 0.13, CW * 0.20, CW * 0.45],
            key='spec-chosen'))

    add(tbl('Assumed, in place of a measurement. Replace each one from the '
            'first prototype.',
            [['Item', 'Symbol', 'Assumed', 'If it is wrong'],
             ['LLC stage efficiency', '&eta;<sub>HB</sub>',
              '%(etaHB).0f %%' % V,
              'R<sub>CS</sub> and R<sub>ac</sub> move by about 3 % for a '
              '95 % outcome &mdash; nothing downstream is sensitive'],
             ['Rectifier forward drop', 'N<sub>rect</sub>V<sub>f</sub>',
              '0 V',
              'a synchronous rectifier drops I&thinsp;R<sub>DS(on)</sub>, '
              'carried in the loss budget rather than in the reflected '
              'voltage'],
             ['Oscillator idle time', 'T<sub>idle</sub>',
              '%(Tidle).0f ns' % V,
              'the draft datasheet also says 700 ns, which would close the '
              'floor margin entirely &mdash; the first thing to measure'],
             ['R<sub>DS(on)</sub> temperature factor',
              'k<sub>T</sub>', '%(Rdpk).1f / %(Rdsk).1f' % V,
              'primary / secondary, read off datasheet curves at '
              'T<sub>j,max</sub>; a wrong factor mis-sizes the heatsink '
              'directly'],
             ['Burst entry point', 'r<sub>BM</sub>',
              '%(PinBM).0f W (%(rBM).0f %% of rated)'
              % dict(V, rBM=A.SH['r.BM'] * 100),
              'sets R<sub>BM</sub>, which then has to be checked against '
              'the feedback ripple']],
            widths=[CW * 0.22, CW * 0.13, CW * 0.16, CW * 0.49],
            key='spec-assumed'))

    add(tbl('Follows from the three tables above &mdash; arithmetic, not '
            'input.',
            [['Item', 'Symbol', 'Value', 'From'],
             ['Output ripple in volts', '&Delta;v<sub>pp</sub>',
              '%(dVo).2f V' % V, '%(dv).0f %% of %(Vout).0f V' % V],
             ['Reflected output voltage', 'V<sub>o,eff</sub>',
              '%(Vout).1f V' % V,
              'V<sub>out</sub> + N<sub>rect</sub>V<sub>f</sub>, with '
              'V<sub>f</sub> = 0'],
             ['Rated input power', 'P<sub>in</sub>', '%(Pin).1f W' % V,
              'P<sub>out</sub> through the bridge, EMI and LLC loss budgets'],
             ['Overall efficiency', '&eta;<sub>tot</sub>',
              '%(eta).2f %%' % V, 'P<sub>out</sub>/P<sub>in</sub>'],
             ['Equivalent input range', 'V<sub>ac,eq</sub>',
              '%(Veqlo).1f to %(Veqhi).1f Vac' % V,
              'the morphing edges, not the mains range &mdash; next section']],
            widths=[CW * 0.24, CW * 0.13, CW * 0.18, CW * 0.45],
            key='spec-derived'))

    add(h2('What the design came out as'))
    add(tbl('Principal values.',
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
    add(p('Every check has the same shape. Take what the design gets, '
          'X<sub>act</sub>, divide it by what the design needs, '
          'X<sub>req</sub>, and call the answer k:'))
    add(eq(r'k\;=\;\frac{X_{\mathrm{act}}}{X_{\mathrm{req}}}\qquad\Longrightarrow\qquad \mathrm{pass\;when}\;k>1', key='margin'))
    add(p('That is the whole definition. k&nbsp;=&nbsp;1.05 is five per cent '
          'of room, k&nbsp;=&nbsp;0.9 is ten per cent short, and the number '
          'is read directly as a factor rather than as a difference.'))
    add(p('Why force every check into the same shape? Because the raw '
          'quantities do not agree on which way is good. T<sub>ZC</sub> '
          'should be <i>large</i>. f<sub>o</sub> should be <i>small</i>. A '
          'loss should be small, a hold-up time long. As raw numbers, a '
          'reviewer has to remember the direction of each one.'))
    add(p('As ratios they all point the same way, and they have no units. So '
          'a frequency check and a power check can sit in the same column '
          'and be compared. The smallest k in the table is the thinnest part '
          'of the design, whatever it happens to be about.'))
    _kb = V['kPloss'] * A.SH['P.mos_dc']          # the budget, recovered
    _ks = V['kPSR'] * A.SH['P.SR'] / 2.0
    add(tbl('The verification margins, and the ratio each one is.',
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
    add(note('<b>k below 1 is a result, not a failed build.</b> '
             'k<sub>Ploss</sub> = %(kPloss).3f says the standing primary '
             'device spends %(a).2f&nbsp;W against a %(b).0f&nbsp;W budget. '
             'The budget is itself a choice, so the ratio could be made to '
             'pass by writing %(c).0f&nbsp;W into the numerator &mdash; at '
             'which point the check stops checking anything. It is left as it '
             'is, and Section&nbsp;%(ref)s says why the design goes ahead '
             'anyway.'
             % dict(V, a=A.SH['P.mos_dc'], b=_kb,
                    c=A.SH['P.mos_dc'] * 1.05,
                    ref=SR('Semiconductor requirements'))))
    add(note('<b>Do not read two of these as percentages.</b> '
             'k<sub>floor</sub> = %(kfloor).3f looks like a safe '
             '2&nbsp;%%. But two things move it &mdash; the transformer '
             'open-circuit tolerance and the oscillator idle time &mdash; '
             'and neither is known to 2&nbsp;%% yet. k<sub>ZVS</sub> is the '
             'same: its numerator came from a sweep, not a formula. The rest '
             'of the table is arithmetic on values that are already fixed.'
             % V))

    # ------------------------------------------------ the chain, step by step
    add(h2('Following the numbers through'))
    add(p('The table above is the destination. This is the road: every '
          'quantity in the order it was actually computed, with what it was '
          'computed from. Read down the &ldquo;from&rdquo; column and it is '
          'a chain &mdash; nothing in it appears before the things it needs, '
          'which is the whole reason the design procedure is in that order.'))
    add(tbl('The design, step by step.',
            [['#', 'Quantity', 'Value', 'Eq.', 'From'],
             ['1', 'Input power P<sub>in</sub>', '%(Pin).1f W' % V, '&mdash;',
              'P<sub>out</sub> %(Pout).1f W plus the bridge, EMI and LLC '
              'loss budgets' % V],
             ['2', 'Power into the tank P<sub>in,LLC</sub>',
              '%(PinLLC).1f W' % dict(V, PinLLC=A.SH['P.in_LLC']),
              '&mdash;',
              'P<sub>in</sub> less the bridge and EMI budgets'],
             ['3', 'Equivalent input, low corner', '%(Veqlo).1f Vac' % V,
              ER('Veq'),
              '245 V<sub>pk</sub> in half bridge, &divide;&radic;2'],
             ['4', 'Equivalent input, high corner', '%(Veqhi).1f Vac' % V,
              ER('Veq'),
              '235 V<sub>pk</sub> in full bridge, &times;2&divide;&radic;2'],
             ['5', 'Turns ratio n', '%(n).3f' % V,
              ER('nnT'),
              'chosen with L<sub>m</sub> so that n<sub>T</sub> lands on a '
              'windable ratio &mdash; the plain calculation gives '
              '%(ncalc).3f' % dict(V, ncalc=A.SH['n.calc'])],
             ['6', 'Reflected voltage', '%(Vrefl).1f V' % V,
              ER('Vrefl'),
              'n V<sub>o,eff</sub>'],
             ['7', 'Gain demanded at the low corner',
              '%(Mhb).4f' % dict(V, Mhb=A.SH['M.HBmin']),
              ER('Mreq'),
              '2 n V<sub>o,eff</sub> / (&radic;2 &times; %(Veqlo).1f)' % V],
             ['8', 'Gain demanded at the high corner',
              '%(Mfb).4f' % dict(V, Mfb=A.SH['M.FBthr']),
              ER('Mreq'),
              'the same expression at %(Veqhi).1f Vac' % V],
             ['9', 'AC load resistance R<sub>ac</sub>',
              '%(Rac).2f &Omega;' % V,
              ER('Rac'),
              '(4/&pi;&sup2;) n&sup2; V<sub>o,eff</sub>&sup2; / '
              'P<sub>in,LLC</sub> &mdash; the 4 is the line peak'],
             ['10', 'Quality-factor cap Q<sub>ZVS</sub>',
              '%(QZVS).4f' % V,
              ER('zvs'),
              'the smaller of the gain and ZVS limits at the low corner'],
             ['11', 'Design impedance', '%(Z0).2f &Omega;' % V,
              '&mdash;',
              'R<sub>ac</sub> Q<sub>ZVS</sub>'],
             ['12', 'C<sub>r</sub>', '%(Crc).2f &rarr; %(Cr).0f nF' % V,
              ER('fr'),
              '1/(2&pi; f<sub>r</sub> &times; design impedance), then '
              'rounded up hard to buy Q margin'],
             ['13', 'L<sub>r</sub>', '%(Lrc).2f &rarr; %(Lr).0f &micro;H' % V,
              ER('fr'),
              'whatever pairs with the selected C<sub>r</sub> at '
              'f<sub>r</sub> = %(frt).0f kHz' % V],
             ['14', '&lambda; required', '%(lamTD).3f' % V,
              ER('lam'),
              'the largest of four candidates &mdash; two of them carry '
              'f<sub>sw,max</sub> in a denominator'],
             ['15', 'L<sub>m</sub>', '%(Lmc).2f &rarr; %(Lm).0f &micro;H' % V,
              '&mdash;',
              'not that ratio: chosen with n, knowingly missing the no-load '
              'condition'],
             ['16', 'Realised &lambda;<sub>act</sub>', '%(lam).3f' % V,
              '&mdash;',
              'L<sub>r</sub>/L<sub>m</sub> of the selected parts'],
             ['17', 'Realised f<sub>r</sub>, f<sub>o</sub>',
              '%(fr).1f / %(fo).1f kHz' % V,
              ER('fr') + ', ' + ER('fo'),
              'from C<sub>r</sub>, L<sub>r</sub> and L<sub>r</sub>+'
              'L<sub>m</sub>'],
             ['18', 'Realised Q<sub>pk</sub>', '%(Qpk).3f' % V,
              ER('M'),
              '&radic;(L<sub>r</sub>/C<sub>r</sub>) = %(Z0s).2f &Omega;, '
              'divided by R<sub>ac</sub> &mdash; well under the cap' % V],
             ['19', 'Physical turns ratio n<sub>T</sub>', '%(nT).3f' % V,
              ER('nnT'),
              'n &radic;(1+&lambda;<sub>act</sub>), landing on %(NpSet)d:'
              '%(Ns)d' % V]],
            widths=[CW * 0.055, CW * 0.22, CW * 0.165, CW * 0.06,
                    CW * 0.50],
            key='chain'))
    add(p('Six of those rows do the real work, and they are worth seeing '
          'opened out. Each one is the equation named beside it, with this '
          'design&rsquo;s numbers put in:'))
    ext(bullets([
        '<b>Row 5, the turns ratio.</b> Equation&nbsp;%(e)s is inverted: '
        'n&nbsp;=&nbsp;n<sub>T</sub>/&radic;(1+&lambda;<sub>act</sub>) '
        '&nbsp;=&nbsp; %(nT).3f/&radic;(1+%(lam).3f) &nbsp;=&nbsp; '
        '%(nT).3f/%(rt).4f &nbsp;=&nbsp; <b>%(n).3f</b>. The wound ratio is '
        'the input here, not the output, because %(NpSet)d:%(Ns)d is what can '
        'be built.' % dict(V, e=ER('nnT'), rt=(1 + V['lam']) ** 0.5),
        '<b>Row 7, the gain the tank is asked for.</b> Equation&nbsp;%(e)s '
        'at &theta;&nbsp;=&nbsp;90&deg;: M&nbsp;=&nbsp;2&thinsp;n&thinsp;'
        'V<sub>o,eff</sub>/(&radic;2&thinsp;V<sub>ac,eq</sub>) &nbsp;=&nbsp; '
        '2&times;%(n).3f&times;%(Vout).1f / (1.4142&times;%(Veqlo).2f) '
        '&nbsp;=&nbsp; %(num).1f/%(den).1f &nbsp;=&nbsp; <b>%(M).4f</b>.'
        % dict(V, e=ER('Mreq'), num=2 * V['n'] * V['Vout'],
               den=2 ** 0.5 * V['Veqlo'], M=A.SH['M.HBmin']),
        '<b>Row 9, the load the tank sees.</b> Equation&nbsp;%(e)s: '
        'R<sub>ac</sub>&nbsp;=&nbsp;(4/&pi;&sup2;)&thinsp;n&sup2;&thinsp;'
        'V<sub>o,eff</sub>&sup2;/P<sub>in,LLC</sub> &nbsp;=&nbsp; '
        '0.4053&times;%(n2).2f&times;%(Vo2).0f / %(PL).1f &nbsp;=&nbsp; '
        '<b>%(Rac).2f&nbsp;&Omega;</b>. Note the 4, not the textbook 8: '
        'P<sub>in,LLC</sub> is the line-peak power.'
        % dict(V, e=ER('Rac'), n2=V['n'] ** 2, Vo2=V['Vout'] ** 2,
               PL=A.SH['P.in_LLC']),
        '<b>Row 12, the resonant capacitor.</b> The design impedance and the '
        'target f<sub>r</sub> give it through equation&nbsp;%(e)s rearranged: '
        'C<sub>r</sub>&nbsp;=&nbsp;1/(2&pi;&thinsp;f<sub>r</sub>&thinsp;'
        'R<sub>ac</sub>Q<sub>ZVS</sub>) &nbsp;=&nbsp; '
        '1/(2&pi;&times;%(frt)s&nbsp;kHz&times;%(Z0).2f&nbsp;&Omega;) &nbsp;=&nbsp; '
        '%(Crc).2f&nbsp;nF, taken to <b>%(Cr).0f&nbsp;nF</b>.'
        % dict(V, e=ER('fr'), frt='%.0f' % V['frt']),
        '<b>Row 13, the resonant inductor.</b> Same equation, now solved for '
        'L with the <i>selected</i> C<sub>r</sub>: L<sub>r</sub>&nbsp;=&nbsp;'
        '1/((2&pi;f<sub>r</sub>)&sup2;C<sub>r</sub>) &nbsp;=&nbsp; '
        '1/((2&pi;&times;%(frt)s&nbsp;kHz)&sup2;&times;%(Cr).0f&nbsp;nF) &nbsp;=&nbsp; '
        '%(Lrc).2f&nbsp;&micro;H, taken to '
        '<b>%(Lr).0f&nbsp;&micro;H</b>. This is why L<sub>r</sub> is not '
        'R<sub>ac</sub>Q<sub>ZVS</sub>/2&pi;f<sub>r</sub>: C<sub>r</sub> '
        'moved first.' % dict(V, e=ER('fr'), frt='%.0f' % V['frt']),
        '<b>Row 18, the quality factor the tank actually runs at.</b> '
        'Z<sub>0</sub>&nbsp;=&nbsp;&radic;(L<sub>r</sub>/C<sub>r</sub>) '
        '&nbsp;=&nbsp; &radic;(%(Lr).0f&nbsp;&micro;H / %(Cr).0f&nbsp;nF) &nbsp;=&nbsp; '
        '%(Z0s).2f&nbsp;&Omega;, and '
        'Q<sub>pk</sub>&nbsp;=&nbsp;Z<sub>0</sub>/R<sub>ac</sub> '
        '&nbsp;=&nbsp; %(Z0s).2f/%(Rac).2f &nbsp;=&nbsp; <b>%(Qpk).3f</b>, '
        'against the %(QZVS).3f cap of row 10.' % dict(V, e=ER('M')),
    ]))
    add(note('<b>Steps 12, 15 and 18 are where the judgement is.</b> '
             'Everything else in that table is arithmetic that any two '
             'engineers would reproduce identically. C<sub>r</sub> was taken '
             'to %(Cr).0f&nbsp;nF against a calculated %(Crc).1f&nbsp;nF and '
             'L<sub>m</sub> to %(Lm).0f&nbsp;&micro;H against a calculated '
             '%(Lmc).1f&nbsp;&micro;H, and the two together are why the tank '
             'runs at Q<sub>pk</sub> = %(Qpk).3f instead of at the '
             '%(QZVS).3f cap. That gap is most of the ZVS margin this design '
             'has.' % V))

    # ------------------------------------------------ transformer as built
    add(tbl('T<sub>ZC</sub> [ns] over the operating space, selected tank. The '
            'dead time is %(tD).0f ns.' % V,
            _zvs_grid(A),
            widths=[CW * 0.16] + [CW * 0.168] * 5, key='zvs',
            align={1: 'CENTER', 2: 'CENTER', 3: 'CENTER', 4: 'CENTER',
                   5: 'CENTER'}))
    add(h2('ZVS over the whole operating space'))
    add(p('The closed form of Section&nbsp;' + SR('ZVS verification') + ' reads %(TzcCF).0f&nbsp;ns on this tank against a swept %(Tzc).0f&nbsp;ns, so it understates the margin by %(mag).0f&nbsp;%%; on another tank in the same family it overstates by about 23&nbsp;%%. Read with &lambda;<sub>act</sub>&nbsp;=&nbsp;%(lam).3f instead of the design &lambda;&nbsp;=&nbsp;%(lamreq).3f it returns %(TzcCFact).0f&nbsp;ns &mdash; capacitive, for a tank that is well inside the inductive region. So the sweep is what this design is held to.'
          % dict(V, mag=abs(V['TzcCFpc']), lamreq=A.SH['λ'])))
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
                 'so that current falls even though the node still has the '
                 'same capacitance to move. Whether this beats the '
                 'full-load corner depends on the tank: it does not on a '
                 'high turns ratio, where the design already sits deep '
                 'below resonance, and it does on a lower one. <b>Sweeping '
                 'only the design corner will therefore report a margin '
                 'that is not there</b>, which is the same trap as trusting '
                 'the closed form.'))

    add(h2('Which side of resonance this design runs on'))
    add(p('Section&nbsp;' + SR('Which side of resonance the converter runs on') + ' says the turns ratio decides this. With '
          'n<sub>T</sub>&nbsp;=&nbsp;%(nT).2f the answer is below. At all '
          'but the lowest line conditions the tank spends part of every line '
          'cycle above f<sub>r</sub>. There the secondary loses zero-current '
          'turn-off, so the rectifier body diode and the SR dead time both '
          'need checking.' % V))
    add(tbl('Peak f<sub>sw</sub> over the half cycle against f<sub>r</sub> = '
            '%(fr).1f kHz. %(nAbove)d of the seven line conditions cross into '
            'above-resonance operation for part of the cycle.' % V,
            [['Line condition', 'V<sub>eq</sub>', 'peak f<sub>sw</sub>',
              'side of f<sub>r</sub>']]
            + [[nm, '%.0f V' % veq, '%.1f kHz' % pk,
                '<b>above</b>' if ab else 'below']
               for nm, veq, pk, ab in V['fswPk']],
            widths=[CW * 0.30, CW * 0.18, CW * 0.22, CW * 0.30]))
    add(h2('The currents this design has to carry'))
    add(p('Ratings come from the worst switching cycle and losses from the '
          'line-cycle rms, so both are listed and they are different numbers. '
          'The row to watch is the composite tank peak: it is what the '
          'primary devices and R<sub>CS</sub> actually see, and it is neither '
          'the sum of the two component peaks nor the larger of them.'))
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

    add(tbl('Tank: calculated against selected.',
            [['Quantity', 'Calculated', 'Selected', 'Direction'],
             ['C<sub>r</sub>', '%(Crc).2f nF' % V, '%(Cr).0f nF' % V,
              'rounded <b>up</b>'],
             ['L<sub>r</sub>', '%(Lrc).2f &micro;H' % V,
              '%(Lr).0f &micro;H' % V, 'rounded down'],
             ['L<sub>m</sub>', '%(Lmc).2f &micro;H' % V,
              '%(Lm).0f &micro;H' % V, '<b>not a rounding</b> &mdash; see '
              'below'],
             ['&lambda;<sub>act</sub> / f<sub>r</sub> / f<sub>o</sub>',
              '&mdash;',
              '%(lam).3f / %(fr).1f kHz / %(fo).1f kHz' % V,
              'from the selected parts']],
            widths=[CW * 0.26, CW * 0.20, CW * 0.28, CW * 0.26]))
    add(h2('The transformer, as built'))
    add(p('The tank asks for L<sub>r</sub> = %(Lr).0f&nbsp;&micro;H, '
          'L<sub>m</sub> = %(Lm).0f&nbsp;&micro;H and n<sub>T</sub> = '
          '%(nT).2f. At %(Iout).1f&nbsp;A out the secondary wants to be one '
          'or two heavy turns, and a single core that can carry the flux at '
          'that few turns comes out too large for the enclosure. This design '
          'therefore uses %(nser)d identical units, primaries in series and '
          'secondaries in parallel, as Section&nbsp;%(ref)s describes.'
          % dict(V, ref=SR('If one transformer is not practical'))))
    add(tbl('The transformer as it is actually wound and specified.',
            [['Quantity', 'Per unit', 'Assembly', 'Note'],
             ['Turns', '%(Np)d : %(Ns)d' % V, '%(NpSet)d : %(Ns)d' % V,
              'primaries in series, secondaries in parallel'],
             ['Open-circuit inductance',
              '%(Lu).1f &micro;H' % dict(V, Lu=V['Lopen'] / V['nser']),
              '%(Lopen).1f &micro;H' % V,
              'L<sub>r</sub> + L<sub>m</sub>, measured with every other '
              'winding open'],
             ['Short-circuit inductance',
              '%(Ls).2f &micro;H' % dict(V, Ls=V['Lshort'] / V['nser']),
              '%(Lshort).1f &micro;H' % V,
              'this is L<sub>r</sub>: no separate resonant inductor'],
             ['A<sub>L</sub>', '%(AL).0f nH' % V, '&mdash;',
              'open-circuit inductance / N<sub>p</sub>&sup2;'],
             ['Peak flux density', '%(Bpk).0f mT' % V, '&mdash;',
              'V<sub>o,eff</sub>/(4 f<sub>r</sub> N<sub>s</sub> '
              'A<sub>e</sub>) &mdash; N<sub>p</sub> does not enter'],
             ['Core area', '&ge; %(Aereq).0f mm&sup2;' % V,
              '&mdash;', 'to hold B<sub>pk</sub> at 0.20 T; EE6405 offers '
              '%(Aemm).0f mm&sup2;, a factor of %(kAe).3f' % V],
             ['Saturation test current', '%(Isatspec).1f A' % V, '&mdash;',
              'flux-equivalent %(Isateq).1f A rounded up, <b>not</b> the '
              '%(Icomp).1f A tank peak' % V]],
            widths=[CW * 0.24, CW * 0.15, CW * 0.15, CW * 0.46],
            key='trafo-built'))
    add(p('Three of those rows are computed rather than specified, and this '
          'is the arithmetic:'))
    ext(bullets([
        '<b>Peak flux.</b> Equation&nbsp;%(e)s, at f<sub>r</sub> because that '
        'is the worst case anywhere on the line cycle: B<sub>pk</sub>'
        '&nbsp;=&nbsp;V<sub>o,eff</sub>/(4&thinsp;f<sub>r</sub>'
        '&thinsp;N<sub>s</sub>&thinsp;A<sub>e</sub>) &nbsp;=&nbsp; '
        '%(Vout).1f&nbsp;V/(4&times;%(fr).2f&nbsp;kHz&times;%(Ns)d&times;'
        '%(Aemm).1f&nbsp;mm&sup2;) &nbsp;=&nbsp; '
        '<b>%(Bpk).0f&nbsp;mT</b>. N<sub>p</sub> is absent, which is the '
        'whole point of that equation.' % dict(V, e=ER('Bpk')),
        '<b>Core area needed.</b> The same equation solved for A<sub>e</sub> '
        'at B<sub>max</sub>&nbsp;=&nbsp;0.20&nbsp;T: A<sub>e</sub>'
        '&nbsp;&ge;&nbsp;%(Vout).1f&nbsp;V/(4&times;%(fr).2f&nbsp;kHz&times;'
        '%(Ns)d&times;0.20&nbsp;T) &nbsp;=&nbsp; <b>%(Aereq).0f&nbsp;mm&sup2;</b>. '
        'EE6405 gives %(Aemm).1f, so the margin is %(kAe).3f &mdash; and '
        'halving N<sub>s</sub> would double the requirement to '
        '%(Ae2).0f&nbsp;mm&sup2;, which EE6405 does not meet.'
        % dict(V, Ae2=2 * V['Aereq']),
        '<b>Saturation test current.</b> Equation&nbsp;%(e)s, per unit: '
        'I<sub>eq</sub>&nbsp;=&nbsp;B<sub>pk</sub>N<sub>p</sub>A<sub>e</sub>/'
        'L<sub>open</sub> &nbsp;=&nbsp; %(B).4f&nbsp;T&times;%(Np)d&times;'
        '%(Aemm).1f&nbsp;mm&sup2; / %(Lu).2f&nbsp;&micro;H '
        '&nbsp;=&nbsp; %(Isateq).2f&nbsp;A, specified as '
        '<b>%(Isatspec).1f&nbsp;A</b>. The tank peak is %(Icomp).1f&nbsp;A '
        'and handing that over instead would ask for nearly twice the flux.'
        % dict(V, e=ER('Isat'), B=V['Bpk'] / 1e3,
               Lu=V['Lopen'] / V['nser'])]))
    add(note('<b>The quantisation is a constraint on the tank, not a detail '
             'of the build.</b> With %(nser)d units in series the assembly '
             'ratio is %(nser)d&thinsp;N<sub>p</sub>/N<sub>s</sub>, so the '
             'only ratios available are multiples of %(nser)d/N<sub>s</sub>. '
             'n<sub>T</sub> = %(nT).2f exists because %(NpSet)d:%(Ns)d '
             'exists; a tank that had asked for %(nTx).2f could not have been '
             'wound this way at all. That has to be checked while the tank is '
             'being chosen.' % dict(V, nTx=V['nT'] + 0.4)))

    # ------------------------------------------------ output bank as sized
    add(p('Reduced to what a supplier can measure at the terminals, that '
          'becomes the sheet below. Nothing on it is a construction '
          'instruction, and L<sub>&mu;</sub> is deliberately absent &mdash; '
          'Section&nbsp;' + SR('What the transformer specification must say')
          + ' says why.'))
    add(tbl('Transformer specification for the worked design.',
            [['Item', 'Value', 'Condition'],
             ['Turns ratio',
              'N<sub>p</sub> : N<sub>s</sub> = %(NpSet)d : %(Ns)d' % V,
              'two secondary windings, centre tap outside the part'],
             ['Open-circuit inductance',
              '%(Lopen).1f &micro;H, &minus;%(Ldrop).1f %% at worst'
              % V,
              'primary, all other windings open'],
             ['Leakage inductance', '%(Lshort).1f &micro;H &plusmn;10 %%' % V,
              'primary, secondary shorted'],
             ['DC overlap', '&ge; 90 %% of initial inductance' % V,
              'test current %(Isatspec).0f A' % V],
             ['Primary current', '%(Iprilc).1f A rms / %(Icomp).1f A pk' % V,
              'line-cycle rms, composite peak'],
             ['Secondary current, each winding',
              '%(Idio).1f A rms / %(Isec).0f A pk' % V, 'line-cycle rms'],
             ['Core area', 'A<sub>e</sub> &ge; %(Aereq).0f mm&sup2;' % V,
              'holds B<sub>pk</sub> at or below 0.20 T'],
             ['Switching frequency', '%(fswA).0f to %(fswB).0f kHz' % V,
              'at full load']],
            widths=[CW * 0.28, CW * 0.34, CW * 0.38]))
    add(h2('The output bank, as sized'))
    add(p('Both conditions of Section&nbsp;%(ref)s, worked out on the '
          'specification above.'
          % dict(V, ref=SR('The output capacitor bank'))))
    add(tbl('The two sizing conditions, evaluated.',
            [['Condition', 'Asks for', 'Driven by'],
             ['2f<sub>l</sub> ripple &le; %(dv).0f %%' % V,
              '<b>%(Crip).2f mF</b>' % V,
              'I<sub>out</sub>, f<sub>l</sub> = %(flmin).0f Hz and the '
              'allowed &Delta;v &mdash; this one wins' % V],
             ['Hold-up %(Thold).0f ms to %(Vomin).0f V' % V,
              '%(Chold).2f mF' % V,
              'the energy %(Ehold).2f J between the starting voltage and '
              '%(Vomin).0f V, starting at the ripple trough' % V],
             ['Selected', '%(Cout).1f mF' % V,
              '%(Cout1).0f &micro;F &times; %(nC).0f, the next assembly up '
              'from %(Crip).1f mF' % V]],
            widths=[CW * 0.30, CW * 0.18, CW * 0.52], key='bank-sized'))
    ext(bullets([
        '<b>The ripple condition</b>, equation&nbsp;%(e)s: C<sub>out</sub>'
        '&nbsp;&ge;&nbsp;P<sub>out</sub>/(2&pi;f<sub>l,min</sub>&thinsp;'
        '&Delta;v&thinsp;V<sub>out</sub>&sup2;) &nbsp;=&nbsp; '
        '%(Pout).1f&nbsp;W/(2&pi;&times;%(flmin).0f&nbsp;Hz&times;%(dvf).2f&times;'
        '%(Vo2).0f&nbsp;V&sup2;) &nbsp;=&nbsp; <b>%(Crip).2f&nbsp;mF</b>, with &Delta;v '
        'as a fraction and V<sub>out</sub> in volts.'
        % dict(V, e=ER('Crip'), dvf=V['dv'] / 100.0, Vo2=V['Vout'] ** 2),
        '<b>The hold-up condition</b>, equation&nbsp;%(e)s, starting half a '
        'ripple low: C<sub>out</sub>&nbsp;&ge;&nbsp;2P<sub>out</sub>'
        'T<sub>hold</sub>/((V<sub>out</sub>&minus;&frac12;&Delta;v'
        '<sub>pp</sub>)&sup2;&minus;V<sub>o,min</sub>&sup2;) &nbsp;=&nbsp; '
        '2&times;%(Pout).1f&nbsp;W&times;%(Th).3f&nbsp;s/(%(Vs).2f&sup2;&minus;'
        '%(Vomin).0f&sup2;) &nbsp;=&nbsp; <b>%(Chold).2f&nbsp;mF</b>. '
        'Starting at V<sub>out</sub> instead would have asked for only '
        '%(Cnaive).2f&nbsp;mF.'
        % dict(V, e=ER('Chold'), Th=V['Thold'] / 1e3,
               Vs=V['Vout'] - V['dVo'] / 2,
               Cnaive=2 * V['Pout'] * V['Thold'] / 1e3
               / (V['Vout'] ** 2 - V['Vomin'] ** 2) * 1e3)]))
    add(p('The two are only %(ripK).3f apart. That is close, so the '
          'screening inequality is worth carrying. At k = '
          'V<sub>o,min</sub>/V<sub>out</sub> = %(k).3f it reads %(lhs).3f '
          'against %(rhs).3f: the left side is larger, so ripple wins. '
          'Loosen &Delta;v to 10&nbsp;%% and the sides swap.'
          % dict(V, k=V['Vomin'] / V['Vout'], lhs=V['ripLHS'],
                 rhs=V['ripRHS'])))
    add(tbl('What the selected bank then delivers, and what it has to '
            'survive.',
            [['Quantity', 'Value', 'Against'],
             ['Achieved ripple', '%(dVo).2f V (%(dVopc).2f %%)' % V,
              '%(dv).0f %% allowed' % V],
             ['Achieved hold-up', '%(thold).2f ms' % V,
              '%(Thold).0f ms required &mdash; and %(tholdVo).2f ms if it '
              'had been started at V<sub>out</sub> instead of at the '
              'trough' % V],
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
    add(p('The specification allowed %(diff).1f&nbsp;W of loss to get from '
          'P<sub>in</sub> = %(Pin).1f&nbsp;W to P<sub>out</sub> = '
          '%(Pout).1f&nbsp;W. That allowance was split three ways before any '
          'component existed, and the itemised device losses are computed '
          'afterwards. The two do not have to agree, and here they do not.'
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
    add(note('<b>That disagreement is the efficiency assumption being '
             'caught.</b> The itemised device losses already come to '
             '%(t).1f&nbsp;W against the %(b).1f&nbsp;W that '
             '&eta;<sub>HB</sub> = %(etaHB).0f&nbsp;%% allows the LLC stage, '
             'and the transformer is not even in the list. So the assumption '
             'is optimistic, which is why it is filed as an assumption rather '
             'than as a figure. It is not load-bearing: taking 95&nbsp;%% '
             'instead moves R<sub>ac</sub> and R<sub>CS</sub> by about '
             '3&nbsp;%% and nothing downstream is sensitive to that. What it '
             'does change is the thermal design, and that is settled by '
             'measurement rather than by either number.'
             % dict(V, t=A.SH['P.mos_dc'] + A.SH['P.mos_sw'] + A.SH['P.SR']
                    + A.SH['P.RCS'] + A.SH['P.Cout'], b=A.SH['P.d_LLC'])))

    # ------------------------------------------------ the loop as built
    add(h2('What the semiconductors have to be'))
    add(p('Requirements, not part numbers. What to pick depends on package, '
          'thermal design and cost. The four rules of Section&nbsp;'
          + SR('Semiconductor requirements')
          + ' decide whether these are even stated correctly.'))
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
    add(p('Section&nbsp;%(ref)s gives the method. These are the numbers it '
          'produces on this converter, in the order they are found.'
          % dict(V, ref=SR('Voltage loop and compensation'))))
    add(tbl('The compensator, from the plant to the parts.',
            [['#', 'Quantity', 'Value', 'From'],
             ['1', 'Output divider', 'R<sub>I</sub> %(RI).0f k&Omega; / '
              'R<sub>o</sub> %(Ro).0f k&Omega;'
              % dict(RI=A.SH['R.I'], Ro=A.SH['R.o']),
              'sets the regulated output against the '
              '%(VR).3f V reference' % dict(VR=A.SH['V.R'])],
             ['2', 'Plant gain G<sub>o</sub>', '%(Go).2f rad/s' % V,
              'a pure integrator &mdash; the output is a capacitor fed by a '
              'power source'],
             ['3', 'Error-amplifier gain needed at 2f<sub>l</sub>',
              '%(GEA).4f' % dict(GEA=A.SH['G.EA']),
              'what the loop needs there, against what the amplifier has'],
             ['4', 'K factor K<sub>v</sub>', '%(Kv).4f' % V,
              'places the zero and pole symmetrically'],
             ['5', 'Geometric mean f<sub>MB</sub>', '%(fMB).3f Hz' % V,
              'the point they are placed about'],
             ['6', 'Zero / pole', '%(fz).3f / %(fp).3f Hz' % V,
              'f<sub>MB</sub>/K<sub>v</sub> and K<sub>v</sub>f<sub>MB</sub>'],
             ['7', 'High-frequency pole f<sub>px</sub>',
              '%(fpx).1f Hz' % V, 'added to roll off switching noise'],
             ['8', 'Components', 'C<sub>Fo</sub> %(CFo).0f nF, '
              'C<sub>F</sub> %(CF).0f nF, R<sub>F</sub> %(RF).0f k&Omega;, '
              'C<sub>fx</sub> %(Cfx).2f nF' % V,
              'the nearest standard values to the pole and zero above'],
             ['9', 'Optocoupler bias', 'R<sub>P</sub> %(RP).1f k&Omega;, '
              'R<sub>B</sub> %(RB).1f k&Omega;' % V,
              'R<sub>B</sub> must land inside %(lo).2f to %(hi).2f k&Omega; '
              'or the anti-saturation circuit cannot act'
              % dict(lo=A.SH['R.B_min'], hi=A.SH['R.B_max'])]],
            widths=[CW * 0.05, CW * 0.25, CW * 0.26, CW * 0.44],
            key='loop-built'))
    add(tbl('And what that loop then measures as.',
            [['Quantity', 'Value', 'Against'],
             ['Crossover f<sub>cross</sub>', '%(fcross).2f Hz' % V,
              'the high teens of hertz this topology lands in'],
             ['Phase margin', '%(PM).2f&deg;' % V, '45&deg; as a floor'],
             ['Gain margin', '%(GM).2f dB at %(f180).0f Hz' % V,
              '6 dB floor, 10 dB comfortable'],
             ['Third harmonic on the input current', '%(D3).2f %%' % V,
              'the price of crossing this low'],
             ['Feedback ripple at the burst point',
              '%(dVFB).0f mV' % dict(dVFB=V['dVFBBM']),
              'move R<sub>BM</sub> down %(dR).2f k&Omega; to clear it'
              % dict(dR=V['dRBM'])]],
            widths=[CW * 0.36, CW * 0.24, CW * 0.40], key='loop-result'))

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
    add(p('<b>I<sub>EA</sub> is the only actuator in the converter.</b> More '
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
            '%(a).2f and %(b).2f&nbsp;m&Omega;, so the power law binds. '
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
    add(note('<b>Two ways to get this wrong, both of which stop the converter '
             'dead.</b> Swapping the two resistors inverts the ratio and OVP1 '
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
        'whether or not anything has.' % '120',
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

    add(h2('Ten things that go wrong'))
    ext(bullets([
        'Designing the tank for the mains range instead of the <b>equivalent</b> '
        'range. The corners are the morphing edges.',
        'Carrying over &lambda; from a two-stage LLC. '
        'L<sub>m</sub>/L<sub>r</sub> of 5 to 10 will not start at low line.',
        'Putting the oscillator floor below f<sub>o</sub> and relying on the '
        'anti-capacitive protection to catch it.',
        'Checking the turns ratio instead of the reflected voltage, so that '
        'n and n<sub>T</sub> are with no warning interchanged.',
        'Rating the primary switch on the reflected load current rather than '
        'the composite tank peak.',
        'Omitting the 2f<sub>l</sub> component from the output capacitor '
        'ripple current, or judging it per winding on a centre tap.',
        'Rounding L<sub>m</sub> up, which without showing it removes the ZVS margin.',
        'Trusting the closed-form ZVS estimate instead of sweeping the '
        'selected tank &mdash; or sweeping only the design corner, which is '
        'where the <i>gain</i> is worst and not always where ZVS is.',
        'Using capacitor ESR at 120&nbsp;Hz, or R<sub>DS(on)</sub> at '
        '25&nbsp;&deg;C, to compute a loss at the operating point.',
        'Judging device stress without dividing by the number of parts '
        'actually in parallel.']))

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
        'every downstream check read the selected one. A sheet that with no warning '
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
        'presents, and the start-up window is finite. This risk is created by '
        'the architecture, so it has no precedent to borrow from.' % V,
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
        'accepted loss-budget miss is settled: measure it in <b>half-bridge '
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
        'IEEE ECCE.']))

    # =============================================================== 9
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
              'The required thermal resistance comes out roughly twice as '
              'easy as it is'],
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
