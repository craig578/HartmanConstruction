#!/workspace/.clipenv/bin/python
"""Visual type scores for Raken photos (CLIP ViT-B-32, zero-shot). Incremental cache.
Usage: clip_classify.py [photo_dir] [cache.json]"""
import sys, os, json, torch, open_clip
from PIL import Image
HERE=os.path.dirname(os.path.abspath(__file__))
PD=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,'..','raken','photos')
CACHE=sys.argv[2] if len(sys.argv)>2 else os.path.join(HERE,'clip-cache.json')
TYPES={
 'lagoon':["a large lagoon pond with a black plastic liner","geomembrane liner on an earthen berm","a black covered lagoon digester cover with ballast pipes","a manure storage pond"],
 'concrete':["tall concrete walls being formed with rebar for a large tank","concrete wall forms and scaffolding","a concrete pump truck pouring walls","inside a large concrete tank under construction"],
 'slab':["rebar mat laid on the ground for a concrete slab","a freshly poured flat concrete slab","workers finishing a concrete slab"],
 'steelbldg':["a steel frame building under construction","a metal building with roll-up garage doors","spray foam insulation inside a metal building","metal roof panels being installed"],
 'interior':["inside an office with drywall and paint","laboratory cabinets and counters","a finished office room interior","a restroom interior"],
 'electrical':["electrical panels and switchgear","conduit and cable tray with wires","an electrical transformer","a large diesel generator"],
 'piping':["stainless steel process piping and valves","an industrial equipment skid with pipes and pumps","black HDPE pipe being fusion welded","pipe insulation with aluminum jacket"],
 'earthwork':["an excavator digging a trench","a bulldozer moving dirt on a construction site","backfilling a trench with soil","a dirt road on a construction site"],
 'barn':["a dairy barn with cows","inside a large open freestall barn","a long dairy barn roof"],
 'pit':["an octagonal concrete manure pit","a round concrete pit with pumps","a manure pit with agitator"],
 'crane':["a crane lifting heavy equipment","a mobile crane setting a module"],
 'flare':["a biogas flare stack"],
 'doc':["a photo of a paper document or drawing","a screenshot of text","a delivery ticket"],
}
names=list(TYPES)
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
files=[f for f in sorted(os.listdir(PD)) if f.lower().endswith(('.jpg','.jpeg','.png')) and f not in cache]
print('to classify',len(files),'cached',len(cache),flush=True)
if files:
  torch.set_num_threads(os.cpu_count())
  m,_,pre=open_clip.create_model_and_transforms('ViT-B-32',pretrained='laion2b_s34b_b79k'); m.eval()
  tok=open_clip.get_tokenizer('ViT-B-32')
  prompts=[(n,p) for n in names for p in TYPES[n]]
  with torch.no_grad():
    T=m.encode_text(tok([p for _,p in prompts])); T/=T.norm(dim=-1,keepdim=True)
    for i in range(0,len(files),64):
      b=files[i:i+64]; ims=[]
      for f in b:
        try: ims.append(pre(Image.open(os.path.join(PD,f)).convert('RGB')))
        except Exception: ims.append(torch.zeros(3,224,224))
      I=m.encode_image(torch.stack(ims)); I/=I.norm(dim=-1,keepdim=True)
      S=(100*I@T.T)
      for k,f in enumerate(b):
        # max over prompts per type, softmax over types
        tv=torch.stack([S[k,[j for j,(n,_) in enumerate(prompts) if n==t]].max() for t in names])
        pr=tv.softmax(0).tolist(); cache[f]={t:round(p,3) for t,p in zip(names,pr)}
      if (i//64)%10==0:
        print(i+len(b),flush=True); json.dump(cache,open(CACHE,'w'))
  json.dump(cache,open(CACHE,'w'))
print('done',len(cache))
