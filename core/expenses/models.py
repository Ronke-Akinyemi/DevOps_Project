from django.db import models
import uuid
from category.models import Category
from business.models import Business
from django.contrib.auth import get_user_model

# Create your models here.
User = get_user_model()
class Expenses(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name =  models.CharField(max_length=200)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="business_expenses")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, related_name="category_expenses", null=True, blank=True)
    amount = models.PositiveBigIntegerField()
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} - by {self.business}"