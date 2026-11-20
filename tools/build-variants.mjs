// Generates every variant theme from tools/variants/*.json. Each config names its `base`
// ("dark" = the source theme, or another variant's slug); a variant is built from its
// base's in-memory output, so `--check` never depends on a stale file. Edit the dark
// theme and the configs only, then run this. `--check` writes nothing and exits 1 on any
// drift or bad config.
//
// Config: { name, type, base, out, map, alpha, overrides, add }
//   map       base hex -> new hex. Total when the variant's type differs from its base's
//             (a re-theming, so a new base hex fails loudly); partial (unmapped = identity)
//             when the type is the same (a chrome-only variant). Must stay injective.
//   alpha     base hex-with-alpha -> new alpha byte.
//   overrides colors.<key> present in the base -> { value, why }.
//   add       colors.<key> absent from the base -> { value, why }; key must be in ADD_ALLOWED.
import { readFileSync, writeFileSync, existsSync, readdirSync } from "node:fs";

const DARK = "themes/lilac-nights-color-theme.json";
const DIR = "tools/variants";
const HEX = /"(#[0-9a-fA-F]{6})([0-9a-fA-F]{2})?"/g;
const BASE = /^#[0-9a-f]{6}$/;
const VALUE = /^#[0-9a-f]{6}([0-9a-f]{2})?$/;
const CHECK = process.argv.includes("--check");
// Colour ids that exist in VS Code 1.70 (engines.vscode floor): colorRegistry.ts,
// workbench/common/theme.ts and editorColorRegistry.ts at microsoft/vscode release/1.70.
// VS Code silently ignores an unknown id, so a typo in `add` must fail here instead.
const ADD_ALLOWED = [
  "menu.background", "menu.foreground", "menu.border", "menu.selectionBackground",
  "menu.selectionForeground", "menu.selectionBorder", "menu.separatorBackground",
  "notificationToast.border", "notificationCenter.border", "notifications.border",
  "list.focusOutline", "list.focusAndSelectionOutline",
  "editorHoverWidget.statusBarBackground", "listFilterWidget.background",
  "listFilterWidget.shadow", "breadcrumbPicker.background",
  "editorGroup.dropIntoPromptBackground",
  // workbench/common/theme.ts at release/1.70, all in api/references/theme-color.md
  "activityBar.activeBackground", "sideBarSectionHeader.border", "tab.hoverBorder",
];
const problems = [];
const bad = (msg) => problems.push(msg);

const scan = (src) => {
  const bases = new Set();
  const full = new Set();
  for (const [, b, a] of src.matchAll(HEX)) {
    bases.add(b.toLowerCase());
    if (a) full.add((b + a).toLowerCase());
  }
  return { bases, full };
};

const loadConfigs = () =>
  readdirSync(DIR).filter((f) => f.endsWith(".json")).sort().map((f) => {
    const cfg = JSON.parse(readFileSync(`${DIR}/${f}`, "utf8"));
    return { slug: f.slice(0, -5), ...cfg, map: cfg.map ?? {}, alpha: cfg.alpha ?? {}, overrides: cfg.overrides ?? {}, add: cfg.add ?? {} };
  });

// Parents before children; an unknown base or a cycle is an error.
const order = (cfgs) => {
  const done = new Set(["dark"]);
  const sorted = [];
  while (sorted.length < cfgs.length) {
    const next = cfgs.find((c) => !done.has(c.slug) && done.has(c.base));
    if (!next) {
      for (const c of cfgs) if (!done.has(c.slug)) bad(`${c.slug}: base "${c.base}" is unknown or part of a cycle`);
      return null;
    }
    done.add(next.slug);
    sorted.push(next);
  }
  return sorted;
};

