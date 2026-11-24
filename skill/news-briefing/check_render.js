// Render check: runs the page script against a minimal fake DOM, lists the story tiles it draws, and opens every sheet.
// Usage: node check_render.js out/site/briefing.html   (exit code 1 when something is wrong)
const fs = require("fs");
const html = fs.readFileSync(process.argv[2], "utf8");
const json = html.match(/<script type="application\/json" id="edition">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<\/script>\s*<script>([\s\S]*?)<\/script>/)[1];
class El {
  constructor(tag) { this.tag = tag; this.children = []; this.attrs = {}; this.classList = { contains: c => (this.className || "").split(" ").includes(c) }; this.hidden = false; }
  append(...k) { for (const x of k) this.children.push(x); }
  replaceChildren(...k) { this.children = k; }
  replaceWith() {}
  setAttribute(k, v) { this.attrs[k] = v; }
  closest() { return null; }
  querySelector() { return null; }
  focus() {}
  set textContent(v) { this.children = [String(v)]; }
  get textContent() { return this.children.map(c => typeof c === "string" ? c : c ? c.textContent : String(c)).join(""); }
}
const fake = { app: new El("div"), sheet: new El("div"), edition: new El("script") };
fake.edition.children = [json];
global.document = {
  getElementById: id => fake[id] || null,
  createElement: t => new El(t),
  createElementNS: (ns, t) => new El(t),
  addEventListener() {}, visibilityState: "visible", body: { classList: { add() {}, remove() {} } }, activeElement: null,
};
global.window = { addEventListener() {} };
global.location = { hash: "" };
global.history = { back() {} };
global.claude = { use: async () => null };
global.__fake = fake;

// The checks run inside the same eval as the page script, so they can see its constants.
const checks = `
;(function () {
  const app = __fake.app, sheet = __fake.sheet;
  const stray = [], tiles = [];
  const bad = s => /\\[object |\\bundefined\\b/.test(s);
  (function walk(n) {
    for (const c of n.children) {
      if (typeof c === "string") { if (bad(c)) stray.push(c.slice(0, 80)); }
      else if (c) { if (c.tag === "button" && (c.className || "").includes("tap")) tiles.push(c.attrs["aria-label"]); walk(c); }
    }
  })(app);
  console.log("front page parts:", app.children.length, "| plain-text parts at top level:", app.children.filter(c => typeof c === "string").length);
  console.log("tiles drawn:", tiles.length, "of", ALL.length + (LV ? 1 : 0), "expected");
  tiles.forEach(t => console.log("  -", t));
  let problems = stray.length + (tiles.length === ALL.length + (LV ? 1 : 0) ? 0 : 1);
  if (stray.length) console.log("STRAY TEXT on front page:", stray);
  let opened = 0;
  for (const id of Object.keys(byId)) {
    try {
      openSheet(id); opened++;
      const found = [];
      (function walk(n) { for (const c of n.children) { if (typeof c === "string") { if (bad(c)) found.push(c.slice(0, 60)); } else if (c) walk(c); } })(sheet);
      if (found.length || sheet.textContent.length < 300) { problems++; console.log("  SHEET PROBLEM", id, found, "length", sheet.textContent.length); }
      closeSheet(true);
    } catch (err) { problems++; console.log("  SHEET ERROR", id, err.message); }
  }
  console.log("sheets opened:", opened, "of", Object.keys(byId).length);
  console.log("long view:", LV ? "present, " + LV.body.length + " paragraphs, " + (E.next_questions || []).length + " next questions" : "absent");
  const extras = E.sections.map(s => s.id + ": " + (s.events || []).length + " events, " + (s.rankings || []).length + " rankings").filter(x => !x.includes(": 0 events, 0 rankings"));
  if (extras.length) console.log("section extras:", extras.join("; "));
  console.log(problems ? "RESULT: " + problems + " PROBLEM(S), do not publish" : "RESULT: ok");
  if (problems) process.exitCode = 1;
})();`;
eval(code + checks);
