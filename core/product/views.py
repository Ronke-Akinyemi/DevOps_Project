from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import status,  generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Q
from product.serializers import ProductSerializer, SupplierProductRestockSerializer, GetProductsSerializer
from product.models import Product, ProductStocking, RESTOCK_PAYMENT_METHOD
from utils.pagination import CustomPagination
from business.models import  Supplier
from category.models import Category
from django.db.models import Sum, Count, Q, F, DecimalField
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from service.models import Service
from itertools import chain
from utils.permissions import IsSubscribed
from operator import attrgetter
from user.models import SyncSubscription
# Create your views here.


class UserProductView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    retrieval_serializer_class = GetProductsSerializer
    def get_serializer(self, *args, **kwargs):
        if self.request.method == 'GET':
            return self.retrieval_serializer_class(*args, **kwargs)
        return self.serializer_class(*args, **kwargs)
    def get_queryset(self):
        user = self.request.user
        id = self.kwargs["id"]
        search_param = self.request.query_params.get('search', None)
        category_param = self.request.query_params.get('category_id', None)
        products = Product.objects.filter(Q(category__business__owner=user) | Q(category__business__attendants=user), category__business__id= id).order_by("-created_at").distinct()
        services = Service.objects.filter(Q(category__business__owner=user) | Q(category__business__attendants=user), category__business__id= id).order_by("-created_at").distinct()
        if category_param:
            products = products.filter(category__id = category_param)
            services = products.filter(category__id = category_param)
        if search_param:
            products = products.filter(Q(name__icontains=search_param) | Q(sku__icontains=search_param))
            services = products.filter(Q(name__icontains=search_param) | Q(sku__icontains=search_param))
        return products, services
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description='Search by item name or SKU',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('category_id', openapi.IN_QUERY, description='Filter by category id',
                              type=openapi.TYPE_STRING,format='uuid', required=False),
            openapi.Parameter('type', openapi.IN_QUERY, description='Filter by type',
                              type=openapi.TYPE_STRING, enum=['PRODUCT', 'SERVICE'], required=False),

        ]
    )
    def get(self, request, id):
        product_queryset, service_queryset = self.get_queryset()
        inventory_value = product_queryset.aggregate(inv_value=Sum(F('quantity') * F('cost_price')))["inv_value"] or 0
        selling_price = product_queryset.aggregate(inv_value=Sum(F('quantity') * F('selling_price')))["inv_value"] or 0
        profit = selling_price - inventory_value
        type_param = request.query_params.get('type')
        if type_param == "PRODUCT":
            combined_qs = product_queryset
        elif type_param == "SERVICE":
            combined_qs = service_queryset
        else:
            combined_qs = sorted(
                chain(product_queryset, service_queryset),
                key=attrgetter('created_at'),
                reverse=True
            )
        serializer = self.get_serializer(combined_qs, many=True)
        page = self.paginate_queryset(combined_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({"inventory_value": inventory_value,"selling_price":selling_price,"profit":profit, "data": serializer.data})
        else:
            data = serializer.data
            response_data = {
                "inventory_value": inventory_value,
                "selling_price":selling_price,
                "profit":profit,
                "data": data,
                # "total_products": queryset.count(),
                # "total_sold": queryset.filter(sold_quantity__gt=0).aggregate(Sum('sold_quantity'))["sold_quantity__sum"] or 0,
                # "total_restocked": queryset.filter(restock_amount__gt=0).aggregate(Sum('restock_amount'))["restock_amount__sum"] or 0,
                # "total_sold_value": queryset.filter(sold_quantity__gt=0).aggregate(Sum('sold_quantity') * F('selling_price'))["sold_quantity__sum__sum"] or 0.0,
            }
            return Response(response_data, status=status.HTTP_200_OK)
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
        category_id = serializer.validated_data.pop("category_id", None)
        supplier_id = serializer.validated_data.pop("supplier_id", None)
        payment_method = serializer.validated_data.pop("payment_method", None)
        amount_paid = serializer.validated_data.pop("amount_paid", None)
        due_date = serializer.validated_data.pop("due_date", None)
        category = get_object_or_404(Category, business__id = id, id= category_id, type="PRODUCT", business__owner=user)
        supplier = None
        if supplier_id:
            supplier = get_object_or_404(Supplier, id=supplier_id, business__id=id)
        cost_price =serializer.validated_data.get("cost_price")
        selling_price=serializer.validated_data.get("selling_price")
        quantity = serializer.validated_data.get("quantity")
        restock_amount = cost_price * quantity
        if payment_method == RESTOCK_PAYMENT_METHOD[2][0]:
            amount_paid = 0
        elif payment_method == RESTOCK_PAYMENT_METHOD[0][0]:
            amount_paid = restock_amount
        elif payment_method == RESTOCK_PAYMENT_METHOD[1][0]:
            if amount_paid > restock_amount:
                return Response(data={"message": "Amount paid can't be more than restock price"}, status=status.HTTP_400_BAD_REQUEST)
            if amount_paid == restock_amount:
                payment_method = RESTOCK_PAYMENT_METHOD[0][0]
        else:
            payment_method = RESTOCK_PAYMENT_METHOD[0][0]
            amount_paid = restock_amount
        with transaction.atomic():
            product = serializer.save(category=category, supplier=supplier)
            if supplier:
                supplier.wallet -= (restock_amount - amount_paid)
                supplier.save()
            ProductStocking.objects.create(
                quantity=quantity,
                product = product,
                supplier=supplier,
                payment_method= payment_method,
                cost_price=cost_price,
                selling_price=selling_price,
                amount_paid = amount_paid,
                due_date = due_date,
                restock_amount= restock_amount,
                )
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

class UserProductSingleView(generics.GenericAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    def get_queryset(self, *args, **kwargs):
        user = self.request.user
        id = self.kwargs["id"]
        # q = Q(category__business__owner=user) | Q(category__business__attendants=user)
        return get_object_or_404(Product,id=id)
    def get(self, request, id):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        product = get_object_or_404(Product, category__business__owner=user, id=id)
        serializer = self.serializer_class(instance=product, data=request.data, partial=True)
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
        product = get_object_or_404(Product, category__business__owner=user, id=id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class UserSupplierProductRestock(generics.GenericAPIView):
    serializer_class = SupplierProductRestockSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    def get_queryset(self):
        id = self.kwargs["id"]
        user = self.request.user
        return ProductStocking.objects.filter(Q(product__category__business__owner=user) | Q(product__category__business__attendants=user), product__id=id).order_by("-created_at").distinct()
    def get(self, request, id):
        user = request.user
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request, id):
        user = request.user
        if user.role != "OWNER":
            return Response(data={"message": "You are not authorized"}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        supplier_id = serializer.validated_data.pop("supplier_id", None)
        amount_paid = serializer.validated_data.pop("amount_paid", None)
        payment_method = serializer.validated_data.get("payment_method")
        restock_cost_price = serializer.validated_data.get("cost_price")
        restock_selling_price = serializer.validated_data.get("selling_price")
        supplier = None
        if supplier_id:
            supplier = get_object_or_404(Supplier, business__owner = user, id=supplier_id)
        quantity = serializer.validated_data.get("quantity")
        product = get_object_or_404(Product, id=id, category__business__owner = user)
        restock_amount = restock_cost_price * quantity
        if payment_method == RESTOCK_PAYMENT_METHOD[2][0]:
            amount_paid = 0
        elif payment_method  == RESTOCK_PAYMENT_METHOD[0][0]:
            amount_paid = restock_amount
        else:
            if amount_paid > restock_amount:
                return Response(data={"message": "Amount paid can't be more than restock price"}, status=status.HTTP_400_BAD_REQUEST)
            if amount_paid == restock_amount:
                payment_method = RESTOCK_PAYMENT_METHOD[0][0]
        with transaction.atomic():
            product.quantity += quantity
            product.cost_price = restock_cost_price
            product.selling_price = restock_selling_price
            if product.quantity > product.low_stock_threshold:
                product.status = "IN-STOCK"
            else:
                product.status = "LOW"
            product.save()
            if supplier:
                supplier.wallet -= (restock_amount - amount_paid)
                supplier.save()
            serializer.save(
                cost_price=restock_cost_price, selling_price=restock_selling_price,
                restock_amount=restock_amount, product=product,
                supplier=supplier, amount_paid=amount_paid, payment_method=payment_method
                )
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)