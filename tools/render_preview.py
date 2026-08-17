#!/usr/bin/env python3
"""Render the README preview images.

Colors are read from the theme file itself, so re-running this after a palette
change keeps the screenshots honest. Tokenizing is done with Pygments, with a
few refinements for the distinctions this theme cares about (attribute access,
`self`, parameters) that a generic lexer doesn't draw on its own.

    python3 tools/render_preview.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import (CppLexer, GoLexer, JavascriptLexer, PythonLexer,
                             RustLexer, TypeScriptLexer)
from pygments.token import Token

ROOT = Path(__file__).resolve().parent.parent
THEME = json.loads((ROOT / "themes" / "lilac-nights-color-theme.json").read_text())
UI = THEME["colors"]
SEM = THEME["semanticTokenColors"]

C = {
    "bg": UI["editor.background"],
    "chrome": UI["titleBar.activeBackground"],
    "line_hl": UI["editor.lineHighlightBackground"],
    "gutter": UI["editorLineNumber.foreground"],
    "gutter_active": UI["editorLineNumber.activeForeground"],
    "fg": UI["editor.foreground"],
    "border": UI["editorWidget.border"],
    "keyword": "#b98cff",
    "self": SEM["selfParameter"]["foreground"],
    "attr": SEM["property"]["foreground"],
    "func": SEM["function"]["foreground"],
    "cls": SEM["class"]["foreground"],
    "string": SEM["string"]["foreground"],
    "number": SEM["number"]["foreground"],
    "param": SEM["parameter"]["foreground"],
    "decorator": SEM["decorator"]["foreground"],
    "operator": SEM["operator"]["foreground"],
    "comment": SEM["comment"]["foreground"],
    "punct": "#9a8fbd",
}

TRAFFIC = ["#ff5f57", "#febc2e", "#28c840"]
MENLO = "/System/Library/Fonts/Menlo.ttc"
UISANS = "/System/Library/Fonts/Supplemental/Arial.ttf"

# Pygments token -> (color key, style). Looked up by walking a token's parents,
# so Token.Literal.String.Double falls back to the Token.Literal.String entry.
STYLES = {
    Token.Comment: ("comment", "italic"),
    # preprocessor directives, Rust attributes, macros: the theme's orchid role
    Token.Comment.Preproc: ("decorator", "regular"),
    Token.Comment.PreprocFile: ("string", "regular"),
    Token.Keyword: ("keyword", "bold"),
    Token.Keyword.Constant: ("number", "italic"),
    Token.Keyword.Type: ("cls", "regular"),
    Token.Name: ("fg", "regular"),
    Token.Name.Attribute: ("attr", "regular"),
    Token.Name.Builtin: ("cls", "italic"),
    Token.Name.Builtin.Pseudo: ("self", "italic"),
    Token.Name.Class: ("cls", "bold"),
    Token.Name.Decorator: ("decorator", "regular"),
    Token.Name.Exception: ("cls", "regular"),
    Token.Name.Function: ("func", "regular"),
    Token.Name.Function.Magic: ("func", "italic"),
    Token.Name.Label: ("attr", "regular"),
    Token.Name.Namespace: ("cls", "italic"),
    Token.Name.Other: ("fg", "regular"),
    Token.Name.Parameter: ("param", "regular"),
    Token.Name.Tag: ("attr", "regular"),
    Token.Name.Variable: ("fg", "regular"),
    Token.Literal: ("string", "regular"),
    Token.Literal.Number: ("number", "regular"),
    Token.Literal.String: ("string", "regular"),
    Token.Literal.String.Doc: ("string", "italic"),
    Token.Literal.String.Affix: ("keyword", "regular"),
    Token.Literal.String.Interpol: ("operator", "regular"),
    Token.Literal.String.Escape: ("operator", "regular"),
    Token.Operator: ("operator", "regular"),
    Token.Operator.Word: ("keyword", "bold"),
    Token.Punctuation: ("punct", "regular"),
    Token.Text: ("fg", "regular"),
    Token.Error: ("param", "regular"),
}

TYPE_NAMES = {"str", "int", "float", "bool", "bytes", "list", "dict", "set",
              "tuple", "string", "number", "boolean", "void", "unknown", "any",
              # Go and Rust fixed-width primitives
              "int8", "int16", "int32", "int64", "uint", "uint8", "uint16",
              "uint32", "uint64", "float32", "float64", "rune", "byte", "error",
              "f32", "f64", "i8", "i16", "i32", "i64", "u8", "u16", "u32",
              "u64", "usize", "isize", "char", "double", "long", "size_t"}


def style_for(ttype):
    t = ttype
    while t is not None:
        if t in STYLES:
            key, style = STYLES[t]
            return C[key], style
        t = t.parent
    return C["fg"], "regular"


def tokenize(code, lexer):
    """Pygments tokens, split to one entry per line, with local refinements."""
    raw = [(t, v) for t, v in lex(code, lexer) if v]

    # Refinement pass: Pygments emits a bare Token.Name for most identifiers.
    # Decide what each one actually is from its neighbours, the same way the
    # language server would.
    out = []
    prev = ""        # previous non-whitespace token text
    depth = 0        # paren depth
    was_def = False  # the last keyword seen was `def`/`function`
    sig_depth = None  # paren depth of the `def name(...)` signature we're in
    bol = True       # this token is the first thing on its line
    for i, (ttype, value) in enumerate(raw):
        nxt = ""
        for t2, v2 in raw[i + 1:]:
            if v2.strip():
                nxt = v2.strip()
                break

        if value.strip() in ("def", "function"):
            was_def = True

        if value == "(":
            depth += 1
            if was_def and sig_depth is None:
                sig_depth, was_def = depth, False
        elif value == ")":
            if sig_depth == depth:
                sig_depth = None
            depth -= 1

        if ttype in Token.Name and ttype not in Token.Name.Decorator:
            in_signature = sig_depth is not None and depth == sig_depth
            plain = ttype in (Token.Name, Token.Name.Other)
            if value in ("self", "this", "cls"):
                ttype = Token.Name.Builtin.Pseudo
            elif prev == ".":
                ttype = Token.Name.Function if nxt == "(" else Token.Name.Attribute
            elif nxt == "(" and plain:
                ttype = Token.Name.Function
            elif value in TYPE_NAMES:
                ttype = Token.Keyword.Type
            # a parameter in a signature, or a keyword argument at a call site
            elif in_signature and prev in ("(", ",", "*", "**"):
                ttype = Token.Name.Parameter
            elif nxt == "=" and depth > 0:
                ttype = Token.Name.Parameter
            # `Title string` / `Tags []string`: a declaration, not a type. The
            # theme paints declaration sites plain and use sites lilac.
            elif plain and (nxt in TYPE_NAMES or nxt == "[") and bol:
                ttype = Token.Name
            elif value[:1].isupper() and not value.isupper() and plain:
                ttype = Token.Name.Class

        if value.strip():
            prev = value.strip()[-1] if value.strip() in ".," else value.strip()
            bol = False
        if "\n" in value:
            bol = True

        color, fstyle = style_for(ttype)
        for j, part in enumerate(value.split("\n")):
            out.append((part, color, fstyle, j > 0))
    return out


def fonts(size):
    return {
        "regular": ImageFont.truetype(MENLO, size, index=0),
        "bold": ImageFont.truetype(MENLO, size, index=1),
        "italic": ImageFont.truetype(MENLO, size, index=2),
    }


def _chrome(d, width, title, title_h, pad, radius, scale, fill):
    d.rounded_rectangle([0, 0, width - 1, title_h + radius], radius=radius, fill=fill)
    d.rectangle([0, title_h - 1, width - 1, title_h], fill=C["border"])
    r = 6 * scale
    for i, col in enumerate(TRAFFIC):
        cx = pad + i * (r * 2 + 8 * scale) + r
        d.ellipse([cx - r, title_h // 2 - r, cx + r, title_h // 2 + r], fill=col)
    fui = ImageFont.truetype(UISANS, int(12.5 * scale))
    tw = d.textlength(title, font=fui)
    d.text(((width - tw) / 2, (title_h - int(15 * scale)) / 2), title, font=fui, fill=C["gutter"])


def window(code, filename, lexer, out_path, size=19, scale=2, highlight=None):
    code = code.rstrip("\n")
    lines = code.split("\n")
    F = fonts(size * scale)
    cw = F["regular"].getlength("M")
    lh = int(size * scale * 1.62)

    pad = 18 * scale
    gutter = int(cw * 4)
    title_h = 38 * scale
    width = int(pad * 2 + gutter + cw * (max(len(l) for l in lines) + 3))
    height = title_h + lh * len(lines) + pad * 2
    radius = 11 * scale

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=C["bg"])
    _chrome(d, width, filename, title_h, pad, radius, scale, C["chrome"])

    y0 = title_h + pad
    if highlight:
        yy = y0 + (highlight - 1) * lh
        d.rectangle([1, yy - 2, width - 2, yy + lh - 2], fill=C["line_hl"])

    for n in range(1, len(lines) + 1):
        num = str(n)
        d.text(
            (pad + gutter - cw - F["regular"].getlength(num), y0 + (n - 1) * lh),
            num,
            font=F["regular"],
            fill=C["gutter_active"] if n == highlight else C["gutter"],
        )

    x0 = pad + gutter + cw
    x, row = x0, 0
    for text, color, fstyle, newline in tokenize(code, lexer):
        if newline:
            row, x = row + 1, x0
        if text:
            d.text((x, y0 + row * lh), text, font=F[fstyle], fill=color)
            x += F[fstyle].getlength(text)

    img.resize((width // scale, height // scale), Image.LANCZOS).save(out_path)
    return out_path, (width // scale, height // scale)


TERMINAL = [
    ("#9ce8a4", "~/vscode-themes/lilac-nights "), ("#d7b8ff", "main "),
    ("#5fe3d4", "$ "), ("#e6e0f5", "vsce package\n"),
    ("#716490", " INFO  Files included in the VSIX:\n"),
    ("#e6e0f5", "lilac-nights-1.0.1.vsix\n"),
    ("#9a8fbd", "├─ "), ("#e6e0f5", "package.json\n"),
    ("#9a8fbd", "├─ "), ("#e6e0f5", "icon.png\n"),
    ("#9a8fbd", "└─ "), ("#ffcc80", "themes/lilac-nights-color-theme.json\n"),
    ("#9ce8a4", " DONE  "), ("#e6e0f5", "Packaged: 8 files, 25.06 KB\n"),
]


def terminal(out_path, size=19, scale=2):
    F = fonts(size * scale)
    cw = F["regular"].getlength("M")
    lh = int(size * scale * 1.62)
    pad, title_h = 18 * scale, 38 * scale
    lines = "".join(t for _, t in TERMINAL).split("\n")
    width = int(pad * 2 + cw * (max(len(l) for l in lines) + 2))
    height = title_h + pad * 2 + lh * len(lines)
    radius = 11 * scale

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=UI["terminal.background"])
    _chrome(d, width, "zsh", title_h, pad, radius, scale, C["chrome"])

    x, y = pad, title_h + pad
    for color, text in TERMINAL:
        for j, part in enumerate(text.split("\n")):
            if j:
                x, y = pad, y + lh
            if part:
                d.text((x, y), part, font=F["regular"], fill=color)
                x += F["regular"].getlength(part)

    img.resize((width // scale, height // scale), Image.LANCZOS).save(out_path)
    return out_path, (width // scale, height // scale)


SAMPLES = [
    ("python", "track.py", PythonLexer(), 18, """from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Track:
    \"\"\"A single audio track, as read from disk.\"\"\"

    title: str
    seconds: float
    tags: list[str] = field(default_factory=list)

    @property
    def duration(self) -> str:
        minutes, rest = divmod(int(self.seconds), 60)
        return f"{minutes}:{rest:02d}"


