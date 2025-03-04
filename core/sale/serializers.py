from rest_framework import serializers
from sale.models import Sale, PAYMENT_METHOD, SaleProduct, SaleService
from datetime import date
from product.models import Product
from itertools import chain


class ProductSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    quantity = serializers.IntegerField(min_value=1, required=False)
    type = serializers.ChoiceField(choices=["PRODUCT", "SERVICE"], default="PRODUCT")
    class Meta:
        ref_name = 'ProductSerializerProduct'
    def validate(self, attrs):
        quantity = attrs.get("quantity")
        type =  attrs.get("type")
        if type == "PRODUCT" and not quantity:
            raise serializers.ValidationError("Quantity must be provided for PRODUCT type")
        return attrs


class UserSalesSerializer(serializers.ModelSerializer):
    date =  serializers.DateField()
    customer = serializers.UUIDField(required=False, write_only=True)
    bank = serializers.UUIDField(required=False, write_only=True)
    due_date = serializers.DateField(required=False)
    method = serializers.ChoiceField(choices=[p[0] for p in PAYMENT_METHOD])
    description = serializers.CharField(required=False)
    amount_paid = serializers.DecimalField(decimal_places=2,max_digits=10, required=False, write_only=True)
    partial_method = serializers.ChoiceField(choices=["CASH","BANK"], required=False, write_only=True)
    products = ProductSerializer(many=True, write_only=True)
    class Meta:
        model = Sale
        fields = ["date", "customer", "due_date", "method", "description", "products", "amount_paid", "partial_method", "bank",  "created_at"]

    def validate(self, attrs):
        method = attrs.get("method")
        due_date = attrs.get("due_date")
        customer = attrs.get("customer")
        bank = attrs.get("bank")
        products = attrs.get("products")
        product_ids = [product['id'] for product in products]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Product IDs must be unique")
        amount_paid = attrs.get("amount_paid")
        partial_method = attrs.get("partial_method")

        if method in ["CREDIT", "PARTIAL"] and not due_date:
            raise serializers.ValidationError("Due date required for credit or partial method")
        if method in ["CREDIT", "PARTIAL", "ADVANCE"] and not customer:
            raise serializers.ValidationError("Customer must be provided for this payment method")
        if method == "PARTIAL" and (not amount_paid or not partial_method):
            raise serializers.ValidationError("Partial payment must have amount paid and partial payment method")
        if method == "PARTIAL" and partial_method == "BANK" and not bank:
            raise serializers.ValidationError("Bank ID must be provided for this partial payment method")
        if method == "BANK" and not bank:
            raise serializers.ValidationError("Bank ID must be provided for this payment method")
        if due_date and due_date <= date.today():
            raise serializers.ValidationError("Due date must be a future date.")
        
        return super().validate(attrs)

class SalesCatAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "sku", "image", "sold", "selling_price"]

class SalesProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source= "product.image")
    name = serializers.CharField(source="product.name")
    class Meta:
        model = SaleProduct
        fields = ["image", "name", "quantity", "price","unit_price"]
class SalesServiceSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source= "service.image")
    name = serializers.CharField(source="service.name")
    unit_price = serializers.CharField(source="price")
    class Meta:
        model = SaleService
        fields = ["image", "name", "quantity", "price", "unit_price"]
class OrderHIstorySerializer(serializers.ModelSerializer):
    products = serializers.SerializerMethodField()
    attendant = serializers.SerializerMethodField()
    class Meta:
        model = Sale
        fields = ["id", "date", "attendant", "payment_status", "method", "total_price", "products", "created_at"]

    def get_attendant(self, obj):
        if obj.attendant:
            return f"{obj.attendant.firstname} {obj.attendant.lastname}"
        return None
    def get_products(self, obj):
        sales_products = obj.sale_products.all()
        sales_services = obj.sale_services.all()
        sales_product_serializer =  SalesProductSerializer(sales_products, many=True)
        sales_service_serializer =  SalesServiceSerializer(sales_services, many=True)
        return list(chain(sales_product_serializer.data, sales_service_serializer.data))  