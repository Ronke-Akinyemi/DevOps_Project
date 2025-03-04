from django.db import models
import uuid
from django.contrib.auth import get_user_model
from authentication.models import Marketter


# Create your models here.

User = get_user_model()

class SyncSubscription(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=15, default="STARTER")
    monthly = models.IntegerField()
    quarterly = models.IntegerField()
    biannually = models.IntegerField()
    annually = models.IntegerField()
    no_of_users = models.IntegerField(default=1)
    no_of_attendants = models.IntegerField(default=0)
    no_of_business = models.IntegerField(default=0)
    store_front = models.BooleanField(default=False)
    sales_count = models.IntegerField()
    invoice_count = models.IntegerField(default=0)
    inventory_count = models.IntegerField(default=0)
    customers_count = models.IntegerField(default=5)
    track_income = models.BooleanField(default=True)
    in_store_checkout = models.BooleanField(default=False)
    bulk_sms  = models.BooleanField(default=False)
    bulk_email = models.BooleanField(default=False)
    bank_expenses_traking = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name


SUBSCRIPTION_PAYMENT_METHOD = [
    ("PAYSTACK", "Paystack"),
    ("VELVPAY", "Velvepay")
]

SUBSCRIPTION_DURATION_TYPE = [
    ("MONTHLY", "Monthly"),
    ("QUATERLY", "Quarterly"),
    ("BIANNUAL", "Biannual"),
    ("ANNUAL", "Annual"),

]

SUBSCRIPTION_PAYMENT_STATUS = [
    ("PENDING", "Pending Payment"),
    ("SUCCESSFUL", "Successful payment")
]
class UserSubscriptions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_subscriptions")
    plan = models.ForeignKey(SyncSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.IntegerField()
    refrence = models.CharField(blank=True, null=True)
    payment_method = models.CharField(choices=SUBSCRIPTION_PAYMENT_METHOD, default=SUBSCRIPTION_PAYMENT_METHOD[0][0], max_length=50)
    status = models.CharField(max_length=50, choices=SUBSCRIPTION_PAYMENT_STATUS, default=SUBSCRIPTION_PAYMENT_STATUS[0][0])
    payment_url = models.URLField(null=True, blank=True)
    duration_type = models.CharField(max_length=15, default=SUBSCRIPTION_DURATION_TYPE[0][0], choices=SUBSCRIPTION_DURATION_TYPE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.firstname} {self.plan}"
    

class MarketerCommision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    marketer = models.ForeignKey(Marketter, on_delete=models.CASCADE, related_name="marketer_commision")
    description = models.TextField(blank=True, null=True)
    subscription = models.ForeignKey(UserSubscriptions, on_delete=models.SET_NULL, null=True, blank=True, related_name="subscription_by_user")
    amount = models.DecimalField(decimal_places=2, max_digits=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return str(self.id)

