from django.contrib import admin
from .models import Expense, Income, Category, Tag, Budget, SavingsGoal

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'user', 'date', 'payment_method']
    list_filter = ['payment_method', 'category', 'date']
    search_fields = ['title', 'user__email']
    date_hierarchy = 'date'

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'source', 'user', 'date']
    list_filter = ['source', 'date']

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Budget)
admin.site.register(SavingsGoal)