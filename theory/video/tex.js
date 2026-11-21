#!/usr/bin/env node
// LaTeX → MathML for the slides. Reads JSON [[tex, display], …] on stdin, writes JSON [mathml, …].
// KaTeX lives outside the repository:  (cd ~/.cache/sd-course/node && npm install katex@0.16.11)
// Chromium renders MathML Core natively; sd.css sets the math font (STIX Two Math, shipped with macOS).
const path = require("path"), os = require("os");
const katex = require(path.join(os.homedir(), ".cache/sd-course/node/node_modules/katex"));
let buf = "";
process.stdin.on("data", d => (buf += d)).on("end", () => {
  const out = JSON.parse(buf).map(([tex, display]) =>
    katex.renderToString(tex, { output: "mathml", displayMode: !!display, throwOnError: true, strict: "ignore" }));
  process.stdout.write(JSON.stringify(out));
});
