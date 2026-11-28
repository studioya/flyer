// node shoot.js out.png "query" ; renders render.html?query and saves the canvas as a transparent PNG
const { chromium } = require('playwright');
(async () => {
  const jobs = JSON.parse(process.argv[2]);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage();
  p.on('console', (m) => console.log('console:', m.text())); p.on('pageerror', (e) => console.log('err:', e.message));
  for (const [out, q] of jobs) {
    await p.goto('http://127.0.0.1:8765/' + (process.env.PAGE || 'render.html') + '?' + q);
    await p.waitForFunction('window.DONE === true', null, { timeout: 300000 });
    const data = await p.evaluate(() => document.getElementById('out').toDataURL('image/png'));
    require('fs').writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
    console.log('wrote', out);
  }
  await b.close();
})();
