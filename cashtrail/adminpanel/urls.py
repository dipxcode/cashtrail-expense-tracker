from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.admin_users, name='admin_users'),
    path('users/<int:pk>/', views.admin_user_detail, name='admin_user_detail'),
    path('transactions/', views.admin_transactions, name='admin_transactions'),
]