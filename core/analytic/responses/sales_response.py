from drf_yasg import openapi
sales_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "total_Revenue": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total revenue generated"),
        "total_Revenue_change": openapi.Schema(type=openapi.TYPE_INTEGER, description="Percentage change in revenue"),
        "transaction_count": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total number of transactions"),
        "transaction_count_change": openapi.Schema(type=openapi.TYPE_INTEGER, description="Change in transaction count"),
        "average_transaction_value": openapi.Schema(type=openapi.TYPE_INTEGER, description="Average transaction value"),
        "average_transaction_value_change": openapi.Schema(type=openapi.TYPE_INTEGER, description="Change in average transaction value"),
        "chart_data": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "all_time_revenue": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total revenue of all time"),
                "one_month_revenue": openapi.Schema(type=openapi.TYPE_INTEGER, description="Revenue for the last month"),
                "six_month_revenue": openapi.Schema(type=openapi.TYPE_INTEGER, description="Revenue for the last six months"),
                "one_year_revenue": openapi.Schema(type=openapi.TYPE_INTEGER, description="Revenue for the last year"),
                "all_time_expenses": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total expenses of all time"),
                "one_month_expenses": openapi.Schema(type=openapi.TYPE_INTEGER, description="Expenses for the last month"),
                "six_month_expenses": openapi.Schema(type=openapi.TYPE_INTEGER, description="Expenses for the last six months"),
                "one_year_expenses": openapi.Schema(type=openapi.TYPE_INTEGER, description="Expenses for the last year"),
                "all_time_profit": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total profit of all time"),
                "one_month_profit": openapi.Schema(type=openapi.TYPE_INTEGER, description="Profit for the last month"),
                "six_month_profit": openapi.Schema(type=openapi.TYPE_INTEGER, description="Profit for the last six months"),
                "one_year_profit": openapi.Schema(type=openapi.TYPE_INTEGER, description="Profit for the last year"),
            },
        ),
        "transaction_breakdown": openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "payment_method": openapi.Schema(type=openapi.TYPE_STRING, description="Payment method used"),
                "total_amount": openapi.Schema(type=openapi.TYPE_INTEGER, description="Total amount transacted"),
            },
        ),
    },
    example={
        "total_Revenue": 2000,
        "total_Revenue_change": 60,
        "transaction_count": 23,
        "transaction_count_change": 5,
        "average_transaction_value": 4500,
        "average_transaction_value_change": 65,
        "chart_data": {
            "all_time_revenue": 10000,
            "one_month_revenue": 300,
            "six_month_revenue": 500,
            "one_year_revenue": 2000,
            "all_time_expenses": 10000,
            "one_month_expenses": 500,
            "six_month_expenses": 800,
            "one_year_expenses": 15000,
            "all_time_profit": 34000,
            "one_month_profit": 455,
            "six_month_profit": 7888,
            "one_year_profit": 7889
        },
        "transaction_breakdown": {
            "payment_method": "BANK",
            "total_amount": 900
        }
    }
)