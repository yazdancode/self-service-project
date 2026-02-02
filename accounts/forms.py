from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from accounts.models import User


class CustomAuthenticationForm(forms.Form):
    student_id = forms.CharField(
        max_length=10,
        label="شناسه کاربر",
        widget=forms.TextInput(attrs={"placeholder": "نام کاربری"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "رمز عبور"}), label="رمز عبور"
    )
    user_cache = None

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        student_id = cleaned_data.get("student_id")
        password = cleaned_data.get("password")

        if student_id and password:
            user = authenticate(
                username=student_id, password=password, request=self.request
            )
            if user is None:
                raise ValidationError("شناسه دانشجویی یا رمز عبور اشتباه است")
            self.user_cache = user

        return cleaned_data

    def get_user(self):
        return self.user_cache


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="رمز عبور")
    confirm_password = forms.CharField(
        widget=forms.PasswordInput, label="تکرار رمز عبور"
    )

    class Meta:
        model = User
        fields = ["student_id"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_type = None

    def clean_student_id(self):
        student_id = self.cleaned_data.get("student_id")

        if not student_id.isdigit():
            raise forms.ValidationError("شناسه باید فقط عدد باشد")

        if len(student_id) == 10:
            self.user_type = User.Role.STUDENT
        elif len(student_id) == 9:
            self.user_type = User.Role.OSTAD
        else:
            raise forms.ValidationError("شناسه باید ۹ یا ۱۰ رقم باشد")

        if User.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError("این شناسه قبلاً ثبت شده است")

        return student_id

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("رمز عبور و تکرار آن یکسان نیستند")
        return cleaned_data
