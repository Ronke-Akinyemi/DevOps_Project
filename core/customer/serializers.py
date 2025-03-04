from rest_framework import serializers
from customer.models import Customer, CustomerWalletTransaction, PAYMENT_METHOD, CUSTOMER_TRANSACTION_TYPE
from sale.models import Sale, SaleProduct


# class UserGetCustomerSerializer(serializers.ModelSerializer):
#     business_id = serializers.UUIDField(write_only=True)
#     class Meta:
#         model = Customer
#         fields = ["id", "name", "business_id", "phone", "wallet"]
class UserCustomerSerializer(serializers.ModelSerializer):
    email=serializers.EmailField()
    name = serializers.CharField(max_length=250)
    phone = serializers.CharField(max_length=15)
    wallet = serializers.IntegerField(read_only=True)
    profile_pic = serializers.ImageField(required=False)
    id = serializers.UUIDField(read_only=True)
    class Meta:
        model = Customer
        fields = ["id", "name", "phone", "wallet", "email", "profile_pic"]

class CustomerTransactionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    amount = serializers.IntegerField()
    type = serializers.ChoiceField(choices = [x[0] for x in CUSTOMER_TRANSACTION_TYPE])
    payment_method = serializers.ChoiceField(choices = [x[0] for x in PAYMENT_METHOD])
    note = serializers.CharField(max_length=500, required=False)
    initial = serializers.IntegerField(read_only=True)
    balance = serializers.IntegerField(read_only=True)
    attendance = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CustomerWalletTransaction
        fields = ["id", "amount", "payment_method","type","initial","balance","attendance", "note", "created_at"]
    def get_attendance(self, obj):
        return f"{obj.attendance.firstname} {obj.attendance.lastname}" if obj.attendance else "DELETED ATTENDANT"



class ProductHistorySerializer(serializers.ModelSerializer):
    price = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    class Meta:
        model = SaleProduct
        fields = ["name","image","price", "quantity"]
    def get_price(self, obj):
        return obj.unit_price
    def get_name(self, obj):
        return obj.product.name
    def get_image(self, obj):
        return obj.product.image.url if obj.product.image else None
class CustomerPurchaseHistorySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    attendance = serializers.SerializerMethodField(read_only=True)
    products = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Sale
        fields = ["id","attendant","method", "payment_status", "products","total_price", "balance","created_at", "attendance"]
    
    def get_attendance(self, obj):
        return f"{obj.attendant.firstname} {obj.attendant.lastname}" if obj.attendant else "DELETED ATTENDANT"
    def get_products(self, obj):
        products = obj.sale_products
        return ProductHistorySerializer(products, many=True).data