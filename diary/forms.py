from typing import Any

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from diary.models import Entry


class EntryForm(forms.ModelForm):
    """Форма создания/редактирования записи."""

    class Meta:
        model = Entry
        fields = ('title', 'content')
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Заголовок записи'},
            ),
            'content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Текст...'},
            ),
        }


class RegisterForm(UserCreationForm):
    """Регистрация с обязательным email."""

    email = forms.EmailField(required=True, widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'email@example.com'},
    ))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Логин'},
        )
        for name in ('password1', 'password2'):
            self.fields[name].widget.attrs.update({'class': 'form-control'})
