from django.contrib import admin
from customer.models import Customer, CustomerWalletTransaction

# Register your models here.
admin.site.register(Customer)
admin.site.register(CustomerWalletTransaction)
