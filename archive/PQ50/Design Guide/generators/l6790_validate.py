from l6790 import *
R=design(Cr_sel=33e-9, Lr_sel=34e-6, Lm_sel=65e-6, n_sel=2.5)
print('--- validate vs guide 240 W / 60 V example ---')
ref=[('Pin_LLC',244.90),('Iin_max',2.721),('Pd_BR',0.984),('Pd_EMI',1.111),('Pin',246.99),
     ('Vin_min',173.24),('n_calc',2.519),('MVmin',1.2245),('MVmax',0.8035),
     ('l1',0.2445),('l2',0.4401),('lTD',0.5413),('lam',0.5413),('Rac',37.24),
     ('Qz1',0.9736),('Qz2',4.073),('Qz',0.8466),('Z0',31.52),('Cr_c',33.66e-9),
     ('lam_a',0.5231),('nT',3.085),('Z0s',32.10),('Z0p',54.77),('fr',150.25e3),('fo',88.05e3),
     ('Lmu',80.22e-6),('LL1',18.78e-6),('LL2',1.973e-6),('Qpk',0.862)]
bad=0
for k,v in ref:
    g=R[k]; ok = abs(g-v)<=abs(v)*2e-3
    bad += 0 if ok else 1
    print(f'  {k:9s} guide={v:<12.6g} calc={g:<12.6g} {"OK" if ok else "** DIFF"}')
print('mismatches:',bad)

print()
print('--- fsw(theta) table, full load  [guide 4.2] ---')
print(f"{'theta':>6}"+"".join(f"{v:>12.4g}" for v in (173.24,180,225,264,332.34)))
for deg in (15,30,45,60,90):
    out=[]
    for V in (173.24,180.,225.,264.,332.34):
        rows,_=sweep(R,V); r=rows[round((deg/90)*180)-1]
        out.append(r['fsw']/1e3 if r else float('nan'))
    print(f"{deg:>5}d"+"".join(f"{x:>12.1f}" for x in out))

print()
print('--- [38a] Tzc sweep (ns), by load ---')
print(f"{'load':>6}"+"".join(f"{v:>10.4g}" for v in (173.24,180,225,264,332.34)))
for L in (1.0,0.75,0.5,0.25):
    out=[sweep(R,V,L)[1]['Tzc_min']*1e9 for V in (173.24,180.,225.,264.,332.34)]
    print(f"{L*100:>5.0f}%"+"".join(f"{x:>10.0f}" for x in out))

print()
rows,S=sweep(R,173.24)
print('--- worst corner 173.24 Vac, full load ---')
i=len(rows)-1; r=rows[i]
print(f"  theta=90d fsw={r['fsw']/1e3:.1f}k Isec_pk={r['Ipk']:.2f} Itr={r['Itr']:.3f} ILm={r['ILm']:.3f} "
      f"Ipri={r['Ipri']:.3f} Imos={r['Imos']:.3f} comp={r['comp']:.3f} Tzc={r['Tzc']*1e9:.0f}ns fn={r['fn']:.4f}")
print(f"  line-cycle rms: Isec={S['Isec_lc']:.3f} Idio={S['Idio_lc']:.3f} Ipri={S['Ipri_lc']:.3f} ICout={S['ICout']:.3f}")
print("  guide says   : Isec=6.185 Idio=4.374 Ipri=3.760 ICout=4.72 ; Isec_pk=15.42 Itr=6.169 ILm=3.840 Ipri=4.945 comp=6.660 Tzc=246")
