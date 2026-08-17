#!/usr/bin/env python3
"""Render the README preview images.

Colors are read from the theme file itself, so re-running this after a palette
change keeps the screenshots honest.

    python3 tools/render_preview.py
"""

import io
import json
import keyword
import os
import tokenize
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
THEME = json.loads((ROOT / "themes" / "lilac-nights-color-theme.json").read_text())
UI = THEME["colors"]
SEM = THEME["semanticTokenColors"]

C = {
    "bg": UI["editor.background"],
    "chrome": UI["titleBar.activeBackground"],
    "panel": UI["sideBar.background"],
    "line_hl": UI["editor.lineHighlightBackground"],
    "gutter": UI["editorLineNumber.foreground"],
    "gutter_active": UI["editorLineNumber.activeForeground"],
    "fg": UI["editor.foreground"],
    "keyword": "#b98cff",
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
    "border": UI["editorWidget.border"],
}

TRAFFIC = ["#ff5f57", "#febc2e", "#28c840"]
MENLO = "/System/Library/Fonts/Menlo.ttc"
UISANS = "/System/Library/Fonts/Supplemental/Arial.ttf"

SAMPLE = '''from dataclasses import dataclass

from django.db import models
from django.http import HttpRequest


@dataclass(frozen=True)
class SessionSummary:
    """A flattened view of a signing session."""

    external_id: str
    signer_count: int = 0


class Session(models.Model):
    external_session_id = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)

    def summarise(self, request: HttpRequest) -> SessionSummary:
        # only signers who actually opened the envelope
        signers = self.signers.filter(opened=True)
        return SessionSummary(
            external_id=self.external_session_id,
            signer_count=signers.count(),
        )
'''

