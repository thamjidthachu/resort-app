import logging
auth_logger = logging.getLogger('authentication')
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.utils.crypto import get_random_string
from rest_framework import status, generics
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError

from django.db.models import Q
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    ForgotPasswordSerializer, 
    PasswordResetSerializer,
    ProfileUpdateSerializer,
    AvatarUpdateSerializer,
    GoogleAuthSerializer,
    GoogleSignupSerializer,
    GoogleLoginSerializer
)
from .google_auth import GoogleAuthService
from utils.email import send_email_message

User = get_user_model()


class UserCheckView(RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'username'

    def get(self, request, *args, **kwargs):
        username = request.query_params.get('username')
        email = request.query_params.get('email')
        if username:
            user = User.objects.filter(username=username).first()
            if user:
                return Response({'status': True}, status=status.HTTP_200_OK)

        if email:
            user = User.objects.filter(email=email).first()
            if user:
                return Response({'status': True}, status=status.HTTP_200_OK)

        return Response({'status': False}, status=status.HTTP_404_NOT_FOUND)

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_data = {
            'user': UserSerializer(user).data,
            'message': 'User registered successfully. Please check your email for login credentials.'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'detail': 'Please provide both username/email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = User.objects.filter(Q(email=username) | Q(username=username)).first()
        if user is None:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        email = user.email
        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response(
                {'detail': 'Invalid Credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Serialize user data
        user_serializer = UserSerializer(user, context={'request': request})

        return Response({
            'user': user_serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful.'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, format=None):
        try:
            # Blacklist refresh token (if provided)
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            # Blacklist access token (from Authorization header)
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                access_token_str = auth_header.split(" ")[1]
                access_token = AccessToken(access_token_str)

                # Store access token in blacklist
                outstanding_token, _ = OutstandingToken.objects.get_or_create(
                    jti=access_token["jti"],
                    defaults={
                        "token": access_token_str,
                        "expires_at": access_token["exp"],
                        "user": request.user,
                    },
                )
                BlacklistedToken.objects.get_or_create(token=outstanding_token)

            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response({"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get(self, request, format=None):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def get_serializer_context(self):
        return {'request': self.request}

class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        user = User.objects.filter(Q(email=username) | Q(username=username)).first()
        token = get_random_string(32)
        user.reset_token = token
        user.save(update_fields=['reset_token'])
        url = f"{settings.BASE_FRONTEND_URL}/reset-password/?token={token}&username={user.username}"
        # Send reset email
        # send_email_message.delay(
        send_email_message(
            subject="Password Reset Request",
            template_name="password-reset.html",
            context={"reset_url": url, "email": user.email, "full_name": user.full_name},
            recipient_list=[user.email]
        )
        return Response({"message": "Password reset instructions sent to your email."}, status=status.HTTP_200_OK)

class PasswordResetView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        try:
            user = User.objects.filter(
                (Q(email=username) | Q(username=username)) & Q(reset_token=token)
                ).first()
        except User.DoesNotExist:
            return Response({"error": "Invalid token or email/username."}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.reset_token = None
        user.save(update_fields=['password', 'reset_token'])
        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class ProfileUpdateView(APIView):
    """API endpoint for updating user profile information"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request, format=None):
        """Update user profile (full update)"""
        serializer = ProfileUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=False,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            auth_logger.info(f"User {request.user.username} updated their profile")
            
            # Return updated user data
            user_serializer = UserSerializer(request.user, context={'request': request})
            return Response({
                'user': user_serializer.data,
                'message': 'Profile updated successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, format=None):
        """Partially update user profile"""
        serializer = ProfileUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            auth_logger.info(f"User {request.user.username} partially updated their profile")
            
            # Return updated user data
            user_serializer = UserSerializer(request.user, context={'request': request})
            return Response({
                'user': user_serializer.data,
                'message': 'Profile updated successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvatarUpdateView(APIView):
    """API endpoint for updating user avatar"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def put(self, request, format=None):
        """Update user avatar"""
        serializer = AvatarUpdateSerializer(
            request.user, 
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Delete old avatar if exists
            if request.user.avatar:
                old_avatar = request.user.avatar
                try:
                    old_avatar.delete(save=False)
                except Exception as e:
                    auth_logger.warning(f"Failed to delete old avatar: {str(e)}")
            
            serializer.save()
            auth_logger.info(f"User {request.user.username} updated their avatar")
            
            # Return updated user data
            user_serializer = UserSerializer(request.user, context={'request': request})
            return Response({
                'user': user_serializer.data,
                'message': 'Avatar updated successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, format=None):
        """Update user avatar (same as PUT for avatar)"""
        return self.put(request, format)

    def delete(self, request, format=None):
        """Delete user avatar"""
        if request.user.avatar:
            try:
                request.user.avatar.delete(save=True)
                auth_logger.info(f"User {request.user.username} deleted their avatar")
                
                # Return updated user data
                user_serializer = UserSerializer(request.user, context={'request': request})
                return Response({
                    'user': user_serializer.data,
                    'message': 'Avatar deleted successfully.'
                }, status=status.HTTP_200_OK)
            except Exception as e:
                auth_logger.error(f"Failed to delete avatar: {str(e)}")
                return Response({
                    'error': 'Failed to delete avatar.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'No avatar to delete.'
        }, status=status.HTTP_404_NOT_FOUND)


class GoogleSignupView(APIView):
    """API endpoint for Google signup"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Sign up user with Google OAuth2 token"""
        serializer = GoogleSignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        phone = serializer.validated_data.get('phone', '')
        username = serializer.validated_data.get('username')
        
        try:
            # Verify Google token and get user info
            user_info = GoogleAuthService.verify_google_token(token)
        except Exception as e:
            auth_logger.error(f"Google token verification failed: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = user_info['email']
        full_name = user_info['full_name']
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'detail': 'User with this email already exists. Please use login.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate username if not provided
        if not username:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
        
        try:
            # Create new user
            user = User.objects.create_user(
                email=email,
                username=username,
                full_name=full_name,
                phone=phone,
                password=get_random_string(32)  # Generate random password since using Google
            )
            
            # Log signup
            auth_logger.info(f"New user registered via Google: {email}")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Serialize user data
            user_serializer = UserSerializer(user, context={'request': request})
            
            return Response({
                'user': user_serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Google signup successful.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            auth_logger.error(f"Error creating user from Google signup: {str(e)}")
            return Response(
                {'detail': 'Error creating user account.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GoogleSigninView(APIView):
    """API endpoint for Google signin"""
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Sign in user with Google OAuth2 token"""
        serializer = GoogleLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        try:
            # Verify Google token and get user info
            user_info = GoogleAuthService.verify_google_token(token)
        except Exception as e:
            auth_logger.error(f"Google token verification failed: {str(e)}")
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = user_info['email']
        
        # Check if user exists
        user = User.objects.filter(email=email).first()
        
        if not user:
            return Response(
                {'detail': 'User with this email does not exist. Please sign up first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is active
        if not user.is_active:
            return Response(
                {'detail': 'User account is inactive.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Serialize user data
            user_serializer = UserSerializer(user, context={'request': request})
            
            auth_logger.info(f"User logged in via Google: {email}")
            
            return Response({
                'user': user_serializer.data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Google signin successful.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            auth_logger.error(f"Error during Google signin: {str(e)}")
            return Response(
                {'detail': 'Error signing in.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )