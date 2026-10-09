from django.urls import path

from . import views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('following/', views.following_feed, name='following_feed'),
    path('followers/', views.followers_feed, name='followers_feed'),
    path('search/', views.search, name='search'),
    path('new/', views.new_post, name='new_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/like/', views.like_toggle, name='like_toggle'),
    path('post/<int:pk>/comment/', views.comment_add, name='comment_add'),
]
