from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import F
from .models import UserReviews, UserReviewsImage, User, UserReviewsComment, Menu
from .forms import UserReviewsForm, UserReviewsImageForm
from django.http import JsonResponse

# 리뷰 목록 보기
def userreviews_list(request):
    query = request.GET.get("query", "").strip()
    sort = request.GET.get("sort", "latest")
    userreviews = UserReviews.objects.all()

    if query:
        userreviews = userreviews.filter(menu__menu_name__icontains=query)

    sort_options = {
        "views": "-views",
        "rating": "-rating",
        "latest": "-created_at"
    }
    userreviews = userreviews.order_by(sort_options.get(sort, "-created_at"))

    return render(request, "review/userreviews_list.html", {"userreviews": userreviews, "query": query, "sort": sort})

# 리뷰 상세 보기
def userreviews_detail(request, pk):
    userreviews = get_object_or_404(UserReviews, pk=pk)
    UserReviews.objects.filter(pk=pk).update(views=F("views") + 1)
    return render(request, "review/userreviews_detail.html", {"userreviews": userreviews})

# 리뷰 작성
@login_required
def userreviews_create(request):
    if request.method == "POST":
        form = UserReviewsForm(request.POST)
        image_form = UserReviewsImageForm(request.POST, request.FILES)
        if form.is_valid():
            userreviews = form.save(commit=False)
            userreviews.user = request.user
            userreviews.save()
            return redirect("userreviews_detail", pk=userreviews.pk)
    else:
        form = UserReviewsForm()
    return render(request, "review/userreviews_form.html", {"form": form})

# 리뷰 수정
@login_required
def userreviews_update(request, pk):
    userreviews = get_object_or_404(UserReviews, pk=pk, user=request.user)
    if request.method == "POST":
        form = UserReviewsForm(request.POST, instance=userreviews)
        if form.is_valid():
            form.save()
            return redirect("userreviews_detail", pk=pk)
    else:
        form = UserReviewsForm(instance=userreviews)
    return render(request, "review/userreviews_form.html", {"form": form, "userreviews": userreviews})