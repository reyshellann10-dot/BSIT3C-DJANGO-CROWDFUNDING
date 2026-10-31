from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    def test_home_renders_for_guest(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_home_redirects_authenticated_user_to_portal(self):
        user = get_user_model().objects.create_user(
            username='maria', password='secret1234'
        )

        self.client.force_login(user)
        response = self.client.get(reverse('home'))

        self.assertRedirects(response, '/campaigns/portal/')

    def test_home_redirects_staff_to_admin_dashboard(self):
        user = get_user_model().objects.create_user(
            username='admin', password='secret1234', is_staff=True
        )

        self.client.force_login(user)
        response = self.client.get(reverse('home'))

        self.assertRedirects(response, '/campaigns/')
