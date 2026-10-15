const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(process.env.HTTPS_PROXY ? { args: ['--ignore-certificate-errors'], proxy: { server: process.env.HTTPS_PROXY } } : {});
  const p = await b.newPage();
  await p.goto('https://transparency.meta.com/reports/regulatory-transparency-reports/', { waitUntil: 'networkidle', timeout: 90000 });
  const heading = p.getByText('India Monthly Report under the Information Technology', { exact: false }).first();
  const c = heading.locator('xpath=ancestor::div[.//*[normalize-space(text())="Download report"]][1]');
  const tp = c.locator('[role=combobox][aria-label="Time Period"]');
  const mo = c.locator('[role=combobox][aria-label="Month"]');
  const opts = async (combo) => { await combo.click(); const id = await combo.getAttribute('aria-controls'); const lb = p.locator('#'+id); await lb.waitFor(); const o = await lb.locator('[role=option]').allInnerTexts(); await p.keyboard.press('Escape'); return o.map(s=>s.trim()); };
  const pick = async (combo, text) => { await combo.click(); const id = await combo.getAttribute('aria-controls'); await p.locator('#'+id).locator('[role=option]', { hasText: text }).first().click(); await p.waitForTimeout(300); };
  const years = await opts(tp);
  console.error('years', years);
  const out = [];
  for (const y of years) {
    await pick(tp, y);
    const months = await opts(mo);
    for (const m of months) {
      await pick(mo, m);
      const href = await c.locator('a', { hasText: 'Download report' }).getAttribute('href');
      out.push({ period: y, month: m, href });
      console.error(y, m, href);
    }
  }
  require('fs').writeFileSync(process.argv[2] || 'meta_links.json', JSON.stringify(out, null, 1));
  await b.close();
})();
