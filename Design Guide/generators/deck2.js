const pptx = new (require('pptxgenjs'))();
const fs=require('fs');
pptx.layout='LAYOUT_16x9';                 // 10 x 5.625 in
pptx.author='L6790A design guide rev 0.6';
pptx.title='Single-Stage PF LLC with L6790A';

const NAVY='03234B', YEL='FFD200', MAG='E6007E', CYA='3CB4E6', GRN='49B170', PUR='8C0078';
const GREY='464650', LT='E8E8E9', WHITE='FFFFFF';
const F='Arial';
const LOGO='logo/image1.png';
const W=10, H=5.625;

function b64(p){ return 'image/png;base64,'+fs.readFileSync(p).toString('base64'); }
function imgSize(p){ // read png header
  const b=fs.readFileSync(p);
  return {w:b.readUInt32BE(16), h:b.readUInt32BE(20)};
}
// place an image inside a box, preserving aspect, centred
function fit(p, bx, by, bw, bh){
  const s=imgSize(p), r=s.w/s.h, br=bw/bh;
  let w,h;
  if(r>br){ w=bw; h=bw/r; } else { h=bh; w=bh*r; }
  return {path:p, x:bx+(bw-w)/2, y:by+(bh-h)/2, w, h};
}

/* ---------- slide shells ---------- */
function content(title, kicker){
  const s=pptx.addSlide();
  s.background={color:WHITE};
  s.addImage({path:LOGO, x:0.30, y:H-0.62, w:0.55, h:0.42});
  s.addText(title,{x:3.0,y:0.16,w:6.75,h:0.5,align:'right',fontFace:F,fontSize:20,bold:true,color:NAVY,margin:0});
  if(kicker) s.addText(kicker,{x:0.45,y:0.78,w:9.1,h:0.30,fontFace:F,fontSize:12,bold:true,color:WHITE,
      fill:{color:NAVY},align:'left',margin:[2,8,2,8],valign:'middle'});
  s.addText('L6790A  single-stage PF LLC',{x:6.6,y:H-0.30,w:3.15,h:0.22,align:'right',fontFace:F,fontSize:7,color:'BBBBBB',margin:0});
  return s;
}
function section(n, title, sub){
  const s=pptx.addSlide(); s.background={color:NAVY};
  s.addShape(pptx.ShapeType.rect,{x:0,y:1.75,w:6.4,h:1.05,fill:{color:YEL}});
  s.addText(title,{x:0.55,y:1.75,w:5.7,h:1.05,fontFace:F,fontSize:26,bold:true,color:NAVY,valign:'middle',margin:0});
  s.addText('PART '+n,{x:0.55,y:1.25,w:4,h:0.35,fontFace:F,fontSize:13,bold:true,color:YEL,margin:0});
  if(sub) s.addText(sub,{x:0.55,y:3.05,w:8.5,h:1.2,fontFace:F,fontSize:13,color:'C8D4E4',margin:0});
  s.addImage({path:LOGO,x:0.30,y:H-0.62,w:0.55,h:0.42});
  return s;
}
function bullets(s, items, x,y,w,h, sz){
  s.addText(items.map((t,i)=>({text:t, options:{bullet:{indent:14}, breakLine:i<items.length-1}})),
    {x,y,w,h,fontFace:F,fontSize:sz||12.5,color:NAVY,paraSpaceAfter:7,valign:'top',margin:0});
}
function eqimg(s, name, x, y, w){
  const p='eq/'+name+'.png', d=imgSize(p), SC=(15/26)/260;
  let iw=Math.min(w,d.w*SC), ih=iw*d.h/d.w;
  s.addImage({path:p, x, y, w:iw, h:ih});
  return ih;
}
function eqBox(s, name, x,y,w, pad){
  pad=pad===undefined?0.11:pad;
  const p='eq/'+name+'.png', d=imgSize(p);
  const SC=(15/26)/260;                       // rendered at 26 pt / 260 dpi -> show at 15 pt
  let iw=d.w*SC, ih=d.h*SC;
  const maxW=w-2*pad, maxH=(4.98)-y-2*pad;    // never spill sideways or past the footer band
  if(iw>maxW){ ih*=maxW/iw; iw=maxW; }
  if(ih>maxH){ iw*=maxH/ih; ih=maxH; }
  const bw=Math.min(w, iw+2*pad), bh=ih+2*pad, bx=x+(w-bw)/2;
  s.addShape(pptx.ShapeType.roundRect,{x:bx,y,w:bw,h:bh,fill:{color:'F2F5F9'},line:{color:LT,width:0.75},rectRadius:0.04});
  s.addImage({path:p,x:bx+(bw-iw)/2,y:y+pad,w:iw,h:ih});
  return bh;
}
function card(s,x,y,w,h,head,body,col){
  s.addShape(pptx.ShapeType.roundRect,{x,y,w,h,fill:{color:'F5F7FA'},line:{color:col||NAVY,width:1},rectRadius:0.05});
  s.addText(head,{x:x+0.12,y:y+0.09,w:w-0.24,h:0.3,fontFace:F,fontSize:11.5,bold:true,color:col||NAVY,margin:0});
  s.addText(body,{x:x+0.12,y:y+0.42,w:w-0.24,h:h-0.52,fontFace:F,fontSize:10,color:GREY,margin:0,valign:'top'});
}
function stat(s,x,y,w,val,lab,col){
  s.addText(val,{x,y,w,h:0.55,fontFace:F,fontSize:28,bold:true,color:col||MAG,align:'center',margin:0});
  s.addText(lab,{x,y:y+0.54,w,h:0.34,fontFace:F,fontSize:9,color:GREY,align:'center',margin:0});
}
function table(s, rows, x,y,w, colW, fsz){
  s.addTable(rows,{x,y,w,colW,fontFace:F,fontSize:fsz||10,color:NAVY,border:{type:'solid',color:LT,pt:0.5},
    autoPage:false,valign:'middle'});
}
const TH=(t)=>({text:t,options:{bold:true,color:WHITE,fill:{color:NAVY},fontSize:10}});
const src=(s,t)=>s.addText(t,{x:1.00,y:H-0.30,w:5.4,h:0.22,fontFace:F,fontSize:7,italic:true,color:'BBBBBB',margin:0});

/* ============================ 1. TITLE ============================ */
{
  const s=pptx.addSlide(); s.background={color:NAVY};
  s.addShape(pptx.ShapeType.rect,{x:0,y:0,w:0.28,h:H,fill:{color:YEL}});
  s.addText('Single-Stage PF LLC Converter',{x:0.9,y:1.55,w:8.4,h:0.65,fontFace:F,fontSize:30,bold:true,color:WHITE,margin:0});
  s.addText('Design with the L6790A — and how it differs from a classic LLC',
    {x:0.9,y:2.25,w:8.4,h:0.5,fontFace:F,fontSize:16,color:YEL,margin:0});
  s.addText('A beginner-friendly walkthrough:  operating principle · design equations · a full 240 W / 60 V worked example',
    {x:0.9,y:2.85,w:8.4,h:0.5,fontFace:F,fontSize:11.5,color:'C8D4E4',margin:0});
  s.addText('Reference material:  L6790A preliminary datasheet · L6790 design spreadsheet r1.0 · EVL6790_670W schematics\nBackground on the classic LLC:  Infineon AN 2013-03 · onsemi / Fairchild AN-4151',
    {x:0.9,y:3.95,w:8.4,h:0.8,fontFace:F,fontSize:9.5,color:'9FB3CC',margin:0});
  s.addImage({path:LOGO,x:8.85,y:0.30,w:0.85,h:0.66});
  s.addNotes('This deck assumes no prior LLC knowledge. Part 1 builds the classic LLC from scratch, Part 2 shows what single-stage operation changes, Part 3 covers the L6790A itself, Part 4 is the side-by-side comparison, Part 5 a worked example, Part 6 the verification findings.');
}

/* ============================ 2. AGENDA ============================ */
{
  const s=content('Agenda');
  const items=[
    ['1','What an LLC converter is','symbols, the four blocks, FHA, the gain curve, ZVS'],
    ['2','What "single stage PF" changes','no bulk capacitor — and why that changes everything'],
    ['3','The L6790A','pins, oscillator, morphing, protections'],
    ['4','Side by side','a table of every difference that matters'],
    ['5','Worked example','240 W / 60 V universal input, step by step'],
    ['6','Verification & errata','what we re-derived, and what we found wrong'],
  ];
  items.forEach((it,i)=>{
    const y=1.30+i*0.66;
    s.addShape(pptx.ShapeType.roundRect,{x:0.55,y,w:0.42,h:0.42,fill:{color:YEL},rectRadius:0.08});
    s.addText(it[0],{x:0.55,y,w:0.42,h:0.42,fontFace:F,fontSize:15,bold:true,color:NAVY,align:'center',valign:'middle',margin:0});
    s.addText(it[1],{x:1.15,y:y+0.01,w:3.3,h:0.4,fontFace:F,fontSize:13.5,bold:true,color:NAVY,valign:'middle',margin:0});
    s.addText(it[2],{x:4.5,y:y+0.01,w:5.0,h:0.4,fontFace:F,fontSize:11,color:GREY,valign:'middle',margin:0});
  });
  s.addNotes('Roughly 10 minutes per part.');
}


