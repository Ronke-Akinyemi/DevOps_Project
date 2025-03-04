from django.shortcuts import render
from business.serializers import (
    BusinessSerializer,
    BusinessSupplierSerializer,
    FundSupplier,
    InviteAttendantSerializer,
    GetAttendanceSerializer,
    BusinessBankDetails)
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from business.models import Business, Supplier, BusinessBank
from django.db import transaction
from django.db.models import Q
from utils.pagination import CustomPagination
from django.shortcuts import get_object_or_404
from user.models import SyncSubscription
from django.contrib.auth import get_user_model
import random
import string
from utils.email import SendMail
from utils.permissions import IsBusinessOwner, IsSubscribed
from django.db.models import Sum, Count, Q, F, DecimalField
# Create your views here.

User = get_user_model()
class UserBusinessView(generics.GenericAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    def get(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.serializer_class(data=request.data)
        active_sub = SyncSubscription.objects.filter(code=user.subscription).first()
        if not active_sub:
            return Response(data={"message": "User not subscribed"}, status= status.HTTP_402_PAYMENT_REQUIRED)
        businesses = Business.objects.filter(owner=user).count()
        if (businesses >= active_sub.no_of_business) and (active_sub.no_of_business != -1 ):
            return Response(data={"message": "Maximum number of businesses reached for your plan"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(owner=user)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        return Business.objects.filter(Q(owner=user) | Q(attendants=user)).order_by("-created_at").distinct()

class UserBusinessBank(generics.GenericAPIView):
    serializer_class = BusinessBankDetails
    permission_classes = [IsAuthenticated, IsSubscribed]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs.get('id')
        return BusinessBank.objects.filter(Q(business__owner=user) | Q(business__attendants=user), business__id=id).order_by("-created_at").distinct()
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status = status.HTTP_200_OK)
    def post(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(business=get_object_or_404(Business, owner=user, id=id))
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)


class UserSingleBusinessBankView(generics.GenericAPIView):
    serializer_class = BusinessBankDetails
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    pagination_class = CustomPagination
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs.get("id")
        return get_object_or_404(BusinessBank, id=id, business__owner=user)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        bank = self.get_queryset()
        serializer = self.serializer_class(instance=bank, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        bank = self.get_queryset()
        bank.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserSingleBusinessView(generics.GenericAPIView):
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs.get("id")
        return Business.objects.filter(Q(owner=user) | Q(attendants=user), id=id).order_by("-created_at")
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        business = get_object_or_404(Business, id=id, owner=user)
        serializer = self.serializer_class(instance=business, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        business = get_object_or_404(Business, id=id, owner=user)
        attendants = business.attendants.all()
        with transaction.atomic():
            for att in attendants:
                att.delete()
            business.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserBusinessSuppliersView(generics.GenericAPIView):
    serializer_class = BusinessSupplierSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    def get(self, request, id):
        queryset = self.get_queryset()
        supplier_with_debt = queryset.filter(wallet__lt=0)
        supplier_with_no_debt = queryset.filter(wallet__gt=0)
        debt = supplier_with_debt.aggregate(wallet=Sum(F('wallet')))["wallet"] or 0
        wallet = supplier_with_no_debt.aggregate(wallet=Sum(F('wallet')))["wallet"] or 0
        count = queryset.count()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response({"wallet_balance":wallet,"debt":debt, "supplier_count":count,  "data":serializer.data})
        serializer = self.serializer_class(queryset, many=True)
        return Response({"wallet_balance":wallet,"debt":debt, "supplier_count":count,  "data":serializer.data}, status=status.HTTP_200_OK)
    def post(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.is_subscribed:
            return Response(data={"message": "Your subscription is expired."}, status=status.HTTP_401_UNAUTHORIZED)

        business = get_object_or_404(Business, id=id, owner=user)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(business=business)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        return Supplier.objects.filter(Q(business__owner=user) | Q(business__attendants=user)).order_by("-created_at").distinct()

class UserSingleBusinessSupplierView(generics.GenericAPIView):
    serializer_class = BusinessSupplierSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs["id"]
        return get_object_or_404(Supplier,Q(business__owner=user) | Q(business__attendants=user), id=id)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        supplier = get_object_or_404(Supplier, business__owner=user, id=id)
        serializer = self.serializer_class(instance=supplier, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        supplier = get_object_or_404(Supplier, business__owner=user, id=id)
        supplier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FundSupplierView(generics.GenericAPIView):
    serializer_class = FundSupplier
    permission_classes = [IsAuthenticated, IsSubscribed]
    def post(self, request, id):
        user = request.user
        supplier = get_object_or_404(Supplier, id=id, business__owner=user)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction_type = serializer.validated_data.get("type", "DEPOSIT")
        amount = serializer.validated_data.get("amount")
        if transaction_type != "DEPOSIT" and supplier.wallet < amount:
            return Response(data={"message": "Insufficient fund in supplier wallet"}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            if transaction_type == "DEPOSIT":
                supplier.wallet += amount
            else:
                supplier.wallet -= amount
            supplier.save()
            serializer.save(supplier = supplier)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

def generate_random_password(length=10):
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice('!_+-&*():/?@$%^&)')

    # Create a pool of all characters and fill the rest of the password
    all_characters = string.ascii_letters + string.digits + '!_+-&*():/?@$%^&)'
    remaining_length = length - 4
    remaining_characters = ''.join(random.choice(all_characters) for _ in range(remaining_length))

    # Combine and shuffle to ensure randomness
    password = uppercase + lowercase + digit + special + remaining_characters
    password = ''.join(random.sample(password, len(password)))

    return password
class InviteAttendantView(generics.GenericAPIView):
    serializer_class = InviteAttendantSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    def post(self, request, id):
        user = request.user
        active_sub = SyncSubscription.objects.filter(code=user.subscription).first()
        if not active_sub:
            return Response(data={"message": "User not subscribed"}, status= status.HTTP_402_PAYMENT_REQUIRED)
        business = get_object_or_404(Business, owner=user, id=id)
        if (business.attendants.count() >= active_sub.no_of_attendants) and (active_sub.no_of_attendants != -1 ):
            return Response(data={"message": "Maximum number of attendance reached for your plan"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = User.objects.filter(phone=serializer.validated_data['phone']).first()
        if phone:
            return Response({
                "status_code": 400,
                "error": "User with phone number already exists",
                "message": "User with phone number already exists",
                "payload": []
            }, status.HTTP_400_BAD_REQUEST)
        firstname = serializer.validated_data["firstname"].replace(" ","")
        lastname = serializer.validated_data["lastname"].replace(" ","")
        business_name = business.name.replace(" ", "-")
        email = f"{firstname}{lastname}{random.randint(1, 100)}@{business_name}.sync".lower()
        with transaction.atomic():
            password = generate_random_password()
            new_user = User.objects.create(firstname=firstname, lastname=lastname, email=email, is_verified=True, role="ATTENDANT", is_tempPassword=True)
            new_user.set_password(password)
            business.attendants.add(new_user)
            new_user.save()
            business.save()
            info = {
                "name": f"{firstname} {lastname}",
                "email": email,
                "password": password,
                "business_email": business.owner.email
            }
            SendMail.send_attendance_email(info)
            return Response(data={"message": "success"}, status=status.HTTP_201_CREATED)

class ListAttendanceView(generics.GenericAPIView):
    serializer_class = GetAttendanceSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs["id"]
        return get_object_or_404(Business,owner=user, id=id)
    def get(self, request, id):
        business = self.get_queryset()
        attendances = business.attendants
        serializer = self.serializer_class(attendances, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    

    