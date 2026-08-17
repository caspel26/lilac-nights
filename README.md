# Lilac Nights

A dark VS Code theme built around a lilac/violet spine, with a small, deliberate
set of supporting accents. Every color is contrast-checked against the editor
background (WCAG AA, ≥4.5:1 for text-weight tokens).

## Design rules

1. **Purple carries the structure of the code.** Keywords, storage/modifiers,
   tags, `self`/`this`, and object properties are all in the violet→lilac ramp,
   so the theme's identity shows up on nearly every line without shouting.
2. **Each supporting hue has exactly one job.** No color does double duty in a
   way that makes two different concepts look alike.
3. **Attention follows rarity.** Frequent tokens (strings, variables, properties)
   sit calm and low-contrast-ish; rare, high-signal tokens (keywords, decorators,
   errors) are the brightest things on screen.

## Palette

### Purple spine
| Role | Hex | Used for |
|---|---|---|
| Violet | `#b98cff` | keywords **incl. flow control** (`return`/`raise`/`await`), tags, badges, buttons, primary UI accent |
| Lilac | `#d7b8ff` | **properties & attributes** (`session.external_session_id`), HTML/YAML attrs & keys, shell vars, storage/modifiers, `self`/`this`, cursor, focus ring, active borders |
| Orchid | `#f18ce8` | decorators / macros |

### Supporting accents
| Role | Hex | Used for |
|---|---|---|
| Azure | `#7ab8ff` | functions, methods |
| Aqua | `#5fe3d4` | operators, regex, escapes, enum members |
| Honey | `#ffcc80` | classes, types, namespaces, CSS selectors |
| Sage | `#9ce8a4` | strings |
| Red | `#ff6b85` | **function parameters**, errors |
| Coral | `#ff9d7a` | numbers, constants |


**Plain variables stay white** (`#e6e0f5`) so attributes stand out against them.

### Surfaces
`#15111f` chrome · `#1a1526` panels/sidebar · `#211a2e` editor · `#2b2340`
line highlight · `#372c52` / `#453863` selection & borders

## Install

```sh
ln -s ~/vscode-themes/lilac-nights ~/.vscode/extensions/lilac-nights
```

Reload VS Code, then `Cmd+K Cmd+T` → **Lilac Nights**.

## Tweaking

- UI colors: `themes/lilac-nights-color-theme.json` → `"colors"`
- Grammar syntax colors: → `"tokenColors"`
- LSP-driven per-symbol colors: → `"semanticTokenColors"`

Reload the window after edits — no rebuild needed.

## Packaging

```sh
npm install -g @vscode/vsce
cd ~/vscode-themes/lilac-nights
vsce package
code --install-extension lilac-nights-1.0.0.vsix
```
