export interface RetrievalEnv {
  VECTORIZE: VectorizeIndex;
  HF_TOKEN: string;
}

export interface RetrievedChunk {
  id: string;
  score: number;
  metadata: Record<string, unknown>;
}

const HF_EMBEDDING_URL =
  "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction";

const CANDIDATE_K = 10;
const TOP_K = 3;
const MAX_PER_SOURCE = 1;
async function createEmbedding(
  question: string,
  env: RetrievalEnv,
): Promise<number[]> {
  const response = await fetch(HF_EMBEDDING_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.HF_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      inputs: question,
    }),
  });

  if (!response.ok) {
    throw new Error(`Embedding request failed: ${response.status}`);
  }

  const vector = (await response.json()) as number[];

  if (!Array.isArray(vector) || vector.length !== 384) {
    throw new Error(
      `Invalid embedding dimensions: ${
        Array.isArray(vector) ? vector.length : "unknown"
      }`,
    );
  }

  return vector;
}

export async function retrieve(
  question: string,
  env: RetrievalEnv,
): Promise<{
  candidates: RetrievedChunk[];
  selected: RetrievedChunk[];
}> {
  const vector = await createEmbedding(question, env);

  const result = await env.VECTORIZE.query(vector, {
    topK: CANDIDATE_K,
    returnMetadata: "all",
  });

  const candidates: RetrievedChunk[] = result.matches.map((match) => ({
    id: match.id,
    score: match.score,
    metadata: (match.metadata ?? {}) as Record<string, unknown>,
  }));

  const selected: RetrievedChunk[] = [];
  const seenSources = new Set<string>();

  for (const chunk of candidates) {
    const sourceId = String(chunk.metadata.source_id ?? "");

    if (seenSources.has(sourceId)) {
      continue;
    }

    seenSources.add(sourceId);
    selected.push(chunk);

    if (selected.length === TOP_K) {
      break;
    }
  }

  return {
    candidates,
    selected,
  };
}