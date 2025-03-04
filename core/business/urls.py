from django.urls import path
from .views import (UserBusinessView,
                    UserSingleBusinessView,
                    UserSingleBusinessSupplierView,
                    UserBusinessSuppliersView,
                    FundSupplierView,
                    InviteAttendantView,
                    ListAttendanceView,
                    UserBusinessBank,
                    UserSingleBusinessBankView
                    )


urlpatterns = [
    path("supplier/<uuid:id>/", UserBusinessSuppliersView.as_view(), name="business_supplier"),
    path("fund_supplier/<uuid:id>/", FundSupplierView.as_view(), name="business_supplier"),
    path("add_attendant/<uuid:id>/", InviteAttendantView.as_view(), name="invite_attendant"),
    path("list_attendants/<uuid:id>/", ListAttendanceView.as_view(), name="get_attendant_list"),
    path("single_supplier/<uuid:id>/", UserSingleBusinessSupplierView.as_view(), name= "business_supplier_single"),
    path("bank/<uuid:id>/", UserBusinessBank.as_view(), name= "banks"),
    path("single_bank/<uuid:id>/", UserSingleBusinessBankView.as_view(), name= "business_bank_single"),
    path("<uuid:id>/", UserSingleBusinessView.as_view(), name="user_business"),
    path("", UserBusinessView.as_view(), name="user_business"),
]