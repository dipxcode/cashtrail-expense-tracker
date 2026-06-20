from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.http import JsonResponse
from django.core.paginator import Paginator
import json
from datetime import timedelta
from .models import Expense, Income, Category, Tag, Budget, SavingsGoal
from .forms import (ExpenseForm, IncomeForm, CategoryForm, TagForm, BudgetForm, SavingsGoalForm, ExpenseFilterForm)

def get_dashboard_stats(user):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    monthly_expenses = Expense.objects.filter(user=user, date__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_income = Income.objects.filter(user=user, date__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses_all = Expense.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
    total_income_all = Income.objects.filter(user=user).aggregate(total=Sum('amount'))['total'] or 0
    
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    last_month_expenses = Expense.objects.filter(user=user, date__gte=last_month_start, date__lt=month_start).aggregate(total=Sum('amount'))['total'] or 0
    
    return {
        'monthly_expenses': monthly_expenses,
        'monthly_income': monthly_income,
        'net_savings': monthly_income - monthly_expenses,
        'total_expenses': total_expenses_all,
        'total_income': total_income_all,
        'overall_balance': total_income_all - total_expenses_all,
        'last_month_expenses': last_month_expenses,
        'expense_change': float(monthly_expenses - last_month_expenses),
    }

@login_required
def dashboard(request):
    user = request.user
    stats = get_dashboard_stats(user)
    
    recent_expenses = Expense.objects.filter(user=user).select_related('category')[:8]
    recent_incomes = Income.objects.filter(user=user)[:5]
    
    # Category breakdown
    category_data = Expense.objects.filter(user=user, date__gte=timezone.now().date().replace(day=1)).values('category__name', 'category__color', 'category__icon').annotate(total=Sum('amount')).order_by('-total')[:8]
    
    # Daily spending last 30 days
    thirty_days_ago = timezone.now().date() - timedelta(days=29)
    daily_data = Expense.objects.filter(user=user, date__gte=thirty_days_ago).values('date').annotate(total=Sum('amount')).order_by('date')
    
    budgets = Budget.objects.filter(
        user=user, 
        month=timezone.now().month, 
        year=timezone.now().year
    ).select_related('category')
    
    savings_goals = SavingsGoal.objects.filter(user=user, is_completed=False)[:3]
    
    context = {
        **stats,
        'recent_expenses': recent_expenses,
        'recent_incomes': recent_incomes,
        'category_data': json.dumps(list(category_data), default=str),
        'daily_data': json.dumps(list(daily_data), default=str),
        'budgets': budgets,
        'savings_goals': savings_goals,
        'currency': user.get_currency_symbol(),
    }
    return render(request, 'expenses/dashboard.html', context)

@login_required
def expense_list(request):
    user = request.user
    form = ExpenseFilterForm(user, request.GET)
    expenses = Expense.objects.filter(user=user).select_related('category').prefetch_related('tags')
    
    if form.is_valid():
        d = form.cleaned_data
        if d.get('start_date'): expenses = expenses.filter(date__gte=d['start_date'])
        if d.get('end_date'): expenses = expenses.filter(date__lte=d['end_date'])
        if d.get('category'): expenses = expenses.filter(category=d['category'])
        if d.get('payment_method'): expenses = expenses.filter(payment_method=d['payment_method'])
        if d.get('min_amount'): expenses = expenses.filter(amount__gte=d['min_amount'])
        if d.get('max_amount'): expenses = expenses.filter(amount__lte=d['max_amount'])
        if d.get('search'): expenses = expenses.filter(Q(title__icontains=d['search']) | Q(notes__icontains=d['search']))
        if d.get('tag'): expenses = expenses.filter(tags=d['tag'])
    
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    paginator = Paginator(expenses, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'expenses/expense_list.html', { 'expenses': page, 'filter_form': form, 'total': total, 'currency': user.get_currency_symbol() })

@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            form.save_m2m()
            messages.success(request, f'Expense "{expense.title}" added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(request.user)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Add Expense', 'action': 'Add'})

@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, id=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(request.user, instance=expense)
    return render(request, 'expenses/expense_form.html', {'form': form, 'title': 'Edit Expense', 'action': 'Update', 'expense': expense})

@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, id=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expense_list')
    return render(request, 'expenses/confirm_delete.html', {'object': expense, 'type': 'Expense'})

@login_required
def income_list(request):
    user = request.user
    incomes = Income.objects.filter(user=user)
    total = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    
    source_filter = request.GET.get('source', '')
    if source_filter:
        incomes = incomes.filter(source=source_filter)
    
    paginator = Paginator(incomes, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'expenses/income_list.html', { 'incomes': page, 'total': total, 'currency': user.get_currency_symbol(), 'source_choices': Income.SOURCE_CHOICES, 'selected_source': source_filter })

@login_required
def add_income(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, f'Income "{income.title}" added!')
            return redirect('income_list')
    else:
        form = IncomeForm()
    return render(request, 'expenses/income_form.html', {'form': form, 'title': 'Add Income'})

@login_required
def edit_income(request, pk):
    income = get_object_or_404(Income, id=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income updated!')
            return redirect('income_list')
    else:
        form = IncomeForm(instance=income)
    return render(request, 'expenses/income_form.html', {'form': form, 'title': 'Edit Income'})

@login_required
def delete_income(request, pk):
    income = get_object_or_404(Income, id=pk, user=request.user)
    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Income deleted.')
        return redirect('income_list')
    return render(request, 'expenses/confirm_delete.html', {'object': income, 'type': 'Income'})

@login_required
def categories(request):
    user = request.user
    cats = Category.objects.filter(user=user).annotate(expense_count=Count('expenses'), total_spent=Sum('expenses__amount'))
    tags = Tag.objects.filter(user=user).annotate(expense_count=Count('expense'))
    cat_form = CategoryForm()
    tag_form = TagForm()
    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'category')
        if form_type == 'category':
            cat_form = CategoryForm(request.POST)
            if cat_form.is_valid():
                cat = cat_form.save(commit=False)
                cat.user = user
                cat.save()
                messages.success(request, f'Category "{cat.name}" created!')
                return redirect('categories')
        else:
            tag_form = TagForm(request.POST)
            if tag_form.is_valid():
                tag = tag_form.save(commit=False)
                tag.user = user
                tag.save()
                messages.success(request, f'Tag "{tag.name}" created!')
                return redirect('categories')
    return render(request, 'expenses/categories.html', {'categories': cats, 'tags': tags, 'cat_form': cat_form, 'tag_form': tag_form, 'currency': user.get_currency_symbol()})

@login_required
def delete_category(request, pk):
    cat = get_object_or_404(Category, id=pk, user=request.user)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
    return redirect('categories')

@login_required
def tags_view(request):
    return redirect('/expenses/categories/?tab=tags')

@login_required
def budgets_view(request):
    user = request.user
    today = timezone.now()
    if request.method == 'POST':
        form = BudgetForm(user, request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = user
            budget.save()
            messages.success(request, 'Budget set!')
            return redirect('budgets')
    else:
        form = BudgetForm(user)
    
    budgets = Budget.objects.filter(user=user, month=today.month, year=today.year).select_related('category')
    return render(request, 'expenses/budgets.html', {'budgets': budgets, 'form': form, 'currency': user.get_currency_symbol()})

@login_required
def savings_goals_view(request):
    user = request.user
    if request.method == 'POST':
        form = SavingsGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = user
            goal.save()
            messages.success(request, f'Goal "{goal.title}" created!')
            return redirect('savings_goals')
    else:
        form = SavingsGoalForm()
    
    goals = SavingsGoal.objects.filter(user=user).order_by('is_completed', '-created_at')
    return render(request, 'expenses/savings_goals.html', {'goals': goals, 'form': form, 'currency': user.get_currency_symbol()})

@login_required
def update_goal_progress(request, pk):
    goal = get_object_or_404(SavingsGoal, id=pk, user=request.user)
    if request.method == 'POST':
        amount = request.POST.get('amount', 0)
        try:
            goal.current_amount += float(amount)
            if goal.current_amount >= float(goal.target_amount):
                goal.is_completed = True
            goal.save()
            messages.success(request, f'Goal updated! {goal.percentage():.1f}% complete.')
        except:
            messages.error(request, 'Invalid amount.')
    return redirect('savings_goals')

@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, id=pk, user=request.user)
    return render(request, 'expenses/expense_detail.html', {'expense': expense, 'currency': request.user.get_currency_symbol()})


@login_required
def add_transaction(request):
    """Combined Add Expense + Add Income page."""
    expense_form = ExpenseForm(request.user)
    income_form  = IncomeForm()
    return render(request, 'expenses/add_transaction.html', {
        'expense_form': expense_form,
        'income_form':  income_form,
    })