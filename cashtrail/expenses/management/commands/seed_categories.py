from django.core.management.base import BaseCommand
from expenses.models import Category
from accounts.models import User

DEFAULT_CATEGORIES = [
    ('Food & Dining',    '🍔', '#FF6B6B'),
    ('Transportation',   '🚗', '#45B7D1'),
    ('Housing & Rent',   '🏠', '#96CEB4'),
    ('Health & Medical', '💊', '#DDA0DD'),
    ('Entertainment',    '🎬', '#FFEAA7'),
    ('Shopping',         '👗', '#FFB7B2'),
    ('Education',        '📚', '#A8E6CF'),
    ('Travel',           '✈️', '#FFD700'),
    ('Utilities',        '💡', '#B5EAD7'),
    ('Fitness',          '💪', '#FF8C42'),
    ('Personal Care',    '🌿', '#C7CEEA'),
    ('Savings',          '💰', '#00D4AA'),
    ('Investment',       '📈', '#6C63FF'),
    ('Gifts & Donations','🎁', '#FF9AA2'),
    ('Technology',       '📱', '#74B9FF'),
    ('Coffee & Snacks',  '☕', '#FDCB6E'),
    ('Groceries',        '🛒', '#55EFC4'),
    ('Insurance',        '🛡️', '#636E72'),
    ('Subscriptions',    '📺', '#A29BFE'),
    ('Miscellaneous',    '🔄', '#B2BEC3'),
]

class Command(BaseCommand):
    help = 'Seed default categories for all users who have none'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='Email of specific user (optional)')
        parser.add_argument('--all', action='store_true', help='Apply to all users')

    def handle(self, *args, **options):
        if options.get('user'):
            try:
                users = [User.objects.get(email=options['user'])]
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User not found: {options['user']}"))
                return
        else:
            users = User.objects.all()

        total_created = 0
        for user in users:
            if user.categories.exists() and not options.get('all'):
                self.stdout.write(f'Skipping {user.email} (already has categories)')
                continue
            created = 0
            for name, icon, color in DEFAULT_CATEGORIES:
                _, was_created = Category.objects.get_or_create(
                    user=user, name=name,
                    defaults={'icon': icon, 'color': color, 'is_default': True}
                )
                if was_created:
                    created += 1
            total_created += created
            self.stdout.write(self.style.SUCCESS(f'✓ {user.email}: {created} categories created'))

        self.stdout.write(self.style.SUCCESS(f'\nDone. Total created: {total_created}'))