/* ===================== SYMBOL GLOSSARY ========================== */
const GLOSS=[
 ['vin','bus voltage','What the bridge is fed from. Two-stage: a flat 400 V. Single-stage: the raw rectified mains, sweeping 0 \u2192 373 V, one hundred times a second.'],
 ['vdrive','tank drive amplitude','How hard the bridge drives the tank. A full bridge drives with Vᵢₙ, a half bridge with Vᵢₙ/2 \u2014 Cᵣ blocks the DC component.'],
 ['Nrect','rectifier count and drop','Nrect = 1 for a centre tap, 2 for a secondary full bridge. Vrect is the forward drop of ONE device.'],
 ['voeff','reflected output voltage','Vₒᵤₜ + Nrect \u00b7 Vrect \u2014 what the secondary looks like once the rectifier drops are added in.'],
 ['n','turns ratio','It only ever appears multiplied by Vo,eff. That product is the voltage the secondary reflects back to the primary side.'],
 ['M','tank voltage gain','(voltage the tank hands to the transformer) \u00f7 (voltage the bridge applies). M = 1 at the series resonance, for any load.'],
 ['LrCr','series resonant pair','The series arm of the tank. Together they fix the series resonance fᵣ and the impedance scale Z₀.'],
 ['Lm','magnetising inductance','The shunt arm. Its current never reaches the load \u2014 it is what discharges the MOSFET output capacitance and buys ZVS.'],
 ['lam','inductance ratio \u2014 the SHAPE knob','Bigger \u03bb = a taller, steeper gain curve = more boost available, but also more circulating current. A single stage lands near 0.5.'],
 ['m','the same knob, inverted','m = 1 + 1/\u03bb. Application notes quote m, this deck quotes \u03bb. m = 3\u20268 is the classic range; a single stage needs about 2.9.'],
 ['frfo','the two resonances','fᵣ is Cᵣ with Lᵣ alone (secondary conducting). fₒ is Cᵣ with Lᵣ + Lₘ (no load). fₒ is the FREQUENCY FLOOR.'],
 ['fn','normalised frequency','1 means "at resonance". Below 1 the tank boosts, above 1 it bucks. The floor sits at fₙ₀ = fₒ/fᵣ.'],
 ['Rac','equivalent ac load','Rectifier, transformer and load collapsed into ONE resistor, so the tank becomes a plain RLC divider.'],
 ['Z0','characteristic impedance','The tank\u2019s own impedance scale, in ohms. It does not depend on the load at all.'],
 ['Q','quality factor','HOW HEAVILY the tank is loaded. Q \u2192 0 is no load (a tall, peaky curve); large Q is full load (a low, flat curve).'],
 ['th','line phase angle','0 at the mains zero crossing, 90\u00b0 at the mains peak. In a single-stage design EVERY quantity is a function of \u03b8.'],
];
function symRow(s,x,y,w,img,name,desc,alt){
  const p='sym/'+img+'.png', d=imgSize(p), bh=0.58;
  s.addShape(pptx.ShapeType.roundRect,{x,y,w,h:bh,fill:{color:alt?'F5F7FA':'FFFFFF'},
    line:{color:'DDE3EA',width:0.75},rectRadius:0.03});
  let iw=1.35, ih=iw*d.h/d.w;
  if(ih>0.34){ ih=0.34; iw=ih*d.w/d.h; }
  s.addImage({path:p,x:x+0.14,y:y+(bh-ih)/2,w:iw,h:ih});
  s.addText(name,{x:x+1.72,y:y+0.04,w:w-1.86,h:0.22,fontFace:F,fontSize:10.5,bold:true,color:NAVY,margin:0,valign:'middle'});
  s.addText(desc,{x:x+1.72,y:y+0.24,w:w-1.86,h:0.30,fontFace:F,fontSize:8.5,color:GREY,margin:0,valign:'top'});
}
[[0,6,'the tank itself \u2014 voltages, turns ratio, and the three reactive parts'],
 [6,12,'gain, the two design knobs, and the two resonances'],
 [12,16,'loading \u2014 and the one variable that only exists in a single-stage design']].forEach((g,gi)=>{
  const s=content('The symbols, once and for all  ('+(gi+1)+'/3)',GLOSS.slice(g[0],g[1]).length+' of 16 \u2014 '+g[2]);
  GLOSS.slice(g[0],g[1]).forEach((r,k)=>symRow(s,0.42,1.20+k*0.63,9.16,r[0],r[1],r[2],k%2===1));
});

{
  const s=content('Reading the gain equation term by term','One equation carries the whole LLC. Here is what each piece does.');
  eqBox(s,'M_split',2.35,1.18,4.6);
  card(s,0.40,2.62,4.50,1.10,'A(fₙ) = 1 + \u03bb \u2212 \u03bb/fₙ\u00b2   \u2014 the SHAPE',
    'A carries no load information at all. It becomes ZERO at fₙ₀ = \u221a(\u03bb/(1+\u03bb)); with no load that is where M blows up. That singularity IS fₒ, the frequency floor. At fₙ = 1 we get A = 1, hence M = 1 at resonance.',NAVY);
  card(s,5.10,2.62,4.50,1.10,'Q\u00b2(fₙ \u2212 1/fₙ)\u00b2   \u2014 the LOADING',
    'Zero at fₙ = 1, growing on both sides. This is what DAMPS the peak: heavier load = bigger Q = lower, flatter curve. It is also why FULL LOAD is the worst case for the tank design.',MAG);
  eqBox(s,'A_def',0.40,3.86,9.2);
  s.addText('\u03bb decides WHERE the pole sits and how tall the curve can be. Q decides HOW MUCH of that height the load lets you keep. Those two numbers are the only degrees of freedom in the entire tank.',
    {x:1.05,y:4.60,w:8.5,h:0.50,fontFace:F,fontSize:10,bold:true,color:MAG,margin:0});
}

{
  const s=content('Two resonances, and why the lower one matters','Every LLC has fᵣ and fₒ. The single-stage converter lives near fₒ.');
  s.addImage(fit('fig/c_gain.png',0.40,1.20,5.5,3.9));
  let y=1.25;
  y+=eqBox(s,'fr_fo',6.05,y,3.55)+0.16;
  bullets(s,[
    'fᵣ : Cᵣ resonates with Lᵣ alone. This happens when the secondary is conducting, so Lₘ is clamped by the reflected output voltage and drops out of the circuit. At fᵣ the gain is 1 for ANY load \u2014 the load term vanishes.',
    'fₒ : Cᵣ resonates with Lᵣ + Lₘ. This happens at NO load, when nothing clamps Lₘ. At fₒ the no-load gain is infinite \u2014 so nothing can push the converter below fₒ.',
    'Every operating point sits between fₒ and infinity. Below fₒ the tank turns capacitive and the bridge hard-switches.',
    'In this design fₒ = 88.1 kHz and fᵣ = 150.3 kHz. That whole band is where a single-stage converter spends most of the line cycle.',
  ],6.05,y,3.55,2.95,9.5);
}
/* ===================== PART 1 : CLASSIC LLC ======================= */
section('1','What an LLC converter is','Everything in this part is the CLASSIC, two-stage LLC. If you already know it, skip to Part 2 — but note the numbers, because Part 4 compares against them.');

{ // 1.1 four blocks
  const s=content('The LLC in four blocks','A square-wave generator, a resonant tank, a transformer, a rectifier');
  s.addImage(fit('fig/f_llc_sch.png',0.40,1.22,5.05,2.45));
  s.addImage(fit('fig/f_llc_wave.png',5.60,1.22,1.95,2.45));
  card(s,7.70,1.22,1.90,2.45,'Remember this',
    'Only the FREQUENCY is available as a control handle. The height of the square wave is whatever the bus happens to be.',MAG);
  bullets(s,[
    'Q1/Q2 chop the DC bus into a square wave at 50 % duty. Only the FREQUENCY can be changed \u2014 never the height.',
    'The tank (Lᵣ, Cᵣ, Lₘ) filters that square wave down to (almost) a pure sine. It also decides how much voltage reaches the transformer.',
    'Lₘ is small on purpose \u2014 3 to 8 times Lᵣ \u2014 so a large magnetising current circulates. That current is what discharges the MOSFET output capacitance and gives ZVS.',
    'The rectifier restores DC. Centre-tap or full bridge, diodes or synchronous MOSFETs.',
  ],0.40,3.78,9.20,1.20,9.5);
  src(s,'Figures: onsemi / Fairchild AN-4151, Fig. 3 and Fig. 4');
  s.addNotes('The single most important sentence: only frequency is available as a control handle.');
}

{ // 1.2 FHA
  const s=content('First-harmonic approximation (FHA)','Replace everything after the tank by one resistor, then it is just an RLC divider');
  s.addImage(fit('fig/f_ac_equiv.png',0.45,1.30,3.9,3.6));
  let y=1.35;
  s.addText('The load, rectifier and transformer collapse into one equivalent resistance:',{x:4.6,y:y,w:5.0,h:0.35,fontFace:F,fontSize:11.5,color:NAVY,margin:0});
  y+=0.38; y+=eqBox(s,'rac_conv',4.6,y,5.0)+0.16;
  s.addText('and the tank becomes a frequency-dependent divider whose gain is:',{x:4.6,y:y,w:5.0,h:0.32,fontFace:F,fontSize:11.5,color:NAVY,margin:0});
  y+=0.36; y+=eqBox(s,'fha_gain',4.6,y,5.0)+0.16;
  y+=eqBox(s,'q_solve',4.6,y,5.0)+0.14;
  s.addText('Two numbers describe the whole tank: \u03bb is the SHAPE, Q is the LOADING. Next slide takes them apart.',
    {x:4.6,y:4.72,w:5.0,h:0.5,fontFace:F,fontSize:10,italic:true,bold:true,color:MAG,margin:0});
  src(s,'Figure: onsemi / Fairchild AN-4151, Fig. 5 and Fig. 6');
}

{ // 1.3 gain curve
  const s=content('The gain curve','Gain is 1 at resonance, boosts below it, bucks above it');
  s.addImage(fit('fig/f_gain_q.png',0.40,1.30,4.6,3.3));
  s.addImage(fit('fig/f_inf_gainm.png',5.15,1.30,4.45,2.2));
  bullets(s,[
    'Light load (small Q) → tall, peaky curve → lots of boost available.',
    'Heavy load (large Q) → flat curve → the peak gain DROPS. Full load is therefore the worst case for the tank design.',
    'Smaller m = Lp/Lr (i.e. larger \u03bb) raises the whole curve, at the price of more circulating current.',
  ],5.15,3.52,4.45,1.40,10);
  src(s,'Figures: onsemi AN-4151 Fig. 7 (left) · Infineon AN 2013-03 Fig. 3.2 (right)');
}

{ // 1.4 operation modes
  const s=content('Below or above resonance?','Both work — they trade rectifier losses against circulating current');
  s.addImage(fit('fig/f_opmodes.png',0.40,1.30,4.5,2.9));
  s.addImage(fit('fig/f_modewave.png',5.05,1.30,4.55,2.9));
  card(s,0.40,4.16,4.5,1.05,'Below resonance  (fsw < fr)',
    'Secondary current is a half-sine that reaches zero before the half period ends → rectifier turns off at ZERO CURRENT. But the circulating current is large.',MAG);
  card(s,5.05,4.16,4.55,1.05,'Above resonance  (fsw > fr)',
    'Minimum circulating current, best conduction loss. But the rectifier is hard-commutated, and light load pushes the frequency very high.',CYA);
  src(s,'Figures: onsemi / Fairchild AN-4151, Fig. 10 and Fig. 11');
}

{ // 1.5 ZVS
  const s=content('ZVS and the forbidden capacitive region','Stay on the inductive side of the gain peak — always');
  s.addImage(fit('fig/f_zvs_cap.png',5.05,1.25,4.55,3.9));
  bullets(s,[
    'INDUCTIVE side (right of the gain peak): the tank current LAGS the square wave. During the dead time it keeps flowing and pulls the midpoint to the next rail — the MOSFET turns on at zero volts. This is ZVS.',
    'CAPACITIVE side (left of the peak): the current LEADS. The body diode is hard reverse-recovered, the noise is violent, and the gain slope reverses so the output goes out of control.',
    'The minimum switching frequency must therefore be clamped WELL above the peak-gain frequency.',
    'Practical rule from both application notes: leave 10–20 % margin on the maximum gain so that ZVS survives load steps and start-up.',
  ],0.40,1.25,4.5,3.7,10.5);
  src(s,'Figure: onsemi / Fairchild AN-4151, Fig. 12');
}

{ // 1.6 classic design flow
  const s=content('The classic design recipe','Both Infineon and onsemi follow the same eleven steps');
  const rows=[
    [TH('Step'),TH('What you do'),TH('onsemi AN-4151 / Infineon AN 2013-03')],
    ['1–2','specification, efficiency, gain range','Mmin at Vin,max, Mmax at Vin,min (+10–20 % margin)'],
    ['3','turns ratio','n = Vin,max /(2(Vₒ+V_F)) × Mmin'],
    ['4','equivalent load','Rac = 8n²Vₒ²/(\u03c0²Pₒ)'],
    ['5','pick m (or \u03bb), read Q from the peak-gain chart','m = 3…8  →  gain 1.1…1.2 at resonance'],
    ['6','resonant components','Cr = 1/(2\u03c0 Q fₒ Rac),  Lr = 1/((2\u03c0fₒ)²Cr),  Lp = m·Lr'],
    ['7–8','transformer turns / core, resonant capacitor rating','Nₚ from \u0394B; Cr voltage from the OCP trip point'],
    ['9–10','rectifier, output capacitor, control circuit','V_D = 2(Vₒ+V_F);  RT/soft-start network'],
    ['11','current sensing and protection','R_sense from the OCP threshold'],
  ];
  table(s,rows,0.40,1.30,9.2,[0.72,2.75,5.73],9.5);
  s.addText('Keep this list in mind. In Part 4 we will walk it again and mark every step that a single-stage converter changes.',
    {x:0.40,y:4.80,w:9.2,h:0.32,fontFace:F,fontSize:10,italic:true,bold:true,color:MAG,margin:0});
}

/* ================= PART 2 : SINGLE STAGE PF ====================== */
section('2','What "single stage PF" changes','Remove the boost PFC and the 400 V bulk capacitor. Everything you just learned still applies — but the ROLE of the switching frequency changes completely.');

{
  const s=content('Two stages, or one','The boost stage and the 400 V bank both disappear');
  s.addImage(fit('fig/c_block.png',0.35,1.20,9.3,3.05));
  const y=4.14;
  card(s,0.35,y,2.95,1.08,'What you gain','One stage instead of two: fewer parts, no 400 V electrolytic bank, one control loop, no product of two efficiencies.',GRN);
  card(s,3.50,y,2.95,1.08,'What you pay','The tank must cover the whole mains range, \u03bb must be large, circulating current is high, and the output carries a 2fl ripple.',MAG);
  card(s,0.35+2*3.15,y,2.95,1.08,'Where it fits','LED drivers, LCD TV, AIO PC, server and telecom front ends, USB-PD \u2014 anywhere a few % of 100/120 Hz ripple is fine.',NAVY);
}

{
  const s=content('Why unity power factor forces a ripple','The mains delivers 2P sin²\u03b8 — the load wants a constant P');
  s.addImage(fit('fig/c_energy.png',0.40,1.25,5.4,2.9));
  let y=1.30;
  y+=eqBox(s,'pinst',6.00,y,3.6)+0.20;
  bullets(s,[
    'At the line peak the instantaneous power is TWICE the average. At the zero crossing it is zero.',
    'The difference has to be stored somewhere for a quarter of a line cycle.',
    'In a two-stage supply the 400 V bulk capacitor does that job.',
    'In a single stage there is no bulk capacitor — so the OUTPUT capacitor does it instead.',
    'The energy did not disappear. It moved from 400 V to 60 V, which is usually a good trade — but the output bank now carries the whole 2fl ripple current.',
  ],6.00,y,3.6,3.2,11);
  s.addShape(pptx.ShapeType.roundRect,{x:0.40,y:4.28,w:5.4,h:0.82,fill:{color:'FDF3F8'},line:{color:MAG,width:1},rectRadius:0.05});
  s.addText('Everything is sized at 2 \u00d7 P, not at P',{x:0.55,y:4.36,w:5.1,h:0.30,fontFace:F,fontSize:13,bold:true,color:MAG,align:'center',margin:0});
  s.addText('peak instantaneous power = 2 P     \u2022     peak output current = 2 I',{x:0.55,y:4.72,w:5.1,h:0.30,fontFace:F,fontSize:10,color:GREY,align:'center',margin:0});
}

{
  const s=content('Gain is no longer a control variable','Both ports are voltage sources — so the gain is FORCED from outside');
  let y=1.25;
  s.addText('In a classic LLC you change the frequency to change the gain, and the gain sets Vₒᵤₜ. Here that reasoning breaks:',
    {x:0.40,y,w:9.2,h:0.35,fontFace:F,fontSize:12,color:NAVY,margin:0});
  y+=0.42;
  card(s,0.40,y,4.5,0.95,'The output is a voltage source','Cₒᵤₜ is in the millifarad range, so Vₒᵤₜ simply cannot move inside one 10 ms line half cycle.',CYA);
  card(s,5.10,y,4.5,0.95,'The input is a voltage source too','There is no bulk capacitor, so the bus IS the rectified mains, |v_ac(\u03b8)| — a sine, every cycle.',CYA);
  y+=1.12;
  y+=eqBox(s,'gain_forced',0.40,y,9.2)+0.22;
  s.addText('M is already decided at every instant. Feed it back into the FHA gain equation and solve — what the frequency actually sets is Q, and Q is the load. In other words: THE FREQUENCY SETS POWER, NOT VOLTAGE.',
    {x:0.40,y,w:9.2,h:0.7,fontFace:F,fontSize:12.5,bold:true,color:MAG,margin:0});
  s.addNotes('This is the single most important slide in the deck.');
}

