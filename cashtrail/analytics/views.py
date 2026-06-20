from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta, date
import json, csv, urllib.request, urllib.error, ssl
from expenses.models import Expense, Income, Category
from django.conf import settings


def get_monthly_data(user, months=12):
    today = timezone.now().date()
    data = []
    for i in range(months - 1, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
        exp = Expense.objects.filter(user=user, date__year=month_date.year, date__month=month_date.month).aggregate(total=Sum('amount'))['total'] or 0
        inc = Income.objects.filter(user=user,  date__year=month_date.year, date__month=month_date.month).aggregate(total=Sum('amount'))['total'] or 0
        data.append({'month': month_date.strftime('%b %Y'), 'expenses': float(exp), 'income': float(inc), 'savings': float(inc - exp)})
    return data


@login_required
def analytics_dashboard(request):
    user  = request.user
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start  = today.replace(month=1, day=1)

    monthly_data    = get_monthly_data(user, 12)
    category_yearly = list(Expense.objects.filter(user=user, date__gte=year_start)
        .values('category__name', 'category__color', 'category__icon')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total'))

    # Add percentage to each category
    cat_total = sum(float(c['total']) for c in category_yearly) or 1
    for c in category_yearly:
        c['pct'] = round(float(c['total']) / cat_total * 100, 1)

    week_data = []
    for i, day in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun']):
        avg = Expense.objects.filter(user=user, date__week_day=i+2).aggregate(avg=Avg('amount'))['avg'] or 0
        week_data.append({'day': day, 'avg': float(avg)})

    payment_data = list(Expense.objects.filter(user=user, date__gte=month_start)
        .values('payment_method').annotate(total=Sum('amount')).order_by('-total'))

    # Income by source
    source_labels = {'salary':'💼 Salary','freelance':'💻 Freelance','business':'🏢 Business', 'investment':'📈 Investment','rental':'🏠 Rental','gift':'🎁 Gift','refund':'↩️ Refund','other':'💰 Other'}
    income_source_data = [
        {'source': source_labels.get(r['source'], r['source']), 'total': float(r['total'])} for r in Income.objects.filter(user=user, date__gte=year_start).values('source').annotate(total=Sum('amount')).order_by('-total')
    ]

    top_days = Expense.objects.filter(user=user, date__gte=year_start)\
        .values('date').annotate(total=Sum('amount')).order_by('-total')[:5]

    yearly_expense = Expense.objects.filter(user=user, date__gte=year_start).aggregate(Sum('amount'))['amount__sum'] or 0
    yearly_income  = Income.objects.filter(user=user,  date__gte=year_start).aggregate(Sum('amount'))['amount__sum'] or 0

    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    this_month_exp   = Expense.objects.filter(user=user, date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0
    last_month_exp   = Expense.objects.filter(user=user, date__gte=last_month_start, date__lt=month_start).aggregate(Sum('amount'))['amount__sum'] or 0
    mom_change = ((this_month_exp - last_month_exp) / last_month_exp * 100) if last_month_exp else 0
    savings_rate = float(yearly_income - yearly_expense) / float(yearly_income) * 100 if yearly_income > 0 else 0

    # Reports inline data (calendar year)
    year = today.year
    monthly_summary = []
    for month in range(1, 13):
        exp = Expense.objects.filter(user=user, date__year=year, date__month=month).aggregate(Sum('amount'))['amount__sum'] or 0
        inc = Income.objects.filter(user=user,  date__year=year, date__month=month).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_summary.append({'month': date(year, month, 1).strftime('%B'), 'expenses': float(exp), 'income': float(inc), 'savings': float(inc - exp)})
    total_exp = sum(m['expenses'] for m in monthly_summary)
    total_inc = sum(m['income']   for m in monthly_summary)

    context = {
        'monthly_data':        json.dumps(monthly_data),
        'category_yearly':     json.dumps(category_yearly, default=str),
        'week_data':           json.dumps(week_data),
        'payment_data':        json.dumps(payment_data, default=str),
        'income_source_data':  json.dumps(income_source_data),
        'top_days':            top_days,
        'yearly_expense':      yearly_expense,
        'yearly_income':       yearly_income,
        'yearly_savings':      yearly_income - yearly_expense,
        'savings_rate':        round(savings_rate, 1),
        'this_month_exp':      this_month_exp,
        'mom_change':          round(mom_change, 1),
        'currency':            user.get_currency_symbol(),
        # reports inline
        'monthly_summary':     monthly_summary,
        'year':                year,
        'total_expenses':      total_exp,
        'total_income':        total_inc,
        'total_savings':       total_inc - total_exp,
        'years':               range(2020, today.year + 1),
    }
    return render(request, 'analytics/dashboard.html', context)


# ── FREE AI HELPERS ──────────────────────────────────────────────────────────

def _call_groq(prompt, api_key):
    """Groq free API — llama-3.3-70b-versatile (free tier, fast)."""
    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a friendly personal finance advisor. Be concise, specific, encouraging, and use emojis. Format with markdown headers and bullet points."},
            {"role": "user",   "content": prompt}
        ],
        "max_tokens": 1400, "temperature": 0.7,
    }).encode()
    ctx = ssl._create_unverified_context()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def _call_gemini(prompt, api_key):
    """Google Gemini 1.5 Flash — free tier (15 req/min, 1500 req/day)."""
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 1400, "temperature": 0.7}
    }).encode()
    ctx = ssl._create_unverified_context()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
        data = json.loads(resp.read())
        return data["candidates"][0]["content"]["parts"][0]["text"]


