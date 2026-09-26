# -*- coding: utf-8 -*-
"""Minimal expression -> SMath RPN (with display brackets) + worksheet builder."""
import re, base64, html
from PIL import Image

# ---------------- tokenizer / parser ----------------
TOK=re.compile(r"\s*(?:(?P<num>\d+\.?\d*(?:[eE][-+]?\d+)?)|(?P<unit>'[A-Za-zμΩ°]+)|"
               r"(?P<id>[A-Za-zα-ωΑ-Ωπφλδη_][A-Za-zα-ωΑ-Ωπφλδη_0-9]*(?:\.[A-Za-z0-9_]+)*)|"
               r"(?P<op>\*\*|[-+*/^(),]))")
def lex(s):
    out=[];i=0
    while i<len(s):
        m=TOK.match(s,i)
        if not m:
            if s[i].isspace(): i+=1; continue
            raise SyntaxError(f'bad char {s[i]!r} in {s}')
        i=m.end()
        for k in ('num','unit','id','op'):
            if m.group(k): out.append((k,m.group(k))); break
    out.append(('end',''));return out

class P:
    def __init__(s,t): s.t=t; s.i=0
    def pk(s): return s.t[s.i]
    def nx(s): s.i+=1; return s.t[s.i-1]
    def expect(s,v):
        k,x=s.nx()
        if x!=v: raise SyntaxError(f'expected {v} got {x}')
    def expr(s,rbp=0):
        left=s.nud()
        while True:
            k,v=s.pk()
            if k!='op' or v not in BP or BP[v][0]<=rbp: break
            s.nx()
            if v=='^': right=s.expr(BP[v][0]-1)      # right-assoc
            else:      right=s.expr(BP[v][0])
            left=('op',v,left,right)
        return left
    def nud(s):
        k,v=s.nx()
        if k=='num': return ('num',v)
        if k=='unit': return ('unit',v[1:])
        if k=='id':
            if s.pk()==('op','('):
                s.nx(); args=[]
                if s.pk()!=('op',')'):
                    args.append(s.expr())
                    while s.pk()==('op',','): s.nx(); args.append(s.expr())
                s.expect(')')
                return ('fun',v,args)
            return ('var',v)
        if k=='op' and v=='(':
            e=s.expr(); s.expect(')'); return e
        if k=='op' and v=='-': return ('neg',s.expr(BP['*'][0]))
        raise SyntaxError(f'unexpected {v}')
BP={'+':(2,),'-':(2,),'*':(3,),'/':(3,),'^':(5,)}
def parse(s): return P(lex(s)).expr()

# ---------------- RPN emitter with brackets ----------------
def prec(n):
    if n[0]=='op': return {'+':2,'-':2,'*':3,'/':3,'^':5}[n[1]]
    if n[0]=='neg': return 4
    return 9
def emit(n, need_bracket=False, out=None):
    out=[] if out is None else out
    start=len(out)
    if n[0]=='num':  out.append(('operand',n[1],None))
    elif n[0]=='unit': out.append(('operand',n[1],'unit'))
    elif n[0]=='var': out.append(('operand',n[1],None))
    elif n[0]=='neg':
        emit(n[1], prec(n[1])<4, out); out.append(('operator','-',1))
    elif n[0]=='fun':
        for a in n[2]: emit(a,False,out)
        out.append(('function',n[1],len(n[2])))
    elif n[0]=='op':
        o=n[1]; a,b=n[2],n[3]; p=prec(n)
        if o=='/':      # rendered as a fraction: children never need brackets
            emit(a,False,out); emit(b,False,out)
        elif o=='^':    # base may need one, exponent is superscript
            emit(a, prec(a)<9, out); emit(b,False,out)
        elif o=='*':
            emit(a, prec(a)<3, out); emit(b, prec(b)<3, out)
        elif o=='+':
            emit(a,False,out);       emit(b, prec(b)<2, out)
        elif o=='-':
            emit(a,False,out);       emit(b, prec(b)<=2, out)
        out.append(('operator',o,2))
    if need_bracket: out.append(('bracket','(',None))
    return out
def rpn_xml(elems, indent='        '):
    L=[]
    for t in elems:
        if t[0]=='bracket': L.append(f'{indent}<e type="bracket">(</e>')
        elif t[0]=='operand':
            st=' style="unit"' if t[2]=='unit' else ''
            L.append(f'{indent}<e type="operand"{st}>{html.escape(t[1])}</e>')
        else:
            L.append(f'{indent}<e type="{t[0]}" args="{t[2]}">{html.escape(t[1])}</e>')
    return '\n'.join(L)
def expr_rpn(src):  return emit(parse(src))
def assign_rpn(lhs,src):
    e=[('operand',lhs,None)]+expr_rpn(src)+[('operator',':',2)]
    return e

