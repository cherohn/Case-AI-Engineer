import csv
from decimal import Decimal
from pathlib import Path
import shutil
import tempfile
import unittest

from store_agent.catalog import Catalog, DATA_DIR


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.catalog = Catalog()

    def test_discovery_lists_only_categories_with_available_products(self):
        categories = self.catalog.list_categories()["categories"]
        self.assertEqual(sum(c["available_products"] for c in categories), 61)
        self.assertIn("Acoustic guitars", [c["name"] for c in categories])
        self.assertNotIn("Woodwinds", [c["name"] for c in categories])

    def test_catalog_pages_have_no_duplicates_and_cover_every_available_product(self):
        first = self.catalog.search_products(limit=20)
        second = self.catalog.search_products(limit=20, offset=20)
        third = self.catalog.search_products(limit=20, offset=40)
        fourth = self.catalog.search_products(limit=20, offset=60)
        ids = [p["product_id"] for page in [first, second, third, fourth] for p in page["products"]]
        self.assertEqual(len(ids), first["total_matches"])
        self.assertEqual(len(set(ids)), len(ids))

    def test_budget_search_returns_available_guitars_in_price_order(self):
        result = self.catalog.search_products(category="violoes", max_price="1000", limit=20)
        products = result["products"]
        self.assertGreater(len(products), 0)
        self.assertTrue(all(p["category"] == "Acoustic guitars" and p["available"] for p in products))
        prices = [Decimal(p["price_brl"]) for p in products]
        self.assertEqual(prices, sorted(prices))
        self.assertTrue(all(price <= 1000 for price in prices))

    def test_takamine_price_comes_from_catalog(self):
        product = self.catalog.search_products(query="Takamine GD20")["products"][0]
        self.assertEqual(product["price_brl"], "2199.00")
        self.assertEqual(product["pix_price_brl"], "2089.05")

    def test_english_filters_and_original_category_aliases_return_the_same_products(self):
        english = self.catalog.search_products(category="Acoustic guitars", max_price="1000")
        original = self.catalog.search_products(category="violoes", max_price="1000")
        self.assertEqual(english["products"], original["products"])
        self.assertGreater(english["total_matches"], 0)

    def test_status_and_stock_both_control_availability(self):
        for product_id in ["96", "113", "130", "136"]:
            with self.subTest(product_id=product_id):
                product = self.catalog.get_product(product_id)["product"]
                self.assertFalse(product["available"])
                result = self.catalog.search_products(query=product["name"])
                self.assertEqual(result["total_matches"], 0)

    def test_active_discount_does_not_stack_with_pix(self):
        product = self.catalog.get_product("90")["product"]
        self.assertEqual(product["discount_percent"], "18")
        expected = (Decimal(product["original_price_brl"]) * Decimal("0.82")).quantize(Decimal("0.01"))
        self.assertEqual(Decimal(product["price_brl"]), expected)
        self.assertEqual(product["pix_price_brl"], product["price_brl"])

    def test_inactive_promotions_are_ignored(self):
        product = self.catalog.get_product("102")["product"]
        self.assertEqual(product["discount_percent"], "0")
        self.assertEqual(product["price_brl"], product["original_price_brl"])

    def test_missing_product_is_not_invented(self):
        self.assertIsNone(self.catalog.get_product("unknown")["product"])
        self.assertEqual(self.catalog.search_products(query="nonexistent instrument")["total_matches"], 0)

    def test_stock_changes_are_visible_on_the_next_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            data_dir = Path(directory)
            for filename in ["products.csv", "categories.csv", "promotions.csv"]:
                shutil.copyfile(DATA_DIR / filename, data_dir / filename)
            catalog = Catalog(data_dir)
            self.assertTrue(catalog.get_product("95")["product"]["available"])
            with (data_dir / "products.csv").open(newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                fields = reader.fieldnames
                rows = list(reader)
            for row in rows:
                if row["product_id"] == "95":
                    row["stock_quantity"] = "0"
            with (data_dir / "products.csv").open("w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            self.assertFalse(catalog.get_product("95")["product"]["available"])

    def test_invalid_price_caps_are_rejected(self):
        for value in ["-1", "NaN", "Infinity"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.catalog.search_products(max_price=value)


if __name__ == "__main__":
    unittest.main()
