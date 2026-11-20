// Generates the light theme from the dark one: every hex in the dark file goes through
// tools/variants/light.json (map, alpha, overrides). Edit the dark file and light.json
// only, then run this. `--check` writes nothing and exits 1 on any drift or bad config.
import { readFileSync, writeFileSync, existsSync } from "node:fs";

const DARK = "themes/lilac-nights-color-theme.json";
const OUT = "themes/lilac-nights-light-color-theme.json";
const CFG = "tools/variants/light.json";
const HEX = /"(#[0-9a-fA-F]{6})([0-9a-fA-F]{2})?"/g;
const BASE = /^#[0-9a-f]{6}$/;
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

const checkMap = (map, bases) => {
  const seen = new Map();
  for (const b of bases) if (!map[b]) bad(`unmapped dark hex ${b}`);
  for (const [dark, light] of Object.entries(map)) {
    if (!bases.has(dark)) bad(`map key ${dark} is not in the dark theme`);
    if (!BASE.test(light)) bad(`map ${dark} -> ${light} is not a #rrggbb hex`);
    if (seen.has(light)) bad(`map is not injective: ${seen.get(light)} and ${dark} -> ${light}`);
    seen.set(light, dark);
  }
};

const checkExtras = (cfg, theme, full) => {
  for (const [k, v] of Object.entries(cfg.overrides)) {
    if (!k.startsWith("colors.") || !(k.slice(7) in theme.colors)) bad(`unknown override key ${k}`);
    if (!v.why || !/^#[0-9a-f]{6}([0-9a-f]{2})?$/.test(v.value ?? "")) bad(`override ${k} needs a hex value and a why`);
  }
  for (const [k, a] of Object.entries(cfg.alpha)) {
    if (!full.has(k)) bad(`alpha key ${k} is not a colour with alpha in the dark theme`);
    if (!/^[0-9a-f]{2}$/.test(a)) bad(`alpha ${k} -> ${a} is not two hex digits`);
  }
};

const generate = (src, cfg) => {
  let out = src.replace(HEX, (_, b, a = "") => {
    const dark = (b + a).toLowerCase();
    return `"${cfg.map[b.toLowerCase()]}${cfg.alpha[dark] ?? a.toLowerCase()}"`;
  });
  for (const [k, { value }] of Object.entries(cfg.overrides)) {
    const key = k.slice(7).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    out = out.replace(new RegExp(`("${key}"\\s*:\\s*)"#[0-9a-f]{6,8}"`), `$1"${value}"`);
  }
  return out.replace('"name": "Lilac Nights"', '"name": "Lilac Nights Light"').replace('"type": "dark"', '"type": "light"');
};

const src = readFileSync(DARK, "utf8");
const cfg = JSON.parse(readFileSync(CFG, "utf8"));
const { bases, full } = scan(src);
checkMap(cfg.map, bases);
checkExtras(cfg, JSON.parse(src), full);
const out = problems.length ? "" : generate(src, cfg);
if (process.argv.includes("--check") && !problems.length) {
  if (!existsSync(OUT) || readFileSync(OUT, "utf8") !== out) bad(`${OUT} is stale: run node tools/build-variants.mjs`);
}
if (problems.length) {
  problems.forEach((p) => console.error(`build-variants: ${p}`));
  process.exit(1);
}
if (!process.argv.includes("--check")) writeFileSync(OUT, out);
console.log(`${process.argv.includes("--check") ? "checked" : "wrote"} ${OUT}`);
