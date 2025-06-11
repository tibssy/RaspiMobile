from django.test import TestCase, Client
from django.urls import reverse
from .models import ShippingAddress
from .forms import ShippingAddressForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import resolve_url


class ManageProfileViewTests(TestCase):
    def setUp(self):
        """
        Set up the test environment.
        """

        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        self.manage_profile_url = reverse('manage_profile')

    def test_manage_profile_view_loads_ok(self):
        """
        Test that the manage profile page loads with a 200 status code.
        """

        self.client.login(username='testuser', password='password')
        response = self.client.get(self.manage_profile_url)
        self.assertEqual(response.status_code, 200)

    def test_manage_profile_view_uses_correct_template(self):
        """
        Test that the manage profile view uses the correct template.
        """

        self.client.login(username='testuser', password='password')
        response = self.client.get(self.manage_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profiles/manage_profile.html')
        self.assertTemplateUsed(response, 'base.html')

    def test_manage_profile_view_requires_login(self):
        """
        Test that the manage profile view requires login.
        """

        response = self.client.get(self.manage_profile_url)
        self.assertEqual(response.status_code, 302)
        login_url = reverse('account_login')
        expected_url = f"{login_url}?next={self.manage_profile_url}"
        self.assertRedirects(response, expected_url)

    def test_manage_profile_view_displays_existing_address(self):
        """
        Test that the manage profile view displays an existing
        shipping address.
        """

        self.client.login(username='testuser', password='password')
        ShippingAddress.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            city='Test City',
            zipcode='12345',
            country='Test Country'
        )
        response = self.client.get(self.manage_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(
            response.context['address_form'],
            ShippingAddressForm
        )
        self.assertTrue(response.context['existing_address'])
        self.assertEqual(
            response.context['address_form'].instance.full_name,
            'Test User'
        )

    def test_manage_profile_view_displays_empty_form_if_no_address(self):
        """
        Test that the manage profile view displays an empty form if
        no address exists.
        """

        self.client.login(username='testuser', password='password')
        response = self.client.get(self.manage_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(
            response.context['address_form'],
            ShippingAddressForm
        )
        self.assertFalse(response.context['existing_address'])

    def test_manage_profile_view_can_add_address(self):
        """
        Test that the manage profile view can add a new shipping address.
        """

        self.client.login(username='testuser', password='password')
        form_data = {
            'full_name': 'New User',
            'email': 'new@example.com',
            'address1': '456 New St',
            'city': 'New City',
            'zipcode': '67890',
            'country': 'New Country'
        }

        response = self.client.post(self.manage_profile_url, data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ShippingAddress.objects.count(), 1)
        address = ShippingAddress.objects.first()
        self.assertEqual(address.user, self.user)
        self.assertEqual(address.full_name, 'New User')
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(
            str(messages_list[0]),
            'Shipping address saved successfully.'
        )

    def test_manage_profile_view_can_edit_address(self):
        """
        Test that the manage profile view can edit an existing
        shipping address.
        """

        self.client.login(username='testuser', password='password')
        address = ShippingAddress.objects.create(
            user=self.user,
            full_name='Old User',
            email='old@example.com',
            address1='789 Old St',
            city='Old City',
            zipcode='00000',
            country='Old Country'
        )
        form_data = {
            'full_name': 'Updated User',
            'email': 'updated@example.com',
            'address1': 'Updated Address',
            'city': 'Updated City',
            'zipcode': '11111',
            'country': 'Updated Country'
        }

        response = self.client.post(self.manage_profile_url, data=form_data)
        self.assertEqual(response.status_code, 302)
        address.refresh_from_db()
        self.assertEqual(address.full_name, 'Updated User')
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(
            str(messages_list[0]),
            'Shipping address updated successfully.'
        )

    def test_manage_profile_view_form_invalid(self):
        """
        Test that the manage profile view handles invalid form data.
        """

        self.client.login(username='testuser', password='password')
        form_data = {
            'full_name': 'A',
            'email': 'invalid-email',
            'address1': '',
            'city': '',
            'zipcode': '',
            'country': ''
        }

        response = self.client.post(self.manage_profile_url, data=form_data)
        self.assertEqual(response.status_code, 200)
        form = response.context['address_form']
        self.assertFormError(form, 'full_name', 'Full name seems too short.')
        self.assertFormError(form, 'email', 'Enter a valid email address.')
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(
            str(messages_list[0]),
            'Please correct the errors below.'
        )


class DeleteAccountViewTests(TestCase):
    def setUp(self):
        """
        Set up the test environment.
        """

        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )
        self.delete_account_url = reverse('delete_account')

    def test_delete_account_view_requires_login(self):
        """
        Test that the delete account view requires login.
        """

        response = self.client.post(self.delete_account_url)
        self.assertEqual(response.status_code, 302)
        login_url = reverse('account_login')
        expected_url = f"{login_url}?next={self.delete_account_url}"
        self.assertRedirects(response, expected_url)

    def test_delete_account_view_deletes_account(self):
        """
        Test that the delete account view deletes the user's account.
        """

        self.client.login(username='testuser', password='password')
        self.assertEqual(User.objects.count(), 1)
        response = self.client.post(self.delete_account_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), 0)
        self.assertRedirects(response, resolve_url('home'))
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(
            str(messages_list[0]),
            'Your account has been successfully deleted.'
        )

    def test_delete_account_view_redirects_get_request(self):
        """
        Test that the delete account view redirects GET requests.
        """

        self.client.login(username='testuser', password='password')
        response = self.client.get(self.delete_account_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, resolve_url('manage_profile'))
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), 'Invalid request method.')


