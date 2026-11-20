# Design v1.2: Lilac Nights Glow and Lilac Nights Glass

Status: design only, nothing implemented. Target version **1.2.0**. Adds two themes
beside the existing two. `Lilac Nights` (dark) and `Lilac Nights Light` must stay
byte-identical; every step below keeps `git diff themes/lilac-nights-color-theme.json
themes/lilac-nights-light-color-theme.json` empty.

| New theme | Parent | `uiTheme` | One-line concept |
|---|---|---|---|
| Lilac Nights Glow | Light | `vs` | Lilac-tinted whites, a saturated violet accent, slightly see-through floating widgets with violet edges and lilac halos |
| Lilac Nights Glass | Dark | `vs-dark` | Deeper chrome, lifted translucent widgets with thin luminous edges, a restrained lilac halo |

## 0. What a colors-only theme can and cannot do

A theme is a JSON of colors. There is no blur, `backdrop-filter`, gradient, radius or
shadow geometry. Injected CSS ("Custom CSS and JS") is unsupported and is out of
scope. Everything below uses only the colours VS Code already exposes.

Confirmed from the official reference (`microsoft/vscode-docs`
`api/references/theme-color.md`, fetched 2026-11-20) and the VS Code source
(`release/1.70` and `main`):

- **Alpha.** Every colour accepts `#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA`. Missing alpha means opaque (theme-color.md l.28-30). Some keys *must* be translucent ("must not be opaque so as not to hide underlying decorations": selection highlight, word highlight, find, diff, merge, hover highlight; l.32, l.409-431, l.672-679). Others must be opaque (`editorGutter.itemBackground`, comment ruler markers).
- **Compositing.** Alpha is applied as a CSS colour, so it blends with whatever DOM is underneath. For a docked part (side bar, panel, status bar) the thing underneath is a flat workbench background, so alpha only gives a *different flat colour*: no depth, no glass. For an **overlay** widget positioned over the editor (suggest, hover, parameter hints, find, quick input, notification toasts, custom menus), the code underneath shows through with **no blur**. That is the only place "glass" can exist. That widget backgrounds really composite over the view lines is the expected DOM behaviour, but it was not seen: **[unverified]**, check it in the EDH (section 5).
- **Shadows.** The theme picks the colour; VS Code fixes the geometry:
  - `widget.shadow` defaults to black at .36 (dark) and .16 (light) (`colorRegistry.ts`, 1.70 l.238).
  - In 1.70 the quick input applies it as `box-shadow: 0 0 8px 2px <color>` (`quickInput.ts` l.1807). That is a symmetric soft band, so a tinted alpha colour does read as a halo.
  - On `main`, the suggest widget uses `0 2px 8px` (`suggest.css` l.14), a downward-biased tint.
  - So geometry varies by widget and version, and the theme cannot set it.
- **`widget.shadow` is not only a shadow.** It also paints:
  - keybinding chips in the command palette's focused and hovered rows (`quickInput.css` on `main` l.459, `border-color`);
  - an inset underline under keybinding labels (`actionWidget.css` l.305; in 1.70 `styler.ts` l.279 falls back `keybindingLabelShadow` to it, drawn `inset 0 -1px 0` in `quickInput.ts` l.1842).

  A saturated lilac shadow therefore also tints those chips, which is acceptable (it is on-brand) but must be looked at.
