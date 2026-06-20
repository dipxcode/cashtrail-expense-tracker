from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User

DEFAULT_CATEGORIES = [
    ('Food & Dining','🍔','#FF6B6B'), ('Transportation','🚗','#45B7D1'),
    ('Housing & Rent','🏠','#96CEB4'), ('Health & Medical','💊','#DDA0DD'),
    ('Entertainment','🎬','#FFEAA7'), ('Shopping','👗','#FFB7B2'),
    ('Education','📚','#A8E6CF'), ('Travel','✈️','#FFD700'),
    ('Utilities','💡','#B5EAD7'), ('Fitness','💪','#FF8C42'),
    ('Personal Care','🌿','#C7CEEA'), ('Savings','💰','#00D4AA'),
    ('Investment','📈','#6C63FF'), ('Gifts & Donations','🎁','#FF9AA2'),
    ('Technology','📱','#74B9FF'), ('Coffee & Snacks','☕','#FDCB6E'),
    ('Groceries','🛒','#55EFC4'), ('Insurance','🛡️','#636E72'),
    ('Subscriptions','📺','#A29BFE'), ('Miscellaneous','🔄','#B2BEC3'),
]

@receiver(post_save, sender=User)
def on_user_created(sender, instance, created, **kwargs):
    if not created:
        return
    # 1. Seed default categories
    from expenses.models import Category
    for name, icon, color in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            user=instance, name=name,
            defaults={'icon': icon, 'color': color, 'is_default': True}
        )
    # 2. Create registration log
    from .models import UserRegistrationLog
    algo = instance.password.split('$')[0] if instance.password else 'unknown'
    UserRegistrationLog.objects.get_or_create(
        user=instance,
        defaults={'password_algo': algo}
    )
