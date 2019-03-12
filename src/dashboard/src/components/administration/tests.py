import os

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.test import TestCase
from django.test.client import Client

from components import helpers
from components.administration.views_dip_upload import _AS_DICTNAME, _ATOM_DICTNAME
from main.models import DashboardSetting

import mock

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(THIS_DIR, '../../../tests/fixtures'))


class TestUploadDipAsConfigView(TestCase):
    fixture_files = ['test_user.json']
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')
        self.url = reverse('components.administration.views_dip_upload.admin_as')

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.request.get('PATH_INFO'), '/administration/dips/as/')
        self.assertTemplateUsed(response, 'administration/dips_as_edit.html')
        self.assertFalse(response.context['form'].is_valid())

    def test_post_minimum_required(self):
        response = self.client.post(self.url, {
            'host': 'aspace.test.org',
            'port': 8089,
            'user': 'admin',
            'premis': 'yes',
            'xlink_show': 'embed',
            'xlink_actuate': 'none',
            'uri_prefix': 'http://example.com',
            'repository': 2,
        })
        form = response.context['form']
        messages = list(response.context['messages'])
        config = DashboardSetting.objects.get_dict(_AS_DICTNAME)

        self.assertTrue(form.is_valid())
        self.assertFalse(form.errors)

        self.assertTrue(messages)
        self.assertEqual(messages[0].message, 'Saved.')
        self.assertEqual(messages[0].tags, 'info')

        self.assertIsInstance(config, dict)
        self.assertEqual(config['host'], 'aspace.test.org')
        self.assertEqual(config['port'], '8089')
        self.assertEqual(config['repository'], '2')
        self.assertEquals(len(config.keys()), len(form.fields))

    def test_post_missing_fields(self):
        response = self.client.post(self.url, {
            'host': 'aspace.test.org',
            'port': 8089,
        })
        form = response.context['form']
        config = DashboardSetting.objects.get_dict(_AS_DICTNAME)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

        self.assertFormError(response, 'form', 'user', 'This field is required.')
        self.assertFormError(response, 'form', 'premis', 'This field is required.')
        self.assertFormError(response, 'form', 'xlink_show', 'This field is required.')
        self.assertFormError(response, 'form', 'xlink_actuate', 'This field is required.')
        self.assertFormError(response, 'form', 'uri_prefix', 'This field is required.')
        self.assertFormError(response, 'form', 'repository', 'This field is required.')

        self.assertIsInstance(config, dict)
        self.assertFalse(config)


class TestUploadDipAtoMConfigView(TestCase):
    fixture_files = ['test_user.json']
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')
        self.url = reverse('components.administration.views_dip_upload.admin_atom')

    def test_get(self):
        response = self.client.get(self.url)

        self.assertEqual(response.request.get('PATH_INFO'), '/administration/dips/atom/')
        self.assertTemplateUsed(response, 'administration/dips_atom_edit.html')
        self.assertFalse(response.context['form'].is_valid())

    def test_post_minimum_required(self):
        response = self.client.post(self.url, {
            'url': 'https://search.efimm.org',
            'email': 'demo@example.com',
            'password': 'demo',
            'version': 2,
        })
        form = response.context['form']
        messages = list(response.context['messages'])
        config = DashboardSetting.objects.get_dict(_ATOM_DICTNAME)

        self.assertTrue(form.is_valid())
        self.assertFalse(form.errors)

        self.assertTrue(messages)
        self.assertEqual(messages[0].message, 'Saved.')
        self.assertEqual(messages[0].tags, 'info')

        self.assertIsInstance(config, dict)
        self.assertEqual(config['url'], 'https://search.efimm.org')
        self.assertEqual(config['email'], 'demo@example.com')
        self.assertEqual(config['password'], 'demo')
        self.assertEqual(config['version'], '2')
        self.assertEqual(config['key'], '')
        self.assertEquals(len(config.keys()), len(form.fields))

    def test_post_missing_fields(self):
        response = self.client.post(self.url, {
            'url': 'https://search.efimm.org',
        })
        form = response.context['form']
        config = DashboardSetting.objects.get_dict(_ATOM_DICTNAME)

        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)

        self.assertFormError(response, 'form', 'email', 'This field is required.')
        self.assertFormError(response, 'form', 'password', 'This field is required.')
        self.assertFormError(response, 'form', 'version', 'This field is required.')

        self.assertIsInstance(config, dict)
        self.assertFalse(config)


class TestProcessingConfig(TestCase):
    fixture_files = ['test_user.json']
    fixtures = [os.path.join(FIXTURES_DIR, p) for p in fixture_files]

    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='test')
        helpers.set_setting('dashboard_uuid', 'test-uuid')

    @staticmethod
    def send_file_404_mock(*args, **kwargs):
        raise Http404

    @staticmethod
    def send_file_ok_mock(*args, **kwargs):
        DEFAULT = '<!DOCTYPE _[<!ELEMENT _ EMPTY>]><_/>'
        return HttpResponse(DEFAULT)

    def test_download_404(self):
        with mock.patch('components.helpers.send_file',
                        side_effect=self.send_file_404_mock):
            response = self.client.get(reverse(
                'components.administration.views_processing.download',
                args=['default']))

        self.assertEquals(response.status_code, 404)

    def test_download_ok(self):
        with mock.patch('components.helpers.send_file',
                        side_effect=self.send_file_ok_mock):
            response = self.client.get(reverse(
                'components.administration.views_processing.download',
                args=['default']))

        self.assertEquals(
            response.content,
            '<!DOCTYPE _[<!ELEMENT _ EMPTY>]><_/>')

    def test_edit_new_config(self):
        url = reverse("components.administration.views_processing.edit")
        response = self.client.get(url)

        self.assertEquals(url, "/administration/processing/add/")
        self.assertEquals(response.status_code, 200)
        self.assertNotIn("name", response.context["form"].initial)

    @mock.patch('components.administration.forms.'
                'ProcessingConfigurationForm.load_config')
    def test_edit_not_found_config(self, load_config):
        load_config.side_effect = IOError()
        url = reverse(
            "components.administration.views_processing.edit",
            args=["not_found_config"])
        response = self.client.get(url)

        self.assertEquals(url, "/administration/processing/"
                               "edit/not_found_config/")
        self.assertEquals(response.status_code, 404)
        load_config.assert_called_once_with("not_found_config")

    @mock.patch('components.administration.forms.'
                'ProcessingConfigurationForm.load_config')
    def test_edit_found_config(self, load_config):
        response = self.client.get(reverse(
            "components.administration.views_processing.edit",
            args=["found_config"]))

        self.assertEquals(response.status_code, 200)
        load_config.assert_called_once_with("found_config")
