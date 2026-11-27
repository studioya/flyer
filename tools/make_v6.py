#!/usr/bin/env python3
"""Derive build_v6.py (shape picker instead of free drawing) from build_v5.py."""
D = '/tmp/claude-0/-home-user/de665114-9855-5d3e-a296-c68bfd085cac/scratchpad/v5/'
s = open(D + 'build_v5.py').read()

def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:100])
    s = s.replace(old, new)

rep("OUT = '/home/user/flyer/v5/index.html'", "OUT = '/home/user/flyer/v6/index.html'")
rep('<meta property="og:url" content="https://job.yardenamir.com/v5/">', '<meta property="og:url" content="https://job.yardenamir.com/v6/">')

# ---- brief
rep('aria-label="Laser cutters are not a game. Tap the sheet to play. Draw on the flyer, close a shape and press Cut; that piece of the flyer lifts out."',
    'aria-label="Laser cutters are not a game. Tap the sheet to play. Pick a shape, place it on the flyer and press Cut; that piece of the flyer lifts out."')
rep('<div class="w3">Draw on the flyer with your finger. Close a shape, press Cut, and that piece of the flyer lifts out.</div>',
    '<div class="w3">Pick a shape, tap the flyer to place it, drag it where you like. Press Cut, and that piece of the flyer lifts out.</div>')

# ---- tray of shapes in the dock
import json as _j
TRAY_ICONS = _j.load(open(D + '../motif/icons.json'))
TRAY_NAMES = {'rosette': 'Mashrabiya rosette', 'carvedStar': 'Carved Gothic star', 'tracery': 'Lancet tracery', 'wheat': 'Ear of wheat', 'radialTile': 'Radial test tile', 'quatrefoil': 'Quatrefoil', 'mark': 'Test-plate mark'}
tray = '<div id="tray" role="radiogroup" aria-label="Shapes">' + ''.join(
    f'<button class="shp" data-shape="{k}" role="radio" aria-label="{TRAY_NAMES[k]}" title="{TRAY_NAMES[k]}"><svg viewBox="0 0 24 24" width="24" height="24">{v}</svg></button>'
    for k, v in TRAY_ICONS.items()) + '</div>\n'
rep('<div id="armedRow" class="row row3">', tray + '<div id="armedRow" class="row row3">')
rep(".row{{display:grid;gap:8px}}",
    ".row{{display:grid;gap:8px}}\n"
    "#tray{{display:none;grid-template-columns:repeat(7,1fr);gap:6px}}\n"
    ".shp{{height:42px;border:1px solid rgba(241,233,220,.35);background:transparent;color:#F1E9DC;display:grid;place-items:center;cursor:pointer;padding:0;border-radius:0;-webkit-tap-highlight-color:transparent}}\n"
    ".shp svg{{fill:none;stroke:currentColor;stroke-width:1.3;stroke-linejoin:round;stroke-linecap:round}}\n"
    ".shp[aria-checked=\"true\"]{{background:#C79A5B;border-color:#C79A5B;color:#262422}}")

