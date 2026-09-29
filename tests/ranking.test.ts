import test from "node:test";
import assert from "node:assert/strict";
import {
  adjustedCtr,
  calculateFreshness,
  calculatePenalty,
  calculateRanking,
  getTimeDecay,
  isStudentOnly,
  rankItems,
  type RankingConfig,
} from "../scripts/ranking_engine.ts";

const config: RankingConfig = {
  version: 1,
  weights: { freshness: 0.35, freeValue: 0.30, popularity: 0.20, behavior: 0.10, specialOffer: 0.05 },
  timeDecay: [
    { maxDays: 3, multiplier: 1 },
    { maxDays: 7, multiplier: 0.9 },
    { maxDays: 14, multiplier: 0.75 },
    { maxDays: 30, multiplier: 0.55 },
    { maxDays: 60, multiplier: 0.3 },
    { maxDays: 90, multiplier: 0.15 },
    { maxDays: null, multiplier: 0.05 },
  ],
  eventImportance: { model_release: 1, availability_change: 0.95, pricing_change: 0.5, catalog_added: 0.85, default: 0.6 },
  freeMechanismBase: { permanent: 100, daily_quota: 90, weekly_quota: 85, monthly_quota: 80, limited_time_free: 65, open_weights: 70, trial: 50, first_month_promo: 30, not_confirmed: 0 },
  freeQuotaScore: { permanent: 95, daily_quota: 90, weekly_quota: 85, monthly_quota: 80, limited_time_free: 60, open_weights: 70, trial: 50, first_month_promo: 25, not_confirmed: 0 },
  popularityDefault: 50,
  specialOfferScores: { student: 10, developerCredits: 60, startup: 40 },
  penalties: { needsReview: 15, brokenLink: 30, notConfirmed: 20, studentOnly: 20, stale90: 10, stale180: 20, lowInterest30: 5, lowInterest60: 10, lowInterest90: 15 },
  behavior: { neutralScore: 50, confidenceImpressions: 500, recentWeight: 0.7, baselineMultiplierForFullScore: 2 },
  diversity: { topWindow: 10, maxPerProvider: 2, studentOnlyTopWindow: 20, maxStudentOnly: 1 },
};

test("time decay follows the agreed buckets", () => {
  assert.equal(getTimeDecay(2, config), 1);
  assert.equal(getTimeDecay(7, config), 0.9);
  assert.equal(getTimeDecay(20, config), 0.55);
  assert.equal(getTimeDecay(91, config), 0.05);
});

test("small-sample CTR is pulled toward the site average", () => {
  const adjusted = adjustedCtr(2, 2, 0.08, 500);
  assert.ok(adjusted < 0.09, `adjusted CTR should remain close to baseline, got ${adjusted}`);
  assert.ok(adjusted > 0.08);
});

test("content edits do not create freshness", () => {
  const base = { id: "old", date: "2026-06-01", contentUpdatedAt: "2026-09-22" };
  const changed = { ...base, contentUpdatedAt: "2026-09-23" };
  assert.equal(calculateFreshness(base, "2026-09-22", config), calculateFreshness(changed, "2026-09-22", config));
});

test("general free plans with a student add-on are not student-only", () => {
  assert.equal(isStudentOnly({ id: "copilot", type: ["student", "free"], freeMechanism: "monthly_quota" }), false);
  assert.equal(isStudentOnly({ id: "student-plan", type: ["student"], studentEligibility: "school email", freeMechanism: "trial" }), true);
});

test("student-only entries receive an explicit downgrade", () => {
  const result = calculatePenalty(
    { id: "student-plan", type: ["student"], studentEligibility: "school email", freeMechanism: "trial", status: "verified", lastVerifiedAt: "2026-09-22" },
    "2026-09-22",
    undefined,
    config,
  );
  assert.ok(result.score >= 20);
  assert.ok(result.reasons.includes("student_only"));
});

test("broken or unreachable entries receive a strong penalty", () => {
  const result = calculatePenalty(
    { id: "broken", freeMechanism: "permanent", status: "verified", lastVerifiedAt: "2026-09-22", endpointCheck: { verdict: "NETWORK_ERROR" } },
    "2026-09-22",
    undefined,
    config,
  );
  assert.ok(result.score >= 30);
  assert.ok(result.reasons.includes("broken_or_unreachable"));
});

test("a newly added otherwise-equal entry outranks an old one", () => {
  const common = { provider: "Example", freeMechanism: "permanent", status: "verified", lastVerifiedAt: "2026-09-22", cardRequired: "no" };
  const ranked = rankItems([
    { id: "old", order: 1, date: "2026-06-01", ...common },
    { id: "new", order: 2, date: "2026-09-22", ...common },
  ], "2026-09-22", config);
  assert.equal(ranked[0].id, "new");
  assert.ok(ranked[0].rankingScore > ranked[1].rankingScore);
});

test("missing behavior data is neutral instead of zero", () => {
  const result = calculateRanking(
    { id: "x", date: "2026-09-22", freeMechanism: "permanent", lastVerifiedAt: "2026-09-22" },
    "2026-09-22",
    config,
  );
  assert.equal(result.components.behaviorScore, 50);
});

test("diversity keeps one provider from filling the top window", () => {
  const items = [
    { id: "a1", provider: "A", order: 1, date: "2026-09-22", freeMechanism: "permanent", lastVerifiedAt: "2026-09-22" },
    { id: "a2", provider: "A", order: 2, date: "2026-09-22", freeMechanism: "permanent", lastVerifiedAt: "2026-09-22" },
    { id: "a3", provider: "A", order: 3, date: "2026-09-22", freeMechanism: "permanent", lastVerifiedAt: "2026-09-22" },
    { id: "b1", provider: "B", order: 4, date: "2026-09-21", freeMechanism: "permanent", lastVerifiedAt: "2026-09-22" },
  ];
  const ranked = rankItems(items, "2026-09-22", config);
  assert.equal(ranked[2].id, "b1");
  assert.equal(ranked[3].id, "a3");
});
