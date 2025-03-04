from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UserChangeForm
from .models import Users


# 회원가입 폼 (CustomUser 모델 기반)
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = Users
        fields = ['login_id', 'email', 'nickname', 'birthdate', 'user_photo', 'full_name', 'password']
    
    def clean_email(self):
        """이메일 중복 체크"""
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

    def clean_nickname(self):
        """닉네임 중복 체크"""
        nickname = self.cleaned_data.get('nickname')
        if Users.objects.filter(nickname=nickname).exists():
            raise forms.ValidationError("이미 사용 중인 닉네임입니다.")
        return nickname
    
    def clean_login_id(self):
        """닉네임 중복 체크"""
        login_id = self.cleaned_data.get('login_id')
        if Users.objects.filter(login_id=login_id).exists():
            raise forms.ValidationError("이미 사용 중인 아이디디입니다.")
        return login_id
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        
        return password2

# 로그인 폼 (아이디 + 비밀번호)
class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="아이디", widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label="비밀번호", widget=forms.PasswordInput)


# 회원 정보 수정 폼 (비밀번호, 닉네임, 프로필 사진 변경 가능)
class UserUpdateForm(UserChangeForm):
    class Meta:
        model = Users
        fields = ['nickname', 'user_photo']
    
    password = None  # 기존 비밀번호 필드를 제거

    def clean_nickname(self):
        """닉네임 중복 체크"""
        nickname = self.cleaned_data.get('nickname')
        if Users.objects.exclude(pk=self.instance.pk).filter(nickname=nickname).exists():
            raise forms.ValidationError("이미 사용 중인 닉네임입니다.")
        return nickname


# 비밀번호 찾기 폼 (아이디 + 이메일 입력)
class FindIDForm(forms.Form):
    full_name = forms.CharField(label="이름", max_length=50)
    email = forms.EmailField(label="이메일")


class FindPWForm(forms.Form):
    login_id = forms.CharField(label="아이디", max_length=50)
    email = forms.EmailField(label="이메일")


# 이메일 인증 폼
class EmailVerificationForm(forms.Form):
    code = forms.CharField(label="인증번호", max_length=6)


# 비밀번호 재설정 폼
class PasswordResetForm(forms.Form):
    password = forms.CharField(label="새 비밀번호", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="새 비밀번호 확인", widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        
        return cleaned_data
