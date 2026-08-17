// Catches the failure mode a theme actually has: a typo'd or truncated hex
// value. VS Code silently ignores those, so the color just goes missing and
// nothing tells you why.
import { readFileSync, readdirSync } from "node:fs";

const HEX = /^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/;
let failures = 0;

const walk = (node, path, onColor) => {
  if (typeof node === "string") return onColor(node, path);
  if (Array.isArray(node)) {
    node.forEach((v, i) => walk(v, `${path}[${i}]`, onColor));
  } else if (node && typeof node === "object") {
    for (const [k, v] of Object.entries(node)) walk(v, `${path}.${k}`, onColor);
  }
};

for (const file of readdirSync("themes").filter((f) => f.endsWith(".json"))) {
  const theme = JSON.parse(readFileSync(`themes/${file}`, "utf8"));

  walk(theme.colors ?? {}, "colors", (value, path) => {
    if (!HEX.test(value)) {
      console.error(`${file}: ${path} is not a hex color: ${JSON.stringify(value)}`);
      failures++;
    }
  });

  const checkForeground = (section, label) =>
    walk(section ?? {}, label, (value, path) => {
      if (!path.endsWith(".foreground") && !path.endsWith(".background")) return;
      if (!HEX.test(value)) {
        console.error(`${file}: ${path} is not a hex color: ${JSON.stringify(value)}`);
        failures++;
      }
    });

  checkForeground(theme.semanticTokenColors, "semanticTokenColors");
  for (const [i, rule] of (theme.tokenColors ?? []).entries()) {
    checkForeground(rule.settings, `tokenColors[${i}].settings`);
    if (rule.scope === undefined) {
      console.error(`${file}: tokenColors[${i}] (${rule.name ?? "unnamed"}) has no scope`);
      failures++;
    }
  }

  console.log(`checked ${file}`);
}

if (failures) {
  console.error(`\n${failures} problem(s) found`);
  process.exit(1);
}
console.log("all colors valid");
