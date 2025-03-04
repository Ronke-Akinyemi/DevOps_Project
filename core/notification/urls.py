from django.urls import path
from . import views

urlpatterns = [
    path("paystack_webhook/", views.PaystackWebhook.as_view(), name="paystack"),
    path("velvpay_webhook/", views.VelvpayWebhook.as_view(), name="velvpay"),
    path("daily_cron/", views.TriggerTaskAPIView.as_view(), name="daily_cron")
    # path('', views.Notify.as_view(), name='notification'),
]