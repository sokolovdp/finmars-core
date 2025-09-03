from django.test import override_settings

from poms.common.common_base_test import BaseTestCase

expected_response = {
    "status": "ok",
    "task_id": "1",
    "meta": {
        "execution_time": 41,
        "request_id": "44b3ffbe-afc2-4c97-ae32-0700b35eac2d",
    },
}


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class SyncViewSetTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.init_test_case()
        self.url = f"/{self.realm_code}/{self.space_code}/api/v1/explorer/sync/"

    def test__post(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)

        response_json = response.json()
        self.assertIn("status", response_json)
        self.assertEqual(response_json["status"], "ok")
        self.assertIn("task_id", response_json)

    @BaseTestCase.cases(
        ("get", "get"),
        ("put", "put"),
        ("patch", "patch"),
        ("delete", "delete"),
    )
    def test__invalid_methods(self, name: str):
        method = getattr(self.client, name)

        response = method(self.url)

        self.assertEqual(response.status_code, 405)
