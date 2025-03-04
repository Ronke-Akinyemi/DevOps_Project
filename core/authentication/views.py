import base64
from decouple import config
from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, status, views, permissions, parsers
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.encoding import smart_bytes, smart_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.http import HttpResponsePermanentRedirect, HttpResponse
from django.db import transaction
import random
from datetime import datetime, timedelta
from user.models import SyncSubscription
from utils.email import SendMail
from authentication.models import User, EmailVerification, ForgetPasswordToken, Marketter
from .serializers import (
    SignupSerializer,
    ResendVerificationMailSerializer,
    LoginSerializer,
    PhoneVerificationSerializer,
    RequestPasswordResetEmailSerializer,
    SetNewPasswordSerializer,
    ChangePasswordSerializer,
    PhoneCodeVerificationSerializer,
    DropUserSerializer,
    ChangePasswordNewInvite,
    TwoFactorLoginSerializer
)
from django.shortcuts import get_object_or_404



class SignupView(generics.GenericAPIView):
    serializer_class = SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        # check that user doesn't exist
        user = User.objects.filter(email=serializer.validated_data['email']).first()
        referal = serializer.validated_data.pop('referal', None)
        marketter = Marketter.objects.filter(referral_code=referal).first()
        if user:
            return Response({
                "status_code": 400,
                "error": "User with email already exists",
                "message": "User with email already exists",
                "payload": []
            }, status.HTTP_400_BAD_REQUEST)
        phone = User.objects.filter(phone=serializer.validated_data['phone']).first()
        if phone:
            return Response({
                "status_code": 400,
                "error": "User with phone number already exists",
                "message": "User with phone number already exists",
                "payload": []
            }, status.HTTP_400_BAD_REQUEST)
        trial_plan = SyncSubscription.objects.filter(name="TRIAL").first()
        if not trial_plan:
            return Response(data={"message": "something went wrong"}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            # persist user in db
            today = datetime.today().date()
            seven_days = today + timedelta(days=7)
            #TODO
            user = serializer.save(
                subscription="TRIAL",
                marketter=marketter,
                subscription_date = today,
                subscription_end_date=seven_days
                )
            # generate email verification token
            token = ''.join(random.choices('0123456789', k=6))
            token_expiry = timezone.now() + timedelta(minutes=10)
            EmailVerification.objects.create(user=user, token=token, token_expiry=token_expiry)
            data = {"token": token, 'email': user.email, 'subject': "Sync Account Verification"}
            SendMail.sendVerificationCode(data)
        return Response({
            "message": "Registration successful"
        }, status=status.HTTP_201_CREATED)

class TwoFactorLoginView(generics.GenericAPIView):
    serializer_class = TwoFactorLoginSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        fcm_token = request.data.get('fcm_token')
        user.fcm_token = fcm_token
        user.save()
        return Response( serializer.data, status=status.HTTP_200_OK)
class ResendVerificationMail(generics.GenericAPIView):
    serializer_class = ResendVerificationMailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification_obj = serializer.validated_data

        with transaction.atomic():
            if verification_obj:
                # generate email verification token
                token = ''.join(random.choices('0123456789', k=6))
                token_expiry = timezone.now() + timedelta(minutes=10)
                verification_obj.token = token
                verification_obj.token_expiry = token_expiry
                verification_obj.save()
                data = {"token": token, 'email': verification_obj.user.email, 'subject': "Sync Account Verification"}
                SendMail.sendVerificationCode(data)

        return Response({
            "message": "check phone for verification code",
        }, status=200)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        fcm_token = request.data.get('fcm_token')
        user.fcm_token = fcm_token
        user.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class ResetPasswordNewInvite(generics.GenericAPIView):
    serializer_class = ChangePasswordNewInvite
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        default_password = serializer.validated_data["default_password"]
        new_password = serializer.validated_data["new_password"]
        user = get_object_or_404(User, email = email)
        isCorrectPassword = user.check_password(default_password)
        if not isCorrectPassword:
            return Response(daa={"message": "invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.is_tempPassword = False
        user.save()
        return Response(data={"message": "success"}, status=status.HTTP_200_OK)

        

class DropUser(generics.GenericAPIView):
    serializer_class = DropUserSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        user = get_object_or_404(User, email=email)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class VerifyPhone(generics.GenericAPIView):
    serializer_class = PhoneVerificationSerializer

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({"message": "success"}, status=status.HTTP_200_OK)





class CustomRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = ['http', 'https']


class RequestPasswordResetEmailView(generics.GenericAPIView):
    serializer_class = RequestPasswordResetEmailSerializer

    def post(self, request):
        # validate request body
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        # serializer validated_data retuns custom "False" value if encounters error
        if serializer.validated_data:
            # send sms
            data = {"token": serializer.validated_data["token"], 'email': serializer.validated_data["email"], 'subject': "Sync Password reset"}
            SendMail.sendVerificationCode(data)
        return Response({
            'message': 'we have sent you a code to reset your password'
        }, status=status.HTTP_200_OK)

class VerifyPasswordResetCode(generics.GenericAPIView):
    serializer_class = PhoneCodeVerificationSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        return Response(data=data, status=status.HTTP_200_OK)

class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        serializer = self.serializer_class(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({'message': 'password change successful'}, status=status.HTTP_200_OK)
