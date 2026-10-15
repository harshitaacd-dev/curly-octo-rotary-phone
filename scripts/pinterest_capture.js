const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const out = process.argv[2];
  const b = await chromium.launch(process.env.HTTPS_PROXY ? { args: ['--ignore-certificate-errors'], proxy: { server: process.env.HTTPS_PROXY } } : {});
  const p = await b.newPage();
  const src = 'https://policy.pinterest.com/en/india-transparency-report';
  await p.goto(src, { waitUntil: 'networkidle', timeout: 90000 });
  const items = await p.$$eval('[id^=accordion-]', ds => ds.filter(d => /^accordion-[a-z]+-\d{4}$/.test(d.id)).map(d => ({ id: d.id, title: d.querySelector('button').innerText.trim(), html: d.querySelector('[role=region]').innerHTML })));
  const months = { january:1,february:2,march:3,april:4,may:5,june:6,july:7,august:8,september:9,october:10,november:11,december:12 };
  const q = await b.newPage();
  for (const it of items) {
    const [, mon, yr] = it.id.match(/accordion-([a-z]+)-(\d{4})/);
    const name = `${out}/pinterest_india_${yr}-${String(months[mon]).padStart(2,'0')}`;
    const doc = `<!doctype html><html><head><meta charset="utf-8"><title>Pinterest India Transparency Report — ${it.title}</title><style>body{font-family:sans-serif;max-width:900px;margin:24px auto;padding:0 16px}table{border-collapse:collapse}td,th{border:1px solid #999;padding:4px 8px;vertical-align:top}</style></head><body><p><em>Source: ${src} (section “${it.title}”). Retrieved ${new Date().toISOString()}.</em></p><h1>Pinterest India Transparency Report — ${it.title}</h1>${it.html}</body></html>`;
    fs.writeFileSync(name + '.html', doc);
    await q.setContent(doc, { waitUntil: 'load' });
    fs.writeFileSync(name + '.txt', `Source: ${src} (section "${it.title}")\nRetrieved: ${new Date().toISOString()}\n\n` + await q.evaluate(() => document.body.innerText));
    await q.pdf({ path: name + '.pdf', format: 'A4', printBackground: true });
    console.log(it.title);
  }
  await b.close();
})();