# ---------------- worksheet ----------------
class Sheet:
    def __init__(s,title,author,desc):
        s.r=[];s.y=9;s.title=title;s.author=author;s.desc=desc
        s.paper_id=1;s.paper_or='Portrait';s.paper_w=850;s.paper_h=1100;s.gap=20
        s.cols=None;s.ci=0;s.colx=[9];s.colh=10**9;s.ytop=9;s.maxy=9
    def setcols(s,xs,colh,ytop=9,colw=None):
        s.colx=xs; s.colh=colh; s.ci=0; s.ytop=ytop; s.y=ytop; s.cols=True
        s.colw=colw or ((xs[1]-xs[0]-25) if len(xs)>1 else 760)
    def _brk(s,h):
        if s.cols and s.y+h>s.colh and s.ci<len(s.colx)-1:
            s.ci+=1; s.y=s.ytop
    def _reg(s,body,h,w=760,x=None,extra=''):
        s._brk(h)
        xx=s.colx[s.ci] if x is None else x
        if s.cols: w=min(w,s.colw)
        s.r.append(f'  <region left="{xx}" top="{s.y}" width="{w}" height="{h}" '
                   f'color="#000000" bgColor="#ffffff"{extra}>\n{body}\n  </region>')
        s.y+=h+s.gap
        if s.y>s.maxy: s.maxy=s.y
    def text(s,lines,size=10,bold=False,box=False,color='#000000',w=760):
        if isinstance(lines,str): lines=[lines]
        attr = ' bold="true"' if bold else ''      # no backslash inside an f-string: Python 3.11
        ps=''.join(f'<p{attr}>{html.escape(l)}</p>' for l in lines)
        extra=' border="true" bgColor="#dde8f0"' if box else ''
        h=(19 if size<=8 else 27)*len(lines)+12
        s._brk(h)
        xx=s.colx[s.ci]
        if s.cols: w=min(w,s.colw)
        s.r.append(f'  <region left="{xx}" top="{s.y}" width="{w}" height="{h}" '
                   f'color="{color}"{extra} fontSize="{size}">\n    <text lang="eng">\n      {ps}\n    </text>\n  </region>')
        s.y+=h+s.gap
        if s.y>s.maxy: s.maxy=s.y
    def head(s,t):
        s.text([t],size=11,bold=True,box=True,color='#0f2a44',w=560)
    def math(s,lhs,src,desc='',h=None,contract=None):
        e=assign_rpn(lhs,src)
        d=f'\n      <description active="true" position="Right" lang="eng"><p>{html.escape(desc)}</p></description>' if desc else ''
        c=''
        if contract:
            c='\n      <contract>\n'+rpn_xml(expr_rpn(contract))+'\n      </contract>'
        body=f'    <math>{d}\n      <input>\n{rpn_xml(e)}\n      </input>{c}\n    </math>'
        s._reg(body, int((h or (34+22*src.count('/')))*1.30))
    def show(s,src,desc='',contract=None,h=32):
        e=expr_rpn(src)
        d=f'\n      <description active="true" position="Right" lang="eng"><p>{html.escape(desc)}</p></description>' if desc else ''
        c=''
        if contract:
            c='\n      <contract>\n'+rpn_xml(expr_rpn(contract))+'\n      </contract>'
        r='\n      <result action="numeric">\n        <e type="operand">0</e>\n      </result>'
        body=f'    <math>{d}\n      <input>\n{rpn_xml(e)}\n      </input>{c}{r}\n    </math>'
        s._reg(body,int(h*1.25))
    def pic(s,path,cap=None,w=560):
        im=Image.open(path); ww,hh=im.size
        h=int(w*hh/ww)
        b=base64.b64encode(open(path,'rb').read()).decode()
        body=f'    <picture>\n      <raw format="png" encoding="base64">{b}</raw>\n    </picture>'
        s._reg(body,h,w=w)
        if cap: s.text([cap],size=8)
    def save(s,path):
        xml=('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
             '<?application progid="SMath Studio" version="1.5.0.9678"?>\n'
             '<regions xmlns="http://smath.info/schemas/worksheet/1.0">\n'
             '  <settings>\n'
             '    <identity><id>7f3a1c90-1111-4a55-9e21-0c6d5b8e4a02</id><revision>1</revision></identity>\n'
             f'    <metadata lang="eng"><title>{html.escape(s.title)}</title><author>{html.escape(s.author)}</author>'
             f'<description>{html.escape(s.desc)}</description></metadata>\n'
             '    <calculation><precision>4</precision><exponentialThreshold>5</exponentialThreshold><fractions>decimal</fractions></calculation>\n'
             '    <pageModel active="true" viewMode="0" printGrid="false" printAreas="true" simpleEqualsOnly="false" printBackgroundImages="true">'
             f'<paper id="{s.paper_id}" orientation="{s.paper_or}" width="{s.paper_w}" height="{s.paper_h}"/><margins left="20" right="20" top="20" bottom="20"/>'
             '<header alignment="Center" color="#a9a9a9">&amp;[TITLE]</header><footer alignment="Center" color="#a9a9a9">&amp;[PAGENUM] / &amp;[COUNT]</footer>'
             '<backgrounds/></pageModel>\n'
             '    <dependencies><assembly name="SMath Studio Desktop" version="1.5.0.9678" guid="a37cba83-b69c-4c71-9992-55ff666763bd"/></dependencies>\n'
             '  </settings>\n'+'\n'.join(s.r)+'\n</regions>\n')
        open(path,'w',encoding='utf-8').write(xml)
        return len(xml)
