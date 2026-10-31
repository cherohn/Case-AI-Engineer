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

    def test_return_question_only_requests_missing_facts(self):
        result = self.policies.check_return(purchase_channel="online")
        self.assertIn("days ago did you receive", result["question"])
        self.assertNotIn("online or in store", result["question"])
        self.assertNotIn("text", result)

    def test_supplied_purchase_facts_unlock_the_policy_without_approving_a_return(self):
        result = self.policies.check_return(purchase_channel="online", days_since_receipt=3)
        self.assertEqual(result["section"], "4. Política de Trocas e Devoluções")
        self.assertEqual(result["customer_facts"]["days_since_receipt"], 3)
        self.assertEqual(result["service_boundary"]["available_actions"], [])
