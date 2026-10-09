from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


def use_placeholders(form):
    """The login card has no visible labels, so each field shows its label as a placeholder."""
    for field in form.fields.values():
        field.widget.attrs.update({'placeholder': field.label, 'aria-label': field.label})


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        use_placeholders(self)


class RegisterForm(UserCreationForm):
    """Sign up with a username, email and password."""
    email = forms.EmailField(label='Email', required=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password2'].label = 'Confirm password'
        use_placeholders(self)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'bio', 'avatar')
        widgets = {'bio': forms.Textarea(attrs={'rows': 3, 'maxlength': 280})}
