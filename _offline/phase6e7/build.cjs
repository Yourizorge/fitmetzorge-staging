"use strict";
const fs = require("node:fs"), path = require("node:path"), {publicData} = require("./adapter.cjs");
const root = path.resolve(__dirname, "../..");
const data = publicData();
const serialized = JSON.stringify(data).replace(/</g, "\\u003c");
fs.writeFileSync(path.join(root, "training-review-demo/data.js"), "/* Generated public synthetic fixtures only. */\nwindow.FMZDemoData = " + serialized + ";\n");
console.log(JSON.stringify({synthetic_scenarios: Object.keys(data.seeds).length, public_fixture_bytes: serialized.length}));