- **Other shadow keys:** `scrollbar.shadow` (the band along the top of any scrolled editor or list), `listFilterWidget.shadow` (both in 1.70); `editorStickyScroll.shadow`, `sideBarStickyScroll.shadow`, `panelStickyScroll.shadow`, `inlineChat.shadow` exist on `main` but **not** in 1.70.
- **Focus and outline keys** (all in 1.70): `focusBorder`, `contrastBorder`, `contrastActiveBorder`, `list.focusOutline`, `list.focusAndSelectionOutline`, `inputOption.activeBorder`, `editorWidget.border`, `editorWidget.resizeBorder`, `editorSuggestWidget.border`, `editorHoverWidget.border`, `peekView.border`, `menu.border`, `menu.selectionBorder`, `notificationToast.border`, `notificationCenter.border`, `notifications.border`, `editor.lineHighlightBorder`, `tab.activeBorderTop`.
- **Keys newer than the engine floor.** `widget.border` (the generic widget-border fallback) and the sticky-scroll shadows are absent from `release/1.70`. Older VS Code ignores unknown colour ids, so they are safe but inert there **[unverified: no 1.70 run]**. The plan below avoids them; every key it sets is in the 1.70 registry (checked by grep of `colorRegistry.ts`, `workbench/common/theme.ts` and `editorColorRegistry.ts` at `release/1.70`).
- **Inherited defaults.** A key the theme leaves unset follows its registry default, so changing one key also changes its dependents. Glass must pin these (1.70 registry; dark sets none of them):
  - From `editorWidget.background`:
    - `editorHoverWidget.statusBarBackground` = `lighten(hover bg, .2)`. It would come out translucent. Pin it opaque, `#382957`, via `add`.
    - `listFilterWidget.background` covers a list, not code. Pin it opaque, `#271f3a`.
    - `breadcrumbPicker.background` and `editorGroup.dropIntoPromptBackground` are overlays, and translucency is acceptable for both.
    - `notifications.background` and `quickInput.background` are already set by dark.
  - From `widget.shadow`: `listFilterWidget.shadow`, plus the shadows of custom menus and modal dialogs (`styler.ts` l.329, l.366). They get the lilac halo too.
  - From `focusBorder`: `list.focusOutline` (set explicitly below) and `contrastActiveBorder` (only in high-contrast themes).
  - `menu.background` defaults to `dropdown.background` and `menu.selectionBackground` to `list.activeSelectionBackground`. Hence the explicit `menu.*` additions.
- **Menus.** `menu.*` only applies to VS Code's custom menus. Native menus (macOS menu bar, `window.titleBarStyle: native`, possibly macOS context menus) ignore them **[unverified per platform]**.
- **Avoid alpha on** `editor.background`, `terminal.background`, `editorStickyScroll.background` and `peekViewEditor.background`:
  - the first two are the base the code is drawn on;
  - sticky scroll sits over scrolled code and would show it through;
  - peek is an inline zone with nothing behind it.
  - `check-contrast.mjs` also composites `editor.background` over black, so it must stay opaque.

**Honest summary for users:** "Glass" in VS Code means layered surfaces, thin light edges,
tinted shadows, and floating widgets that let the code behind them show faintly. It is
not frosted glass: nothing behind a widget is blurred, so translucency is kept low.

## 1. Concept and palette

**Syntax colours do not change in either variant.** `tokenColors` and
`semanticTokenColors` are copied unchanged from the parent (Glow from Light, Glass from Dark):

- The syntax palette is the tuned, gated part of the project. Four syntax palettes would quadruple the work every colour change needs (rules 2 and 3), for no gain the owner asked for.
- The variants differ in the chrome, which is what "glow" and "glass" describe.
- Glass keeps `editor.background` `#211a2e`, so its syntax contrast table is exactly the dark one.
- Glow tints `editor.background` slightly. The measured contrast change is at most -0.02 for every role, and the rank order is unchanged (table below).

All values below were computed in OKLCH with the repo's own `derive_light.py`
conversions (scratch script, not committed). The hue is held on the theme's 297-305 violet axis.

### 1a. Glow (light, parent Light)

**Surfaces.** Warmer lilac whites: the same lightness as Light, with about twice the chroma.

| Role | Light | Glow | OKLCH (L C h) |
|---|---|---|---|
| editor bg | `#faf8fd` | `#fbf7ff` | .981 .011 308 |
| side bar / panel / input | `#f4f2f8` | `#f5f0fd` | .963 .018 303 |
| chrome (title, activity, status, tab strip) | `#e0dee8` | `#e7e0f6` | .919 .030 300 |
| line highlight / hover | `#e8e6f3` | `#eee8fb` | .941 .026 300 |
| borders, secondary selection | `#dad6eb` | `#e2d8f6` | .899 .042 301 |
| selection | `#cec7e5` | `#d8caf6` | .864 .062 300 |
| floating widgets (lifted card) | `#f4f2f8` | `#fdfbff` (override) | .991 .006 308 |

**Accent.** The accent is the existing keyword violet **`#8051bf`** (L .540, C .167), reused rather than a new hex. A first candidate `#7d40c8` sat at OKLab dE .039 from `#8051bf`, below the gate's 0.05, which is exactly the near-twin that rule 2 forbids. Reusing a syntax hex for chrome follows dark's own idiom (the dark cursor is the property lilac).

