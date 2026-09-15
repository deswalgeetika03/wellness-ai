export interface EvidenceEnv {
  AI: Ai;
}

export interface EvidenceChunk {
  id: string;
  score: number;
  metadata: Record<string, unknown>;
}

export const EVIDENCE_DISTANCE_THRESHOLD = 1.25;

const EVIDENCE_EXTRACTION_PROMPT = `You are an evidence extraction assistant.

Your task is to extract only factual information that is explicitly stated in the provided Wellness knowledge.

Rules:
- Use ONLY the provided Wellness knowledge.
- Copy or closely preserve the meaning of information explicitly stated in the knowledge.
- Do not use pretrained knowledge.
- Do not infer missing information.
- Do not add examples, symptoms, causes, treatments, definitions, durations, numbers, or recommendations that are not explicitly stated.
- If the knowledge does not contain information relevant to the question, output exactly:
  NO_SUPPORTED_EVIDENCE
- Keep the extracted evidence short and factual.
- Do not answer the user's question.
- Do not provide explanations beyond the extracted evidence.

Wellness knowledge:
{context}

Question:
{question}
`;

function buildContext(chunks: EvidenceChunk[]): string {
  return chunks
    .map((chunk) => {
      const organization = String(
        chunk.metadata.organization ?? "Unknown organization",
      );

      const title = String(
        chunk.metadata.title ?? "Untitled source",
      );

      const text = String(chunk.metadata.text ?? "");

      return `[${organization} - ${title}]\n${text}`;
    })
    .join("\n\n");
}

/**
 * Extract a small deterministic evidence fallback from retrieved text.
 *
 * This is intentionally conservative:
 * - It never generates new factual content.
 * - It only returns sentences already present in the retrieved chunks.
 * - It requires overlap between meaningful question terms and the sentence.
 */
function normalizeEvidenceTerm(term: string): string {
  let normalized = term.toLowerCase();

  if (normalized.endsWith("ies") && normalized.length > 5) {
    normalized = `${normalized.slice(0, -3)}y`;
  } else if (
    normalized.endsWith("ing") &&
    normalized.length > 6
  ) {
    normalized = normalized.slice(0, -3);
  } else if (
    normalized.endsWith("ed") &&
    normalized.length > 5
  ) {
    normalized = normalized.slice(0, -2);
  } else if (
    normalized.endsWith("es") &&
    normalized.length > 5
  ) {
    normalized = normalized.slice(0, -2);
  } else if (
    normalized.endsWith("s") &&
    normalized.length > 4
  ) {
    normalized = normalized.slice(0, -1);
  }

  return normalized;
}

