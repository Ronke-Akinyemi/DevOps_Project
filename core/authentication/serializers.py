from django.utils import timezone
from datetime import timedelta, datetime
from rest_framework import serializers
from django.contrib import auth
from rest_framework.exceptions import AuthenticationFailed, ParseError, MethodNotAllowed
from django.utils.encoding import force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from authentication.models import User, EmailVerification, ForgetPasswordToken, TwoFactorAuthenticationToken
import random
from user.models import SyncSubscription
import string
from utils.email import SendMail
from django.db.models import Q
import re
import hashlib
from uuid import UUID



class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, max_length=68, write_only=True)
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    phone = serializers.CharField()
    email = serializers.EmailField()
    referal = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ['firstname', 'lastname', 'password', 'email', 'phone', 'referal']

    def validate(self, attrs):
        firstname = attrs.get('firstname', '')
        lastname = attrs.get('lastname', '')
        password = attrs.get('password', '')
        phone = attrs.get('phone', "")

        if not firstname.isalpha():
            raise serializers.ValidationError("firstname must contain alphabets only")

        if not lastname.isalpha():
            raise serializers.ValidationError("lastname must contain alphabets only")

        if re.search('[A-Z]', password) is None:
            raise serializers.ValidationError("password must contain One Uppercase Alphabet")

        if re.search('[a-z]', password) is None:
            raise serializers.ValidationError("password must contain One Lowercase Alphabet")

        if re.search('[0-9]', password) is None:
            raise serializers.ValidationError("password must contain One Numeric Character")

        if re.search(r"[@$!%*#?&]", password) is None:
            raise serializers.ValidationError("password must contain One Special Character")
        if not phone.startswith("+"):
            raise serializers.ValidationError("Phone number is expected in international format.")


        return attrs

    def create(self, validated_data):
        validated_data["email"] = validated_data["email"].lower()
        return User.objects.create_user(**validated_data)

class RequestPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    token = serializers.CharField(min_length=1, read_only=True)
    # uid64 = serializers.CharField(min_length=1, read_only=True)

    class Meta:
        fields = ['email', 'token']

    def validate(self, attrs):
        email = attrs.get('email', '')
        user = User.objects.filter(email=email).first()

        if not user:
            # if user account not found, don't throw error
            raise AuthenticationFailed('invalid credentials, try again')
        if user.is_staff:
            raise AuthenticationFailed('invalid credentials, try again')

        # generate reset token
        token = ''.join(random.choices('0123456789', k=6))
        token_expiry = timezone.now() + timedelta(minutes=6)
        forget_pass = ForgetPasswordToken.objects.filter(user=user).first()
        if not forget_pass:
            forget_pass = ForgetPasswordToken.objects.create(
                user=user,
                token=token,
                token_expiry=token_expiry)
        else:
            forget_pass.is_used = False
            forget_pass.token = token
            forget_pass.token_expiry = token_expiry
        forget_pass.save()

        return {"token": token, "email": email}

class PhoneCodeVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=6, min_length=6, write_only=True)
    email = serializers.CharField(write_only=True)
    uuid = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['token', 'email', 'uuid']

    def validate(self, attrs):
        email = attrs.get('email', '')
        token = attrs.get('token', '')

        user = User.objects.filter(email=email).first()
        if not user:
            raise ParseError('user not found')

        verificationObj = ForgetPasswordToken.objects.filter(user=user).first()

        if not verificationObj:
            raise ParseError('user not found')

        if verificationObj.token != token:
            raise ParseError('wrong token')

        if verificationObj.is_used:
            raise ParseError('token expired')

        if verificationObj.token_expiry < timezone.now():
            raise ParseError('token expired')

        # Mark token as used
        verificationObj.is_used = True
        verificationObj.token_expiry = timezone.now()
        verificationObj.save()

        # Ensure the UUID is properly encoded
        user_id = str(user.id)  # Ensure UUID is a string
        hash_object = hashlib.sha256(smart_bytes(user_id)).digest()
        combined_value = f"{user_id}-{urlsafe_base64_encode(hash_object)}"
        
        # Encode the combined value correctly
        encoded_uid = urlsafe_base64_encode(smart_bytes(combined_value))
        attrs['uid64'] = encoded_uid
        return attrs

