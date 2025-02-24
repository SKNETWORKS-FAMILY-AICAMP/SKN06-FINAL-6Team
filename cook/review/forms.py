from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["menu_name", "rating", "content"]
        widgets = {
            "menu_name": forms.TextInput(attrs={"placeholder": "메뉴명을 입력하세요."}),
            "rating": forms.NumberInput(attrs={
                "placeholder": "별점을 입력하세요. (0.5~5)",
                "step": "0.5",
                "min": "0.5",
                "max": "5",
                "style": "width: 80px;",
            }),
            "content": forms.Textarea(attrs={"placeholder": "요리의 난이도, 맛, 소요시간 등 후기를 작성해주세요."}),
        }
        labels = {
            "menu_name": "메뉴명",
            "rating": "별점",
            "content": "내용",
        }