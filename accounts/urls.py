from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('settings/', views.settings_page, name='settings'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('u/<str:username>/', views.profile, name='profile'),
    path('u/<str:username>/followers/', views.follow_list, {'kind': 'followers'}, name='followers'),
    path('u/<str:username>/following/', views.follow_list, {'kind': 'following'}, name='following'),
    path('u/<str:username>/follow/', views.follow_toggle, name='follow_toggle'),
]
