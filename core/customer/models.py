from django.db import models
from business.models import Business
import uuid
from django.contrib.auth import get_user_model
# Create your models here.

User  = get_user_model()

class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="business_customers")
    name = models.CharField(max_length=250)
    phone = models.CharField(max_length=15)
    profile_pic = models.ImageField(upload_to="customer", null=True, blank=True)
    email = models.EmailField()
    email_marketting = models.BooleanField(default=False)
    sms_marketting = models.BooleanField(default=False)
    wallet = models.BigIntegerField(default=0)
    purchase_value = models.PositiveBigIntegerField(default=0)
    lastSales = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} - {self.business.name}"



CUSTOMER_TRANSACTION_TYPE = [
    ("DEPOSIT", "Deposit"),
    ("WITHDRAWAL", "Withdrawal")
]
TRANSACTION_STATUS = [
    ("PENDING", "Pending"),
    ("SUCCESSFUL", "Successful"),
    ("CANCELLED", "Cancelled")
]
PAYMENT_METHOD = [
    ("CASH", "Cash Payment"),
    ("BANK", "Bank Transfer")
]
class CustomerWalletTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=CUSTOMER_TRANSACTION_TYPE, default=CUSTOMER_TRANSACTION_TYPE[0][0])
    initial = models.IntegerField()
    amount = models.IntegerField()
    balance = models.IntegerField() 
    status = models.CharField(max_length=12, choices=TRANSACTION_STATUS, default=TRANSACTION_STATUS[0][0])
    payment_method = models.CharField(max_length=4, choices=PAYMENT_METHOD, default=PAYMENT_METHOD[0][0])
    note = models.TextField(null=True, blank=True)
    attendance = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_ransaction")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.amount} {self.type} -- {self.customer.name} -- {self.customer.business.name}"