{
  const s=content('Frequency modulation IS the power factor correction','Follow 2P sin²\u03b8 and the input current becomes a sine in phase with the voltage');
  s.addImage(fit('fig/c_fsw.png',0.40,1.18,5.6,3.30));
  let y=1.30;
  y+=eqBox(s,'fha_gain',6.15,y,3.45)+0.14;
  y+=eqBox(s,'q_solve',6.15,y,3.45)+0.18;
  bullets(s,[
    'At each line phase \u03b8 the required gain M and the required Q are both known. Solve the FHA equation numerically for fₙ.',
    'TAKE THE LARGER ROOT. The smaller root is the capacitive region — hard switching.',
    'All curves converge to fₒ at the zero crossing: the required gain diverges as 1/sin\u03b8, but the achievable gain diverges at fₒ too. The two divergences cancel, so a solution always exists.',
  ],6.15,y,3.45,1.95,9);
  eqBox(s,'fo',6.15,4.32,3.45);
}


{
  const s=content('How does an LLC do power factor correction at all?','Six steps. Follow them once and the whole topology falls out.');
  const st=[
    ['1','What PFC actually demands','Nothing about voltage. It says the INPUT CURRENT must be a sine in phase with the mains. Multiply the two and you get the instantaneous power the converter must draw: p(\u03b8) = 2P sin\u00b2\u03b8.'],
    ['2','What the LLC can control','Only frequency. The bridge is a fixed 50 % square wave; its height is the mains, which you cannot touch. So frequency is the one and only actuator.'],
    ['3','What frequency normally does','In a classic LLC it changes the GAIN, and the gain sets Vₒᵤₜ. That path is closed here, because both ends of the converter are already voltage sources.'],
    ['4','So the gain is forced','Cₒᵤₜ is millifarads \u2192 Vₒᵤₜ cannot move within a line half cycle. No bulk capacitor \u2192 the bus IS |v_ac(\u03b8)|. Both ends fixed \u21d2 M(\u03b8) is fixed, instant by instant.'],
    ['5','Which leaves Q','Put the forced M(\u03b8) back into the gain equation and solve for fₙ. The only free variable left in that equation is Q \u2014 and Q is the load, i.e. the POWER.'],
    ['6','Therefore frequency = power','Sweep fsw over the line half cycle so that the delivered power follows 2P sin\u00b2\u03b8, and the input current becomes the sine PFC asked for in step 1. That IS the power factor correction.'],
  ];
  st.forEach((r,i)=>{
    const y=1.22+i*0.68;
    s.addShape(pptx.ShapeType.roundRect,{x:0.42,y:y+0.04,w:0.36,h:0.36,fill:{color:i>=4?MAG:NAVY},rectRadius:0.08});
    s.addText(r[0],{x:0.42,y:y+0.04,w:0.36,h:0.36,fontFace:F,fontSize:12,bold:true,color:WHITE,align:'center',valign:'middle',margin:0});
    s.addText(r[1],{x:0.92,y:y+0.02,w:2.35,h:0.42,fontFace:F,fontSize:11,bold:true,color:NAVY,valign:'middle',margin:0});
    s.addText(r[2],{x:3.35,y:y-0.02,w:6.25,h:0.62,fontFace:F,fontSize:9.5,color:GREY,valign:'middle',margin:0});
  });
}

{
  const s=content('Step 1 \u00b7 What unity power factor really asks for','It is a statement about CURRENT, and it becomes a statement about POWER');
  let y=1.24;
  y+=eqBox(s,'pfc_req',0.40,y,9.2)+0.20;
  s.addImage(fit('fig/c_energy.png',0.40,y,5.3,2.6));
  bullets(s,[
    'The mains voltage is \u221a2\u00b7Vac\u00b7sin\u03b8, fixed by the grid. PF = 1 means the current must have exactly the same shape and phase.',
    'Their product is the instantaneous power. sin\u03b8 \u00d7 sin\u03b8 gives sin\u00b2\u03b8, whose average is \u00bd \u2014 hence the factor 2 in front of P.',
    'So "make the current a sine" and "make the power follow 2P sin\u00b2\u03b8" are the SAME instruction. The second form is the useful one, because power is what a resonant converter can actually be told to deliver.',
    'The load, meanwhile, wants a flat P. The mismatch \u2014 the yellow and blue areas \u2014 has to be stored for a quarter of a line cycle. In a single stage that store is the output capacitor.',
  ],5.95,y,3.65,2.6,10);
}

{
  const s=content('Step 4 \u00b7 Why the gain is not yours to choose','Two voltage sources, one tank in between');
  let y=1.24;
  card(s,0.40,y,4.50,1.00,'The output side is clamped','Cₒᵤₜ is in the millifarad range. Over one 10 ms line half cycle Vₒᵤₜ simply cannot move. So the voltage the tank must PRODUCE is fixed at n\u00b7Vo,eff.',CYA);
  card(s,5.10,y,4.50,1.00,'The input side is a raw sine','There is no bulk capacitor to hold the bus up. The bus voltage IS |v_ac(\u03b8)| \u2014 it sweeps from 0 to 373 V and back, 100 times a second.',CYA);
  y+=1.16;
  y+=eqBox(s,'gain_forced',0.40,y,9.2)+0.14;
  y+=eqBox(s,'voeff',0.40,y,9.2)+0.18;
  s.addText('Numerator fixed, denominator dictated by the grid \u21d2 M(\u03b8) is an INPUT to the problem, not an output. This single fact is what makes a single-stage PF LLC different from every other LLC you have seen.',
    {x:0.40,y,w:9.2,h:0.6,fontFace:F,fontSize:11.5,bold:true,color:MAG,margin:0});
}

{
  const s=content('Step 5 \u00b7 With M fixed, frequency buys you Q','and Q is nothing other than the load');
  let y=1.18;
  y+=eqBox(s,'mreq',0.40,y,8.5)+0.12;
  y+=eqBox(s,'q_theta',0.40,y,8.5)+0.12;
  y+=eqBox(s,'solve_fn',0.40,y,8.5)+0.16;
  bullets(s,[
    'Rac is inversely proportional to the power delivered, so Q is DIRECTLY proportional to it \u2014 commanding Q is commanding watts.',
    'At each \u03b8 you know Mreq and you know the Q you want, so the gain equation has exactly one unknown left: fₙ. Solve it numerically.',
    'TAKE THE LARGER ROOT \u2014 the smaller one is the capacitive region (hard switching, reversed gain slope, runaway loop). Repeat for every \u03b8 and you have the frequency trajectory the IC must follow across the line half cycle.',
  ],0.40,y+0.04,9.2,1.05,9.5);
}

{
  const s=content('Step 6 \u00b7 Why it never runs out of gain','The demand and the ceiling blow up at the same place');
  s.addImage(fit('fig/c_gain.png',0.40,1.20,5.4,3.9));
  let y=1.25;
  s.addText('Near the mains zero crossing the required gain goes to infinity. That sounds fatal \u2014 and it would be, if the load stayed on.',
    {x:5.90,y,w:3.70,h:0.55,fontFace:F,fontSize:11,color:NAVY,margin:0});
  y+=0.60;
  y+=eqBox(s,'mreq',5.90,y,3.70)+0.14;
  s.addText('But the load vanishes at exactly the same rate. And with no load the gain ceiling itself becomes infinite, right at fₒ:',
    {x:5.90,y,w:3.70,h:0.55,fontFace:F,fontSize:11,color:NAVY,margin:0});
  y+=0.60;
  y+=eqBox(s,'ceiling',5.90,y,3.70)+0.16;
  s.addText('Two divergences that cancel. The operating point simply slides down towards fₒ as \u03b8 \u2192 0, and a solution exists at every phase. fₒ is the frequency FLOOR \u2014 keep the VCO clamp at or above it.',
    {x:5.90,y,w:3.70,h:0.9,fontFace:F,fontSize:10.5,bold:true,color:MAG,margin:0});
}

