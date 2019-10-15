from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):

    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput)

    # Override label suffix for djangos authentication model
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(LoginForm, self).__init__(*args, **kwargs)


class SignUpForm(forms.ModelForm):
    username = forms.CharField(label='Username', max_length=100)
    email = forms.EmailField(label='Email', max_length=254,
                             widget=forms.TextInput(
                                attrs={'class': 'validate',
                                       'type': 'email'}))

    password = forms.CharField(label='Password',
                               widget=forms.PasswordInput)

    password_confirm = forms.CharField(label='Confirm Password',
                                       widget=forms.PasswordInput)

    # Override label suffix  (Changes label text from 'text:' -> 'text')
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(SignUpForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirm")

        if(password and password_confirmation and
           password != password_confirmation):
            raise forms.ValidationError("Passwords do not match")
