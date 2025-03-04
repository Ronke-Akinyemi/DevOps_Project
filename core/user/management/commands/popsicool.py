from django.core.management.base import BaseCommand
from authentication.models import User, Marketter
from user.models import UserSubscriptions
from django.utils.timezone import now
from django.db import transaction

class Command(BaseCommand):
    help = "Update subscriptions"
    def handle(self, *args, **kwargs):
        self.stdout.write("Starting subscription update process...")
        self.check_overdue_subscription()
        self.stdout.write("Subscription update process completed.")
    def check_overdue_subscription(self):
        user = User.objects.get(email="theinsighttech@gmail.com")
        subs = UserSubscriptions.objects.filter(user=user).order_by("-created_at")
        for s in subs:
            print(s.status)