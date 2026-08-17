# Changelog

## [1.0.3]

- Parameters retuned from `#fb92bb` to `#f17ec1`. Same hue-separation goals as
  1.0.2, refined twice more against real code:
  - Dimmed lightness/saturation (L .78/S .93 → L .72/S .80) so parameters no
    longer matched `self`'s brightness — they were competing for attention
    instead of `self` reading as senior, per the brightness-tracks-importance
    rule.
  - Nudged hue from 336.6° to 325°, closing the gap to `self` from 73° to
    61.5° while keeping a 20° buffer from orchid decorators — about as close
    as it can get without crowding them.

## [1.0.2]

- Parameters move from red (`#ff8a8e`) to rose (`#fb92bb`). The old red sat 95°
  from `self` in hue while being only 18° from numeric literals — too far from
  the token beside it, too close to the one below it.
- Functions lift to `#8ec5ff` and strings drop to `#8fdc98`, so the names you
  scan for outrank the string literals you don't.
- `variable.classMember.readonly` added, so a constant attribute like
  `settings.API_KEY` is colored by the theme instead of by whichever
  single-modifier rule happened to win the tie.

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
