from django import forms
from .models import *
from django.contrib.auth import get_user_model

class ArtistProfileForm(forms.ModelForm):
    class Meta:
        model = ArtistProfile
        fields = ['bio', 'avatar', 'email_contact', 'facebook', 'instagram', 'twitter', 'youtube', 'phone']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 5}),
        }

class FanProfileForm(forms.ModelForm):
    class Meta:
        model = FanProfile
        fields = ['avatar', 'bio', 'facebook', 'instagram', 'twitter', 'youtube', 'tiktok']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

User = get_user_model()

class FanUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ['name']

class AlbumForm(forms.ModelForm):
    genre = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = Album
        fields = ['title', 'songs', 'genre']


class WalletProfileForm(forms.ModelForm):
    class Meta:
        model = WalletProfile
        fields = [
            'address',
            'network',
            'wallet_label',
        ]
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control funding-input',
                'placeholder': 'Ingresa tu address IOTA'
            }),
            'network': forms.Select(attrs={
                'class': 'form-select funding-input'
            }),
            'wallet_label': forms.TextInput(attrs={
                'class': 'form-control funding-input',
                'placeholder': 'Ej: Wallet principal'
            }),
        }


class KYCProfileForm(forms.ModelForm):
    class Meta:
        model = KYCProfile
        fields = [
            'verification_level',
            'country_code',
            'document_country',
            'document_type',
            'consent_accepted',
        ]
        widgets = {
            'verification_level': forms.Select(attrs={
                'class': 'form-select funding-input'
            }),
            'country_code': forms.TextInput(attrs={
                'class': 'form-control funding-input',
                'placeholder': 'Ej: EC'
            }),
            'document_country': forms.TextInput(attrs={
                'class': 'form-control funding-input',
                'placeholder': 'Ej: EC'
            }),
            'document_type': forms.TextInput(attrs={
                'class': 'form-control funding-input',
                'placeholder': 'Cédula / Pasaporte'
            }),
            'consent_accepted': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


        