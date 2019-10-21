from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate


class LoginForm(AuthenticationForm):

    # Override label suffix for djangos authentication model
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(LoginForm, self).__init__(*args, **kwargs)

    # Override clean method, retaining source code & adjust error message only
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request,
                                           username=username,
                                           password=password)

            if self.user_cache is None:
                raise forms.ValidationError("Invalid login")
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


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
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        # Password validation
        if(password and password_confirmation and
           password != password_confirmation):
            raise forms.ValidationError("Passwords do not match")

        # Username validation
        if username and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")

        # Email validation
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is in use")