# ---- input: place, move and resize shapes instead of free drawing
i = s.index('  onDown(e) {', s.index('JS = r"""')); j = s.index('  onClear() {', i)
s = s[:i] + r'''  // ---------- shapes ----------
  shapePaths(type, cx, cy, R) {
    // shapes traced from the portfolio (CUT_SHAPES), scaled so the longer side is ~2R, centred on (cx, cy)
    const paths = window.CUT_SHAPES[type]();
    const all = [].concat(...paths.map((q) => q.pts));
    const x0 = Math.min(...all.map((p) => p[0])), x1 = Math.max(...all.map((p) => p[0])), y0 = Math.min(...all.map((p) => p[1])), y1 = Math.max(...all.map((p) => p[1]));
    const k = 2 * R / Math.max(x1 - x0, y1 - y0), mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
    return paths.map((q) => { const pts = q.pts.map((p) => this.clampP([cx + (p[0] - mx) * k, cy + (p[1] - my) * k])); if (q.closed) pts.push(pts[0]); return { pts, closed: q.closed }; });
  }
  setGroup(gid) {
    const gr = this.groups[gid];
    const keep = this.state.strokes.filter((s) => s.gid !== gid || s.cut);
    const fresh = this.shapePaths(gr.type, gr.cx, gr.cy, gr.R).map((q) => ({ pts: q.pts, closed: q.closed, nodes: [], cut: false, gid }));
    this.state.strokes = keep.concat(fresh);
  }
  groupBox(gid) {
    const pts = [].concat(...this.state.strokes.filter((s) => s.gid === gid && !s.cut).map((s) => s.pts));
    if (!pts.length) return null;
    return [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))];
  }
  onDown(e) {
    if (this.mode !== 'draw') return;
    e.preventDefault();
    try { ov.setPointerCapture(e.pointerId); } catch (err) {}
    this.groups = this.groups || {}; this.gseq = this.gseq || 0;
    const p = this.pt(e);
    const live = Object.keys(this.groups).map(Number).filter((gid) => this.groupBox(gid)).reverse();
    if (this.active && this.groupBox(this.active)) live.unshift(this.active);
    for (const gid of live) {
      const b = this.groupBox(gid), gr = this.groups[gid];
      if (gid === this.active && Math.hypot(p[0] - b[2], p[1] - b[3]) < 26) { this.drag = { gid, kind: 'size', d0: Math.hypot(p[0] - gr.cx, p[1] - gr.cy), R0: gr.R }; return; }
      if (p[0] > b[0] - 8 && p[0] < b[2] + 8 && p[1] > b[1] - 8 && p[1] < b[3] + 8) { this.active = gid; this.drag = { gid, kind: 'move', ox: p[0] - gr.cx, oy: p[1] - gr.cy }; draw(); return; }
    }
    const gid = ++this.gseq;
    this.groups[gid] = { type: this.sel || 'rosette', cx: p[0], cy: p[1], R: ({ wheat: 74, tracery: 56, mark: 50 })[this.sel || 'rosette'] || 52 };
    this.active = gid; this.setGroup(gid);
    this.drag = { gid, kind: 'move', ox: 0, oy: 0 };
    draw();
  }
  onMove(e) {
    const d = this.drag;
    if (!d) return;
    const p = this.pt(e), gr = this.groups[d.gid];
    if (d.kind === 'move') { gr.cx = p[0] - d.ox; gr.cy = p[1] - d.oy; }
    else gr.R = Math.max(18, Math.min(150, d.R0 * Math.hypot(p[0] - gr.cx, p[1] - gr.cy) / Math.max(10, d.d0)));
    this.setGroup(d.gid); draw();
  }
  onUp() { this.drag = null; }
''' + s[j:]
rep("    this.setState({ cur: null, strokes: this.state.strokes.filter((s) => s.cut) });",
    "    this.active = null;\n    this.setState({ cur: null, strokes: this.state.strokes.filter((s) => s.cut) });")

# ---- draw(): resize handle on the active shape, tray visibility, hints
rep("    uncut.forEach((s) => s.nodes.forEach((n) => { o += '<rect x=\"' + (n[0] - 3).toFixed(1) + '\" y=\"' + (n[1] - 3).toFixed(1) + '\" width=\"6\" height=\"6\" fill=\"#C79A5B\" stroke=\"#262422\" stroke-width=\"1\"/>'; }));",
    "    const ab = g.active && mode === 'draw' ? g.groupBox(g.active) : null;\n"
    "    if (ab) o += '<rect x=\"' + (ab[0] - 6).toFixed(1) + '\" y=\"' + (ab[1] - 6).toFixed(1) + '\" width=\"' + (ab[2] - ab[0] + 12).toFixed(1) + '\" height=\"' + (ab[3] - ab[1] + 12).toFixed(1) + '\" fill=\"none\" stroke=\"#262422\" stroke-width=\".8\" stroke-dasharray=\"2 4\" opacity=\".5\"/>'\n"
    "      + '<g transform=\"translate(' + ab[2].toFixed(1) + ',' + ab[3].toFixed(1) + ')\"><circle r=\"11\" fill=\"#C79A5B\" stroke=\"#262422\" stroke-width=\"1.2\"/><path d=\"M-4 -4 L4 4 M4 -1 V4 H-1 M-4 1 V-4 H1\" fill=\"none\" stroke=\"#262422\" stroke-width=\"1.4\"/></g>';")
rep("      if (n) hint = n + (n === 1 ? ' path' : ' paths') + ' ready · add more, or press Cut';",
    "      if (n) hint = 'drag to move · corner to resize · or press Cut';")
rep("      else hint = 'draw on the flyer · close a shape · press Cut';",
    "      else hint = 'pick a shape · tap the flyer to place it';")
rep("    $('armedRow').style.display = (mode === 'draw' || cutting || mode === 'parking') ? 'grid' : 'none';",
    "    $('armedRow').style.display = (mode === 'draw' || cutting || mode === 'parking') ? 'grid' : 'none';\n"
    "    $('tray').style.display = mode === 'draw' ? 'grid' : 'none';\n"
    "    document.querySelectorAll('.shp').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.shape === (g.sel || 'rosette'))));")
rep("$('cutB').addEventListener('click', () => g.onCut());",
    "$('cutB').addEventListener('click', () => g.onCut());\n"
    "document.querySelectorAll('.shp').forEach((b) => b.addEventListener('click', () => {\n"
    "  g.sel = b.dataset.shape;\n"
    "  g.active = null;  // the next tap on the flyer places this shape\n"
    "  draw();\n"
    "}));")
rep("const LOGO = __LOGO__;", "const LOGO = __LOGO__;\n" + open(D + '../motif/shapes.js').read().replace('\\\\', '\\\\\\\\'))
open(D + 'build_v6.py', 'w').write(s)
print('wrote build_v6.py')
