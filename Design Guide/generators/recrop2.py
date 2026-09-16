from PIL import Image, ImageChops
import numpy as np
def cut(src,out,x0,y0,x1,y1,pad=14):
    im=Image.open(src).convert('L'); W,H=im.size
    box=(int(x0*W),int(y0*H),int(x1*W),int(y1*H))
    g=np.array(im.crop(box))
    ink=g<235
    rows=np.where(ink.any(1))[0]; cols=np.where(ink.any(0))[0]
    if len(rows)==0: raise SystemExit('empty '+out)
    r0,r1=rows[0],rows[-1]; c0,c1=cols[0],cols[-1]
    full=Image.open(src).convert('RGB')
    b=(box[0]+max(0,c0-pad), box[1]+max(0,r0-pad),
       box[0]+min(box[2]-box[0],c1+pad+1), box[1]+min(box[3]-box[1],r1+pad+1))
    full.crop(b).save(out)
    return Image.open(out).size
if __name__=='__main__':
    jobs=[
     # (page, out, x0,y0,x1,y1)  -- generous window, auto-trimmed to the ink
     ('fig/onsemi_p03.png','fig/f_llc_sch.png',   0.050,0.648,0.510,0.888),
     ('fig/onsemi_p03.png','fig/f_llc_wave.png',  0.500,0.030,0.995,0.425),
     ('fig/onsemi_p04.png','fig/f_ac_equiv.png',  0.048,0.285,0.510,0.680),
     ('fig/onsemi_p04.png','fig/f_gain_q.png',    0.495,0.615,0.995,0.912),
     ('fig/onsemi_p06.png','fig/f_opmodes.png',   0.048,0.560,0.510,0.905),
     ('fig/onsemi_p06.png','fig/f_modewave.png',  0.495,0.030,0.995,0.375),
     ('fig/onsemi_p06.png','fig/f_zvs_cap.png',   0.495,0.552,0.995,0.925),
     ('fig/onsemi_p07.png','fig/f_peakgain.png',  0.495,0.030,0.995,0.460),
     ('fig/onsemi_p07.png','fig/f_maxgain.png',   0.048,0.170,0.510,0.430),
     ('fig/inf_p06.png',   'fig/f_inf_gainq.png', 0.190,0.585,0.930,0.868),
     ('fig/inf_p08.png',   'fig/f_inf_gainm.png', 0.190,0.108,0.930,0.360),
     ('fig/inf_p12.png',   'fig/f_inf_modes.png', 0.045,0.098,0.995,0.292),
     ('fig/inf_p13.png',   'fig/f_inf_ires.png',  0.210,0.072,0.830,0.315),
    ]
    for j in jobs: print(j[1],cut(*j))
