#!/usr/bin/env python3
"""Render every README image for every theme in package.json: the language
previews, the gallery grid, the workbench mock, the terminal mock and the
palette swatch sheet. The base (dark) theme keeps the plain file names; other
themes get a `-<slug>` suffix.

Every color here is read from the theme files themselves (or, for the palette
labels, the section/description text below), so re-running this after a
palette change keeps every image honest — including `images/palette.png`,
which used to be hand-made and drift out of sync. Tokenizing is done with
Pygments, with a few refinements for the distinctions this theme cares about
(attribute access, `self`, parameters) that a generic lexer doesn't draw on
its own.

    python3 tools/render_preview.py
"""

import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import (CppLexer, CSharpLexer, GoLexer, HtmlLexer,
                             JavaLexer, JavascriptLexer, PhpLexer,
                             PythonLexer, RustLexer, TypeScriptLexer,
                             TsxLexer)
from pygments.token import Token

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = json.loads((ROOT / "package.json").read_text())


def theme_slug(theme_path):
    """Output-name suffix for a theme: "" for the base theme (today's names),
    "-light" for lilac-nights-light-color-theme.json, and so on."""
    stem = Path(theme_path).name.removesuffix(".json").removesuffix("-color-theme")
    rest = stem.removeprefix(MANIFEST["name"]).strip("-")
    return f"-{rest}" if rest else ""


def _token_color(theme, name):
    return next(r["settings"]["foreground"] for r in theme["tokenColors"] if r["name"] == name)


def load(theme_path):
    """Read one theme file and return (C, UI): the color roles used by the
    renderers and the raw workbench color map. Nothing is hardcoded here."""
    theme = json.loads(Path(theme_path).read_text())
    ui, sem = theme["colors"], theme["semanticTokenColors"]
    roles = {
        "bg": ui["editor.background"],
        "chrome": ui["titleBar.activeBackground"],
        "line_hl": ui["editor.lineHighlightBackground"],
        "gutter": ui["editorLineNumber.foreground"],
        "gutter_active": ui["editorLineNumber.activeForeground"],
        "fg": ui["editor.foreground"],
        "border": ui["editorWidget.border"],
        "keyword": _token_color(theme, "Keywords"),
        "self": sem["selfParameter"]["foreground"],
        "attr": sem["property"]["foreground"],
        "func": sem["function"]["foreground"],
        "cls": sem["class"]["foreground"],
        "builtin_type": sem["type.defaultLibrary"]["foreground"],
        "string": sem["string"]["foreground"],
        "number": sem["number"]["foreground"],
        "param": sem["parameter"]["foreground"],
        "decorator": sem["decorator"]["foreground"],
        "operator": sem["operator"]["foreground"],
        "comment": sem["comment"]["foreground"],
        "punct": _token_color(theme, "Punctuation"),
        "tagpunct": _token_color(theme, "Tag punctuation"),
        "error": ui["editorError.foreground"],
    }
    return roles, ui


def manifest_themes():
    """(theme file path, output suffix) for every theme the manifest contributes."""
    return [(ROOT / t["path"], theme_slug(t["path"])) for t in MANIFEST["contributes"]["themes"]]


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
    Token.Keyword.Type: ("builtin_type", "italic"),
    Token.Name: ("fg", "regular"),
    Token.Name.Attribute: ("attr", "italic"),
    Token.Name.Builtin: ("cls", "italic"),
    Token.Name.Builtin.Pseudo: ("self", "italic"),
    Token.Name.Class: ("cls", "bold"),
    Token.Name.Decorator: ("decorator", "regular"),
    Token.Name.Entity: ("number", "regular"),
    Token.Name.Exception: ("cls", "regular"),
    Token.Name.Function: ("func", "regular"),
    Token.Name.Function.Magic: ("func", "italic"),
    Token.Name.Label: ("attr", "regular"),
    Token.Name.Namespace: ("cls", "italic"),
    Token.Name.Other: ("fg", "regular"),
    Token.Name.Parameter: ("param", "regular"),
    Token.Name.Tag: ("keyword", "regular"),
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


def style_for(ttype, C):
    t = ttype
    while t is not None:
        if t in STYLES:
            key, style = STYLES[t]
            return C[key], style
        t = t.parent
    return C["fg"], "regular"


REFINED_LANGS = (JavaLexer, CSharpLexer, PhpLexer, TsxLexer)


def _split_punct(raw):
    """Pygments glues closers such as `))` or `);` into one token, which would
    hide a paren from the depth counter. Split them to one character each."""
    out = []
    for ttype, value in raw:
        if ttype is Token.Punctuation and len(value) > 1 and set(value) <= set("()[]{};,"):
            out.extend((ttype, ch) for ch in value)
        else:
            out.append((ttype, value))
    return out


