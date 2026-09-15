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
  history?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
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

function isFollowUpQuestion(question: string): boolean {
  const normalized = question.toLowerCase().trim();

  const followUpPatterns = [
    /\bwhat should i try first\b/,
    /\bwhat should i try\b/,
    /\bwhat should i do first\b/,
    /\bwhat can i try first\b/,
    /\bhow do i start\b/,
    /\bwhere should i start\b/,
    /\bwhat are the main signs\b/,
    /\bwhat about this\b/,
    /\bwhat about that\b/,
    /\bcan you explain more\b/,
    /\btell me more\b/,
    /\bcan you give me more\b/,
    /\bwhat else\b/,
    /\bhow about\b/,
    /\bwhat do you mean\b/,
    /\bwhy is that\b/,
    /\bhow does that work\b/,
    /\bcan you explain that\b/,
    /\bwhat about it\b/,
    /\bhow can i do that\b/,
    /\bhow can i try that\b/,
  ];

  return followUpPatterns.some((pattern) =>
    pattern.test(normalized),
  );
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
      const previousUserMessage = body.history
  ?.slice()
  .reverse()
  .find((message) => message.role === "user")?.content?.trim();

const retrievalQuery =
  previousUserMessage && isFollowUpQuestion(question)
    ? `${previousUserMessage} ${question}`
    : question;

const retrieval = await retrieve(retrievalQuery, env);
  

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
              retrievalQuery,
              retrieval.context,
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
          chunks: retrieval.context.map((match) => ({
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
         history: body.history,
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