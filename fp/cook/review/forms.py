from django import forms
from .models import UserReviews, UserReviewsImage

class UserReviewsForm(forms.ModelForm):
    class Meta:
        model = UserReviews
        fields = ["menu", "rating", "review_text"]
        widgets = {
            "menu": forms.Select(),
            "rating": forms.NumberInput(attrs={
                "min": "1",
                "max": "5",
                "step": "1",
                "style": "width: 80px;",
            }),
            "review_text": forms.Textarea(attrs={"placeholder": "리뷰 내용을 입력하세요."}),
        }
        labels = {
            "menu": "메뉴",
            "rating": "별점",
            "review_text": "리뷰 내용",
        }

class UserReviewsImageForm(forms.ModelForm):
    class Meta:
        model = UserReviewsImage
        fields = ["image_url"]