def _refine_keyword(lang, ttype, value):
    """Keyword fixes: C#/PHP literals are constants, PHP `array` is a type, and
    TSX type references are classes, not built-in types."""
    if lang in (CSharpLexer, PhpLexer):
        if value in ("true", "false", "null"):
            return Token.Keyword.Constant
        if lang is PhpLexer and value == "array":
            return Token.Keyword.Type
    if lang is TsxLexer and ttype is Token.Keyword.Type and value not in TYPE_NAMES:
        return Token.Name.Class
    return ttype


def _jsx_punct(value, nxt_type, in_tag):
    """TSX tag brackets: `<`/`</` before a tag name open a tag, `>`/`/>` close it."""
    if value in ("<", "</") and nxt_type is Token.Name.Tag:
        return True, True
    if in_tag and value in (">", "/>"):
        return False, True
    return in_tag, False


def _refine_name(lang, ttype, value, prev, prev_ident, prev_attr, nxt,
                 in_signature, depth, params):
    """Overrides for Java, C#, PHP and TSX identifiers; None means the generic
    rules in tokenize() apply."""
    if lang is TsxLexer:
        if ttype is Token.Name.Tag and value[:1].isupper():
            return Token.Name.Class
        return ttype if ttype in (Token.Name.Tag, Token.Name.Attribute) else None
    if prev_attr:
        return Token.Name.Decorator  # C# `[Attribute]`
    if lang is PhpLexer:
        return _refine_php(ttype, value, prev, nxt, in_signature, params)
    plain = ttype in (Token.Name, Token.Name.Other)
    # `(Type name,` / `(Type name)`: a declared parameter. A call site has no
    # identifier before its arguments, so it never matches.
    if (plain and depth > 0 and (prev_ident or prev in (">", "]"))
            and nxt in (",", ")", "=") and value not in TYPE_NAMES):
        params.add(value)
        return Token.Name.Parameter
    # `int Limit =` / `Type Name =>`: a declaration site, which the theme paints plain
    if plain and depth == 0 and (prev_ident or prev in (">", "]")) and nxt in ("=", "=>", ";", "{"):
        return Token.Name
    return None


def _refine_php(ttype, value, prev, nxt, in_signature, params):
    if value in ("self", "static", "parent"):
        return Token.Name.Builtin.Pseudo
    if ttype is Token.Name.Builtin and nxt == "(":
        return Token.Name.Function  # count(), min(): built-in functions
    if ttype is Token.Name.Variable:
        if value == "$this":
            return Token.Name.Builtin.Pseudo
        if in_signature:
            params.add(value)
        return Token.Name.Parameter if value in params else None
    if prev in ("->", "?->"):
        return Token.Name.Function if nxt == "(" else Token.Name.Attribute
    if ttype is Token.Name.Other and value[:1].isupper():
        return Token.Name.Class
    return None


