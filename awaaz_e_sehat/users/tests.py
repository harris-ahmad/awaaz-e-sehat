from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse, resolve

from .forms import CustomUserCreationForm
from .views import SignupPageView


class CustomUserTests(TestCase):
    '''
    Tests for CustomUser model
    '''

    def test_create_user(self):
        '''
        Tests creating a new user
        '''
        User = get_user_model()
        user = User.objects.create_user(
            username='bakhtawar',
            email='bakhtwar09@gmail.com',
            password='helloBakhti123'
        )

        self.assertEqual(user.username, 'bakhtawar')
        self.assertEqual(user.email, 'bakhtwar09@gmail.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        '''
        Tests creating a new superuser
        '''
        User = get_user_model()
        superuser = User.objects.create_superuser(
            username='superadmin',
            email='admin@awaaz_e_sehat.com',
            password='admin123'
        )

        self.assertEqual(superuser.username, 'superadmin')
        self.assertEqual(superuser.email, 'admin@awaaz_e_sehat.com')
        self.assertTrue(superuser.is_active)
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)


class SignupPageTests(TestCase):
    '''
    Tests for Signup page
    '''

    def setUp(self):
        url = reverse('signup')
        self.response = self.client.get(url)

    def test_signup_template(self):
        '''
        Tests that the signup page uses the correct template
        '''
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, 'signup.html')
        self.assertContains(self.response, 'Sign Up')
        self.assertNotContains(
            self.response, 'Hi there! I should not be on the page.')
        
    def test_signup_form(self):
        '''
        Tests that the signup page contains a form
        '''
        form = self.response.context.get('form')
        self.assertIsInstance(form, CustomUserCreationForm)
        self.assertContains(self.response, 'csrfmiddlewaretoken')

    def test_signup_view(self):
        view = resolve('/accounts/signup/')
        self.assertEqual(
            view.func.__name__,
            SignupPageView.as_view().__name__
        )