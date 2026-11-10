#!/usr/bin/env python3
"""Reusable Blue Sky photo placement.
Inputs : raken/index.json + raken/<month>.json (read-only), raken/photos/*.jpg (EXIF), placement/clip-cache.json
         (run clip_classify.py first for new photos), VIS visual calls embedded in src.html, plan bounds in placement/features.json
Output : placement/photo-place.json  {"date|s|j":[lat,lon,FEAT,conf,method]}   (inlined by build.py as __PLACE__)
         placement/placement-report.json (counts / low-confidence list)
Order  : EXIF GPS -> visual call (VIS, from photo+drawings) -> report text + CLIP visual -> fallback (general construction yard)."""
import json, os, re, glob, math, sys
from collections import defaultdict, Counter
HERE=os.path.dirname(os.path.abspath(__file__)); APP=os.path.dirname(HERE)
F=json.load(open(os.path.join(HERE,'features.json')))
B=F['bounds']; PW,PH=F['plan_px']
mx=lambda lon:(lon+180)/360; my=lambda lat:(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2
ilat=lambda y:math.degrees(math.atan(math.sinh(math.pi*(1-2*y))))
def p2ll(u,v):
    x=mx(B[0][1])+(mx(B[1][1])-mx(B[0][1]))*u/PW; y=my(B[0][0])+(my(B[1][0])-my(B[0][0]))*v/PH
    return ilat(y),x*360-180
FEAT=F['features']                       # code -> {label, rect:[u0,v0,u1,v1], band?, aff:{type:w}}
RULES=[(re.compile(r,re.I),f,w) for r,f,w in F['rules']]
VISMAP=F.get('vis_map',{})
def halton(i,b):
    f,r=1,0
    while i>0: f/=b; r+=f*(i%b); i//=b
    return r
def spot(code,i):
    u0,v0,u1,v1=FEAT[code]['rect']; band=FEAT[code].get('band')
    a,b=halton(i+1,2),halton(i+1,3)
    if band:   # spread around the working perimeter band (berms) of lagoons
        w,h=u1-u0,v1-v0; per=2*(w+h); t=a*per; d=band*(0.15+0.85*b)
        if t<w: u,v=u0+t,v0+d
        elif t<w+h: u,v=u1-d,v0+(t-w)
        elif t<2*w+h: u,v=u1-(t-w-h),v1-d
        else: u,v=u0+d,v1-(t-2*w-h)
    else:
        m=0.08; u=u0+(u1-u0)*(m+(1-2*m)*a); v=v0+(v1-v0)*(m+(1-2*m)*b)
    return p2ll(u,v)
def exif_gps(path):
    try:
        from PIL import Image
        g=Image.open(path).getexif().get_ifd(0x8825)
        if not g or 2 not in g: return None
        c=lambda t:float(t[0])+float(t[1])/60+float(t[2])/3600
        la,lo=c(g[2]),c(g[4]); la=-la if g.get(1)=='S' else la; lo=-lo if g.get(3)=='W' else lo
        return la,lo
    except Exception: return None
def load_vis():
    return json.load(open(os.path.join(HERE,'vis-calls.json')))
    s=''; i=-1
    if i<0: return {}
    j=s.find('};',i); return json.loads(s[i+10:j+1])
def main():
    ix=json.load(open(os.path.join(APP,'raken','index.json')))
    reps=[]
    for mo in ix['months']:
        p=os.path.join(APP,'raken',mo+'.json')
        if os.path.exists(p): reps+=json.load(open(p))['reports']
    clip=json.load(open(os.path.join(HERE,'clip-cache.json'))) if os.path.exists(os.path.join(HERE,'clip-cache.json')) else {}
    vis=load_vis(); out={}; rec=[]; queue=defaultdict(list)
    for r in sorted(reps,key=lambda r:r['date']):
        if r.get('pid')!='raken-bluesky': continue
        text=(r.get('notes') or '')+'\n'+'\n'.join(s.get('name','')+' '+s.get('items','') for s in r.get('subs',[]))
        dw=Counter()
        for sent in re.split(r'[\n.;]+',text):
            for rx,f,w in RULES:
                if rx.search(sent): dw[f]+=w
        tot=sum(dw.values()); dp={f:w/tot for f,w in dw.items()} if tot else {}
        for k in ('site','att'):
            for j,p in enumerate(r.get(k,[])):
                key=r['date']+'|'+k[0]+'|'+str(j); fn=os.path.basename(p.get('url','') or '')
                g=None
                if p.get('lat') is not None and p.get('lon') is not None: g=(p['lat'],p['lon'])
                elif fn: g=exif_gps(os.path.join(APP,'raken','photos',fn))
                if g:
                    out[key]=[round(g[0],6),round(g[1],6),'GPS','h','gps']; rec.append((key,'gps','GPS','h',None)); continue
                v=vis.get(r['id']+'|'+k+'|'+str(j))
                if v:
                    code=VISMAP.get(v[0],v[0]); conf=v[1]
                    if code in FEAT and conf in 'hm':
                        queue[code].append(key); rec.append((key,'visual+drawing',code,conf,v[2][:90])); continue
                ct=clip.get(fn,{})
                best=None
                for f,pw in dp.items():
                    aff=sum(ct.get(t,0)*w for t,w in FEAT[f]['aff'].items()) if ct else 0.3
                    sc=pw*(0.25+aff)
                    if best is None or sc>best[0]: best=(sc,f,pw,aff)
                if best:
                    sc,f,pw,aff=best; others=[x for x in dp if x!=f]
                    if pw>=0.6 and (aff>=0.2 or not ct): conf,meth='m','report-text'
                    elif aff>=0.45 and pw>=0.2: conf,meth='m','visual+drawing'
                    elif ct.get('doc',0)<0.5 and pw>=0.35 and aff>=0.3: conf,meth='m','report-text'
                    else: conf,meth='l','fallback'
                    if conf=='m' and f!='YARD':
                        queue[f].append(key); rec.append((key,meth,f,conf,'day text %.0f%% %s; visual %.2f'%(pw*100,FEAT[f]['label'],aff))); continue
                    guess=f
                else: guess=None
                queue['YARD'].append(key); rec.append((key,'fallback','YARD','l','guess '+(FEAT[guess]['label'] if guess else 'none')))
    for code,keys in queue.items():
        for i,key in enumerate(keys):
            la,lo=spot(code,i); out.setdefault(key,None)
            out[key]=[round(la,6),round(lo,6),code,None,None]
    for key,meth,code,conf,why in rec:
        if code=='GPS': continue
        out[key][3]=conf; out[key][4]={'gps':'g','visual+drawing':'v','report-text':'t','fallback':'f'}[meth]
    json.dump(out,open(os.path.join(HERE,'photo-place.json'),'w'),separators=(',',':'))
    bym=Counter(m for _,m,_,_,_ in rec); byf=Counter(c for _,_,c,_,_ in rec); byc=Counter(c for _,_,_,c,_ in rec)
    low=[{'photo':k,'why':w} for k,m,c,cf,w in rec if cf=='l']
    rep={'bounds':B,'total':len(rec),'by_method':bym,'by_feature':{c:{'n':n,'label':FEAT.get(c,{}).get('label',c)} for c,n in byf.most_common()},
         'by_confidence':byc,'low_confidence_count':len(low),'low_confidence_list':low}
    json.dump(rep,open(os.path.join(HERE,'placement-report.json'),'w'),indent=1)
    print(json.dumps({k:rep[k] for k in ('total','by_method','by_confidence','low_confidence_count')}))
    print({c:v['n'] for c,v in rep['by_feature'].items()})
if __name__=='__main__': main()