def tokenize(code, lexer, C):
    """Pygments tokens, split to one entry per line, with local refinements."""
    raw = [(t, v) for t, v in lex(code, lexer) if v]
    is_html = isinstance(lexer, HtmlLexer)
    lang = type(lexer)
    if lang in REFINED_LANGS:
        raw = _split_punct(raw)
    in_tag = False   # TSX: between `<Tag` and `>`
    bdepth = 0       # brace depth, to end a Java/C#/PHP parameter's scope
    param_bdepth = None
    prev_ident = False  # previous token was an identifier or a built-in type
    prev_attr = False   # previous token was a `[` opening a line (C# attribute)

    # Refinement pass: Pygments emits a bare Token.Name for most identifiers.
    # Decide what each one actually is from its neighbours, the same way the
    # language server would.
    out = []
    prev = ""        # previous non-whitespace token text
    depth = 0        # paren depth
    was_def = False  # the last keyword seen was `def`/`function`
    sig_depth = None  # paren depth of the `def name(...)` signature we're in
    func_groups_left = 0  # Go `func`: receiver + params are separate paren groups
    current_params = set()  # names declared in the current signature, incl. use sites
    bol = True       # this token is the first thing on its line
    for i, (ttype, value) in enumerate(raw):
        nxt, nxt_type = "", None
        for t2, v2 in raw[i + 1:]:
            if v2.strip():
                nxt, nxt_type = v2.strip(), t2
                break

        if lang in REFINED_LANGS:
            ttype = _refine_keyword(lang, ttype, value)

        if value.strip() in ("def", "function", "fn"):
            was_def = True
            current_params = set()
        elif value.strip() == "func":
            # a receiver `func (t Track) Name(...)` is two paren groups; a
            # bare `func Name(...)` or closure `func(...)` is one
            func_groups_left = 2 if nxt == "(" else 1
            current_params = set()

        # brackets inside a string or comment token are text, not structure
        bracket = "" if ttype in Token.Literal or ttype in Token.Comment else value
        if bracket == "{":
            bdepth += 1
        elif bracket == "}":
            bdepth -= 1
            if param_bdepth is not None and bdepth <= param_bdepth:
                current_params.clear()
                param_bdepth = None

        if bracket == "(":
            depth += 1
            if was_def and sig_depth is None:
                sig_depth, was_def = depth, False
            elif func_groups_left > 0 and sig_depth is None:
                sig_depth = depth
        elif bracket == ")":
            if sig_depth == depth:
                sig_depth = None
                if func_groups_left > 0:
                    func_groups_left -= 1
            depth -= 1

        if ttype in Token.Name and ttype not in Token.Name.Decorator:
            in_signature = sig_depth is not None and depth == sig_depth
            plain = ttype in (Token.Name, Token.Name.Other)
            override = None
            if lang in REFINED_LANGS:
                override = _refine_name(lang, ttype, value, prev, prev_ident, prev_attr,
                                        nxt, in_signature, depth, current_params)
            if override is not None:
                ttype = override
                if override is Token.Name.Parameter and param_bdepth is None:
                    param_bdepth = bdepth
            elif value in ("self", "this", "cls"):
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
                current_params.add(value)
            elif nxt == "=" and depth > 0:
                ttype = Token.Name.Parameter
            # a use of a parameter/receiver declared in this signature
            elif plain and value in current_params:
                ttype = Token.Name.Parameter
            # `Title string` / `Tags []string`: a declaration, not a type. The
            # theme paints declaration sites plain and use sites lilac.
            elif plain and (nxt in TYPE_NAMES or nxt == "[") and bol:
                ttype = Token.Name
            elif value[:1].isupper() and not value.isupper() and plain:
                ttype = Token.Name.Class

        if value.strip():
            prev_attr = value.strip() == "[" and bol
            prev_ident = raw[i][0] in Token.Name or raw[i][0] is Token.Keyword.Type
            prev = value.strip()[-1] if value.strip() in ".," else value.strip()
            bol = False
        if "\n" in value:
            bol = True

        color, fstyle = style_for(ttype, C)
        if is_html:
            if value.startswith("<!DOCTYPE"):
                color, fstyle = C["tagpunct"], "italic"
            elif ttype is Token.Punctuation and value in ("<", ">", "/"):
                color, fstyle = C["tagpunct"], "regular"
        if lang is TsxLexer and ttype is Token.Punctuation:
            in_tag, tag_punct = _jsx_punct(value, nxt_type, in_tag)
            if tag_punct:
                color, fstyle = C["tagpunct"], "regular"
        for j, part in enumerate(value.split("\n")):
            out.append((part, color, fstyle, j > 0))
    return out


def fonts(size):
    return {
        "regular": ImageFont.truetype(MENLO, size, index=0),
        "bold": ImageFont.truetype(MENLO, size, index=1),
        "italic": ImageFont.truetype(MENLO, size, index=2),
    }


