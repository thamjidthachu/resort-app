from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from utils.email import send_email_message
from django.db.models import Q

from apps.authentication.models import User


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id',  'avatar', 'username', 'full_name', 'email', 'phone', 'gender', 'is_active',]
        read_only_fields = ['id', 'is_active']
    
    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('avatar','username', 'email', 'phone', 'password', 'password2', 'full_name')
        extra_kwargs = {
            'full_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email is already in use."})

        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"username": "Username is already in use."})

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Remove password2 from the data
        validated_data.pop('password2', None)
        
        # Create user
        user = User.objects.create_user(
            avatar=validated_data.get('avatar'),
            username=validated_data['username'],
            email=validated_data['email'],
            phone=validated_data['phone'],
            full_name=validated_data.get('full_name'),
            password=validated_data['password']
        )
        
        # Send welcome email asynchronously using Celery
        send_email_message.delay(
            subject="Welcome to Azure Horizon | Login Details",
            template_name="welcome.html",
            context={
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "password": validated_data['password']
            },
            recipient_list=[user.email]
        )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(label=_("Token"), read_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(request=self.context.get('request'),
                              username=username, password=password)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Must include "username" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate_username(self, value):
        if not User.objects.filter(Q(email=value) | Q(username=value)).exists():
            raise serializers.ValidationError("No user is associated with this username.")
        return value


class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        username = attrs.get('username')
        token = attrs.get('token')
        if not User.objects.filter(
                (Q(email=username) | Q(username=username)) & Q(reset_token=token)
                ).exists():
            raise serializers.ValidationError("Invalid token or email/username.")
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile information"""
    
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone', 'gender']
        extra_kwargs = {
            'username': {'required': False},
            'full_name': {'required': False},
            'email': {'required': False},
            'phone': {'required': False},
            'gender': {'required': False},
        }

    def validate_username(self, value):
        """Ensure username is unique (excluding current user)"""
        user = self.instance
        if User.objects.filter(username=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value

    def validate_email(self, value):
        """Ensure email is unique (excluding current user)"""
        user = self.instance
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user avatar"""
    
    class Meta:
        model = User
        fields = ['avatar']

    def validate_avatar(self, value):
        """Validate avatar file"""
        if value:
            # Check file size (limit to 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Avatar file size should not exceed 5MB.")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError(
                    "Invalid file type. Only JPEG, PNG, GIF, and WebP images are allowed."
                )
        return value


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth2 authentication"""
    token = serializers.CharField(required=True, write_only=True)
    
    def validate_token(self, value):
        """Validate Google token"""
        if not value:
            raise serializers.ValidationError("Token is required")
        return value


class GoogleSignupSerializer(GoogleAuthSerializer):
    """Serializer for Google signup with additional fields"""
    phone = serializers.CharField(required=False, allow_blank=True, max_length=50)
    username = serializers.CharField(required=False, allow_blank=True, max_length=50)
    
    def validate_username(self, value):
        """Validate username is unique if provided"""
        if value and User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already in use.")
        return value


class GoogleLoginSerializer(GoogleAuthSerializer):
    """Serializer for Google login"""
    pass