function extractDeterministicEvidence(
  question: string,
  chunks: EvidenceChunk[],
): string {
  const stopWords = new Set([
    "a",
    "an",
    "and",
    "are",
    "be",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
    "with",
    "you",
    "your",
  ]);

  const questionTerms = question
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(
      (term) =>
        term.length >= 4 &&
        !stopWords.has(term),
    )
    .map(normalizeEvidenceTerm);

  if (questionTerms.length === 0) {
    return "NO_SUPPORTED_EVIDENCE";
  }

  const candidates: Array<{
    sentence: string;
    score: number;
    chunkIndex: number;
    overlapCount: number;
  }> = [];

  chunks.forEach((chunk, chunkIndex) => {
    const text = String(chunk.metadata.text ?? "").trim();

    if (!text) {
      return;
    }

    const sentences = text
      .split(/(?<=[.!?])\s+|\n+/)
      .map((sentence) => sentence.trim())
      .filter(Boolean);

    const chunkTerms = new Set(
      sentences
        .flatMap((sentence) =>
          sentence
            .toLowerCase()
            .replace(/[^a-z0-9\s]/g, " ")
            .split(/\s+/)
            .filter(
              (term) =>
                term.length >= 4 &&
                !stopWords.has(term),
            )
            .map(normalizeEvidenceTerm),
        ),
    );

    const chunkOverlapCount = questionTerms.filter((term) =>
      chunkTerms.has(term),
    ).length;

    if (chunkOverlapCount === 0) {
      return;
    }

    sentences.forEach((sentence) => {
      const sentenceTerms = new Set(
        sentence
          .toLowerCase()
          .replace(/[^a-z0-9\s]/g, " ")
          .split(/\s+/)
          .filter(
            (term) =>
              term.length >= 4 &&
              !stopWords.has(term),
          )
          .map(normalizeEvidenceTerm),
      );

      const overlapCount = questionTerms.filter((term) =>
        sentenceTerms.has(term),
      ).length;

      if (overlapCount === 0) {
        return;
      }

      candidates.push({
        sentence,
        score:
          overlapCount / questionTerms.length +
          chunkOverlapCount / questionTerms.length,
        chunkIndex,
        overlapCount,
      });
    });
  });

  if (candidates.length === 0) {
  const actionIntentPatterns = [
    /\bwhat can i do\b/i,
    /\bwhat should i do\b/i,
    /\bwhat can i try\b/i,
    /\bwhat should i try\b/i,
    /\bhow can i\b/i,
    /\bhow do i\b/i,
    /\bways to\b/i,
    /\bways of\b/i,
    /\btips (to|for|on)\b/i,
  ];

  const hasActionIntent = actionIntentPatterns.some(
    (pattern) => pattern.test(question),
  );

  if (!hasActionIntent) {
    return "NO_SUPPORTED_EVIDENCE";
  }

  const actionPatterns = [
    /\btry\b/i,
    /\bexplore\b/i,
    /\bschedule\b/i,
    /\bpractice\b/i,
    /\bengage\b/i,
    /\buse\b/i,
    /\bset\b/i,
    /\bseek\b/i,
  ];

  for (const chunk of chunks) {
    const text = String(chunk.metadata.text ?? "").trim();

    if (!text) {
      continue;
    }

    const sentences = text
      .split(/(?<=[.!?])\s+|\n+/)
      .map((sentence) => sentence.trim())
      .filter(Boolean);

    const actionableSentence = sentences.find((sentence) =>
      actionPatterns.some((pattern) =>
        pattern.test(sentence),
      ),
    );

    if (actionableSentence) {
      return actionableSentence;
    }
  }

  return "NO_SUPPORTED_EVIDENCE";
}

  candidates.sort((a, b) => {
    if (b.score !== a.score) {
      return b.score - a.score;
    }

    if (b.overlapCount !== a.overlapCount) {
      return b.overlapCount - a.overlapCount;
    }

    return a.chunkIndex - b.chunkIndex;
  });

  return candidates[0].sentence;
}

export async function extractEvidence(
  question: string,
  chunks: EvidenceChunk[],
  env: EvidenceEnv,
): Promise<string> {
  if (chunks.length === 0) {
    return "NO_SUPPORTED_EVIDENCE";
  }

  const bestScore = chunks[0]?.score;

  if (
    typeof bestScore !== "number" ||
    bestScore < 0
  ) {
    return "NO_SUPPORTED_EVIDENCE";
  }

  const context = buildContext(chunks);

  const prompt = EVIDENCE_EXTRACTION_PROMPT
    .replace("{context}", context)
    .replace("{question}", question);

  const response = await env.AI.run(
    "@cf/ibm-granite/granite-4.0-h-micro",
    {
      messages: [
        {
          role: "system",
          content:
            "Follow the evidence extraction instructions exactly. Use only the provided Wellness knowledge.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
      temperature: 0,
      max_tokens: 256,
    },
  );

  let evidence = "";

  if (response && typeof response === "object") {
    const responseObject = response as Record<string, unknown>;

    if (Array.isArray(responseObject.choices)) {
      const firstChoice = responseObject.choices[0];

      if (
        firstChoice &&
        typeof firstChoice === "object"
      ) {
        const choice = firstChoice as Record<string, unknown>;
        const message = choice.message;

        if (
          message &&
          typeof message === "object"
        ) {
          const messageObject =
            message as Record<string, unknown>;

          if (
            typeof messageObject.content === "string"
          ) {
            evidence = messageObject.content.trim();
          }
        }
      }
    }
  }

  if (!evidence) {
    return "EMPTY_MODEL_RESPONSE";
  }

  if (evidence === "NO_SUPPORTED_EVIDENCE") {
  return extractDeterministicEvidence(
    question,
    chunks,
  );
}

  return evidence;
}