from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Category(models.Model):
    ICON_CHOICES = [
        ('🍔', 'Food & Dining'), ('🚗', 'Transportation'), ('🏠', 'Housing'),
        ('💊', 'Health & Medical'), ('🎬', 'Entertainment'), ('👗', 'Shopping'),
        ('📚', 'Education'), ('✈️', 'Travel'), ('💡', 'Utilities'),
        ('💪', 'Fitness'), ('🐾', 'Pets'), ('🎁', 'Gifts'),
        ('💼', 'Business'), ('📱', 'Technology'), ('🌿', 'Personal Care'),
        ('💰', 'Savings'), ('📈', 'Investment'), ('🏦', 'Banking'),
        ('🍺', 'Alcohol'), ('☕', 'Coffee'), ('🎮', 'Gaming'), ('📷', 'Photography'),
    ]
    COLOR_CHOICES = [
        ('#FF6B6B', 'Red'), ('#4ECDC4', 'Teal'), ('#45B7D1', 'Blue'),
        ('#96CEB4', 'Green'), ('#FFEAA7', 'Yellow'), ('#DDA0DD', 'Plum'),
        ('#FF8C42', 'Orange'), ('#A8E6CF', 'Mint'), ('#FFB7B2', 'Pink'),
        ('#C7CEEA', 'Lavender'), ('#B5EAD7', 'Sage'), ('#FF9AA2', 'Rose'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, default='💰')
    color = models.CharField(max_length=7, default='#4ECDC4')
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    budget_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.icon} {self.name}"

class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#4ECDC4')

    def __str__(self):
        return self.name

class Expense(models.Model):
    PAYMENT_METHODS = [
        ('cash', '💵 Cash'),
        ('card', '💳 Credit/Debit Card'),
        ('upi', '📱 UPI'),
        ('netbanking', '🏦 Net Banking'),
        ('wallet', '👛 Digital Wallet'),
        ('cheque', '📄 Cheque'),
        ('other', '🔄 Other'),
    ]
    RECURRENCE_CHOICES = [
        ('none', 'None'), ('daily', 'Daily'), ('weekly', 'Weekly'),
        ('monthly', 'Monthly'), ('yearly', 'Yearly'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='expenses')
    tags = models.ManyToManyField(Tag, blank=True)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    notes = models.TextField(blank=True)
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='none')
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount}"

class Income(models.Model):
    SOURCE_CHOICES = [
        ('salary', '💼 Salary'), ('freelance', '💻 Freelance'),
        ('business', '🏢 Business'), ('investment', '📈 Investment'),
        ('rental', '🏠 Rental'), ('gift', '🎁 Gift'),
        ('refund', '↩️ Refund'), ('other', '💰 Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='incomes')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='salary')
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence = models.CharField(max_length=10, choices=[
        ('none','None'),('daily','Daily'),('weekly','Weekly'),('monthly','Monthly'),('yearly','Yearly')
    ], default='none')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.amount}"

class Budget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.IntegerField()
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'category', 'month', 'year']

    def spent(self):
        from django.db.models import Sum
        total = self.category.expenses.filter(
            user=self.user, date__month=self.month, date__year=self.year
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        return total

    def percentage(self):
        if self.amount > 0:
            return min(float(self.spent() / self.amount * 100), 100)
        return 0

class SavingsGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings_goals')
    title = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    target_date = models.DateField(null=True, blank=True)
    icon = models.CharField(max_length=10, default='🎯')
    color = models.CharField(max_length=7, default='#4ECDC4')
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def percentage(self):
        if self.target_amount > 0:
            return min(float(self.current_amount / self.target_amount * 100), 100)
        return 0

    def __str__(self):
        return self.title