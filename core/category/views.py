from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import status, generics
from rest_framework.response import Response
from utils.pagination import CustomPagination
from utils.permissions import IsSubscribed
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q
from category.models import Category
from category.serializers import CategorySerializer
from business.models import Business
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
# Create your views here.

class BusinessCategoryView(generics.GenericAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('type', openapi.IN_QUERY, description='Filter by expenses type',
                              type=openapi.TYPE_STRING, enum=['PRODUCT', 'EXPENSES'], required=False),
        ]
    )
    def get(self, request, id):
        type = request.query_params.get('type', None)
        queryset = self.get_queryset()
        if type:
            queryset = queryset.filter(type = type)
        page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.serializer_class(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        business = get_object_or_404(Business, owner=user, id=id)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(business=business)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def get_queryset(self):
        business_id = self.kwargs['id']
        user = self.request.user
        return Category.objects.filter(Q(business__owner=user) | Q(business__attendants=user), business__id=business_id).order_by("-created_at").distinct()

class BusinessSingleCategoryView(generics.GenericAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs["id"]
        return get_object_or_404(Category, Q(business__owner=user) | Q(business__attendants=user), id=id)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        category = get_object_or_404(Category, id=id, business__owner=user)
        serializer = self.serializer_class(instance=category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        category = get_object_or_404(Category, id=id, business__owner=user)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
