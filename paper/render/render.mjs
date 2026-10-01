// Optional reading-copy renderer. The catalogs and manuscript remain authoritative.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createServer } from 'node:http';
import { dirname, resolve, extname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { marked } from 'marked';
import { chromium } from 'playwright';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../..');
const output = resolve(process.argv[2] || resolve(root, 'output/pdf'));
await mkdir(output, { recursive: true });
const source = await readFile(resolve(root, 'paper/manuscript_draft.md'), 'utf8');
const views = await readFile(resolve(root, 'docs/reference/VIEWS.md'), 'utf8');
const viewBlocks = [...views.matchAll(/```mermaid\n([\s\S]*?)\n```/g)].map(match => match[1]);
const revision = process.env.GITHUB_SHA || process.env.MANUSCRIPT_REF
  || execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
const repoBase = `https://github.com/noahstephenson/leo-edge-architecture/blob/${revision}`;
const [prose, references] = source.split(/^## References\s*$/m);
const cited = new Set([...prose.matchAll(/\[(\d+)\]/g)].map(match => match[1]));
const listed = new Set([...references.matchAll(/^\[(\d+)\]/gm)].map(match => match[1]));
if ([...cited].some(id => !listed.has(id)) || [...listed].some(id => !cited.has(id))) {
  throw new Error('Citation numbers and reference entries do not agree');
}
const css = `
@page { size: Letter; margin: .75in .7in .7in; }
body { margin: 0; font: 11pt/1.42 Georgia, 'Times New Roman', serif; color: #17212b; }
main { width: 7.1in; margin: auto; }
h1 { font-size: 20pt; line-height: 1.18; margin: 0 0 12pt; }
h2 { font-size: 14pt; margin: 18pt 0 8pt; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14pt 0 6pt; break-after: avoid; }
p { margin: 0 0 9pt; orphans: 3; widows: 3; }
a { color: #254862; text-decoration: none; overflow-wrap: anywhere; }
code { font-size: 9pt; }
figure { margin: 13pt 0; break-inside: avoid; text-align: center; }
figure svg { display: block; margin: auto; }
figure img { display: block; width: 100%; height: auto; margin: auto; }
figcaption { font-size: 9.5pt; line-height: 1.3; text-align: left; margin-top: 7pt; }
table { width: 100%; border-collapse: collapse; font-size: 10pt; margin-bottom: 12pt; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
th, td { padding: 6pt 8pt; text-align: left; border-bottom: .5pt solid #abb4bc; vertical-align: top; }
th { background: #eef2f4; }
.table-block { break-inside: avoid; }
.table-caption { font-size: 9.5pt; margin: 10pt 0 5pt; }
.references p { font-size: 9.5pt; line-height: 1.35; }
@media screen { body { background: #e7ebee; } main { padding: .75in .7in; background: white; } }
`;
let body = marked.parse(source);
for (const match of [...body.matchAll(/<img src="([^"]+)"/g)]) {
  const path = resolve(root, 'paper', match[1]);
  if (relative(root, path).startsWith('..')) throw new Error('Image outside repository');
  const mime = extname(path) === '.svg' ? 'image/svg+xml' : 'image/png';
  body = body.replace(match[0], `<img src="data:${mime};base64,${(await readFile(path)).toString('base64')}"`);
}
const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>LEO imagery architecture manuscript</title><style>${css}</style></head><body><main>${body}</main></body></html>`;
// Serve only the local repository. No CDN or remote images are required.
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname === '/paper/manuscript.html') {
      res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.end(html); return;
    }
    const path = resolve(root, '.' + decodeURIComponent(url.pathname));
    const rel = relative(root, path);
    if (rel.startsWith('..') || rel.includes(':')) { res.writeHead(403).end(); return; }
    const types = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.svg': 'image/svg+xml' };
    res.setHeader('Content-Type', types[extname(path)] || 'application/octet-stream');
    res.end(await readFile(path));
  } catch { res.writeHead(404).end(); }
});
await new Promise(done => server.listen(0, '127.0.0.1', done));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  browser = await chromium.launch(process.env.MANUSCRIPT_BROWSER
    ? { executablePath: process.env.MANUSCRIPT_BROWSER }
    : { channel: process.env.MANUSCRIPT_CHANNEL || 'msedge' });
  const page = await browser.newPage({ viewport: { width: 1000, height: 1200 } });
  await page.route('**/*', route => route.request().url().startsWith(origin + '/')
    ? route.continue() : route.abort());
  await page.goto(origin + '/paper/manuscript.html');
  await page.emulateMedia({ media: 'print' });
  const diagrams = await page.evaluate(async ({ viewBlocks, repoBase }) => {
    const { default: mermaid } = await import('/paper/render/node_modules/mermaid/dist/mermaid.esm.min.mjs');
    mermaid.initialize({ startOnLoad: false, theme: 'base', securityLevel: 'strict',
      themeVariables: { fontFamily: 'Arial', fontSize: '16px', primaryColor: '#f4f7f9',
        primaryTextColor: '#17212b', lineColor: '#41576a', primaryBorderColor: '#41576a' },
      flowchart: { htmlLabels: false, useMaxWidth: false, curve: 'linear',
        rankSpacing: 18, nodeSpacing: 22, padding: 8,
        subGraphTitleMargin: { top: 8, bottom: 16 } },
      state: { useMaxWidth: false, padding: 8, rankSpacing: 40, nodeSpacing: 80 },
      sequence: { useMaxWidth: false, wrap: false, width: 100, height: 40,
        actorMargin: 10, mirrorActors: false, messageMargin: 5, noteMargin: 3,
        boxMargin: 4, boxTextMargin: 3, messageFontSize: 16, noteFontSize: 15 },
    });
    for (const block of viewBlocks) await mermaid.parse(block);
    const stats = [];
    for (const [i, code] of [...document.querySelectorAll('code.language-mermaid')].entries()) {
      const diagramSource = code.textContent.startsWith('stateDiagram')
        ? '%%{init: {"flowchart":{"nodeSpacing":120,"rankSpacing":25}}}%%\n' + code.textContent
        : code.textContent;
      const { svg } = await mermaid.render('diagram' + i, diagramSource);
      const figure = document.createElement('figure'); figure.innerHTML = svg;
      const pre = code.parentElement, caption = pre.nextElementSibling;
      pre.replaceWith(figure);
      if (caption?.textContent.startsWith('Fig.')) {
        const fc = document.createElement('figcaption'); fc.innerHTML = caption.innerHTML;
        caption.remove(); figure.append(fc);
      }
      const el = figure.querySelector('svg'), box = el.viewBox.baseVal;
      // Guard text sits across fragment borders in Mermaid's sequence renderer.
      // Mask only the background behind that text, preserving arrows and labels.
      for (const text of el.querySelectorAll('text.loopText')) {
        const bounds = text.getBBox();
        const background = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        for (const [name, value] of Object.entries({ x: bounds.x - 2, y: bounds.y - 1,
          width: bounds.width + 4, height: bounds.height + 2, fill: 'white' })) background.setAttribute(name, value);
        text.before(background);
      }
      const scale = Math.min(1, 681.6 / box.width, 810 / box.height);
      el.style.width = `${box.width * scale}px`; el.style.height = `${box.height * scale}px`;
      el.style.maxWidth = 'none';
      const fonts = [...el.querySelectorAll('text')].map(t => parseFloat(getComputedStyle(t).fontSize) * scale);
      stats.push({ figure: i + 1, width: box.width, height: box.height,
        renderedWidth: box.width * scale, renderedHeight: box.height * scale,
        minFontPx: Math.min(...fonts), caption: figure.querySelector('figcaption')?.textContent });
    }
    for (const img of document.querySelectorAll('p > img')) {
      const p = img.parentElement, caption = p.nextElementSibling;
      const figure = document.createElement('figure'); p.replaceWith(figure); figure.append(img);
      if (caption?.textContent.startsWith('Fig.')) {
        const fc = document.createElement('figcaption'); fc.innerHTML = caption.innerHTML;
        caption.remove(); figure.append(fc);
      }
    }
    for (const table of document.querySelectorAll('table')) {
      const caption = table.previousElementSibling;
      if (caption?.textContent.startsWith('Table')) {
        const block = document.createElement('div'); block.className = 'table-block';
        caption.className = 'table-caption'; caption.before(block); block.append(caption, table);
      }
    }
    let inRefs = false;
    for (const el of document.querySelector('main').children) {
      if (el.tagName === 'H2') inRefs = el.textContent === 'References';
      if (inRefs && el.tagName === 'P') {
        el.classList.add('references'); el.style.fontSize = '9.5pt';
        const n = el.textContent.match(/^\[(\d+)\]/)?.[1]; if (n) el.id = 'ref-' + n;
      }
    }
    for (const a of document.querySelectorAll('a')) {
      const href = a.getAttribute('href');
      if (href && !/^(https?:|#)/.test(href)) {
        const path = new URL(href, 'https://example.test/paper/manuscript_draft.md').pathname;
        a.href = repoBase + path;
      }
    }
    return stats;
  }, { viewBlocks, repoBase });
  const tooSmall = diagrams.filter(item => item.minFontPx < 10.6);
  if (tooSmall.length) throw new Error('Diagram text below 8 pt at reading size: ' + tooSmall.map(item => item.figure));
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.decode()));
  });
  await writeFile(resolve(output, 'manuscript_draft.html'), await page.content());
  await page.pdf({ path: resolve(output, 'manuscript_draft.pdf'), preferCSSPageSize: true,
    printBackground: true, displayHeaderFooter: true, headerTemplate: '<span></span>',
    footerTemplate: '<div style="font:9px Arial;width:100%;text-align:center;color:#52606b">Reading draft · <span class="pageNumber"></span> / <span class="totalPages"></span></div>' });
  const figures = [...await page.locator('figure').all()];
  for (const [i, figure] of figures.entries()) {
    await figure.screenshot({ path: resolve(output, `figure-${i + 1}.png`) });
  }
  const hash = value => createHash('sha256').update(value).digest('hex');
  const manifest = { source: 'paper/manuscript_draft.md', source_sha256: hash(source.replace(/\r\n?/g, '\n')),
    renderer: { marked: '17.0.5', mermaid: '11.12.0', playwright: '1.62.1', browser: browser.version() },
    diagrams, figures: figures.length, parsed_catalog_views: viewBlocks.length,
    repository_revision: revision, references: listed.size,
    pdf_sha256: hash(await readFile(resolve(output, 'manuscript_draft.pdf'))) };
  await writeFile(resolve(output, 'render_manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
  console.log(JSON.stringify(manifest, null, 2));
} finally {
  await browser?.close(); await new Promise(done => server.close(done));
}
