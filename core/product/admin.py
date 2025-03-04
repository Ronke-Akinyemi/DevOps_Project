from django.contrib import admin
from product.models import Product, ProductStocking
# Register your models here.

admin.site.register(Product)
admin.site.register(ProductStocking)