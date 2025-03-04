from django.contrib import admin
from user.models import UserSubscriptions, SyncSubscription, MarketerCommision
# Register your models here.

admin.site.register(SyncSubscription)
admin.site.register(UserSubscriptions)
admin.site.register(MarketerCommision)