def _chrome(d, C, width, title, title_h, pad, radius, scale, fill):
    d.rounded_rectangle([0, 0, width - 1, title_h + radius], radius=radius, fill=fill)
    d.rectangle([0, title_h - 1, width - 1, title_h], fill=C["border"])
    r = 6 * scale
    for i, col in enumerate(TRAFFIC):
        cx = pad + i * (r * 2 + 8 * scale) + r
        d.ellipse([cx - r, title_h // 2 - r, cx + r, title_h // 2 + r], fill=col)
    fui = ImageFont.truetype(UISANS, int(12.5 * scale))
    tw = d.textlength(title, font=fui)
    d.text(((width - tw) / 2, (title_h - int(15 * scale)) / 2), title, font=fui, fill=C["gutter"])


def window(code, filename, lexer, out_path, C, size=19, scale=2, highlight=None):
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
    _chrome(d, C, width, filename, title_h, pad, radius, scale, C["chrome"])

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
    for text, color, fstyle, newline in tokenize(code, lexer, C):
        if newline:
            row, x = row + 1, x0
        if text:
            d.text((x, y0 + row * lh), text, font=F[fstyle], fill=color)
            x += F[fstyle].getlength(text)

    img.resize((width // scale, height // scale), Image.LANCZOS).save(out_path)
    return out_path, (width // scale, height // scale)


PKG_VERSION = MANIFEST["version"]


def packaged_files():
    """What `vsce package` would really put in the VSIX, straight from vsce
    (manifest + .vscodeignore), so the terminal mock cannot drift from it."""
    res = subprocess.run(["npx", "--yes", "@vscode/vsce", "ls"], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def terminal_lines(C, UI, files):
    theme_files = {t["path"].removeprefix("./") for t in MANIFEST["contributes"]["themes"]}
    lines = [
        (UI["terminal.ansiGreen"], "~/vscode-themes/lilac-nights "), (C["attr"], "main "),
        (UI["terminal.ansiCyan"], "$ "), (C["fg"], "vsce package\n"),
        (C["gutter"], " INFO  Files included in the VSIX:\n"),
        (C["fg"], f"{MANIFEST['name']}-{PKG_VERSION}.vsix\n"),
    ]
    for n, path in enumerate(files):
        branch = "└─ " if n == len(files) - 1 else "├─ "
        lines += [(C["punct"], branch), (C["cls"] if path in theme_files else C["fg"], path + "\n")]
    lines += [(UI["terminal.ansiGreen"], " DONE  "), (C["fg"], f"Packaged: {len(files)} files\n")]
    return lines


def terminal(out_path, C, UI, files, size=19, scale=2):
    TERMINAL = terminal_lines(C, UI, files)
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
    _chrome(d, C, width, "zsh", title_h, pad, radius, scale, C["chrome"])

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


def palette_items(C, UI):
    return [
        ("PURPLE SPINE", [
            ("Violet", C["keyword"], "keywords, tags"),
            ("Lilac", C["attr"], "properties, attributes"),
            ("Orchid", C["decorator"], "decorators, macros"),
        ]),
        ("ACCENTS", [
            ("Azure", C["func"], "functions, methods"),
            ("Aqua", C["operator"], "operators, regex"),
            ("Honey", C["cls"], "classes, types"),
            ("Sage", C["string"], "strings"),
            ("Rose", C["param"], "parameters"),
            ("Coral", C["number"], "numbers, constants"),
            ("Red", C["error"], "errors"),
        ]),
        ("SURFACES", [
            ("Chrome", C["chrome"], "title bar, tabs"),
            ("Panel", UI["panel.background"], "sidebar, terminal"),
            ("Editor", C["bg"], "editor background"),
            ("Line", C["line_hl"], "current line"),
            ("Select", UI["editor.selectionBackground"], "selection, borders"),
            ("Comment", C["comment"], "comments"),
        ]),
    ]


def _wrap(text, font, max_w):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if font.getlength(trial) > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def palette(out_path, C, UI, scale=2, cols=4):
    PALETTE = palette_items(C, UI)
    pad = 44 * scale
    card_w, gap_x = 150 * scale, 16 * scale
    pitch = card_w + gap_x
    swatch_h = 84 * scale
    header_h = 34 * scale
    name_gap = 16 * scale
    text_lh = 21 * scale
    row_gap = 34 * scale
    section_gap = 40 * scale
    swatch_border = UI["editorWidget.border"]

    f_header = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", int(13.5 * scale))
    f_name = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", int(15.5 * scale))
    f_hex = ImageFont.truetype(MENLO, int(12.5 * scale))
    f_desc = ImageFont.truetype(UISANS, int(12.5 * scale))

    width = pad * 2 + min(cols, max(len(items) for _, items in PALETTE)) * pitch - gap_x

    # First pass: measure total height.
    y = pad
    section_rows = []
    for title, items in PALETTE:
        y += header_h
        rows = [items[i:i + cols] for i in range(0, len(items), cols)]
        for row in rows:
            desc_lines = max(len(_wrap(desc, f_desc, card_w)) for _, _, desc in row)
            row_h = swatch_h + name_gap + text_lh * (2 + desc_lines)
            y += row_h + row_gap
        section_rows.append(rows)
        y += section_gap - row_gap
    height = y + pad - section_gap + row_gap

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width, height], fill=C["bg"])

    y = pad
    for (title, items), rows in zip(PALETTE, section_rows):
        d.text((pad, y), title, font=f_header, fill=C["comment"])
        y += header_h
        for row in rows:
            row_h = 0
            for i, (name, hexval, desc) in enumerate(row):
                x = pad + i * pitch
                d.rounded_rectangle([x, y, x + card_w, y + swatch_h], radius=10 * scale,
                                     fill=hexval, outline=swatch_border, width=scale)
                ty = y + swatch_h + name_gap
                d.text((x, ty), name, font=f_name, fill=C["fg"])
                ty += text_lh
                d.text((x, ty), hexval, font=f_hex, fill=C["comment"])
                ty += text_lh
                for line in _wrap(desc, f_desc, card_w):
                    d.text((x, ty), line, font=f_desc, fill=C["gutter"])
                    ty += text_lh
                row_h = max(row_h, ty - y)
            y += row_h + row_gap
        y += section_gap - row_gap

    img.resize((width // scale, height // scale), Image.LANCZOS).save(out_path)
    return out_path, (width // scale, height // scale)


WB_W, WB_H = 1280, 800
ACT_W, SIDE_W = 48, 240
TAB_H, CRUMB_H, PANEL_H, STATUS_H = 35, 22, 200, 22
EDITOR_X = ACT_W + SIDE_W
PANEL_Y = WB_H - STATUS_H - PANEL_H
ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


class Canvas:
    """Draw in 1x workbench coordinates, rendered at `scale` and shrunk on save."""

    def __init__(self, w, h, scale=2):
        self.w, self.h, self.s = w, h, scale
        self.img = Image.new("RGB", (w * scale, h * scale))
        self.d = ImageDraw.Draw(self.img)

    def rect(self, x0, y0, x1, y1, fill):
        s = self.s
        self.d.rectangle([x0 * s, y0 * s, x1 * s - 1, y1 * s - 1], fill=fill)

    def circle(self, cx, cy, r, fill=None, outline=None):
        s = self.s
        self.d.ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
                       fill=fill, outline=outline, width=s)

    def line(self, pts, fill):
        self.d.line([(x * self.s, y * self.s) for x, y in pts], fill=fill, width=self.s)

    def box(self, x0, y0, x1, y1, color):
        self.d.rectangle([x0 * self.s, y0 * self.s, x1 * self.s, y1 * self.s],
                         outline=color, width=self.s)

    def poly(self, pts, fill):
        self.d.polygon([(x * self.s, y * self.s) for x, y in pts], fill=fill)

    def font(self, size, path=UISANS):
        return ImageFont.truetype(path, int(size * self.s))

    def text(self, x, y, text, font, fill):
        self.d.text((x * self.s, y * self.s), text, font=font, fill=fill)
        return x + font.getlength(text) / self.s

    def save(self, out_path):
        self.img.resize((self.w, self.h), Image.BOX).save(out_path)
        return out_path, (self.w, self.h)


def _glyph(cv, kind, cx, cy, color):
    """Activity-bar icons as simple shapes: files, search, branch, run, blocks."""
    if kind == "files":
        cv.box(cx - 8, cy - 9, cx + 3, cy + 7, color)
        cv.box(cx - 3, cy - 5, cx + 8, cy + 10, color)
    elif kind == "search":
        cv.circle(cx - 2, cy - 2, 7, outline=color)
        cv.line([(cx + 3, cy + 3), (cx + 9, cy + 9)], color)
    elif kind == "branch":
        cv.line([(cx - 5, cy - 7), (cx - 5, cy + 7)], color)
        cv.line([(cx - 5, cy), (cx + 5, cy - 4), (cx + 5, cy - 6)], color)
        for px, py in ((-5, -8), (-5, 8), (5, -8)):
            cv.circle(cx + px, cy + py, 3, fill=color)
    elif kind == "run":
        cv.poly([(cx - 6, cy - 9), (cx - 6, cy + 9), (cx + 8, cy)], color)
    else:
        for dx, dy in ((-9, -9), (1, -9), (-9, 1), (-9 + 10, 1)):
            cv.box(cx + dx, cy + dy, cx + dx + 7, cy + dy + 7, color)


def _activity(cv, UI):
    cv.rect(0, 0, ACT_W, WB_H - STATUS_H, UI["activityBar.background"])
    for i, kind in enumerate(("files", "search", "branch", "run", "blocks")):
        cy = 24 + i * 48
        color = UI["activityBar.foreground"] if i == 0 else UI["activityBar.inactiveForeground"]
        _glyph(cv, kind, 24, cy, color)
    cv.rect(0, 12, 2, 36, UI["activityBar.foreground"])
    cv.circle(36, 24 + 2 * 48 + 12, 8, fill=UI["activityBarBadge.background"])
    cv.text(33, 24 + 2 * 48 + 5, "3", cv.font(10, ARIAL_BOLD), UI["activityBarBadge.foreground"])


# (indent, name, state, is_folder) rows of the explorer mock
EXPLORER = [
    (0, "src", "", True), (1, "models.py", "modified", False), (1, "scan.py", "hover", False),
    (1, "track.py", "selected", False), (1, "broken.py", "error", False),
    (0, "tests", "", True), (0, "README.md", "", False), (0, "pyproject.toml", "", False),
]
ROW_H = 22


def _row_colors(UI, state):
    fg = {"selected": UI["list.activeSelectionForeground"],
          "modified": UI["gitDecoration.modifiedResourceForeground"],
          "error": UI["list.errorForeground"]}.get(state, UI["sideBar.foreground"])
    bg = {"selected": UI["list.activeSelectionBackground"],
          "hover": UI["list.hoverBackground"]}.get(state)
    return fg, bg


def _sidebar(cv, UI):
    cv.rect(ACT_W, 0, EDITOR_X, WB_H - STATUS_H, UI["sideBar.background"])
    cv.rect(ACT_W, 0, EDITOR_X, 34, UI["sideBarSectionHeader.background"])
    cv.text(ACT_W + 16, 11, "EXPLORER", cv.font(11, ARIAL_BOLD), UI["sideBarSectionHeader.foreground"])
    font, mark = cv.font(13), {"modified": "M", "error": "1"}
    for n, (indent, name, state, folder) in enumerate(EXPLORER):
        y = 40 + n * ROW_H
        fg, bg = _row_colors(UI, state)
        if bg:
            cv.rect(ACT_W, y, EDITOR_X, y + ROW_H, bg)
        label = ("v " if name == "src" else "> ") + name if folder else name
        cv.text(ACT_W + 16 + indent * 14 + (0 if folder else 14), y + 3, label, font, fg)
        if state in mark:
            cv.text(EDITOR_X - 18, y + 3, mark[state], font, fg)


# (title, state) of the tab mock: one active, one dirty, one plain
TABS = [("track.py", "active"), ("scan.py", "inactive"), ("models.py", "dirty")]
TAB_W = 130


def _tabs(cv, UI):
    cv.rect(EDITOR_X, 0, WB_W, TAB_H, UI["editorGroupHeader.tabsBackground"])
    font = cv.font(13)
    for n, (title, state) in enumerate(TABS):
        x = EDITOR_X + n * TAB_W
        active = state == "active"
        fg = UI["tab.activeForeground"] if active else UI["tab.inactiveForeground"]
        cv.rect(x, 0, x + TAB_W, TAB_H, UI["tab.activeBackground"] if active else UI["tab.inactiveBackground"])
        cv.rect(x + TAB_W - 1, 0, x + TAB_W, TAB_H, UI["tab.border"])
        if active:
            cv.rect(x, 0, x + TAB_W - 1, 2, UI["tab.activeBorderTop"])
        cv.text(x + 14, 9, title, font, fg)
        if state == "dirty":
            cv.circle(x + TAB_W - 18, TAB_H // 2, 3, fill=fg)
        elif active:
            cv.text(x + TAB_W - 24, 8, "x", font, fg)


def _breadcrumbs(cv, UI, C):
    y = TAB_H
    cv.rect(EDITOR_X, y, WB_W, y + CRUMB_H, C["bg"])
    cv.text(EDITOR_X + 16, y + 4, "src  >  track.py  >  Track  >  duration",
            cv.font(12), UI["breadcrumb.foreground"])


def _editor(cv, C, code, lexer, highlight, size=13, lh=19):
    top = TAB_H + CRUMB_H
    cv.rect(EDITOR_X, top, WB_W, PANEL_Y, C["bg"])
    mono = fonts(size * cv.s)
    cw = mono["regular"].getlength("M") / cv.s
    lines = code.rstrip("\n").split("\n")
    y0 = top + 8
    cv.rect(EDITOR_X, y0 + (highlight - 1) * lh - 2, WB_W, y0 + highlight * lh - 2, C["line_hl"])
    for n in range(1, len(lines) + 1):
        num = str(n)
        color = C["gutter_active"] if n == highlight else C["gutter"]
        cv.text(EDITOR_X + 14 + cw * (3 - len(num)), y0 + (n - 1) * lh, num, mono["regular"], color)
    x0, x, row = EDITOR_X + 14 + cw * 5, EDITOR_X + 14 + cw * 5, 0
    for text, color, fstyle, newline in tokenize(code.rstrip("\n"), lexer, C):
        if newline:
            row, x = row + 1, x0
        if text:
            x = cv.text(x, y0 + row * lh, text, mono[fstyle], color)


def _panel(cv, UI):
    cv.rect(EDITOR_X, PANEL_Y, WB_W, PANEL_Y + PANEL_H, UI["panel.background"])
    cv.rect(EDITOR_X, PANEL_Y, WB_W, PANEL_Y + 1, UI["panel.border"])
    font, x = cv.font(11, ARIAL_BOLD), EDITOR_X + 16
    for title in ("PROBLEMS", "OUTPUT", "TERMINAL"):
        active = title == "TERMINAL"
        fg = UI["panelTitle.activeForeground"] if active else UI["panelTitle.inactiveForeground"]
        x2 = cv.text(x, PANEL_Y + 9, title, font, fg)
        if active:
            cv.rect(x, PANEL_Y + 27, x2, PANEL_Y + 29, UI["panelTitle.activeBorder"])
        x = x2 + 24
    ty = PANEL_Y + 30
    cv.rect(EDITOR_X, ty, WB_W, PANEL_Y + PANEL_H, UI["terminal.background"])
    mono = cv.font(13, MENLO)
    rows = [
        [(UI["terminal.ansiGreen"], "lilac-nights "), (UI["terminal.ansiMagenta"], "main "),
         (UI["terminal.ansiCyan"], "$ "), (UI["terminal.foreground"], "python3 tools/render_preview.py")],
        [(UI["terminal.ansiBrightBlack"], "wrote "), (UI["terminal.ansiBlue"], "images/workbench.png")],
        [(UI["terminal.ansiYellow"], "warning: "), (UI["terminal.foreground"], "mock, not VS Code")],
        [(UI["terminal.ansiRed"], "error: "), (UI["terminal.foreground"], "none")],
        [(UI["terminal.ansiGreen"], "lilac-nights "), (UI["terminal.ansiMagenta"], "main "),
         (UI["terminal.ansiCyan"], "$ ")],
    ]
    for n, row in enumerate(rows):
        x = EDITOR_X + 16
        for color, text in row:
            x = cv.text(x, ty + 8 + n * 19, text, mono, color)
    cv.rect(x, ty + 8 + 4 * 19, x + 8, ty + 8 + 4 * 19 + 15, UI["terminal.foreground"])


def _status(cv, UI):
    y = WB_H - STATUS_H
    cv.rect(0, y, WB_W, WB_H, UI["statusBar.background"])
    cv.rect(0, y, 40, WB_H, UI["statusBarItem.remoteBackground"])
    font = cv.font(12)
    cv.text(10, y + 4, "><", cv.font(12, ARIAL_BOLD), UI["statusBarItem.remoteForeground"])
    x = 52
    for label in ("main", "0 errors, 0 warnings"):
        x = cv.text(x, y + 4, label, font, UI["statusBar.foreground"]) + 16
    x = WB_W - 16
    for label in ("Python", "UTF-8", "Spaces: 4", "Ln 18, Col 1"):
        x -= font.getlength(label) / cv.s
        cv.text(x, y + 4, label, font, UI["statusBar.foreground"])
        x -= 16


def workbench(out_path, C, UI, code, lexer, highlight):
    """A 1280x800 mock of the whole VS Code window, drawn from theme colors only.
    A missing UI key raises KeyError: there are no fallback colors."""
    cv = Canvas(WB_W, WB_H)
    _activity(cv, UI)
    _sidebar(cv, UI)
    _tabs(cv, UI)
    _breadcrumbs(cv, UI, C)
    _editor(cv, C, code, lexer, highlight)
    _panel(cv, UI)
    _status(cv, UI)
    return cv.save(out_path)


def gallery(paths, C, out_path, cols=3, gap=24, pad=32):
    """Grid of the language previews at half scale, on the editor background."""
    imgs = [Image.open(p) for p in paths]
    imgs = [im.resize((im.width // 2, im.height // 2), Image.LANCZOS) for im in imgs]
    rows = math.ceil(len(imgs) / cols)
    col_w = [max(im.width for im in imgs[c::cols]) for c in range(cols)]
    row_h = [max(im.height for im in imgs[r * cols:(r + 1) * cols]) for r in range(rows)]
    width = pad * 2 + sum(col_w) + gap * (cols - 1)
    height = pad * 2 + sum(row_h) + gap * (rows - 1)
    sheet = Image.new("RGBA", (width, height), C["bg"])
    for n, im in enumerate(imgs):
        r, c = divmod(n, cols)
        x = pad + sum(col_w[:c]) + gap * c
        y = pad + sum(row_h[:r]) + gap * r
        sheet.paste(im, (x, y), im)
    sheet.save(out_path)
    return out_path, (width, height)


def pair(left_path, right_path, out_path, bg, gap=16):
    """Dark workbench on the left, light on the right, same height, thin gap."""
    left, right = Image.open(left_path), Image.open(right_path)
    h = min(left.height, right.height)
    left = left.resize((round(left.width * h / left.height), h), Image.LANCZOS)
    right = right.resize((round(right.width * h / right.height), h), Image.LANCZOS)
    sheet = Image.new("RGB", (left.width + gap + right.width, h), bg)
    sheet.paste(left, (0, 0))
    sheet.paste(right, (left.width + gap, 0))
    sheet.save(out_path)
    return out_path, sheet.size


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

    ("html", "tracks.html", HtmlLexer(), 19, """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Track list</title>
  <style>
    .track { color: #b98cff; font-size: 14px; }
  </style>
</head>
<body class="dark" data-theme="lilac">
  <!-- render one row per track -->
  <ul id="tracks">
    <li class="track">
      <a href="/tracks/1">Sample &amp; Test</a>
    </li>
  </ul>
  <script>
    const total = 42;
    console.log(`loaded ${total} tracks`);
  </script>
</body>
</html>
"""),

    ("java", "Library.java", JavaLexer(), 16, """package audio;

import java.util.ArrayList;
import java.util.List;

public class Library {
    private static final int LIMIT = 100;
    private final List<Track> tracks = new ArrayList<>();

    @Override
    public String toString() {
        return "Library(" + tracks.size() + ")";
    }

    /** Adds a track unless the library is full. */
    public boolean add(Track track, int limit) {
        // refuse early, so callers never see a half-filled library
        if (tracks.size() >= Math.min(limit, LIMIT)) {
            return false;
        }
        tracks.add(track);
        return true;
    }
}
"""),

    ("csharp", "Library.cs", CSharpLexer(), 17, """using System.Collections.Generic;
using System.Linq;

namespace Audio;

public sealed class Library
{
    private const int Limit = 100;
    private readonly List<Track> _tracks = new();

    [Obsolete("use Count")]
    public int Size => _tracks.Count;

    public bool Add(Track track, int limit = Limit)
    {
        // refuse early, so callers never see a half-filled library
        if (_tracks.Count >= Math.Min(limit, Limit))
        {
            return false;
        }

        _tracks.Add(track);
        return true;
    }

    public IEnumerable<Track> Longest(int count) =>
        _tracks.OrderByDescending(t => t.Seconds).Take(count);
}
"""),

    ("php", "Library.php", PhpLexer(), 14, """<?php

declare(strict_types=1);

namespace Audio;

final class Library
{
    private const LIMIT = 100;

    /** @var Track[] */
    private array $tracks = [];

    public function add(Track $track, int $limit = self::LIMIT): bool
    {
        // refuse early, so callers never see a half-filled library
        if (count($this->tracks) >= min($limit, self::LIMIT)) {
            return false;
        }

        $this->tracks[] = $track;
        return true;
    }
}
"""),

    ("tsx", "TrackList.tsx", TsxLexer(), 8, """import type { Track } from "./tracks";

interface Props {
  items: Track[];
  onPick?: (track: Track) => void;
}

export function TrackList(props: Props) {
  // newest first, so a partial list still shows the useful half
  const sorted = [...props.items].sort((a, b) => b.seconds - a.seconds);

  return (
    <ul className="tracks">
      {sorted.map((track) => (
        <li key={track.title} onClick={() => props.onPick?.(track)}>
          <Badge count={track.tags?.length ?? 0} />
          {track.title}
        </li>
      ))}
    </ul>
  );
}
"""),
]


def render_theme(theme_path, suffix):
    C, UI = load(theme_path)
    img = ROOT / "images"
    previews = []
    for name, filename, lexer, hl, code in SAMPLES:
        out = img / f"preview-{name}{suffix}.png"
        previews.append(out)
        print(*window(code, filename, lexer, out, C, highlight=hl))
    files = packaged_files()
    print(*terminal(img / f"terminal{suffix}.png", C, UI, files))
    print(*palette(img / f"palette{suffix}.png", C, UI))
    _, filename, lexer, hl, code = SAMPLES[0]
    print(*workbench(img / f"workbench{suffix}.png", C, UI, code, lexer, hl))
    print(*gallery(previews, C, img / f"gallery{suffix}.png"))


if __name__ == "__main__":
    (ROOT / "images").mkdir(exist_ok=True)
    for theme_path, suffix in manifest_themes():
        render_theme(theme_path, suffix)
    img = ROOT / "images"
    if (img / "workbench-light.png").exists():
        dark_bg = load(manifest_themes()[0][0])[0]["bg"]
        print(*pair(img / "workbench.png", img / "workbench-light.png",
                    img / "workbench-pair.png", dark_bg))
