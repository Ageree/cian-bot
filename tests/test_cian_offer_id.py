import unittest

from cian_api import _extract_offer_id


class ExtractOfferIdTests(unittest.TestCase):
    def test_extracts_sale_offer_id(self):
        self.assertEqual(
            _extract_offer_id("https://www.cian.ru/sale/flat/123456789/"),
            "123456789",
        )

    def test_extracts_rent_offer_id(self):
        self.assertEqual(
            _extract_offer_id("https://www.cian.ru/rent/flat/987654321/"),
            "987654321",
        )

    def test_invalid_url_returns_empty_string(self):
        self.assertEqual(_extract_offer_id("https://www.cian.ru/not-an-offer/"), "")


if __name__ == "__main__":
    unittest.main()
