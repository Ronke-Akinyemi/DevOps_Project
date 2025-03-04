from rest_framework import status, generics, views
from rest_framework.response import Response
from utils.pagination import CustomPagination
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsBusinessOwner, IsSubscribed
from utils.date import CustomDateFormating
from sale.models import Sale, SaleProduct, PaymentHistory
from django.db.models import Sum, Count
from product.models import Product
from customer.models import Customer
from expenses.models import Expenses
from business.models import Business
from drf_yasg import openapi
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import get_user_model
from .responses.sales_response import sales_response_schema
# Create your views here.
User = get_user_model()

def calculate_percentage_change(yesterday_sales, today_sales):
    if yesterday_sales == 0:
        return 100 if today_sales > 0 else 0
    
    percentage_change = ((today_sales - yesterday_sales) / yesterday_sales) * 100
    return round(percentage_change, 2)


class SalesAnalyticView(views.APIView):
    permission_classes = [IsAuthenticated, IsSubscribed]
    pagination_class = CustomPagination
    @swagger_auto_schema(
        operation_description="Retrieve sales analytics data",
        responses={200: sales_response_schema},
        manual_parameters=[
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
        param1 = self.request.query_params.get('start_date', None)
        param2 = self.request.query_params.get('end_date', None)
        attendant_id = self.request.query_params.get('attendance_id', None)
        start_date, end_date, date_before = CustomDateFormating.start_end_date(param1, param2)
        if not start_date:
            return Response(data={"message":end_date}, status=status.HTTP_400_BAD_REQUEST)

        all_sales = Sale.objects.filter(business__id = id, business__owner=user)
        all_expenses = Expenses.objects.filter(business__id = id, business__owner=user)
        payment_data = PaymentHistory.objects.filter(
            sale__business__id=id,
            sale__business__owner=user,
            created_at__range=[start_date, end_date]
        )
        if is_attendant:
            all_sales = all_sales.filter(attendant=user)
            payment_data = payment_data.filter(sale__attendant =user)
        if attendant_id and not is_attendant:
            attendant = get_object_or_404(User, id=attendant_id)
            all_sales = all_sales.filter(attendant=attendant)
            payment_data = payment_data.filter(sale__attendant =attendant)
        duration = all_sales.filter(date__range=[start_date, end_date])
        before_duration = all_sales.filter(date__range=[date_before, start_date])
        duration_total_revenue = duration.aggregate(total=Sum("total_price"))["total"] or 0
        duration_count_of_transactions = duration.count()
        duration_average_volume = round(duration_total_revenue / duration_count_of_transactions, 0) if duration_count_of_transactions > 0 else 0
        before_duration_total_revenue = before_duration.aggregate(total=Sum("total_price"))["total"] or 0
        before_duration_count_of_transactions = before_duration.count()
        before_duration_average_volume = round(before_duration_total_revenue / before_duration_count_of_transactions, 0) if before_duration_count_of_transactions > 0 else 0
        revenue_change = calculate_percentage_change(before_duration_total_revenue,duration_total_revenue)
        transaction_change = calculate_percentage_change(before_duration_count_of_transactions,duration_count_of_transactions)
        volume_change = calculate_percentage_change(before_duration_average_volume,duration_average_volume)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today = CustomDateFormating.single_day(today)
        one_month_ago = today - relativedelta(months=1)
        six_months_ago = today - relativedelta(months=6)
        one_year_ago = today - relativedelta(years=1)

        all_time_revenue = all_sales.aggregate(total=Sum("total_price"))["total"] or 0
        duration_revenue = duration.aggregate(total=Sum("total_price"))["total"] or 0
        before_duration_revenue = before_duration.aggregate(total=Sum("total_price"))["total"] or 0
        one_month_revenue = all_sales.filter(date__range=[one_month_ago, today]).aggregate(total=Sum("total_price"))["total"] or 0
        six_month_revenue = all_sales.filter(date__range=[six_months_ago, today]).aggregate(total=Sum("total_price"))["total"] or 0
        one_year_revenue = all_sales.filter(date__range=[one_year_ago, today]).aggregate(total=Sum("total_price"))["total"] or 0

        all_time_expenses = all_expenses.aggregate(total=Sum("amount"))["total"] or 0
        duration_expenses = all_expenses.filter(date__range=[start_date, end_date]).aggregate(total=Sum("amount"))["total"] or 0
        before_duration_expenses = all_expenses.filter(date__range=[date_before, start_date]).aggregate(total=Sum("amount"))["total"] or 0
        one_month_expenses = all_expenses.filter(created_at__range=[one_month_ago, today]).aggregate(total=Sum("amount"))["total"] or 0
        six_month_expenses = all_expenses.filter(created_at__range=[six_months_ago, today]).aggregate(total=Sum("amount"))["total"] or 0
        one_year_expenses = all_expenses.filter(created_at__range=[one_year_ago, today]).aggregate(total=Sum("amount"))["total"] or 0
        all_time_profit = all_time_revenue - all_time_expenses
        duration_time_profit = duration_revenue - duration_expenses
        before_duration_profit = before_duration_revenue - before_duration_expenses
        profit_change = calculate_percentage_change(before_duration_profit, duration_time_profit)
        one_month_profit = one_month_revenue - one_month_expenses
        six_month_profit = six_month_revenue - six_month_expenses
        one_year_profit = one_year_revenue - one_year_expenses

        

        payment_data = payment_data.values('method', 'bank__bank_name').annotate(total_amount=Sum('amount')).order_by('method', 'bank__bank_name')

        transaction_data = []
        for payment in payment_data:
            payment_method = {"CASH":"Cash", "MYCLIQ": "Mycliq"}.get(payment['method'])
            record = {
                'payment_method': payment_method,
                'total_amount': payment['total_amount']
            }
            if payment['bank__bank_name'] is not None:
                bank = payment['bank__bank_name'] or "DELETED BANK"
                record['payment_method'] = bank
            transaction_data.append(record)

        chart = {
            'all_time_revenue': all_time_revenue,
            'one_month_revenue': one_month_revenue,
            'six_month_revenue': six_month_revenue,
            'one_year_revenue': one_year_revenue,
            'all_time_expenses': all_time_expenses,
            'one_month_expenses': one_month_expenses,
            'six_month_expenses': six_month_expenses,
            'one_year_expenses': one_year_expenses,
            'all_time_profit': all_time_profit,
            'one_month_profit': one_month_profit,
            'six_month_profit': six_month_profit,
            'one_year_profit': one_year_profit
        }

        return Response({
            'total_Revenue': duration_total_revenue,
            'total_Revenue_change':revenue_change,
            'total_profit': duration_time_profit,
            'total_profit_change': profit_change,
            'transaction_count':duration_count_of_transactions,
            'transaction_count_change':transaction_change,
            'average_transaction_value':duration_average_volume,
            'average_transaction_value_change':volume_change,
            'chart_data': chart,
            'transaction_breakdown':transaction_data
        }, status=200)
    

class ProductAnalytics(views.APIView):
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    pagination_class = CustomPagination
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('start_date', openapi.IN_QUERY, description='Start date (YYYY-MM-DD)', type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description='End date (YYYY-MM-DD)', type=openapi.TYPE_STRING, required=False),
        ]
    )
    def get(self, request, id):
        user = request.user
        param1 = self.request.query_params.get('start_date', None)
        param2 = self.request.query_params.get('end_date', None)
        start_date, end_date, date_before = CustomDateFormating.start_end_date(param1, param2)
        if not start_date:
            return Response(data={"message":end_date}, status=status.HTTP_400_BAD_REQUEST)
        all_products = Product.objects.filter(category__business__id = id, category__business__owner = user)
        total_products =  all_products.count()
        low_stock = all_products.filter(status="LOW").count()
        out_of_stock = all_products.filter(status="OUT-OF-STOCK").count()
        sales_products = SaleProduct.objects.filter(sale__business__id=id)
        last_7_days = timezone.now().date() - timedelta(days=7)
        fast_moving = sales_products.filter(sale__date__gte=last_7_days).values("product__name", "product__image").annotate(quantity_sold=Sum("quantity")).order_by("-quantity_sold").first()
        return Response({
            'total_products':total_products,
            'low_stock':low_stock,
            'out_of_stock':out_of_stock,
            'fast_moving_product': fast_moving,
        }, status=status.HTTP_200_OK)

