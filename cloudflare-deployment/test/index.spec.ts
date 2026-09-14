import {
  env,
  createExecutionContext,
  waitOnExecutionContext,
} from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

describe("Wellness AI Worker HTTP contract", () => {
  it("rejects non-POST requests with 405", async () => {
    const request = new IncomingRequest("http://example.com");
    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(405);
    expect(await response.json()).toEqual({
      error: "Method not allowed",
    });
  });

  it("rejects invalid JSON with 400", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: "{invalid",
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      error: "Invalid JSON body",
    });
  });

  it("rejects a missing question with 400", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({}),
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      error: "Question is required",
    });
  });

  it("rejects an oversized question with 400", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: "a".repeat(2001),
      }),
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      error: "Question is too long",
    });
  });

  it("routes a crisis request before retrieval", async () => {
    const question = "I want to kill myself";

    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.route).toBe("crisis");
    expect(body.question).toBe(question);
    expect(body.response).toBeTruthy();
  });

  it("routes medication requests before retrieval", async () => {
    const question = "What medication should I take for anxiety?";

    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.route).toBe("medication_restricted");
    expect(body.question).toBe(question);
    expect(body.response).toBeTruthy();
  });

    it("routes eating-disorder requests before retrieval", async () => {
    const question = "How many calories should I eat?";

    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.route).toBe("eating_disorder_restricted");
    expect(body.question).toBe(question);
    expect(body.response).toBeTruthy();
  });

  it("routes restrictive-eating requests before retrieval", async () => {
    const question = "How can I severely restrict my food intake?";

    const request = new IncomingRequest("http://example.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    const body = await response.json();

    expect(response.status).toBe(200);
    expect(body.route).toBe("eating_disorder_restricted");
    expect(body.question).toBe(question);
    expect(body.response).toBeTruthy();
  });

  it("handles CORS preflight requests", async () => {
    const request = new IncomingRequest("http://example.com", {
      method: "OPTIONS",
    });

    const ctx = createExecutionContext();

    const response = await worker.fetch(request, env, ctx);
    await waitOnExecutionContext(ctx);

    expect(response.status).toBe(204);
    expect(response.headers.get("Access-Control-Allow-Origin")).toBe("*");
    expect(response.headers.get("Access-Control-Allow-Methods")).toBe(
      "POST, OPTIONS",
    );
  });
});