class ShippingAddressFormTests(TestCase):
    def test_shipping_address_form_valid_data(self):
        """
        Test that the shipping address form is valid with valid data.
        """

        form_data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'address1': '123 Test St',
            'city': 'Test City',
            'zipcode': '12345',
            'country': 'Test Country'
        }

        form = ShippingAddressForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_shipping_address_form_invalid_data(self):
        """
        Test that the shipping address form is invalid with invalid data.
        """

        form_data = {
            'full_name': 'A',
            'email': 'invalid-email',
            'address1': '',
            'city': '',
            'zipcode': '',
            'country': ''
        }

        form = ShippingAddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('full_name', form.errors)
        self.assertIn('email', form.errors)

    def test_shipping_address_form_requires_state_for_us(self):
        """
        Test that the shipping address form requires 'state' for US addresses.
        """

        form_data = {
            'full_name': 'Test User',
            'email': 'test@example.com',
            'address1': '123 Test St',
            'city': 'Test City',
            'zipcode': '12345',
            'country': 'United States',
            'state': ''
        }

        form = ShippingAddressForm(data=form_data)
        self.assertFalse(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(len(form.errors), 1)
        self.assertIn('state', form.errors)
        self.assertEqual(
            form.errors['state'][0],
            'State is required for shipments within the United States.'
        )


class ShippingAddressModelTests(TestCase):
    def setUp(self):
        """
        Set up the test environment.
        """

        self.user = User.objects.create_user(
            username='testuser',
            password='password'
        )

    def test_shipping_address_creation(self):
        """
        Test that a shipping address can be created.
        """

        address = ShippingAddress.objects.create(
            user=self.user,
            full_name='Test User',
            email='test@example.com',
            address1='123 Test St',
            city='Test City',
            zipcode='12345',
            country='Test Country'
        )
        self.assertEqual(address.full_name, 'Test User')
        self.assertEqual(address.user, self.user)
        self.assertEqual(
            str(address),
            'Test User, 123 Test St, Test City (testuser)'
        )

    def test_shipping_address_verbose_name_plural(self):
        """
        Test the verbose name plural for the ShippingAddress model.
        """

        self.assertEqual(
            str(ShippingAddress._meta.verbose_name_plural),
            'User Profile Shipping Addresses'
        )
