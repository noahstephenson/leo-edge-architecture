# Render the reading draft

This optional renderer produces a Letter-size reading copy from
[the manuscript](../manuscript_draft.md). It renders the seven catalog-backed
diagrams, embeds the three evidence figures, keeps captions with their figures,
and keeps the candidate table with its heading. It also parses every generated
reference diagram with Mermaid. The numerical study does not depend on Node.

Use Node.js 22 or newer. From this directory:

```bash
npm ci
npx playwright install chromium
```

Then choose the installed browser. In PowerShell:

```powershell
$env:MANUSCRIPT_CHANNEL = 'chromium'
npm run render
```

On Linux or macOS:

```bash
MANUSCRIPT_CHANNEL=chromium npm run render
```

On Windows, `npm run render` uses installed Microsoft Edge by default.
`MANUSCRIPT_BROWSER` can instead name an explicit browser executable.
`node render.mjs <output-directory>` selects another destination.

The default output is `output/pdf/`: a PDF, a self-contained HTML reading copy,
individual figure PNGs, and a render manifest recording the source hash,
renderer versions, browser version, and diagram sizes. Derived reading copies
and installed Node packages are ignored by Git. Rebuild after manuscript edits.
CI retains its reading copy as an artifact for the exact commit being checked.

Body text is 11 pt. The renderer rejects diagram text below approximately 8 pt
at page width; visual inspection is still needed to assess arrows, labels, and
pagination. PDF bytes can vary with browser version and generated metadata.
This is a reading layout. Venue formatting remains separate.
