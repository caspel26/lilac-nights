# Changelog

## [1.0.1]

- `self` and `cls` move from lilac to violet (`#b98cff`), so `self.attribute`
  reads as two distinct tokens instead of one flat color.
- Class fields stay white where they are *declared* and lilac where they are
  *used*, via `variable.classMember.declaration` and `property.declaration`.

## [1.0.0]

Initial release.

- Dark theme built on a lilac/violet spine (`#b98cff` → `#d7b8ff`) with seven
  supporting accents, each assigned exactly one job.
- Full semantic token support, including `variable.classMember` so Python
  attribute access (`session.external_session_id`) reads distinctly from plain
  variables.
- All syntax colors contrast-checked against the editor background at WCAG AA
  (≥4.5:1).
- Complete workbench coverage: symbol icons, inlay hints, ghost text, testing
  and debug views, notebooks, terminal ANSI, and diff/merge decorations.
- Extra grammar coverage for YAML, TOML, Dockerfile, shell, SQL, `.env`, CSS,
  and git commit messages.
