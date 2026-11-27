#!/usr/bin/env python3
"""Build Flyer v5 (the whole flyer is the laser sheet) from the live v3 page."""
import math, re, sys, urllib.parse

SRC = '/home/user/flyer/index.html'
OUT = '/home/user/flyer/v5/index.html'
s = open(SRC).read()

head_html, rest = s.split('<div id="app">', 1)
body_html = rest.split('<script>', 1)[0]
script = rest.split('<script>', 1)[1].split('</script>', 1)[0]

# --- page content: drop the v3 bed block (from the bed wrapper to the blank line before the headline)
start = body_html.index('<div style="display: flex; flex-direction: column; opacity: 1;')
end = body_html.index('\n\n', start)
content = body_html[:start] + body_html[end + 2:]
content = content.rstrip()
assert content.endswith('</div>'), content[-80:]
content = content[: -len('</div>')].rstrip()  # remove the closing tag of #app
content = content.replace('src="img/', 'src="../img/')
_hdr = '</svg><span style="font-size: 28px; font-weight: 500; letter-spacing: -0.005em; line-height: 1">Yarden Amir</span>'
assert content.count(_hdr) == 1
content = content.replace(_hdr, '</svg>')
_h0 = content.index('<div style="display: flex; align-items: center; gap: 11px"><svg width="32"')
_s0 = content.index('<svg', _h0); _s1 = content.index('</svg>', _s0) + len('</svg>')
LOGO_INNER = content[content.index('>', _s0) + 1:_s1 - len('</svg>')]
content = content[:_s0] + content[_s0:_s1].replace('<svg width="32" height="32"', '<svg width="40" height="40"', 1) + content[_s1:]
import json as _json
assert content.count('>Yarden is looking for the next thing.</h1>') == 1
content = content.replace('>Yarden is looking for the next thing.</h1>', '>Yarden Amir is looking for the next thing.</h1>')
for gone in ('id="bed"', 'id="cut"', 'id="shareBtn"', 'id="hint"'):
    assert gone not in content, gone
assert 'id="shareLinkBtn"' in content and 'id="linkMsg"' in content

FIT = r"""  fitStroke(raw, closed, pinEnd) {
    // Even spacing, then a light [1,2,1] smoothing: keeps the hand in the line, takes the jitter out.
    let src = raw.slice();
    if (closed && src.length > 2 && Math.hypot(src[0][0] - src[src.length - 1][0], src[0][1] - src[src.length - 1][1]) < 1) src.pop();
    const loop = closed ? src.concat([src[0]]) : src;
    const STEP = 3, res = [loop[0].slice()];
    let need = STEP;
    for (let i = 1; i < loop.length; i++) {
      let a = res.length && i === 1 ? loop[0].slice() : loop[i - 1].slice();
      const b = loop[i];
      let L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      while (L >= need) {
        const t = need / L;
        a = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
        res.push(a); L -= need; need = STEP;
      }
      need -= L;
    }
    if (closed) { if (res.length > 3 && Math.hypot(res[res.length - 1][0] - res[0][0], res[res.length - 1][1] - res[0][1]) < STEP * 0.6) res.pop(); }
    else { const e = loop[loop.length - 1]; if (Math.hypot(e[0] - res[res.length - 1][0], e[1] - res[res.length - 1][1]) > 0.5) res.push(e.slice()); }
    let p = res;
    const n = p.length;
    if (n >= 3) for (let pass = 0; pass < 3; pass++) {
      const q = p.map((v) => v.slice());
      for (let i = 0; i < n; i++) {
        if (!closed && (i === 0 || i === n - 1)) continue;
        const A = p[(i - 1 + n) % n], B = p[(i + 1) % n];
        q[i] = [(A[0] + 2 * p[i][0] + B[0]) / 4, (A[1] + 2 * p[i][1] + B[1]) / 4];
      }
      p = q;
    }
    // drop points that add nothing (Ramer-Douglas-Peucker, 0.45 px)
    const keep = new Array(p.length).fill(false);
    const rdp = (i, j) => {
      let dmax = 0, k = -1;
      for (let m = i + 1; m < j; m++) { const d = this.distSeg(p[m], p[i], p[j]); if (d > dmax) { dmax = d; k = m; } }
      if (dmax > 0.45 && k > 0) { keep[k] = true; rdp(i, k); rdp(k, j); }
    };
    keep[0] = true; keep[p.length - 1] = true; rdp(0, p.length - 1);
    let out = p.filter((v, i) => keep[i]).map((v) => this.clampP(v));
    if (closed) out.push(out[0]);
    return { pts: out, closed, nodes: closed ? [] : [out[0], out[out.length - 1]], cut: false };
  }
"""

# --- geometry from v3 (stroke fitting, joining, faces, parts)
g0 = script.index('  // ---------- geometry')
g1 = script.index('  // ---------- input ----------')
geo = script[g0:g1]
geo = re.sub(r'  clampP\(p\) \{[^\n]*\n',
             '  clampP(p) { return [Math.max(4, Math.min(this.W - 4, p[0])), Math.max(4, Math.min(this.H - 4, p[1]))]; }\n', geo)
assert 'this.W - 4' in geo
_f0 = geo.index('  fitStroke(raw, closed, pinEnd) {'); _f1 = geo.index('  // ---------- joining strokes into shapes ----------')
geo = geo[:_f0] + FIT + '\n' + geo[_f1:]
p0 = script.index('  plateSVG(r) {')
p1 = script.index('  async prepareStory() {')
plate_js = script[p0:p1]  # plateSVG, svgImage, innerPath

# --- honeycomb tile for the bed under the flyer
r = 7.0
w = math.sqrt(3) * r
def hexp(cx, cy):
    return 'M' + 'L'.join(f'{cx + r * math.cos(math.pi / 6 + k * math.pi / 3):.2f} {cy + r * math.sin(math.pi / 6 + k * math.pi / 3):.2f}' for k in range(6)) + 'Z'
tile = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{3*r:.3f}">'
        f'<path d="{"".join(hexp(x, y) for x, y in [(0,0),(w,0),(w/2,1.5*r),(0,3*r),(w,3*r)])}" fill="none" stroke="#3A3733" stroke-width="1.1"/></svg>')
tile_uri = 'data:image/svg+xml,' + urllib.parse.quote(tile)

MONO = "'IBM Plex Mono', ui-monospace, Menlo, monospace"

head_html = head_html.replace('<meta property="og:url" content="https://job.yardenamir.com">',
                              '<meta property="og:url" content="https://job.yardenamir.com/v5/">\n<meta name="robots" content="noindex">')
head_html = head_html.replace('<meta name="description" content="Yarden Amir is on a job hunt. Draw on the laser bed, then press Cut.">',
                              '<meta name="description" content="Yarden Amir is on a job hunt. Arm the laser and cut a piece out of his flyer.">')
head_html = head_html.replace('display=swap" rel="stylesheet">', 'display=swap" rel="stylesheet" crossorigin="anonymous">')
assert 'crossorigin="anonymous"' in head_html
assert 'noindex' in head_html and 'Arm the laser' in head_html

