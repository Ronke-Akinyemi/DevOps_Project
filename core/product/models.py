from django.db import models
import uuid
from category.models import Category
from business.models import Supplier
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
# Create your models here.

User = get_user_model()


STOCK_STATUS = [
    ("IN-STOCK", "In stock"),
    ("LOW", "Low stock"),
    ("OUT-OF-STOCK", "Out of stock"),
]

DISCOUNT_TYPE = [
    ("PERCENTAGE", "Percentage off"),
    ("PRICE", "Price Slash")
]

PRODUCT_UNIT = [
    ("Pcs", "Pieces"),
    ("Kg", "Kilogram"),
    ("Bag", "Bags"),
    ("Box", "Box"),
    ("Ctn", "Ctn"),
    ("Ltd", "Ltd"),
    ("Pair", "Pair"),
    ("Gram", "Gram"),
    ("Feet", "Feet"),
    ("Roll", "Roll"),
    ("Meter", "Meter"),
    ("Mil", "Mil"),
    ("Bottle", "Bottle"),
    ("Bundle","Bundle"),
    ("Ml", "Ml"),
    ("Ton", "Ton"),
    ("Dozen", "Dozen"),
    ("Mg", "Mg"),
    ("Gr", "Gr")
]


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    sku = models.CharField(max_length=50, null=True, blank=True)
    image = models.ImageField(upload_to="product", null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    expiry_date = models.DateField(null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField()
    sold = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=10, choices=PRODUCT_UNIT, default=PRODUCT_UNIT[0][0])
    low_stock_threshold = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    status = models.CharField(max_length=12, choices=STOCK_STATUS, default=STOCK_STATUS[0][0])
    # currency = models.CharField(max_length=5, default="NGN")
    cost_price = models.IntegerField(validators=[MinValueValidator(1)])
    selling_price = models.IntegerField(validators=[MinValueValidator(1)])
    discount = models.DecimalField(default=0,decimal_places=2,max_digits=10, validators=[MinValueValidator(0)])
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE, default=DISCOUNT_TYPE[0][0])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def image_url(self):
        return self.image.url if self.image else None
    def __str__(self):
        return f"{self.name} - {self.quantity} by {self.category.business.name}"


STOCKING_PAYMENT_STATUS = [
    ("PAID", "Paid"),
    ("UNPAID", "Unpaid")
]

RESTOCK_PAYMENT_METHOD = [
    ("FULL", "Paid in full"),
    ("PART", "Partial"),
    ("CREDIT", "Credit")
]
class ProductStocking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quantity = models.IntegerField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="supplier_stocking")
    cost_price = models.IntegerField(validators=[MinValueValidator(1)])
    selling_price = models.IntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=10, choices=STOCKING_PAYMENT_STATUS, default=STOCKING_PAYMENT_STATUS[0][0])
    restock_amount = models.IntegerField(validators=[MinValueValidator(1)])
    payment_method = models.CharField(max_length=15, choices=RESTOCK_PAYMENT_METHOD, default=RESTOCK_PAYMENT_METHOD[0][0])
    amount_paid = models.IntegerField(default=0)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.product.name} - {self.quantity} - {self.created_at}"
