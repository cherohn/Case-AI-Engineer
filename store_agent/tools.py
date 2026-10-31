from store_agent.policies import SECTIONS


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": "Discover which instrument categories actually have available stock. Use when customers ask what the store sells or need help getting started.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": (
                "Look up current prices, stock, and promotions. Use short product name terms, "
                "not a full sentence. For a specific model, omit category. Category names: "
                "Acoustic guitars, Electric guitars, Basses, Ukuleles, "
                "Drums and percussion, Keyboards and pianos. Empty query lists products by category. "
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
            "name": "check_return",
            "description": "Use first when a customer wants to return their own purchase or has changed their mind. Pass only explicitly supplied facts; omit unknown fields or pass null. Never infer receipt time from purchase time. Missing facts produce a clarification question before eligibility can be discussed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "purchase_channel": {"type": ["string", "null"], "enum": ["online", "in_store", None]},
                    "days_since_receipt": {"type": ["integer", "null"], "minimum": 0},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_policy",
            "description": "Read the store manual for general policies and store information. For a customer asking to return their own purchase, use check_return first.",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string", "enum": list(SECTIONS)}},
                "required": ["topic"],
                "additionalProperties": False,
            },
        },
    },
]
