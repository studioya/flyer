#!/usr/bin/env python3
"""Export the canvas pages as desktop PDFs (A4 landscape boards, A4 portrait CV), exactly as laid out."""
import glob, os, re, subprocess, sys, json
S = '/tmp/claude-0/-home-user/de665114-9855-5d3e-a296-c68bfd085cac/scratchpad/'
SRC = S + 'flyer/project/'; OUT = S + 'pdfm/out/'
DOCS = {'lasers-ceramics': (['Ceramics%02d' % i for i in range(1, 11)], 1123, 794),
        'parametric-objects': (['Parametric%02d' % i for i in range(1, 7)], 1123, 794),
        'aumbry-2.0': (['Aumbry%02d' % i for i in range(1, 7)], 1123, 794),
        'cv-yarden-amir': (['CV'], 794, 1123)}
blob = {os.path.basename(p).split('.')[0]: p for p in glob.glob(S + 'pdfm/blob/*')}
def page(fn):
    h = open(SRC + fn + '.dc.html').read()
    inner = re.sub(r'<helmet>[\s\S]*?</helmet>', '', h.split('<x-dc>', 1)[1].split('</x-dc>', 1)[0]).strip()
    return '<section class="pg">' + re.sub(r'/_blob/([0-9a-f]{32})', lambda m: 'file://' + blob[m.group(1)], inner) + '</section>'
only = sys.argv[1:] or list(DOCS)
jobs = {}
for d in only:
    files, W, H = DOCS[d]
    html = ('<!doctype html><html><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">'
            '<style>@page{size:%dpx %dpx;margin:0}html,body{margin:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}section.pg{width:%dpx;height:%dpx;overflow:hidden;break-after:page}a{color:#7A5A30;text-decoration:none}</style></head><body>' % (W, H, W, H)
            + ''.join(page(f) for f in files) + '</body></html>')
    p = OUT + d + '-desktop.html'; open(p, 'w').write(html); jobs[d] = [p, W, H]
js = """const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
for (const [d,[p,W,H]] of Object.entries(%s)) { const pg=await b.newPage({viewport:{width:W,height:H}});
 await pg.goto('file://'+p,{waitUntil:'networkidle'});await pg.evaluate(()=>document.fonts.ready);await pg.waitForTimeout(500);
 await pg.pdf({path:'%s'+d+'.pdf',width:W+'px',height:H+'px',printBackground:true,preferCSSPageSize:true});await pg.close();console.log('pdf',d);}
await b.close()})()""" % (json.dumps(jobs), OUT)
open(OUT + 'print_desktop.js', 'w').write(js)
subprocess.run(['node', OUT + 'print_desktop.js'], check=True)