It replaces Light's dim `#684b8a` on:

- `editorCursor.foreground`, `terminalCursor.foreground`, `editorLineNumber.activeForeground`;
- `tab.activeBorderTop`, `activityBar.activeBorder`, `panelTitle.activeBorder`;
- `inputOption.activeBorder`, `progressBar.background`;
- `focusBorder` (as `#8051bf99`).

Measured contrast for the accent: cursor 5.16:1 on the editor, 4.57 on the line highlight, 4.26 on the chrome.

`editorBracketMatch.border` deliberately stays `#684b8a`. `#8051bf` is `editorBracketHighlight.foreground1`, so a violet box would vanish around level-1 brackets.

**Glow.**

- `widget.shadow` `#8051bf29`, replacing Light's `#2f2b3a29`.
- `editorWidget.border`, `editorSuggestWidget.border` and `editorHoverWidget.border` become `#8051bf47` (1.48:1 against the card).
- The lifted white card with a violet edge and a violet haze is the "glowing" widget.

**Glow widgets are translucent too (owner correction, as built).** Both variants carry both effects, with the same four dials: `widget.shadow` alpha, widget border alpha, `focusBorder` alpha and widget background alpha. Glow's floating widgets (`editorWidget`, `editorSuggestWidget`, `editorHoverWidget`, `quickInput`, `notifications`, plus added `menu.background`) are `#fdfbffeb` (alpha .92). The light-side worst glyph is the darkest syntax role (`#2f2b3a`); measured ghost at `eb` is 1.15:1, and the 1.35 cap is reached at `d6`, so `d6` is the floor. Added: `menu.*` (violet `#8051bf47` border, `#8051bf1f` separator, selection `#eee8fb`), `notificationToast.border` `#8051bf47`, `list.focusOutline` `#8051bf80`, and opaque pins `editorHoverWidget.statusBarBackground` `#f1ebfc`, `listFilterWidget.background` `#fdfbff`. Pane borders stay the mapped lilac `#e2d8f6` (no extra violet pane edge). Final Glow dials: widget bg `eb`, edge `47` on `#8051bf`, halo `29` on `#8051bf`, focus `99` on `#8051bf`.

**Syntax against the Glow background** (measured; Light value / Glow value):

- fg: 13.03 / 13.00
- types: 7.17 / 7.15
- strings: 6.63 / 6.61
- properties: 6.72 / 6.70
- functions: 6.30 / 6.28
- numbers: 5.93 / 5.92
- parameters: 5.43 / 5.41
- keywords: 5.18 / 5.16
- comments: 4.62 / 4.61
- tag punctuation: 3.23 / 3.22

Comments on the selection improve from 3.00 to 3.18, because the selection is lighter but more chromatic. Inactive chrome text `#82759f` measures 3.28 on the new chrome (it was 3.16 in Light).

### 1b. Glass (dark, parent Dark), with a measured glow

**Layering.** Chrome sinks, the editor stays, floating widgets lift, edges catch light.

| Role | Dark | Glass | OKLCH | How |
|---|---|---|---|---|
| chrome (activity, title, status, tab strip, ansiBlack) | `#15111f` | `#0f0b18` | .162 .027 297 | map |
| side bar, panel, terminal, input | `#1a1526` | `#1a1526` | .211 .034 297 | unchanged |
| editor | `#211a2e` | `#211a2e` | .236 .039 300 | unchanged |
| floating widgets: `editorWidget`, `editorSuggestWidget`, `editorHoverWidget`, `quickInput`, `notifications`, `debugToolBar` and (added) `menu.background` | `#1a1526` | `#271f3aeb` | .262 .050 296, alpha .92 | override / add |
| selected row inside a widget: `editorSuggestWidget.selectedBackground`, `quickInputList.focusBackground`, (added) `menu.selectionBackground` | `#372c52` | `#382957` | .322 .080 297 | override / add |
| luminous widget edge: `editorWidget.border`, `editorSuggestWidget.border`, `editorHoverWidget.border`, (added) `menu.border`, `notificationToast.border` | `#372c52` | `#d7b8ff47` | 1.96:1 vs the composited widget | override / add |
| pane edge: `sideBar.border`, `panel.border`, `editorGroup.border` | various | `#d7b8ff1f` | 1.24-1.30:1 vs neighbours | override |

