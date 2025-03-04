from rest_framework import serializers
from expenses.models import Expenses
from rest_framework import serializers

class ExpensesSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField(read_only=True)
    name = serializers.CharField(max_length=200)
    category_id = serializers.UUIDField(write_only=True)
    amount = serializers.IntegerField(min_value=1)
    date = serializers.DateField()
    note= serializers.CharField(required=False)
    added_by = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Expenses
        fields = ["id", "name","category","category_id", "amount", "date", "note", "added_by"]
    def get_category(self, obj):
        return {"id": obj.category.id ,"name": obj.category.name} if obj.category else None
    def get_added_by(self, obj):
        return f"{obj.added_by.firstname} {obj.added_by.lastname}" if obj.added_by else None