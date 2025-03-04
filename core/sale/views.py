from django.shortcuts import render
from sale.serializers import (
    UserSalesSerializer,
    SalesCatAnalysisSerializer,
    OrderHIstorySerializer
    )
from rest_framework import generics, status, views, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from business.models import Business, BusinessBank
from product.models import Product
from customer.models import Customer
from sale.models import Sale, SaleProduct, PaymentHistory, SaleService
from django.shortcuts import get_object_or_404, get_list_or_404
from datetime import datetime
from utils.permissions import IsBusinessOwner
from django.db.models import Sum, Count, Q, F, DecimalField, FloatField
from django.utils import timezone
from datetime import timedelta
from drf_yasg import openapi
from service.models import Service
from drf_yasg.utils import swagger_auto_schema
from utils.pagination import CustomPagination
from django.db import models
from django.contrib.auth import get_user_model
from utils.date import CustomDateFormating
from utils.notification import SendPushNotification
from utils.permissions import IsSubscribed
from itertools import chain
# Create your views here.

User = get_user_model()


class UserSaleView(generics.GenericAPIView):
    serializer_class = UserSalesSerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    def post(self, request, id):
        user = request.user
        business = get_object_or_404(Business, id=id)
        is_attendant = business.attendants.filter(id=user.id).exists()
        if not business.owner == user and not is_attendant:
            return Response(data={"message": "No Business matches the given query"}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        products = serializer.validated_data.pop("products", None)
        product_ids = [p["id"] for p in products if p["type"] == "PRODUCT"]
        service_ids = [p["id"] for p in products if p["type"] == "SERVICE"]
        customer = serializer.validated_data.pop("customer", None)
        bank = serializer.validated_data.pop("bank", None)
        if customer:
            customer = get_object_or_404(Customer, business=business, id=customer)
        if bank:
            bank  = get_object_or_404(BusinessBank, business=business, id=bank)
        amount_paid = serializer.validated_data.pop("amount_paid", None)
        method = serializer.validated_data.get("method")
        valid_products = Product.objects.filter(id__in = product_ids, category__business = business).exclude(status="OUT-OF-STOCK")
        valid_services = Service.objects.filter(id__in = service_ids, category__business = business)
        total_amount = 0
        partial_method  = serializer.validated_data.pop("partial_method", None)

        ## Notification check
        low_stock_notification = business.owner.low_stock_alert_notification
        out_stock_notification = business.owner.out_of_stock_alert_notification
        fcm_token = business.owner.fcm_token

        with transaction.atomic():
            for product in valid_products:
                prd = next((d for d in products if d.get('id') == product.id))
                if product.quantity < prd["quantity"]:
                    return Response(data={"message": f'Quantity of {product.name} available is less than {prd["quantity"]}'}, status=status.HTTP_400_BAD_REQUEST)
                total_amount += (prd["quantity"] * prd["unit_price"])
            for service in valid_services:
                prd = next((d for d in products if d.get('id') == service.id))
                service_qty = prd.get("quantity", 1)
                total_amount += (prd["unit_price"] * service_qty )
            mtd = method
            amt = total_amount
            balance = 0
            if method == "CREDIT":
                balance = total_amount
                customer.wallet -= total_amount
            elif method == "PARTIAL":
                if amount_paid > total_amount:
                    return Response(data={"message":"Amount paid greater than value"}, status=status.HTTP_400_BAD_REQUEST)
                debt = total_amount - amount_paid
                customer.wallet -= debt
                balance = debt
                mtd = partial_method
                amt = amount_paid
            elif method == "ADVANCE" and customer.wallet < total_amount:
                return Response(data={"message":"Wallet balance not up to amount"}, status=status.HTTP_400_BAD_REQUEST)
            elif method == "ADVANCE":
                customer.wallet -= total_amount
            if balance:
                payment_status = "UNPAID"
            else:
                payment_status = "PAID"
            sales = serializer.save(business=business, attendant=user,total_price=total_amount, balance=balance, payment_status=payment_status,customer=customer)
            if customer:
                customer.lastSales = timezone.now().date()
                customer.purchase_value += total_amount
                customer.save()
            if method != "CREDIT":
                PaymentHistory.objects.create(amount=amt, sale=sales, method=mtd, bank=bank)
            for product in valid_products:
                prd = next((d for d in products if d.get('id') == product.id))
                product.quantity -= prd["quantity"]
                if product.quantity == 0:
                    product.status = "OUT-OF-STOCK"
                    if out_stock_notification and fcm_token:
                        SendPushNotification.notify(
                            {
                                "token":fcm_token,
                                "title": "Product Out of stock",
                                "body": f'Your product {product.name} has been sold out',
                                "data": {}
                            }
                        )
                elif product.quantity <= product.low_stock_threshold:
                    product.status = "LOW"
                    if low_stock_notification and fcm_token:
                        SendPushNotification.notify(
                            {
                                "token":fcm_token,
                                "title": "Product Low on stock",
                                "body": f'Your product {product.name} is running out of stock',
                                "data": {}
                            }
                        )
                product.sold += prd["quantity"]
                product.save()
                amt = prd["quantity"] * prd["unit_price"]
                dsc = prd.get("discount") or 0
                price = amt - dsc
                qty = prd["quantity"]
                profit = price - (product.cost_price * qty)
                SaleProduct.objects.create(sale=sales, product=product, unit_price=prd["unit_price"], discount=dsc, quantity=prd["quantity"], price=price, profit=profit)

            for service in valid_services:
                prd = next((d for d in products if d.get('id') == service.id))
                service_qty = prd.get("quantity", 1)
                SaleService.objects.create(sale=sales, service=service, price=prd["unit_price"], quantity=service_qty)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

class SalesAnalysisView(views.APIView):
    serializer_class = UserSalesSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    pagination_class = CustomPagination
    def get(self, request, id):
        user = request.user
        business = get_object_or_404(Business, id=id, owner=user)
        today = datetime.now()
        start_of_today = today.replace(hour=0, minute=0, second=0)
        end_of_today = start_of_today + timedelta(days=1)
        all_sales = Sale.objects.filter(business=business)
        # annotated_sales = all_sales.annotate(
        #     total_revenue=Sum(F('sale_products__price') * F('sale_products__quantity'), output_field=DecimalField()),
        #     total_cost=Sum(F('sale_products__product__cost_price') * F('sale_products__quantity'), output_field=DecimalField())
        # )
        # total_product_cost = annotated_sales.aggregate(total_cost=Sum('total_cost'))['total_cost']
        # total_revenue = annotated_sales.aggregate(total_revenue=Sum('total_revenue'))['total_revenue']
        orders = all_sales.aggregate(total=Sum("total_price"))["total"] or 0.0
        all_customers = Customer.objects.filter(business=business)
        sales_products = SaleProduct.objects.filter(sale__business=business)
        business_products = Product.objects.filter(category__business = business)
        returning_customer = all_sales.filter(created_at__date=timezone.now().date()).values('customer').distinct().count()
        last_7_days = timezone.now().date() - timedelta(days=7)
        next_7_days = timezone.now().date() + timedelta(days=7)
        today_sales = all_sales.filter(created_at__range=(start_of_today, end_of_today))
        total_sales_today = today_sales.aggregate(total=Sum('total_price'))['total'] or 0.0
        current_balance = business.balance
        total_purchases = all_sales.count()
        new_customer = all_customers.filter(created_at__range=(start_of_today, end_of_today)).count()
        # fast_moving = sales_products.filter(sale__date__gte=last_7_days).values("product__name").annotate(total_quantity=Sum("quantity")).order_by("-total_quantity").first()
        fast_moving = sales_products.filter(sale__date__gte=last_7_days).values("product__name", "product__status", "product__image", "product__selling_price").annotate(quantity_sold=Sum("quantity")).order_by("-quantity_sold")[:10]
        for product in fast_moving:
            product["product__image"] = f"https://sync-bck.s3.amazonaws.com{product['product__image']}"
        top_products = sales_products.values("product__name", "product__status", "product__image", "product__selling_price").annotate(quantity_sold=Sum("quantity")).order_by("-quantity_sold")[:10]
        for product in top_products:
            product["product__image"] = f"https://sync-bck.s3.amazonaws.com{product['product__image']}"
        expiring_soon = business_products.filter(expiry_date__range=(end_of_today,next_7_days)).order_by("-expiry_date")[:10]
        expired_product = business_products.filter(expiry_date__lte=end_of_today).order_by("-expiry_date")[:10]
        if expiring_soon:
            expiring_soon = [{
                "product__name": prod.name,
                "product__status": prod.status,
                "product__image": prod.image.url if prod.image else None,
                "product__selling_price": prod.selling_price,
                "quantity_sold": prod.sold
            } for prod in expiring_soon]
        if expired_product:
            expired_product = [{
                "product__name": prod.name,
                "product__status": prod.status,
                "product__image": prod.image.url if prod.image else None,
                "product__selling_price": prod.selling_price,
                "quantity_sold": prod.sold
            } for prod in expired_product]
        return Response({
            'total_sales_today': total_sales_today,
            'current_balance': current_balance,
            'returning_customer':returning_customer,
            'total_purchases': total_purchases,
            'new_customer': new_customer,
            'fast_moving_product': fast_moving,
            'top_selling_products': top_products,
            # 'total_product_cost':total_product_cost,
            # 'total_revenue': total_revenue,
            'total_orders':orders,
            'expiring_soon': expiring_soon,
            'expired_product':expired_product
        }, status=status.HTTP_200_OK)
    

class ProductCategoryAnalysis(generics.ListAPIView):
    serializer_class = SalesCatAnalysisSerializer
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    filter_backends = [filters.SearchFilter]
    search_fields = ["user__id", "user__firstname", "user__lastname", "user__email"]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('type', openapi.IN_QUERY, description='Filter by account status',
                              type=openapi.TYPE_STRING, enum=['TOP-SELLING', 'FAST-MOVING', 'EXPIRING', 'EXPIRED'], required=False)
        ]
    )
    def get(self, request, id):
        user = request.user
        business = get_object_or_404(Business, id=id, owner=user)
        search = request.GET.get("search")
        business_products = Product.objects.filter(category__business = business)
        type  = request.GET.get("type")
        if not type or type.upper() not in ['TOP-SELLING', 'FAST-MOVING', 'EXPIRING', 'EXPIRED']:
            type = 'TOP-SELLING'
        today = datetime.now()
        start_of_today = today.replace(hour=0, minute=0, second=0)
        end_of_today = start_of_today + timedelta(days=1)
        next_7_days = timezone.now().date() + timedelta(days=7)
        # all_sales = Sale.objects.filter(business=business)
        if type == 'TOP-SELLING':
            products = business_products.annotate(
                total_sold=Sum('product_sales__quantity')
            ).order_by('-total_sold')
        elif type == 'FAST-MOVING':
            last_7_days = timezone.now() - timedelta(days=7)
            products = business_products.filter(
                product_sales__sale__date__gte=last_7_days
            ).annotate(
                total_sold=Sum('product_sales__quantity')
            ).order_by('-total_sold')
        elif type == 'EXPIRING':
            products = business_products.filter(
                expiry_date__range=(end_of_today,next_7_days)
            ).order_by('-expiry_date')
        else:
            products = business_products.filter(
                expiry_date__lte=end_of_today
            ).order_by('-expiry_date')
        page = self.paginate_queryset(products)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SalesHistory(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description='Search by item name',
                              type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('type', openapi.IN_QUERY, description='Filter by account status',
                              type=openapi.TYPE_STRING, enum=['TOP-SELLING', 'FAST-MOVING', 'MOST-PROFITABLE'], required=False),
            openapi.Parameter('attendance_id', openapi.IN_QUERY, description='Filter by attendance id',
                              type=openapi.TYPE_STRING,format='uuid', required=False),
            openapi.Parameter('start_date', openapi.IN_QUERY, description='Start date (YYYY-MM-DD)', type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description='End date (YYYY-MM-DD)', type=openapi.TYPE_STRING, required=False),
        ]
    )
    def get(self, request, id):
        user = request.user
        business = get_object_or_404(Business, id=id)
        is_attendant = business.attendants.filter(id=user.id).exists()
        if not business.owner == user and not is_attendant:
            return Response(data={"message": "No Business matches the given query"}, status=status.HTTP_401_UNAUTHORIZED)
        search = request.GET.get("search")
        param1 = self.request.query_params.get('start_date', None)
        param2 = self.request.query_params.get('end_date', None)
        start_date, end_date, _ = CustomDateFormating.start_end_date(param1, param2)
        if not start_date:
            return Response(data={"message":end_date}, status=status.HTTP_400_BAD_REQUEST)
        # business_products = Product.objects.filter(category__business = business)
        all_sales = Sale.objects.filter(business=business, date__range=[start_date, end_date])
        if is_attendant:
            all_sales = all_sales.filter(attendant=user)
        type  = request.GET.get("type")
        attendance_id  = request.GET.get("attendance_id")
        attendance = None
        if attendance_id and is_attendant:
            return Response(data={"message": "Only business owner can filter by attendant"}, status=401)
        if attendance_id:
            attendance = get_object_or_404(User, id=attendance_id)
        if not type or type.upper() not in ['TOP-SELLING', 'FAST-MOVING', 'MOST-PROFITABLE']:
            type = 'TOP-SELLING'
        business_sales_products = SaleProduct.objects.filter(
            sale__business=business,
            sale__date__range=[start_date, end_date]
        )
        business_sales_services = SaleService.objects.filter(
            sale__business=business,
            sale__date__range=[start_date, end_date]
        )
        if is_attendant:
            business_sales_products = business_sales_products.filter(sale__attendant = user)
            business_sales_services = business_sales_services.filter(sale__attendant = user)
        if attendance:
            all_sales = all_sales.filter(attendant = attendance)
            business_sales_products = business_sales_products.filter(sale__attendant = attendance)
            business_sales_services = business_sales_services.filter(sale__attendant = attendance)
        revenue = all_sales.aggregate(total=Sum("total_price"))["total"] or 0.0
    
        today = datetime.now()
        start_of_today = today.replace(hour=0, minute=0, second=0)
        # end_of_today = start_of_today + timedelta(days=1)
        # last_7_days = timezone.now().date() - timedelta(days=7)
        products = business_sales_products.values('product__name').annotate(
            unit_sold=Sum('quantity'),
            revenue=Sum(F('unit_price') * F('quantity'), output_field=FloatField()),
            profit=Sum('profit')
        ).values('product__name', 'unit_sold', 'revenue', 'profit').order_by('unit_sold')

        products = [{'name': p['product__name'], 'unit_sold': p['unit_sold'], 'revenue': p['revenue'], 'profit': p['profit']} for p in products]

        '''
        "name": "Headset",
        "unit_sold": 3,
        "revenue": 900,
        "profit": 2110
        '''
        services = business_sales_services.values(
            'service__name'
        ).annotate(
            name=F('service__name'),
            unit_sold=Sum('quantity'),
            revenue=Sum(F('price') * F('quantity'), output_field=FloatField()),
            profit=Sum(F('price') * F('quantity'), output_field=FloatField()),
        ).values(
            'name',
            'unit_sold',
            'revenue',
            'profit'
        ).order_by('unit_sold')
        if search:
            products = products.filter(name__icontains=search)
            services = services.filter(name__icontains=search)
        costs = business_sales_products.aggregate(
            cost=Sum(F('product__cost_price') * F('quantity') - F('discount'), output_field=FloatField())
        )['cost'] or 0.0
        product_orders = business_sales_products.aggregate(
            sum_orders = Sum('quantity')
        )['sum_orders'] or 0.0
        service_orders = business_sales_services.aggregate(
            sum_orders = Count('id')
        )['sum_orders'] or 0.0
        orders = product_orders + service_orders
        joint_results = list(chain(products, services))
        page = self.paginate_queryset(joint_results)
        if page is not None:
            return self.get_paginated_response({
                "revenue":revenue,
                "cost":costs,
                'orders':orders,
                "data": page
                })
        resp = {
            "revenue":revenue,
            "cost":costs,
            'orders':orders,
            "data": products
        }
        return Response(resp, status=status.HTTP_200_OK)

class OrderHistory(generics.ListAPIView):
    serializer_class = OrderHIstorySerializer
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["id", "customer__firstname", "customer__lastname", "user__email"]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description='Filter by account status',
                              type=openapi.TYPE_STRING, enum=['COMPLETED', 'PENDING', 'CANCELLED'], required=False)
        ]
    )
    def get(self, request, id):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def get_queryset(self):
        id = self.kwargs["id"]
        user = self.request.user
        business = get_object_or_404(Business, id=id)
        is_attendant = business.attendants.filter(id=user.id).exists()
        if not business.owner == user and not is_attendant:
            return Response(data={"message": "No Business matches the given query"}, status=status.HTTP_401_UNAUTHORIZED)
        search_param = self.request.query_params.get('search', None)
        queryset = Sale.objects.filter(business=business).order_by("-created_at").distinct()
        if is_attendant:
            queryset = queryset.filter(attendant=user)
        # if search_param:
        #     queryset = queryset.filter(Q(id__icontains=search_param) | Q(customer__firstname__icontains=search_param) | Q(customer__lastname__icontains=search_param) | Q(customer__email__icontains=search_param))
        return queryset