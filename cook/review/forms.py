from django import forms
from .models import UserReviews

class ReviewForm(forms.ModelForm):
    class Meta:
        model = UserReviews
        fields = ['selected_menu', 'review_text', 'rating']  
        widgets = {
            "selected_menu": forms.TextInput(attrs={"placeholder": "메뉴명을 입력하세요."}),
            "rating": forms.NumberInput(attrs={
                "placeholder": "별점을 입력하세요. (1~5)",
                "step": "0.5",
                "min": "0.5",
                "max": "5",
                "style": "width: 80px;",
            }),
            "review_text": forms.Textarea(attrs={"placeholder": "요리의 난이도, 맛, 소요시간 등 후기를 작성해주세요."}),
        }
        labels = {
            "selected_menu": "메뉴명",
            "rating": "별점",
            "review_text": "내용",
        }
