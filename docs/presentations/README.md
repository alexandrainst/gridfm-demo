# Presentations

Slides about the GridFM demo, written with [Slidev](https://sli.dev) and the
modern layouts of
[slidev-theme-alex](https://github.com/alexandrainst/slidev-theme-alex).

## Usage

Install the dependencies once:

```bash
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install
```

Start the slides in the browser:

```bash
npm run dev
```

`npm run build` writes a static site to `dist/`. `npm run export` writes a PDF
and needs a Chromium, which `npx playwright install chromium` downloads.

The layouts and their frontmatter are described in the
[theme README](https://github.com/alexandrainst/slidev-theme-alex#modern-variant).
