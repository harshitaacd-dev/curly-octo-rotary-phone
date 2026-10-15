const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(process.env.HTTPS_PROXY ? { args: ['--ignore-certificate-errors'], proxy: { server: process.env.HTTPS_PROXY } } : {});
  const p = await b.newPage();
  const r = await p.goto('https://www.whatsapp.com/legal/india-monthly-reports', { waitUntil: 'networkidle', timeout: 90000 });
  console.log('status', r.status(), p.url(), await p.title());
  require('fs').writeFileSync(process.argv[2] || 'whatsapp_index.html', await p.content());
  const links = await p.$$eval('a', as => as.map(a => (a.innerText||'').trim().replace(/\s+/g,' ').slice(0,100) + ' | ' + a.href));
  for (const l of links) if (/report|pdf|fbcdn|20\d\d/i.test(l)) console.log(l);
  const t = await p.evaluate(()=>document.body.innerText); console.log(t.slice(0,3000));
  await b.close();
})();
