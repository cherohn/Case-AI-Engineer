import unittest

from store_agent.policies import Policies


class PoliciesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policies = Policies()

    def test_return_rules_keep_conditions_and_exclusions(self):
        policy = self.policies.read_policy("returns")
        self.assertIn("7 (sete) dias corridos", policy["text"])
        self.assertIn("após o recebimento", policy["text"])
        self.assertIn("4.4 Itens Não Elegíveis", policy["text"])
        self.assertNotIn("5. Política de Frete", policy["text"])

    def test_shipping_includes_both_pages(self):
        text = self.policies.read_policy("shipping")["text"]
        self.assertIn("R$ 500,00", text)
        self.assertIn("5.3 Código de Rastreamento", text)
        self.assertNotIn("6. Promoções", text)

    def test_privacy_section_continues_across_pages(self):
        text = self.policies.read_policy("privacy")["text"]
        self.assertIn("consentimento explícito", text)
        self.assertIn("exclusão de seus dados", text)

    def test_unknown_section_fails_instead_of_returning_unrelated_text(self):
        with self.assertRaises(ValueError):
            self.policies.read_policy("invented")
