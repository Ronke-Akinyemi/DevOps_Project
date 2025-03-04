from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from customer.models import  Customer, CustomerWalletTransaction
from customer.serializers import UserCustomerSerializer, CustomerTransactionSerializer, CustomerPurchaseHistorySerializer
from rest_framework.permissions import IsAuthenticated
from utils.pagination import CustomPagination
from utils.permissions import  IsSubscribed
from django.shortcuts import get_object_or_404
from business.models import Business
from django.db.models import Q, Sum
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from sale.models import Sale
from django.db.models import Count
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from user.models import SyncSubscription

# Create your views here.

class UserCustomersView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = UserCustomerSerializer
    pagination_class = CustomPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description='Search by name, email, phone',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('status', openapi.IN_QUERY, description='Filter by status',
                              type=openapi.TYPE_STRING, enum=['MOST_ACTIVE', 'LEAST_ACTIVE', 'DEBTS'], required=False),
        ]
    )
    def get(self, request, id):
        queryset = self.get_queryset()
        search_param = self.request.GET.get("search", None)
        if search_param:
            queryset = queryset.filter(Q(id__icontains=search_param) | Q(name__icontains=search_param) | Q(phone__icontains=search_param) | Q(email__icontains=search_param))
        cus_status = self.request.GET.get("status", None)
        customer_count = queryset.count()
        if cus_status == 'MOST_ACTIVE':
            queryset = queryset.order_by('-lastSales')
        elif cus_status == 'LEAST_ACTIVE':
            queryset = queryset.order_by('lastSales')
        elif cus_status == "DEBTS":
            queryset = queryset.filter(wallet__lt = 0).order_by('wallet')
        else:
            queryset = queryset.order_by("-created_at")
        page = self.paginate_queryset(queryset)
        total_debt = queryset.filter(wallet__lt=0).aggregate(Sum('wallet'))['wallet__sum'] or 0
        total_wallet = queryset.filter(wallet__gt=0).aggregate(Sum('wallet'))['wallet__sum'] or 0
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response({
                'total_debt': total_debt,
                'total_wallet':total_wallet,
                'customer_count':customer_count,
                'data':serializer.data,
                })
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'total_debt': total_debt,
            'total_wallet':total_wallet,
            'customer_count':customer_count,
            'data': serializer.data,
        }, status=status.HTTP_200_OK)
    def post(self, request, id):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = get_object_or_404(Business, id=id, owner=user)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_customers_count = Customer.objects.filter(business__owner=user, created_at__gte=thirty_days_ago).count()
        active_sub = SyncSubscription.objects.filter(code=user.subscription).first()
        if not active_sub:
            return Response(data={"message": "User not subscribed"}, status= status.HTTP_400_BAD_REQUEST)
        if (recent_customers_count >= active_sub.customers_count) and (active_sub.customers_count != -1 ):
            return Response(data={"message": "Maximum number of customers reached for last 30 days"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(business=business)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        user = self.request.user
        id = self.kwargs["id"]
        return Customer.objects.filter(Q(business__owner=user) | Q(business__attendants=user), business=id).distinct()
    
class UserSingleCustomerView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = UserCustomerSerializer
    pagination_class = CustomPagination
    def get_queryset(self):
        user = self.request.user
        id = self.kwargs["id"]
        return get_object_or_404(Customer, Q(business__owner=user) | Q(business__attendants=user), id=id)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        user = request.user
        customer = get_object_or_404(Customer, Q(business__owner=user) | Q(business__attendants=user), id=id)
        serializer = self.serializer_class(instance=customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        customer = get_object_or_404(Customer, business__owner=user, id=id)
        customer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class CustomerTransactionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = CustomerTransactionSerializer
    pagination_class = CustomPagination
    def get_queryset(self):
        user = self.request.user
        id = self.kwargs["id"]
        return CustomerWalletTransaction.objects.filter(Q(customer__business__owner=user) | Q(customer__business__attendants=user), customer__id=id).order_by("-created_at").distinct()
    def post(self, request, id):
        user = request.user
        customer = get_object_or_404(Customer, Q(business__owner=user) | Q(business__attendants=user), id=id)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        type = serializer.validated_data.get("type")
        amount = serializer.validated_data.get("amount")
        if type == "DEPOSIT":
            balance = customer.wallet + amount
        else:
            balance = customer.wallet - amount
        if balance < 0:
            return Response(data={"message": "Amount greater than available balance"}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            serializer.save(customer=customer, initial = customer.wallet, balance=balance, status="SUCCESSFUL", attendance=user)
            customer.wallet = balance
            customer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

class CustomerPaymentHistory(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = CustomerTransactionSerializer
    pagination_class = CustomPagination
    def get_queryset(self):
        user = self.request.user
        id = self.kwargs["id"]
        return CustomerWalletTransaction.objects.filter(Q(customer__business__owner=user) | Q(customer__business__attendants=user), customer__id=id).order_by("-created_at").distinct()
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

class CustomerPurchaseHistory(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = CustomerPurchaseHistorySerializer
    pagination_class = CustomPagination
    def get_queryset(self):
        user = self.request.user
        id = self.kwargs["id"]
        return Sale.objects.filter(Q(business__owner=user) | Q(business__attendants=user), customer__id=id ).order_by("-created_at").distinct()
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

