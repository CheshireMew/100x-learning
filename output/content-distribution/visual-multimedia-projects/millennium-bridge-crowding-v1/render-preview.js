const { chromium } = require("playwright");
const { pathToFileURL } = require("url");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const projectDir = __dirname;
const previewDir = path.join(projectDir, "preview");
const framesDir = path.join(previewDir, "frames");
const chrome = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const mode = process.argv.includes("--frames") ? "frames" : "keyframes";
const fromFrameArg = process.argv.find((value) => value.startsWith("--from="));
const toFrameArg = process.argv.find((value) => value.startsWith("--to="));

function digest(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

(async () => {
  fs.mkdirSync(previewDir, { recursive: true });
  const browser = await chromium.launch({ executablePath: chrome, headless: true });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1350 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));

  const url = `${pathToFileURL(path.join(projectDir, "index.html")).href}?capture=1&time=0`;
  await page.goto(url, { waitUntil: "load" });
  await page.evaluate(() => window.editableMedia.ready);
  const canvas = page.locator("#mediaCanvas");

  const bounds = await page.evaluate(() => window.editableMedia.getBounds());
  const required = ["title", "shared-base", "walkers", "metronomes", "caption-card", "source"];
  for (const id of required) {
    if (!bounds[id] || bounds[id].width <= 0 || bounds[id].height <= 0) {
      errors.push(`bounds: invalid ${id}`);
    }
  }

  const original = await page.evaluate(() => window.editableMedia.getState());
  await page.evaluate(() => {
    const state = window.editableMedia.getState();
    state.layers.subtitle = { ...(state.layers.subtitle || {}), content: "可编辑性检查" };
    state.revision += 1;
    window.editableMedia.setState(state);
  });
  const editedSubtitle = await page.locator("[data-editable-id='subtitle']").textContent();
  if (editedSubtitle !== "可编辑性检查") errors.push("editability: subtitle did not update");
  await page.evaluate((state) => window.editableMedia.setState(state), original);

  if (mode === "frames") {
    fs.mkdirSync(framesDir, { recursive: true });
    const fps = 30;
    const durationMs = 12000;
    const total = Math.round(durationMs / 1000 * fps);
    const fromFrame = Math.max(0, Math.min(total, Number(fromFrameArg?.split("=")[1] ?? 0)));
    const toFrame = Math.max(fromFrame, Math.min(total, Number(toFrameArg?.split("=")[1] ?? total)));
    for (let frame = fromFrame; frame <= toFrame; frame += 1) {
      const time = Math.round(frame * 1000 / fps);
      await page.evaluate((value) => window.editableMedia.setTime(value), time);
      await canvas.screenshot({ path: path.join(framesDir, `frame-${String(frame).padStart(4, "0")}.png`) });
    }
    process.stdout.write(`frames=${fromFrame}-${toFrame}\n`);
  } else {
    const times = [0, 1800, 5200, 8200, 10400, 12000];
    for (const time of times) {
      await page.evaluate((value) => window.editableMedia.setTime(value), time);
      await canvas.screenshot({ path: path.join(previewDir, `state-${String(time).padStart(5, "0")}.png`) });
    }
    const first = path.join(previewDir, "determinism-a.png");
    const second = path.join(previewDir, "determinism-b.png");
    await page.evaluate(() => window.editableMedia.setTime(5200));
    await canvas.screenshot({ path: first });
    await page.evaluate(() => window.editableMedia.setTime(5200));
    await canvas.screenshot({ path: second });
    if (digest(first) !== digest(second)) errors.push("determinism: repeated 5200ms captures differ");
  }

  await browser.close();
  if (errors.length) {
    process.stderr.write(`${errors.join("\n")}\n`);
    process.exitCode = 1;
  } else {
    process.stdout.write(`render-ok mode=${mode}\n`);
  }
})();
