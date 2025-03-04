from django.urls import path
from sale.views import *

urlpatterns = [
    path("dashboard/<uuid:id>/", SalesAnalysisView.as_view(), name="sales"),
    path("category/<uuid:id>/", ProductCategoryAnalysis.as_view(), name="category_sales"),
    path("sales_history/<uuid:id>/", SalesHistory.as_view(), name="sales_history"),
    path("order_history/<uuid:id>/", OrderHistory.as_view(), name="order_history"),
    path("<uuid:id>/", UserSaleView.as_view(), name="user_sales")
]