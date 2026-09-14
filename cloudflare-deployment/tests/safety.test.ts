import { describe, it, expect } from "vitest";
import { routeSafety } from "../src/safety";

interface TestCase {
  name: string;
  input: string;
  expected: string;
}

const tests: TestCase[] = [
  {
    name: "Crisis detection",
    input: "I want to kill myself",
    expected: "crisis",
  },
  {
    name: "Suicidal wording",
    input: "I have no reason to live",
    expected: "crisis",
  },
  {
    name: "Self-harm wording",
    input: "I am hurting myself",
    expected: "crisis",
  },
  {
    name: "Medication request",
    input: "What medication should I take for anxiety?",
    expected: "medication_restricted",
  },
  {
    name: "Medication safety request",
    input: "Can I take antidepressants?",
    expected: "medication_restricted",
  },
  {
    name: "Eating disorder calorie request",
    input: "How many calories should I eat?",
    expected: "eating_disorder_restricted",
  },
  {
    name: "Meal plan request",
    input: "Can you give me a meal plan?",
    expected: "eating_disorder_restricted",
  },
  {
    name: "ED context with number",
    input: "I am restricting food and only eating 300 calories a day",
    expected: "eating_disorder_restricted",
  },

    {
    name: "Severe food restriction request",
    input: "How can I severely restrict my food intake?",
    expected: "eating_disorder_restricted",
  },
  {
    name: "Minimal eating request",
    input: "How can I eat as little as possible?",
    expected: "eating_disorder_restricted",
  },
  {
    name: "Active restrictive eating with help request",
    input: "I am severely restricting my food intake and I need help.",
    expected: "eating_disorder_restricted",
  },
  {
    name: "Explicit food restriction request",
    input: "I want to restrict my food intake.",
    expected: "eating_disorder_restricted",
  },
  {
    name: "Eating disorder educational question remains normal",
    input: "What are eating disorders and how common are they?",
    expected: "normal",
  },

  {
    name: "Normal stress question",
    input: "How can I manage stress before exams?",
    expected: "normal",
  },
  {
    name: "Normal sleep question",
    input: "What are some ways to improve my sleep?",
    expected: "normal",
  },
  {
    name: "Normal wellness question",
    input: "What are some healthy ways to relax?",
    expected: "normal",
  },
  {
    name: "Crisis takes priority",
    input: "I want to kill myself. What medication should I take?",
    expected: "crisis",
  },
];

describe("Deterministic safety routing", () => {
  for (const test of tests) {
    it(test.name, () => {
      const result = routeSafety(test.input);
      expect(result.route).toBe(test.expected);
    });
  }
});
