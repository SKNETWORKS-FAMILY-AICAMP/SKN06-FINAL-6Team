from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import JsonResponse
from .models import UserReviews, ReviewImages, Users, ReviewComments
from chat.models import UserSelectedMenus
from .forms import ReviewForm
from django.db.models import Q
import os
from django.conf import settings
from django.urls import reverse

# 리뷰 목록 보기 (검색 & 정렬)
def review_list(request):
    query = request.GET.get("query", "").strip()
    sort = request.GET.get("sort", "latest")

    reviews = UserReviews.objects.select_related("user", "selected_menu").all()
    
    if query:
        reviews = reviews.filter(Q(selected_menu__menu_name__icontains=query) | Q(user__nickname__icontains=query))

    sort_options = {
        "views": "-views",
        "rating": "-rating",
        "latest": "-created_at" # (기본값)
    }
    reviews = reviews.order_by(sort_options.get(sort, "-created_at"))

    for review in reviews:
        print(f"📌 리뷰 ID: {review.review_id}, 별점: {review.rating}, 작성자: {review.user.nickname}")

    return render(request, "review_list.html", {"reviews": reviews, "query": query, "sort": sort})

# 리뷰 상세 보기 (조회수 증가, 댓글 및 좋아요 포함)
def review_detail(request, pk):
    review = get_object_or_404(UserReviews, pk=pk)

    # 조회수 증가
    UserReviews.objects.filter(pk=pk).update(views=F("views") + 1)

    # 좋아요 개수 추가
    like_count = ReviewComments.objects.filter(review=review, like_type="review_like").count()
    comments = ReviewComments.objects.filter(review=review).order_by("created_at")

    return render(request, "review_detail.html", {
        "review": review,
        "like_count": like_count,
        "comments": comments
    })

# 리뷰 작성 (다중 이미지 업로드 가능)
@login_required
def review_create(request):
    menus = UserSelectedMenus.objects.filter(user=request.user) 

    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES, user=request.user)
        files = request.FILES.getlist("images")

        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user

            # 선택한 메뉴 정보 저장 (pk 값으로 조회)
            selected_menu_id = request.POST.get("selected_menu")
            if selected_menu_id:
                selected_menu = get_object_or_404(UserSelectedMenus, pk=selected_menu_id, user=request.user)
                review.selected_menu = selected_menu
            else:
                print("🚨 selected_menu가 비어 있습니다.")

            review.save()  # 리뷰를 먼저 저장해야 review ID가 생성됨

            # 이미지 저장 디렉토리 설정
            upload_dir = os.path.join(settings.MEDIA_ROOT, "review_images")
            os.makedirs(upload_dir, exist_ok=True)  # 폴더가 없으면 생성

            # 이미지 저장
            for file in files:
                review_image = ReviewImages(review=review, image_url=file)  # ImageField에 직접 저장
                review_image.save()

            # 쿠키 지급 로직 추가
            if files:  # 사진이 포함된 리뷰
                request.user.points = F('points') + 15  # 15 쿠키 지급
            else:  # 텍스트 리뷰만 작성한 경우
                request.user.points = F('points') + 10  # 10 쿠키 지급
            request.user.save()

            return JsonResponse({"success": True, "redirect_url": reverse("review_list")})

        else:
            return JsonResponse({"success": False, "error": str(form.errors)}, status=400)
    
    
    else:
        form = ReviewForm(user=request.user)

    return render(request, "review_form.html", {"form": form, "menus": menus})

# 리뷰 수정
@login_required
def review_update(request, pk):
    review = get_object_or_404(UserReviews, pk=pk, user=request.user)
    menus = UserSelectedMenus.objects.filter(user=request.user)

    if request.method == "POST":
        form = ReviewForm(request.POST, request.FILES, instance=review, user=request.user)
        files = request.FILES.getlist("images")

        if form.is_valid():
            updated_review = form.save(commit=False)
            updated_review.user = request.user

            # 선택한 메뉴 정보 저장
            selected_menu_id = request.POST.get("selected_menu")
            if selected_menu_id:
                selected_menu = get_object_or_404(UserSelectedMenus, pk=selected_menu_id, user=request.user)
                updated_review.selected_menu = selected_menu

            updated_review.save()

            # 기존 이미지 유지 + 새 이미지 추가 가능
            for file in files:
                ReviewImages.objects.create(review=updated_review, image_url=file)

            return redirect("review_list", pk=pk)
        else:
            print("🚨 폼 에러:", form.errors)
    else:
        form = ReviewForm(instance=review, user=request.user)

    return render(request, "review_form.html", {"form": form, "review": review, "menus": menus})

# 특정 사용자의 리뷰 목록 조회
def user_reviews(request, username):
    user = get_object_or_404(Users, username=username)
    sort_option = request.GET.get('sort', 'created_at')

    reviews = UserReviews.objects.filter(user=user).order_by(
        {'views': '-views', 'rating': '-rating'}.get(sort_option, '-created_at')
    )

    return render(request, "user_reviews.html", {"reviews": reviews, "user": user, "sort_option": sort_option})

# 좋아요 기능
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

# 댓글 추가
@login_required
def add_comment(request, pk):
    review = get_object_or_404(UserReviews, pk=pk)
    
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            ReviewComments.objects.create(review=review, user=request.user, comment_text=content, like_type='comment')
    
    return redirect("review_detail", pk=pk)

# 대댓글 추가
@login_required
def add_reply(request, comment_id):
    comment = get_object_or_404(ReviewComments, comment_id=comment_id, like_type='comment')
    
    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content:
            ReviewComments.objects.create(review=comment.review, user=request.user, comment_text=content, like_type='comment', parent_id=comment.comment_id)
    
    return redirect("review_detail", pk=comment.review.pk)

# 댓글 삭제
@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(ReviewComments, comment_id=comment_id, like_type='comment')
    if request.user == comment.user:
        comment.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "권한이 없습니다."}, status=403)

# 대댓글 삭제
@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(ReviewComments, comment_id=reply_id, like_type='comment')
    if request.user == reply.user:
        reply.delete()
    return redirect("review_detail", pk=reply.review.pk)

# 이미지 삭제
@login_required
def delete_review_image(request, image_id):
    if request.method == "POST":
        image = get_object_or_404(ReviewImages, id=image_id)
        
        # 이미지 파일 삭제 (선택 사항)
        image.image_url.delete(save=False)
        
        # DB에서 이미지 객체 삭제
        image.delete()
        
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)