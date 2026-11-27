#!/usr/bin/env python3
"""Build phone-format versions of the portfolio PDFs from the canvas page sources.

Each landscape page is reflowed into one column on a 9:16 page: grids collapse to one
column (image galleries to two), images go full width at their natural shape, small
type is bumped up, running page numbers are dropped. Chrome paginates the result.
"""
import glob, os, re, subprocess, sys

S = '/tmp/claude-0/-home-user/de665114-9855-5d3e-a296-c68bfd085cac/scratchpad/'
SRC = S + 'flyer/project/'
OUT = S + 'pdfm/out/'
os.makedirs(OUT, exist_ok=True)
DOCS = {
    'lasers-ceramics': ['Ceramics%02d' % i for i in range(1, 11)],
    'parametric-objects': ['Parametric%02d' % i for i in range(1, 7)],
    'aumbry-2.0': ['Aumbry%02d' % i for i in range(1, 7)],
    'cv-yarden-amir': ['CV'],
}
blob = {os.path.basename(p).split('.')[0]: p for p in glob.glob(S + 'pdfm/blob_m/*')}

PW, PH = 420, 747          # CSS px; 9:16
CSS = """
@page { margin: 0; }
html, body { margin: 0; background: #FFFFFF; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
section.pg { padding: 30px 22px 34px; }
section.pg > div { width: auto !important; height: auto !important; min-height: 0 !important; padding: 0 !important;
  display: flex !important; flex-direction: column !important; gap: 20px !important; background: transparent !important; }
section.pg img { width: 100%% !important; height: auto !important; max-height: 540px; object-fit: cover; }
section.pg svg { max-width: 100%%; }
section.pg figure, section.pg img, section.pg tr, section.pg li { break-inside: avoid; }
section.pg h1, section.pg h2 { break-after: avoid; }
section.pg table { font-size: 10.5px !important; }
section.pg th { white-space: normal !important; vertical-align: bottom; }
section.pg td, section.pg th { padding-left: 4px !important; }
.mob-hide { display: none !important; }
section.pg > div > * { flex: none !important; }
section.pg div[style*="text-align: right"], section.pg span[style*="text-align: right"] { text-align: left !important; }
section.pg [style*="align-items: flex-end"] { align-items: flex-start !important; }
""" 

JS = r"""
(() => {
  const root = (s) => s.firstElementChild;
  document.querySelectorAll('section.pg').forEach((sec) => {
    const r = root(sec);
    sec.querySelectorAll('*').forEach((el) => {
      const st = el.getAttribute('style') || '';
      // grids: one column; image galleries of 3+ keep two
      if (getComputedStyle(el).display === 'grid') {
        const kids = [...el.children];
        const imgOnly = kids.every((k) => k.tagName === 'IMG' || (k.querySelector('img') && k.textContent.trim().length < 140));
        const allHaveImg = kids.every((k) => k.tagName === 'IMG' || k.querySelector('img'));
        const cols = (kids.length >= 3 && imgOnly) || (kids.length >= 4 && allHaveImg) ? 2 : 1;
        el.style.setProperty('grid-template-columns', 'repeat(' + cols + ', minmax(0, 1fr))', 'important');
        el.style.setProperty('grid-template-rows', 'none', 'important');
        el.style.setProperty('height', 'auto', 'important');
        kids.forEach((k) => {
          const span = /span/.test(k.getAttribute('style') || '') && cols === 2;
          k.style.setProperty('grid-column', span ? '1 / -1' : 'auto', 'important'); k.style.setProperty('grid-row', 'auto', 'important');
        });
      }
      // side-by-side flex rows wrap instead of squeezing
      const cs = getComputedStyle(el);
      if (cs.display === 'flex' && cs.flexDirection === 'row') el.style.setProperty('flex-wrap', 'wrap', 'important');
      // nothing wider than the column, nothing locked to a desktop height
      const w = parseFloat(el.style.width);
      if (el.style.width.endsWith('px') && w > 360 && el.tagName !== 'svg') el.style.setProperty('width', '100%', 'important');
      if (el.style.maxWidth && parseFloat(el.style.maxWidth) > 360) el.style.setProperty('max-width', '100%', 'important');
      if (el.tagName !== 'IMG' && el.style.height.endsWith('px') && parseFloat(el.style.height) > 60) el.style.setProperty('height', 'auto', 'important');
      // small print a step larger
      const fs = parseFloat(el.style.fontSize);
      if (fs && fs <= 12.5) el.style.setProperty('font-size', (fs + 1.5) + 'px', 'important');
      if (fs && fs > 60) el.style.setProperty('font-size', Math.round(fs * 0.86) + 'px', 'important');
    });
    // drop running page numbers; drop a footer that only held the site name
    sec.querySelectorAll('span, div').forEach((el) => {
      if (el.children.length === 0 && /^\d{2}$/.test(el.textContent.trim())) {
        el.classList.add('mob-hide');
        const row = el.parentElement;
        if (row && /^yardenamir\.com$/.test(row.textContent.replace(/\d{2}\s*$/, '').trim())) row.classList.add('mob-hide');
      }
    });
  });
  window.__heights = [...document.querySelectorAll('section.pg')].map((sec) => Math.ceil(sec.getBoundingClientRect().height));
  document.body.dataset.ready = '1';
})();
"""


