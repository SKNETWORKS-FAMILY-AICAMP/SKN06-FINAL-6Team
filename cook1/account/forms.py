from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Users
from django.contrib.auth.hashers import make_password

class CustomUserCreationForm(forms.ModelForm):
    """회원가입 폼 (Users 모델 기반)"""
    login_id = forms.CharField(max_length=50, required=True, label="로그인 ID")
    email = forms.EmailField(required=True, label="이메일")
    name = forms.CharField(max_length=50, required=True, label="이름")
    nickname = forms.CharField(max_length=30, required=True, label="별명")
    birthday = forms.DateField(required=True, label="생년월일", widget=forms.DateInput(attrs={'type': 'date'}))
    user_photo = forms.ImageField(required=False, label="프로필 사진")

    # ✅ Users 모델에는 없지만, 폼에서만 사용할 필드
    password1 = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(attrs={"placeholder": "비밀번호 입력"}),
        required=True
    )
    password2 = forms.CharField(
        label="비밀번호 확인",
        widget=forms.PasswordInput(attrs={"placeholder": "비밀번호 확인"}),
        required=True
    )

    class Meta:
        model = Users
        fields = ("login_id", "email", "name", "nickname", "birthday", "user_photo")  # ✅ `password1`, `password2` 제거

    def clean(self):
        """비밀번호 확인 로직 추가"""
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")

        return cleaned_data

    def save(self, commit=True):
        """비밀번호를 해싱하여 저장"""
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password1"])  # ✅ 비밀번호 해싱 후 저장
        if commit:
            user.save()
        return user

# 아이디 찾기 폼
class FindIDForm(forms.Form):
    name = forms.CharField(label="이름", max_length=100, widget=forms.TextInput(attrs={"placeholder": "이름"}))
    email = forms.EmailField(label="이메일", widget=forms.EmailInput(attrs={"placeholder": "이메일"}))

# 비밀번호 찾기 폼
class FindPWForm(forms.Form):
    login_id = forms.CharField(label="아이디", max_length=150, widget=forms.TextInput(attrs={"placeholder": "아이디"}))
    name = forms.CharField(label="이름", max_length=100, widget=forms.TextInput(attrs={"placeholder": "이름"}))
    email = forms.EmailField(label="이메일", widget=forms.EmailInput(attrs={"placeholder": "이메일"}))

# 정보 수정 폼
class UserUpdateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Users
        fields = ['nickname', 'user_photo']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

# 이메일 인증 폼 (6자리 인증번호 입력)
class EmailVerificationForm(forms.Form):
    code = forms.CharField(
        label="인증번호",
        max_length=6,
        widget=forms.TextInput(attrs={"placeholder": "인증번호 입력"})
    )


# 비밀번호 재설정 폼
class PasswordResetForm(forms.Form):
    password = forms.CharField(
        label="새 비밀번호",
        widget=forms.PasswordInput(attrs={"placeholder": "새 비밀번호"}),
        required=True
    )
    confirm_password = forms.CharField(
        label="비밀번호 확인",
        widget=forms.PasswordInput(attrs={"placeholder": "비밀번호 확인"}),
        required=True
    )

    def clean(self):
        """비밀번호 일치 여부 확인"""
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")

        return cleaned_data
