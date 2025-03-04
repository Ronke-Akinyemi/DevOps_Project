from django.db import models
import uuid
from django.contrib.auth import get_user_model


# Create your models here.

User = get_user_model()
BUSINESS_TYPES = [
    ("Food & Restaurant", "Food & Restaurant"),
    ("Beauty & Personal Care", "Beauty & Personal Care"),
    ("Book & Stationery", "Book & Stationery"),
    ("Minimart & Retail", "Minimart & Retail"),
    ("Electronics & Gadget", "Electronics & Gadget"),
    ("Laundry", "Laundry"),
    ("Salon Business", "Salon Business"),
    ("Pharmacy & Health Products", "Pharmacy & Health Products"),
    ("Home & Furniture", "Home & Furniture"),
    ("Construction Material & Suppliers", "Construction Material & Suppliers"),
    ("Logistics & Others", "Logistics & Others"),
]

CURRENCIES = [
    ("NGN", "Nigerian Naira"),
    ("USD", "United state dollar"),
    ("EUR", "Euro"),
    ("GBP", "British Pound Sterling"),
    ("JPY", "Japanese yen"),
    ("CHF", "Swiss Franc"),
    ("CAD", "Canadian Dollar"),
    ("AUD", "Australian Dollar"),
    ("NZD", "New zealand Dollar"),
    ("CNY", "Chinese Yuan"),
    ("INR", "Indian Rupee"),
    ("RUB", "Russian Ruble"),
    ("BRL", "Brazilian Real"),
    ("ZAR", "South African Rand"),
    ("MXN", "Mexican Peso"),
    ("SGD", "Singapore Dollar"),
    ("HKD", "Hong kong Dollar"),
    ("SEK", "Swwedish Krona"),
    ("KES", "Kenya Shillings"),
    ("GHS", "Ghana Cedis")
]
class Business(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_business")
    name = models.CharField(max_length=250)
    type = models.CharField(max_length=50, choices=BUSINESS_TYPES, default=BUSINESS_TYPES[0][0])
    country = models.CharField(max_length=50)
    balance = models.BigIntegerField(default=0)
    attendants = models.ManyToManyField(User, related_name="attendance_businesses", blank=True)
    state = models.CharField(max_length=50)
    currency = models.CharField(max_length=5, choices=CURRENCIES, default=CURRENCIES[0][0])
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to="business")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} by  {self.owner.firstname} {self.owner.lastname} = {self.id}"

class BusinessBank(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="business_banks")
    bank_name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.bank_name} == {self.account_name} == {self.account_number} == {self.business.name} == {self.business.owner.lastname}"


class Supplier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="business_supplier")
    name = models.CharField(max_length=250)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    purchase_value = models.BigIntegerField(default=0)
    wallet = models.BigIntegerField(default=0)
    debt = models.BigIntegerField(default=0)
    balance = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} for {self.business.name}"

PAYMENT_METHOD = [
    ("CASH", "Cash"),
    ("BANK", "Bank Transfer"),
    ("MYCLIQ", "Mycliq")
]
PAYMENT_TYPE = [
    ("DEPOSIT", "Deposit"),
    ("REFUND", "Refund")
]
class SupplierFunding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.PositiveBigIntegerField()
    method = models.CharField(max_length=15, choices=PAYMENT_METHOD, default=PAYMENT_METHOD[0][0])
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=PAYMENT_TYPE, default=PAYMENT_TYPE[0][0])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.type} of {self.amount} to {self.supplier.name} by {self.supplier.business.name}"

# from product.models import Product
# class SupplierRestock(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="product_supply_restock")
#     supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
#     quantity = models.IntegerField()
#     date = models.DateField()
#     amount = models.BigIntegerField()
#     quantity = models.IntegerField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     def __str__(self):
#         return f"{self.product.name} - "