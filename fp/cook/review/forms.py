from django import forms
from .models import UserReviews, UserReviewsImage, UserReviewsComment


class UserReviewsForm(forms.ModelForm):
    db_source = forms.ChoiceField(choices=[("funs", "편스토랑"), ("mans", "만개의 레시피"), ("fridge", "냉장고를 부탁해")])
    recipe_id = forms.IntegerField()

    class Meta:
        model = UserReviews
        fields = ["db_source", "recipe_id", "rating", "review_text"]
        widgets = {
            "menu": forms.TextInput(attrs={"placeholder": "메뉴명을 입력하세요."}),
            # "menu": forms.Select(),
            "rating": forms.NumberInput(attrs={
                "min": "0.5",
                "max": "5",
                "step": "0.5",
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

# 리뷰 좋아요 폼 추가 (ReviewComments 활용)
class ReviewLikeForm(forms.ModelForm):
    class Meta:
        model = UserReviewsComment
        fields = []  # 좋아요는 데이터 입력이 필요 없음