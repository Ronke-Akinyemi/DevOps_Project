from rest_framework import serializers
from product.models import Product, ProductStocking, STOCK_STATUS, DISCOUNT_TYPE, PRODUCT_UNIT, RESTOCK_PAYMENT_METHOD
from datetime import date
from service.models import Service


# class GetProductsSerializer(serializers.ModelSerializer):
#     category = serializers.SerializerMethodField(read_only=True)
#     class Meta:
#         model = Product
#         fields = ["id","name", "image", "sku", "status", "selling_price", "sold", "quantity", "category"]
#     def get_category(self, obj):
#         return obj.category.name
class GetProductsSerializer(serializers.Serializer):
    def to_representation(self, instance):
        if isinstance(instance, Product):
            return {
                "id": instance.id,
                "name": instance.name,
                "image": instance.image.url if instance.image else None,
                "sku": instance.sku,
                "status": instance.status,
                "selling_price": instance.selling_price,
                "cost_price": instance.cost_price,
                "sold": instance.sold,
                "quantity": instance.quantity,
                "category": instance.category.name,
                "type": "PRODUCT"
            }
        elif isinstance(instance, Service):
            return {
                "id": instance.id,
                "name": instance.name,
                "image": instance.image.url if instance.image else None,
                "description": instance.description,
                "amount": instance.amount,
                "category": instance.category.name,
                "type": "SERVICE"
            }
        return super().to_representation(instance)


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(write_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField()
    sku = serializers.CharField(max_length=50,required=False)
    image= serializers.ImageField()
    expiry_date = serializers.DateField(required=False)
    supplier_id = serializers.UUIDField(write_only=True, required=False)
    payment_method = serializers.ChoiceField(choices=[p[0] for p in RESTOCK_PAYMENT_METHOD], required=False, write_only=True)
    amount_paid = serializers.DecimalField(decimal_places=2,max_digits=10, required=False)
    supplier = serializers.SerializerMethodField(read_only=True)
    quantity = serializers.IntegerField()
    sold = serializers.IntegerField(read_only=True)
    low_stock_threshold = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=[s[0] for s in STOCK_STATUS], required=False)
    unit = serializers.ChoiceField(choices=[u[0] for u in PRODUCT_UNIT], required=False)
    # currency = serializers.CharField(required=False)
    cost_price= serializers.DecimalField(max_digits=10, decimal_places=2)
    selling_price= serializers.DecimalField(max_digits=10, decimal_places=2)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    discount_type = serializers.ChoiceField(choices=[d[0] for d in DISCOUNT_TYPE], required=False)
    total_stock_price = serializers.SerializerMethodField(read_only=True)
    history = serializers.SerializerMethodField(read_only=True)
    due_date = serializers.DateField(required=False)

    class Meta:
        model = Product
        fields = ["id","name","sku","image", "category","category_id", "expiry_date", "supplier", "supplier_id",
                  "payment_method", "amount_paid",
                  "quantity", "low_stock_threshold", "status","cost_price",
                  "selling_price", "discount", "discount_type", "unit", "total_stock_price",
                  "sold", "history", "due_date"]
    def get_category(self, obj):
        return obj.category.name
    def get_total_stock_price(self, obj):
        return obj.quantity * obj.cost_price
    def get_supplier(self, obj):
        return obj.supplier.name if obj.supplier else None
    def get_history(self, obj):
        history_data = ProductStocking.objects.filter(product=obj)
        history_serializer = SupplierProductRestockSerializer(history_data, many=True)
        return history_serializer.data
    def validate(self, attrs):
        discount = attrs.get("discount")
        discount_type = attrs.get("discount_type")
        expiry_date = attrs.get("expiry_date")
        cost_price = attrs.get("cost_price")
        selling_price = attrs.get("selling_price")
        supplier_id = attrs.get("supplier_id")
        payment_method = attrs.get("payment_method")
        amount_paid = attrs.get("amount_paid")
        due_date = attrs.get("due_date")
        if supplier_id and not payment_method:
            raise serializers.ValidationError("Select a payment method used for supplier")            
        if payment_method in [RESTOCK_PAYMENT_METHOD[1][0], RESTOCK_PAYMENT_METHOD[2][0]] and not supplier_id:
            raise serializers.ValidationError("Supplier is required when payment is not full")
        if payment_method in [RESTOCK_PAYMENT_METHOD[1][0], RESTOCK_PAYMENT_METHOD[2][0]] and not due_date:
            raise serializers.ValidationError("Date due is required when payment is not full")
        if payment_method == RESTOCK_PAYMENT_METHOD[1][0] and not amount_paid:
            raise serializers.ValidationError("Amount paid must be specified for partial payment")
        if due_date and due_date <= date.today():
            raise serializers.ValidationError("Date due must be a future date")
        if (selling_price and cost_price) and (selling_price <= cost_price):
            raise serializers.ValidationError("Selling price must be above cost price")
        if expiry_date and (expiry_date <= date.today()):
            raise serializers.ValidationError("Expiry date must be in the future")
        
        if discount:
            if (discount_type == "PERCENTAGE" or not discount_type) and discount > 90:
                raise serializers.ValidationError("Discount about 90%")
            if discount_type == "PRICE" and discount >= selling_price:
                raise serializers.ValidationError("Discount must be less than the selling price")
        return attrs
        
class SupplierProductRestockSerializer(serializers.ModelSerializer):
    cost_price = serializers.IntegerField()
    selling_price = serializers.IntegerField()
    restock_amount = serializers.IntegerField(read_only=True)
    quantity = serializers.IntegerField(min_value = 1)
    supplier_id = serializers.UUIDField(write_only=True, required=False)
    payment_method = serializers.ChoiceField(choices=[p[0] for p in RESTOCK_PAYMENT_METHOD])
    amount_paid = serializers.DecimalField(decimal_places=2,max_digits=10, required=False)
    due_date = serializers.DateField(required=False)
    class Meta:
        model = ProductStocking
        fields = ["id", "cost_price", "selling_price","supplier_id", "quantity", "restock_amount","amount_paid","payment_method","due_date", "created_at"]
    def validate(self, attrs):
        supplier = attrs.get('supplier_id')
        due_date = attrs.get('due_date')
        payment_method = attrs.get('payment_method')
        amount_paid = attrs.get("amount_paid")
        cost_price = attrs.get("cost_price")
        selling_price = attrs.get("selling_price")
        if (selling_price and cost_price) and (selling_price <= cost_price):
            raise serializers.ValidationError("Selling price must be above cost price")
        if payment_method != RESTOCK_PAYMENT_METHOD[0][0] and not supplier:
            raise serializers.ValidationError("Supplier is required when payment is not full")
        if payment_method != RESTOCK_PAYMENT_METHOD[0][0] and not due_date:
            raise serializers.ValidationError("Date due is required when payment is not full")
        if payment_method == RESTOCK_PAYMENT_METHOD[1][0] and not amount_paid:
            raise serializers.ValidationError("Amount paid must be specified for partial payment")
        if due_date and due_date <= date.today():
            raise serializers.ValidationError("Date due must be a future date")
        
        
        return attrs