const checkMap = (cfg, bases, total) => {
  const seen = new Map();
  if (total) for (const b of bases) if (!cfg.map[b]) bad(`${cfg.slug}: unmapped ${cfg.base} hex ${b}`);
  for (const [from, to] of Object.entries(cfg.map)) {
    if (!bases.has(from)) bad(`${cfg.slug}: map key ${from} is not in ${cfg.base}`);
    if (!BASE.test(to)) bad(`${cfg.slug}: map ${from} -> ${to} is not a #rrggbb hex`);
  }
  for (const b of bases) {
    const to = cfg.map[b] ?? b;
    if (seen.has(to)) bad(`${cfg.slug}: map is not injective: ${seen.get(to)} and ${b} -> ${to}`);
    seen.set(to, b);
  }
};

const checkEntries = (cfg, theme, full) => {
  const entries = (obj, what, ok) => {
    for (const [k, v] of Object.entries(obj)) {
      if (!k.startsWith("colors.") || !ok(k.slice(7))) bad(`${cfg.slug}: ${what} ${k}`);
      if (!v.why || !VALUE.test(v.value ?? "")) bad(`${cfg.slug}: ${k} needs a hex value and a why`);
    }
  };
  entries(cfg.overrides, "unknown override key", (k) => k in theme.colors);
  entries(cfg.add, "add key not allowed or already in the base:", (k) => ADD_ALLOWED.includes(k) && !(k in theme.colors));
  for (const [k, a] of Object.entries(cfg.alpha)) {
    if (!full.has(k)) bad(`${cfg.slug}: alpha key ${k} is not a colour with alpha in ${cfg.base}`);
    if (!/^[0-9a-f]{2}$/.test(a)) bad(`${cfg.slug}: alpha ${k} -> ${a} is not two hex digits`);
  }
};

const insertAdds = (out, adds) => {
  const keys = Object.keys(adds).sort();
  if (!keys.length) return out;
  const anchor = '\n  },\n  "tokenColors"';
  if (!out.includes(anchor)) throw new Error("colors block anchor not found");
  const lines = keys.map((k) => `    "${k.slice(7)}": "${adds[k].value}"`);
  return out.replace(anchor, `,\n${lines.join(",\n")}${anchor}`);
};

const generate = (src, cfg) => {
  let out = src.replace(HEX, (_, b, a = "") => {
    const hex = (b + a).toLowerCase();
    return `"${cfg.map[b.toLowerCase()] ?? b.toLowerCase()}${cfg.alpha[hex] ?? a.toLowerCase()}"`;
  });
  for (const [k, { value }] of Object.entries(cfg.overrides)) {
    const key = k.slice(7).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    out = out.replace(new RegExp(`("${key}"\\s*:\\s*)"#[0-9a-f]{6,8}"`), `$1"${value}"`);
  }
  out = insertAdds(out, cfg.add);
  return out.replace(/"name": "[^"]*"/, `"name": "${cfg.name}"`).replace(/"type": "[a-z]+"/, `"type": "${cfg.type}"`);
};

const cfgs = loadConfigs();
const sorted = order(cfgs);
const built = new Map([["dark", { src: readFileSync(DARK, "utf8"), type: "dark" }]]);
for (const cfg of sorted ?? []) {
  for (const f of ["name", "type", "base", "out"]) if (!cfg[f]) bad(`${cfg.slug}: missing "${f}"`);
  const parent = built.get(cfg.base);
  const before = problems.length;
  const { bases, full } = scan(parent.src);
  checkMap(cfg, bases, cfg.type !== parent.type);
  checkEntries(cfg, JSON.parse(parent.src), full);
  if (problems.length > before) break;
  built.set(cfg.slug, { src: generate(parent.src, cfg), type: cfg.type });
}

const wrote = [];
if (!problems.length) {
  for (const cfg of sorted) {
    const { src: out } = built.get(cfg.slug);
    if (CHECK) {
      if (!existsSync(cfg.out) || readFileSync(cfg.out, "utf8") !== out) bad(`${cfg.out} is stale: run node tools/build-variants.mjs`);
    } else {
      writeFileSync(cfg.out, out);
    }
    wrote.push(cfg.out);
  }
}
if (problems.length) {
  problems.forEach((p) => console.error(`build-variants: ${p}`));
  process.exit(1);
}
for (const f of wrote) console.log(`${CHECK ? "checked" : "wrote"} ${f}`);
