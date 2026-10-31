import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from groq import AuthenticationError, RateLimitError
import httpx

from store_agent.web import create_app


class WebTest(unittest.TestCase):
    def setUp(self):
        self.agent_patch = patch("store_agent.web.Agent")
        self.agent_class = self.agent_patch.start()
        self.addCleanup(self.agent_patch.stop)
        self.agent_class.side_effect = lambda *args, **kwargs: Mock(reply=Mock(return_value="Here is the answer."))
        self.client = TestClient(create_app(client=Mock()))
        self.addCleanup(self.client.close)

    def test_page_and_assets_load_without_calling_the_agent(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Let's talk music.", response.text)
        for path in ["/static/chat.js", "/static/style.css", "/api/health"]:
            self.assertEqual(self.client.get(path).status_code, 200)
        self.agent_class.assert_not_called()

    def test_session_reuses_its_agent_and_new_sessions_are_separate(self):
        first = self.client.post("/api/chat", json={"message": "Hello"}).json()
        second = self.client.post("/api/chat", json={"message": "And PIX?", "session_id": first["session_id"]}).json()
        third = self.client.post("/api/chat", json={"message": "Hello"}).json()
        self.assertEqual(first["session_id"], second["session_id"])
        self.assertNotEqual(first["session_id"], third["session_id"])
        self.assertEqual(self.agent_class.call_count, 2)

    def test_clear_session_prevents_old_history_from_being_reused(self):
        session = self.client.post("/api/chat", json={"message": "Hello"}).json()["session_id"]
        self.assertEqual(self.client.delete(f"/api/sessions/{session}").status_code, 200)
        response = self.client.post("/api/chat", json={"message": "Again", "session_id": session})
        self.assertEqual(response.status_code, 404)

    def test_invalid_input_never_creates_an_agent(self):
        for body in [{"message": " "}, {"message": "x" * 1001}, {"message": "Hello", "session_id": "invalid"}]:
            self.assertEqual(self.client.post("/api/chat", json=body).status_code, 422)
        self.agent_class.assert_not_called()

    def test_unknown_session_does_not_call_the_agent(self):
        response = self.client.post("/api/chat", json={"message": "Hi", "session_id": str(uuid4())})
        self.assertEqual(response.status_code, 404)
        self.agent_class.assert_not_called()

    def test_rate_limit_is_forwarded_without_retry(self):
        agent = Mock()
        agent.reply.side_effect = RateLimitError(
            "limited",
            response=httpx.Response(429, headers={"retry-after": "12"}, request=httpx.Request("POST", "https://api.groq.com")),
            body=None,
        )
        self.agent_class.side_effect = None
        self.agent_class.return_value = agent
        response = self.client.post("/api/chat", json={"message": "Hello"})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "12")
        agent.reply.assert_called_once()

    def test_provider_error_details_are_not_exposed_to_the_browser(self):
        agent = Mock()
        agent.reply.side_effect = AuthenticationError(
            "sensitive provider details",
            response=httpx.Response(401, request=httpx.Request("POST", "https://api.groq.com")),
            body=None,
        )
        self.agent_class.side_effect = None
        self.agent_class.return_value = agent
        response = self.client.post("/api/chat", json={"message": "Hello"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("sensitive provider details", response.text)
