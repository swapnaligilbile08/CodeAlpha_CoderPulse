from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from notifications.models import notify, unnotify

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import Follow, User

class LoginView(auth_views.LoginView):
    """The login and sign up forms share one page, so this view also hands over a blank sign up form."""
    template_name = 'accounts/auth.html'
    redirect_authenticated_user = True
    authentication_form = LoginForm

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'auto_id': 'login_%s'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(mode='login', login_form=context['form'], register_form=RegisterForm(auto_id='register_%s'))
        return context

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None, auto_id='register_%s')
    if form.is_valid():
        login(request, form.save())
        return redirect('home')
    return render(request, 'accounts/auth.html', {
        'mode': 'register', 'register_form': form, 'login_form': LoginForm(auto_id='login_%s'),
    })

@login_required
def profile(request, username):
    owner = get_object_or_404(User, username=username)
    is_me = owner == request.user
    return render(request, 'accounts/profile.html', {
        'owner': owner,
        'is_me': is_me,
        'posts': owner.posts.all(),
        'is_following': Follow.objects.filter(follower=request.user, following=owner).exists(),
    })

@login_required
def follow_list(request, username, kind):
    owner = get_object_or_404(User, username=username)
    if kind == 'followers':
        users = User.objects.filter(following_set__following=owner)
    else:
        users = User.objects.filter(follower_set__follower=owner)
    users = users.annotate(i_follow=Exists(
        Follow.objects.filter(follower=request.user, following=OuterRef('pk'))))
    return render(request, 'accounts/follow_list.html', {'owner': owner, 'users': users, 'kind': kind})

@login_required
@require_POST
def follow_toggle(request, username):
    """Follow, or unfollow if already following."""
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return JsonResponse({'error': "You can't follow yourself."}, status=400)
    follow, created = Follow.objects.get_or_create(follower=request.user, following=target)
    if created:
        notify(target, request.user, 'follow')
    else:
        follow.delete()
        unnotify(target, request.user, 'follow')
    return JsonResponse({'following': created, 'followers': target.followers_count})

@login_required
def settings_page(request):
    return render(request, 'accounts/settings.html')

@login_required
def edit_profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile saved.')
        return redirect('profile', username=request.user.username)
    return render(request, 'accounts/edit_profile.html', {'form': form})
