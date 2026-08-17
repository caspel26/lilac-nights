<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/icon.png" width="112" alt="Lilac Nights">
</p>

<h1 align="center">Lilac Nights</h1>

<p align="center">
  A dark VS Code theme with a lilac spine — built to be read for eight hours straight.
</p>

<p align="center">
  <a href="https://open-vsx.org/extension/caspel26/lilac-nights"><img src="https://img.shields.io/open-vsx/v/caspel26/lilac-nights?color=b98cff&labelColor=211a2e&style=flat-square&label=open%20vsx" alt="Open VSX"></a>
  <a href="https://open-vsx.org/extension/caspel26/lilac-nights"><img src="https://img.shields.io/open-vsx/dt/caspel26/lilac-nights?color=d7b8ff&labelColor=211a2e&style=flat-square&label=downloads" alt="Downloads"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-d7b8ff?labelColor=211a2e&style=flat-square" alt="MIT"></a>
  <img src="https://img.shields.io/badge/VS%20Code-%5E1.70-7ab8ff?labelColor=211a2e&style=flat-square" alt="VS Code ^1.70">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/preview-python.png" width="720" alt="Lilac Nights in Python">
</p>

Most purple themes pick a purple and stop there — everything else drifts into
whatever hue was lying around. Lilac Nights runs the purple through the parts of
the code that carry *structure* (keywords, properties, decorators) and gives each
remaining hue exactly one job. The result stays unmistakably lilac without every
line looking the same.

## Palette

![Palette](https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/palette.png)

## Three rules it follows

**1. Purple carries the structure.** Keywords, tags, `self`/`this`, and object
properties all live on the violet → lilac ramp, so the theme's identity shows up
on nearly every line instead of in one lonely accent.

**2. Each hue has exactly one job.** No color does double duty in a way that makes
two different concepts look alike. If something is azure, it is callable.

**3. Brightness tracks importance, not frequency.** Function names outrank string
literals, because that's the order you read them in. Every syntax color clears
WCAG AA (≥4.5:1) against the editor background, and the ranking below is
deliberate rather than accidental:

| Token | Contrast |
|---|---|
| plain variables | 13.06 |
| strings | 11.58 |
| classes, types | 11.34 |
| properties, attributes | 9.74 |
| functions, methods | 8.09 |
| numbers, constants | 8.27 |
| parameters | 6.15 |
| comments | 4.49 |

## Previews

The same rules hold across grammars: violet keywords, honey types, azure
calls, sage strings, and orchid for whatever the language treats as a
directive — decorators in Python, attributes in Rust, preprocessor lines in
C++. Pick a language:

<p align="center">
  <a href="https://github.com/caspel26/lilac-nights/blob/main/images/preview-python.png"><img src="https://img.shields.io/badge/Python-211a2e?style=for-the-badge&logo=python&logoColor=b98cff&labelColor=211a2e&color=211a2e" alt="Python"></a>
  <a href="https://github.com/caspel26/lilac-nights/blob/main/images/preview-typescript.png"><img src="https://img.shields.io/badge/TypeScript-211a2e?style=for-the-badge&logo=typescript&logoColor=b98cff&labelColor=211a2e&color=211a2e" alt="TypeScript"></a>
  <a href="https://github.com/caspel26/lilac-nights/blob/main/images/preview-javascript.png"><img src="https://img.shields.io/badge/JavaScript-211a2e?style=for-the-badge&logo=javascript&logoColor=b98cff&labelColor=211a2e&color=211a2e" alt="JavaScript"></a>
  <a href="https://github.com/caspel26/lilac-nights/blob/main/images/preview-go.png"><img src="https://img.shields.io/badge/Go-211a2e?style=for-the-badge&logo=go&logoColor=b98cff&labelColor=211a2e&color=211a2e" alt="Go"></a>
  <a href="https://github.com/caspel26/lilac-nights/blob/main/images/preview-rust.png"><img src="https://img.shields.io/badge/Rust-211a2e?style=for-the-badge&logo=rust&logoColor=b98cff&labelColor=211a2e&color=211a2e" alt="Rust"></a>
  <a href="https://github.com/caspel26/lilac-nights/blob/main/images/preview-cpp.png"><img src="https://img.shields.io/badge/C%2B%2B-211a2e?style=for-the-badge&logo=cplusplus&logoColor=b98cff&labelColor=211a2e&color=211a2e" alt="C++"></a>
</p>

## What it covers

Beyond the usual: **semantic tokens** (including `variable.classMember`, so
`session.external_session_id` reads as *variable → attribute* rather than one flat
blur), symbol icons, inlay hints, ghost text, bracket-pair colorization, testing
and debug views, notebooks, diff and merge decorations, and all 16 terminal ANSI
colors.

Extra grammar rules for **Python, TypeScript, YAML, TOML, Dockerfile, shell, SQL,
`.env`, CSS,** and git commit messages.

## Install

**From Open VSX** — in VSCodium, Cursor, Windsurf or Gitpod, search *Lilac Nights*
in the Extensions panel, or:

```sh
codium --install-extension caspel26.lilac-nights
```

**From a release** — for stock VS Code, which doesn't search Open VSX. Download
the `.vsix` from
[Releases](https://github.com/caspel26/lilac-nights/releases/latest), then:

```sh
code --install-extension lilac-nights-1.0.1.vsix
```

**From source:**

```sh
git clone https://github.com/caspel26/lilac-nights.git
ln -s "$PWD/lilac-nights" ~/.vscode/extensions/lilac-nights
```

Then `Cmd+K Cmd+T` → **Lilac Nights**.

The terminal gets all 16 ANSI colors mapped to the same palette:

<p align="center">
  <img src="https://raw.githubusercontent.com/caspel26/lilac-nights/main/images/terminal.png" width="560" alt="Terminal colors">
</p>

## Making it yours

Everything lives in one file, [`themes/lilac-nights-color-theme.json`](themes/lilac-nights-color-theme.json):

| Section | Controls |
|---|---|
| `colors` | the workbench — chrome, sidebar, terminal, widgets |
| `tokenColors` | syntax, via TextMate grammar scopes |
| `semanticTokenColors` | per-symbol colors from the language server |

Reload the window after editing — no build step. To find out which rule is
painting a token, run **Developer: Inspect Editor Tokens and Scopes** from the
command palette; it names the winning rule directly.

Semantic tokens override TextMate scopes, which is the usual reason an edit
appears to do nothing.

## License

MIT — see [LICENSE](LICENSE).
