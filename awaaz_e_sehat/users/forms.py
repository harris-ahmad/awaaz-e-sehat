'''
This file contains the forms for the users app.

CustomUserCreationForm:
-----------------------
> This form is used to create a new user.
> It inherits from the UserCreationForm class of django.contrib.auth.forms

CustomUserChangeForm:
---------------------
> This form is used to update the user details.
> It inherits from the UserChangeForm class of django.contrib.auth.forms
'''


from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'username',)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'username',)
