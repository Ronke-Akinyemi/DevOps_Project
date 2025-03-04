from rest_framework import serializers
from service.models import Service

class ServiceSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(write_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    amount = serializers.IntegerField()
    image= serializers.ImageField(required=False)
    class Meta:
        model = Service
        fields = ["id", "name", "category", "category_id","description", "amount", "image"]
    def validate_amount(self, amt):
        if amt < 1:
            raise serializers.ValidationError("Amount must be greater than 0")
        return amt
    def get_category(self, obj):
        return obj.category.name