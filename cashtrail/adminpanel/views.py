from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
import json
from accounts.models import User
from expenses.models import Expense, Income, Category

def is_staff(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_staff, login_url='/accounts/login/')
def admin_dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)

    total_users = User.objects.count()
    new_users_month = User.objects.filter(date_joined__gte=month_start).count()
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = Income.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_transactions = Expense.objects.count() + Income.objects.count()

    recent_users = User.objects.order_by('-date_joined')[:8]
    recent_expenses = Expense.objects.select_related('user', 'category').order_by('-created_at')[:10]

    # Monthly user growth (last 6 months)
    user_growth = []
    for i in range(5, -1, -1):
        d = (today.replace(day=1) - timedelta(days=i*28)).replace(day=1)
        count = User.objects.filter(date_joined__year=d.year, date_joined__month=d.month).count()
        user_growth.append({'month': d.strftime('%b'), 'count': count})

    # Expense by category (all users)
    cat_breakdown = Expense.objects.values('category__name', 'category__color').annotate(
        total=Sum('amount')
    ).order_by('-total')[:8]

    top_spenders = User.objects.annotate(
        total_spent=Sum('expenses__amount')
    ).filter(total_spent__isnull=False).order_by('-total_spent')[:5]

    context = {
        'total_users': total_users,
        'new_users_month': new_users_month,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'total_transactions': total_transactions,
        'recent_users': recent_users,
        'recent_expenses': recent_expenses,
        'user_growth': json.dumps(user_growth),
        'cat_breakdown': json.dumps(list(cat_breakdown), default=str),
        'top_spenders': top_spenders,
    }
    return render(request, 'adminpanel/dashboard.html', context)

@user_passes_test(is_staff, login_url='/accounts/login/')
def admin_users(request):
    users = User.objects.annotate(
        expense_count=Count('expenses'),
        income_count=Count('incomes'),
        total_spent=Sum('expenses__amount')
    ).order_by('-date_joined')

    search = request.GET.get('search', '')
    if search:
        users = users.filter(email__icontains=search) | User.objects.filter(username__icontains=search)

    return render(request, 'adminpanel/users.html', {'users': users, 'search': search})

@user_passes_test(is_staff, login_url='/accounts/login/')
def admin_user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    expenses = Expense.objects.filter(user=user).order_by('-date')[:20]
    incomes = Income.objects.filter(user=user).order_by('-date')[:10]
    total_spent = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_earned = incomes.aggregate(Sum('amount'))['amount__sum'] or 0

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'toggle_staff':
            user.is_staff = not user.is_staff
            user.save()
            messages.success(request, f"Staff status toggled for {user.email}")
        elif action == 'toggle_active':
            user.is_active = not user.is_active
            user.save()
            messages.success(request, f"Active status toggled for {user.email}")
        return redirect('admin_user_detail', pk=pk)

    return render(request, 'adminpanel/user_detail.html', {
        'target_user': user, 'expenses': expenses, 'incomes': incomes,
        'total_spent': total_spent, 'total_earned': total_earned
    })

@user_passes_test(is_staff, login_url='/accounts/login/')
def admin_transactions(request):
    expenses = Expense.objects.select_related('user', 'category').order_by('-date')
    incomes = Income.objects.select_related('user').order_by('-date')

    exp_total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    inc_total = incomes.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'adminpanel/transactions.html', {
        'expenses': expenses[:50], 'incomes': incomes[:30],
        'exp_total': exp_total, 'inc_total': inc_total
    })
