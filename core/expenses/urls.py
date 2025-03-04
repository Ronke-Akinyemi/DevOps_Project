from django.urls import path
from expenses.views import UserExpensesView, UserExpensesSingleCategoryView

urlpatterns = [
    path("business/<uuid:id>/", UserExpensesView.as_view(), name="business_category"),
    path("<uuid:id>/", UserExpensesSingleCategoryView.as_view(), name="single_category"),
]