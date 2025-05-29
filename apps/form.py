from django import forms
from django.core.exceptions import ValidationError
from django.forms import Form, CharField, ModelForm, PasswordInput, EmailField

from apps.models import Order, Payment
from apps.models import Stream
from apps.models import User


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['product', 'name', 'phone_number', 'region']

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        order = super().save(commit=False)
        if self.product:
            order.product = self.product
        if commit:
            order.save()
        return order


class StreamForm(ModelForm):
    class Meta:
        model = Stream
        fields = 'name', 'discount', 'product', 'user'


class EmailForm(Form):
    email = CharField(max_length=255)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        query = User.objects.filter(email=email)
        if query.exists():
            raise ValidationError(f'{email} exists')
        return email


class RegisterModelForm(ModelForm):
    password = CharField(widget=PasswordInput())
    password_confirm = CharField(widget=PasswordInput())
    sms = CharField(label='SMS Code')
    email = EmailField()

    class Meta:
        model = User
        fields = ['email', 'sms', 'password', 'password_confirm']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise ValidationError("Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(Form):
    email = CharField(max_length=255)
    password = CharField(max_length=255)


class ProfileUpdateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False, label="Yangi parol")
    password_confirm = forms.CharField(widget=forms.PasswordInput, required=False, label="Parolni tasdiqlang")

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and not password_confirm:
            raise forms.ValidationError("Parolni tasdiqlash kerak.")
        elif not password and password_confirm:
            raise forms.ValidationError("Parol kiritilmagan.")
        elif password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Parollar mos emas.")
        return cleaned_data


class ProfileModelForm(ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'address', 'district']


class UserPasswordChangeForm(forms.ModelForm):
    old_password = forms.CharField(widget=forms.PasswordInput, label='Eski parol')
    new_password_confirm = forms.CharField(widget=forms.PasswordInput, label='Parolni tasdiqlang')
    new_password = forms.CharField(widget=forms.PasswordInput, label='Yangi parol')

    class Meta:
        model = User
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')

        if new_password and new_password != new_password_confirm:
            raise forms.ValidationError("Yangi parollar mos emas!")
        return cleaned_data
class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['card_number', 'amount']