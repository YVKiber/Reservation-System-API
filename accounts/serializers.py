from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError, ValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from rest_framework import serializers

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        required=True,
    )

    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'password',
                  'password_confirm')
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate (self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        if password != password_confirm:
            raise serializers.ValidationError('Passwords do not match.')

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')

        password = validated_data.pop('password')

        user = User(**validated_data)
        user.is_active = False
        send_verification_email(user)
        user.set_password(password)
        user.save()

        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',
                  'username',
                  'email',
                  'first_name',
                  'last_name',
                  'is_staff',
                  'date_joined',
                  )
        read_only_fields = ['id', 'is_staff', 'date_joined']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def validate_email(self, value):
        user = self.context['request'].user

        if value and User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError('Email already registered.')
        
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True,
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )
    def validate_new_password(self, value):
        user = self.context["request"].user
        try:
            validate_password(value, user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)

        return value

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"]

        user = User.objects.filter(
            email=email,
            is_active=True
        ).first()

        if not user:
            return

        uid = urlsafe_base64_encode(
            force_bytes(user.pk),
        )

        token = default_token_generator.make_token(user)

        reset_link = (
            f"{settings.FRONTEND_BASE_URL}"
            f"/password-reset-confirm"
            f"?uid={uid}&token={token}"
        )

        subject = "Password reset request"

        message = (
            "Hello,\n\n"
            "You requested a password reset for your account.\n\n"
            f"Use this link to reset your password:\n{reset_link}\n\n"
            "If you did not request this, you can ignore this email.\n"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")
        new_password = attrs.get("new_password")

        try:
            user_id = force_str(
                urlsafe_base64_decode(uid)
            )

            user = User.objects.get(
                pk=user_id,
                is_active=True,
            )

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {
                    "detail": "Invalid password reset link."
                }
            )

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError(
                {
                    "detail": "Invalid or expired password reset token."
                }
            )

        validate_password(
            password=new_password,
            user=user,
        )

        attrs["user"] = user

        return attrs

    def save(self):
        user = self.validated_data["user"]
        new_password = self.validated_data["new_password"]

        user.set_password(new_password)
        user.save(update_fields=["password"])

def send_verification_email(user):
    uid = urlsafe_base64_encode(
        force_bytes(str(user.pk))
    )

    token = default_token_generator.make_token(user)

    verification_link = (
        f"{settings.FRONTEND_BASE_URL}"
        f"/verify-email"
        f"?uid={uid}&token={token}"
    )

    subject = "Verify your email address"

    message = (
        "Hello,\n\n"
        "Thank you for registering in Django Blogging API.\n\n"
        f"Verification link:\n{verification_link}\n\n"
        "For API testing, use these values:\n"
        f"uid: {uid}\n"
        f"token: {token}\n\n"
        "If you did not create this account, you can ignore this email.\n"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")

        try:
            user_id = force_str(
                urlsafe_base64_decode(uid)
            )

            user = User.objects.get(
                pk=user_id
            )

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                {
                    "detail": "Invalid email verification link."
                }
            )

        if user.is_active:
            raise serializers.ValidationError(
                {
                    "detail": "Account is already verified."
                }
            )

        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError(
                {
                    "detail": "Invalid or expired email verification token."
                }
            )

        attrs["user"] = user

        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.is_active = True
        user.save(update_fields=["is_active"])

class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"]

        user = User.objects.filter(
            email=email
        ).first()

        if not user:
            return

        if user.is_active:
            return

        send_verification_email(user)

