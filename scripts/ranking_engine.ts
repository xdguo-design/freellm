export type FreeMechanism =
  | "permanent"
  | "daily_quota"
  | "weekly_quota"
  | "monthly_quota"
  | "trial"
  | "limited_time_free"
  | "first_month_promo"
  | "open_weights"
  | "not_confirmed"
  | string;

export interface RankingWeights {
  freshness: number;
  freeValue: number;
  popularity: number;
  behavior: number;
  specialOffer: number;
}

export interface RankingConfig {
  version: number;
  weights: RankingWeights;
  timeDecay: Array<{ maxDays: number | null; multiplier: number }>;
  eventImportance: Record<string, number>;
  freeMechanismBase: Record<string, number>;
  freeQuotaScore: Record<string, number>;
  popularityDefault: number;
  providerPopularity?: Record<string, number>;
  offerPopularity?: Record<string, number>;
  specialOfferScores?: Record<string, number>;
  manualBoost?: Record<string, number>;
  pinnedIds?: string[];
  penalties: {
    needsReview: number;
    brokenLink: number;
    notConfirmed: number;
    studentOnly: number;
    stale90: number;
    stale180: number;
    lowInterest30: number;
    lowInterest60: number;
    lowInterest90: number;
  };
  behavior: {
    neutralScore: number;
    confidenceImpressions: number;
    recentWeight: number;
    baselineMultiplierForFullScore: number;
  };
  diversity?: {
    topWindow: number;
    maxPerProvider: number;
    studentOnlyTopWindow: number;
    maxStudentOnly: number;
  };
}

export interface RankingBehaviorItem {
  impressions7d?: number;
  clicks7d?: number;
  impressions30d?: number;
  clicks30d?: number;
  lowInterestDays?: number;
}

export interface RankingBehaviorData {
  siteAverageCtr: number;
  items?: Record<string, RankingBehaviorItem>;
}

export interface RankableItem {
  id: string;
  provider?: string;
  order?: number;
  date?: string;
  modelReleaseAt?: string;
  availabilityChangedAt?: string;
  pricingChangedAt?: string;
  contentUpdatedAt?: string;
  lastVerifiedAt?: string;
  freeMechanism?: FreeMechanism;
  type?: string[];
  productType?: string;
  status?: string;
  confidence?: string;
  cardRequired?: string;
  phoneRequired?: string;
  studentEligibility?: string;
  endpointCheck?: { verdict?: string };
  networkCheck?: { region?: string; deadTargets?: string[] };
}

export interface RankingComponents {
  freshnessScore: number;
  freeValueScore: number;
  popularityScore: number;
  behaviorScore: number;
  specialOfferScore: number;
}

export interface RankingResult {
  id: string;
  provider: string;
  sourceOrder: number;
  effectiveEventAt: string | null;
  studentOnly: boolean;
  pinned: boolean;
  manualBoost: number;
  penaltyScore: number;
  penalties: string[];
  components: RankingComponents;
  rankingScore: number;
}

const DAY_MS = 86_400_000;
const GENERAL_FREE_MECHANISMS = new Set([
  "permanent",
  "daily_quota",
  "weekly_quota",
  "monthly_quota",
  "limited_time_free",
  "open_weights",
]);

export function clamp(value: number, minimum = 0, maximum = 100): number {
  return Math.max(minimum, Math.min(maximum, value));
}

export function roundScore(value: number): number {
  return Number(value.toFixed(2));
}

