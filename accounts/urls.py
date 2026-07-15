from django.urls import path

from .views import MeView, RegisterView, EmailVerificationView, ResendEmailVerificationView, ChangePasswordView, \
    PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email', ),
    path('resend-verification/', ResendEmailVerificationView.as_view(), name='resend-verification', ),
    path('me/', MeView.as_view(), name='me'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name="password-reset", ),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name="password-reset-confirm", ),
]