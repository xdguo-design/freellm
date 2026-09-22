import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  parseIsoDate,
  rankItems,
  type RankableItem,
  type RankingBehaviorData,
  type RankingConfig,
} from "./ranking_engine.ts";

interface CliOptions {
  input: string;
  config: string;
  behavior: string;
  output: string;
  asOf?: string;
  check: boolean;
}

function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = {
    input: "data/offers.json",
    config: "data/ranking-config.json",
    behavior: "data/ranking-behavior.json",
    output: "data/ranked-offers.json",
    check: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--check") options.check = true;
    else if (arg === "--input") options.input = argv[++index];
    else if (arg === "--config") options.config = argv[++index];
    else if (arg === "--behavior") options.behavior = argv[++index];
    else if (arg === "--output") options.output = argv[++index];
    else if (arg === "--as-of") options.asOf = argv[++index];
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return options;
}

function readJson<T>(path: string): { raw: Buffer; value: T } {
  const raw = readFileSync(path);
  return { raw, value: JSON.parse(raw.toString("utf8")) as T };
}

function maxCatalogDate(items: RankableItem[]): string {
  const dates = items
    .flatMap(item => [item.modelReleaseAt, item.availabilityChangedAt, item.pricingChangedAt, item.date, item.lastVerifiedAt])
    .filter((value): value is string => Boolean(parseIsoDate(value)));
  if (!dates.length) throw new Error("No valid catalog date available for ranking asOf");
  return dates.sort().at(-1)!;
}

function digestSources(rawSources: Buffer[], asOf: string): string {
  const hash = createHash("sha256");
  for (const raw of rawSources) {
    hash.update(raw);
    hash.update("\0");
  }
  hash.update(`asOf=${asOf}`);
  return hash.digest("hex");
}

function renderOutput(
  items: RankableItem[],
  config: RankingConfig,
  behavior: RankingBehaviorData,
  asOf: string,
  sourceDigest: string,
): string {
  const ranked = rankItems(items, asOf, config, behavior);
  const payload = {
    version: config.version,
    asOf,
    sourceDigest,
    weights: config.weights,
    items: ranked.map((result, index) => ({ rank: index + 1, ...result })),
  };
  return `${JSON.stringify(payload, null, 2)}\n`;
}

function main(): void {
  const options = parseArgs(process.argv.slice(2));
  const input = readJson<RankableItem[]>(resolve(options.input));
  const config = readJson<RankingConfig>(resolve(options.config));
  const behavior = readJson<RankingBehaviorData>(resolve(options.behavior));
  if (!Array.isArray(input.value)) throw new Error("ranking input must be an array");

  const asOf = options.asOf || maxCatalogDate(input.value);
  if (!parseIsoDate(asOf)) throw new Error(`Invalid --as-of date: ${asOf}`);
  const sourceDigest = digestSources([input.raw, config.raw, behavior.raw], asOf);
  const rendered = renderOutput(input.value, config.value, behavior.value, asOf, sourceDigest);
  const outputPath = resolve(options.output);

  if (options.check) {
    let current = "";
    try {
      current = readFileSync(outputPath, "utf8");
    } catch {
      // handled by comparison below
    }
    if (current !== rendered) {
      console.error(`stale: ${options.output}; run node scripts/generate_ranking.ts`);
      process.exitCode = 1;
      return;
    }
    console.log(`current: ${options.output} (${input.value.length} ranked offers, asOf ${asOf})`);
    return;
  }

  writeFileSync(outputPath, rendered, "utf8");
  console.log(`built: ${options.output} (${input.value.length} ranked offers, asOf ${asOf})`);
}

main();