export function parseIsoDate(value?: string | null): Date | null {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function daysBetween(earlier?: string | null, later?: string | null): number {
  const start = parseIsoDate(earlier);
  const end = parseIsoDate(later);
  if (!start || !end) return 0;
  return Math.max(0, Math.floor((end.getTime() - start.getTime()) / DAY_MS));
}

export function getTimeDecay(days: number, config: RankingConfig): number {
  for (const bucket of config.timeDecay) {
    if (bucket.maxDays === null || days <= bucket.maxDays) return bucket.multiplier;
  }
  return 0;
}

export function effectiveEvent(item: RankableItem): { date: string | null; type: string } {
  if (parseIsoDate(item.modelReleaseAt)) return { date: item.modelReleaseAt!, type: "model_release" };
  if (parseIsoDate(item.availabilityChangedAt)) return { date: item.availabilityChangedAt!, type: "availability_change" };
  if (parseIsoDate(item.pricingChangedAt)) return { date: item.pricingChangedAt!, type: "pricing_change" };
  if (parseIsoDate(item.date)) return { date: item.date!, type: "catalog_added" };
  return { date: null, type: "unknown" };
}

export function calculateFreshness(item: RankableItem, asOf: string, config: RankingConfig): number {
  const event = effectiveEvent(item);
  if (!event.date) return 0;
  const days = daysBetween(event.date, asOf);
  const importance = config.eventImportance[event.type] ?? config.eventImportance.default ?? 1;
  return roundScore(clamp(100 * importance * getTimeDecay(days, config)));
}

export function verificationScore(item: RankableItem, asOf: string): number {
  if (!parseIsoDate(item.lastVerifiedAt)) return 25;
  const days = daysBetween(item.lastVerifiedAt, asOf);
  if (days <= 7) return 100;
  if (days <= 30) return 90;
  if (days <= 60) return 70;
  if (days <= 90) return 50;
  if (days <= 180) return 20;
  return 0;
}

export function convenienceScore(item: RankableItem): number {
  let score = 50;
  if (item.cardRequired === "no") score += 20;
  else if (item.cardRequired === "yes") score -= 25;

  if (item.phoneRequired === "no") score += 10;
  else if (item.phoneRequired === "yes") score -= 10;

  const region = item.networkCheck?.region;
  if (region === "both") score += 10;
  else if (region === "none") score -= 30;
  else if (region === "cn" || region === "intl") score += 5;

  const verdict = String(item.endpointCheck?.verdict || "").toUpperCase();
  if (verdict === "OK" || verdict === "ALIVE") score += 5;
  else if (verdict === "NETWORK_ERROR" || verdict === "BROKEN") score -= 30;

  if (item.status === "needs_review") score -= 20;
  return roundScore(clamp(score));
}

export function calculateFreeValue(item: RankableItem, asOf: string, config: RankingConfig): number {
  const mechanism = String(item.freeMechanism || "not_confirmed");
  const availabilityBase = config.freeMechanismBase[mechanism] ?? 0;
  const quota = config.freeQuotaScore[mechanism] ?? availabilityBase;
  const convenience = convenienceScore(item);
  const reliability = verificationScore(item, asOf);
  return roundScore(clamp(
    availabilityBase * 0.40 +
    quota * 0.30 +
    convenience * 0.20 +
    reliability * 0.10,
  ));
}

export function calculatePopularity(item: RankableItem, config: RankingConfig): number {
  const byOffer = config.offerPopularity?.[item.id];
  if (Number.isFinite(byOffer)) return roundScore(clamp(Number(byOffer)));
  const byProvider = item.provider ? config.providerPopularity?.[item.provider] : undefined;
  if (Number.isFinite(byProvider)) return roundScore(clamp(Number(byProvider)));
  return roundScore(clamp(config.popularityDefault));
}

export function adjustedCtr(
  clicks: number,
  impressions: number,
  siteAverageCtr: number,
  confidenceImpressions = 500,
): number {
  if (impressions <= 0) return siteAverageCtr;
  const ctr = Math.max(0, clicks) / impressions;
  const confidence = clamp(impressions / Math.max(1, confidenceImpressions), 0, 1);
  return ctr * confidence + siteAverageCtr * (1 - confidence);
}

function ctrToScore(ctr: number, siteAverageCtr: number, fullScoreMultiplier: number): number {
  if (siteAverageCtr <= 0) return 50;
  return clamp((ctr / (siteAverageCtr * Math.max(1, fullScoreMultiplier))) * 100);
}

export function calculateBehavior(
  item: RankableItem,
  behavior: RankingBehaviorData | undefined,
  config: RankingConfig,
): number {
  const data = behavior?.items?.[item.id];
  if (!behavior || !data) return config.behavior.neutralScore;
  const average = behavior.siteAverageCtr > 0 ? behavior.siteAverageCtr : 0.08;
  const confidence = config.behavior.confidenceImpressions;
  const recentCtr = adjustedCtr(data.clicks7d ?? 0, data.impressions7d ?? 0, average, confidence);
  const monthlyCtr = adjustedCtr(data.clicks30d ?? 0, data.impressions30d ?? 0, average, confidence);
  const recentScore = ctrToScore(recentCtr, average, config.behavior.baselineMultiplierForFullScore);
  const monthlyScore = ctrToScore(monthlyCtr, average, config.behavior.baselineMultiplierForFullScore);
  const recentWeight = clamp(config.behavior.recentWeight, 0, 1);
  return roundScore(recentScore * recentWeight + monthlyScore * (1 - recentWeight));
}

export function isStudentOnly(item: RankableItem): boolean {
  const types = new Set((item.type || []).map(value => String(value).toLowerCase()));
  if (!types.has("student") && !item.studentEligibility) return false;
  return !GENERAL_FREE_MECHANISMS.has(String(item.freeMechanism || "not_confirmed"));
}

export function calculateSpecialOffer(item: RankableItem, config: RankingConfig): number {
  const types = new Set((item.type || []).map(value => String(value).toLowerCase()));
  if (types.has("student") || item.studentEligibility) {
    return config.specialOfferScores?.student ?? 10;
  }
  if (types.has("developer_credits")) return config.specialOfferScores?.developerCredits ?? 60;
  if (types.has("startup")) return config.specialOfferScores?.startup ?? 40;
  return 0;
}

export function calculatePenalty(
  item: RankableItem,
  asOf: string,
  behavior: RankingBehaviorData | undefined,
  config: RankingConfig,
): { score: number; reasons: string[] } {
  let score = 0;
  const reasons: string[] = [];
  const add = (amount: number, reason: string) => {
    if (amount <= 0) return;
    score += amount;
    reasons.push(reason);
  };

  if (item.status === "needs_review") add(config.penalties.needsReview, "needs_review");
  if (item.freeMechanism === "not_confirmed") add(config.penalties.notConfirmed, "free_not_confirmed");
  if (isStudentOnly(item)) add(config.penalties.studentOnly, "student_only");

  const verdict = String(item.endpointCheck?.verdict || "").toUpperCase();
  if (verdict === "NETWORK_ERROR" || verdict === "BROKEN" || item.networkCheck?.region === "none") {
    add(config.penalties.brokenLink, "broken_or_unreachable");
  }
  const deadTargets = item.networkCheck?.deadTargets?.length ?? 0;
  if (deadTargets > 0) add(Math.min(20, deadTargets * 5), "dead_targets");

  if (parseIsoDate(item.lastVerifiedAt)) {
    const age = daysBetween(item.lastVerifiedAt, asOf);
    if (age > 180) add(config.penalties.stale180, "verification_stale_180d");
    else if (age > 90) add(config.penalties.stale90, "verification_stale_90d");
  }

  const behaviorItem = behavior?.items?.[item.id];
  const lowInterestDays = behaviorItem?.lowInterestDays ?? 0;
  if (lowInterestDays >= 90) add(config.penalties.lowInterest90, "low_interest_90d");
  else if (lowInterestDays >= 60) add(config.penalties.lowInterest60, "low_interest_60d");
  else if (lowInterestDays >= 30) add(config.penalties.lowInterest30, "low_interest_30d");
  else if (behavior && (behaviorItem?.impressions30d ?? 0) >= 1000) {
    const average = behavior.siteAverageCtr > 0 ? behavior.siteAverageCtr : 0.08;
    const ctr = adjustedCtr(
      behaviorItem?.clicks30d ?? 0,
      behaviorItem?.impressions30d ?? 0,
      average,
      config.behavior.confidenceImpressions,
    );
    if (ctr < average * 0.3) add(config.penalties.lowInterest30, "low_ctr");
  }

  return { score: roundScore(score), reasons };
}

export function calculateRanking(
  item: RankableItem,
  asOf: string,
  config: RankingConfig,
  behavior?: RankingBehaviorData,
): RankingResult {
  const freshnessScore = calculateFreshness(item, asOf, config);
  const freeValueScore = calculateFreeValue(item, asOf, config);
  const popularityScore = calculatePopularity(item, config);
  const behaviorScore = calculateBehavior(item, behavior, config);
  const specialOfferScore = calculateSpecialOffer(item, config);
  const penalty = calculatePenalty(item, asOf, behavior, config);
  const manualBoost = clamp(config.manualBoost?.[item.id] ?? 0, -10, 10);
  const pinned = Boolean(config.pinnedIds?.includes(item.id));

  const weighted =
    freshnessScore * config.weights.freshness +
    freeValueScore * config.weights.freeValue +
    popularityScore * config.weights.popularity +
    behaviorScore * config.weights.behavior +
    specialOfferScore * config.weights.specialOffer;
  const score = clamp(weighted + manualBoost - penalty.score);
  const event = effectiveEvent(item);

  return {
    id: item.id,
    provider: item.provider || "",
    sourceOrder: Number(item.order || 0),
    effectiveEventAt: event.date,
    studentOnly: isStudentOnly(item),
    pinned,
    manualBoost: roundScore(manualBoost),
    penaltyScore: penalty.score,
    penalties: penalty.reasons,
    components: {
      freshnessScore,
      freeValueScore,
      popularityScore,
      behaviorScore,
      specialOfferScore,
    },
    rankingScore: roundScore(score),
  };
}

function compareResults(a: RankingResult, b: RankingResult): number {
  if (a.pinned !== b.pinned) return Number(b.pinned) - Number(a.pinned);
  if (a.rankingScore !== b.rankingScore) return b.rankingScore - a.rankingScore;
  const eventCompare = String(b.effectiveEventAt || "").localeCompare(String(a.effectiveEventAt || ""));
  if (eventCompare !== 0) return eventCompare;
  if (a.sourceOrder !== b.sourceOrder) return a.sourceOrder - b.sourceOrder;
  return a.id.localeCompare(b.id);
}

export function applyDiversity(results: RankingResult[], config: RankingConfig): RankingResult[] {
  const rules = config.diversity;
  if (!rules) return [...results];

  const accepted: RankingResult[] = [];
  const deferred: RankingResult[] = [];
  const providerCounts = new Map<string, number>();
  let studentOnlyCount = 0;

  for (const result of results) {
    const providerKey = result.provider.trim().toLowerCase() || result.id;
    const providerCount = providerCounts.get(providerKey) ?? 0;
    const insideProviderWindow = accepted.length < rules.topWindow;
    const insideStudentWindow = accepted.length < rules.studentOnlyTopWindow;
    const providerBlocked = insideProviderWindow && providerCount >= rules.maxPerProvider;
    const studentBlocked = insideStudentWindow && result.studentOnly && studentOnlyCount >= rules.maxStudentOnly;
    if (providerBlocked || studentBlocked) {
      deferred.push(result);
      continue;
    }
    accepted.push(result);
    providerCounts.set(providerKey, providerCount + 1);
    if (result.studentOnly) studentOnlyCount += 1;
  }

  return [...accepted, ...deferred];
}

export function rankItems(
  items: RankableItem[],
  asOf: string,
  config: RankingConfig,
  behavior?: RankingBehaviorData,
): RankingResult[] {
  const ranked = items.map(item => calculateRanking(item, asOf, config, behavior)).sort(compareResults);
  return applyDiversity(ranked, config);
}
