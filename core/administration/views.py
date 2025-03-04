from django.shortcuts import render
from rest_framework import (permissions, generics, views, filters)
from authentication.permissions import IsAdministrator
from authentication.models import User
from rest_framework.response import Response
from rest_framework import status
import random
import string
from utils.email import SendMail
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Subquery, OuterRef
from datetime import datetime, date
from operator import attrgetter
from django.shortcuts import get_object_or_404
import re
from django.utils.timezone import now
from decimal import Decimal
from .serializers import (
    AdminInviteSerializer
)

# Create your views here.

def generate_random_password(length=10):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


def is_valid_date_format(date_string):
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    return bool(pattern.match(date_string))


class AdminInviteView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsAdministrator]
    serializer_class = AdminInviteSerializer
    queryset = User.objects.filter()

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        role_groups = {
            "administrator": "Administrator",
            "accountant": "Accountant",
            "customer-support": "Customer-support",
            "loan-manager": "Loan-manager"
        }

        email = serializer.validated_data['email']
        first_name = serializer.validated_data['firstname']
        last_name = serializer.validated_data['lastname']
        role = serializer.validated_data.get('role')
        if role:
            role = role.strip().lower()

        user_exists = User.objects.filter(email=email).exists()
        if user_exists:
            return Response(data={"message": "user already exists"}, status=status.HTTP_400_BAD_REQUEST)

        password = generate_random_password()
        new_admin = User.objects.create(
            email=email.lower(), firstname=first_name, lastname=last_name, role="ADMIN")
        new_admin.set_password(password)
        new_admin.is_staff = True
        new_admin.is_verified = True

        # # Add user to the appropriate group based on role
        # group_name = role_groups.get(role, "Customer-support")
        # group, created = Group.objects.get_or_create(name=group_name)
        # new_admin.groups.add(group)

        new_admin.save()

        data = {"email": email, "password": password, "role": role}
        SendMail.send_invite_mail(data)

        return Response(data={"message": "Account created successfully"}, status=status.HTTP_201_CREATED)

