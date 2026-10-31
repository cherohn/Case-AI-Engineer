import csv
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import unicodedata


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in text if not unicodedata.combining(char))


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class Catalog:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = Path(data_dir)

    def _read(self, filename: str) -> list[dict]:
        with (self.data_dir / filename).open(encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

    def _discounts(self) -> dict[str, Decimal]:
        discounts = {}
        for row in self._read("promotions.csv"):
            if row["is_active"] == "1":
                product_id = row["product_id"]
                # If active promotions overlap, apply the largest discount once.
                discounts[product_id] = max(
                    discounts.get(product_id, Decimal("0")),
                    Decimal(row["discount_percent"]),
                )
        return discounts

    def _products(self) -> list[dict]:
        categories = {row["category_id"]: row["name"] for row in self._read("categories.csv")}
        discounts = self._discounts()
        products = []
        for row in self._read("products.csv"):
            original_price = Decimal(row["price_brl"])
            discount = discounts.get(row["product_id"], Decimal("0"))
            price = original_price * (1 - discount / 100)
            stock = int(row["stock_quantity"])
            products.append({
                "product_id": row["product_id"],
                "name": row["name"],
                "category": categories[row["category_id"]],
                "description": row["description"],
                "status": row["status"],
                "stock_quantity": stock,
                "available": row["status"] == "active" and stock > 0,
                "original_price_brl": money(original_price),
                "discount_percent": str(discount),
                "price_brl": money(price),
                "pix_price_brl": money(price if discount else original_price * Decimal("0.95")),
            })
        return products

    def get_product(self, product_id: str) -> dict:
        for product in self._products():
            if product["product_id"] == str(product_id):
                return {"product": product, "source": "data/products.csv; data/promotions.csv"}
        return {"product": None, "message": "Product not found in the supplied catalog."}

    def search_products(
        self,
        query: str = "",
        category: str = "",
        max_price: str | None = None,
        available_only: bool = True,
        limit: int = 5,
    ) -> dict:
        """Search by name terms and category; the price cap uses the current price before PIX."""
        if not 1 <= limit <= 20:
            raise ValueError("limit must be between 1 and 20")
        ceiling = Decimal(str(max_price)) if max_price is not None else None
        if ceiling is not None and (not ceiling.is_finite() or ceiling < 0):
            raise ValueError("max_price must be a finite, non-negative number")

        terms = normalize(query).split()
        matches = []
        for product in self._products():
            if available_only and not product["available"]:
                continue
            if category and normalize(category) not in normalize(product["category"]):
                continue
            if not all(term in normalize(product["name"]) for term in terms):
                continue
            if ceiling is not None and Decimal(product["price_brl"]) > ceiling:
                continue
            matches.append(product)

        matches.sort(key=lambda product: (Decimal(product["price_brl"]), product["name"]))
        return {
            "products": matches[:limit],
            "total_matches": len(matches),
            "source": "data/products.csv; data/categories.csv; data/promotions.csv",
            "price_filter": "Current price before the payment-specific PIX discount.",
        }