def page_html(fn):
    h = open(SRC + fn + '.dc.html').read()
    inner = h.split('<x-dc>', 1)[1].split('</x-dc>', 1)[0]
    inner = re.sub(r'<helmet>[\s\S]*?</helmet>', '', inner).strip()
    def sub(m):
        p = blob.get(m.group(1))
        assert p, 'missing image ' + m.group(1)
        return 'file://' + p
    inner = re.sub(r'/_blob/([0-9a-f]{32})', sub, inner)
    # the canvas pages are fixed-size boards; make each a flowing section
    return '<section class="pg">' + inner + '</section>'


def build(doc, files):
    html = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<link href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">'
            '<style>' + CSS + '</style></head><body>' + ''.join(page_html(f) for f in files)
            + '<script>' + JS + '</script></body></html>')
    path = OUT + doc + '-mobile.html'
    open(path, 'w').write(html)
    return path


if __name__ == '__main__':
    only = sys.argv[1:] or list(DOCS)
    paths = {d: build(d, DOCS[d]) for d in only}
    js = """
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();
for (const [doc,p] of Object.entries(%s)) {
  const pg=await b.newPage({viewport:{width:%d,height:900}});
  await pg.goto('file://'+p,{waitUntil:'networkidle'});await pg.waitForFunction(()=>document.body.dataset.ready==='1');
  await pg.evaluate(()=>document.fonts.ready);await pg.waitForTimeout(400);
  const hs=await pg.evaluate(()=>window.__heights);
  for (let i=0;i<hs.length;i++){
    const h=await pg.evaluate((i)=>{document.querySelectorAll('section.pg').forEach((s,j)=>s.style.display=j===i?'':'none');return Math.ceil(document.querySelectorAll('section.pg')[i].getBoundingClientRect().height);},i);
    await pg.pdf({path:'%s'+doc+'-part'+String(i).padStart(2,'0')+'.pdf',width:'%dpx',height:(h+4)+'px',printBackground:true});
    hs[i]=h;
  }
  await pg.close();console.log('pdf',doc,hs.join(','));
}
await b.close()})()""" % (repr(paths).replace("'", '"'), PW, OUT, PW)
    open(OUT + 'print.js', 'w').write(js)
    subprocess.run(['node', OUT + 'print.js'], check=True)
    for d in only:
        parts = sorted(glob.glob(OUT + d + '-part*.pdf'))
        subprocess.run(['pdfunite'] + parts + [OUT + d + '-mobile.pdf'], check=True)
        for x in parts: os.remove(x)
