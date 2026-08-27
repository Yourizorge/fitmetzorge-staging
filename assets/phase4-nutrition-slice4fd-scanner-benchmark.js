const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const fixtures = ["00011754", "00041560", "00051941", "00094122", "00096072"];

async function run() {
  const edgePath = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  await page.setContent("<!doctype html><html><body></body></html>");
  await page.addScriptTag({ path: path.join(root, "assets", "vendor", "zxing-browser-0.2.1.min.js") });
  const result = await page.evaluate(async (barcodes) => {
    const left = [
      "0001101", "0011001", "0010011", "0111101", "0100011",
      "0110001", "0101111", "0111011", "0110111", "0001011",
    ];
    const right = left.map((pattern) => pattern.replace(/[01]/g, (bit) => bit === "0" ? "1" : "0"));
    const imageFor = (barcode) => {
      const bits = `0000000000${`101${barcode.slice(0, 4).split("").map((digit) => left[Number(digit)]).join("")}01010${barcode.slice(4).split("").map((digit) => right[Number(digit)]).join("")}101`}0000000000`;
      const canvas = document.createElement("canvas");
      canvas.width = bits.length * 4;
      canvas.height = 180;
      const context = canvas.getContext("2d");
      context.fillStyle = "#fff";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.fillStyle = "#000";
      [...bits].forEach((bit, index) => {
        if (bit === "1") context.fillRect(index * 4, 0, 4, 150);
      });
      const image = new Image();
      image.src = canvas.toDataURL("image/png");
      document.body.appendChild(image);
      return image;
    };
    const Reader = window.ZXingBrowser.BrowserMultiFormatOneDReader;
    const formats = window.ZXingBrowser.BarcodeFormat;
    const reader = new Reader(undefined, {
      delayBetweenScanAttempts: 120,
      delayBetweenScanSuccess: 120,
      tryPlayVideoTimeout: 5000,
    });
    reader.possibleFormats = [formats.EAN_13, formats.EAN_8, formats.UPC_A, formats.ITF];
    const images = barcodes.map(imageFor);
    await Promise.all(images.map((image) => image.decode()));

    const durations = [];
    const decoded = [];
    for (let round = 0; round < 20; round += 1) {
      for (let index = 0; index < images.length; index += 1) {
        const started = performance.now();
        const value = await reader.decodeFromImageElement(images[index]);
        durations.push(performance.now() - started);
        decoded.push(value.getText());
      }
    }
    durations.sort((a, b) => a - b);
    const percentile = (fraction) => durations[Math.min(durations.length - 1, Math.ceil(durations.length * fraction) - 1)];
    return {
      samples: durations.length,
      median_ms: Number(percentile(0.5).toFixed(2)),
      p95_ms: Number(percentile(0.95).toFixed(2)),
      max_ms: Number(durations.at(-1).toFixed(2)),
      all_decoded_exactly: decoded.every((value, index) => value === barcodes[index % barcodes.length]),
    };
  }, fixtures);
  await browser.close();
  console.log(JSON.stringify(result));
  if (!result.all_decoded_exactly) process.exit(1);
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