def _rule_based_insights(expense_data, symbol):
    spent    = expense_data['total_spent']
    income   = expense_data['total_income']
    budget   = expense_data['monthly_budget']
    sr       = expense_data['savings_rate']
    cats     = expense_data['categories']
    month    = expense_data['month']

    # Health score
    if sr >= 30:   score, score_label = 9, "Excellent 🌟"
    elif sr >= 20: score, score_label = 8, "Very Good 👍"
    elif sr >= 10: score, score_label = 6, "Good 📈"
    elif sr >= 0:  score, score_label = 4, "Needs Improvement ⚠️"
    else:          score, score_label = 2, "Critical 🔴"

    # Budget status
    if budget > 0:
        budget_pct = spent / float(budget) * 100
        budget_msg = f"You've used **{budget_pct:.0f}%** of your monthly budget."
        if budget_pct > 100: budget_msg += " ⚠️ Over budget!"
        elif budget_pct > 85: budget_msg += " 🟡 Approaching limit."
        else: budget_msg += " 🟢 On track."
    else:
        budget_msg = "No monthly budget set. Consider setting one for better control."

    top_cats = "\n".join([f"- **{c['name']}**: {symbol}{c['amount']:,.0f}" for c in cats[:3]]) if cats else "- No category data yet"

    # Tips based on savings rate
    if sr < 10:
        tips = [
            "🎯 Set a strict monthly budget in the Budgets section and review it weekly",
            "📱 Switch recurring payments (OTT, subscriptions) to annual plans for 15–20% savings",
            "🍱 Meal prep 3 days a week — can cut food spend by ₹3,000–5,000/month",
            "🔍 Audit all subscriptions — cancel anything unused for 30+ days",
            "💳 Use UPI/cash envelopes instead of cards to feel spending more concretely",
        ]
    elif sr < 25:
        tips = [
            "📈 You're on the right track! Try to push your savings rate above 20%",
            "🏦 Auto-transfer savings on salary day before you can spend it",
            "🛒 Use the 48-hour rule: wait 2 days before any non-essential purchase",
            "💡 Review utility bills — negotiate or switch providers annually",
            "🎁 Budget for gifts and entertainment in advance to avoid surprise spikes",
        ]
    else:
        tips = [
            "🌟 Excellent savings rate! Consider investing the surplus",
            "📊 Explore index funds or SIPs for long-term wealth building",
            "🎯 Create savings goals for specific targets (travel, emergency fund, home)",
            "📱 Check if any investments can be automated for compound growth",
            "🏆 You're in the top financial health bracket — keep it consistent!",
        ]

    tips_str = "\n".join(tips)

    return f"""## 💡 AI Financial Insights — {month}

        ### 📊 Spending Snapshot
        - **Total Spent:** {symbol}{spent:,.2f}
        - **Total Income:** {symbol}{income:,.2f}
        - **Net Savings:** {symbol}{max(income-spent,0):,.2f}
        - **Savings Rate:** {sr:.1f}%
        - {budget_msg}

        ### 🔝 Top Spending Categories
        {top_cats}

        ### ✅ 5 Personalised Tips
        {tips_str}

        ### 📈 Budget Recommendation (50/30/20 Rule)
        | Category | Allocation | Amount |
        |----------|-----------|--------|
        | Needs (rent, food, bills) | 50% | {symbol}{income*0.5:,.0f} |
        | Wants (dining, entertainment) | 30% | {symbol}{income*0.3:,.0f} |
        | Savings & investments | 20% | {symbol}{income*0.2:,.0f} |

        ### 🏆 Financial Health Score: {score}/10 — {score_label}

        """


