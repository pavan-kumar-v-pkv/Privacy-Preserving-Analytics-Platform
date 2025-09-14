from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_file, name='upload'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('visualize/', views.visualize, name='visualize'),
]