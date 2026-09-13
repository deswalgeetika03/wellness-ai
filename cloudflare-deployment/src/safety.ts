export type SafetyRoute =
  | "crisis"
  | "medication_restricted"
  | "eating_disorder_restricted"
  | "normal";

export interface SafetyResult {
  route: SafetyRoute;
  response: string | null;
}

const CRISIS_PATTERNS = [
  /\bsuicid(e|al)\b/i,
  /\bkill(ing)?\s+myself\b/i,
  /\bend(ing)?\s+(it all|my life)\b/i,
  /\bwant(ed|s)?\s+to\s+die\b/i,
  /\bnot\s+worth\s+living\b/i,
  /\bno\s+reason\s+to\s+live\b/i,
  /\bno\s+point\s+in\s+living\b/i,
  /\bbetter\s+off\s+dead\b/i,
  /\bhurt(ing)?\s+myself\b/i,
  /\bself[\s-]?harm(ing)?\b/i,
  /\bcutting\s+myself\b/i,
  /\bcan'?t\s+go\s+on\b/i,
  /\btake\s+my\s+(own\s+)?life\b/i,
  /\bdon'?t\s+want\s+to\s+(be\s+alive|live)\s+anymore\b/i,
  /\bwish\s+i\s+(was|were)n'?t\s+alive\b/i,
  /\boverdose\s+on\s+purpose\b/i,
  /\bbetter\s+off\s+(if\s+i\s+(wasn'?t|weren'?t)\s+(here|around)|without\s+me)\b/i,
];

const CRISIS_RESPONSE =
  "It sounds like you might be going through something really difficult. " +
  "Please reach out to Tele MANAS — India's 24/7 mental health helpline — " +
  "at 14416 or 1-800-891-4416. You can also contact KIRAN at 1800-599-0019. " +
  "You don't have to go through this alone, and support is available right now.";

const ED_CONTEXT_PATTERNS = [
  /\bcalories?\b/i,
  /\bbinge\b/i,
  /\bpurg(e|ing)\b/i,
  /\brestrict(ing)?\s+(food|eating)\b/i,
  /\banorexi/i,
  /\bbulimi/i,
  /\beating\s+disorder\b/i,
  /\bweight\s+loss\b/i,
  /\blose\s+weight\b/i,
  /\bskip(ping)?\s+meals\b/i,
  /\bfast(ing)?\s+for\b/i,
];

const NUMERIC_ASK_PATTERNS = [
  /\bhow\s+many\s+calories\b/i,
  /\bhow\s+much\s+should\s+i\s+(eat|weigh)\b/i,
  /\btarget\s+weight\b/i,
  /\bmeal\s+plan\b/i,
  /\bcalorie\s+(count|target|limit|goal)\b/i,
  /\bideal\s+weight\b/i,
  /\bhow\s+little\s+can\s+i\s+eat\b/i,
];

const EATING_DISORDER_RESTRICTED_RESPONSE =
  "I'm not able to give specific numbers around food, weight, or calories — " +
  "that kind of guidance can do real harm, especially if you're already " +
  "struggling with this. Eating disorders are treatable, and they're not " +
  "about willpower or a lifestyle choice. If this is something you're " +
  "dealing with, please consider reaching out to a doctor or counselor, " +
  "or Tele MANAS at 14416 for support.";

const MEDICATION_PATTERNS = [
  /\bwhat\s+medication\b/i,
  /\bwhat\s+medicine\b/i,
  /\bwhich\s+medication\b/i,
  /\bwhich\s+medicine\b/i,
  /\bwhat\s+drug\b/i,
  /\bwhich\s+drug\b/i,
  /\bmedication\s+for\b/i,
  /\bmedicine\s+for\b/i,
  /\bdrug\s+for\b/i,
  /\bshould\s+i\s+take\s+(?:a\s+)?(?:medication|medicine|drug)\b/i,
  /\bcan\s+i\s+take\s+(?:a\s+)?(?:medication|medicine|drug)\b/i,
  /\bis\s+it\s+(?:okay|safe)\s+to\s+take\s+(?:a\s+)?(?:medication|medicine|drug)\b/i,
  /\bshould\s+i\s+take\s+(?:antidepressants?|anti[-\s]?anxiety\s+(?:medication|meds?|drugs?))\b/i,
  /\bcan\s+i\s+take\s+(?:antidepressants?|anti[-\s]?anxiety\s+(?:medication|meds?|drugs?))\b/i,
  /\bshould\s+i\s+take\s+(?:xanax|alprazolam|prozac|fluoxetine|sertraline|zoloft)\b/i,
  /\bcan\s+i\s+take\s+(?:xanax|alprazolam|prozac|fluoxetine|sertraline|zoloft)\b/i,
  /\bwhat\s+should\s+i\s+take\s+for\s+(?:anxiety|panic\s+attacks?|panic\s+disorder|depression)\b/i,
  /\bwhat\s+can\s+i\s+take\s+for\s+(?:anxiety|panic\s+attacks?|panic\s+disorder|depression)\b/i,
  /\bwhat\s+should\s+i\s+take\s+for\s+(?:stress|sleep|insomnia)\b/i,
  /\bwhat\s+can\s+i\s+take\s+for\s+(?:stress|sleep|insomnia)\b/i,
];

const MEDICATION_RESPONSE =
  "I can't recommend or select a specific medication. " +
  "A qualified healthcare professional can assess your situation " +
  "and discuss appropriate treatment options, including potential " +
  "benefits, risks, and side effects. If your symptoms are severe, " +
  "worsening, or interfering with daily life, consider seeking " +
  "professional support.";

function matchesAny(
  input: string,
  patterns: RegExp[],
): boolean {
  return patterns.some((pattern) => pattern.test(input));
}

function checkCrisis(input: string): boolean {
  return matchesAny(input, CRISIS_PATTERNS);
}

function checkMedication(input: string): boolean {
  return matchesAny(input, MEDICATION_PATTERNS);
}

function checkEatingDisorderNumeric(input: string): boolean {
  if (matchesAny(input, NUMERIC_ASK_PATTERNS)) {
    return true;
  }

  const hasEdContext = matchesAny(input, ED_CONTEXT_PATTERNS);
  const hasDigit = /\d/.test(input);

  return hasEdContext && hasDigit;
}

export function routeSafety(input: string): SafetyResult {
  if (checkCrisis(input)) {
    return {
      route: "crisis",
      response: CRISIS_RESPONSE,
    };
  }

  if (checkMedication(input)) {
    return {
      route: "medication_restricted",
      response: MEDICATION_RESPONSE,
    };
  }

  if (checkEatingDisorderNumeric(input)) {
    return {
      route: "eating_disorder_restricted",
      response: EATING_DISORDER_RESTRICTED_RESPONSE,
    };
  }

  return {
    route: "normal",
    response: null,
  };
}