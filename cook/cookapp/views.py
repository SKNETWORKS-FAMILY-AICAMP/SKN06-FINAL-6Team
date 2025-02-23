from django.shortcuts import render

# 홈 화면 뷰 수정
def home(request):
    return render(request, 'cook/home.html')  # home.html을 렌더링하도록 수정
