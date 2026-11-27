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
TRAY_ICONS = {
    'circle': '<circle cx="12" cy="12" r="8.5"/>',
    'square': '<rect x="4" y="4" width="16" height="16"/>',
    'triangle': '<path d="M12 3.5 L21 19.5 H3 Z"/>',
    'hexagon': '<path d="M12 3 L19.8 7.5 V16.5 L12 21 L4.2 16.5 V7.5 Z"/>',
    'star': '<path d="M12 2.8 L14.6 9.2 L21.4 9.6 L16.1 13.9 L17.8 20.6 L12 16.9 L6.2 20.6 L7.9 13.9 L2.6 9.6 L9.4 9.2 Z"/>',
    'heart': '<path d="M12 20.5 C5 15.5 2.8 12 2.8 8.6 C2.8 5.8 5 3.8 7.5 3.8 C9.4 3.8 11 4.9 12 6.6 C13 4.9 14.6 3.8 16.5 3.8 C19 3.8 21.2 5.8 21.2 8.6 C21.2 12 19 15.5 12 20.5 Z"/>',
    'arch': '<path d="M5.5 21 V11.5 C5.5 7.5 8.5 4.2 12 2.8 C15.5 4.2 18.5 7.5 18.5 11.5 V21 Z"/>',
    'mark': ''.join(f'<circle cx="{5.2 + 6.8*i:.1f}" cy="{5.2 + 6.8*j:.1f}" r="2.6"/>' for j in range(3) for i in range(3)),
}
tray = '<div id="tray" role="radiogroup" aria-label="Shapes">' + ''.join(
    f'<button class="shp" data-shape="{k}" role="radio" aria-label="{k}"><svg viewBox="0 0 24 24" width="24" height="24">{v}</svg></button>'
    for k, v in TRAY_ICONS.items()) + '</div>\n'
rep('<div id="armedRow" class="row row3">', tray + '<div id="armedRow" class="row row3">')
rep(".row{{display:grid;gap:8px}}",
    ".row{{display:grid;gap:8px}}\n"
    "#tray{{display:none;grid-template-columns:repeat(8,1fr);gap:6px}}\n"
    ".shp{{height:42px;border:1px solid rgba(241,233,220,.35);background:transparent;color:#F1E9DC;display:grid;place-items:center;cursor:pointer;padding:0;border-radius:0;-webkit-tap-highlight-color:transparent}}\n"
    ".shp svg{{fill:none;stroke:currentColor;stroke-width:1.6;stroke-linejoin:round}}\n"
    ".shp[aria-checked=\"true\"]{{background:#C79A5B;border-color:#C79A5B;color:#262422}}")

# ---- input: place, move and resize shapes instead of free drawing
i = s.index('  onDown(e) {', s.index('JS = r"""')); j = s.index('  onClear() {', i)
s = s[:i] + r'''  // ---------- shapes ----------
  shapePaths(type, cx, cy, R) {
    const ring = (n, r, rot, ox = 0, oy = 0) => { const a = []; for (let k = 0; k < n; k++) { const t = rot + k * 2 * Math.PI / n; a.push([ox + r * Math.cos(t), oy + r * Math.sin(t)]); } return a; };
    let paths;
    if (type === 'circle') paths = [ring(64, R, 0)];
    else if (type === 'square') { const h = R * 0.86; paths = [[[-h, -h], [h, -h], [h, h], [-h, h]]]; }
    else if (type === 'triangle') paths = [ring(3, R * 1.12, -Math.PI / 2)];
    else if (type === 'hexagon') paths = [ring(6, R, -Math.PI / 2)];
    else if (type === 'star') { const a = []; for (let k = 0; k < 10; k++) { const t = -Math.PI / 2 + k * Math.PI / 5, r = k % 2 ? R * 0.45 : R * 1.05; a.push([r * Math.cos(t), r * Math.sin(t)]); } paths = [a]; }
    else if (type === 'heart') { const a = []; for (let k = 0; k < 72; k++) { const t = k / 72 * 2 * Math.PI; a.push([16 * Math.pow(Math.sin(t), 3) * R / 16, -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) * R / 16]); } paths = [a]; }
    else if (type === 'arch') {
      // a pointed (Gothic) arch: two arcs struck from the opposite springing points
      const w = R * 0.66, base = R * 0.9, spring = 0, a = [[-w, base], [w, base], [w, spring]];
      for (let k = 1; k <= 18; k++) { const t = k / 18 * Math.PI / 3; a.push([-w + 2 * w * Math.cos(t), spring - 2 * w * Math.sin(t)]); }
      for (let k = 1; k <= 18; k++) { const t = 2 * Math.PI / 3 + k / 18 * Math.PI / 3; a.push([w + 2 * w * Math.cos(t), spring - 2 * w * Math.sin(t)]); }
      paths = [a];
    }
    else { const r = R * 0.27, step = R * 0.68; paths = []; for (let jj = -1; jj <= 1; jj++) for (let ii = -1; ii <= 1; ii++) paths.push(ring(36, r, 0, ii * step, jj * step)); }
    // centre on the shape's bounding box, then place it
    const all = [].concat(...paths);
    const mx = (Math.min(...all.map((p) => p[0])) + Math.max(...all.map((p) => p[0]))) / 2, my = (Math.min(...all.map((p) => p[1])) + Math.max(...all.map((p) => p[1]))) / 2;
    return paths.map((a) => { const q = a.map((p) => this.clampP([cx + p[0] - mx, cy + p[1] - my])); q.push(q[0]); return q; });
  }
  setGroup(gid) {
    const gr = this.groups[gid];
    const keep = this.state.strokes.filter((s) => s.gid !== gid || s.cut);
    const fresh = this.shapePaths(gr.type, gr.cx, gr.cy, gr.R).map((pts) => ({ pts, closed: true, nodes: [], cut: false, gid }));
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
    this.groups[gid] = { type: this.sel || 'circle', cx: p[0], cy: p[1], R: 46 };
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
    "    document.querySelectorAll('.shp').forEach((b) => b.setAttribute('aria-checked', String(b.dataset.shape === (g.sel || 'circle'))));")
rep("$('cutB').addEventListener('click', () => g.onCut());",
    "$('cutB').addEventListener('click', () => g.onCut());\n"
    "document.querySelectorAll('.shp').forEach((b) => b.addEventListener('click', () => {\n"
    "  g.sel = b.dataset.shape;\n"
    "  g.active = null;  // the next tap on the flyer places this shape\n"
    "  draw();\n"
    "}));")
open(D + 'build_v6.py', 'w').write(s)
print('wrote build_v6.py')
