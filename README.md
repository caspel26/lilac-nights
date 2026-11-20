<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/icon.png" width="112" alt="Lilac Nights">
</p>

<h1 align="center">Lilac Nights</h1>

<p align="center">
  A dark VS Code theme with a lilac spine — built to be read for eight hours straight. Now with a light variant.
</p>

<p align="center">
  <a href="https://marketplace.visualstudio.com/items?itemName=caspel26.lilac-nights"><img src="https://img.shields.io/visual-studio-marketplace/v/caspel26.lilac-nights?color=b98cff&labelColor=211a2e&style=flat-square&label=vs%20marketplace" alt="VS Marketplace"></a>
  <a href="https://open-vsx.org/extension/caspel26/lilac-nights"><img src="https://img.shields.io/open-vsx/v/caspel26/lilac-nights?color=b98cff&labelColor=211a2e&style=flat-square&label=open%20vsx" alt="Open VSX"></a>
  <a href="https://open-vsx.org/extension/caspel26/lilac-nights"><img src="https://img.shields.io/open-vsx/dt/caspel26/lilac-nights?color=d7b8ff&labelColor=211a2e&style=flat-square&label=downloads" alt="Downloads"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-d7b8ff?labelColor=211a2e&style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/VS%20Code-%5E1.70-8ec5ff?labelColor=211a2e&style=flat-square" alt="VS Code ^1.70">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/workbench.png" width="860" alt="Lilac Nights workbench: explorer, tabs, Python editor, terminal and status bar (rendered from the theme file, not a VS Code screenshot)">
</p>

Most purple themes pick a purple and stop there — everything else drifts into
whatever hue was lying around. Lilac Nights runs the purple through the parts of
the code that carry *structure* (keywords, properties, decorators) and gives each
remaining hue exactly one job. The result stays unmistakably lilac without every
line looking the same.

The same rules hold across grammars: violet keywords, honey types, azure
calls, sage strings, and orchid for whatever the language treats as a
directive — decorators in Python, attributes in Rust, annotations in Java,
preprocessor lines in C++.

<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/gallery.png" width="860" alt="Gallery of Lilac Nights previews across languages (rendered from the theme file)">
</p>

Full-size previews for every language:
[docs/previews.md](https://github.com/caspel26/lilac-nights/blob/main/docs/previews.md).

## Palette

<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/palette.png" width="640" alt="Lilac Nights palette swatches (rendered from the theme file)">
</p>

## Three rules it follows

**1. Purple carries the structure.** Keywords, tags, `self`/`this`, and object
properties all live on the violet → lilac ramp, so the theme's identity shows up
on nearly every line instead of in one lonely accent.

**2. Each hue has exactly one job.** No color does double duty in a way that makes
two different concepts look alike. If something is azure, it is callable.

**3. Brightness tracks importance, not frequency.** Strings are the most common
thing in a file and the least worth scanning, so they sit below the names you
actually look for. Every syntax role clears WCAG AA (≥4.5:1) against the editor
background; the one deliberate exception is muted tag punctuation (`<`, `>`, `/`),
which sits at about 3.1:1 so it recedes behind the names. The ranking below is
deliberate rather than accidental:

| Token | Contrast |
|---|---|
| plain variables | 13.06 |
| classes, types | 11.34 |
| strings | 10.27 |
| properties, attributes | 9.74 |
| functions, methods | 9.25 |
| numbers, constants | 8.27 |
| parameters | 6.79 |
| keywords | 6.60 |
| comments | 4.55 |

## Light variant

**Lilac Nights Light** is derived from the dark theme with the same rules: the
same hue keeps the same job, and contrast is checked per role in CI. Pick it
with `Cmd+K Cmd+T` → **Lilac Nights Light**.

<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/workbench-pair.png" width="860" alt="Lilac Nights (dark, left) and Lilac Nights Light (right) workbench side by side (rendered from the theme files)">
</p>

## What it covers

Beyond the usual: **semantic tokens** (including `variable.classMember`, so
`session.external_session_id` reads as *variable → attribute* rather than one flat
blur), symbol icons, inlay hints, ghost text, bracket-pair colorization, testing
and debug views, notebooks, diff and merge decorations, and all 16 terminal ANSI
colors — in both **Dark** and **Light**.

Extra grammar rules for **Python, TypeScript, Java, C#, PHP, Vue, Markdown, YAML,
TOML, Dockerfile, shell, SQL, `.env`, CSS,** and git commit messages.

## Install

**From the VS Code Marketplace** — search *Lilac Nights* in the Extensions
panel, or:

```sh
code --install-extension caspel26.lilac-nights
```

**From Open VSX** — in VSCodium, Cursor, Windsurf or Gitpod, search *Lilac Nights*
in the Extensions panel, or:

```sh
codium --install-extension caspel26.lilac-nights
```

**From a release** — download the `.vsix` from
[Releases](https://github.com/caspel26/lilac-nights/releases/latest), then run
this in the folder you downloaded it to (the glob matches the file you
downloaded; use the exact file name if several `.vsix` files are there):

```sh
code --install-extension ./lilac-nights-*.vsix
```

**From source:**

```sh
git clone https://github.com/caspel26/lilac-nights.git
ln -s "$PWD/lilac-nights" ~/.vscode/extensions/lilac-nights
```

Then `Cmd+K Cmd+T` → **Lilac Nights** (or **Lilac Nights Light**).

## Terminal

The terminal gets all 16 ANSI colors mapped to the same palette:

<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/terminal.png" width="560" alt="Terminal colors (rendered from the theme file)">
</p>

Want to change something? See
[Making it yours](https://github.com/caspel26/lilac-nights/blob/main/docs/customizing.md).

## License

MIT — see [LICENSE](LICENSE).