OPERATORS = {"=", "->", "+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">=", "|", "&", "%", "@="}
PUNCT = {".", ",", ":", "(", ")", "[", "]", "{", "}", ";"}


BUILTIN_TYPES = {"str", "int", "float", "bool", "bytes", "list", "dict", "set", "tuple", "type"}


def analyse(src):
    """Use the AST for the things a token stream can't see on its own.

    Returns the positions of class-body fields (which Pylance reports as
    `variable.classMember`, hence lilac) and the set of imported module names
    (reported as namespaces, hence honey).
    """
    import ast

    tree = ast.parse(src)
    fields, namespaces = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            namespaces.update((a.asname or a.name.split(".")[0]) for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            namespaces.update(node.module.split(".") if node.module else [])
            namespaces.update((a.asname or a.name) for a in node.names)
        elif isinstance(node, ast.ClassDef):
            for stmt in node.body:
                targets = (
                    stmt.targets if isinstance(stmt, ast.Assign)
                    else [stmt.target] if isinstance(stmt, ast.AnnAssign)
                    else []
                )
                for t in targets:
                    if isinstance(t, ast.Name):
                        fields.add((t.lineno, t.col_offset))
    return fields, namespaces


def classify(src):
    """Yield (row, col, text, color, style) for each token."""
    fields, namespaces = analyse(src)
    toks = [
        t
        for t in tokenize.generate_tokens(io.StringIO(src).readline)
        if t.type not in (tokenize.ENCODING, tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                          tokenize.DEDENT, tokenize.ENDMARKER)
    ]
    out = []
    depth = 0            # paren depth
    in_params = False    # inside a `def name(...)` signature
    param_slot = False   # next NAME at depth 1 is a parameter
    in_decorator = False

    for i, t in enumerate(toks):
        prev = toks[i - 1].string if i else ""
        nxt = toks[i + 1].string if i + 1 < len(toks) else ""
        s, ttype = t.string, t.type
        color, style = C["fg"], "regular"

        if ttype == tokenize.COMMENT:
            color, style = C["comment"], "italic"
            in_decorator = False
        elif ttype == tokenize.STRING:
            color = C["string"]
            if s.startswith(('"""', "'''")):
                style = "italic"
        elif ttype == tokenize.NUMBER:
            color = C["number"]
        elif ttype == tokenize.OP:
            if s == "@" and prev in ("", "\n"):
                color, in_decorator = C["decorator"], True
            elif s in PUNCT:
                color = C["punct"]
            elif s in OPERATORS:
                color = C["operator"]
            else:
                color = C["punct"]

            if s == "(":
                depth += 1
                if in_params and depth == 1:
                    param_slot = True
            elif s == ")":
                depth -= 1
                if depth == 0:
                    in_params = param_slot = False
                    in_decorator = False
            elif s == "," and in_params and depth == 1:
                param_slot = True
            elif s in (":", "="):
                param_slot = False
        elif ttype == tokenize.NAME:
            if in_decorator:
                color = C["decorator"]
            elif s in ("self", "cls"):
                color, style = C["attr"], "italic"
            elif keyword.iskeyword(s) or s in ("match", "case"):
                color, style = C["keyword"], "bold"
                if s == "def":
                    in_params = True
            elif (t.start[0], t.start[1]) in fields:
                color = C["attr"]
            elif s in namespaces or s in BUILTIN_TYPES:
                color = C["cls"]
            elif prev == "def":
                color = C["func"]
            elif prev == "class":
                color, style = C["cls"], "bold"
            elif in_params and param_slot and depth == 1:
                color, param_slot = C["param"], False
            elif prev == ".":
                color = C["func"] if nxt == "(" else C["attr"]
            elif nxt == "(":
                color = C["func"]
            elif s[:1].isupper():
                color = C["cls"]
            elif nxt == "=" and depth >= 1:
                color = C["param"]
        else:
            continue

        out.append((t.start[0], t.start[1], s, color, style))
    return out


def fonts(size):
    return {
        "regular": ImageFont.truetype(MENLO, size, index=0),
        "bold": ImageFont.truetype(MENLO, size, index=1),
        "italic": ImageFont.truetype(MENLO, size, index=2),
    }


def window(src, filename, out_path, size=19, scale=2, highlight=None):
    lines = src.rstrip("\n").split("\n")
    F = fonts(size * scale)
    cw = F["regular"].getlength("M")
    lh = int(size * scale * 1.62)

    pad = 18 * scale
    gutter = int(cw * 4)
    title_h = 38 * scale
    body_h = lh * len(lines) + pad * 2
    width = int(pad * 2 + gutter + cw * (max(len(l) for l in lines) + 3))
    height = title_h + body_h

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = 11 * scale

    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=C["bg"])
    d.rounded_rectangle([0, 0, width - 1, title_h + radius], radius=radius, fill=C["chrome"])
    d.rectangle([0, title_h - 1, width - 1, title_h], fill=C["border"])

    r = 6 * scale
    for i, col in enumerate(TRAFFIC):
        cx = pad + i * (r * 2 + 8 * scale) + r
        cy = title_h // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)

    fui = ImageFont.truetype(UISANS, int(12.5 * scale))
    tw = d.textlength(filename, font=fui)
    d.text(((width - tw) / 2, (title_h - int(15 * scale)) / 2), filename, font=fui, fill=C["gutter"])

    y0 = title_h + pad
    if highlight:
        yy = y0 + (highlight - 1) * lh
        d.rectangle([1, yy - 2, width - 2, yy + lh - 2], fill=C["line_hl"])

    for n in range(1, len(lines) + 1):
        active = n == highlight
        num = str(n)
        d.text(
            (pad + gutter - cw - F["regular"].getlength(num), y0 + (n - 1) * lh),
            num,
            font=F["regular"],
            fill=C["gutter_active"] if active else C["gutter"],
        )

    x0 = pad + gutter + cw
    for row, col, text, color, style in classify(src):
        d.text((x0 + col * cw, y0 + (row - 1) * lh), text, font=F[style], fill=color)

    img.resize((width // scale, height // scale), Image.LANCZOS).save(out_path)
    return out_path, (width // scale, height // scale)


TERMINAL = [
    ("#9ce8a4", "~/vscode-themes/lilac-nights "),
    ("#d7b8ff", "main "),
    ("#5fe3d4", "$ "),
    ("#e6e0f5", "vsce package\n"),
    ("#716490", " INFO  Files included in the VSIX:\n"),
    ("#e6e0f5", "lilac-nights-1.0.0.vsix\n"),
    ("#9a8fbd", "├─ "), ("#e6e0f5", "package.json\n"),
    ("#9a8fbd", "├─ "), ("#e6e0f5", "icon.png\n"),
    ("#9a8fbd", "└─ "), ("#ffcc80", "themes/lilac-nights-color-theme.json\n"),
    ("#9ce8a4", " DONE  "), ("#e6e0f5", "Packaged: 8 files, 17.01 KB\n"),
]


def terminal(out_path, size=19, scale=2):
    F = fonts(size * scale)
    cw = F["regular"].getlength("M")
    lh = int(size * scale * 1.62)
    pad = 18 * scale
    title_h = 38 * scale

    flat = "".join(t for _, t in TERMINAL)
    lines = flat.split("\n")
    width = int(pad * 2 + cw * (max(len(l) for l in lines) + 2))
    height = title_h + pad * 2 + lh * len(lines)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = 11 * scale
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=radius, fill=UI["terminal.background"])
    d.rounded_rectangle([0, 0, width - 1, title_h + radius], radius=radius, fill=C["chrome"])
    d.rectangle([0, title_h - 1, width - 1, title_h], fill=C["border"])
    r = 6 * scale
    for i, col in enumerate(TRAFFIC):
        cx = pad + i * (r * 2 + 8 * scale) + r
        d.ellipse([cx - r, title_h // 2 - r, cx + r, title_h // 2 + r], fill=col)
    fui = ImageFont.truetype(UISANS, int(12.5 * scale))
    tw = d.textlength("zsh", font=fui)
    d.text(((width - tw) / 2, (title_h - int(15 * scale)) / 2), "zsh", font=fui, fill=C["gutter"])

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


if __name__ == "__main__":
    os.makedirs(ROOT / "images", exist_ok=True)
    print(*window(SAMPLE, "models.py", ROOT / "images" / "preview.png", highlight=16))
    print(*terminal(ROOT / "images" / "terminal.png"))
