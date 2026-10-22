import base64,json
b=lambda f,m:'data:%s;base64,'%m+base64.b64encode(open(f,'rb').read()).decode()
ts=int(__import__('datetime').datetime(2026,10,22,7,51).timestamp()*1000)
ph=lambda ids:[{"src":b(f"seed/i-{i:03d}.jpg","image/jpeg"),"ts":ts,"cap":""} for i in ids]
seed={"projects":[{"id":"sample-bluesky","name":"Test","job":"","address":"1591 200th Ave Lewis , KS 67552","lat":"","lon":"","by":"Bryan Ricca","subs":["Bennett","Eck Service","Titan"]}],
"reports":[{"id":"sample-bluesky-20261021","pid":"sample-bluesky","date":"2026-10-21","by":"Bryan Ricca","site":ph([6,7,8,9]),"att":ph([48,49,50,51,56,57,58,59]),
"wx":[{"t":56,"c":"Partially cloudy","w":14,"p":".0","h":90},{"t":67,"c":"Clear","w":5,"p":".0","h":59},{"t":76,"c":"Clear","w":7,"p":".0","h":48}],
"notes":"DMT completed the logic and controls work. Dominic (Hartman) can now collect gas samples and send them to the laboratory for analysis.\nThe 18-inch corrugated pipe at the south lagoon has been corrected to the proper elevation. The EFI crew still needs to weld a boot around the pipe to complete the repair.\nA major electrical issue occurred on the dairy side when the service pole connection to the main transformer disconnect completely melted, causing the lagoon feed pumps to shut down. A backup plan was implemented using a generator to power the pumps. The pumps are currently operating at a steady pace at 45 Hz.",
"subs":[{"name":"Bennett","items":"Backfilling the open trenches around both the north and south lagoons.\nRemoving and reinstalling the 18-inch corrugated pipe at the correct elevation to align with the outlet box.\nContinuing overhead pipe welding for the sand removal system."},
{"name":"Eck Service","items":"Relocated the BOP panels to the Kansas gas site.\nInstalling ground rings around the Phase 3 building."},{"name":"Titan","items":"On site installing roll-up garage doors."}],
"survey":[{"a":"N/A","d":""} for _ in range(6)],"sig":b("seed/sig.png","image/png"),"sigTs":ts}]}
s=open('src.html').read().replace('__SEED__',json.dumps(seed)).replace('__LOGO__',b('logo.png','image/png')).replace('__FAV__',b('fav.png','image/png'))
import time;V=time.strftime('%Y%m%d%H%M%S');s=s.replace('__VER__',V);open('index.html','w').write(s);open('version.json','w').write(json.dumps({'v':V}))
