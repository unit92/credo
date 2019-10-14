from django import forms
from django.contrib.auth.models import User


class SignUpForm(forms.ModelForm):
    username = forms.CharField(label='username', max_length=100,
                               required=True, help_text='Test')
    password = forms.CharField(label='password', required=True,
                               help_text='PassTest')
    password_confirm = forms.CharField(label='confirm password',
                                       required=True)
    email = forms.EmailField(max_length=254, help_text='Required Test')

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("username")
        password_confirmation = cleaned_data.get("password_confirmation")
        if(password != password_confirmation):
            raise forms.ValidationError("Passwords do not match")
