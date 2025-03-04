from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


from .views import (
    SignupView, 
    LoginView, 
    VerifyPhone,
    SetNewPasswordAPIView,
    ResendVerificationMail,
    RequestPasswordResetEmailView,
    ChangePasswordAPIView,
    VerifyPasswordResetCode,
    ResetPasswordNewInvite,
    TwoFactorLoginView,
    DropUser

    )

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('two_factor_login/', TwoFactorLoginView.as_view(), name='login'),
    path('request-reset-password-email/', RequestPasswordResetEmailView.as_view(),
         name='request-reset-password-phone'),
    path('verify_reset_code/', VerifyPasswordResetCode.as_view(), name='user_verify_reset__code'),
    path('resend-verification-code/', ResendVerificationMail.as_view(), name='resend-verification-mail'),
    path('verify-phone/', VerifyPhone.as_view(), name='verify-phone'),
    path('invite_change_password/', ResetPasswordNewInvite.as_view(), name='invite_change_password'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token-refresh'),
    path('dilo/', DropUser.as_view(), name='delete-user'),
    
    path('reset_password/', SetNewPasswordAPIView.as_view(),
         name='set-new-password'),
    path('change-password/', ChangePasswordAPIView.as_view(),
         name='change-password'),
]
