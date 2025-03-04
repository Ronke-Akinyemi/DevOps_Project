from django.shortcuts import render
from rest_framework import (permissions, generics, views)
from authentication.models import User
from rest_framework.response import Response
from rest_framework import status
from utils.permissions import IsBusinessOwner, IsSubscribed
from utils.velve import VelvePayment
from django.db.models import Q
from django.db import transaction
from service.models import Service
from product.models import Product
from customer.models import Customer
from django.utils import timezone
from datetime import timedelta
from user.models import UserSubscriptions, SyncSubscription
from django.shortcuts import get_object_or_404
from user.serializers import (
    UserProfileSerializer,
    UserSubcribeSerializer,
    ListPlanSerializer
)

# Create your views here.

class Dashboard(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # serializer_class = UserHome
    queryset = User.objects.filter()
    def get(self, request):
        return Response(status=status.HTTP_200_OK)

class UserBankView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    serializer_class =  UserProfileSerializer
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        return user
    


    
class UserProfileView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    serializer_class =  UserProfileSerializer
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        return user
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request):
        user = request.user
        serializer = self.serializer_class(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get("email")
        phone = serializer.validated_data.get("phone")
        filters = Q()
        if email:
            filters |= Q(email=email)
        if phone:
            filters |= Q(phone=phone)

        if filters:
            existing_users = User.objects.filter(filters).values_list("email", "phone")
            for user_email, user_phone in existing_users:
                if user_email == email:
                    return Response(data={"message": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
                if user_phone == phone:
                    return Response(data={"message": "Phone number already exists"}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

class UserIsSubscribe(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    def get(self, request):
        user = request.user
        return Response(data={"is_subscribed": user.is_subscribed}, status=200)
class UserActivePlan(views.APIView):
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner, IsSubscribed]
    serializer_class =  UserSubcribeSerializer
    def get(self, request):
        user = self.request.user
        plan = UserSubscriptions.objects.filter(user=user, status="SUCCESSFUL").order_by("-created_at").first()
        product_counts = Product.objects.filter(category__business__owner=user).count()
        service_counts = Service.objects.filter(category__business__owner=user).count()
        inventory_count =  product_counts + service_counts
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_customers_count = Customer.objects.filter(business__owner=user, created_at__gte=thirty_days_ago).count()
        return Response(data={
            "plan_id": plan.id if plan else 1,
            "start_date":user.subscription_date,
            "end_date": user.subscription_end_date,
            "amount": plan.amount if plan else 0,
            "inventory_count": inventory_count,
            "inventory_limit": plan.plan.inventory_count if plan else 50,
            "customer_limit": plan.plan.customers_count if plan else 5,
            "customer_count": recent_customers_count,
            "duration": plan.duration_type if plan else "SEVEN DAYS",
        }, status=status.HTTP_200_OK)


    


class UserSubscribeView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    serializer_class =  UserSubcribeSerializer

    def get_queryset(self):
        user = self.request.user
        return UserSubscriptions.objects.filter(user=user).order_by("-created_at")
    def get(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    def post(self, request):
        user = request.user
        serializer  = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan_id = serializer.validated_data.get("plan")
        duration = serializer.validated_data.get("duration")
        plan = get_object_or_404(SyncSubscription, id=plan_id)
        if duration == "MONTHLY":
            amount = plan.monthly
        elif duration == "QUATERLY":
            amount = plan.quarterly
        elif duration == "BIANNUAL":
            amount = plan.biannually
        else:
            amount = plan.annually
        if user.is_subscribed:
            try:
                current_plan = int(str(user.subscription)[-1])
                if plan_id < current_plan:
                    return Response(data={"message": "Plan lower than current subscribed plan"}, status=status.HTTP_400_BAD_REQUEST)
            except:
                pass
            
        payment_reference, payment_url = VelvePayment.initiate_payment({"amount": amount})
        if not payment_reference:
            return Response(data={"message": payment_url}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            UserSubscriptions.objects.create(
                user = user,
                plan = plan,
                amount = amount,
                payment_url=payment_url,
                duration_type = duration,
                refrence=payment_reference,
                payment_method= "VELVPAY"
                )
            return Response(data={"payment_url": payment_url}, status=200)

class ListAllPlansViews(generics.ListAPIView):
    queryset = SyncSubscription.objects.all().exclude(name="TRIAL").order_by("monthly")
    serializer_class = ListPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]