async def scan(root: Path, *, limit: int = 100) -> list[Track]:
    # newest first, so a partial scan still returns the useful half
    found = sorted(root.rglob("*.flac"), key=lambda p: -p.stat().st_mtime)
    tracks = [Track(title=p.stem, seconds=0.0) for p in found[:limit]]
    await asyncio.sleep(0)
    return tracks
"""),

    ("typescript", "tracks.ts", TypeScriptLexer(), 13, """import { readFile } from "node:fs/promises";

export interface Track {
  title: string;
  seconds: number;
  tags?: string[];
}

const FORMATS = new Set(["flac", "wav", "aiff"]);

export async function loadTracks(path: string): Promise<Track[]> {
  // one read, then everything else happens in memory
  const raw = await readFile(path, "utf8");
  const parsed = JSON.parse(raw) as Track[];

  return parsed
    .filter((track) => FORMATS.has(track.title.split(".").pop() ?? ""))
    .map((track) => ({ ...track, tags: track.tags ?? [] }));
}
"""),

    ("javascript", "tracks.js", JavascriptLexer(), 11, """import { readFile } from "node:fs/promises";

const FORMATS = new Set(["flac", "wav", "aiff"]);

export async function loadTracks(path) {
  // one read, then everything else happens in memory
  const raw = await readFile(path, "utf8");
  const tracks = JSON.parse(raw);

  return tracks
    .filter((track) => FORMATS.has(track.format))
    .map((track) => ({ ...track, tags: track.tags ?? [] }))
    .sort((a, b) => b.seconds - a.seconds);
}
"""),

    ("go", "track.go", GoLexer(), 19, """package track