{
  const s=content('And where light load goes: burst mode','Below about a quarter load there is simply no continuous solution');
  let y=1.24;
  y+=eqBox(s,'burst',0.40,y,5.5)+0.18;
  bullets(s,[
    'As the load falls, Q falls, and the whole family of gain curves collapses onto the no-load curve. Its high-frequency asymptote is 1/(1+\u03bb) \u2014 in this design 0.657.',
    'Near the full-bridge morphing edge the REQUIRED gain is only 0.638. That is below the ceiling the converter can reach at any frequency.',
    'So there is nothing to solve: the IC must stop switching for part of the time instead. That is burst mode, and it is STRUCTURAL here, not merely an efficiency option.',
    'In this design the burst entry point lands at about 68.6 W in, i.e. roughly 28 % load. Everything below that is bursting.',
    'Practical consequence: the 20 Hz voltage loop leaves 2fl ripple on the FB pin, and that ripple must not straddle the burst threshold or the converter chatters. Trim RBM.',
  ],0.40,y,5.5,3.0,10.5);
  s.addImage(fit('fig/f_gain_q.png',6.05,1.24,3.55,3.9));
  src(s,'Figure: onsemi / Fairchild AN-4151, Fig. 7');
}
{
  const s=content('Topology morphing','A 2.9 : 1 mains range is too much for one tank — so change the bridge instead');
  s.addImage(fit('fig/c_morph.png',0.40,1.20,5.5,2.4));
  s.addImage(fit('fig/c_range.png',0.40,3.55,5.5,1.55));
  bullets(s,[
    'Below 235 V peak the IC runs a FULL bridge: the tank sees twice the input.',
    'Above 245 V peak it runs a HALF bridge: the tank sees half of it. Cᵣ blocks the DC, so the half bridge really does present only ±Vᵢₙ/2.',
    'Half-bridge mode is obtained by holding LOUT2 statically high — no extra hardware.',
    'The transition is silent and hysteretic (235 / 245 Vpk).',
  ],6.10,1.20,3.5,2.3,10.5);
  let y=3.60;
  y+=eqBox(s,'vinmin',6.10,y,3.5)+0.12;
  y+=eqBox(s,'vinfbmax',6.10,y,3.5)+0.12;
  s.addText('The worst corners are the morphing EDGES — not the ends of the mains range.',
    {x:6.10,y:4.62,w:3.5,h:0.55,fontFace:F,fontSize:10,bold:true,color:MAG,margin:0});
}

{
  const s=content('The FB pin is a POWER command','Not an error voltage — a set point in watts');
  let y=1.25;
  y+=eqBox(s,'vfb',0.75,y,8.5)+0.25;
  bullets(s,[
    'Substituting the datasheet burst-mode relations gives 0.167 V per \u03a9·W. Multiply by the 2.8 V feedback span and you get 16.8 \u03a9·W — exactly the maximum-power rule in the datasheet. The two are the same equation.',
    'So the maximum power limit, the burst-mode entry point and the overload detection all sit on ONE scale: the FB voltage.',
    'The external opto loop commands an INPUT POWER. The internal loop then distributes that power across the line cycle as sin²\u03b8. That distribution is the PFC.',
  ],0.75,y,8.5,2.0,12);
  y=4.05;
  stat(s,0.75,y,2.6,'0.5 V','FB offset  Vos',NAVY);
  stat(s,3.45,y,2.6,'0.167 V/\u03a9W','power-to-FB gain',MAG);
  stat(s,6.15,y,3.1,'16.8 \u03a9\u00b7W','RCS × Pᵢₙ,max',MAG);
}

/* ===================== PART 3 : THE L6790A ======================== */
section('3','The L6790A','An analog controller that runs an LLC tank directly from the rectified mains, with PF = 1 and a THD optimiser — plus a full protection set.');

{
  const s=content('L6790A at a glance','SO16N, 800 V start-up, logic-level outputs — external half-bridge drivers are mandatory');
  const rows=[
    [TH('Pin'),TH('Name'),TH('Function — and the rule you must not break')],
    ['1','HVSU','800 V start-up + mains sensing + X-cap discharge. Connect via two HV diodes AHEAD of the bridge, on the AC side.'],
    ['3','DRV_EN','Enables the external drivers; can also be pulled low to disable the IC. NO capacitor (sampled every 2 ms).'],
    ['6','ISEN','Negative current sense. Feeds OCP1/OCP2, anti-capacitive detection, adaptive dead time AND the max-power law. NO filter, NO series resistor.'],
    ['7 / 8','RT / CT','Oscillator. RT 5–30 k\u03a9, CT 270–1000 pF, RT·CT 2.5–12 \u00b5s. No capacitor on RT.'],
    ['9','FB','Opto collector direct. This is the power command (previous slide).'],
    ['10','BM','Burst-mode threshold, read once at power-up (pin strap). Tie to GND to disable burst. No capacitor.'],
    ['11','CFG','Brown-out level AND bridge configuration, read at power-up. Outside 15–100 k\u03a9 the IC latches. No capacitor.'],
    ['12','ZCD','Auxiliary winding divider: output voltage sensing, OVP1/OVP2, demagnetisation. Polarity: ZCD must go POSITIVE when LOUT1 is on.'],
    ['13–16','LOUTx / HOUTx','Logic-level drive signals (VOH = 4 V). LOUT2 also selects half vs full bridge at start-up — never fit a pull-down.'],
  ];
  table(s,rows,0.40,1.25,9.2,[0.62,0.95,7.63],8.5);
}

{
  const s=content('Configuration is a pin strap','RCFG plus the state of LOUT2 decide the whole operating scheme');
  const rows=[
    [TH('Configuration'),TH('RCFG'),TH('LOUT2'),TH('Input peak voltage'),TH('Mode')],
    ['Morphing, fixed BIBO','15 k\u03a9','OPEN','< 60 V / 70–235 V / > 245 V','stop / full bridge / half bridge'],
    ['Morphing, adjusted BIBO','15–47 k\u03a9','OPEN','< VBO / VBO+10…235 V / > 245 V','stop / full bridge / half bridge'],
    ['Fixed full bridge','47–100 k\u03a9','OPEN','< VBO  /  > VBO+10 V','stop / full bridge'],
    ['Fixed half bridge','15–100 k\u03a9','GND','< VBO  /  > VBO+10 V','stop / half bridge — SPLIT Cᵣ MANDATORY'],
  ];
  table(s,rows,0.40,1.25,9.2,[2.15,1.05,0.85,2.85,2.30],9.5);
  let y=3.20;
  y+=eqBox(s,'osc',0.40,y,4.5)+0.15;
  s.addText('VBO = RCFG × 4 V/k\u03a9.  The datasheet quotes it as a PEAK value while the design tool and the EVL board notes quote rms — a factor \u221a2 waiting to bite.',
    {x:0.40,y,w:4.5,h:0.7,fontFace:F,fontSize:10,color:MAG,margin:0});
  card(s,5.15,3.20,4.45,0.95,'The only actuator is IEA','The error amplifier current adds to the CT charging current. More current → higher frequency → LESS power. Everything else in the oscillator is fixed by RT, CT and Tidle.',NAVY);
  card(s,5.15,4.30,4.45,0.95,'Watch Tidle','The datasheet is self-contradictory: 250, 350 or 700 ns depending on where you read. fMax swings by \u00b125 %. Keep it as a variable and measure it on the first board.',MAG);
}

{
  const s=content('Protections','Two levels almost everywhere, so a fault degrades before it stops the converter');
  const it=[
    ['OCP1 / OCP2','−550 mV / −750 mV on ISEN. Level 1 raises the frequency (folds power back); level 2 stops for 50 \u00b5s then restarts at the start-up frequency.',MAG],
    ['ACP soft / hard','Anti-capacitive. Soft raises the frequency; hard stops for 50 \u00b5s. This is what keeps the tank out of the capacitive region.',MAG],
    ['OVP1 / OVP2','2.3 V / 2.5 V on ZCD. Level 1 keeps switching with reduced power; level 2 stops for 100 ms and restarts with safe start.',CYA],
    ['Brown-out / brown-in','40 ms debounce, 500 \u00b5s deglitch. Threshold set by RCFG.',CYA],
    ['Safe start / demag','Pulse and dead-time shaping during the first cycles so the bridge never hard-switches at start-up.',GRN],
    ['X-cap discharge','Discharges the EMI filter capacitors to a safe level when the mains is unplugged. Needs HVSU on the AC side.',GRN],
    ['FB / ZCD / ISEN open','1 s time-out on FB, 14 ms on ZCD, 7 cycles on ISEN — the last two latch.',NAVY],
    ['Over-temperature','HVSU charge current is reduced until the junction cools.',NAVY],
  ];
  it.forEach((r,i)=>{
    const col=i%2, row=Math.floor(i/2);
    card(s,0.40+col*4.70,1.25+row*0.99,4.50,0.90,r[0],r[1],r[2]);
  });
}

/* ================ PART 4 : SIDE BY SIDE ========================== */
section('4','Side by side','The same eleven design steps — and every place where the single-stage answer is different.');

