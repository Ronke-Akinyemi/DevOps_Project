from django.urls import path
from .views import *

urlpatterns = [
    path('sales/<uuid:id>/', SalesAnalyticView.as_view(), name="sales_analytic"),
    path('products/<uuid:id>/', ProductAnalytics.as_view(), name="sales_analytic"),
    path('customers/<uuid:id>/', CustomerAnalytics.as_view(), name="sales_analytic"),
]