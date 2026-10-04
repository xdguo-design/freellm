const test = require("node:test");
const assert = require("node:assert/strict");
const { addComparedModel, benchmarksComparable, filterModels } = require("./models-discovery.js");

test("region and capability filters combine with AND", () => {
  const models = [
    { id: "a", region: "domestic", capabilities: ["image"] },
    { id: "b", region: "domestic", capabilities: ["text"] },
    { id: "c", region: "international", capabilities: ["image"] },
    { id: "d", region: "both", capabilities: ["image"] },
  ];
  assert.deepEqual(filterModels(models, { region: "domestic", capability: "image" }).map(model => model.id), ["a", "d"]);
});

test("comparison selection refuses a fourth model and keeps the first three", () => {
  const selected = ["a", "b", "c"];
  assert.deepEqual(addComparedModel(selected, "d"), { accepted: false, selected });
});

test("benchmarks compare only when protocol, task, language, sampling settings, and test region match", () => {
  const first = { protocolVersion: "text-stream-v1", taskId: "short-answer-v1", language: "zh", samplingMode: "temperature-0", temperature: "0", region: "domestic" };
  assert.equal(benchmarksComparable(first, { ...first }), true);
  assert.equal(benchmarksComparable(first, { ...first, protocolVersion: "text-stream-v2" }), false);
  assert.equal(benchmarksComparable(first, { ...first, taskId: "long-answer-v1" }), false);
  assert.equal(benchmarksComparable(first, { ...first, language: "en" }), false);
  assert.equal(benchmarksComparable(first, { ...first, samplingMode: "provider-default", temperature: "0.7" }), false);
  assert.equal(benchmarksComparable(first, { ...first, temperature: "0.2" }), false);
  assert.equal(benchmarksComparable(first, { ...first, region: "international" }), false);
});
