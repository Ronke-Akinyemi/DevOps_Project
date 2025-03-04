from django.urls import path
from product.views import UserProductView, UserProductSingleView, UserSupplierProductRestock

urlpatterns = [
    path("single_product/<str:id>/", UserProductSingleView.as_view(), name="single_product"),
    path("restock/<str:id>/", UserSupplierProductRestock.as_view(), name="supplier_restock_product"),
    path("business/<str:id>/", UserProductView.as_view(), name="business_product"),
]