class CustomerAnalytics(views.APIView):
    permission_classes = [IsAuthenticated, IsBusinessOwner, IsSubscribed]
    pagination_class = CustomPagination
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('start_date', openapi.IN_QUERY, description='Start date (YYYY-MM-DD)', type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('end_date', openapi.IN_QUERY, description='End date (YYYY-MM-DD)', type=openapi.TYPE_STRING, required=False),
        ]
    )
    def get(self, request, id):
        user = request.user
        param1 = self.request.query_params.get('start_date', None)
        param2 = self.request.query_params.get('end_date', None)
        business = get_object_or_404(Business, id=id, owner=user)
        start_date, end_date, date_before = CustomDateFormating.start_end_date(param1, param2)
        if not start_date:
            return Response(data={"message":end_date}, status=status.HTTP_400_BAD_REQUEST)
        all_customers = Customer.objects.filter(business= business)
        total_customers = all_customers.count()
        new_customers = all_customers.filter(created_at__range = [start_date, end_date])
        before_period = all_customers.filter(created_at__range= [date_before, start_date])
        change_in_customer = calculate_percentage_change(before_period.count(), new_customers.count())
        all_sales = Sale.objects.filter(business=business)
        top_customer = all_customers.order_by('-purchase_value').first()
        top_customer_last_sales = all_sales.filter(customer=top_customer).order_by("-created_at").first()
        top_customer_info = {}
        if top_customer_last_sales and top_customer:
            last_amt = top_customer_last_sales.total_price
            top_customer_info["name"] = top_customer.name
            # top_customer_info["image"] = top_customer.profile_pic
            top_customer_info["last_amount"]  = last_amt
        returning_customer = all_sales.filter(created_at__range=[start_date, end_date]).values('customer').distinct().count()
        # before_period_returning_customer = all_sales.filter(created_at__range=[date_before, start_date]).values('customer').distinct().count()
        returning_customer_percentage = round((returning_customer / total_customers * 0.01), 0) if total_customers else 0

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today = CustomDateFormating.single_day(today)
        one_month_ago = today - relativedelta(months=1)
        six_months_ago = today - relativedelta(months=6)
        one_year_ago = today - relativedelta(years=1)

        all_time_total_customer = total_customers
        one_month_total_customer = all_customers.filter(created_at__range = [one_month_ago, today]).count()
        six_months_total_customer = all_customers.filter(created_at__range = [six_months_ago, today]).count()
        one_year_total_customer = all_customers.filter(created_at__range = [one_year_ago, today]).count()
        all_time_returning_customer = all_sales.filter().values('customer').distinct().count()
        one_month_returning_customer = all_sales.filter(created_at__range = [one_month_ago, today]).values('customer').distinct().count()
        six_months_returning_customer = all_sales.filter(created_at__range = [six_months_ago, today]).values('customer').distinct().count()
        one_year_returning_customer = all_sales.filter(created_at__range = [one_year_ago, today]).values('customer').distinct().count()

        chart={
            'all_time_total_customer': all_time_total_customer,
            'one_month_total_customer': one_month_total_customer,
            'six_months_total_customer': six_months_total_customer,
            'one_year_total_customer': one_year_total_customer,
            'all_time_returning_customer': all_time_returning_customer,
            'one_month_returning_customer': one_month_returning_customer,
            'six_months_returning_customer': six_months_returning_customer,
            'one_year_returning_customer':one_year_returning_customer
        }

        return Response({
            'total_customers':total_customers,
            'new_customers':new_customers.count(),
            'change_customers':change_in_customer,
            'returning_customers':returning_customer_percentage,
            'top_customer':top_customer_info,
            'chart_data':chart
        }, status=status.HTTP_200_OK)