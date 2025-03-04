from django.db import models
from business.models import Business
from django.contrib.auth import get_user_model
import uuid
# Create your models here.

User = get_user_model()

CATEGORY_TYPE = [
    ("PRODUCT", "Product category"),
    ("EXPENSES", "Expenses category")
]
class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="business_categories")
    type = models.CharField(max_length=10, choices=CATEGORY_TYPE, default=CATEGORY_TYPE[0][0])
    name= models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} - {self.type} category for {self.business.name} by {self.business.owner.firstname} {self.business.owner.lastname}"
    