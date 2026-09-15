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

/**
 * A short question-only chunk is usually a section heading produced by
 * the source-aware document chunker. When such a chunk is retrieved,
 * the actual answer may begin in the following chunks.
 */
const SECTION_HEADING_MAX_LENGTH = 200;

/**
 * Bound section expansion so a malformed source cannot cause an
 * unbounded number of Vectorize lookups or an oversized context.
 */
const MAX_SECTION_CONTINUATIONS = 4;

function isSectionHeadingChunk(chunk: RetrievedChunk): boolean {
  const text = String(chunk.metadata.text ?? "").trim();

  if (!text || text.length > SECTION_HEADING_MAX_LENGTH) {
    return false;
  }

  return (
    text.endsWith("?") ||
    text.endsWith(":")
  );
}

function parseChunkId(
  chunkId: string,
): {
  sourceId: string;
  sequence: number;
} | null {
  const match = /^(.+?)_(\d+)$/.exec(chunkId);

  if (!match) {
    return null;
  }

  return {
    sourceId: match[1],
    sequence: Number(match[2]),
  };
}

async function expandSection(
  chunk: RetrievedChunk,
  env: RetrievalEnv,
): Promise<RetrievedChunk[]> {
  if (!isSectionHeadingChunk(chunk)) {
    return [chunk];
  }

  const chunkId = String(
    chunk.metadata.chunk_id ?? chunk.id,
  );

  const parsed = parseChunkId(chunkId);

  if (!parsed || !Number.isFinite(parsed.sequence)) {
    return [chunk];
  }

  const ids: string[] = [];

  for (
    let offset = 1;
    offset <= MAX_SECTION_CONTINUATIONS;
    offset += 1
  ) {
    ids.push(
      `${parsed.sourceId}_${String(
        parsed.sequence + offset,
      ).padStart(4, "0")}`,
    );
  }

  const vectors = await env.VECTORIZE.getByIds(ids);

  const byId = new Map(
    vectors.map((vector) => [vector.id, vector]),
  );

  const expanded: RetrievedChunk[] = [chunk];

  for (const id of ids) {
    const vector = byId.get(id);

    if (!vector) {
      break;
    }

    const metadata = (vector.metadata ?? {}) as Record<
      string,
      unknown
    >;

    const sourceId = String(
      metadata.source_id ?? "",
    );

    if (sourceId !== parsed.sourceId) {
      break;
    }

    const text = String(
      metadata.text ?? "",
    ).trim();

    if (!text) {
      break;
    }

    /*
     * A new question/heading marks the beginning of the next
     * section. Do not include that section in the current context.
     */
    if (
      expanded.length > 1 &&
      isSectionHeadingChunk({
        id: vector.id,
        score: chunk.score,
        metadata,
      })
    ) {
      break;
    }

    expanded.push({
      id: vector.id,
      score: chunk.score,
      metadata,
    });
  }

  return expanded;
}

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
    throw new Error(
      `Embedding request failed: ${response.status}`,
    );
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
  context: RetrievedChunk[];
}> {
  const vector = await createEmbedding(
    question,
    env,
  );

  const result = await env.VECTORIZE.query(vector, {
    topK: CANDIDATE_K,
    returnMetadata: "all",
  });

  const candidates: RetrievedChunk[] =
    result.matches.map((match) => ({
      id: match.id,
      score: match.score,
      metadata: (match.metadata ?? {}) as Record<
        string,
        unknown
      >,
    }));

  const selected: RetrievedChunk[] = [];
  const seenSources = new Set<string>();

  for (const chunk of candidates) {
    const sourceId = String(
      chunk.metadata.source_id ?? "",
    );

    if (seenSources.has(sourceId)) {
      continue;
    }

    seenSources.add(sourceId);
    selected.push(chunk);

    if (selected.length === TOP_K) {
      break;
    }
  }

    /*
     * Preserve the original source-diverse Top-K retrieval selection.
     * Section expansion is context assembly only and must not change
     * the meaning of the retrieval result.
    */
    const context: RetrievedChunk[] = [];

    for (const chunk of selected) {
      const expanded = await expandSection(
        chunk,
        env,
      );

      context.push(...expanded);
    }

    return {
      candidates,
      selected,
      context,
  };
}