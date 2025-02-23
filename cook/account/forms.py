from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    full_name = forms.CharField(max_length=50, required=True, label="이름")
    nickname = forms.CharField(max_length=30, required=True, label="별명")
    birthdate = forms.DateField(required=True, label="생년월일", widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = CustomUser
        fields = ("username", "email", "full_name", "nickname", "birthdate", "password1", "password2")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")

        return cleaned_data
# 아이디 찾기 폼 (이름 + 이메일 입력)
class FindIDForm(forms.Form):
    full_name = forms.CharField(label="이름", max_length=100)
    email = forms.EmailField(label="이메일")

# 비밀번호 찾기 폼 (아이디 + 이름 + 이메일 입력)
class FindPWForm(forms.Form):
    username = forms.CharField(label="아이디", max_length=150)
    full_name = forms.CharField(label="이름", max_length=100)
    email = forms.EmailField(label="이메일")

# 이메일 인증 폼 (6자리 인증번호 입력)
class EmailVerificationForm(forms.Form):
    email = forms.EmailField(label="이메일")
    code = forms.CharField(label="인증번호", max_length=6)