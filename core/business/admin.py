from django.contrib import admin
from business.models import Business, Supplier, SupplierFunding, BusinessBank

# Register your models here.

admin.site.register(Business)
admin.site.register(Supplier)
admin.site.register(SupplierFunding)
admin.site.register(BusinessBank)