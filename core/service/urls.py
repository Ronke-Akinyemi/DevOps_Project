from django.urls import path
from service.views import *

urlpatterns = [
    path("single_service/<str:id>/", UserServiceSingleView.as_view(), name="business_service_single"),
    path('business/<str:id>/', UserServiceView.as_view(), name="services")
]