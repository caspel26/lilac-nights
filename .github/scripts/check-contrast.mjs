// Gates what a theme must keep true beyond "every hex parses": per-role contrast
// floors, the brightness rank order, hue-separated neighbours, same-hue pairs and
// (for variants) hue drift against the dark theme. Roles are looked up by the
// tokenColors rule `name` or the semantic token key, so a renamed rule fails loudly.
// Run with --table to print role, hex and contrast for each theme.
import { readFileSync, readdirSync } from "node:fs";

const TABLE = process.argv.includes("--table");
const TOL = 0.2; // rank order tolerance, in contrast ratio
const FG_MIN = 12;
const FLOOR = 4.5;
const MUTED_FLOOR = 3.0;
const DE_MIN = 0.05; // OKLab distance for hue-separated neighbours
const DL_MIN = 0.06; // OKLCH lightness gap for same-hue pairs
const DRIFT_MAX = 5; // degrees
const MIN_CHROMA = 0.04; // hue is unstable below this

// role -> [kind, key]. kind: "tm" = tokenColors name, "sem" = semantic key, "ui" = colors key.
const ROLES = {
  fg: ["ui", "editor.foreground"],
  types: ["tm", "Classes & types"],
  strings: ["tm", "Strings"],
  properties: ["tm", "Object properties"],
  functions: ["tm", "Functions"],
  numbers: ["tm", "Numbers"],
  parameters: ["tm", "Parameters"],
  keywords: ["tm", "Keywords"],
  comments: ["tm", "Comments"],
  operators: ["tm", "Operators"],
  decorators: ["tm", "Decorators"],
  invalid: ["tm", "Invalid"],
  "builtin types": ["sem", "type.defaultLibrary"],
  "tag punctuation": ["tm", "Tag punctuation"],
  "html doctype": ["tm", "HTML doctype"],
};
const MUTED = ["tag punctuation", "html doctype"];
const RANK = ["fg", "types", "strings", "properties", "functions", "numbers", "parameters", "keywords", "comments"];

const NEIGHBOURS = [
  ["parameters", "keywords"], ["parameters", "numbers"], ["parameters", "decorators"],
  ["numbers", "types"], ["functions", "operators"], ["strings", "operators"],
  ["decorators", "keywords"], ["parameters", "invalid"], ["numbers", "invalid"],
];
const SAME_HUE = [
  ["keywords", "properties", "violet vs lilac are 2.7 degrees apart on purpose; only lightness separates them"],
  ["properties", "fg", "lilac vs near-white lilac-tinted text; only lightness separates them"],
  ["types", "builtin types", "honey vs tan are 2.7 degrees apart on purpose; builtin is dimmer and italic"],
  ["comments", "fg", "comments share the text hue and must stay visibly quieter"],
];

const parse = (hex) => {
  let h = hex.slice(1);
  if (h.length <= 4) h = [...h].map((c) => c + c).join("");
  const n = (i) => parseInt(h.slice(i, i + 2), 16);
  return { rgb: [n(0), n(2), n(4)], a: h.length === 8 ? n(6) / 255 : 1 };
};
const composite = (hex, bg) => {
  const { rgb, a } = parse(hex);
  return rgb.map((c, i) => Math.round(c * a + bg[i] * (1 - a)));
};
const lin = (c) => ((c /= 255) <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const luminance = (rgb) => {
  const [r, g, b] = rgb.map(lin);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a, b) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};
const oklab = (rgb) => {
  const [r, g, b] = rgb.map(lin);
  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
};
const lch = (rgb) => {
  const [L, a, b] = oklab(rgb);
  return { L, C: Math.hypot(a, b), h: ((Math.atan2(b, a) * 180) / Math.PI + 360) % 360 };
};
const deltaE = (x, y) => Math.hypot(...oklab(x).map((v, i) => v - oklab(y)[i]));
const hueGap = (a, b) => Math.abs(((a - b + 540) % 360) - 180);

const resolve = (theme, [kind, key]) => {
  if (kind === "ui") return theme.colors?.[key];
  if (kind === "sem") return theme.semanticTokenColors?.[key]?.foreground;
  const rules = (theme.tokenColors ?? []).filter((r) => r.name === key);
  if (rules.length > 1) throw new Error(`tokenColors name "${key}" is ambiguous (${rules.length} rules)`);
  return rules[0]?.settings?.foreground;
};

