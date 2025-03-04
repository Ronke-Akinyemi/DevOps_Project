from django.db import models
from category.models import Category
import uuid

# Create your models here.

class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="service", null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.name} - {self.amount} by {self.category.business.name}"