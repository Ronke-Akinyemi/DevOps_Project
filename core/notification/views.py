from django.shortcuts import render
from rest_framework import (permissions, generics, views, filters)
from authentication.models import User
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import hmac
import hashlib
import json
from decimal import Decimal
import ipaddress
from user.models import UserSubscriptions, MarketerCommision
from datetime import date, timedelta
from django.utils.timezone import now
from django.db import transaction
from decouple import config
from user.management.commands.daily import Command as DailyCheckCommand


# Create your views here.


class Notify(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    # serializer_class = UserHome
    queryset = User.objects.filter()
    def get(self, request):
        return Response(status=status.HTTP_200_OK)


class VelvpayWebhook(views.APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
        auth_token = request.headers.get('Authorization')
        expected_token = config('VELVE_WEBHOOK_TOKEN')
        if not auth_token or auth_token != expected_token:
            return Response({'error': 'Invalid Token'}, status=status.HTTP_400_BAD_REQUEST)
        reference = data.get("data", {}).get("referenceId")
        user_sub = UserSubscriptions.objects.filter(refrence=reference, status="PENDING").first()
        if not user_sub:
            return Response({'error': 'Invalid ReferenceID'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            amount = user_sub.amount
            user_sub.status = "SUCCESSFUL"
            duration = user_sub.duration_type
            if duration == "ANNUAL":
                days = 365
                commision = amount * 0.2
            elif duration == "QUATERLY":
                days = 120
                commision = amount * 0.05
            elif duration == "BIANNUAL":
                days = 182
                commision = amount * 0.1
            else:
                days = 30
                commision = amount * 0.015
            today = date.today()
            end_date = today + timedelta(days=days)
            user_sub.start_date = today
            user_sub.end_date = end_date
            user_sub.save()
            user = user_sub.user
            marketer = user.marketter
            if marketer:
                days_difference = (now() - user.created_at).days
                difference_in_years = (days_difference // 365) + 1
                if difference_in_years <= 3:
                    if difference_in_years <= 1:
                        yrs = "first year"
                    elif difference_in_years == 2:
                        yrs = "second year"
                        commision /= 2
                    elif difference_in_years == 3:
                        yrs = "third year"
                        commision /= 4
                    marketer.balance += Decimal(commision)
                    MarketerCommision.objects.create(
                        marketer=marketer,
                        subscription=user_sub,
                        description = f'Commision of {round(commision, 2)} on {user_sub.plan.name} {duration.lower()} by {user.firstname} {user.lastname} for {yrs} subscription',
                        amount=Decimal(commision))
                    marketer.save()
            user.subscription = user_sub.plan.code
            user.subscription_date = today
            user.subscription_end_date = end_date
            user.is_subscribed = True
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
        

class PaystackWebhook(views.APIView):
    authentication_classes = []
    permission_classes = []
    def post(self, request):
        allowed_ips = [
            ipaddress.ip_address('52.31.139.75'),
            ipaddress.ip_address('52.49.173.169'),
            ipaddress.ip_address('52.214.14.220'),
            ipaddress.ip_address('172.18.0.1'),
            ipaddress.ip_address('127.0.0.1'),
        ]
        client_ip = ipaddress.ip_address(request.META.get('REMOTE_ADDR'))
        # Check if the client's IP address is in the allowed list
        if client_ip not in allowed_ips:
            return Response({'message': 'Unauthorized IP address'}, status=status.HTTP_401_UNAUTHORIZED)

        # Get the request body and headers
        data = json.loads(request.body)
        signature = request.headers.get('X-Paystack-Signature')
        # Validate the event by checking the signature
        expected_signature = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), json.dumps(data).encode(), hashlib.sha512).hexdigest()
        if expected_signature != signature:
            # Retrieve the request's body
            event = data
            if event.get('event') == 'charge.success' and event.get('data'):
                event_data = event.get('data')
                reference = event_data.get('reference')
                user_sub = UserSubscriptions.objects.filter(refrence=reference, status="PENDING").first()
                if not user_sub:
                    return Response(status=status.HTTP_204_NO_CONTENT)
                user_sub.status = "SUCCESSFUL"
                user_sub.save()
                user = user_sub.user
                today = date.today()
                user.subscription = user_sub.plan.name
                user.subscription_date = today
                user.subscription_end_date = today + timedelta(days=30)
                user.is_subscribed = True
                user.save()
            # Do something with event
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        

class TriggerTaskAPIView(views.APIView):
    def post(self, request):
        token = request.data.get("token")
        expected_token = config("ADMIN_JWT_REFRESH_SECRET")
        if token != expected_token:
            return Response({"detail": "Invalid token"}, status=status.HTTP_403_FORBIDDEN)
        try:
            DailyCheckCommand().handle()
            return Response({"detail": "Task executed successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Task execution failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)