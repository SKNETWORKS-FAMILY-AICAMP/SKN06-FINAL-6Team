from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import F
from .models import Review, ReviewImage, User, ReviewLike, ReviewComment, Reply
from .forms import ReviewForm
from django.contrib.auth import get_user_model
from django.http import JsonResponse


User = get_user_model()

# 리뷰 목록 보기 (검색 & 정렬)
def review_list(request):
    query = request.GET.get("query", "").strip()  # 검색어 (메뉴명 검색)
    sort = request.GET.get("sort", "latest")  # 정렬 방식 (기본값: 최신순)

    reviews = Review.objects.all()

    if query:
        reviews = reviews.filter(menu_name__icontains=query)

    sort_options = {
        "views": "-views",
        "rating": "-rating",
        "latest": "-created_at"
    }
    reviews = reviews.order_by(sort_options.get(sort, "-created_at"))

    return render(request, "review/review_list.html", {"reviews": reviews, "query": query, "sort": sort})

# 리뷰 상세 보기 (조회수 증가)
def review_detail(request, pk):
    review = get_object_or_404(Review, pk=pk)
    Review.objects.filter(pk=pk).update(views=F("views") + 1)  # 조회수 증가
    return render(request, "review/review_detail.html", {"review": review})

# 리뷰 작성 (다중 이미지 업로드 가능)
@login_required
def review_create(request):
    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES)
        files = request.FILES.getlist("images")

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()

            # 다중 이미지 업로드 처리
            for file in files:
                ReviewImage.objects.create(review=review, image=file)

            return redirect("review_detail", pk=review.pk)  # ✅ 작성 후 상세 페이지로 이동
    else:
        form = ReviewForm()

    return render(request, "review/review_form.html", {"form": form})  # ✅ 올바른 템플릿 연결


# 리뷰 수정 (기존 이미지 유지 + 새 이미지 추가 가능)
@login_required
def review_update(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        files = request.FILES.getlist("images")

        if form.is_valid():
            form.save()

            for file in files:
                ReviewImage.objects.create(review=review, image=file)

            return redirect("review_detail", pk=pk)
    else:
        form = ReviewForm(instance=review)

    return render(request, "review/review_form.html", {"form": form, "review": review})

# 리뷰 삭제 (작성자만 가능)
@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        review.delete()
        return redirect("review_list")

    return render(request, "review/review_confirm_delete.html", {"review": review})

# 특정 사용자의 리뷰 목록 조회
def user_reviews(request, username):
    user = get_object_or_404(User, username=username)
    
    # 🔥 GET 파라미터에서 정렬 옵션 가져오기 (기본값: 최신순)
    sort_option = request.GET.get('sort', 'created_at')

    # 사용자가 선택한 옵션에 따라 정렬
    if sort_option == 'views':
        reviews = Review.objects.filter(user=user).order_by('-views')
    elif sort_option == 'rating':
        reviews = Review.objects.filter(user=user).order_by('-rating')
    else:  # 최신순 (기본값)
        reviews = Review.objects.filter(user=user).order_by('-created_at')

    return render(request, "review/user_reviews.html", {
        "reviews": reviews, 
        "user": user, 
        "sort_option": sort_option
    })

@login_required
def review_like(request, pk):
    """좋아요 기능"""
    review = get_object_or_404(Review, pk=pk)
    like, created = ReviewLike.objects.get_or_create(review=review, user=request.user)

    if not created:
        like.delete()  # 이미 좋아요 눌렀다면 삭제

    return JsonResponse({"likes": review.likes.count()})

@login_required
def add_comment(request, pk):
    """댓글 추가"""
    review = get_object_or_404(Review, pk=pk)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            ReviewComment.objects.create(review=review, user=request.user, content=content)
    
    return redirect("review_detail", pk=pk)

@login_required
def delete_comment(request, pk):
    """댓글 삭제"""
    comment = get_object_or_404(ReviewComment, pk=pk)

    if request.user == comment.user:
        comment.delete()
        return JsonResponse({"success": True}) # JSON 응답 반환 (AJAX와 연동됨)
    
    return JsonResponse({"error": "권한이 없습니다."}, status=403)

@login_required
def add_reply(request, comment_id):
    """대댓글 추가"""
    comment = get_object_or_404(ReviewComment, id=comment_id)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            Reply.objects.create(comment=comment, user=request.user, content=content)

    return redirect("review_detail", pk=comment.review.pk)

@login_required
def delete_reply(request, reply_id):
    """대댓글 삭제"""
    reply = get_object_or_404(Reply, id=reply_id)

    if request.user == reply.user:
        reply.delete()

    return redirect("review_detail", pk=reply.comment.review.pk)