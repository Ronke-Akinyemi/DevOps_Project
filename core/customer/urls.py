from django.urls import path
from customer.views import UserCustomersView, UserSingleCustomerView, CustomerTransactionView, CustomerPaymentHistory, CustomerPurchaseHistory


urlpatterns = [
    path("single/<uuid:id>/", UserSingleCustomerView.as_view(), name="user_single_customers"),
    path("fund/<uuid:id>/", CustomerTransactionView.as_view(), name="fund_customer"),
    path("wallet_history/<uuid:id>/", CustomerPaymentHistory.as_view(), name="wallet_customer"),
    path("purchase_history/<uuid:id>/", CustomerPurchaseHistory.as_view(), name="purcchase_customer"),
    path("<uuid:id>/", UserCustomersView.as_view(), name="user_customers")
]