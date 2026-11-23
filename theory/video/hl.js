#!/usr/bin/env node
// Syntax highlighting for code slides. Reads JSON [[code, language], …] on stdin, writes JSON [html, …].
// highlight.js lives outside the repository:  (cd ~/.cache/sd-course/node && npm install highlight.js@11.10.0)
// Colours come from sd.css (.hljs-* classes, a light GitHub-like palette).
const path = require("path"), os = require("os");
const hljs = require(path.join(os.homedir(), ".cache/sd-course/node/node_modules/highlight.js"));
let buf = "";
process.stdin.on("data", d => (buf += d)).on("end", () => {
  const out = JSON.parse(buf).map(([code, lang]) => hljs.highlight(code, { language: lang, ignoreIllegals: true }).value);
  process.stdout.write(JSON.stringify(out));
});
