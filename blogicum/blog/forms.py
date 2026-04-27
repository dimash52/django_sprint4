from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Discussion, Article

User = get_user_model()


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ('title', 'text', 'pub_date', 'category', 'location', 'image')


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ('text',)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
