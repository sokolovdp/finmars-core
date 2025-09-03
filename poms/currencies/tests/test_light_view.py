from poms.common.common_base_test import BaseTestCase
from poms.currencies.models import Currency


class CompanyViewTestCase(BaseTestCase):
    databases = "__all__"

    def setUp(self):
        super().setUp()
        self.init_test_case()
        self.realm_code = "realm00000"
        self.space_code = "space00000"
        self.url = f"/{self.realm_code}/{self.space_code}/api/v1/currencies/currency/light/"

    @BaseTestCase.cases(
        ("name", "name"),
        ("user_code", "user_code"),
        ("short_name", "short_name"),
        ("public_name", "public_name"),
    )
    def test__filter_by_query(self, field):
        query = self.random_string(7)
        currency = Currency.objects.first()

        self.assertTrue(hasattr(currency, field))
        setattr(currency, field, query)

        currency.save()

        response = self.client.get(self.url, data={"query": query})
        self.assertEqual(response.status_code, 200, response.content)
        response_data = response.json()

        self.assertEqual(len(response_data["results"]), 1)
        self.assertEqual(response_data["count"], 1)
        self.assertIsNone(response_data["next"])
        self.assertIsNone(response_data["previous"])

        item = response_data["results"][0]
        self.assertEqual(item[field], query)
