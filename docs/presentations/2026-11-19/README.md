# Presentations

Slides about the GridFM demo, written with [Slidev](https://sli.dev) and the
modern layouts of
[slidev-theme-alex](https://github.com/alexandrainst/slidev-theme-alex).

## Dependencies

The slides need Node.js with npm, and the Slidev theme
[slidev-theme-alex](https://github.com/alexandrainst/slidev-theme-alex). The theme is
not on the npm registry. `package.json` installs it from GitHub:

```json
"slidev-theme-alex": "github:alexandrainst/slidev-theme-alex"
```

## Usage

Install the dependencies, the theme included, once:

```bash
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm install
```

To install only the theme, for example in another project:

```bash
npm install github:alexandrainst/slidev-theme-alex
```

Then set `theme: alex` in the frontmatter of the slides.

Start the slides in the browser:

```bash
npm run dev
```

`npm run build` writes a static site to `dist/`. `npm run export` writes a PDF
and needs a Chromium, which `npx playwright install chromium` downloads.

The layouts and their frontmatter are described in the
[theme README](https://github.com/alexandrainst/slidev-theme-alex#modern-variant).
