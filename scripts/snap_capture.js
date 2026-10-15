const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch(process.env.HTTPS_PROXY ? { args: ['--ignore-certificate-errors'], proxy: { server: process.env.HTTPS_PROXY } } : {});
  const idx = await b.newPage();
  await idx.goto('https://values.snap.com/privacy/transparency/india-transparency-page', { waitUntil: 'networkidle', timeout: 90000 });
  const links = await idx.$$eval('a', as => as.map(a => a.href).filter(h => /india-\d{2}-\d{4}/.test(h)));
  await idx.close();
  const out = process.argv[2];
  for (const u of [...new Set(links)]) {
    const [, mm, yyyy] = u.match(/india-(\d{2})-(\d{4})/);
    const base = `${out}/snap_india_${yyyy}-${mm}`;
    const p = await b.newPage();
    try {
      const r = await p.goto(u, { waitUntil: 'networkidle', timeout: 90000 });
      const txt = await p.evaluate(() => (document.querySelector('main') || document.body).innerText);
      fs.writeFileSync(base + '.txt', `Source: ${p.url()}\nRetrieved: ${new Date().toISOString()}\n\n` + txt);
      await p.emulateMedia({ media: 'screen' });
      await p.pdf({ path: base + '.pdf', format: 'A4', printBackground: true });
      console.log(yyyy, mm, r.status(), txt.length);
    } catch (e) { console.log(yyyy, mm, 'ERR', e.message.slice(0, 100)); }
    await p.close();
  }
  await b.close();
})();
