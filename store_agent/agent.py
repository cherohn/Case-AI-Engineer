from decimal import InvalidOperation
import json
from pathlib import Path

from store_agent.catalog import Catalog
from store_agent.policies import Policies
from store_agent.tools import TOOLS


PROMPT = Path(__file__).with_name("prompt.txt").read_text(encoding="utf-8")


class Agent:
    def __init__(self, client, model="openai/gpt-oss-120b"):
        self.client = client
        self.model = model
        self.history = []
        self.calls = []
        self.requests = 0
        self.tokens = 0
        catalog = Catalog()
        policies = Policies()
        self.tools = {
            "search_products": catalog.search_products,
            "get_product": catalog.get_product,
            "read_policy": policies.read_policy,
        }

    def _run_tool(self, name, arguments):
        if name not in self.tools:
            return {"error": "Unknown tool."}
        try:
            args = json.loads(arguments)
            definition = next(tool["function"] for tool in TOOLS if tool["function"]["name"] == name)
            schema = definition["parameters"]
            if not isinstance(args, dict) or args.keys() - schema["properties"].keys():
                raise ValueError("Unexpected tool arguments.")
            types = {"string": str, "integer": int, "boolean": bool}
            for key, value in args.items():
                field = schema["properties"][key]
                if type(value) is not types[field["type"]]:
                    raise ValueError("Invalid argument type: " + key)
            if name == "search_products" and not 1 <= args.get("limit", 5) <= 5:
                raise ValueError("Return between 1 and 5 products.")
            return self.tools[name](**args)
        except (ValueError, TypeError, InvalidOperation) as error:
            return {"error": str(error), "instruction": "Correct the arguments or ask the customer to clarify."}

    def reply(self, text):
        if not text.strip() or len(text) > 1000:
            raise ValueError("Please enter between 1 and 1,000 characters.")
        self.calls = []
        self.requests = 0
        self.tokens = 0
        messages = [{"role": "system", "content": PROMPT}]
        messages.extend(self.history[-4:])
        messages.append({"role": "user", "content": text})

        # A fixed budget prevents a tool loop from consuming the free quota.
        for step in range(3):
            self.requests += 1
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="none" if step == 2 else "auto",
                parallel_tool_calls=False,
                temperature=0.2,
                reasoning_effort="low",
                include_reasoning=False,
                max_completion_tokens=800,
            )
            if response.usage:
                self.tokens += response.usage.total_tokens
            message = response.choices[0].message
            if response.choices[0].finish_reason == "length":
                raise RuntimeError("The model reached its response limit. Try a shorter question.")
            if not message.tool_calls:
                answer = message.content
                if not answer:
                    raise RuntimeError("The model returned an empty answer.")
                self.history.extend([
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": answer[:2000]},
                ])
                self.history = self.history[-4:]
                return answer

            if step == 2:
                break
            messages.append(message.model_dump(include={"role", "content", "tool_calls"}, exclude_none=True))
            for call in message.tool_calls:
                result = self._run_tool(call.function.name, call.function.arguments)
                self.calls.append({"tool": call.function.name, "arguments": call.function.arguments})
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        raise RuntimeError("The tool-call budget was reached. Try a more specific question.")