{
  const s=content('Classic LLC vs single-stage PF LLC','Read this table twice. It is the whole point of the deck.');
  const rows=[
    [TH('Topic'),TH('Classic LLC (behind a PFC)'),TH('Single-stage PF LLC (L6790A)')],
    ['Input to the tank','pre-regulated 380–400 Vdc, nearly constant','rectified mains |v_ac(\u03b8)|, 0 → 373 V, every 10 ms'],
    ['What frequency controls','the OUTPUT VOLTAGE','the INPUT POWER — the voltage gain is forced'],
    ['Design corner','full load, minimum bus (hold-up)','the two MORPHING EDGES: 173.2 and 332.3 Vac equivalent'],
    ['m = Lp/Lr','3 … 8','2.9  (\u03bb \u2248 0.5, i.e. Lm \u2248 2 Lr)'],
    ['Rac definition','8n²Vₒ²/(\u03c0²Pₒ)','4n²Vo,eff²/(\u03c0²Pᵢₙ)  — defined at the LINE-PEAK power'],
    ['Operating region','mostly at or just above fᵣ','mostly BELOW fᵣ; converges to fₒ at the zero crossing'],
    ['Circulating current','moderate','large — the price of \u03bb \u2248 0.5'],
    ['Bulk storage','400 V electrolytic bank at the input','moved to the OUTPUT; carries the full 2fl ripple current'],
    ['Output ripple','tens of mV','a few % of Vₒᵤₜ at 100/120 Hz, by design'],
    ['Voltage-loop crossing','kHz range','~20 Hz — limited by the 3rd-harmonic (THD) budget'],
    ['Burst mode','optional, for light-load efficiency','structural: below ~28 % load there is no continuous solution'],
  ];
  table(s,rows,0.40,1.25,9.2,[1.90,3.55,3.75],9);
}

{
  const s=content('Why \u03bb has to be about 0.5','The classic rule of thumb will simply not start at low line');
  let y=1.25;
  s.addText('Four independent conditions each put a FLOOR under \u03bb. You take the largest.',{x:0.40,y,w:9.2,h:0.3,fontFace:F,fontSize:11.5,color:NAVY,margin:0});
  y+=0.36;
  const eqs=['lam_min1','lam_min2','lam_minTD','lam_min3'];
  const lbl=['minimum gain at high line','maximum frequency','maximum frequency incl. dead time  \u2190 dominates here','minimum frequency'];
  eqs.forEach((e,i)=>{
    const col=i%2, row=Math.floor(i/2);
    const x=0.40+col*4.70, yy=y+row*1.18;
    s.addText(lbl[i],{x,y:yy,w:4.5,h:0.26,fontFace:F,fontSize:9.5,bold:true,color:(i==2?MAG:GREY),margin:0});
    eqBox(s,e,x,yy+0.28,4.5);
  });
  y+=2.42;
  y+=eqBox(s,'lam_max',0.40,y,9.2)+0.24;
  s.addText('\u03bb = 0.54 means m = 2.85 \u2014 well below the classic 3\u20268. Use the conventional Lm/Lr = 5\u202610 here and the converter simply will not start at low line.',
    {x:1.05,y:4.72,w:8.5,h:0.50,fontFace:F,fontSize:10.5,bold:true,color:MAG,margin:0});
}

{
  const s=content('The output capacitor does two jobs now','Hold-up AND the whole 2fl energy buffer');
  let y=1.25;
  y+=eqBox(s,'cout',0.40,y,5.5)+0.16;
  y+=eqBox(s,'icout',0.40,y,5.5)+0.16;
  bullets(s,[
    'Compute the ripple condition and the hold-up condition separately, take the larger. In the worked example hold-up wins: 4364 \u00b5F against 2258 \u00b5F.',
    'For the RMS ripple current you MUST include the 2fl component. Looking only at the switching-frequency component under-estimates it by about 40 %.',
    'ESR must be the value at the SWITCHING frequency. An electrolytic tan\u03b4 is quoted at 120 Hz and is 5–10× larger there.',
  ],0.40,y,5.5,1.6,10.5);
  const yy=1.30;
  card(s,6.10,yy,3.5,1.15,'Ripple condition','C \u2265 Iₒᵤₜ /(2\u03c0 fl,min Vₒᵤₜ \u0394v)\n\u2192 2258 \u00b5F',CYA);
  card(s,6.10,yy+1.30,3.5,1.15,'Hold-up condition','C \u2265 2 Pₒᵤₜ Thold /(Vₒᵤₜ² \u2212 Vo,min²)\n\u2192 4364 \u00b5F   (dominates)',MAG);
  card(s,6.10,yy+2.60,3.5,1.35,'Selected','680 \u00b5F \u00d7 6 = 4080 \u00b5F, ESR 5 m\u03a9\n\u0394Vₒ = 3.32 V (5.5 %), Thold = 9.35 ms\nI_rms = 4.72 A  (0.79 A per capacitor)',NAVY);
}

{
  const s=content('The voltage loop crosses at 20 Hz','A pure integrator plant, and a hard trade against THD');
  s.addImage(fit('fig/c_bode.png',0.40,1.20,5.3,3.9));
  let y=1.30;
  y+=eqBox(s,'plant',5.95,y,3.65)+0.14;
  y+=eqBox(s,'thd',5.95,y,3.65)+0.16;
  bullets(s,[
    'The output is a capacitor fed by a constant-power source, so the control-to-output transfer is a PURE INTEGRATOR: −90° at every frequency.',
    'Any 2fl ripple that survives the loop and reaches FB becomes input-current distortion — mostly 3rd harmonic.',
    'Raise the crossover and the ripple falls but the THD rises. The two constraints pull in opposite directions; ~20 Hz is the practical compromise.',
    'A 20 Hz loop cannot recover from a large load step. The datasheet anti-saturation circuit does that instead — which is why the opto bias resistor RB must be inside its window.',
  ],5.95,y,3.65,2.35,9.5);
}

/* ============== PART 5 : WORKED EXAMPLE ========================== */
section('5','Worked example','240 W / 60 V, 90–264 Vac universal input, morphing enabled. Every number below is reproducible from the equations in Parts 2–4.');

{
  const s=content('Step 1–3   Specification, power budget, equivalent input');
  const rows=[
    [TH('Item'),TH('Symbol'),TH('Value')],
    ['Input / output','Vac  /  Vₒᵤₜ , Pₒᵤₜ','90–264 Vac  /  60 V, 4 A (240 W)'],
    ['Hold-up / minimum output','Thold / Vo,min','10 ms / 50 V'],
    ['Target series resonance','fᵣ','150 kHz'],
    ['Rectifier','Nrect','2  (secondary full bridge, synchronous)'],
    ['Dead time assumption','tD','220 ns'],
    ['LLC stage efficiency','\u03b7_HB','98 %'],
    ['Rated input power','Pᵢₙ','246.99 W   (\u03b7_tot = 97.17 %)'],
  ];
  table(s,rows,0.40,1.25,4.9,[1.85,1.20,1.85],9);
  let y=1.25;
  y+=eqBox(s,'vinmin',5.55,y,4.05)+0.12;
  y+=eqBox(s,'vinfbmax',5.55,y,4.05)+0.18;
  s.addText('This is the step everyone gets wrong.',{x:5.55,y,w:4.05,h:0.28,fontFace:F,fontSize:11.5,bold:true,color:MAG,margin:0});
  y+=0.32;
  bullets(s,[
    'With morphing, the tank does NOT see 90 Vac at the bottom and 264 Vac at the top.',
    'It sees 173.2 Vac equivalent at the half-bridge edge and 332.3 Vac equivalent at the full-bridge edge.',
    'Equivalent range = 1.92 : 1. Miss this and you miss BOTH worst corners.',
  ],5.55,y,4.05,1.6,10.5);
}

{
  const s=content('Step 4–6   Turns ratio, gain range, \u03bb');
  let y=1.25;
  y+=eqBox(s,'turns',0.40,y,9.2)+0.14;
  y+=eqBox(s,'gainrange',0.40,y,9.2)+0.20;
  const yy=3.52;
  stat(s,0.40,yy,2.2,'n = 2.5','equivalent-model turns ratio',NAVY);
  stat(s,2.70,yy,2.2,'150 V','reflected voltage  n·Vo,eff',MAG);
  stat(s,5.00,yy,2.2,'\u03bb = 0.541','design inductance ratio',MAG);
  stat(s,7.30,yy,2.3,'m = 2.85','equivalent  Lp / Lr',NAVY);
  card(s,0.40,4.36,9.2,0.86,'Always check the REFLECTED voltage, never the ratio alone',
    'n only ever appears multiplied by Vo,eff. Same n\u00b7Vo,eff = same tank \u2014 but every CURRENT that uses n alone is then wrong.\nThe ST spreadsheet prints n = 5 for Nrect = 2; winding that would double the required gain. See Part 6.',MAG);
}

{
  const s=content('Step 7–8   Quality factor, ZVS check, tank components');
  let y=1.25;
  y+=eqBox(s,'qzvs',0.40,y,5.4)+0.12;
  y+=eqBox(s,'qzvs2',0.40,y,5.4)+0.12;
  y+=eqBox(s,'tank',0.40,y,5.4)+0.16;
  s.addText('Never round Lₘ UP. Rounding 62.8 \u2192 65 \u00b5H lowered \u03bb_act to 0.523 and cost 64 ns of ZVS margin.',
    {x:1.00,y:4.62,w:4.8,h:0.6,fontFace:F,fontSize:9.5,bold:true,color:MAG,margin:0});
  const rows=[
    [TH('Quantity'),TH('Calculated'),TH('Selected')],
    ['Rac','37.24 \u03a9','—'],
    ['QZVS,1 / QZVS,2','0.974 / 4.07','QZVS = 0.847'],
    ['Z₀','31.52 \u03a9','—'],
    ['Cᵣ','33.66 nF','33 nF'],
    ['Lᵣ','34.11 \u00b5H','34 \u00b5H'],
    ['Lₘ','62.81 \u00b5H','65 \u00b5H'],
    ['\u03bb_act  /  fᵣ  /  fₒ','—','0.523 / 150.3 kHz / 88.1 kHz'],
  ];
  table(s,rows,5.95,1.25,3.65,[1.35,1.15,1.15],9);
  eqBox(s,'ntreal',5.95,4.20,3.65);
}

