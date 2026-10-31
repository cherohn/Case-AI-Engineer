from store_agent.policies import SECTIONS


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Look up current prices, stock, and promotions. Use short product name terms, "
                "not a full sentence. For a specific model, omit category. Category names: "
                "Violões (acoustic guitars), Guitarras (electric guitars), Baixos, Ukuleles, "
                "Baterias, Teclados. Empty query lists products by category. "
                "Set available_only=false to find unavailable or discontinued models."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "category": {"type": "string"},
                    "max_price": {"type": "string", "description": "BRL price cap, e.g. 1000.00. Before PIX discount."},
                    "available_only": {"type": "boolean"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 5},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product",
            "description": "Look up a product by a known catalog ID. Returns price, stock, and status even if unavailable.",
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "string"}},
                "required": ["product_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_policy",
            "description": "Read a section of the store manual before answering policy or general store questions.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": list(SECTIONS)}},
                "required": ["topic"],
                "additionalProperties": False,
            },
        },
    },
]