import (
    "encoding/json"
    "fmt"
    "os"
    "sort"
)

// Track is a single audio file on disk.
type Track struct {
    Title   string   `json:"title"`
    Seconds float64  `json:"seconds"`
    Tags    []string `json:"tags,omitempty"`
}

// Duration renders the track length as m:ss.
func (t Track) Duration() string {
    return fmt.Sprintf("%d:%02d", int(t.Seconds)/60, int(t.Seconds)%60)
}

func (t Track) Tagged(tag string) bool {
    for _, candidate := range t.Tags {
        if candidate == tag {
            return true
        }
    }
    return false
}

func Load(path string) ([]Track, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("read %s: %w", path, err)
    }

    var tracks []Track
    if err := json.Unmarshal(raw, &tracks); err != nil {
        return nil, err
    }

    sort.Slice(tracks, func(i, j int) bool {
        return tracks[i].Seconds > tracks[j].Seconds
    })
    return tracks, nil
}
"""),

    ("rust", "track.rs", RustLexer(), 16, """use std::path::Path;

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Track {
    pub title: String,
    pub seconds: f64,
    #[serde(default)]
    pub tags: Vec<String>,
}

impl Track {
    /// Human-readable duration, as `m:ss`.
    pub fn duration(&self) -> String {
        let minutes = (self.seconds / 60.0).floor() as u32;
        format!("{}:{:02}", minutes, self.seconds as u32 % 60)
    }
}