{
  const s=content('Step 9   ZVS verification at the REAL operating point','The closed-form short cut is about 10 % optimistic near the boundary');
  let y=1.25;
  y+=eqBox(s,'tzc',0.40,y,5.4)+0.12;
  y+=eqBox(s,'phi',0.40,y,5.4)+0.18;
  const rows=[
    [TH('Load'),TH('173.2'),TH('180'),TH('225'),TH('264'),TH('332.3 Vac eq.')],
    ['100 %','246 ns','354','613','650','615'],
    ['75 %','614','649','723','684','568'],
    ['50 %','979','980','898','755','499'],
    ['25 %','1418','1394','1178','915','380'],
  ];
  table(s,rows,0.40,y,5.4,[0.85,0.95,0.75,0.75,0.75,1.35],9);
  bullets(s,[
    'Sweep \u03b8, input voltage and load with the SELECTED tank, then take the minimum.',
    'Worst point: full load, 173.2 Vac equivalent, \u03b8 = 90° \u2192 TZC = 246 ns.',
    'Against tD = 220 ns that is 12 % margin — thin. Verified: the phase expression is EXACTLY the tank input-impedance phase, so the accuracy equals that of FHA itself.',
    'Alternatives if you want more margin: Lₘ = 62 \u00b5H (310 ns), or Cᵣ 39 nF / Lᵣ 29 \u00b5H / Lₘ 54 \u00b5H (503 ns).',
    'Measure ZVS at the morphing edge on the first board. No exceptions.',
  ],5.95,1.25,3.65,3.9,10.5);
}

{
  const s=content('Step 10   Currents over the line cycle','Ratings come from the worst switching cycle; losses from the line-cycle rms');
  s.addImage(fit('fig/c_ilr.png',0.40,1.20,4.9,3.0));
  let y=1.25;
  y+=eqBox(s,'isecpk',5.45,y,4.15)+0.10;
  y+=eqBox(s,'isecrms',5.45,y,4.15)+0.10;
  y+=eqBox(s,'ilm',5.45,y,4.15)+0.10;
  y+=eqBox(s,'ilr',5.45,y,4.15)+0.14;
  s.addText('The conduction ratio \u221ad matters: below resonance the secondary current flows only for d = fsw/fᵣ of each half period. Ignoring it over-estimates the rms by 11 % at the worst point.',
    {x:5.45,y:4.55,w:4.15,h:0.7,fontFace:F,fontSize:9,color:MAG,margin:0});
  const rows=[
    [TH('At 173.2 Vac eq., \u03b8 = 90°'),TH('Value')],
    ['fsw','122.4 kHz'],
    ['Isec,pk','15.42 A'],
    ['Itrafo,pk  /  ILm,pk','6.17 A  /  3.84 A'],
    ['composite tank peak','6.66 A'],
    ['Iₚᵣᵢ,rms  /  I_mos,rms','4.95 A  /  3.50 A'],
  ];
  table(s,rows,0.40,4.20,4.9,[3.10,1.80],8.5);
}

{
  const s=content('Step 11   IC network and component selection');
  let y=1.25;
  y+=eqBox(s,'rcs',0.40,y,4.6)+0.10;
  y+=eqBox(s,'rbm',0.40,y,4.6)+0.16;
  bullets(s,[
    'RCS is set by the LOWER of the two conditions. Here the maximum-power rule wins: 68.0 m\u03a9 against 82.6 m\u03a9.',
    'Judge the OCP margin against the COMPOSITE tank peak (6.66 A), not against Itrafo,pk. Using the load component alone is dangerous.',
    'fMin must sit at or above fₒ = 88.1 kHz. With RT = 13 k\u03a9 it lands at 77.4 kHz — below the floor, so only the ACP protection stands between you and the capacitive region.',
  ],0.40,y,4.6,1.9,10);
  const rows=[
    [TH('Part'),TH('Value'),TH('Result')],
    ['CT / RT','470 pF / 13 k\u03a9','fMin 77.4 k, fMax 291 k'],
    ['RCS','62.86 m\u03a9  (3 \u00d7 220 m \u2016 440 m)','Pᵢₙ,max 267 W; OCP1 8.75 A'],
    ['RBM','72 k\u03a9  \u2192 65 k\u03a9 suggested','burst entry 68.6 W in'],
    ['RCFG','32 k\u03a9','VBO 90.5 Vrms, morphing on'],
    ['RZCD,H / L','178 k\u03a9 / 20 k\u03a9','OVP1 68.3 V, OVP2 74.3 V'],
    ['Cᵢₙ','820 nF film','3 nF/W — NO bulk capacitor'],
    ['Cₒᵤₜ','680 \u00b5F \u00d7 6 + 10 \u00b5F \u00d7 2','\u0394Vₒ 3.32 V, R&N 18.9 mV'],
    ['Primary switches','600 V, 50 m\u03a9  \u00d7 4','full bridge (morphing)'],
    ['Secondary SR','100 V, 20 A  \u00d7 4','I \u2265 18.5 A'],
    ['Compensation','180 n / 1200 n / 20 k / 1.5 n','fcross 19.8 Hz, \u03a6_M 49.1°'],
  ];
  table(s,rows,5.35,1.25,4.25,[1.35,1.60,1.30],8.5);
}

{
  const s=content('Sanity check against real silicon','The same procedure applied backwards to the EVL6790_670W evaluation board');
  const rows=[
    [TH('Item'),TH('Fitted on the board'),TH('Recomputed with these equations'),TH('Board note')],
    ['Cᵣ','33 nF \u00d7 3 = 99 nF','fᵣ = 152.5 kHz','—'],
    ['Lᵣ / Lₘ','11 / 22 \u00b5H','\u03bb = 0.500, fₒ = 88.1 kHz','matches'],
    ['n / naux','3.2 / 0.33','equivalent 217 Vac design, centre-tap rectifier','matches'],
    ['RCS','68 \u2016 68 \u2016 75 m\u03a9','23.4 m\u03a9 \u2192 Pᵢₙ,max = 718 W','670 W output'],
    ['RCFG','31 k\u03a9','124 Vpk = 87.7 Vrms','VBO = 85 V'],
    ['RBM','24 k\u03a9','Pin,BM = 61.4 W \u2192 55.3 W out','BMi = 55 W'],
    ['ZCD divider','150 k / 23 k\u03a9','OVP1 52.4 V, OVP2 57.0 V','52 V / 57 V'],
    ['Cₒᵤₜ','4700 \u00b5F \u00d7 4 = 18.8 mF','hold-up 10 ms, 48 \u2192 40 V needs 19.0 mF','—'],
  ];
  table(s,rows,0.40,1.25,9.2,[1.35,2.35,3.55,1.95],9);
  card(s,0.40,4.06,4.5,1.10,'It closes','Every fitted value falls out of the same equations, including the two annotations the ST designers wrote on the schematic (BMi = 55 W and VBO = 85 V).',GRN);
  card(s,5.10,4.06,4.5,1.10,'Note the \u03bb','The board runs \u03bb = 0.500, essentially the same as our 0.523. That is the strongest single confirmation that \u03bb \u2248 0.5 is structural, not a quirk of our example.',MAG);
}

/* ============== PART 6 : VERIFICATION ============================ */
section('6','Verification and errata','Every one of the 148 design equations was re-implemented independently and cross-checked against waveform integration and impedance analysis. Here is what came out.');

{
  const s=content('What was verified, and how');
  const it=[
    ['All 148 equations re-derived','Independent second implementation, 172 cross-checks against the worked example. Agreement to the printed precision throughout.',GRN],
    ['FHA solved at the real operating point','\u03b8, input voltage and load swept over the whole range with the SELECTED tank, instead of the closed-form short cut.',GRN],
    ['Phase expression proved exact','The \u03c6 formula is identical to the tank input-impedance phase to 1e−16. So TZC is as accurate as FHA itself.',GRN],
    ['Waveforms integrated numerically','Confirms Isec,pk is exact, the \u221ad correction on the rms is exact for fsw \u2264 fᵣ, and the composite tank peak matches the true maximum.',GRN],
    ['Loop closed numerically','fcross = 19.76 Hz, \u03a6_M = 49.09°, 3rd harmonic 4.54 % — all as printed.',GRN],
    ['Board back-calculated','EVL6790_670W reproduced from the same equations, including the designer annotations.',GRN],
  ];
  it.forEach((r,i)=>{
    const col=i%2, row=Math.floor(i/2);
    card(s,0.40+col*4.70,1.25+row*1.28,4.50,1.18,r[0],r[1],r[2]);
  });
}

