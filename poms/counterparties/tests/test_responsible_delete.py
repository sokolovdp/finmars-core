from poms.common.common_base_test import BaseTestCase
from poms.counterparties.models import Responsible
from poms.currencies.constants import DASH
from poms.users.models import MasterUser, Member


class ResponsibleDeleteViewSetTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.init_test_case()
        self.realm_code = "realm00000"
        self.space_code = "space00000"
        self.url = f"/{self.realm_code}/{self.space_code}/api/v1/counterparties/responsible"

    def test_detail_delete_main_responsibles(self):
        for responsible in Responsible.objects.filter(user_code__in=DASH):
            response = self.client.delete(path=f"{self.url}/{responsible.id}/")
            self.assertEqual(response.status_code, 409)

    def test_detail_delete_custom_responsibles(self):
        owner = Member.objects.first()
        master_user = MasterUser.objects.first()
        responsible = Responsible.objects.create(
            user_code="test",
            name="test",
            owner=owner,
            master_user=master_user,
        )

        self.assertNotIn(responsible.user_code, DASH)

        response = self.client.delete(path=f"{self.url}/{responsible.id}/")
        self.assertEqual(response.status_code, 204)