@login_required
def ai_insights(request):
    user  = request.user
    today = timezone.now().date()
    month_start = today.replace(day=1)

    monthly_expenses   = Expense.objects.filter(user=user, date__gte=month_start)
    category_breakdown = monthly_expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')[:6]

    total_spent  = float(monthly_expenses.aggregate(Sum('amount'))['amount__sum'] or 0)
    total_income = float(Income.objects.filter(user=user, date__gte=month_start).aggregate(Sum('amount'))['amount__sum'] or 0)

    expense_data = {
        'month':          today.strftime('%B %Y'),
        'total_spent':    total_spent,
        'total_income':   total_income,
        'monthly_budget': float(user.monthly_budget),
        'categories':     [{'name': c['category__name'] or 'Uncategorized', 'amount': float(c['total'])} for c in category_breakdown],
        'savings_rate':   (total_income - total_spent) / total_income * 100 if total_income > 0 else 0,
    }

    insights = None
    error = None
    ai_provider = None

    if request.method == 'POST':
        prompt = f"""Analyse this user's personal finance data for {expense_data['month']} and provide actionable advice:

        Total Spent: {user.get_currency_symbol()}{total_spent:,.0f}
        Total Income: {user.get_currency_symbol()}{total_income:,.0f}
        Monthly Budget: {user.get_currency_symbol()}{expense_data['monthly_budget']:,.0f}
        Savings Rate: {expense_data['savings_rate']:.1f}%
        Top Spending Categories: {json.dumps(expense_data['categories'])}

        Please provide:
        ## 1. Spending Analysis
        (2-3 specific observations about their patterns)

        ## 2. Top 3 Concerns
        (concrete issues with their data)

        ## 3. 5 Smart Tips
        (numbered, emoji-prefixed, actionable)

        ## 4. Budget Recommendation
        (simple allocation table)

        ## 5. Financial Health Score
        (X/10 with one-line explanation)

        Keep it encouraging, specific, and under 450 words."""

        groq_key   = (getattr(settings, 'GROQ_API_KEY',   '') or '').strip()
        gemini_key = (getattr(settings, 'GEMINI_API_KEY', '') or '').strip()

        if groq_key:
            try:
                insights    = _call_groq(prompt, groq_key)
                ai_provider = "Groq · Llama 3.3 70B (Free)"
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:200]
                error = f"Groq API error {e.code}: {body}"
            except Exception as e:
                error = f"Groq error: {str(e)[:120]}"

        if not insights and gemini_key:
            try:
                insights    = _call_gemini(prompt, gemini_key)
                ai_provider = "Google Gemini 1.5 Flash (Free)"
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:200]
                error = (error or '') + f" | Gemini error {e.code}: {body}"
            except Exception as e:
                error = (error or '') + f" | Gemini error: {str(e)[:120]}"

        if not insights:
            insights = _rule_based_insights(expense_data, user.get_currency_symbol())
            ai_provider = "Smart Demo Mode (Add free API key for AI insights)"
            error = None

    return render(request, 'analytics/ai_insights.html', { 'expense_data': expense_data, 'insights': insights, 'error': error, 'ai_provider': ai_provider, 'currency': user.get_currency_symbol(), 'has_groq': bool(getattr(settings, 'GROQ_API_KEY', '')), 'has_gemini': bool(getattr(settings, 'GEMINI_API_KEY', ''))})


@login_required
def export_csv(request):
    user = request.user
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="cashtrail_{timezone.now().strftime("%Y%m%d")}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date','Title','Category','Amount','Payment Method','Tags','Notes'])
    for e in Expense.objects.filter(user=user).select_related('category').prefetch_related('tags'):
        writer.writerow([e.date, e.title, e.category.name if e.category else '', e.amount, e.get_payment_method_display(), ', '.join(t.name for t in e.tags.all()), e.notes])
    return response


@login_required
def reports(request):
    user  = request.user
    today = timezone.now().date()

    report_type = request.GET.get('period', 'calendar')  
    year = int(request.GET.get('year', today.year))

    if report_type == 'fy':
        fy_start = date(year, 4, 1)
        fy_end   = date(year + 1, 3, 31)
        months_range = []
        for i in range(12):
            m = ((3 + i) % 12) + 1  
            y = year if m >= 4 else year + 1
            months_range.append((y, m))
        period_label = f"FY {year}–{str(year+1)[2:]}"
    else:
        months_range = [(year, m) for m in range(1, 13)]
        period_label = f"CY {year}"

    monthly_summary = []
    for (y, m) in months_range:
        exp = Expense.objects.filter(user=user, date__year=y, date__month=m).aggregate(Sum('amount'))['amount__sum'] or 0
        inc = Income.objects.filter(user=user,  date__year=y, date__month=m).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_summary.append({
            'month': date(y, m, 1).strftime('%b %Y'),
            'expenses': float(exp), 'income': float(inc), 'savings': float(inc - exp)
        })

    total_exp = sum(m['expenses'] for m in monthly_summary)
    total_inc = sum(m['income']   for m in monthly_summary)

    if report_type == 'fy':
        cat_qs = Expense.objects.filter(user=user, date__gte=fy_start, date__lte=fy_end)
    else:
        cat_qs = Expense.objects.filter(user=user, date__year=year)

    category_breakdown = list(cat_qs.values('category__name','category__color','category__icon')
        .annotate(total=Sum('amount')).order_by('-total')[:8])
    cat_total = sum(float(c['total']) for c in category_breakdown) or 1
    for c in category_breakdown:
        c['pct'] = round(float(c['total']) / cat_total * 100, 1)

    return render(request, 'analytics/reports.html', {
        'monthly_summary':    monthly_summary,
        'year':               year,
        'period_type':        report_type,
        'period_label':       period_label,
        'total_expenses':     total_exp,
        'total_income':       total_inc,
        'total_savings':      total_inc - total_exp,
        'currency':           user.get_currency_symbol(),
        'years':              range(2020, today.year + 1),
        'monthly_data_json':  json.dumps(monthly_summary),
        'category_breakdown': category_breakdown,
    })
