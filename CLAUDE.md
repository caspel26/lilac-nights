# Working in this repo

## Ask before anything leaves the working tree

**Do not `git commit`, `git push`, tag, or create a release without explicit
approval, every time.** Approval for one commit is not approval for the next.

This matters more here than in most repos: a release triggers
`.github/workflows/release.yml`, which publishes to Open VSX — and **Open VSX
will not let you overwrite a published version number.** A mistake that reaches
it cannot be undone, only superseded by burning a version.

Make the edits, run the checks, then stop and report what's staged for review.

## Orientation

Read [HANDOFF.md](HANDOFF.md) first. It covers the layout, the palette rules,
the release process, and the failure modes that have actually bitten this
project. What follows is only the part you need before touching a file.

## Before changing a color

1. **Grep the hex.** Most colors appear 20+ times across syntax, terminal ANSI,
   symbol icons and bracket pairs. Half-swapping a hue leaves two
   near-identical shades, which breaks the theme's one-job-per-hue rule.
2. **Check hue distance from neighbours in real code**, not just contrast
   against the background. A color can clear AAA and still read wrong beside
   the tokens it shares a line with.
3. **Re-run `python3 tools/render_preview.py`.** It reads the theme JSON, so
   skipping it leaves the README advertising colors that no longer exist.
   macOS only — it needs Menlo.
4. **Run `node .github/scripts/check-colors.mjs`.** VS Code silently ignores a
   malformed hex, so a typo just makes a color vanish with nothing to tell you
   why.

## Semantic tokens override TextMate scopes

If a `tokenColors` edit appears to do nothing, a `semanticTokenColors` rule is
winning. Don't guess — **Developer: Inspect Editor Tokens and Scopes** names the
winning rule directly.

Among matching rules, the one with the **most modifiers** wins; an equal count
is a tie the theme does not control. When adding a rule for a modifier that can
co-occur with another, add the combination explicitly. See HANDOFF.md for the
`settings.API_KEY` case where this was a real bug.

## Don't judge colors from a screenshot

Lilac `#d7b8ff` against white `#e6e0f5`, or lilac against honey `#ffcc80`, are
genuinely hard to tell apart in a scaled-down image — misreads have happened
more than once here. Sample the pixels or use the inspector, and say which one
you did.