CSS = f"""
html,body{{margin:0;background:#F1E9DC}}
html{{-webkit-text-size-adjust:100%;text-size-adjust:100%}}
button,#warn{{-webkit-tap-highlight-color:transparent}}
#stage{{position:relative;max-width:480px;margin:0 auto}}
#bedBg{{position:absolute;inset:0;background:#1E1D1B url("{tile_uri}");background-size:{w:.3f}px {3*r:.3f}px;z-index:0}}
#app{{position:relative;z-index:1;max-width:none}}
#app > div{{padding-bottom:132px !important}}
#ov,#rig{{position:absolute;left:0;top:0;display:block;overflow:visible}}
#ov{{z-index:2;pointer-events:none}}
#pieces{{position:absolute;inset:0;z-index:3;pointer-events:none}}
#rig{{z-index:6;pointer-events:none}}
.piece{{position:absolute;left:0;top:0;filter:drop-shadow(0 6px 7px rgba(38,36,34,.38)) drop-shadow(0 1px 1px rgba(38,36,34,.3));will-change:transform}}
#lid{{position:fixed;inset:0;z-index:7;pointer-events:none;perspective:1600px;perspective-origin:50% 0;display:none}}
#lid .frame{{position:absolute;inset:0;transform-origin:50% 0;border:solid #2B2927;border-width:30px 16px calc(118px + env(safe-area-inset-bottom));box-shadow:inset 0 0 0 1px #4E4B46,0 24px 50px rgba(0,0,0,.45)}}
#lid .glass{{position:absolute;inset:0;background:linear-gradient(118deg,rgba(255,255,255,0) 14%,rgba(255,255,255,.30) 19%,rgba(255,255,255,.06) 24%,rgba(255,255,255,0) 30%,rgba(255,255,255,0) 55%,rgba(255,255,255,.18) 58%,rgba(255,255,255,0) 63%),linear-gradient(180deg,rgba(255,255,255,.16),rgba(255,255,255,0) 22%,rgba(255,255,255,0) 80%,rgba(255,255,255,.08)),rgba(214,150,90,.07);box-shadow:inset 0 0 0 1px rgba(255,255,255,.35),inset 0 1px 0 rgba(255,255,255,.6),inset 0 0 40px rgba(40,18,6,.12)}}
#lid .label{{position:absolute;left:0;right:0;top:-22px;text-align:center;font-family:{MONO};font-size:10px;letter-spacing:.14em;color:#C79A5B}}
#lid .handle{{position:absolute;left:28%;right:28%;bottom:-20px;height:9px;border-radius:5px;background:linear-gradient(#6A6660,#45423E);box-shadow:0 2px 3px rgba(0,0,0,.5)}}
html.locked,html.locked body{{overflow:hidden;overscroll-behavior:none}}
html.locked #ov{{pointer-events:auto;touch-action:none;cursor:crosshair}}
#scrim{{position:fixed;inset:0;z-index:4;background:rgba(38,36,34,.32);display:none}}
#warn{{position:fixed;left:50%;top:44%;transform:translate(-50%,-50%);z-index:5;width:min(318px,calc(100vw - 56px));box-sizing:border-box;
  background:#C79A5B;color:#262422;border:1px solid rgba(38,36,34,.3);box-shadow:0 20px 44px rgba(0,0,0,.38);padding:30px 22px 24px;
  text-align:center;font-family:{MONO};cursor:pointer;display:none;-webkit-tap-highlight-color:transparent}}
#warn .w1{{font-weight:500;font-size:24px;line-height:1.25;letter-spacing:.06em}}
#warn .w2{{font-size:13px;margin-top:14px;animation:blink 1.3s steps(2,start) infinite}}
#warn .w3{{font-size:12.5px;line-height:1.55;margin-top:18px;padding-top:14px;border-top:1px dashed rgba(38,36,34,.45);text-align:left}}
@keyframes blink{{to{{opacity:.35}}}}
#dock{{position:fixed;left:0;right:0;bottom:0;z-index:8;max-width:480px;margin:0 auto;box-sizing:border-box;padding:0 12px calc(12px + env(safe-area-inset-bottom))}}
#panel{{background:#262422;color:#F1E9DC;box-shadow:0 10px 28px rgba(0,0,0,.28);padding:10px;display:flex;flex-direction:column;gap:8px;font-family:{MONO}}}
#status{{display:flex;justify-content:space-between;gap:10px;font-size:11.5px;line-height:1.4;color:rgba(241,233,220,.78);min-height:16px;padding:0 2px}}
#status b{{font-weight:500;white-space:nowrap}}
.row{{display:grid;gap:8px}}
.row3{{grid-template-columns:1.3fr 1fr 1fr}}
.row2{{grid-template-columns:1.4fr 1fr}}
.btn{{min-height:46px;border:1px solid rgba(241,233,220,.55);background:transparent;color:#F1E9DC;font-family:{MONO};font-weight:500;font-size:13.5px;letter-spacing:.08em;cursor:pointer;border-radius:0;padding:0 8px}}
.btn.primary{{background:#B4593A;border-color:#B4593A;color:#fff}}
.btn:disabled{{opacity:.38;cursor:default}}
.btn:focus-visible,.arm:focus-visible,#warn:focus-visible{{outline:2px solid #C79A5B;outline-offset:2px}}
.arm{{position:relative;display:flex;align-items:center;gap:14px;width:100%;min-height:68px;padding:0 18px 0 14px;border:0;border-radius:0;
  background:#262422;color:#F1E9DC;font-family:{MONO};cursor:pointer;text-align:left}}
.arm .ants{{position:absolute;inset:5px;width:calc(100% - 10px);height:calc(100% - 10px);overflow:visible;pointer-events:none}}
.arm .ants rect{{fill:none;stroke:#C79A5B;stroke-width:1.2;stroke-dasharray:7 5;animation:march 1.1s linear infinite}}
@keyframes march{{to{{stroke-dashoffset:-24}}}}
.arm .lz{{flex:none;position:relative;width:34px;height:34px;background:#3E3D39;border:1px solid #5A5852;display:grid;place-items:center}}
.arm .lz::before{{content:"";position:absolute;left:-6px;right:-6px;top:50%;height:1px;background:rgba(199,154,91,.55)}}
.arm .lz::after{{content:"";position:absolute;top:-6px;bottom:-6px;left:50%;width:1px;background:rgba(199,154,91,.55)}}
.arm .lz i{{position:relative;z-index:1;width:10px;height:10px;border-radius:50%;background:#B4593A;animation:pulse 1.6s ease-out infinite}}
@keyframes pulse{{0%{{box-shadow:0 0 0 0 rgba(180,89,58,.85),0 0 6px 2px rgba(180,89,58,.9)}}100%{{box-shadow:0 0 0 12px rgba(180,89,58,0),0 0 6px 2px rgba(180,89,58,.9)}}}}
.arm .t{{flex:1;display:flex;flex-direction:column;gap:3px}}
.arm .t b{{font-weight:500;font-size:16px;letter-spacing:.12em}}
.arm .t small{{font-size:12px;color:rgba(241,233,220,.72);letter-spacing:.01em}}
.arm .go{{flex:none;font-size:20px;color:#C79A5B;transition:transform .2s}}
.arm:hover .go{{transform:translateX(4px)}}
.arm.compact{{min-height:52px}}
.arm.compact .t small{{display:none}}
#shareMsg{{font-size:11.5px;line-height:1.4;color:rgba(241,233,220,.72);min-height:16px;padding:0 2px}}
@media (prefers-reduced-motion: reduce){{.arm .ants rect,.arm .lz i,#warn .w2{{animation:none}}}}
"""

head_html = re.sub(r'<style>[\s\S]*?</style>', '<style>' + CSS + '</style>', head_html)

DOCK = """
<div id="scrim"></div>

<div id="warn" role="button" tabindex="0" aria-label="Laser cutters are not a game. Tap the sheet to play. Draw on the flyer, close a shape and press Cut; that piece of the flyer lifts out.">
<div class="w1">LASER CUTTERS<br>ARE NOT A GAME!</div>
<div class="w2">&#9654; tap the sheet to play</div>
<div class="w3">Draw on the flyer with your finger. Close a shape, press Cut, and that piece of the flyer lifts out.</div>
</div>
<div id="dock"><div id="panel">
<div id="status"><span id="hintT"></span><b id="readout"></b></div>
<button id="arm" class="arm" aria-label="Arm the laser, cut a piece out of this flyer">
<svg class="ants" aria-hidden="true"><rect x="0" y="0" width="100%" height="100%"></rect></svg>
<span class="lz" aria-hidden="true"><i></i></span>
<span class="t"><b>ARM THE LASER</b><small>cut a piece out of this flyer</small></span>
<span class="go" aria-hidden="true">&rarr;</span>
</button>
<div id="armedRow" class="row row3"><button id="cutB" class="btn primary">CUT</button><button id="clearB" class="btn">CLEAR</button><button id="doneB" class="btn">DONE</button></div>
<div id="afterRow" class="row row2"><button id="shareB" class="btn primary">SHARE YOUR CUT &#8599;</button><button id="reloadB" class="btn">RELOAD FLYER</button></div>
<div id="shareMsg"></div>
</div></div>
"""