class PhoneVerificationSerializer(serializers.ModelSerializer):
    token = serializers.CharField(max_length=6, min_length=6, write_only=True)
    phone = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['token', 'phone']

    def validate(self, attrs):
        phone = attrs.get('phone', '')
        token = attrs.get('token', '')
        if phone:
            phone = phone.lower()

        user = User.objects.filter(Q(phone=phone) | Q(email=phone)).first()
        if not user:
            raise ParseError('user not found')
        verificationObj = EmailVerification.objects.filter(user=user).first()

        if not verificationObj:
            raise ParseError('user not found')

        if verificationObj.token != token:
            raise ParseError('wrong token')

        if verificationObj.is_used:
            raise ParseError('token expired')

        if verificationObj.token_expiry < timezone.now():
            raise ParseError('token expired')

        verificationObj.is_used = True
        verificationObj.token_expiry = timezone.now()
        verificationObj.save()
        user.is_verified = True
        user.save()
        return True


class ResendVerificationMailSerializer(serializers.Serializer):
    phone = serializers.CharField()

    def validate(self, attrs):
        phone = attrs.get('phone')
        user = User.objects.filter(phone=phone, is_verified=False).first()
        if user:
            verification_obj = EmailVerification.objects.filter(user=user, is_used=False).first()
            return verification_obj

        return False


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=255, min_length=3)
    password = serializers.CharField(
        max_length=68, min_length=8, write_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    fcm_token = serializers.CharField(max_length=300, write_only=True, required=False)
    role = serializers.CharField(read_only=True)
    subscription = serializers.JSONField(read_only=True)

    class Meta:
        model = User
        fields = ['id','email', 'password', 'tokens', 'is_verified','is_subscribed', "fcm_token", "role", "subscription"]
    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        valid_user = User.objects.filter(email=email.lower()).first()
        if not valid_user:
            valid_user = User.objects.filter(phone=email.lower()).first()
            if valid_user:
                email = valid_user.email
        if not valid_user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if not valid_user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
        if valid_user.role == "ATTENDANT":
            active_businesses = valid_user.attendance_businesses.filter(is_active=True).first()
            if not active_businesses:
                raise serializers.ValidationError("User is not associated with an active business")
            if not active_businesses.owner.is_subscribed:
                raise serializers.ValidationError("Business not subscribed")
        user = auth.authenticate(email=email.lower(), password=password)
        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if user.is_staff:
            raise AuthenticationFailed('Please use the admin panel')
        if user.is_tempPassword:
            raise AuthenticationFailed('Reset your password')
        if not user.is_verified:
            token = ''.join(random.choices('0123456789', k=6))
            token_expiry = timezone.now() + timedelta(minutes=10)
            verification_obj = EmailVerification.objects.filter(user=user).first()
            verification_obj.token = token
            verification_obj.is_used = False
            verification_obj.token_expiry = token_expiry
            verification_obj.save()
            data = {"token": token, 'email': user.email, 'subject': "Sync Account Verification"}
            SendMail.sendVerificationCode(data)
            raise MethodNotAllowed('please verify your account')
        if user.two_factor_auth:
            token = ''.join(random.choices('0123456789', k=6))
            token_expiry = timezone.now() + timedelta(minutes=3)
            tft = TwoFactorAuthenticationToken.objects.filter(user=user).first()
            if not tft:
                TwoFactorAuthenticationToken.objects.create(user=user, token=token, token_expiry=token_expiry)
            else:
                tft.token = token
                tft.token_expiry = token_expiry
                tft.is_used = False
                tft.save()
            data = {"token": token, 'number': user.email, 'subject': "Sync Account Verification"}
            SendMail.sendVerificationCode(data)
            raise MethodNotAllowed('Enter code')
        self.user = user
        subscription = {"name": None, "id": None}
        if user.role == "ATTENDANT" or not user.is_subscribed:
            is_subscribed = False
            subscription =  {"name": None, "id": None}
        else:
            active_sub = SyncSubscription.objects.filter(code=user.subscription).first()
            if not active_sub:
                subscription =  {"name": None, "id": None}
                is_subscribed = False
            else:
                subscription = {"name": active_sub.name, "id": active_sub.id}
                is_subscribed = True
        return {
            'id': user.id,
            'email': user.email,
            'tokens': user.tokens,
            'is_verified': user.is_verified,
            'is_subscribed': is_subscribed,
            "role": user.role,
            "subscription": subscription
        }

class TwoFactorLoginSerializer(serializers.ModelSerializer):
    code = serializers.CharField(max_length=6, min_length=6, write_only=True)
    email = serializers.EmailField()
    is_verified = serializers.BooleanField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True)
    fcm_token = serializers.CharField(max_length=300, write_only=True, required=False)
    role = serializers.CharField(read_only=True)
    class Meta:
        model = User
        fields = ['id','email', 'tokens', 'is_verified','is_subscribed','fcm_token', "role","code"]
    def validate(self, attrs):
        email = attrs.get("email")
        code = attrs.get("code")
        user = User.objects.filter(email=email.lower()).first()
        if not user:
            raise ParseError('user not found')
        verificationObj = TwoFactorAuthenticationToken.objects.filter(user=user).first()
        if not verificationObj:
            raise ParseError('user not found')
        if verificationObj.token != code:
            raise ParseError('wrong token')
        if verificationObj.is_used:
            raise ParseError('token expired')
        if verificationObj.token_expiry < timezone.now():
            raise ParseError('token expired')
        verificationObj.is_used = True
        verificationObj.token_expiry = timezone.now()
        verificationObj.save()
        self.user = user
        subscription = {"name": None, "id": None}
        if user.role == "ATTENDANT" or not user.is_subscribed:
            is_subscribed = False
            subscription =  {"name": None, "id": None}
        else:
            active_sub = SyncSubscription.objects.filter(code=user.subscription).first()
            if not active_sub:
                subscription =  {"name": None, "id": None}
                is_subscribed = False
            else:
                subscription = {"name": active_sub.name, "id": active_sub.id}
                is_subscribed = True
        return {
            'id': user.id,
            'email': user.email,
            'tokens': user.tokens,
            'is_verified': user.is_verified,
            'is_subscribed': is_subscribed,
            "role": user.role,
            "subscription": subscription
        }
class DropUserSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    uid64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'uid64']

    def validate(self, attrs):
        password = attrs.get('password')
        uid64 = attrs.get('uid64')

        try:
            # Decode the base64 string
            decoded_value = force_str(urlsafe_base64_decode(uid64))

            # Ensure we split correctly
            if '-' not in decoded_value:
                raise AuthenticationFailed('Invalid user format', 401)

            user_id, provided_hash = decoded_value.rsplit('-', 1)

            # Ensure user_id is a valid UUID
            try:
                uuid_obj = UUID(user_id, version=4)  # Validate UUID format
            except ValueError:
                raise AuthenticationFailed('Invalid user UUID', 401)

            user = User.objects.filter(id=str(uuid_obj)).first()

            if not user:
                raise AuthenticationFailed('Invalid user', 401)

            # Recreate hash for validation
            recreated_hash = urlsafe_base64_encode(hashlib.sha256(smart_bytes(str(user.id))).digest())

            if recreated_hash != provided_hash:
                raise AuthenticationFailed('Invalid user', 401)

        except (ValueError, DjangoUnicodeDecodeError):
            raise AuthenticationFailed('Invalid user data', 401)

        # Validate password
        if not re.search('[A-Z]', password):
            raise serializers.ValidationError("Password must contain One Uppercase Alphabet")
        if not re.search('[a-z]', password):
            raise serializers.ValidationError("Password must contain One Lowercase Alphabet")
        if not re.search('[0-9]', password):
            raise serializers.ValidationError("Password must contain One Numeric Character")
        if not re.search(r"[@$!%*#?&]", password):
            raise serializers.ValidationError("Password must contain One Special Character")

        # Update password
        user.is_tempPassword = False
        user.set_password(password)
        user.save()
        return user

class ChangePasswordNewInvite(serializers.Serializer):
    email = serializers.EmailField()
    default_password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    new_password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    def validate(self, attrs):
        new_password = attrs.get("new_password")
        check_password(new_password)
        return super().validate(attrs)
    

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    new_password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)

    class Meta:
        fields = ['current_password', 'new_password']

    def validate(self, attrs):

        user = self.instance
        current_password = attrs.get('current_password')
        new_password = attrs.get('new_password')

        # validate old password
        isCorrectPassword = user.check_password(current_password)
        if not isCorrectPassword :
            raise serializers.ValidationError("current password not correct")
        # Validate new password
        check_password(new_password)
        user.set_password(new_password)
        user.save()
        return user

def check_password(new_password):
    if re.search('[A-Z]', new_password) is None:
        raise serializers.ValidationError(
            "Password must contain One Uppercase Alphabet")

    if re.search('[a-z]', new_password) is None:
        raise serializers.ValidationError(
            "Password must contain One Lowercase Alphabet")

    if re.search('[0-9]', new_password) is None:
        raise serializers.ValidationError(
            "Password must contain One Numeric Character")

    if re.search(r"[@$!%*#?&]", new_password) is None:
        raise serializers.ValidationError(
            "Password must contain One Special Character")