"""
Unit tests for the RaspiMobile 'home' application.

This module contains test cases for the views (`HomeView`, `AboutView`)
and potentially forms or other components within the home app, ensuring
they function as expected under various conditions.
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.messages import get_messages
from .forms import ContactForm


class HomeViewTests(TestCase):
    def setUp(self):
        """
        Set up the test client.
        """

        self.client = Client()
        self.home_url = reverse('home')

    def test_home_view_loads_ok(self):
        """
        Test that the home page loads with a 200 status code.
        """

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_uses_correct_template(self):
        """
        Test that the home view uses the 'home/index.html' template.
        """

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_home_view_context_keys_exist(self):
        """
        Test that expected context keys exist (without checking content).
        """

        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('featured_products', response.context)
        self.assertIn('best_rated_products', response.context)


@override_settings(EMAIL_HOST_USER='testsender@example.com')
class AboutViewTests(TestCase):

    def setUp(self):
        """
        Set up test client, URL, and form data.
        """

        self.client = Client()
        self.about_url = reverse('about')
        self.valid_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message.',
        }
        self.invalid_data = {
            'name': '',
            'email': 'not-a-valid-email',
            'subject': 'Invalid Test Subject',
            'message': 'Test message for invalid data.',
        }

    def test_about_view_loads_ok(self):
        """
        Test that the about page loads with a 200 status code.
        """

        response = self.client.get(self.about_url)
        self.assertEqual(response.status_code, 200)

    def test_about_view_uses_correct_template(self):
        """
        Test that the about view uses the 'home/about.html' template.
        """

        response = self.client.get(self.about_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/about.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_about_view_get_request_contains_contact_form(self):
        """
        Test that the about page context (GET) contains an unbound ContactForm.
        """

        response = self.client.get(self.about_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('contact_form', response.context)
        self.assertIsInstance(response.context['contact_form'], ContactForm)
        self.assertFalse(response.context['contact_form'].is_bound)

    def test_about_view_post_valid_data_redirects(self):
        """
        Test POSTing valid contact form data redirects successfully.
        """

        response = self.client.post(self.about_url, data=self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.about_url)

    def test_about_view_post_valid_data_shows_success_message(self):
        """
        Test POSTing valid data adds a success message.
        """

        response = self.client.post(
            self.about_url,
            data=self.valid_data, follow=True
        )
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, 'success')
        self.assertIn('Thank you for your message', str(messages[0]))
        self.assertContains(response, 'Thank you for your message')

    def test_about_view_post_invalid_data_reloads_page(self):
        """
        Test POSTing invalid contact form data re-renders the about page (200).
        """

        response = self.client.post(self.about_url, data=self.invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/about.html')

    def test_about_view_post_invalid_data_form_has_errors(self):
        """
        Test POSTing invalid data results in a bound form with errors.
        """

        response = self.client.post(self.about_url, data=self.invalid_data)
        self.assertEqual(response.status_code, 200)
        form = response.context['contact_form']
        self.assertTrue(form.is_bound)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.errors)
        self.assertIn('name', form.errors)
        self.assertIn('email', form.errors)

    def test_about_view_post_invalid_data_shows_error_message(self):
        """
        Test POSTing invalid data adds an error message.
        """

        response = self.client.post(self.about_url, data=self.invalid_data)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].level_tag, 'error')
        self.assertIn('Please correct the errors below', str(messages[0]))
        self.assertContains(response, 'Please correct the errors below')
