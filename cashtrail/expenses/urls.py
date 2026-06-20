from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('list/', views.expense_list, name='expense_list'),
    path('add/', views.add_expense, name='add_expense'),
    path('add-transaction/', views.add_transaction, name='add_transaction'),
    path('edit/<uuid:pk>/', views.edit_expense, name='edit_expense'),
    path('delete/<uuid:pk>/', views.delete_expense, name='delete_expense'),
    path('detail/<uuid:pk>/', views.expense_detail, name='expense_detail'),
    path('income/', views.income_list, name='income_list'),
    path('income/add/', views.add_income, name='add_income'),
    path('income/edit/<uuid:pk>/', views.edit_income, name='edit_income'),
    path('income/delete/<uuid:pk>/', views.delete_income, name='delete_income'),
    path('categories/', views.categories, name='categories'),
    path('categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('tags/', views.tags_view, name='tags'),
    path('budgets/', views.budgets_view, name='budgets'),
    path('savings/', views.savings_goals_view, name='savings_goals'),
    path('savings/update/<int:pk>/', views.update_goal_progress, name='update_goal'),
]
