import { routeSafety } from "./safety";
import { retrieve } from "./retrieval";
import { extractEvidence } from "./evidence";
import { generateFinalAnswer } from "./generation";

export interface Env {
  AI: Ai;
  VECTORIZE: VectorizeIndex;
  HF_TOKEN: string;
}

interface ChatRequest {
  question?: string;
}
const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function jsonResponse(
  data: unknown,
  status = 200,
): Response {
  return Response.json(data, {
    status,
    headers: CORS_HEADERS,
  });
}

export default {
  async fetch(
    request: Request,
    env: Env,
  ): Promise<Response> {
    
if (request.method === "OPTIONS") {
  return new Response(null, {
    status: 204,
    headers: CORS_HEADERS,
  });
}

if (request.method !== "POST") {
  return jsonResponse(
    { error: "Method not allowed" },
    405,
  );
}

    let body: ChatRequest;

    try {
  body = (await request.json()) as ChatRequest;
} catch {
  return jsonResponse(
    { error: "Invalid JSON body" },
    400,
  );
}

const question = body.question?.trim();

if (!question) {
  return jsonResponse(
    { error: "Question is required" },
    400,
  );
}

if (question.length > 2000) {
  return jsonResponse(
    { error: "Question is too long" },
    400,
  );
}

    // ---------------------------------------------------------------
    // Deterministic safety routing MUST happen before retrieval.
    // ---------------------------------------------------------------
    const safety = routeSafety(question);

    if (safety.route !== "normal") {
      return jsonResponse({
        question,
        route: safety.route,
        response: safety.response,
      });
    }

    // ---------------------------------------------------------------
    // Normal RAG pipeline
    // ---------------------------------------------------------------
    try {
      const retrieval = await retrieve(question, env);

      if (retrieval.selected.length === 0) {
        return jsonResponse({
          question,
          route: "normal",
          answer:
            "I don't have enough information in my current knowledge base to answer that.",
          sources: [],
          context_chunks: [],
        });
      }

      // -------------------------------------------------------------
      // Evidence extraction
      // -------------------------------------------------------------
            const evidence = await extractEvidence(
        question,
        retrieval.selected,
        env,
      );

      // -------------------------------------------------------------
      // Evidence sufficiency gate
      // Do not generate an answer when the knowledge base does not
      // provide supported evidence for the question.
      // -------------------------------------------------------------
      if (evidence === "NO_SUPPORTED_EVIDENCE") {
        return jsonResponse({
          question,
          route: "normal",
          answer:
            "I don't have enough information in my current knowledge base to answer that.",
          sources: [],
          candidate_count: retrieval.candidates.length,
          selected_matches: retrieval.selected,
          evidence,
        });
      }

      // -------------------------------------------------------------
      // Final answer generation
      // -------------------------------------------------------------
      const answer = await generateFinalAnswer(
  env.AI,
  {
        question,
        chunks: retrieval.selected.map((match) => ({
          organization: String(
            match.metadata?.organization ?? "Unknown"
          ),
          title: String(
            match.metadata?.title ?? "Unknown"
          ),
          text: String(
            match.metadata?.text ?? ""
          ),
        })),
        verifiedEvidence: evidence,
      },
);

      // -------------------------------------------------------------
      // Source list — same deduplication strategy as local pipeline
      // -------------------------------------------------------------
      const sources: Array<{
        organization: string;
        title: string;
      }> = [];

      const seen = new Set<string>();

      for (const match of retrieval.selected) {
        const organization = String(
          match.metadata?.organization ?? "Unknown"
        );

        const title = String(
          match.metadata?.title ?? "Unknown"
        );

        const key = `${organization}\u0000${title}`;

        if (seen.has(key)) {
          continue;
        }

        seen.add(key);

        sources.push({
          organization,
          title,
        });
      }

      return jsonResponse({
        question,
        route: "normal",
        answer,
        sources,
        candidate_count: retrieval.candidates.length,
        selected_matches: retrieval.selected,
        evidence,
      });
    } catch (error) {
      console.error("RAG generation error:", error);

            
return jsonResponse(
  {
    error: "Generation failed",
  },
  500,
);
    }
  },
};