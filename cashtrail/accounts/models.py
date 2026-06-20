from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    CURRENCY_CHOICES = [
        ('INR', '₹ Indian Rupee'),
        ('USD', '$ US Dollar'),
        ('EUR', '€ Euro'),
        ('GBP', '£ British Pound'),
        ('JPY', '¥ Japanese Yen'),
    ]
    email = models.EmailField(unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def get_currency_symbol(self):
        symbols = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥'}
        return symbols.get(self.currency, '₹')

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"


class UserRegistrationLog(models.Model):
    """Stores registration metadata visible to admins (never stores plain passwords)."""
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='reg_log')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    # Stores hashed password algorithm info only (e.g. "pbkdf2_sha256")
    password_algo  = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Registration Log'
        verbose_name_plural = 'Registration Logs'

    def __str__(self):
        return f"Log for {self.user.email}"
