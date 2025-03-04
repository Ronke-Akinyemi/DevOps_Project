from django.urls import path
from category.views import BusinessCategoryView, BusinessSingleCategoryView


urlpatterns = [
    path("business/<uuid:id>/", BusinessCategoryView.as_view(), name="business_category"),
    path("<uuid:id>/", BusinessSingleCategoryView.as_view(), name="single_category"),
]