JS = r"""
(function () {
const $ = (id) => document.getElementById(id);
const stage = $('stage'), app = $('app'), ov = $('ov'), rig = $('rig'), piecesEl = $('pieces');
const SVGNS = 'http://www.w3.org/2000/svg';
const LIB = 'https://cdn.jsdelivr.net/npm/modern-screenshot@4.6.8/dist/index.js';
const LOGO = __LOGO__;

class Game {
  constructor() {
    this.state = { strokes: [], cur: null };
    this.parts = []; this.faceKey = '';
    this.W = 0; this.H = 0;
    this.mode = 'idle';        // idle | intro | tracing | draw | cutting
    this.introDone = false;
    this.segs = []; this.total = 0; this.el = 0; this.job = null;
    this.smoke = []; this.now = 0; this.raf = null;
    this.lastJob = null; this.jobPartsStart = 0;
    this.storyFile = null; this.storyURL = null; this.storyBusy = false; this.shareMsg = ''; this.linkMsg = '';
    this.cap = null;
    this.SITE = 'https://job.yardenamir.com';
  }
  setState(s) { Object.assign(this.state, s); draw(); }
__GEO__
__PLATE__
  // ---------- view ----------
  viewTop() { return -stage.getBoundingClientRect().top; }
  home() { return [(this.W || 390) - 32, this.viewTop() + 30]; }
  pt(e) { const r = ov.getBoundingClientRect(); return this.clampP([e.clientX - r.left, e.clientY - r.top]); }

  // ---------- arming ----------
  arm() {
    if (this.mode !== 'idle') return;
    document.documentElement.classList.add('locked');
    this.capture().catch(() => {});
    if (this.introDone) { this.mode = 'draw'; this.slideGantry(true); draw(); return; }
    this.mode = 'intro';
    $('scrim').style.display = 'block'; $('scrim').style.opacity = '1';
    const w = $('warn'); w.style.display = 'block'; w.style.opacity = '1'; w.style.transform = ''; w.style.pointerEvents = 'none';
    this.gK = 0;
    const a = w.animate([
      { transform: 'translate(calc(-50% - 110vw),-50%)' },
      { transform: 'translate(calc(-50% + 12px),-50%)', offset: 0.8 },
      { transform: 'translate(-50%,-50%)' }
    ], { duration: 560, easing: 'cubic-bezier(.2,.7,.3,1)' });
    a.onfinish = () => { w.style.pointerEvents = ''; };
    $('scrim').animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400 });
    w.focus({ preventScroll: true });
    draw();
  }
  disarm() {
    if (this.mode !== 'draw') return;
    this.state.strokes = this.state.strokes.filter((s) => s.cut);
    this.state.cur = null;
    this.mode = 'parking';
    this.slideGantry(false, () => { this.mode = 'idle'; document.documentElement.classList.remove('locked'); draw(); });
    draw();
  }
  slideGantry(inward, done) {
    // gK: 0 = machine hidden, 1 = in place. In: rails slide in from the sides, the gantry drops from the top
    // and bounces, then the head homes from left to right with its LED blinking. Out: the reverse, faster.
    const t0 = performance.now(), D = inward ? 1700 : 650, from = inward ? 0 : 1;
    if (this.gRaf) cancelAnimationFrame(this.gRaf);
    const step = () => {
      const k = Math.min(1, (performance.now() - t0) / D);
      this.gK = inward ? k : 1 - k;
      draw();
      if (k < 1) this.gRaf = requestAnimationFrame(step); else { this.gRaf = null; this.gK = inward ? 1 : 0; draw(); if (done) done(); }
    };
    this.gK = from;
    this.gRaf = requestAnimationFrame(step);
  }
  clearWarning() {
    if (this.mode !== 'intro') return;
    const w = $('warn'), sc = $('scrim');
    w.style.pointerEvents = 'none';
    this.introDone = true; this.mode = 'draw'; this.slideGantry(true); draw();
    const a = w.animate([
      { transform: 'translate(-50%,-50%)', opacity: 1 },
      { transform: 'translate(calc(-50% - 12px),-50%)', opacity: 1, offset: 0.15 },
      { transform: 'translate(calc(-50% + 110vw),-50%)', opacity: 1 }
    ], { duration: 650, easing: 'cubic-bezier(.55,0,.75,.3)', fill: 'forwards' });
    sc.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 500, fill: 'forwards' });
    a.onfinish = () => { w.style.display = 'none'; sc.style.display = 'none'; a.cancel(); };
  }

  // ---------- drawing ----------
  onDown(e) {
    if (this.mode !== 'draw') return;
    e.preventDefault();
    try { ov.setPointerCapture(e.pointerId); } catch (err) {}
    this.setState({ cur: [this.pt(e)] });
  }
  onMove(e) {
    const c = this.state.cur;
    if (!c) return;
    const p = this.pt(e), l = c[c.length - 1];
    if (Math.hypot(p[0] - l[0], p[1] - l[1]) < 3) return;
    this.setState({ cur: c.concat([p]) });
  }
  onUp() {
    const c = this.state.cur;
    if (!c) return;
    if (c.length < 2) { this.setState({ cur: null }); return; }
    const closed = c.length >= 6 && Math.hypot(c[0][0] - c[c.length - 1][0], c[0][1] - c[c.length - 1][1]) < 22;
    let raw = c.slice(), pinEnd = false;
    if (!closed) {
      const a = this.snapPoint(raw[0]), b = this.snapPoint(raw[raw.length - 1]);
      if (a) raw[0] = a;
      if (b) { raw[raw.length - 1] = b; pinEnd = true; }
    }
    const body = closed ? raw.slice(0, -1) : raw;
    const s = this.fitStroke(body.length >= 2 ? body : raw, closed, pinEnd);
    this.setState({ cur: null, strokes: this.state.strokes.concat([s]) });
  }
  onClear() {
    if (this.mode !== 'draw') return;
    this.setState({ cur: null, strokes: this.state.strokes.filter((s) => s.cut) });
  }

  // ---------- machine ----------
  onCut() {
    if (this.mode !== 'draw') return;
    const strokes = this.state.strokes;
    const job = strokes.map((s, si) => s.cut ? -1 : si).filter((si) => si >= 0);
    if (!job.length) return;
    // Inside-out: lines inside an enclosed area are cut before that area's edges.
    const faces = this.computeFaces(strokes.filter((s) => s.cut).map((s) => s.pts).concat(job.map((si) => strokes[si].pts)));
    const depth = {};
    job.forEach((si) => {
      const pts = strokes[si].pts, step = Math.max(1, Math.floor(pts.length / 24));
      depth[si] = faces.filter((fc) => {
        let n = 0, inside = 0;
        for (let k = 0; k < pts.length; k += step) { n++; if (!this.nearEdge(pts[k], fc.pts) && this.inPoly(pts[k], fc.pts)) inside++; }
        return inside > n / 2;
      }).length;
    });
    job.sort((x, y) => depth[y] - depth[x] || x - y);
    this.job = job;
    this.runJob(job.map((si) => strokes[si].pts), false);
  }
  lid(close, done) {
    const lid = $('lid'), f = lid.querySelector('.frame');
    lid.style.display = 'block';
    // hinged along the top edge of the screen: open, the lid stands up out of the screen toward you
    const shut = { transform: 'rotateX(0deg)', opacity: 1 }, open = { transform: 'rotateX(84deg)', opacity: 0 };
    const kf = close ? [open, { transform: 'rotateX(55deg)', opacity: 1, offset: 0.35 }, { transform: 'rotateX(-1.2deg)', opacity: 1, offset: 0.86 }, shut]
                     : [shut, { transform: 'rotateX(40deg)', opacity: 1, offset: 0.55 }, open];
    const a = f.animate(kf, { duration: close ? 700 : 650, easing: close ? 'cubic-bezier(.5,0,.85,.4)' : 'cubic-bezier(.3,.1,.4,1)', fill: 'forwards' });
    a.onfinish = () => { if (!close) { lid.style.display = 'none'; a.cancel(); } if (done) done(); };
  }
  runJob(paths, intro) {
    if (this.raf) cancelAnimationFrame(this.raf);
    const CUT = intro ? 520 : 300, TRAVEL = 1100, segs = [];
    const HOME = this.home();
    let pos = HOME;
    const add = (a, b, cut, pi, pj) => segs.push({ a, b, cut, pi, pj, dur: Math.max(0.001, Math.hypot(b[0] - a[0], b[1] - a[1]) / (cut ? CUT : TRAVEL)) });
    paths.forEach((p, pi) => {
      add(pos, p[0], false, pi, 0);
      for (let i = 1; i < p.length; i++) add(p[i - 1], p[i], true, pi, i);
      pos = p[p.length - 1];
    });
    add(pos, HOME, false, -1, 0);
    this.segs = segs; this.paths = paths;
    this.total = segs.reduce((t, s) => t + s.dur, 0);
    this.mode = intro ? 'tracing' : 'cutting';
    this.el = 0;
    const start = performance.now();
    let done = false;
    const tick = () => {
      const now = performance.now();
      if (done) {
        this.stepSmoke(now, null); draw();
        this.raf = this.smoke.length ? requestAnimationFrame(tick) : null;
        return;
      }
      this.el = Math.min(this.total, (now - start) / 1000);
      const h = this.headAt(this.el);
      this.stepSmoke(now, h.laserOn ? h.head : null);
      if (this.el >= this.total) { done = true; this.finishJob(intro); }
      else draw();
      this.raf = requestAnimationFrame(tick);
    };
    draw();
    this.raf = requestAnimationFrame(tick);
  }
  headAt(el) {
    let t = 0;
    for (const s of this.segs) {
      if (t + s.dur <= el) { t += s.dur; continue; }
      const f = (el - t) / s.dur;
      return { head: [s.a[0] + (s.b[0] - s.a[0]) * f, s.a[1] + (s.b[1] - s.a[1]) * f], laserOn: s.cut };
    }
    return { head: this.home(), laserOn: false };
  }
  stepSmoke(now, at) {
    this.now = now;
    if (at && this.smoke.length < 120) this.smoke.push({ x0: at[0], y0: at[1], born: now, life: 1100 + Math.random() * 500, w: Math.random() * 6.28 });
    this.smoke = this.smoke.filter((p) => now - p.born < p.life);
  }
  clusters(parts) {
    const box = parts.map((p) => { const xs = p.pts.map((q) => q[0]), ys = p.pts.map((q) => q[1]); return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]; });
    const up = parts.map((_, i) => i), find = (i) => (up[i] === i ? i : (up[i] = find(up[i])));
    const near = (a, b) => a[0] - 14 < b[2] && b[0] - 14 < a[2] && a[1] - 14 < b[3] && b[1] - 14 < a[3];
    for (let i = 0; i < parts.length; i++) for (let j = i + 1; j < parts.length; j++) if (near(box[i], box[j])) up[find(i)] = find(j);
    const groups = {};
    parts.forEach((_, i) => { const k = find(i); (groups[k] = groups[k] || []).push(i); });
    return Object.values(groups).map((idx) => {
      const b = [Math.min(...idx.map((i) => box[i][0])), Math.min(...idx.map((i) => box[i][1])), Math.max(...idx.map((i) => box[i][2])), Math.max(...idx.map((i) => box[i][3]))];
      return { idx, box: b, cx: (b[0] + b[2]) / 2, cy: (b[1] + b[3]) / 2 };
    });
  }
  pathLen(pts) { return pts.reduce((u, p, i) => i ? u + Math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1]) : 0, 0); }
  finishJob(intro) {
    const job = this.job;
    const strokes = this.state.strokes.map((s, si) => job.indexOf(si) >= 0 ? Object.assign({}, s, { cut: true }) : s);
    this.state.strokes = strokes;
    const start = this.parts.length;
    this.updateParts(strokes.map((s, si) => s.cut ? si : -1).filter((si) => si >= 0));
    const fresh = this.parts.slice(start);
    this.lastJob = { paths: job.length, pieces: fresh.length, start, mm: Math.round(job.reduce((t, si) => t + this.pathLen(strokes[si].pts), 0) * 0.2646) };
    applyHoles();
    this.mode = 'opening'; draw();
    this.storyFile = null; this.shareMsg = '';
    // pieces of one shape (the wedges of a tile, the grains of an ear) lift together, as one
    this.clusters(fresh).forEach((c) => {
      const side = c.cx < this.W / 2 ? 1 : -1;
      const dx = side * (16 + Math.random() * 8), dy = -(7 + Math.random() * 5), rot = side * (2 + Math.random() * 2.5);
      c.idx.forEach((i) => { fresh[i].lift = { dx, dy, rot, ox: c.cx, oy: c.cy }; });
    });
    const els = fresh.map((p) => this.makePiece(p));  // in place right away, so the hole is never empty
    setTimeout(() => {
      this.mode = 'draw';
      fresh.forEach((p, i) => this.liftPiece(p, i, els[i]));
      this.prepareStory();
      draw();
    }, 320);
  }
  makePiece(part) {
    const n = part.pts.length - 1;
    const cx = part.pts.slice(0, n).reduce((t, p) => t + p[0], 0) / n, cy = part.pts.slice(0, n).reduce((t, p) => t + p[1], 0) / n;
    const outer = document.createElement('div');
    outer.className = 'piece';
    outer.style.width = this.W + 'px'; outer.style.height = this.H + 'px';
    outer.style.transformOrigin = cx.toFixed(1) + 'px ' + cy.toFixed(1) + 'px';
    outer.style.filter = 'none';
    const inner = document.createElement('div');
    inner.style.cssText = 'position:absolute;inset:0;clip-path:path(\'' + polyD(part.pts) + '\')';
    const clone = app.cloneNode(true);
    clone.removeAttribute('id'); clone.style.clipPath = 'none'; clone.setAttribute('aria-hidden', 'true');
    clone.querySelectorAll('[id]').forEach((el) => { if (!el.closest('svg')) el.removeAttribute('id'); });
    inner.appendChild(clone);
    const edge = document.createElementNS(SVGNS, 'svg');
    edge.setAttribute('width', this.W); edge.setAttribute('height', this.H);
    edge.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    const cuts = this.state.strokes.filter((s) => s.cut).map((s) => lineD(s.pts)).join('');
    edge.innerHTML = '<path d="' + cuts + '" fill="none" stroke="rgba(92,52,20,.38)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
      + '<path d="' + polyD(part.pts) + '" fill="none" stroke="rgba(92,52,20,.55)" stroke-width="5" stroke-linejoin="round"/>'
      + '<path d="' + cuts + '" fill="none" stroke="#262422" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>';
    inner.appendChild(edge);
    outer.appendChild(inner);
    piecesEl.appendChild(outer);
    return outer;
  }
  liftPiece(part, i, outer) {
    const { dx, dy, rot, ox, oy } = part.lift;
    outer.style.transformOrigin = ox.toFixed(1) + 'px ' + oy.toFixed(1) + 'px';
    outer.style.filter = '';
    outer.animate([
      { transform: 'none', filter: 'drop-shadow(0 0 0 rgba(38,36,34,0))' },
      { transform: 'translate(' + (dx * 0.25).toFixed(1) + 'px,' + (dy * 1.4).toFixed(1) + 'px) scale(1.03)', offset: 0.4 },
      { transform: 'translate(' + dx.toFixed(1) + 'px,' + dy.toFixed(1) + 'px) rotate(' + rot.toFixed(1) + 'deg) scale(1.01)' }
    ], { duration: 750, easing: 'cubic-bezier(.25,.8,.35,1)', fill: 'forwards' });
  }
  reload() {
    if (this.mode !== 'draw' && this.mode !== 'idle') return;
    this.parts = []; this.faceKey = ''; this.lastJob = null;
    this.state.strokes = []; this.state.cur = null;
    this.storyFile = null; this.shareMsg = '';
    piecesEl.innerHTML = '';
    app.animate([{ opacity: 0.35 }, { opacity: 1 }], { duration: 450, easing: 'ease-out' });
    applyHoles(); draw();
  }

  // ---------- story image ----------
  loadLib() {
    if (window.modernScreenshot) return Promise.resolve();
    if (!this.libP) this.libP = new Promise((res, rej) => { const sc = document.createElement('script'); sc.src = LIB; sc.onload = res; sc.onerror = rej; document.head.appendChild(sc); });
    return this.libP;
  }
  capture() {
    if (!this.cap) {
      this.cap = (async () => {
        await this.loadLib();
        try { await document.fonts.ready; } catch (e) {}
        const sc = Math.max(1, Math.min(2, Math.sqrt(14e6 / (this.W * this.H))));
        const cv = await window.modernScreenshot.domToCanvas(app, { scale: sc, backgroundColor: '#F1E9DC', style: { clipPath: 'none' }, width: this.W, height: this.H });
        return { cv, sc };
      })();
      this.cap.catch(() => { this.cap = null; });
    }
    return this.cap;
  }
  async prepareStory() {
    if (this.storyBusy) { this.storyAgain = true; return; }
    const cuts = this.state.strokes.filter((s) => s.cut);
    if (!cuts.length) return;
    this.storyBusy = true; draw();
    try {
      let cap = null;
      try { cap = await this.capture(); } catch (e) { cap = null; }
      const plateImg = await this.svgImage(this.plateSVG(13));
      try { await Promise.all(['500 70px "EB Garamond"', '500 46px "EB Garamond"', '500 26px "IBM Plex Mono"', '400 30px "IBM Plex Mono"'].map((f) => document.fonts.load(f))); } catch (e) {}
      const CW = 1080, CH = 1920;
      const cv = document.createElement('canvas'); cv.width = CW; cv.height = CH;
      const ctx = cv.getContext('2d');
      const serif = '"EB Garamond", Garamond, serif', mono = '"IBM Plex Mono", monospace';
      const parts = this.parts;
      // everything that was cut or lifted, in page coordinates
      // focus on the latest cut: its lines and the pieces it freed
      const jobPts = (this.job || []).map((si) => this.state.strokes[si]).filter(Boolean).map((s) => s.pts);
      const freshIdx = parts.map((p, i) => i).filter((i) => i >= (this.lastJob ? this.lastJob.start : 0));
      // each piece is set down beside its hole, overlapping it a little, toward the side with more room
      const place = [];
      this.clusters(parts).forEach((c) => {
        const minX = c.box[0], maxX = c.box[2], w = maxX - minX;
        const toRight = (this.W - maxX) >= minX;
        // up to ~60% of its width to the side, never past the edge of the flyer (big pieces overlap their hole more)
        const room = toRight ? this.W - 6 - maxX : minX - 6;
        const dx = (toRight ? 1 : -1) * Math.min(w * 0.62, Math.max(room, w * 0.22));
        c.idx.forEach((i) => { place[i] = { dx, dy: -8, rot: toRight ? 4 : -4, ox: c.cx, oy: c.cy }; });
      });
      const all = [].concat(...(jobPts.length ? jobPts : cuts.map((s) => s.pts)));
      freshIdx.forEach((i) => parts[i].pts.forEach((q) => all.push([q[0] + place[i].dx, q[1] + place[i].dy])));
      const bx0 = Math.min(...all.map((p) => p[0])), by0 = Math.min(...all.map((p) => p[1]));
      const bx1 = Math.max(...all.map((p) => p[0])), by1 = Math.max(...all.map((p) => p[1]));
      const cw = bx1 - bx0, ch = by1 - by0;
      // The flyer is shown as what it is: a webpage in a browser window, with the cut in view.
      const BG = '#F1E9DC', WX = 96, WW = 888, WY = 600, TB = 80, CY0 = WY + TB, WB = 1470;
      const k = WW / this.W;                       // the whole page width, like a phone browser
      const visH = (WB - CY0) / k;
      const y0 = Math.max(0, Math.min(this.H - visH, (by0 + by1) / 2 - visH * 0.5));
      ctx.fillStyle = BG; ctx.fillRect(0, 0, CW, CH);
      const rr = (x, y, w, h, r) => { const p = new Path2D(); p.moveTo(x + r, y); p.lineTo(x + w - r, y); p.quadraticCurveTo(x + w, y, x + w, y + r); p.lineTo(x + w, y + h); p.lineTo(x, y + h); p.lineTo(x, y + r); p.quadraticCurveTo(x, y, x + r, y); p.closePath(); return p; };
      const win = rr(WX, WY, WW, WB - WY + 60, 30);
      ctx.save(); ctx.shadowColor = 'rgba(38,36,34,0.25)'; ctx.shadowBlur = 50; ctx.shadowOffsetY = 18; ctx.fillStyle = BG; ctx.fill(win); ctx.restore();
      // page content inside the window
      const toPage = () => { ctx.translate(WX, CY0); ctx.scale(k, k); ctx.translate(0, -y0); };
      ctx.save();
      ctx.beginPath(); ctx.rect(WX, CY0, WW, WB - CY0 + 60); ctx.clip();
      ctx.save(); toPage();
      if (cap) ctx.drawImage(cap.cv, 0, 0, cap.cv.width, cap.cv.height, 0, 0, this.W, this.H);
      const strokesPath = new Path2D(cuts.map((s) => 'M' + s.pts.map((p) => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('L')).join(''));
      const hex = (x, y, w, h, R) => {
        ctx.beginPath();
        const HW = Math.sqrt(3) * R;
        const c0 = Math.floor(x / HW) - 1, r0 = Math.floor(y / (1.5 * R)) - 1;
        for (let row = r0; row * 1.5 * R < y + h + R; row++) for (let col = c0; col * HW < x + w + HW; col++) {
          const hx = col * HW + (Math.abs(row) % 2 ? HW / 2 : 0), hy = row * 1.5 * R;
          for (let q = 0; q < 6; q++) { const a = Math.PI / 6 + q * Math.PI / 3; ctx[q ? 'lineTo' : 'moveTo'](hx + R * Math.cos(a), hy + R * Math.sin(a)); }
          ctx.closePath();
        }
        ctx.stroke();
      };
      if (parts.length) {
        ctx.save(); ctx.clip(new Path2D(parts.map((p) => polyD(p.pts)).join('')), 'evenodd');
        ctx.fillStyle = '#1E1D1B'; ctx.fillRect(0, y0, this.W, visH + 40);
        ctx.strokeStyle = '#3A3733'; ctx.lineWidth = 1.1; hex(0, y0, this.W, visH + 40, 7);
        ctx.restore();
      }
      const kerf = () => {
        ctx.lineCap = 'round'; ctx.lineJoin = 'round';
        ctx.strokeStyle = 'rgba(92,52,20,0.36)'; ctx.lineWidth = 5; ctx.stroke(strokesPath);
        ctx.strokeStyle = '#262422'; ctx.lineWidth = 1.6; ctx.stroke(strokesPath);
      };
      ctx.save();
      ctx.clip(new Path2D('M-50 ' + (y0 - 50) + 'h' + (this.W + 100) + 'v' + (visH + 150) + 'h' + (-(this.W + 100)) + 'Z' + parts.map((p) => polyD(p.pts)).join('')), 'evenodd');
      kerf();
      ctx.restore();
      ctx.restore();
      ctx.restore();
      // browser toolbar with the address
      ctx.save(); ctx.clip(win);
      ctx.fillStyle = '#E6DFD1'; ctx.fillRect(WX, WY, WW, TB);
      ctx.fillStyle = 'rgba(38,36,34,0.18)'; ctx.fillRect(WX, CY0 - 2, WW, 2);
      const pill = rr(WX + 26, WY + 17, WW - 52, 46, 23);
      ctx.fillStyle = '#FFFFFF'; ctx.fill(pill);
      // padlock
      ctx.strokeStyle = '#5F5A52'; ctx.fillStyle = '#5F5A52'; ctx.lineWidth = 2.6;
      ctx.beginPath(); ctx.arc(WX + 62, WY + 36, 6.5, Math.PI, 0); ctx.stroke();
      ctx.fillRect(WX + 53, WY + 36, 18, 13);
      ctx.font = '400 25px ' + mono; ctx.fillStyle = '#262422'; ctx.textBaseline = 'middle';
      ctx.fillText('job.yardenamir.com', WX + 86, WY + 41); ctx.textBaseline = 'alphabetic';
      ctx.restore();
      ctx.strokeStyle = 'rgba(38,36,34,0.55)'; ctx.lineWidth = 2; ctx.stroke(win);
      // the pieces, lifted out of the page; they may rise over the window's edge
      ctx.save(); toPage();
      parts.forEach((part, pi) => {
        const L = place[pi];
        const n = part.pts.length - 1;
        const cx = part.pts.slice(0, n).reduce((t, p) => t + p[0], 0) / n, cy = part.pts.slice(0, n).reduce((t, p) => t + p[1], 0) / n;
        if (cy + 80 < y0 || cy - 80 > y0 + visH) return;
        const path = new Path2D(polyD(part.pts));
        ctx.save();
        ctx.translate(L.ox + L.dx, L.oy + L.dy); ctx.rotate(L.rot * Math.PI / 180); ctx.translate(-L.ox, -L.oy);
        ctx.save();
        ctx.shadowColor = 'rgba(38,36,34,0.42)'; ctx.shadowBlur = 22; ctx.shadowOffsetY = 12;
        ctx.fillStyle = cap ? '#F1E9DC' : '#C79A5B'; ctx.fill(path);
        ctx.restore();
        ctx.save(); ctx.clip(path);
        if (cap) {
          const xs = part.pts.map((p) => p[0]), ys = part.pts.map((p) => p[1]);
          const px = Math.min(...xs) - 2, py = Math.min(...ys) - 2, pw = Math.max(...xs) - px + 4, ph = Math.max(...ys) - py + 4;
          ctx.drawImage(cap.cv, px * cap.sc, py * cap.sc, pw * cap.sc, ph * cap.sc, px, py, pw, ph);
        }
        kerf();
        ctx.restore();
        ctx.strokeStyle = 'rgba(92,52,20,0.5)'; ctx.lineWidth = 3.5; ctx.stroke(path);
        ctx.strokeStyle = '#262422'; ctx.lineWidth = 1.4; ctx.stroke(path);
        ctx.restore();
      });
      ctx.restore();
      // the window runs on below and fades into the page
      const gr = ctx.createLinearGradient(0, 1240, 0, 1480);
      for (let q = 0; q <= 8; q++) { const t = q / 8, e = t * t * (3 - 2 * t); gr.addColorStop(t, 'rgba(241,233,220,' + e.toFixed(3) + ')'); }
      ctx.fillStyle = gr; ctx.fillRect(0, 1240, CW, 240);
      ctx.fillStyle = BG; ctx.fillRect(0, 1480, CW, CH - 1480);
      // text
      ctx.fillStyle = '#7A5A30'; ctx.font = '500 26px ' + mono;
      if ('letterSpacing' in ctx) ctx.letterSpacing = '2px';
      ctx.fillText('I LASER-CUT HIS WEBSITE', 110, 278);
      if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
      ctx.fillStyle = '#262422'; ctx.font = '500 70px ' + serif;
      ['Yarden Amir is on a job hunt.', 'I cut this with a laser', 'on his resume.'].forEach((l, i) => ctx.fillText(l, 110, 370 + i * 76));
      ctx.fillStyle = '#262422'; ctx.fillRect(110, 1500, 860, 2);
      ctx.font = '500 46px ' + serif; ctx.fillText('Your turn →', 110, 1562);
      ctx.fillStyle = '#7A5A30'; ctx.font = '400 30px ' + mono; ctx.textAlign = 'right';
      ctx.fillText('job.yardenamir.com', 970, 1558); ctx.textAlign = 'left';
      ctx.drawImage(plateImg, 110, 1600, 91, 91);
      ctx.fillStyle = '#262422'; ctx.font = '500 44px ' + serif; ctx.fillText('Yarden Amir', 223, 1640);
      ctx.fillStyle = '#5F5A52'; ctx.font = '400 19px ' + mono; ctx.fillText('Designer · Making & Fabrication Instructor · Craft Researcher', 223, 1678);
      const blob = await new Promise((r) => cv.toBlob(r, 'image/png'));
      this.storyFile = new File([blob], 'yarden-amir-laser-cut.png', { type: 'image/png' });
      if (this.storyURL) URL.revokeObjectURL(this.storyURL);
      this.storyURL = URL.createObjectURL(blob);
      this.shareMsg = '';
    } catch (e) {
      this.shareMsg = 'Could not build the image; the link will still be copied';
    } finally {
      this.storyBusy = false; draw();
      if (this.storyAgain) { this.storyAgain = false; this.prepareStory(); }
    }
  }
  copyLink() { try { if (navigator.clipboard) navigator.clipboard.writeText(this.SITE).catch(() => {}); } catch (e) {} }
  isTouch() { return (window.matchMedia && matchMedia('(pointer: coarse)').matches) || navigator.maxTouchPoints > 0; }
  onShare() {
    this.copyLink();
    const f = this.storyFile;
    const text = 'Yarden Amir is on a job hunt. I cut this with a laser on his resume. ' + this.SITE;
    if (f && this.isTouch() && navigator.canShare && navigator.canShare({ files: [f] })) {
      navigator.share({ files: [f], text }).then(() => { this.shareMsg = 'Shared · the link is copied: add it with a Link sticker'; draw(); }).catch(() => {});
      this.shareMsg = 'Link copied: job.yardenamir.com · add it with a Link sticker';
    } else if (f) {
      const a = document.createElement('a'); a.href = this.storyURL; a.download = f.name; document.body.appendChild(a); a.click(); a.remove();
      this.shareMsg = 'Image saved and link copied · post it to your story with a Link sticker';
    } else this.shareMsg = 'Link copied: job.yardenamir.com';
    draw();
  }
  onShareLink() {
    this.copyLink();
    if (this.isTouch() && navigator.share) { navigator.share({ title: 'Yarden Amir is on a job hunt', text: 'Cut something with a laser on his resume.', url: this.SITE }).catch(() => {}); this.linkMsg = ''; }
    else this.linkMsg = 'Link copied: job.yardenamir.com';
    draw();
  }
}

const g = new Game();
window.__flyer = g;
function polyD(pts) { return 'M' + pts.map((p) => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('L') + 'Z'; }
function lineD(pts) { return 'M' + pts.map((p) => p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join('L'); }

function measure() {
  const W = app.offsetWidth, H = app.offsetHeight;
  const changedW = g.W && Math.abs(W - g.W) > 1;
  const ls = document.getElementById('logoSlot');
  if (ls) { const a = ls.getBoundingClientRect(), b = stage.getBoundingClientRect(); g.slot = [a.left - b.left + a.width / 2, a.top - b.top + a.height / 2]; }
  g.W = W; g.H = H;
  [ov, rig].forEach((s) => { s.setAttribute('width', W); s.setAttribute('height', H); s.setAttribute('viewBox', '0 0 ' + W + ' ' + H); });
  if (changedW && g.parts.length) { g.cap = null; g.reload(); }
  else if (changedW) g.cap = null;
  applyHoles(); draw();
}
function applyHoles() {
  if (!g.parts.length) { app.style.clipPath = ''; return; }
  app.style.clipPath = "path(evenodd, 'M0 0H" + g.W + 'V' + g.H + 'H0Z' + g.parts.map((p) => polyD(p.pts)).join('') + "')";
}

let drawing = false;
function draw() {
  if (drawing) return; drawing = true;
  try {
    const st = g.state, mode = g.mode, accent = '#B4593A';
    const cutting = mode === 'cutting' || mode === 'tracing' || mode === 'closing' || mode === 'opening';
    // ---- strokes and kerf (under the pieces)
    let o = '<defs><mask id="hm" maskUnits="userSpaceOnUse" x="0" y="0" width="' + g.W + '" height="' + g.H + '"><rect width="' + g.W + '" height="' + g.H + '" fill="#fff"/>' + g.parts.map((p) => '<path d="' + polyD(p.pts) + '" fill="#000"/>').join('') + '</mask></defs>';
    const reached = {}; let partial = null, partialPi = -1, head = g.home(), laserOn = false;  // head is reassigned while homing
    if (mode === 'cutting') {
      let t = 0;
      for (const s of g.segs) {
        if (t + s.dur <= g.el) { if (s.cut) reached[s.pi] = s.pj; t += s.dur; head = s.b; continue; }
        const f = (g.el - t) / s.dur;
        head = [s.a[0] + (s.b[0] - s.a[0]) * f, s.a[1] + (s.b[1] - s.a[1]) * f];
        laserOn = s.cut; if (s.cut) { partial = head; partialPi = s.pi; }
        break;
      }
    }
    const kerfPaths = st.strokes.filter((s) => s.cut).map((s) => s.pts);
    if (mode === 'cutting') (g.paths || []).forEach((p, pi) => {
      let pts = reached[pi] > 0 ? p.slice(0, reached[pi] + 1) : (pi === partialPi ? [p[0]] : []);
      if (pi === partialPi) pts = pts.concat([partial]);
      if (pts.length > 1) kerfPaths.push(pts);
    });
    o += '<g mask="url(#hm)">' + kerfPaths.map((p) => '<path d="' + lineD(p) + '" fill="none" stroke="rgba(92,52,20,.38)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/><path d="' + lineD(p) + '" fill="none" stroke="#262422" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>').join('') + '</g>';
    const uncut = st.strokes.filter((s) => !s.cut);
    o += uncut.map((s, i) => (cutting && g.job && g.job.indexOf(st.strokes.indexOf(s)) >= 0 && false) ? '' : '<path d="' + lineD(s.pts) + '" fill="none" stroke="' + accent + '" stroke-width="1.6" stroke-dasharray="5 4" stroke-linecap="round" stroke-linejoin="round"/>').join('');
    uncut.forEach((s) => s.nodes.forEach((n) => { o += '<rect x="' + (n[0] - 3).toFixed(1) + '" y="' + (n[1] - 3).toFixed(1) + '" width="6" height="6" fill="#C79A5B" stroke="#262422" stroke-width="1"/>'; }));
    const cur = st.cur;
    if (cur && cur.length > 1) o += '<path d="' + lineD(cur) + '" fill="none" stroke="#262422" stroke-width="1.4" stroke-dasharray="2 3" stroke-linecap="round" opacity=".7"/>';
    if (cur && cur.length > 3) {
      const l = cur[cur.length - 1], near = cur.length >= 6 && Math.hypot(cur[0][0] - l[0], cur[0][1] - l[1]) < 22;
      o += '<circle cx="' + cur[0][0].toFixed(1) + '" cy="' + cur[0][1].toFixed(1) + '" r="11" fill="none" stroke="' + accent + '" stroke-width="1.6" ' + (near ? '' : 'stroke-dasharray="3 3" opacity=".6"') + '/>';
    }
    ov.innerHTML = o;
    // ---- gantry, head and smoke (above everything but the dock)
    let r = '';
    if (mode !== 'idle' && mode !== 'intro') {
      const gk = g.gK == null ? 1 : g.gK, clamp = (v) => Math.max(0, Math.min(1, v)), nowT = performance.now();
      const bounce = (t) => { const n = 7.5625, d = 2.75; if (t < 1 / d) return n * t * t; if (t < 2 / d) return n * (t -= 1.5 / d) * t + 0.75; if (t < 2.5 / d) return n * (t -= 2.25 / d) * t + 0.9375; return n * (t -= 2.625 / d) * t + 0.984375; };
      const railP = 1 - Math.pow(1 - clamp(gk / 0.28), 3);
      const dropP = bounce(clamp((gk - 0.2) / 0.42));
      const homeT = clamp((gk - 0.64) / 0.36), homeP = homeT * homeT * (3 - 2 * homeT);
      const vt = g.viewTop(), vh = innerHeight;
      const y = vt - 44 + dropP * (head[1] - vt + 44);
      if (gk < 1 && !cutting) head = [26 + homeP * (head[0] - 26), head[1]];
      // Y rails along both edges of the screen
      const ro = (1 - railP) * 18;
      r += '<defs><linearGradient id="rl" x1="0" x2="1"><stop offset="0" stop-color="#1F1E1C"/><stop offset=".55" stop-color="#4A4743"/><stop offset="1" stop-color="#2A2926"/></linearGradient></defs>';
      [[-ro, 1], [g.W - 10 + ro, -1]].forEach(([rx, dir]) => {
        r += '<rect x="' + (rx + (dir > 0 ? 10 : -12)).toFixed(1) + '" y="' + vt.toFixed(1) + '" width="12" height="' + vh + '" fill="#000" opacity=".16" filter="url(#hs)"/>';
        r += '<rect x="' + rx.toFixed(1) + '" y="' + vt.toFixed(1) + '" width="10" height="' + vh + '" fill="url(#rl)"/>';
        r += '<rect x="' + (rx + (dir > 0 ? 7 : 1)).toFixed(1) + '" y="' + vt.toFixed(1) + '" width="1.5" height="' + vh + '" fill="#6A6660" opacity=".7"/>';
      });
      r += '<defs><linearGradient id="gs" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".42"/><stop offset=".45" stop-color="#000" stop-opacity=".16"/><stop offset="1" stop-color="#000" stop-opacity="0"/></linearGradient>'
        + '<filter id="hs" x="-60%" y="-60%" width="220%" height="260%"><feGaussianBlur stdDeviation="4"/></filter></defs>';
      r += '<rect x="0" y="' + (y + 5).toFixed(1) + '" width="' + g.W + '" height="26" fill="url(#gs)"/>';
      r += '<rect x="' + (head[0] - 18).toFixed(1) + '" y="' + (y - 16).toFixed(1) + '" width="37" height="37" rx="4" fill="#000" opacity=".34" filter="url(#hs)" transform="translate(4,9)"/>';
      r += '<rect x="0" y="' + (y - 8).toFixed(1) + '" width="' + g.W + '" height="16" fill="#3E3D39" opacity=".97"/><rect x="0" y="' + (y - 8).toFixed(1) + '" width="' + g.W + '" height="2.5" fill="#5F5C57"/>';
      // carriages where the gantry rides on the rails
      r += '<rect x="' + (-ro - 2).toFixed(1) + '" y="' + (y - 13).toFixed(1) + '" width="18" height="26" rx="2" fill="#2E2D2A"/><rect x="' + (g.W - 16 + ro).toFixed(1) + '" y="' + (y - 13).toFixed(1) + '" width="18" height="26" rx="2" fill="#2E2D2A"/>';
      // the head carries the test-plate mark (20% smaller than the header logo); the middle circle is the laser
      const fire = laserOn ? 0.85 + Math.random() * 0.15 : 0, moving = cutting && !laserOn ? 0.22 : (gk < 1 && homeT > 0 && homeT < 1 ? (Math.floor(nowT / 110) % 2 ? 0.9 : 0.15) : 0);
      const L = 27, S = L / 42, c = -L / 2 + 21 * S, rr = 6 * S;
      const glow = Math.max(fire, moving);
      r += '<defs><filter id="led" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="3"/></filter></defs>';
      r += '<g transform="translate(' + head[0].toFixed(1) + ',' + y.toFixed(1) + ')">'
        + '<rect x="-18.5" y="-18.5" width="37" height="37" rx="3.5" fill="#E4DDCE" stroke="#262422" stroke-width=".8"/>'
        + '<rect x="-16.5" y="-16.5" width="33" height="2.5" rx="1.2" fill="#fff" opacity=".45"/>'
        + '<svg x="' + (-L / 2) + '" y="' + (-L / 2) + '" width="' + L + '" height="' + L + '" viewBox="0 0 42 42" style="color:#262422" overflow="visible">' + LOGO + '</svg>'
        + (glow ? '<circle cx="' + c.toFixed(2) + '" cy="' + c.toFixed(2) + '" r="' + (rr * 1.5).toFixed(2) + '" fill="#FF3B2A" opacity="' + (glow * 0.85).toFixed(2) + '" filter="url(#led)"/>'
          + '<circle cx="' + c.toFixed(2) + '" cy="' + c.toFixed(2) + '" r="' + rr.toFixed(2) + '" fill="#FF4A30" opacity="' + glow.toFixed(2) + '"/>'
          + (fire ? '<circle cx="' + c.toFixed(2) + '" cy="' + c.toFixed(2) + '" r="' + (rr * 0.42).toFixed(2) + '" fill="#FFE0CC" opacity="' + (fire * 0.85).toFixed(2) + '"/>' : '') : '')
        + '</g>';
      const now = g.now;
      g.smoke.forEach((p) => {
        const k = Math.min(1, (now - p.born) / p.life);
        const x = p.x0 + Math.sin(k * 7 + p.w) * 9 * k, yy = p.y0 - 70 * k;
        const op = 0.4 * (1 - k) * Math.min(1, k * 8);
        r += '<circle cx="' + x.toFixed(1) + '" cy="' + yy.toFixed(1) + '" r="' + (3 + 10 * k).toFixed(1) + '" fill="rgba(214,208,196,' + op.toFixed(3) + ')"/>';
      });
    }
    rig.innerHTML = r;
    // ---- dock
    const n = uncut.length;
    let hint = '';
    if (mode === 'intro') hint = 'tap the warning to begin';
    else if (mode === 'tracing') hint = 'clearing the warning…';
    else if (mode === 'closing') hint = 'closing the lid…';
    else if (mode === 'opening') hint = 'cut done…';
    else if (mode === 'cutting') hint = 'cutting… ' + Math.round(g.el / g.total * 100) + '%';
    else if (mode === 'draw' && g.gK != null && g.gK < 1) hint = 'homing the laser…';
    else if (mode === 'draw') {
      if (n) hint = n + (n === 1 ? ' path' : ' paths') + ' ready · add more, or press Cut';
      else if (g.lastJob && g.lastJob.pieces) hint = g.lastJob.pieces + (g.lastJob.pieces === 1 ? ' piece' : ' pieces') + ' cut free · ' + g.lastJob.mm + ' mm of kerf';
      else if (g.lastJob) hint = g.lastJob.mm + ' mm of kerf · close a shape to cut out a piece';
      else hint = 'draw on the flyer · close a shape · press Cut';
    }
    $('hintT').textContent = hint;
    $('readout').textContent = mode === 'idle' ? '' : (laserOn ? 'LASER ON' : (cutting ? 'MOVING' : 'ARMED'));
    $('readout').style.color = laserOn ? '#E08A6A' : '#C79A5B';
    $('status').style.display = mode === 'idle' ? 'none' : 'flex';
    const armB = $('arm');
    armB.style.display = mode === 'idle' ? 'flex' : 'none';
    armB.classList.toggle('compact', g.state.strokes.some((s) => s.cut));
    armB.querySelector('.t small').textContent = 'cut a piece out of this flyer';
    $('armedRow').style.display = (mode === 'draw' || cutting || mode === 'parking') ? 'grid' : 'none';
    $('cutB').disabled = mode !== 'draw' || !n;
    $('clearB').disabled = mode !== 'draw' || !n;
    $('doneB').disabled = mode !== 'draw';
    const showAfter = g.state.strokes.some((s) => s.cut) && mode !== 'intro';
    $('afterRow').style.display = showAfter ? 'grid' : 'none';
    $('shareB').disabled = cutting;
    $('reloadB').disabled = cutting;
    const sm = showAfter ? (g.storyBusy ? 'Preparing your image…' : (g.shareMsg || 'Shares a picture of your piece · the link is copied for a Link sticker')) : '';
    $('shareMsg').textContent = sm; $('shareMsg').style.display = sm ? 'block' : 'none';
    $('linkMsg').textContent = g.linkMsg || '';
  } finally { drawing = false; }
}

ov.addEventListener('pointerdown', (e) => g.onDown(e));
ov.addEventListener('pointermove', (e) => g.onMove(e));
ov.addEventListener('pointerup', () => g.onUp());
ov.addEventListener('pointercancel', () => g.onUp());
ov.addEventListener('touchmove', (e) => { if (g.mode !== 'idle') e.preventDefault(); }, { passive: false });
$('arm').addEventListener('click', () => g.arm());
$('warn').addEventListener('click', () => g.clearWarning());
$('warn').addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); g.clearWarning(); } });
$('cutB').addEventListener('click', () => g.onCut());
$('clearB').addEventListener('click', () => g.onClear());
$('doneB').addEventListener('click', () => g.disarm());
$('shareB').addEventListener('click', () => g.onShare());
$('reloadB').addEventListener('click', () => g.reload());
$('shareLinkBtn').addEventListener('click', () => g.onShareLink());
window.addEventListener('resize', measure);
if (window.ResizeObserver) new ResizeObserver(() => measure()).observe(app);
measure();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
})();
"""
MOBILE_PDF = '<script>\n/* Phones get the phone-format PDFs; desktops and tablets keep the originals. */\n(function () { try { if (matchMedia("(max-width: 820px) and (pointer: coarse)").matches) document.querySelectorAll("a[href*=\\"studioya.github.io/pdf/\\"]").forEach(function (a) { a.href = a.href.replace(/\\.pdf$/, "-mobile.pdf"); }); } catch (e) {} })();\n</script>'
JS = JS.replace('__LOGO__', _json.dumps(LOGO_INNER)).replace('__GEO__', geo).replace('__PLATE__', plate_js)

page = (head_html
        + '<div id="stage">\n<div id="bedBg" aria-hidden="true"></div>\n<div id="app">' + content + '\n</div>\n</div>\n'
        + '<svg id="ov" aria-hidden="true"></svg>\n<div id="pieces" aria-hidden="true"></div>\n<svg id="rig" aria-hidden="true"></svg>\n</div>\n'
        + DOCK + '<script>' + JS + '</script>\n' + MOBILE_PDF + '\n</body>\n</html>\n')
# ov/pieces/rig must live inside #stage: fix the order above
page = page.replace('\n</div>\n</div>\n<svg id="ov"', '\n</div>\n<svg id="ov"', 1)
import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'w').write(page)
print('wrote', OUT, len(page))
