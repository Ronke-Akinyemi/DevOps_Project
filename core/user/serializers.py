from rest_framework import serializers
from django.contrib.auth import get_user_model
from user.models import UserSubscriptions, SyncSubscription, SUBSCRIPTION_DURATION_TYPE
from business.models import PAYMENT_METHOD



User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(max_length=50, required=False)
    lastname = serializers.CharField(max_length=50, required=False)
    phone = serializers.CharField(max_length=15, required=False)
    email = serializers.EmailField(required=False)
    new_orders_notification = serializers.BooleanField(required=False)
    orders_status_notification = serializers.BooleanField(required=False)
    payment_receipt_notification = serializers.BooleanField(required=False)
    wallet_update_notification = serializers.BooleanField(required=False)
    low_stock_alert_notification = serializers.BooleanField(required=False)
    out_of_stock_alert_notification = serializers.BooleanField(required=False)
    two_factor_auth = serializers.BooleanField(required=False)
    class Meta:
        model = User
        fields = ["firstname","lastname", "email", "phone","profile_picture",
                  "new_orders_notification", "orders_status_notification","payment_receipt_notification",
                  "wallet_update_notification", "low_stock_alert_notification","out_of_stock_alert_notification","two_factor_auth"]
        
class UserSubcribeSerializer(serializers.Serializer):
    plan = serializers.IntegerField(write_only=True)
    duration = serializers.ChoiceField(choices=[x[0] for x in SUBSCRIPTION_DURATION_TYPE])


class ListPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncSubscription
        fields = ['id', 'name', 'monthly', 'quarterly', 'biannually', 'annually', 'no_of_users', 'no_of_attendants', 'no_of_business',
                  'store_front', 'sales_count', 'invoice_count','inventory_count', 'customers_count', 'track_income', 'in_store_checkout',
                  'bulk_sms', 'bulk_email', 'bank_expenses_traking']

