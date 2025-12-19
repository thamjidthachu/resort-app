from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


from .views import (
    UserCheckView, 
    RegisterView, 
    LoginView, 
    ProfileView, 
    LogoutView, 
    ForgotPasswordView, 
    PasswordResetView,
    ProfileUpdateView,
    AvatarUpdateView,
    GoogleSignupView,
    GoogleSigninView
)

app_name = 'Authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('user-check/', UserCheckView.as_view(), name='user-check'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Google OAuth2 endpoints
    path('google/signup/', GoogleSignupView.as_view(), name='google-signup'),
    path('google/signin/', GoogleSigninView.as_view(), name='google-signin'),

    # Profile endpoints
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/avatar/', AvatarUpdateView.as_view(), name='avatar-update'),

    # Password reset endpoints
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', PasswordResetView.as_view(), name='reset-password'),
]
