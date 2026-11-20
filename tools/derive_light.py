#!/usr/bin/env python3
"""Derive a light palette from the dark theme (stdlib only).

Prints the role table and, with --seed, writes tools/variants/light.json (map only,
refuses to overwrite). The output is a DRAFT: hand-tuning in light.json follows and
`node .github/scripts/check-contrast.mjs` is the gate. Hue is held; only L and C move.

Method (DESIGN-v1.1.md section 3):
  syntax/accent hexes  target contrast t = 4.6 + 0.35 * (c_dark - 4.49), rank-preserving
  muted hexes          fixed low targets
  text hexes           fixed high targets (editor.foreground >= 12:1)
  surfaces             explicit OKLCH lightness/chroma ramp, dark order reversed
Each target is met by binary-searching L at the largest in-gamut chroma <= the dark chroma.
"""
import json, math, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DARK = ROOT / "themes/lilac-nights-color-theme.json"
CFG = ROOT / "tools/variants/light.json"
LIGHT_BG, TEXT_HEX = "#faf8fd", "#e6e0f5"
# Contrast targets that are not the generic formula.
FIXED = {"#e6e0f5": 13.0, "#f2ecff": 15.0, "#c3bade": 9.0, "#716490": 3.2, "#5f5479": 2.6}
# Surfaces: dark hex -> (light L, light C). Dark order (low L = recessed) is reversed.
SURF = {"#211a2e": None, "#1a1526": (0.965, 0.008), "#15111f": (0.905, 0.014),
        "#2b2340": (0.930, 0.018), "#372c52": (0.885, 0.030), "#453863": (0.845, 0.042),
        "#3d1f2b": (0.930, 0.030), "#000000": None}
ROLES = {"types": "Classes & types", "strings": "Strings", "operators": "Operators",
         "properties": "Object properties", "functions": "Functions", "numbers": "Numbers",
         "decorators": "Decorators", "builtin types": "type.defaultLibrary",
         "parameters": "Parameters", "keywords": "Keywords", "invalid": "Invalid",
         "comments": "Comments", "tag punctuation": "Tag punctuation"}

lin = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
gam = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
rgb_of = lambda h: [int(h[i:i + 2], 16) for i in (1, 3, 5)]
hex_of = lambda rgb: "#%02x%02x%02x" % tuple(rgb)


def luminance(rgb):
    r, g, b = (lin(c / 255) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def to_oklch(rgb):
    r, g, b = (lin(c / 255) for c in rgb)
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def from_oklch(L, C, h):
    """Return (float rgb, in_gamut)."""
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin_rgb = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
               -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
               -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    ok = all(-1e-4 <= c <= 1 + 1e-4 for c in lin_rgb)
    return [min(1, max(0, c)) for c in lin_rgb], ok


def quantise(L, C, h):
    lin_rgb, _ = from_oklch(L, C, h)
    return [round(255 * gam(c)) for c in lin_rgb]


def max_chroma(L, h, cap):
    if from_oklch(L, cap, h)[1]:
        return cap
    lo, hi = 0.0, cap
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if from_oklch(L, mid, h)[1] else (lo, mid)
    return lo


def solve(target, bg, c_dark, h):
    """Lightest L whose in-gamut colour reaches the contrast target on bg."""
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        rgb = quantise(mid, max_chroma(mid, h, c_dark), h)
        lo, hi = (mid, hi) if contrast(rgb, bg) >= target else (lo, mid)
    return hex_of(quantise(lo, max_chroma(lo, h, c_dark), h))


def derive(dark_hex, dark_bg, light_bg):
    L, C, h = to_oklch(rgb_of(dark_hex))
    if dark_hex == "#000000":
        return dark_hex
    if dark_hex == "#211a2e":
        return LIGHT_BG
    if dark_hex in SURF:
        tl, tc = SURF[dark_hex]
        return hex_of(quantise(tl, max_chroma(tl, h, tc), h))
    target = FIXED.get(dark_hex, 4.6 + 0.35 * (contrast(rgb_of(dark_hex), dark_bg) - 4.49))
    return solve(target, light_bg, C, h)


def dark_roles(theme):
    out = {}
    for role, name in ROLES.items():
        if "." in name:
            out[role] = theme["semanticTokenColors"][name]["foreground"]
        else:
            out[role] = next(r["settings"]["foreground"] for r in theme["tokenColors"] if r.get("name") == name)
    return out


def main():
    src = DARK.read_text()
    theme = json.loads(src)
    bases = sorted(set(m.lower() for m in re.findall(r'"(#[0-9a-fA-F]{6})(?:[0-9a-fA-F]{2})?"', src)))
    dark_bg, light_bg = rgb_of(theme["colors"]["editor.background"]), rgb_of(LIGHT_BG)
    mapping = {h: derive(h, dark_bg, light_bg) for h in bases}
    print(f"{len(bases)} distinct base hexes; injective: {len(set(mapping.values())) == len(mapping)}")
    print("role\tdark\tlight\tcontrast\thue dark->light")
    for role, dh in dark_roles(theme).items():
        lh = mapping[dh]
        hd, hl = to_oklch(rgb_of(dh))[2], to_oklch(rgb_of(lh))[2]
        print(f"{role}\t{dh}\t{lh}\t{contrast(rgb_of(lh), light_bg):.2f}\t{hd:.0f}->{hl:.0f}")
    fg = mapping[TEXT_HEX]
    print(f"fg\t{TEXT_HEX}\t{fg}\t{contrast(rgb_of(fg), light_bg):.2f}")
    if "--seed" in sys.argv:
        if CFG.exists():
            sys.exit(f"{CFG} exists; refusing to overwrite hand-tuned values")
        CFG.parent.mkdir(parents=True, exist_ok=True)
        CFG.write_text(json.dumps({"map": mapping, "alpha": {}, "overrides": {}}, indent=2) + "\n")


if __name__ == "__main__":
    main()
