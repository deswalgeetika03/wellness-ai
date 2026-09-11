import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import api


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(api.app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")

        self.assertIn(response.status_code, [200, 503])

        data = response.json()

        self.assertIn("status", data)
        self.assertIn("service", data)

        print("\n[PASS] Health endpoint")

    @patch("api.answer_query")
    def test_normal_chat(self, mock_answer):
        mock_answer.return_value = {
            "route": "normal",
            "answer": "Try taking a few slow breaths.",
            "sources": [],
            "context_chunks": [],
        }

        response = self.client.post(
            "/api/chat",
            json={
                "question": "How can I reduce stress?",
                "history": [],
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["route"], "normal")
        self.assertEqual(
            data["answer"],
            "Try taking a few slow breaths.",
        )

        print("[PASS] Normal chat request")

    def test_empty_question(self):
        response = self.client.post(
            "/api/chat",
            json={
                "question": "   ",
                "history": [],
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["route"], "empty")
        self.assertIn("Please enter a question", data["answer"])

        print("[PASS] Empty question handling")

    def test_question_too_long(self):
        question = "a" * 2001

        response = self.client.post(
            "/api/chat",
            json={
                "question": question,
                "history": [],
            },
        )

        self.assertEqual(response.status_code, 422)

        print("[PASS] Question length validation")

    @patch("api.answer_query")
    def test_ollama_failure_returns_503(self, mock_answer):
        mock_answer.side_effect = RuntimeError(
            "Couldn't reach Ollama"
        )

        response = self.client.post(
            "/api/chat",
            json={
                "question": "How can I manage stress?",
                "history": [],
            },
        )

        self.assertEqual(response.status_code, 503)

        data = response.json()

        self.assertIn("temporarily unavailable", data["detail"])

        print("[PASS] Ollama failure → 503")

    @patch("api.answer_query")
    def test_history_is_accepted(self, mock_answer):
        mock_answer.return_value = {
            "route": "normal",
            "answer": "That sounds difficult.",
            "sources": [],
            "context_chunks": [],
        }

        history = [
            {
                "role": "user",
                "content": "I have been feeling stressed.",
            },
            {
                "role": "assistant",
                "content": "What has been causing the stress?",
            },
        ]

        response = self.client.post(
            "/api/chat",
            json={
                "question": "It is mostly because of college.",
                "history": history,
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["route"], "normal")

        print("[PASS] Conversation history accepted")


if __name__ == "__main__":
    unittest.main(verbosity=2)