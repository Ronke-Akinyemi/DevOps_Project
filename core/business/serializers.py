from rest_framework import serializers
from business.models import Business, Supplier, SupplierFunding, BUSINESS_TYPES, CURRENCIES, PAYMENT_METHOD, PAYMENT_TYPE, BusinessBank
from django.contrib.auth import get_user_model
from product.models import ProductStocking


User = get_user_model()
class BusinessSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    owner = serializers.SerializerMethodField(read_only=True)
    currency = serializers.ChoiceField(choices=[c[0] for c in CURRENCIES])
    type = serializers.ChoiceField(
        choices=[t[0] for t in BUSINESS_TYPES])
    class Meta:
        model = Business
        fields = ["id", "name","owner", "type", "country", "state", "city", "street",
                  "logo", "currency"]
    def get_owner(self, obj):
        return {"id": obj.owner.id, "firstname": obj.owner.firstname, "lastname": obj.owner.lastname, "email":obj.owner.email, "phone":obj.owner.phone}
    def validate(self, attrs):
        currency = attrs.get("currency")
        attrs["currency"] = currency.upper()
        return super().validate(attrs)


class BusinessBankDetails(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    bank_name = serializers.CharField(max_length=100)
    account_name = serializers.CharField(max_length=100)
    account_number = serializers.CharField(max_length=100)
    class Meta:
        model = BusinessBank
        fields = ["id", "bank_name", "account_name", "account_number"]

class SupplierStockingHistorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    supplier = serializers.SerializerMethodField()
    class Meta:
        model = ProductStocking
        fields = ["id","status", "created_at", "quantity", "cost_price", "name", "supplier"]
    def get_name(self, obj):
        return obj.product.name
    def get_supplier(self, obj):
        return obj.supplier.name if obj.supplier else None
class BusinessSupplierSerializer(serializers.ModelSerializer):
    wallet = serializers.IntegerField(required=False, min_value=1)
    supply_history = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Supplier
        fields = ["id", "name", "phone", "wallet", "supply_history"]
    def get_supply_history(self, obj):
        history = obj.supplier_stocking
        return SupplierStockingHistorySerializer(history, many=True).data

class FundSupplier(serializers.ModelSerializer):
    supplier = serializers.SerializerMethodField(read_only=True)
    method = serializers.ChoiceField(choices=[p[0] for p in PAYMENT_METHOD])
    type = serializers.ChoiceField(choices=[p[0] for p in PAYMENT_TYPE])
    amount = serializers.IntegerField(min_value= 1)
    class Meta:
        model = SupplierFunding
        fields = ["id", "amount", "method", "supplier", "type"]
    def get_supplier(self, obj):
        return {"id": obj.supplier.id, "name": obj.supplier.name}

class InviteAttendantSerializer(serializers.Serializer):
    firstname = serializers.CharField(max_length=50)
    lastname = serializers.CharField(max_length=50)
    phone = serializers.CharField()

class GetAttendanceSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ["id", "name"]
    def get_name(self, obj):
        return f"{obj.firstname} {obj.lastname}"