import mock
import os

from django.conf import settings
from django.test import TestCase

from components import helpers

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


class TestAdministrationUsage(TestCase):
    fixtures = [os.path.join(THIS_DIR, "fixtures", "test_user.json")]

    def setUp(self):
        self.client.login(username="test", password="test")
        helpers.set_setting("dashboard_uuid", "test-uuid")

    def test_no_calculation(self):
        response = self.client.get("/administration/usage/")
        self.assertFalse(response.context["calculate_usage"])
        self.assertIn('<a href="?calculate=true"', response.content)
        self.assertIn("Calculate disk usage", response.content)

    @mock.patch(
        "components.administration.views._usage_get_directory_used_bytes",
        return_value=5368709120,
    )
    @mock.patch(
        "components.administration.views._usage_check_directory_volume_size",
        return_value=10737418240,
    )
    @mock.patch(
        "components.administration.views._get_mount_point_path", return_value="/"
    )
    def test_calculation(self, mock_mount_path, mock_dir_size, mock_dir_used):
        response = self.client.get("/administration/usage/?calculate=true")
        self.assertTrue(response.context["calculate_usage"])
        mock_mount_path.assert_called_once_with(settings.SHARED_DIRECTORY)
        mock_dir_size.assert_called_once_with("/")
        self.assertEqual(mock_dir_used.call_count, 9)