pub fn load(path: &Path) -> anyhow::Result<Vec<Track>> {
    let raw = std::fs::read_to_string(path)?;
    let tracks: Vec<Track> = serde_json::from_str(&raw)?;
    Ok(tracks)
}
"""),

    ("cpp", "track.cpp", CppLexer(), 19, """#include <algorithm>
#include <string>
#include <vector>

namespace audio {

struct Track {
    std::string title;
    double seconds = 0.0;
    std::vector<std::string> tags;

    [[nodiscard]] int minutes() const noexcept {
        return static_cast<int>(seconds) / 60;
    }
};

std::vector<Track> longest(std::vector<Track> tracks, std::size_t limit) {
    // longest first, then keep only what the caller asked for
    std::sort(tracks.begin(), tracks.end(), [](const Track& a, const Track& b) {
        return a.seconds > b.seconds;
    });
    tracks.resize(std::min(limit, tracks.size()));
    return tracks;
}

}  // namespace audio
"""),
]


if __name__ == "__main__":
    (ROOT / "images").mkdir(exist_ok=True)
    for name, filename, lexer, hl, code in SAMPLES:
        out = ROOT / "images" / f"preview-{name}.png"
        print(*window(code, filename, lexer, out, highlight=hl))
    print(*terminal(ROOT / "images" / "terminal.png"))
