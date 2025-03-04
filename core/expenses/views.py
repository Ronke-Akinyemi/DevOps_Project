from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import status, generics
from rest_framework.response import Response
from utils.pagination import CustomPagination
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from business.models import Business
from expenses.serializers import ExpensesSerializer
from expenses.models import Expenses
from category.models import Category
from django.db.models import Sum, Count, Q
from  utils.permissions import IsBusinessOwner, IsSubscribed
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from utils.date import CustomDateFormating
# Create your views here.

class UserExpensesView(generics.GenericAPIView):
    serializer_class = ExpensesSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    pagination_class = CustomPagination
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description='Filter by category',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('search', openapi.IN_QUERY, description='search by expense name',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description='Start date',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description='End date',
                              type=openapi.TYPE_STRING, required=False)
        ]
    )
    def get(self, request, id):
        queryset = self.get_queryset()
        total_expenses = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response({
                'total_expenses':total_expenses,
                'data':serializer.data})
        serializer = self.serializer_class(queryset, many=True)
        return Response({'total_expenses':total_expenses,'data':serializer.data}, status=status.HTTP_200_OK)
    def post(self, request, id):
        user = request.user
        business = get_object_or_404(Business, owner=user, id=id)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data.pop("category_id", None)
        category = get_object_or_404(Category, type="EXPENSES", id=category_id, business = business)
        with transaction.atomic():
            serializer.save(business=business, category=category, added_by=user)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def get_queryset(self):
        business_id = self.kwargs['id']
        start_date = self.request.GET.get("start_date")
        search = self.request.GET.get("search")
        end_date = self.request.GET.get("end_date")
        category = self.request.GET.get("category")
        start_date, end_date, _ = CustomDateFormating.start_end_date(start_date, end_date)
        user = self.request.user
        expenses = Expenses.objects.filter(business__id=business_id, business__owner=user, date__range=[start_date, end_date]).order_by("-date").distinct()
        if search:
            expenses = expenses.filter(Q(name__icontains= search) | Q(id__icontains=search))
        if category:
            expenses = expenses.filter(category__id = category)
        return expenses

class UserExpensesSingleCategoryView(generics.GenericAPIView):
    serializer_class = ExpensesSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    pagination_class = CustomPagination
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs["id"]
        return get_object_or_404(Expenses, business__owner=user, id=id)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        user = request.user
        expenses = get_object_or_404(Expenses, id=id, business__owner=user)
        serializer = self.serializer_class(instance=expenses, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data.pop("category_id", None)
        if category_id:
            category = get_object_or_404(Category, type="EXPENSES", id=category_id, business__owner = user)
            serializer.save(category=category)
        else:
            serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        user = request.user
        expenses = get_object_or_404(Expenses, id=id, business__owner=user)
        expenses.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
