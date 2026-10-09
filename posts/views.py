from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from notifications.models import notify, unnotify

from .forms import PostForm
from .models import CATEGORIES, CATEGORY_KEYS, Comment, Like, Post


def posts_with_counts(user):
    """Posts with like and comment counts, and whether `user` liked each one."""
    return Post.objects.select_related('author').annotate(
        like_count=Count('likes', distinct=True),
        comment_count=Count('comments', distinct=True),
        liked=Exists(Like.objects.filter(post=OuterRef('pk'), user=user)),
    ).order_by('-created_at')  # Meta ordering is ignored when counting


@login_required
def home(request):
    return render(request, 'posts/feed.html', {
        'title': 'Home', 'posts': posts_with_counts(request.user)[:50], 'suggestions': request.user.suggestions(),
    })


def people_feed(request, people, kind):
    """Newest posts by `people`, with the Following | Followers switch on top."""
    posts = posts_with_counts(request.user).filter(author__in=people)[:50]
    return render(request, 'posts/feed.html', {
        'title': 'Feed', 'posts': posts, 'kind': kind, 'suggestions': request.user.suggestions(),
    })


@login_required
def following_feed(request):
    return people_feed(request, request.user.following_set.values('following'), 'following')


@login_required
def followers_feed(request):
    return people_feed(request, request.user.follower_set.values('follower'), 'followers')


@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    cat = request.GET.get('cat', '')
    posts = posts_with_counts(request.user)
    if q:
        posts = posts.filter(Q(title__icontains=q) | Q(body__icontains=q) | Q(author__username__icontains=q))
    if cat in CATEGORY_KEYS:
        posts = posts.filter(category=cat)
    return render(request, 'posts/search.html', {
        'posts': posts[:50], 'q': q, 'cat': cat, 'categories': CATEGORIES,
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(post)
    return render(request, 'posts/new_post.html', {'form': form})


@login_required
def post_detail(request, pk):
    post = get_object_or_404(posts_with_counts(request.user), pk=pk)
    comments = post.comments.select_related('author')
    return render(request, 'posts/post_detail.html', {'post': post, 'comments': comments})


@login_required
@require_POST
def like_toggle(request, pk):
    """Like, or unlike if already liked."""
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if created:
        notify(post.author, request.user, 'like', post)
    else:
        like.delete()
        unnotify(post.author, request.user, 'like', post)
    return JsonResponse({'liked': created, 'count': post.likes.count()})


@login_required
@require_POST
def comment_add(request, pk):
    post = get_object_or_404(Post, pk=pk)
    body = request.POST.get('body', '').strip()
    if not body:
        messages.error(request, 'Write something before posting a comment.')
    else:
        Comment.objects.create(post=post, author=request.user, body=body[:500])
        notify(post.author, request.user, 'comment', post)
    return redirect(post.get_absolute_url() + '#comments')
