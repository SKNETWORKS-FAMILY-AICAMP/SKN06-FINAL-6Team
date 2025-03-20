from django import forms
from .models import UserReviews, UserSelectedMenus

class ReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # 🔥 현재 로그인한 사용자 가져오기
        super().__init__(*args, **kwargs)
        if user:
            self.fields['selected_menu'].queryset = UserSelectedMenus.objects.filter(user=user)  # ✅ 현재 유저의 메뉴만 표시

    class Meta:
        model = UserReviews
        fields = ['selected_menu', 'review_text', 'rating']
        widgets = {
            "rating": forms.NumberInput(attrs={
                "placeholder": "별점을 입력하세요. (1~5)",
                "step": "0.5",
                "min": "0.5",
                "max": "5",
                "style": "width: 80px;",
            }),
            "review_text": forms.Textarea(attrs={"placeholder": "요리의 난이도, 맛, 소요시간 등 후기를 작성해주세요."}),
        }