{
  const s=content('Findings — design tool r1.0','Corrected copies of the spreadsheet and the SMath sheet accompany this deck');
  const rows=[
    [TH('Where'),TH('What is wrong'),TH('Effect')],
    ['Res.Tank D9 (+ the whole RTC grid)','Vo,eff divided by Nrect a second time, so n is doubled when Nrect = 2','n = 5 instead of 2.5. Wind that and the required gain doubles — no start-up at low line. The tank values themselves are unaffected.'],
    ['Design Spec D20 / D79','Equivalent input range taken as 165–180 and 264 Vac','Both morphing corners missed. True range 173.2–332.3 Vac; max operating frequency 187 \u2192 241 kHz'],
    ['Device Setting D3','fsw,max,design = MIN(spec, 1.5·fₒp) — the outer MAX is missing','The oscillator can be sized for a ceiling BELOW the real operating point'],
    ['Res.Tank D35','IR1,pk uses the average power instead of the line-peak power','Exactly half; under-states the ZVS current'],
    ['CC C25/D25/E25','Secondary rms has no \u221ad conduction-ratio term (row 31 does have it)','Up to 11 % over-estimate — inconsistent inside one sheet'],
    ['CC C31','Output-capacitor rms holds only the switching-frequency part at one \u03b8','3.35 A instead of 4.72 A — 40 % low'],
    ['Device Setting D83','(naux/nsec)max divided by Nrect while V_aux,OVP2 is not','Twice as permissive; a legal-looking choice can exceed the VCC rating'],
    ['Comp D15 / D43','CTR applied twice to IFB,max','RB window shifted from 6.27–7.13 to 4.47 k\u03a9'],
    ['Prelim D17','labelled \u03b7_HB but computes \u03b7_rect·\u03b7_HB','identical only while Vrect = 0'],
  ];
  table(s,rows,0.40,1.25,9.2,[1.95,3.35,3.90],8);
}

{
  const s=content('Findings — datasheet and SMath sheet','The datasheet is still a DRAFT; treat these as open items');
  const rows=[
    [TH('Item'),TH('Issue'),TH('What to do')],
    ['Tidle','§5.3.2 implies 700 ns in one equation and 350 ns in another; Table 5 back-calculates to 250 ns','Keep it as an input variable. fMax swings 242–309 kHz. At 700 ns there is NO margin at the FB morphing edge.'],
    ['VBO','written as min(60 V, RCFG·4 V/k\u03a9), which would give 60 V for every legal RCFG','Read it as RCFG·4 with 15 k\u03a9 as the floor. Also: datasheet peak vs tool/board rms — a \u221a2 trap.'],
    ['RZCD,L formula §5.3.4','dimensionally A\u207b¹, not \u03a9; gives 95.7 k\u03a9 and a 24 \u00b5A divider current','Use RZCD,L = V_OVP1,th / I_bias. The EVL board fits exactly that.'],
    ['SMath as-built ZVS re-check','used the DESIGN \u03bb with the AS-BUILT Q','FIXED: with \u03bb_act it gives 240 ns against the exact 246 ns — conservative instead of 10 % optimistic'],
    ['SMath summary annotations','still carried rev 0.2 numbers (Q 0.9298, Z₀ 34.62 \u03a9, TZC 275.8 ns)','FIXED, and every input now carries a real SMath unit'],
    ['Guide [125]/[130]','G_o and EA_o labelled "Hz" but they are rad/s','Cosmetic, but fcross = G_o/2\u03c0 only makes sense in rad/s'],
    ['Guide [134]/[135]','CF and RF examples are computed from the SELECTED CFo, not the calculated one','State it explicitly, as [96] already does for RZCD'],
  ];
  table(s,rows,0.40,1.25,9.2,[1.95,3.55,3.70],8);
}

{
  const s=content('Measure these first','The eight things that will decide whether the board works');
  const it=[
    ['1','ZVS at the HB morphing edge','245 Vpk, full load. Calculated TZC = 246 ns — the worst point anywhere. Look at the gate and midpoint waveforms directly.'],
    ['2','fsw at the FB morphing edge','235 Vpk, full load. Calculated 241 kHz. If Tidle is really 700 ns the VCO ceiling is 242 kHz.'],
    ['3','fsw(\u03b8) over a line half cycle','Confirms Tidle and the margin against the fₒ floor.'],
    ['4','Input current and THD at 90 Vac full load','Quantifies the zero-crossing dead zone.'],
    ['5','Cold start-up','Can a millifarad output bank be charged inside the 120 ms HVSU window?'],
    ['6','FB ripple against the burst threshold','A 20 Hz loop leaves 2fl ripple on FB. Trim RBM if it chatters.'],
    ['7','Low-line start-up (only if Nrect = 2)','A doubled turns ratio shows up here first.'],
    ['8','Adaptive dead time','Does it really settle at or below 220 ns at the worst corner?'],
  ];
  it.forEach((r,i)=>{
    const y=1.25+i*0.50;
    s.addShape(pptx.ShapeType.roundRect,{x:0.40,y:y+0.02,w:0.34,h:0.34,fill:{color:i<2?MAG:NAVY},rectRadius:0.08});
    s.addText(r[0],{x:0.40,y:y+0.02,w:0.34,h:0.34,fontFace:F,fontSize:11,bold:true,color:WHITE,align:'center',valign:'middle',margin:0});
    s.addText(r[1],{x:0.88,y:y+0.02,w:2.65,h:0.34,fontFace:F,fontSize:10.5,bold:true,color:NAVY,valign:'middle',margin:0});
    s.addText(r[2],{x:3.60,y:y+0.02,w:6.0,h:0.34,fontFace:F,fontSize:9.5,color:GREY,valign:'middle',margin:0});
  });
}

{
  const s=content('Fourteen rules to take away');
  const L=[
    'Design the tank at the real ends of the EQUIVALENT input range. With morphing that is 173.2 and 332.3 Vac, not 180 and 264.',
    'Expect \u03bb \u2248 0.5. The classic Lm/Lr = 5…10 will not start at low line.',
    'Keep the VCO minimum clamp at or above fₒ. Do not rely on the anti-capacitive protection alone.',
    'Size the output bank from ripple AND hold-up, take the larger, then check the RMS ripple current.',
    'The voltage loop crosses near 20 Hz; manage the leftover FB ripple with RBM.',
    'Measure both morphing edges. HB edge = worst gain and ZVS; FB edge = worst frequency.',
    'Always verify the turns ratio through the REFLECTED voltage n·Vo,eff.',
    'Judge the OCP margin on the COMPOSITE tank current peak, not on the load component.',
    'Include the 2fl component in the output-capacitor ripple current — it is about 40 % of it.',
    'Apply the \u221ad conduction ratio to the secondary rms when fsw < fᵣ.',
    'Decide first whether Lᵣ is a discrete inductor or transformer leakage; that decides whether you wind n or n_T.',
    'Use the ESR at the switching frequency, never the 120 Hz tan\u03b4 value.',
    'Never round Lₘ up. \u03bb_act falls and the ZVS margin goes with it.',
    'Do the final ZVS check at the REAL operating point, not with the closed-form short cut.',
  ];
  L.forEach((t,i)=>{
    const col=i%2, row=Math.floor(i/2);
    const x=0.40+col*4.70, y=1.22+row*0.57;
    s.addText((i+1)+'.',{x,y,w:0.30,h:0.5,fontFace:F,fontSize:10,bold:true,color:YEL,margin:0});
    s.addText(t,{x:x+0.30,y,w:4.20,h:0.53,fontFace:F,fontSize:9,color:NAVY,margin:0,valign:'top'});
  });
}

/* ---------------- closing ---------------- */
{
  const s=pptx.addSlide(); s.background={color:NAVY};
  s.addText('Our technology\nstarts with You',{x:0.9,y:1.55,w:8.2,h:1.4,fontFace:F,fontSize:30,bold:true,color:WHITE,align:'center',margin:0});
  s.addShape(pptx.ShapeType.rect,{x:0,y:H-1.0,w:0.9,h:1.0,fill:{color:YEL}});
  s.addText('Accompanying files:   corrected design spreadsheet (CHANGELOG_rev0_6 sheet)  ·  SMath worksheet with SI units  ·  design guide rev 0.6',
    {x:0.9,y:3.35,w:8.2,h:0.4,fontFace:F,fontSize:10.5,color:'C8D4E4',align:'center',margin:0});
  s.addText('This deck is a study document. The L6790A datasheet is a DRAFT — re-verify against the released datasheet before any production design.',
    {x:0.9,y:3.80,w:8.2,h:0.4,fontFace:F,fontSize:9.5,italic:true,color:'9FB3CC',align:'center',margin:0});
  s.addImage({path:LOGO,x:8.6,y:H-0.85,w:0.9,h:0.70});
}

pptx.writeFile({fileName:'/mnt/user-data/outputs/L6790A_SingleStage_PF_LLC_Design_Training.pptx'})
  .then(()=>console.log('deck written'));
