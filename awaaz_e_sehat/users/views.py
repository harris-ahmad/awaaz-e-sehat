from django.urls import reverse_lazy
from django.views import generic
from .forms import CustomUserCreationForm


class SignupPageView(generic.CreateView):
    '''
    SignupPageView is a generic view that inherits from CreateView.
    It will display a form to create a User object and save it to the database.
    '''
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'