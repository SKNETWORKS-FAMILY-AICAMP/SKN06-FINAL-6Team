from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import F
from .models import UserReviews, UserReviewsImage, User, UserReviewsComment, Menu
from .forms import UserReviewsForm, UserReviewsImageForm
from django.http import JsonResponse
from chat.models import FridgeRecipes, FunsRecipes, ManRecipes
import sqlite3

# 리뷰 목록 보기
def userreviews_list(request):
    query = request.GET.get("query", "").strip()
    sort = request.GET.get("sort", "latest")
    userreviews = UserReviews.objects.all()

    if query:
        userreviews = userreviews.filter(recipe__name__icontains=query) 

    sort_options = {
        "views": "-views",
        "rating": "-rating",
        "latest": "-created_at"
    }
    userreviews = userreviews.order_by(sort_options.get(sort, "-created_at"))

    return render(request, "review/userreviews_list.html", {"userreviews": userreviews, "query": query, "sort": sort})

# 리뷰 상세 보기
def userreviews_detail(request, pk):
    user_review = get_object_or_404(UserReviews, pk=pk)
    Review.objects.filter(pk=pk).update(views=F('views') + 1)
    # 레시피 데이터 가져오기 (이전 SQL 방식 대신 ORM 사용)
    recipe_data = get_recipe_data(user_review)

    return render(request, "review/userreviews_detail.html", {
        "userreviews": user_review,
        "recipe": recipe_data  # 템플릿에서 사용 가능
    })

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

# 리뷰 좋아요 기능 (ReviewComments 테이블 활용)
@login_required
def review_like(request, pk):
    review = get_object_or_404(UserReviews, pk=pk)
    like, created = UserReviewsComment.objects.get_or_create(
        userreviews=review,
        user=request.user,
        like_type='review_like',
        defaults={'comment_text': None}  # 좋아요는 텍스트가 없음
    )

    if not created:
        like.delete()  # 이미 좋아요를 누른 경우 취소
        return JsonResponse({"like_count": UserReviewsComment.objects.filter(userreviews=review, like_type='review_like').count()})

    return JsonResponse({"like_count": UserReviewsComment.objects.filter(userreviews=review, like_type='review_like').count()})

def get_recipe_data(user_review):
    """UserReviews 모델의 recipe_id와 db_source를 사용하여 해당 레시피 데이터를 가져오는 함수"""
    db_source = user_review.db_source
    recipe_id = user_review.recipe_id

    if db_source == "fridge":
        return get_object_or_404(FridgeRecipes, recipe_id=recipe_id)
    elif db_source == "funs":
        return get_object_or_404(FunsRecipes, recipe_id=recipe_id)
    elif db_source == "mans":
        return get_object_or_404(ManRecipes, recipe_id=recipe_id)
    return None

def get_recipe_from_db(recipe_id, db_source):
    """레시피 데이터를 해당 DB에서 가져오는 함수"""
    db_paths = {
        "funs": "funs.db",
        "mans": "mans.db",
        "fridge": "fridge.db"
    }
    db_path = db_paths.get(db_source)

    if not db_path:
        return None  # 잘못된 db_source

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 각 DB에 맞는 테이블을 조회하도록 수정
    if db_source == "mans":
        query = "SELECT name, ingredients, recipe FROM processed_data WHERE id=?"
    elif db_source == "fridge":
        query = "SELECT name, ingredients, recipe FROM fridge_menu WHERE id=?"  
    elif db_source == "funs":
        query = "SELECT name, ingredients, recipe FROM funs_menu WHERE id=?"  
    else:
        return None

    cursor.execute(query, (recipe_id,))
    recipe = cursor.fetchone()
    conn.close()

    return recipe  # (name, ingredients, recipe)


