from django.db import models
import uuid
from product.models import Product
from business.models import Business, BusinessBank
from customer.models import Customer
from django.contrib.auth import get_user_model
from django.utils import timezone
from service.models import Service
# Create your models here.

User = get_user_model()

PAYMENT_METHOD = [
    ("CREDIT", "Credit"),
    ("PARTIAL", "Partial"),
    ("CASH", "Cash"),
    ("MYCLIQ", "Mycliq"),
    ("BANK", "Bank"),
    ("ADVANCE", "Advance balance")
]

PAYMENT_STATUS = [
    ("PAID", "Fully paid"),
    ("UNPAID", "Outstanding debt")
]

class Sale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(default=timezone.now)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    attendant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(decimal_places=2,max_digits=10)
    balance = models.DecimalField(decimal_places=2,max_digits=10, default=0)
    due_date = models.DateField(null=True, blank=True)
    payment_status = models.CharField(max_length=6, default=PAYMENT_STATUS[0][0], choices=PAYMENT_STATUS)
    description = models.TextField(blank=True, null=True)
    method = models.CharField(max_length=10, default=PAYMENT_METHOD[0][0], choices=PAYMENT_METHOD)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.customer.name if self.customer else "ANNONYMOUS"} in Sale {self.total_price}'


class PaymentHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount =  models.DecimalField(decimal_places=2,max_digits=10, default=0)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="sale_payment_history")
    method = models.CharField(max_length=10, default=PAYMENT_METHOD[0][0], choices=PAYMENT_METHOD)
    bank = models.ForeignKey(BusinessBank, related_name="bank_payment_history", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SaleProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="sale_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_sales")
    unit_price = models.DecimalField(decimal_places=2,max_digits=10)
    profit = models.DecimalField(decimal_places=2,max_digits=10, default=0)
    discount = models.DecimalField(decimal_places=2,max_digits=10, default=0)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} in Sale {self.sale.id} == {self.quantity}"
class SaleService(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="sale_services")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="service_sales")
    discount = models.DecimalField(decimal_places=2,max_digits=10, default=0)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.service.name} in Sale {self.sale.id}"