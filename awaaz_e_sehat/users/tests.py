from django.test import TestCase
from django.contrib.auth import get_user_model


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
