import json
import unittest
from unittest.mock import Mock

from groq.types.chat import ChatCompletion

from store_agent.agent import Agent


def completion(content=None, tool=None, arguments=None, finish_reason="stop"):
    message = {"role": "assistant", "content": content}
    if tool:
        message["tool_calls"] = [{
            "id": "call_1", "type": "function",
            "function": {"name": tool, "arguments": json.dumps(arguments)},
        }]
        finish_reason = "tool_calls"
    return ChatCompletion(
        id="test", created=0, model="test", object="chat.completion",
        choices=[{"index": 0, "finish_reason": finish_reason, "message": message}],
        usage={"prompt_tokens": 80, "completion_tokens": 20, "total_tokens": 100},
    )


class AgentTest(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.agent = Agent(self.client)
        self.create = self.client.chat.completions.create

    def test_product_facts_are_sent_back_to_the_model(self):
        self.create.side_effect = [
            completion(tool="search_products", arguments={"query": "Takamine GD20"}),
            completion(content="The Takamine GD20 costs R$2,199.00."),
        ]
        answer = self.agent.reply("How much is the Takamine GD20?")
        self.assertIn("2,199", answer)
        messages = self.create.call_args.kwargs["messages"]
        result = json.loads(messages[-1]["content"])
        self.assertEqual(result["products"][0]["price_brl"], "2199.00")
        self.assertEqual(messages[-1]["tool_call_id"], "call_1")
        self.assertEqual(self.agent.requests, 2)
        self.assertEqual(self.agent.tokens, 200)

    def test_repeated_tool_calls_stop_at_the_budget(self):
        self.create.return_value = completion(tool="read_policy", arguments={"topic": "returns"})
        with self.assertRaisesRegex(RuntimeError, "budget"):
            self.agent.reply("Can I return this?")
        self.assertEqual(self.create.call_count, 3)
        self.assertEqual(self.agent.history, [])

    def test_failed_api_request_is_not_retried(self):
        self.create.side_effect = RuntimeError("Network unavailable")
        with self.assertRaises(RuntimeError):
            self.agent.reply("Hello")
        self.assertEqual(self.create.call_count, 1)
        self.assertEqual(self.agent.history, [])

    def test_invalid_tool_arguments_do_not_reach_the_catalog(self):
        invalid = [
            '{"max_price": "NaN"}',
            '{"available_only": "false"}',
            '{"limit": 20}',
            '{"sql": "DROP TABLE products"}',
            'not json',
        ]
        for arguments in invalid:
            with self.subTest(arguments=arguments):
                result = self.agent._run_tool("search_products", arguments)
                self.assertIn("error", result)

    def test_unknown_tool_is_not_executed(self):
        self.assertIn("error", self.agent._run_tool("run_shell", '{"command": "pwd"}'))

    def test_history_keeps_only_two_completed_turns(self):
        self.create.return_value = completion(content="Hello!")
        for text in ["First", "Second", "Third"]:
            self.agent.reply(text)
        self.assertEqual(len(self.agent.history), 4)
        self.assertEqual(self.agent.history[0]["content"], "Second")

    def test_oversized_input_does_not_call_the_api(self):
        with self.assertRaises(ValueError):
            self.agent.reply("x" * 1001)
        self.create.assert_not_called()

    def test_truncated_answer_is_not_shown_as_complete(self):
        self.create.return_value = completion(content="Incomplete", finish_reason="length")
        with self.assertRaisesRegex(RuntimeError, "response limit"):
            self.agent.reply("Hello")
        self.assertEqual(self.agent.history, [])
