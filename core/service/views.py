from django.shortcuts import render
from service.serializers import ServiceSerializer
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from utils.pagination import CustomPagination
from utils.permissions import IsSubscribed
from django.shortcuts import get_object_or_404
from category.models import Category
from service.models import Service
from django.db.models import Q
from product.models import Product
from user.models import SyncSubscription
# Create your views here.


class UserServiceView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = ServiceSerializer
    pagination_class = CustomPagination
    def get_queryset(self):
        user = self.request.user
        id = self.kwargs["id"]
        search_param = self.request.query_params.get('search', None)
        category_param = self.request.query_params.get('category_id', None)
        services = Service.objects.filter(Q(category__business__owner=user) | Q(category__business__attendants=user), category__business__id= id).order_by("-created_at").distinct()
        if category_param:
            services = services.filter(category__id = category_param)
        if search_param:
            services =services.filter(name__icontains=search_param)
        return services
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description='Search service by name',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('category_id', openapi.IN_QUERY, description='Filter by category id',
                              type=openapi.TYPE_STRING,format='uuid', required=False),
        ]
    )
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
    def post(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        active_sub = SyncSubscription.objects.filter(code=user.subscription).first()
        if not active_sub:
            return Response(data={"message": "User not subscribed"}, status= status.HTTP_402_PAYMENT_REQUIRED)
        product_counts = Product.objects.filter(category__business__owner=user).count()
        service_counts = Service.objects.filter(category__business__owner=user).count()
        if ((product_counts + service_counts) >= active_sub.inventory_count) and (active_sub.inventory_count != -1 ):
            return Response(data={"message": "Maximum number of Inventory reached for your plan"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data.pop("category_id")
        category = get_object_or_404(Category, business__id = id, id= category_id, type="PRODUCT", business__owner=user)
        serializer.save(category=category)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

class UserServiceSingleView(generics.GenericAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs["id"]
        return get_object_or_404(Service, Q(category__business__owner=user) | Q(category__business__attendants=user), id=id)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        service = get_object_or_404(Service, category__business__owner=user, id=id)
        serializer = self.serializer_class(instance=service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data.pop("category_id", None)
        if category_id:
            category = get_object_or_404(Category, business__id = id, id= category_id, type="PRODUCT", business__owner=user)
            serializer.save(category=category)
        else:
            serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        service = get_object_or_404(Service, category__business__owner=user, id=id)
        service.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



