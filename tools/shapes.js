// Cut shapes drawn from Yarden's own work. Each returns a list of paths in unit space
// (roughly -1..1), each {pts, closed}. Closed paths become pieces; open paths are cut lines.
(function (root) {
  const TAU = Math.PI * 2;
  const arcPts = (cx, cy, r, a0, a1, n) => { const o = []; for (let k = 0; k <= n; k++) { const t = a0 + (a1 - a0) * k / n; o.push([cx + r * Math.cos(t), cy + r * Math.sin(t)]); } return o; };
  const close = (p) => ({ pts: p, closed: true });
  // a straight edge bowed outward (away from c) by `bow` x its length, sampled
  const bowed = (a, b, bow, c, n = 10) => {
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    let nx = -(b[1] - a[1]) / L, ny = (b[0] - a[0]) / L;
    if ((mx - c[0]) * nx + (my - c[1]) * ny < 0) { nx = -nx; ny = -ny; }
    const o = [];
    for (let k = 0; k < n; k++) { const t = k / n, off = bow * L * 4 * t * (1 - t); o.push([a[0] + (b[0] - a[0]) * t + nx * off, a[1] + (b[1] - a[1]) * t + ny * off]); }
    return o;
  };
  const lancet = (cx, base, spring, w, n = 14) => {
    // pointed (equilateral) arch, springing at y=spring, half-width w
    const o = [[cx - w, base], [cx + w, base], [cx + w, spring]];
    for (let k = 1; k <= n; k++) { const t = k / n * Math.PI / 3; o.push([cx - w + 2 * w * Math.cos(t), spring - 2 * w * Math.sin(t)]); }
    for (let k = 1; k <= n; k++) { const t = 2 * Math.PI / 3 + k / n * Math.PI / 3; o.push([cx + w + 2 * w * Math.cos(t), spring - 2 * w * Math.sin(t)]); }
    return o;
  };
  const lens = (cx, cy, len, wid, ang, n = 12) => {
    // a grain: two arcs meeting in points at both ends
    const o = [];
    for (let k = 0; k < n; k++) { const t = -1 + 2 * k / n; o.push([t * len / 2, -wid / 2 * (1 - t * t)]); }
    for (let k = 0; k < n; k++) { const t = 1 - 2 * k / n; o.push([t * len / 2, wid / 2 * (1 - t * t)]); }
    const c = Math.cos(ang), s = Math.sin(ang);
    return o.map(([x, y]) => [cx + x * c - y * s, cy + x * s + y * c]);
  };

  const SHAPES = {
    // Mashrabiya, Museum for Islamic Art: the eight-point star, each arm bowed out ~10% "into a petal"
    rosette() {
      const o = [];
      for (let k = 0; k < 8; k++) {
        const a = -Math.PI / 2 + k * TAU / 8, b = a + TAU / 16;
        const tip = [Math.cos(a), Math.sin(a)], inn = [0.56 * Math.cos(b), 0.56 * Math.sin(b)];
        const prevIn = [0.56 * Math.cos(a - TAU / 16), 0.56 * Math.sin(a - TAU / 16)];
        o.push(...bowed(prevIn, tip, 0.1, [0, 0]), ...bowed(tip, inn, 0.1, [0, 0]));
      }
      return [close(o)];
    },
    // Aumbry 2.0, the hand-carved Gothic piercing: a four-point star of concave arcs
    carvedStar() {
      const o = [], tips = [[0, -1], [0.78, 0], [0, 1], [-0.78, 0]];
      for (let k = 0; k < 4; k++) {
        const A = tips[k], B = tips[(k + 1) % 4], C = [(A[0] + B[0]) * 0.18, (A[1] + B[1]) * 0.18];
        for (let j = 0; j < 14; j++) { const t = j / 14; o.push([(1 - t) * (1 - t) * A[0] + 2 * (1 - t) * t * C[0] + t * t * B[0], (1 - t) * (1 - t) * A[1] + 2 * (1 - t) * t * C[1] + t * t * B[1]]); }
      }
      return [close(o)];
    },
    // Aumbry 2.0 tracery: two pointed lancets under a round oculus, three openings
    tracery() {
      return [close(lancet(-0.29, 1, 0.05, 0.25)), close(lancet(0.29, 1, 0.05, 0.25)), close(arcPts(0, -0.74, 0.2, 0, TAU, 40).slice(0, -1))];
    },
    // Seven Species porcelain: an ear of wheat, the stem a cut line, each grain its own piece
    wheat() {
      // an open ear: a gently curved stem, slender grains set apart and alternating, each with an awn
      const stem = (t) => [0.06 * (1 - t) * (1 - t) - 0.02 * t, 1.05 - 1.85 * t];   // t 0 (base) .. 1 (top)
      const sp = []; for (let k = 0; k <= 16; k++) sp.push(stem(k / 16));
      const p = [{ pts: sp, closed: false }];
      const L = 0.3, W = 0.11, gap = 0.05;
      [[0.42, -1], [0.54, 1], [0.66, -1], [0.78, 1], [0.88, -1]].forEach(([t, side]) => {
        const [x, y] = stem(t), ang = -Math.PI / 2 + side * 0.72;
        const cx = x + Math.cos(ang) * (gap + L / 2), cy = y + Math.sin(ang) * (gap + L / 2);
        p.push(close(lens(cx, cy, L, W, ang)));
        const tx = cx + Math.cos(ang) * L / 2, ty = cy + Math.sin(ang) * L / 2;
        p.push({ pts: [[tx + Math.cos(ang) * 0.03, ty + Math.sin(ang) * 0.03], [tx + Math.cos(ang - side * 0.18) * 0.3, ty + Math.sin(ang - side * 0.18) * 0.3]], closed: false });
      });
      const [x, y] = stem(1);
      p.push(close(lens(x, y - 0.04 - L / 2, L, W, -Math.PI / 2)));
      p.push({ pts: [[x, y - 0.08 - L], [x + 0.02, y - 0.38 - L]], closed: false });
      return p;
    },
    // The first ceramic test: an octagonal tile cut into eight tone wedges
    radialTile() {
      const v = []; for (let k = 0; k < 8; k++) { const a = -Math.PI / 2 + TAU / 16 + k * TAU / 8; v.push([Math.cos(a), Math.sin(a)]); }
      const p = [close(v)];
      v.forEach((q) => p.push({ pts: [[0, 0], q], closed: false }));
      return p;
    },
    // Parametric planters: one tapered terracotta pot from the gradient column
    planter() {
      return [close([[-0.74, -0.86], [0.74, -0.86], [0.74, -0.6], [0.64, -0.6], [0.44, 0.92], [-0.44, 0.92], [-0.64, -0.6], [-0.74, -0.6]])];
    },
    // Aumbry 2.0: the forged key
    key() {
      const cy = -0.55, r = 0.4, hw = 0.07, jy = cy + Math.sqrt(r * r - hw * hw);
      const a0 = Math.atan2(jy - cy, -hw), a1 = Math.atan2(jy - cy, hw) + TAU;
      const o = [[hw, jy], [hw, 0.52], [0.36, 0.52], [0.36, 0.64], [0.24, 0.64], [0.24, 0.74], [0.36, 0.74], [0.36, 0.9], [hw, 0.9], [hw, 1.0], [-hw, 1.0], [-hw, jy]];
      const arc = arcPts(0, cy, r, a0, a1, 44);
      return [close(o.concat(arc.slice(1, -1)))];
    },
    // Passover pot holders and Gothic tracery alike: the quatrefoil
    quatrefoil() {
      const o = [], d = 0.48, r = 0.48;
      [[d, 0, -Math.PI / 2], [0, d, 0], [-d, 0, Math.PI / 2], [0, -d, Math.PI]].forEach(([cx, cy, a]) => o.push(...arcPts(cx, cy, r, a, a + Math.PI, 20).slice(0, -1)));
      return [close(o)];
    },
    // G-code muddler: a toolpath ring with its coordinates jittered into a nest
    nest() {
      const o = []; let s = 7;
      const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
      for (let k = 0; k < 90; k++) { const a = k / 90 * TAU, rr = 1 + (rnd() - 0.5) * 0.12 + 0.04 * Math.sin(a * 7); o.push([rr * Math.cos(a), rr * Math.sin(a)]); }
      return [close(o)];
    },
    // the test-plate mark: nine circles
    mark() {
      const p = []; for (let j = -1; j <= 1; j++) for (let i = -1; i <= 1; i++) p.push(close(arcPts(i * 0.68, j * 0.68, 0.27, 0, TAU, 32).slice(0, -1)));
      return p;
    },
  };
  root.CUT_SHAPES = SHAPES;
})(typeof window !== 'undefined' ? window : globalThis);
