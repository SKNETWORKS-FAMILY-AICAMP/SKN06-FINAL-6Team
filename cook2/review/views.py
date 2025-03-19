from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
from .models import UserReviews, ReviewImages, Users, ReviewComments
from chat.models import UserSelectedMenus
from .forms import ReviewForm

# 리뷰 목록 보기 (검색 & 정렬)
def review_list(request):
    query = request.GET.get("query", "").strip()
    sort = request.GET.get("sort", "latest")

    reviews = UserReviews.objects.all()
    if query:
        reviews = reviews.filter(selected_menu__menu_name__icontains=query)  # ✅ 필드명 수정
    
    sort_options = {
        "views": "-views",
        "rating": "-rating",
        "latest": "-created_at"
    }
    reviews = reviews.order_by(sort_options.get(sort, "-created_at"))

    return render(request, "review_list.html", {"reviews": reviews, "query": query, "sort": sort})

# 리뷰 상세 보기 (조회수 증가)
def review_detail(request, pk):
    review = get_object_or_404(UserReviews, pk=pk)
    UserReviews.objects.filter(pk=pk).update(views=F("views") + 1)
    return render(request, "review_detail.html", {"review": review})

# 리뷰 작성 (다중 이미지 업로드 가능)
@login_required
def review_create(request):
    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES)
        files = request.FILES.getlist("images")

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user

            # 선택한 메뉴 정보 저장
            selected_menu_id = request.POST.get("selected_menu")
            if selected_menu_id:
                selected_menu = get_object_or_404(UserSelectedMenus, id=selected_menu_id, user=request.user)
                review.selected_menu = selected_menu
            review.save()

            for file in files:
                ReviewImages.objects.create(review=review, image_url=file)

            return redirect("review_detail", pk=review.pk)
    else:
        form = ReviewForm()

    # 현재 로그인한 사용자의 저장된 메뉴 리스트 가져오기
    menus = UserSelectedMenus.objects.filter(user=request.user)    
    
    return render(request, "review_form.html", {"form": form, "menus": menus})

# 리뷰 수정 (기존 이미지 유지 + 새 이미지 추가 가능)
@login_required
def review_update(request, pk):
    review = get_object_or_404(UserReviews, pk=pk, user=request.user)
    
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        files = request.FILES.getlist("images")
        
        if form.is_valid():
            form.save()
            for file in files:
                ReviewImages.objects.create(review=review, image_url=file)
            
            return redirect("review_detail", pk=pk)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, "review_form.html", {"form": form, "review": review})

# 특정 사용자의 리뷰 목록 조회
def user_reviews(request, username):
    user = get_object_or_404(Users, username=username)
    sort_option = request.GET.get('sort', 'created_at')

    reviews = UserReviews.objects.filter(user=user).order_by(
        {'views': '-views', 'rating': '-rating'}.get(sort_option, '-created_at')
    )

    return render(request, "user_reviews.html", {"reviews": reviews, "user": user, "sort_option": sort_option})

@login_required
def review_like(request, pk):
    review = get_object_or_404(UserReviews, pk=pk)
    like, created = ReviewComments.objects.get_or_create(
        review=review, user=request.user, like_type='review_like'
    )
    
    if not created:
        like.delete()
    
    likes_count = ReviewComments.objects.filter(review=review, like_type='review_like').count()
    return JsonResponse({"likes": likes_count})

@login_required
def add_comment(request, pk):
    review = get_object_or_404(UserReviews, pk=pk)
    
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            ReviewComments.objects.create(review=review, user=request.user, comment_text=content, like_type='comment')
    
    return redirect("review_detail", pk=pk)

@login_required
def delete_comment(request, pk):
    comment = get_object_or_404(ReviewComments, pk=pk, like_type='comment')
    if request.user == comment.user:
        comment.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "권한이 없습니다."}, status=403)

@login_required
def add_reply(request, comment_id):
    comment = get_object_or_404(ReviewComments, id=comment_id, like_type='comment')
    
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            ReviewComments.objects.create(review=comment.review, user=request.user, comment_text=content, like_type='comment', parent_id=comment.comment_id)
    
    return redirect("review_detail", pk=comment.review.pk)

@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(ReviewComments, id=reply_id, like_type='comment')
    if request.user == reply.user:
        reply.delete()
    return redirect("review_detail", pk=reply.review.pk)
