from django.contrib import admin
from sale.models import Sale, PaymentHistory, SaleProduct, SaleService
# Register your models here.

admin.site.register(Sale)
admin.site.register(PaymentHistory)
admin.site.register(SaleProduct)
admin.site.register(SaleService)
