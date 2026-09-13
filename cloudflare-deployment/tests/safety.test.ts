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
