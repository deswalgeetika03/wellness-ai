export interface GroundingEnv {
  HF_TOKEN: string;
}

export interface GroundingResult {
  status: "pass" | "review";
  score: number;
  checked_sentences: number;
  sentence_scores: number[];
}

const HF_EMBEDDING_URL =
  "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction";

// Initial calibration threshold.
// This is an experiment value, not a final project metric.
const SENTENCE_SIMILARITY_THRESHOLD = 0.55;

function splitSentences(text: string): string[] {
  return text
    .replace(/\r/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

function splitEvidence(text: string): string[] {
  return text
    .replace(/\r/g, " ")
    .split(/\n+/)
    .flatMap((line) => splitSentences(line))
    .map((statement) => statement.trim())
    .filter(Boolean);
}

async function createEmbedding(
  text: string,
  env: GroundingEnv,
): Promise<number[]> {
  const response = await fetch(HF_EMBEDDING_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.HF_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      inputs: text,
    }),
  });

  if (!response.ok) {
    throw new Error(
      `Grounding embedding request failed: ${response.status}`,
    );
  }

  const vector = (await response.json()) as number[];

  if (!Array.isArray(vector) || vector.length !== 384) {
    throw new Error(
      `Invalid grounding embedding dimensions: ${
        Array.isArray(vector) ? vector.length : "unknown"
      }`,
    );
  }

  return vector;
}

function cosineSimilarity(
  a: number[],
  b: number[],
): number {
  let dot = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  if (normA === 0 || normB === 0) {
    return 0;
  }

  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

export async function validateGrounding(
  answer: string,
  verifiedEvidence: string,
  env: GroundingEnv,
): Promise<GroundingResult> {
  if (!answer.trim() || !verifiedEvidence.trim()) {
    return {
      status: "review",
      score: 0,
      checked_sentences: 0,
      sentence_scores: [],
    };
  }

  const answerSentences = splitSentences(answer);
  const evidenceStatements = splitEvidence(verifiedEvidence);

  if (
    answerSentences.length === 0 ||
    evidenceStatements.length === 0
  ) {
    return {
      status: "review",
      score: 0,
      checked_sentences: 0,
      sentence_scores: [],
    };
  }

  // Embed each evidence statement independently.
  const evidenceEmbeddings: number[][] = [];

  for (const statement of evidenceStatements) {
    evidenceEmbeddings.push(
      await createEmbedding(statement, env),
    );
  }

  const sentenceScores: number[] = [];

  // For every answer sentence, compare it against every
  // evidence statement and keep the strongest match.
  for (const sentence of answerSentences) {
    const sentenceEmbedding = await createEmbedding(
      sentence,
      env,
    );

    let bestScore = 0;

    for (const evidenceEmbedding of evidenceEmbeddings) {
      const similarity = cosineSimilarity(
        sentenceEmbedding,
        evidenceEmbedding,
      );

      if (similarity > bestScore) {
        bestScore = similarity;
      }
    }

    sentenceScores.push(bestScore);
  }

  const score =
    sentenceScores.reduce((sum, value) => sum + value, 0) /
    sentenceScores.length;

  const allSentencesSupported = sentenceScores.every(
    (value) => value >= SENTENCE_SIMILARITY_THRESHOLD,
  );

  return {
    status: allSentencesSupported ? "pass" : "review",
    score,
    checked_sentences: answerSentences.length,
    sentence_scores: sentenceScores,
  };
}