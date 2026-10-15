// usage: node capture.js <outdir> <listfile: "basename url" per line>
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [out, list] = process.argv.slice(2);
  const items = fs.readFileSync(list, 'utf8').trim().split('\n').map(l => l.split(' '));
  const b = await chromium.launch(process.env.HTTPS_PROXY ? { args: ['--ignore-certificate-errors'], proxy: { server: process.env.HTTPS_PROXY } } : {});
  for (const [name, u] of items) {
    const p = await b.newPage();
    try {
      const r = await p.goto(u, { waitUntil: 'networkidle', timeout: 90000 });
      const title = await p.title();
      if (r.status() >= 400 || /not found|404/i.test(title)) { console.log(name, 'MISSING', r.status(), title); await p.close(); continue; }
      const txt = await p.evaluate(() => (document.querySelector('article') || document.querySelector('main') || document.body).innerText);
      fs.writeFileSync(`${out}/${name}.txt`, `Source: ${p.url()}\nRetrieved: ${new Date().toISOString()}\n\n` + txt);
      await p.emulateMedia({ media: 'screen' });
      await p.pdf({ path: `${out}/${name}.pdf`, format: 'A4', printBackground: true });
      console.log(name, r.status(), txt.length, title);
    } catch (e) { console.log(name, 'ERR', e.message.slice(0, 100)); }
    await p.close();
  }
  await b.close();
})();
