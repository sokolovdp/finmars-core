from poms.accounts.models import Account
from poms.common.common_base_test import BaseTestCase
from poms.currencies.constants import DASH


class AccountDeleteViewSetTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.init_test_case()

        self.realm_code = "realm00000"
        self.space_code = "space00000"

        self.url = f"/{self.realm_code}/{self.space_code}/api/v1/accounts/account"

    def test_detail_delete_main_accounts(self):
        for account in Account.objects.filter(user_code__in=DASH):
            response = self.client.delete(path=f"{self.url}/{account.id}/")
            self.assertEqual(response.status_code, 409)

    def test_detail_delete_custom_accounts(self):
        account = Account.objects.last()
        portfolio = Account.objects.create(  # noqa: F841
            user_code="test",
            name="test",
            owner=account.owner,
            master_user=account.master_user,
        )

        self.assertNotIn(account.user_code, DASH)

        response = self.client.delete(path=f"{self.url}/{account.id}/")
        self.assertEqual(response.status_code, 204)
