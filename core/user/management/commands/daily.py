from django.core.management.base import BaseCommand
from authentication.models import User
from django.utils.timezone import now
from django.db import transaction

class Command(BaseCommand):
    help = "Update subscriptions"
    def handle(self, *args, **kwargs):
        self.stdout.write("Starting subscription update process...")
        self.check_overdue_subscription()
        self.stdout.write("Subscription update process completed.")
    def check_overdue_subscription(self):
        users_with_subs = User.objects.filter(
            is_subscribed=True,
            subscription_end_date__lte=now().date()
        )
        # .prefetch_related('user_business')
        if not users_with_subs.exists():
            return
        # Use a transaction for atomic updates
        with transaction.atomic():
            for user in users_with_subs:
                # Bulk update businesses linked to the user
                # businesses = user.user_business.all()
                # businesses.update(is_active=False)  # Bulk update
                user.is_subscribed = False
                user.save()
                self.stdout.write(f"Updated subscription for user {user.id}")
        self.stdout.write(f"Processed {users_with_subs.count()} users.")