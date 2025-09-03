from poms.common.common_base_test import BaseTestCase
from poms.ui.models import MemberLayout


class MemberLayoutViewSetTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.init_test_case()
        self.realm_code = "realm00000"
        self.space_code = "space00000"
        self.url = f"/{self.realm_code}/{self.space_code}/api/v1/ui/member-layout/"

    def test__list(self):
        response = self.client.get(path=self.url)
        self.assertEqual(response.status_code, 200, response.content)

        response_json = response.json()
        self.assertEqual(response_json["count"], 1)
        self.assertIsNone(response_json["next"])
        self.assertIsNone(response_json["previous"])

        layout_data = response_json["results"][0]
        self.assertEqual(layout_data["name"], "default")
        self.assertEqual(layout_data["configuration_code"], "local.poms.space00000")
        self.assertTrue(layout_data["is_default"])

    def test__ping(self):
        layout = MemberLayout.objects.get(member=self.member, is_default=True)
        response = self.client.get(path=f"{self.url}{layout.id}/ping/")
        self.assertEqual(response.status_code, 200, response.content)

        response_json = response.json()
        self.assertEqual(response_json["id"], layout.id)
        self.assertTrue(response_json["is_default"])
        self.assertEqual(
            response_json["modified_at"],
            layout.modified_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        )