`notificationCenterHeader.background`, `peekView*`, `editorStickyScroll.background` and the terminal stay opaque.

**Legibility of the translucent widget** (alpha `eb` = .92, measured):

- Over the editor background, the widget composites to `#271f39`. On it: fg 12.19, sub-text `#c3bade` 8.50, match highlight `#d7b8ff` 9.09, descriptions `#8b7eae` 4.24.
- **Worst case**, with the brightest glyph `#e6e0f5` directly under widget text: fg 9.94, descriptions 3.46. The ghost of that glyph against the clean widget is only 1.23:1, so it reads as texture, not text.
- On the same surface, the ghost and the worst-case descriptions measure:

  | alpha | ghost | worst-case descriptions |
  |---|---|---|
  | .85 | 1.53 | 2.81 |
  | .878 (`e0`) | 1.41 | 3.04 |
  | .89 (`e3`) | 1.35 | 3.17 |
  | .90 | 1.31 | 3.27 |

  The ghost cap (1.35) therefore sets the minimum alpha at `e3`. The default is `eb`.
- **Consequence:** descriptions (`descriptionForeground` `#8b7eae`) drop below AA on a lifted widget (4.24 vs 4.87 on dark's widget). Any lift above the editor lightness does this. I keep `#8b7eae` and treat descriptions as a muted role (floor 3.0) rather than add a brighter description hex. The candidate `#9588b8` sat dL .032 from comments, under `DL_MIN` .06: a near-twin.

**The glow on dark (owner addendum).** It is restrained, because a light halo on a dark surface *lightens* the code next to the widget and lowers its contrast. VS Code's default black shadow did the opposite. The ring-like glow comes from the borders, and the halo from `widget.shadow`.

| Lever | Key(s) | Default | Range |
|---|---|---|---|
| **Halo** (main dial) | `widget.shadow` alpha byte on `#b98cff` | `1f` | `14` subtle … `33` ceiling |
| Edge | widget borders alpha on `#d7b8ff` | `47` (1.96:1) | `33` (1.60) … `5c` (2.39) |
| Focus | `focusBorder` alpha on `#d7b8ff` (dark `90`) | `a6` (5.06:1 on `#1a1526`) | `90` (4.13) … `cc` (6.99) |
| Focused list row ring | (added) `list.focusOutline` | `#d7b8ff80` | `00` to switch off |

The halo cost is measured at full shadow alpha over the editor; the real peak is lower, because blur spreads it:

| `widget.shadow` | comments | tag punctuation | keywords | fg |
|---|---|---|---|---|
| `14` | 4.01 | | | |
| `1f` | 3.71 | 2.56 | 5.38 | 10.65 |
| `2e` | 3.30 | 2.27 | 4.78 | 9.47 |
| `33` | 3.18 | | | 9.12 |
| `3d` | 2.95 | 2.03 | 4.28 | 8.46 |
| `66` | 2.09 | 1.44 | 3.03 | 6.00 |

The gate (section 3) enforces comments ≥ 3.0 and fg ≥ 7 under the halo, which caps the dial at about `33`. `scrollbar.shadow` stays dark (`#0f0b1880` via the map), because a lilac band at the top of every scrolled list would be glow everywhere.

Glow's equivalent dial is `widget.shadow` on `#8051bf`: `1f` gives comments 3.92 under the halo, `29` (default) 3.70, and `3d` (ceiling) 3.32.

## 2. Generation: `build-variants.mjs` to N variants

The rule becomes: **edit only the dark theme and `tools/variants/*.json`, then run
`node tools/build-variants.mjs`.** CI keeps `--check`.

**As built:** `map` is total only when the variant's `type` differs from its base's (re-theming: Light from Dark); otherwise partial (Glow, Glass), so Glass's one-entry map has `base: "dark"`. `ADD_ALLOWED` lists the 17 `add` keys. The gate treats a variant as chrome-only (syntax identity asserted) when its `type` equals its parent's.

**Config schema** (each `tools/variants/<slug>.json`):

```json
{ "name": "Lilac Nights Glass", "type": "dark", "base": "dark",
  "out": "themes/lilac-nights-glass-color-theme.json",
  "map": {}, "alpha": {}, "overrides": {}, "add": {} }
```

- **`base`.** Either `"dark"` (the source file) or another variant's slug. `light.json` gets `base: "dark"`, `glow.json` gets `base: "light"`, `glass.json` gets `base: "dark"`. Build in topological order, feeding each child the *in-memory* output of its parent, so `--check` never depends on a stale file. A cycle or an unknown base is an error.
- **`map`.** It stays explicit and total for `light.json`, as today, so a new dark hex fails loudly there. For a `base` that is not dark, the map is **partial: unmapped means identity**. That keeps `glow.json` at about 6 entries instead of a 37-entry copy of Light that would drift. Glass's map is partial too (one entry). Checks:
  - a map key must be a hex present in the base;
  - every value must be `#rrggbb`;
  - **injectivity is checked on the composed function** `f(h) = map[h] ?? h` over all base hexes, so a remap cannot land on an untouched base hex. The ten candidate hexes above were grepped: none occurs in dark or light.
- **`alpha`.** Unchanged semantics: the keys are full hexes with alpha *in the base*. Widget translucency in Glass is **not** done here, because `#1a1526` is also the side bar, panel, terminal and input. It goes through per-key `overrides`.
- **`overrides`.** Unchanged: the key must exist in the base, and each entry needs `value` and `why`.
- **`add`** (new). Keys the base does not set, e.g. `menu.background`, `menu.border`, `menu.selectionBackground`, `menu.foreground`, `menu.separatorBackground`, `notificationToast.border`, `list.focusOutline`. Rules:
  - reject a key the base already has (use `overrides`);
  - each entry needs `value` and `why`;
  - insert deterministically: sorted, appended at the end of the `colors` block after the last entry (anchor `\n  },\n  "tokenColors"`, add a comma to the previous line, 4-space indent), so `--check` is byte-stable;
  - only keys present in `release/1.70` (section 0). Keep a short comment in the script naming that source, plus an allowlist array `ADD_ALLOWED` that is checked, so a typo'd key fails instead of being silently ignored by VS Code.
- **`name` and `type`** come from config, replacing the hardcoded `"Lilac Nights Light"` / `"light"` strings.
- **Function size.** Keep each function under complexity 15 by splitting `loadConfigs`, `order`, `checkConfig`, `generate`, `insertAdds`.

**Step 2a, refactor only.** Add `name/type/base/out` to `light.json` and generalise the script.
- Verify: `node tools/build-variants.mjs --check` passes, and `git diff --exit-code themes/` is empty after `node tools/build-variants.mjs`.
- Risk: a regex change in `generate` alters Light's bytes, which the empty diff catches.

## 3. Contrast and legibility gate (`check-contrast.mjs`)

1. **Explicit parent.** Today `themes.find(type === "dark")` picks the first dark file in sort order. That works only because `-color-` sorts before `-glass-`. Instead, read `tools/variants/*.json` and map `out` to `base`; a theme with no config is the root. Drift is checked against the declared parent, as today (5°).
2. **Syntax identity for chrome-only variants.** For Glow and Glass, assert that `tokenColors` and `semanticTokenColors` deep-equal the parent's. This is the hue-drift rule made exact: 0° drift. If an owner later wants a syntax change in a variant, they drop the assertion for that file and the 5° drift rule applies.
3. **The per-role floors, rank and neighbours** run unchanged against each theme's own `editor.background`. This catches Glow's tinted background.
4. **Overlay widgets (new).** The table is `[surfaceKey, [textKey, floor, worstFloor]...]` for `editorSuggestWidget.background`, `editorHoverWidget.background`, `editorWidget.background`, `quickInput.background`, `notifications.background` and `menu.background` (when set). Composite the surface over `editor.background`. If it has alpha < 1, also composite it over the **worst glyph**: the syntax role with the highest contrast against the editor (the brightest on dark, the darkest on light).
   - Floors: primary text (`editor.foreground` / `foreground` / `menu.foreground`) 7.0 normal and 4.5 worst. Highlight (`editorSuggestWidget.highlightForeground`, `list.highlightForeground`) 4.5 and 3.0. Descriptions (`descriptionForeground`) 3.0 and 3.0.
   - Ghost cap: `contrast(over glyph, over editor bg) ≤ 1.35`. The cap alone governs, and it implies alpha ≥ `e3` for Glass's surface; there is no separate alpha floor.
   - Applies to every theme. Dark and Light are opaque, so the check passes trivially.
5. **Halo.** Composite `widget.shadow` at full alpha over `editor.background`. Comments ≥ 3.0 and fg ≥ 7.0 on the result. This is a strict upper bound, because the blur only lowers the peak.
   - Computed by hand, not yet run: Dark's `#15111f80` gives comments 4.82; Light's `#2f2b3a29` gives comments 3.42 and fg 9.64. Both pass.
6. **Selection (informational, `--table` only).** Comments on `editor.selectionBackground`, with no gate. Light is already at 3.00 and Dark at 2.85, and changing that is out of scope.
7. **Keep `editor.background` opaque:** fail if it has alpha, because the gate's composite over black would be meaningless.

Verify each check by mutation: temporarily set Glass's widget alpha to `b3`, then its shadow to `#b98cff66`. The gate must fail with the expected message both times; revert.

## 4. Manifest, previews, README, CHANGELOG, packaging

**`package.json`**
- Add `{ "label": "Lilac Nights Glass", "uiTheme": "vs-dark", "path": "./themes/lilac-nights-glass-color-theme.json" }` and `{ "label": "Lilac Nights Glow", "uiTheme": "vs", "path": "./themes/lilac-nights-glow-color-theme.json" }` after the existing two.
- Add the keywords `glass` and `glow`. Description: "Dark, light, glass and glow themes with a lilac/violet spine and a contrast-checked syntax palette."
- Version `1.2.0`.

**`render_preview.py`**
- `theme_slug` already yields `-glass` and `-glow`.
- Because syntax equals the parent, the eleven language previews, the terminal and the palette for the new themes would duplicate their parent. Render **only `workbench-<slug>.png`** for a theme whose variant config is chrome-only (read `tools/variants/*.json`; no new manifest field). That is about 110 KB each.
- **Floating-widget overlay (needed, or the new mocks look like their parents).** Draw a suggest widget over the editor code, about 6 rows with one selected, plus a highlight match:
  - The canvas becomes RGBA internally and is flattened on save.
  - Shadow: a filled rect in `widget.shadow` on its own layer, grown by 2 px, `GaussianBlur(4 * scale)`, offset per the 1.70 quick-input geometry (`0 0 8px 2px`), then `alpha_composite`.
  - Body: `editorSuggestWidget.background` RGBA composited **over the already-drawn code**, so Glass shows the real ghosting.
  - Then a 1 px border and the rows.
  - It is an approximation of VS Code's CSS, not a capture; the alt text says "rendered from the theme file".
  - Drawing the overlay in every theme keeps the four mocks comparable, but it also **changes `workbench.png` / `workbench-light.png` / `workbench-pair.png`** (images, not themes). **Owner decision.** I recommend yes, in its own commit.
- `terminal.png` and `terminal-light.png` re-render regardless, because `vsce ls` gains two theme files and the vsix name becomes `-1.2.0`.
- Add `workbench-variants.png`, a 2x2 sheet (Dark, Light, Glass, Glow), with a generalised `pair()`. Keep `workbench-pair.png`, because the README uses it.
- Verify:
  - `python3 tools/render_preview.py`, then `git status --short images/`;
  - **sample pixels** with PIL (the widget body over a code row, the halo 3 px outside the edge, the border) and compare them with the composites in section 1.

**README**
- New section "Variants" after "Light variant", showing `workbench-variants.png`.
- One paragraph per theme. The Glass wording is honest: "VS Code themes can't blur. Glass layers the surfaces, gives floating widgets a thin light edge and a soft lilac halo, and lets the code behind them show faintly (8%)."
- Update the opening line and "What it covers" ("in all four themes").
- The language previews stay two-up (syntax is shared). Add a note: "Glass uses the dark syntax colours, Glow the light ones."

**CHANGELOG** `[1.2.0]`: two new themes, chrome-only and generated, with syntax identical to their parent; the generator and gate changes; no change to Dark or Light.

**Packaging**
- `.vscodeignore` already excludes `images/**`, `tools/**` and `DESIGN-*.md`, so the vsix grows by two theme JSONs (28 KB each today, uncompressed).
- `vsce ls` lists 4 theme files, and the terminal mock picks them up automatically.
- Release and CI need no workflow edit: they glob `themes/*.json` and run the same three scripts.

## 5. Commit plan, manual verification, risks

The commits are proposed only. Each one is presented for approval before it is made; the push and the release are separate approvals (CLAUDE.md). Trailers follow repo history (`Co-Authored-By`).

1. `refactor(tools): generalise build-variants to n configs with base and add`. Files: `tools/build-variants.mjs`, `tools/variants/light.json`. Verify: `--check` passes, `git diff --exit-code themes/`.
2. `feat(check): explicit parents, syntax identity, overlay and halo gates`. File: `.github/scripts/check-contrast.mjs`. Verify: passes on the current themes, and the mutation tests fail as expected.
3. `feat(theme): add Lilac Nights Glass`. Files: `tools/variants/glass.json`, the generated theme, the `package.json` entry. Verify: all four checks plus `npx @vscode/vsce@4.1.1 package`.
4. `feat(theme): add Lilac Nights Glow`. Same shape as 3.
5. `feat(preview): floating widget overlay and variant workbench sheet`. Files: `tools/render_preview.py`, `images/*`.
6. `docs(readme): variants section and honest glass wording`, plus `docs(handoff): four themes, variant schema, glow dials`. The HANDOFF variant rule, layout table and "things that will bite you" (the widget.shadow side effects) are updated.
7. `release: v1.2.0 — Glow and Glass variants`. Files: `package.json`, `CHANGELOG.md`. Tag and release only on explicit approval: Open VSX cannot overwrite a version.

Every theme commit runs:
- `node .github/scripts/check-colors.mjs`
- `node .github/scripts/check-contrast.mjs` (plus `--table`)
- `node tools/build-variants.mjs --check`
- `python3 tools/render_preview.py`

**Not verifiable headlessly; the owner checks these in the Extension Development Host** (F5), per theme. Use the pixel sampler of a screenshot tool, or Developer: Inspect Editor Tokens and Scopes, never a scaled screenshot.
- The command palette (`Cmd+Shift+P`) over a busy file such as `samples/Sample.cs`. Is the code faint behind it? Are the keybinding chips tinted lilac, and still readable?
- The suggest widget and hover over dense code: ghosting, the border, the halo, descriptions in the details pane.
- Context menu and title-bar menus on macOS, under both `window.titleBarStyle` values: do `menu.*` apply or are they native?
- Notification toasts over code, the find widget, parameter hints, peek view, sticky scroll.
- The focus ring on buttons and inputs; the focused list row with `list.focusOutline`.
- Glow: the lilac whites at reading length (is it tiring?), and cursor visibility on the line highlight.
- Old-engine check (optional): one run on VS Code 1.70 to confirm nothing breaks.

**Risks**
- *Legibility of translucent widgets.* Mitigated by `eb` alpha, the worst-glyph gate and the ghost cap. Residual risk: busy code at high zoom, and subpixel AA differences.
- *Halo lowering contrast near widgets.* Capped by the gate. It is only transient, while a widget is open.
- *`widget.shadow` side effects* on keybinding chips. Look at them in the EDH.
- *Maintenance.* Four themes:
  - Generation keeps the dark-only editing rule, and syntax identity means a syntax change is still one edit.
  - A new dark workbench key needs a decision in up to 3 configs; the partial maps hide most of that.
  - Every chrome hex is still grep-and-replace in dark (CLAUDE.md step 1).
- *User confusion.* Four entries in the picker. The labels name the parent's family (Glass is dark, Glow is light), and the README explains them in one paragraph each.
- *Platform variance* (native menus, the 1.70 versus current shadow geometry). It is documented and not controllable.

## Recommendation

Ship both, in the order of the commit plan, as **chrome-only generated variants with shared syntax**. They cost a config each, plus generator and gate work that also hardens the existing Light pipeline (explicit parents, the composed injectivity check).

Glass is the riskier of the two. Ship it with alpha `eb` and a glow dial at `1f`, and only after the owner's EDH pass on the palette, suggest widget and hover over busy code.

**If scope must shrink, cut in this order:**
1. the 2x2 sheet and the overlay on existing images (the new workbench images still need the overlay);
2. the `list.focusOutline` ring and the `menu.*` additions (no `add` support needed for the rest of Glass, apart from the menus);
3. Glass translucency itself: ship Glass with opaque lifted widgets, edges and the halo. It loses the "see-through" but keeps the layering, and the worst-glyph gate becomes trivial.

Glow (as built) is a 6-entry partial map, 13 accent/halo/border overrides, 5 translucent widget-background overrides and 9 `add` keys; it needs the `add` support and translucency like Glass.
