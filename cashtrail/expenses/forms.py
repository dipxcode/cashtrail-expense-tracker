from django import forms
from django.forms.widgets import CheckboxSelectMultiple
from .models import Expense, Income, Category, Tag, Budget, SavingsGoal


class TagCheckboxWidget(CheckboxSelectMultiple):
    """Renders tags as pill-style checkboxes."""
    template_name = 'django/forms/widgets/checkbox_select.html'


class ExpenseForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=TagCheckboxWidget(attrs={'class': 'tag-checkbox'}),
    )

    class Meta:
        model  = Expense
        fields = ['title', 'amount', 'category', 'tags', 'date', 'payment_method',
                  'notes', 'receipt', 'is_recurring', 'recurrence', 'location']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['tags'].queryset     = Tag.objects.filter(user=user)
        for name, field in self.fields.items():
            if name not in ('tags', 'is_recurring'):
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['category'].widget.attrs.update({'class': 'form-select'})
        self.fields['payment_method'].widget.attrs.update({'class': 'form-select'})
        self.fields['recurrence'].widget.attrs.update({'class': 'form-select'})
        self.fields['is_recurring'].widget.attrs.update({'class': 'form-check-input'})


class IncomeForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    class Meta:
        model  = Income
        fields = ['title', 'amount', 'source', 'date', 'notes', 'is_recurring', 'recurrence']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'is_recurring':
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['source'].widget.attrs.update({'class': 'form-select'})
        self.fields['recurrence'].widget.attrs.update({'class': 'form-select'})
        self.fields['is_recurring'].widget.attrs.update({'class': 'form-check-input'})


class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ['name', 'icon', 'color', 'description', 'budget_limit']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class TagForm(forms.ModelForm):
    class Meta:
        model  = Tag
        fields = ['name', 'color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class BudgetForm(forms.ModelForm):
    class Meta:
        model  = Budget
        fields = ['category', 'amount', 'month', 'year']

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['category'].widget.attrs.update({'class': 'form-select'})


class SavingsGoalForm(forms.ModelForm):
    target_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model  = SavingsGoal
        fields = ['title', 'target_amount', 'current_amount', 'target_date', 'icon', 'color']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class ExpenseFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end_date   = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    category   = forms.ModelChoiceField(queryset=None, required=False, empty_label="All Categories",
                                         widget=forms.Select(attrs={'class': 'form-select'}))
    payment_method = forms.ChoiceField(choices=[('', 'All Methods')] + Expense.PAYMENT_METHODS,
                                        required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    min_amount = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min'}))
    max_amount = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max'}))
    search     = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search expenses...'}))
    tag        = forms.ModelChoiceField(queryset=None, required=False, empty_label="All Tags",
                                         widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['tag'].queryset      = Tag.objects.filter(user=user)