const resolveRoles = (theme, file, fail) => {
  const bg = composite(theme.colors["editor.background"], [0, 0, 0]);
  const roles = {};
  for (const [role, spec] of Object.entries(ROLES)) {
    const hex = resolve(theme, spec);
    if (!hex) {
      fail(`${file}: role "${role}" not found (${spec[0]} "${spec[1]}")`);
      continue;
    }
    const rgb = composite(hex, bg);
    roles[role] = { hex, rgb, cr: contrast(rgb, bg), ...lch(rgb) };
  }
  return roles;
};

const checkFloors = (roles, file, fail) => {
  for (const [role, r] of Object.entries(roles)) {
    if (role === "fg") {
      if (r.cr < FG_MIN) fail(`${file}: fg contrast ${r.cr.toFixed(2)} < ${FG_MIN}`);
      continue;
    }
    const min = MUTED.includes(role) ? MUTED_FLOOR : FLOOR;
    if (r.cr < min) fail(`${file}: ${role} ${r.hex} contrast ${r.cr.toFixed(2)} < ${min}`);
  }
};

const checkRank = (roles, file, fail) => {
  const chain = [...RANK, "muted"];
  const val = (name) => (name === "muted" ? Math.max(...MUTED.map((m) => roles[m]?.cr ?? 0)) : roles[name]?.cr);
  for (let i = 0; i < chain.length - 1; i++) {
    const [a, b] = [val(chain[i]), val(chain[i + 1])];
    if (a !== undefined && b !== undefined && b > a + TOL) {
      fail(`${file}: rank order broken: ${chain[i + 1]} (${b.toFixed(2)}) > ${chain[i]} (${a.toFixed(2)}) + ${TOL}`);
    }
  }
};

const checkPairs = (roles, file, fail) => {
  for (const [a, b] of NEIGHBOURS) {
    if (!roles[a] || !roles[b]) continue;
    const de = deltaE(roles[a].rgb, roles[b].rgb);
    if (de < DE_MIN) fail(`${file}: ${a} vs ${b} OKLab dE ${de.toFixed(3)} < ${DE_MIN}`);
  }
  for (const [a, b, why] of SAME_HUE) {
    if (!roles[a] || !roles[b]) continue;
    const dl = Math.abs(roles[a].L - roles[b].L);
    if (dl < DL_MIN) fail(`${file}: ${a} vs ${b} OKLCH dL ${dl.toFixed(3)} < ${DL_MIN} (${why})`);
  }
};

const checkDrift = (roles, dark, file, fail) => {
  for (const [role, r] of Object.entries(roles)) {
    const d = dark[role];
    if (!d || d.C < MIN_CHROMA || r.C < MIN_CHROMA) continue;
    const gap = hueGap(r.h, d.h);
    if (gap > DRIFT_MAX) fail(`${file}: ${role} hue ${r.h.toFixed(0)} drifts ${gap.toFixed(1)} deg from dark ${d.h.toFixed(0)} (max ${DRIFT_MAX})`);
  }
};

let failures = 0;
const fail = (msg) => {
  console.error(msg);
  failures++;
};

const files = readdirSync("themes").filter((f) => f.endsWith(".json")).sort();
const themes = files.map((file) => ({ file, theme: JSON.parse(readFileSync(`themes/${file}`, "utf8")) }));
const darkEntry = themes.find((t) => t.theme.type === "dark");
const darkRoles = darkEntry && resolveRoles(darkEntry.theme, darkEntry.file, fail);

for (const { file, theme } of themes) {
  const roles = file === darkEntry?.file ? darkRoles : resolveRoles(theme, file, fail);
  if (TABLE) {
    console.log(`\n${file}\nrole\thex\tcontrast`);
    for (const [role, r] of Object.entries(roles)) console.log(`${role}\t${r.hex}\t${r.cr.toFixed(2)}`);
  }
  checkFloors(roles, file, fail);
  checkRank(roles, file, fail);
  checkPairs(roles, file, fail);
  if (darkRoles && file !== darkEntry.file) checkDrift(roles, darkRoles, file, fail);
  console.log(`checked ${file}`);
}

if (failures) {
  console.error(`\n${failures} problem(s) found`);
  process.exit(1);
}
console.log("contrast checks passed");
