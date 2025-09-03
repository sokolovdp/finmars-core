from copy import deepcopy
from unittest import mock

from django.contrib.auth.models import User

from poms.celery_tasks.models import CeleryTask
from poms.common.common_base_test import FINMARS_BOT, BaseTestCase
from poms.configuration.models import Configuration
from poms.configuration.tasks import install_package_from_marketplace
from poms.configuration.tests.common_test_data import *  # noqa: F403


class InstallPackageFromMarketplaceTaskTest(BaseTestCase):
    databases = "__all__"

    def setUp(self):
        super().setUp()
        self.init_test_case()
        User.objects.get_or_create(username=FINMARS_BOT, is_staff=True, is_superuser=True)
        self.mock_response = mock.Mock()
        self.mock_response.status_code = 200

    def create_celery_task(self) -> CeleryTask:
        celery_task = CeleryTask.objects.create(
            master_user=self.master_user,
            member=self.member,
            verbose_name="Install Configuration From Marketplace",
            type="install_configuration_from_marketplace",
        )
        options_object = {
            "configuration_code": POST_PAYLOAD["configuration_code"],  # noqa: F405
            "version": POST_PAYLOAD["version"],  # noqa: F405
            "channel": POST_PAYLOAD["channel"],  # noqa: F405
            "is_package": POST_PAYLOAD["is_package"],  # noqa: F405
            "access_token": TOKEN,  # noqa: F405
        }
        celery_task.options_object = options_object
        celery_task.save()
        return celery_task

    @mock.patch("poms.configuration.tasks.requests.post")
    def test__check_dependencies_handling_http_error(self, requests_post):
        self.mock_response.status_code = 403
        self.mock_response.text = self.random_string()
        requests_post.return_value = self.mock_response

        all_tasks_before = CeleryTask.objects.all()
        self.assertEqual(all_tasks_before.count(), 0)

        celery_task = self.create_celery_task()

        with self.assertRaises(RuntimeError) as error:
            install_package_from_marketplace(task_id=celery_task.id)

        self.assertEqual(str(error.exception), self.mock_response.text)

        all_tasks_after = CeleryTask.objects.all()
        self.assertEqual(all_tasks_after.count(), 1)

    @mock.patch("poms.configuration.tasks.install_configuration_from_marketplace")
    @mock.patch("poms.configuration.tasks.requests.post")
    @mock.patch("poms.configuration.utils.get_workflow")
    def test__check_dependencies_handling_no_http_error(self, get_workflow, requests_post, install_config):
        self.mock_response.json.return_value = deepcopy(PACKAGE_RESPONSE_JSON)  # noqa: F405
        requests_post.return_value = self.mock_response

        all_tasks_before = CeleryTask.objects.all()
        self.assertEqual(all_tasks_before.count(), 0)

        main_task = self.create_celery_task()

        install_package_from_marketplace(task_id=main_task.id)

        all_tasks_after = CeleryTask.objects.all()
        self.assertEqual(all_tasks_after.count(), 3)

        self.assertEqual(install_config.call_count, 2)

        main_task.refresh_from_db()
        self.assertEqual(main_task.progress_object, EXPECTED_PROGRESS_OBJECT)  # noqa: F405

        conf = Configuration.objects.get(configuration_code=CONFIGURATION_CODE)  # noqa: F405
        self.assertEqual(conf.name, PACKAGE_RESPONSE_JSON["configuration_object"]["name"])  # noqa: F405
        self.assertEqual(
            conf.description,
            PACKAGE_RESPONSE_JSON["configuration_object"]["description"],  # noqa: F405
        )
        self.assertEqual(conf.version, PACKAGE_RESPONSE_JSON["version"])  # noqa: F405
        self.assertEqual(conf.manifest, PACKAGE_RESPONSE_JSON["manifest"])  # noqa: F405
        self.assertTrue(conf.is_package)
        self.assertTrue(conf.is_from_marketplace)
        self.assertEqual(get_workflow.call_count, 1)
