import re

from pypdf import PdfReader

from store_agent.catalog import DATA_DIR


SECTIONS = {
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
        headings = list(SECTIONS.values())
        positions = [text.index(heading) for heading in headings]
        self.sections = {}
        for index, topic in enumerate(SECTIONS):
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
