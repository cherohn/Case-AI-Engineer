import re

from pypdf import PdfReader

from store_agent.catalog import DATA_DIR


SOURCE_HEADINGS = {
    "store": "1. Sobre a Empório da Música",
    "hours": "2. Horário de Funcionamento",
    "payments": "3. Formas de Pagamento",
    "returns": "4. Política de Trocas e Devoluções",
    "shipping": "5. Política de Frete e Entregas",
    "promotions": "6. Promoções e Descontos",
    "service": "7. Atendimento via WhatsApp",
    "warranty": "8. Garantia",
    "privacy": "9. Privacidade e Proteção de Dados",
    "general": "10. Disposições Finais",
}
SECTIONS = {
    "store": "1. About Empório da Música",
    "hours": "2. Opening hours",
    "payments": "3. Payment methods",
    "returns": "4. Exchanges and returns",
    "shipping": "5. Shipping and deliveries",
    "promotions": "6. Promotions and discounts",
    "service": "7. WhatsApp customer support",
    "warranty": "8. Warranty",
    "privacy": "9. Privacy and data protection",
    "general": "10. General provisions",
}


class Policies:
    def __init__(self, path=DATA_DIR / "store_policies.pdf"):
        reader = PdfReader(path)
        pages = []
        for page in reader.pages[1:]:
            text = page.extract_text(extraction_mode="layout")
            lines = [" ".join(line.split()) for line in text.splitlines()]
            lines = [line for line in lines if line and not line.startswith(
                "Empório da Música Manual"
            ) and not re.fullmatch(r"Página \d+", line)]
            pages.append("\n".join(lines))

        text = "\n".join(pages)
        headings = list(SOURCE_HEADINGS.values())
        positions = [text.index(heading) for heading in headings]
        self.sections = {}
        for index, topic in enumerate(SOURCE_HEADINGS):
            end = positions[index + 1] if index + 1 < len(positions) else len(text)
            self.sections[topic] = text[positions[index]:end].strip()

    def read_policy(self, topic: str) -> dict:
        if topic not in self.sections:
            raise ValueError("Unknown policy topic. Choose: " + ", ".join(SECTIONS))
        result = {
            "source": "data/store_policies.pdf",
            "section": SECTIONS[topic],
            "text": self.sections[topic],
        }
        if topic == "returns":
            result["service_boundary"] = {
                "next_step": "Contact the store team to confirm the return procedure.",
                "logistics": "The manual does not specify pickup or shipping-label procedures. These are unverified.",
                "available_actions": [],
            }
        return result

    def check_return(self, purchase_channel=None, days_since_receipt=None) -> dict:
        if purchase_channel is not None and purchase_channel not in {"online", "in_store"}:
            raise ValueError("purchase_channel must be online or in_store")
        if days_since_receipt is not None and days_since_receipt < 0:
            raise ValueError("days_since_receipt must be non-negative")
        questions = []
        if purchase_channel is None:
            questions.append("Was the purchase made online or in store?")
        if days_since_receipt is None:
            questions.append("How many calendar days ago did you receive the instrument?")
        if questions:
            return {
                "needs_information": True,
                "question": "I can help check that. " + " ".join(questions),
            }
        result = self.read_policy("returns")
        result["customer_facts"] = {
            "purchase_channel": purchase_channel,
            "days_since_receipt": days_since_receipt,
        }
        return result
